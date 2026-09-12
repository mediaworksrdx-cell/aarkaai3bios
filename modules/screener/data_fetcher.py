from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime

import yfinance as yf

from modules.screener.schemas import DataQuality
from modules.technical import compute_indicators, get_signal, compute_extended_indicators, detect_candlestick_patterns
from modules.finance import _fetch_twelve_data, _fetch_ticker_data, get_options_chain, get_open_interest_summary

logger = logging.getLogger(__name__)

@dataclass
class StockSnapshot:
    symbol: str
    price: float
    prev_close: float
    change_pct: float
    # Fundamentals
    eps: float | None = None
    pe: float | None = None
    pb: float | None = None
    ps: float | None = None
    ev_ebitda: float | None = None
    roe: float | None = None
    roa: float | None = None
    debt_equity: float | None = None
    dividend_yield: float | None = None
    revenue_growth: float | None = None
    profit_margin: float | None = None
    market_cap: float | None = None
    beta: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    # Technical
    indicators: dict = field(default_factory=dict)
    candlestick_patterns: list = field(default_factory=list)
    # Options
    options_data: dict | None = None
    # OHLCV DataFrame (for SMC/institutional engines)
    ohlcv_df: object = None  # pd.DataFrame, typed as object to avoid import issues
    # Meta
    data_quality: DataQuality = DataQuality.FULL
    fetched_at: datetime | None = None
    exchange: str = "NSE"
    currency: str = "INR"

class DataFetcher:
    def __init__(self, max_workers: int = 12, cache_ttl: int = 60):
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[StockSnapshot, float]] = {}
        self._cache_lock = threading.Lock()

    def _is_cache_valid(self, symbol: str) -> bool:
        with self._cache_lock:
            if symbol in self._cache:
                _, cached_time = self._cache[symbol]
                if time.time() - cached_time < self.cache_ttl:
                    return True
        return False

    def invalidate_cache(self, symbol: str | None = None):
        with self._cache_lock:
            if symbol is None:
                self._cache.clear()
            elif symbol in self._cache:
                del self._cache[symbol]

    def fetch_single(self, symbol: str, include_options: bool = False) -> StockSnapshot | None:
        if self._is_cache_valid(symbol):
            with self._cache_lock:
                if symbol in self._cache:
                    return self._cache[symbol][0]

        try:
            is_us_stock = not symbol.endswith('.NS')
            currency = "USD" if is_us_stock else "INR"
            exchange = "US" if is_us_stock else "NSE"
            
            # Fetch Live Price
            price_data = _fetch_ticker_data(symbol)
            if not price_data or 'price' not in price_data:
                logger.error(f"[{symbol}] Failed to fetch price data.")
                return None
            
            price = price_data.get('price', 0.0)
            prev_close = price_data.get('previous_close', price)
            change_pct = price_data.get('change_percent', 0.0)

            snapshot = StockSnapshot(
                symbol=symbol,
                price=price,
                prev_close=prev_close,
                change_pct=change_pct,
                exchange=exchange,
                currency=currency,
                fetched_at=datetime.now()
            )

            missing_fundamentals = False
            missing_technicals = False

            # Fetch Fundamentals
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if info:
                    snapshot.eps = info.get('trailingEps') or info.get('forwardEps')
                    snapshot.pe = info.get('trailingPE') or info.get('forwardPE')
                    snapshot.pb = info.get('priceToBook')
                    snapshot.ps = info.get('priceToSalesTrailing12Months')
                    snapshot.ev_ebitda = info.get('enterpriseToEbitda')
                    snapshot.roe = info.get('returnOnEquity')
                    snapshot.roa = info.get('returnOnAssets')
                    snapshot.debt_equity = info.get('debtToEquity')
                    snapshot.dividend_yield = info.get('dividendYield')
                    snapshot.revenue_growth = info.get('revenueGrowth')
                    snapshot.profit_margin = info.get('profitMargins')
                    snapshot.market_cap = info.get('marketCap')
                    snapshot.beta = info.get('beta')
                    snapshot.high_52w = info.get('fiftyTwoWeekHigh')
                    snapshot.low_52w = info.get('fiftyTwoWeekLow')
                else:
                    missing_fundamentals = True
            except Exception as e:
                logger.warning(f"[{symbol}] Error fetching fundamentals: {e}")
                missing_fundamentals = True

            # Fetch Technicals
            try:
                indicators = compute_extended_indicators(symbol, "6mo")
                if indicators:
                    snapshot.indicators = indicators
                    if "patterns" in indicators and indicators["patterns"]:
                        snapshot.candlestick_patterns = indicators["patterns"]
                else:
                    missing_technicals = True
            except Exception as e:
                logger.warning(f"[{symbol}] Error fetching technicals: {e}")
                missing_technicals = True

            # Fetch OHLCV DataFrame
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="1y")
                if not df.empty:
                    snapshot.ohlcv_df = df
                else:
                    missing_technicals = True
            except Exception as e:
                logger.warning(f"[{symbol}] Error fetching OHLCV data: {e}")
                missing_technicals = True

            # Fetch Options Data
            if include_options:
                try:
                    options_data = {}
                    chain = get_options_chain(symbol)
                    if chain:
                        options_data['chain'] = chain
                    oi_summary = get_open_interest_summary(symbol)
                    if oi_summary:
                        options_data['oi_summary'] = oi_summary
                    if options_data:
                        snapshot.options_data = options_data
                except Exception as e:
                    logger.warning(f"[{symbol}] Error fetching options data: {e}")

            if missing_fundamentals or missing_technicals:
                snapshot.data_quality = DataQuality.PARTIAL
            else:
                snapshot.data_quality = DataQuality.FULL

            with self._cache_lock:
                self._cache[symbol] = (snapshot, time.time())

            return snapshot

        except Exception as e:
            logger.error(f"[{symbol}] Unexpected error in fetch_single: {e}")
            return None

    def fetch_batch(self, symbols: list[str], include_options: bool = False) -> dict[str, StockSnapshot]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.fetch_single, sym, include_options): sym 
                for sym in symbols
            }
            for future in as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                try:
                    snapshot = future.result()
                    if snapshot:
                        results[sym] = snapshot
                except Exception as e:
                    logger.error(f"[{sym}] Error in batch fetch: {e}")
        return results
