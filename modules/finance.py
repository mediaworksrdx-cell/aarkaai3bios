"""
AARKAAI – Finance Module (yfinance)

Supports: US / India stocks, crypto, commodities, forex.
Only triggered when the semantic filter routes a finance query.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import yfinance as yf

from config import COMMODITY_TICKERS, CRYPTO_SUFFIXES, FOREX_PAIRS, INDIA_SUFFIX

logger = logging.getLogger(__name__)

# ─── Common US tickers for quick lookup ───────────────────────────────────────
_US_TICKERS: dict[str, str] = {
    "apple": "AAPL", "google": "GOOGL", "alphabet": "GOOGL",
    "microsoft": "MSFT", "amazon": "AMZN", "meta": "META",
    "tesla": "TSLA", "nvidia": "NVDA", "amd": "AMD",
    "netflix": "NFLX", "intel": "INTC", "ibm": "IBM",
    "disney": "DIS", "walmart": "WMT", "jpmorgan": "JPM",
    "visa": "V", "mastercard": "MA", "paypal": "PYPL",
    "coca-cola": "KO", "pepsi": "PEP", "nike": "NKE",
}

_INDIA_TICKERS: dict[str, str] = {
    "reliance": "RELIANCE.NS", "tcs": "TCS.NS", "infosys": "INFY.NS",
    "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS", "wipro": "WIPRO.NS",
    "sbi": "SBIN.NS", "airtel": "BHARTIARTL.NS", "adani": "ADANIENT.NS",
    "bajaj": "BAJFINANCE.NS", "itc": "ITC.NS", "hul": "HINDUNILVR.NS",
    "maruti": "MARUTI.NS", "tata motors": "TATAMOTORS.NS",
    "tata steel": "TATASTEEL.NS", "kotak": "KOTAKBANK.NS",
    "sunpharma": "SUNPHARMA.NS", "lt": "LT.NS", "hcl": "HCLTECH.NS",
}

_INDEX_TICKERS: dict[str, str] = {
    "nifty 50": "^NSEI", "nifty50": "^NSEI", "nifty": "^NSEI",
    "sensex": "^BSESN", "bse": "^BSESN",
    "bank nifty": "^NSEBANK", "banknifty": "^NSEBANK",
    "s&p 500": "^GSPC", "s&p500": "^GSPC", "sp500": "^GSPC",
    "dow jones": "^DJI", "dow": "^DJI",
    "nasdaq": "^IXIC",
    "nifty it": "^CNXIT", "nifty bank": "^NSEBANK",
    "nifty next 50": "^NSMIDCP", "nifty midcap": "^NSMIDCP",
}

_CRYPTO_TICKERS: dict[str, str] = {
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "cardano": "ADA-USD", "ada": "ADA-USD",
    "xrp": "XRP-USD", "ripple": "XRP-USD",
    "polkadot": "DOT-USD", "litecoin": "LTC-USD",
    "bnb": "BNB-USD", "binance": "BNB-USD",
}


def extract_tickers(query: str) -> list[str]:
    """
    Extract ticker symbols from a natural-language query.
    Looks for known names, explicit $SYMBOLS, and .NS suffixes.
    """
    q_lower = query.lower()
    tickers: list[str] = []

    # Explicit $TICKER mentions
    explicit = re.findall(r"\$([A-Z]{1,6})", query.upper())
    tickers.extend(explicit)

    # Explicit TICKER.NS mentions
    ns_tickers = re.findall(r"([A-Z]{2,20}\.NS)", query.upper())
    tickers.extend(ns_tickers)

    # Named lookups
    for name, ticker in {**_US_TICKERS, **_INDIA_TICKERS, **_INDEX_TICKERS, **_CRYPTO_TICKERS}.items():
        if name in q_lower:
            tickers.append(ticker)

    # Commodity lookups
    for name, ticker in COMMODITY_TICKERS.items():
        if name in q_lower:
            tickers.append(ticker)

    # Forex lookups
    for name, ticker in FOREX_PAIRS.items():
        if name in q_lower:
            tickers.append(ticker)

    return list(dict.fromkeys(tickers))  # deduplicate, preserve order


def _fetch_ticker_data(symbol: str) -> dict:
    """Fetch live data for a single ticker."""
    try:
        tk = yf.Ticker(symbol)
        info = tk.info or {}

        # Get price - try multiple fields (indices use different keys)
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("regularMarketPreviousClose")
        )

        # Fallback: use history if info doesn't have price
        if not price:
            try:
                hist = tk.history(period="1d")
                if not hist.empty:
                    price = round(float(hist["Close"].iloc[-1]), 2)
            except Exception:
                pass

        result: dict = {
            "symbol": symbol,
            "name": info.get("shortName") or info.get("longName", symbol),
            "price": price,
            "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "INR" if ".NS" in symbol or symbol.startswith("^N") else "USD"),
        }

        # Compute change
        if result["price"] and result["previous_close"]:
            change = result["price"] - result["previous_close"]
            pct = (change / result["previous_close"]) * 100
            result["change"] = round(change, 2)
            result["change_percent"] = round(pct, 2)

        return result
    except Exception as exc:
        logger.error("yfinance fetch failed for %s: %s", symbol, exc)
        return {"symbol": symbol, "error": str(exc)}


def get_market_data(query: str) -> dict:
    """
    Main entry point.  Extracts tickers and fetches live data.

    Returns
    -------
    dict with keys: tickers, data, summary
    """
    tickers = extract_tickers(query)
    if not tickers:
        return {"tickers": [], "data": {}, "summary": ""}

    data: dict = {}
    for t in tickers:
        data[t] = _fetch_ticker_data(t)

    summary = format_finance_context(data)
    return {"tickers": tickers, "data": data, "summary": summary}


def format_finance_context(data: dict) -> str:
    """Produce a human-readable summary for context fusion."""
    lines: list[str] = []
    for symbol, info in data.items():
        if "error" in info:
            lines.append(f"• {symbol}: data unavailable ({info['error']})")
            continue
        name = info.get("name", symbol)
        price = info.get("price", "N/A")
        currency = info.get("currency", "USD")
        change = info.get("change", "")
        pct = info.get("change_percent", "")
        cap = info.get("market_cap")
        cap_str = f", Market Cap: {_format_large_number(cap)}" if cap else ""
        change_str = f", Change: {change} ({pct}%)" if change != "" else ""
        lines.append(f"• {name} ({symbol}): {currency} {price}{change_str}{cap_str}")
    return "\n".join(lines) if lines else "No data available."


def _format_large_number(n: Optional[int]) -> str:
    if n is None:
        return "N/A"
    if n >= 1_000_000_000_000:
        return f"${n / 1_000_000_000_000:.2f}T"
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    return f"${n:,}"
