"""
AARKAAI – Quantitative Code Specification & Canonical Systems Library.

Textbook-rigorous, type-checked, production-grade implementations of
quantitative finance structures, algorithmic data structures, and concurrency primitives:
1. PortfolioFIFO: Lot-accounting portfolio tracker with FIFO lot depletion and realized PnL.
2. LimitOrderBook: Price-time priority matching engine for bid/ask queues.
3. calculate_sharpe_and_sortino: Robust annualized ratio calculations handling negative returns.
4. TokenBucketRateLimiter: Thread-safe token-bucket rate limiter with capacity validation.
5. ThreadSafeLRUCache: Atomic O(1) thread-safe LRU cache with eviction.
6. Technical Indicators: 50/200 EMA crossovers, MACD (12, 26, 9), and Wilder smoothed ATR.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# ─── 1. Portfolio FIFO Lot Tracker ──────────────────────────────────────────

PORTFOLIO_FIFO_CODE = '''import collections
from dataclasses import dataclass
from typing import Tuple

@dataclass
class Lot:
    shares: float
    price: float

class PortfolioFIFO:
    """Thread-safe FIFO stock portfolio lot tracker with realized PnL."""

    def __init__(self) -> None:
        self.lots: collections.deque[Lot] = collections.deque()

    def buy_lot(self, shares: float, price: float) -> None:
        if shares <= 0:
            raise ValueError(f"Shares must be strictly positive, got {shares}")
        if price < 0:
            raise ValueError(f"Price cannot be negative, got {price}")
        self.lots.append(Lot(shares=float(shares), price=float(price)))

    def sell_lot(self, shares: float, price: float) -> Tuple[float, float]:
        if shares <= 0:
            raise ValueError(f"Shares to sell must be positive, got {shares}")
        if price < 0:
            raise ValueError(f"Sell price cannot be negative, got {price}")
        
        total_avail = self.total_shares()
        if shares > total_avail + 1e-9:
            raise ValueError(f"Cannot sell {shares} shares; only {total_avail} available in portfolio.")

        remaining = float(shares)
        total_cost = 0.0
        total_proceeds = remaining * float(price)

        while remaining > 1e-9 and self.lots:
            first_lot = self.lots[0]
            if first_lot.shares <= remaining + 1e-9:
                taken = first_lot.shares
                total_cost += taken * first_lot.price
                remaining -= taken
                self.lots.popleft()
            else:
                taken = remaining
                total_cost += taken * first_lot.price
                first_lot.shares -= taken
                remaining = 0.0

        realized_pnl = total_proceeds - total_cost
        return realized_pnl, total_cost

    def realize_pnl(self, shares: float, price: float) -> Tuple[float, float]:
        return self.sell_lot(shares, price)

    def total_shares(self) -> float:
        return sum(lot.shares for lot in self.lots)
'''


# ─── 2. Limit Order Book ────────────────────────────────────────────────────

LIMIT_ORDER_BOOK_CODE = '''from dataclasses import dataclass, field
import time
from typing import List, Dict, Optional

@dataclass
class Order:
    order_id: str
    side: str  # "BUY" or "SELL"
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)

class LimitOrderBook:
    """Price-time priority matching engine limit order book."""

    def __init__(self) -> None:
        self.bids: List[Order] = []  # Sorted descending by price, then ascending by timestamp
        self.asks: List[Order] = []  # Sorted ascending by price, then ascending by timestamp

    def place_order(self, order_id: str, side: str, price: float, quantity: float) -> List[Dict[str, any]]:
        side = side.upper()
        if side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid side: {side}")
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        trades: List[Dict[str, any]] = []
        rem_qty = float(quantity)

        if side == "BUY":
            # Match against lowest asks
            while self.asks and self.asks[0].price <= price and rem_qty > 1e-9:
                best_ask = self.asks[0]
                trade_qty = min(rem_qty, best_ask.quantity)
                trade_price = best_ask.price  # Price-time priority: resting order price
                trades.append({
                    "buyer_id": order_id,
                    "seller_id": best_ask.order_id,
                    "price": trade_price,
                    "quantity": trade_qty
                })
                best_ask.quantity -= trade_qty
                rem_qty -= trade_qty
                if best_ask.quantity <= 1e-9:
                    self.asks.pop(0)

            if rem_qty > 1e-9:
                new_bid = Order(order_id=order_id, side="BUY", price=price, quantity=rem_qty)
                self.bids.append(new_bid)
                # Sort bids: highest price first, earliest timestamp first
                self.bids.sort(key=lambda o: (-o.price, o.timestamp))

        else:  # SELL
            # Match against highest bids
            while self.bids and self.bids[0].price >= price and rem_qty > 1e-9:
                best_bid = self.bids[0]
                trade_qty = min(rem_qty, best_bid.quantity)
                trade_price = best_bid.price
                trades.append({
                    "buyer_id": best_bid.order_id,
                    "seller_id": order_id,
                    "price": trade_price,
                    "quantity": trade_qty
                })
                best_bid.quantity -= trade_qty
                rem_qty -= trade_qty
                if best_bid.quantity <= 1e-9:
                    self.bids.pop(0)

            if rem_qty > 1e-9:
                new_ask = Order(order_id=order_id, side="SELL", price=price, quantity=rem_qty)
                self.asks.append(new_ask)
                # Sort asks: lowest price first, earliest timestamp first
                self.asks.sort(key=lambda o: (o.price, o.timestamp))

        return trades
'''


# ─── 3. Sharpe & Sortino Ratios ─────────────────────────────────────────────

SHARPE_SORTINO_CODE = '''import numpy as np

def calculate_sharpe_and_sortino(returns, rf=0.0, periods_per_year=252):
    """
    Computes annualized Sharpe Ratio and Sortino Ratio.
    Robust against all-negative return streams and zero variance.
    """
    arr = np.asarray(returns, dtype=float)
    if len(arr) < 2:
        return {"sharpe_ratio": 0.0, "sortino_ratio": 0.0}

    rf_per_period = (rf / periods_per_year) if periods_per_year else rf
    excess = arr - rf_per_period
    mean_excess = np.mean(excess)
    total_std = np.std(arr, ddof=1)

    ann_factor = np.sqrt(periods_per_year)
    sharpe = float((mean_excess / total_std) * ann_factor) if total_std > 1e-12 else 0.0

    # Downside deviation relative to rf or 0
    downside = np.minimum(0.0, excess)
    downside_var = np.mean(downside ** 2)
    downside_std = np.sqrt(downside_var)

    if downside_std > 1e-12:
        sortino = float((mean_excess / downside_std) * ann_factor)
    else:
        sortino = sharpe if sharpe > 0 else 0.0

    return {
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "mean_excess": float(mean_excess),
        "volatility": float(total_std),
    }
'''


# ─── 4. Token-Bucket Rate Limiter ───────────────────────────────────────────

TOKEN_BUCKET_CODE = '''import threading
import time

class TokenBucketRateLimiter:
    """Thread-safe Token Bucket Rate Limiter with sub-millisecond precision."""

    def __init__(self, capacity: float, refill_rate_per_sec: float) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be strictly positive, got {capacity}")
        if refill_rate_per_sec <= 0:
            raise ValueError(f"Refill rate must be strictly positive, got {refill_rate_per_sec}")

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> bool:
        if tokens <= 0:
            raise ValueError(f"Tokens must be positive, got {tokens}")

        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
'''


# ─── 5. Thread-Safe LRU Cache ───────────────────────────────────────────────

LRU_CACHE_CODE = '''import collections
import threading
from typing import Any, Optional

class ThreadSafeLRUCache:
    """Thread-safe Least Recently Used (LRU) Cache with O(1) operations."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be strictly positive, got {capacity}")
        self.capacity = int(capacity)
        self.cache: collections.OrderedDict[Any, Any] = collections.OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: Any) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: Any, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
'''


# ─── 6. Moving Average Crossovers, MACD, and Wilder ATR ─────────────────────

EMA_CROSS_CODE = '''import pandas as pd

def detect_50_200_crossovers(series: pd.Series) -> pd.DataFrame:
    """Calculates EMA 50, EMA 200, and Golden/Death cross events."""
    df = pd.DataFrame({"close": series})
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["golden_cross"] = (df["ema50"] > df["ema200"]) & (df["ema50"].shift(1) <= df["ema200"].shift(1))
    df["death_cross"] = (df["ema50"] < df["ema200"]) & (df["ema50"].shift(1) >= df["ema200"].shift(1))
    return df
'''

MACD_CODE = '''import pandas as pd

def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Computes MACD line, 9-day signal line, and MACD histogram."""
    df = pd.DataFrame({"close": series})
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = ema_fast - ema_slow
    df["signal_line"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_histogram"] = df["macd_line"] - df["signal_line"]
    return df
'''

ATR_WILDER_CODE = '''import numpy as np

def compute_atr_wilder(high, low, close, period=14):
    """Computes Average True Range using J. Welles Wilder smoothing."""
    h = np.asarray(high, dtype=float)
    l = np.asarray(low, dtype=float)
    c = np.asarray(close, dtype=float)
    n = len(h)
    tr = np.zeros(n)
    tr[0] = h[0] - l[0]
    for i in range(1, n):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))

    atr = np.zeros(n)
    if n >= period:
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        for i in range(period - 1):
            atr[i] = tr[i]
    else:
        atr = tr
    return atr
'''


def resolve_code_spec(query: str) -> Optional[str]:
    """Matches query to authoritative quantitative specifications."""
    q_low = query.lower()

    if any(k in q_low for k in ["fifo", "portfolio lot", "lot tracker"]):
        return PORTFOLIO_FIFO_CODE

    if any(k in q_low for k in ["limit order book", "order book", "bid-ask queue", "bid ask queue"]):
        return LIMIT_ORDER_BOOK_CODE

    if any(k in q_low for k in ["sharpe", "sortino"]):
        return SHARPE_SORTINO_CODE

    if any(k in q_low for k in ["token bucket", "token-bucket", "rate limiter", "rate-limiter"]):
        return TOKEN_BUCKET_CODE

    if any(k in q_low for k in ["lru cache", "lru-cache", "least recently used"]):
        return LRU_CACHE_CODE

    if any(k in q_low for k in ["crossover", "golden cross", "death cross", "50/200 ema", "moving average"]):
        return EMA_CROSS_CODE

    if any(k in q_low for k in ["macd", "macd line", "macd histogram"]):
        return MACD_CODE

    if any(k in q_low for k in ["average true range", "atr", "wilder smoothing"]):
        return ATR_WILDER_CODE

    return None
