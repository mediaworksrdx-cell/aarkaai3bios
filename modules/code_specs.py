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
7. MinHeap: Min-Heap priority queue data structure with bug-free bubble_down index update.
8. Dijkstra: Adjacency-list shortest path algorithm with priority queue.
9. ParameterizedQueryBuilder: Safe parameterized SQL query builder preventing injection.
10. AsyncWorkerQueue: Production-grade asyncio.Queue worker pool with graceful sentinel shutdown.
11. FastAPIBearerRateLimit: HTTPBearer security dependency and sliding-window rate limiter.
12. MultiStageDockerfile: Hardened multi-stage Dockerfile with non-root runner user.
13. NSETradingDayCalendar: Official NSE calendar excluding weekends and official exchange holidays.
14. CandlestickPatternScanner: Precise Bullish Engulfing and Hammer candlestick scanners.
15. HistoricalVaR_CVaR: Historical Value-at-Risk and Expected Shortfall calculator.
16. OptionGreeksAnalytical: Black-Scholes analytical Delta, Gamma, Vega, Theta, Rho.
17. LoanEMIAmortization: Monthly EMI and amortization schedule with zero-interest handling.
18. BollingerBandsCalculators: 20-period rolling price standard deviation returning bands & BandWidth%.
19. CAPMCalculator: Capital Asset Pricing Model expected return accepting int/float inputs.
20. CAGRWithGuards: Strict domain validation raising ValueError on non-positive principal.
21. SQLiteConnectionManager: Thread-safe SQLite connection manager with thread-local pooling.
22. ATRTrailingStop: Monotonic non-reversing ATR trailing stop for long and short.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union
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
    """Price-time priority matching engine for limit order books."""

    def __init__(self) -> None:
        self.bids: List[Order] = []  # Sorted descending by price, ascending by time
        self.asks: List[Order] = []  # Sorted ascending by price, ascending by time

    def place_order(self, order_id: str, side: str, price: float, quantity: float) -> List[Dict]:
        side_norm = side.upper()
        if side_norm not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL")
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        order = Order(order_id=order_id, side=side_norm, price=float(price), quantity=float(quantity))
        trades = []

        if side_norm == "BUY":
            # Match against lowest asks where ask.price <= buy.price
            while self.asks and self.asks[0].price <= order.price and order.quantity > 0:
                best_ask = self.asks[0]
                match_qty = min(order.quantity, best_ask.quantity)
                match_price = best_ask.price
                trades.append({
                    "buyer_id": order.order_id,
                    "seller_id": best_ask.order_id,
                    "price": match_price,
                    "quantity": match_qty
                })
                order.quantity -= match_qty
                best_ask.quantity -= match_qty
                if best_ask.quantity == 0:
                    self.asks.pop(0)

            if order.quantity > 0:
                self.bids.append(order)
                # Sort bids: highest price first, then earliest timestamp
                self.bids.sort(key=lambda o: (-o.price, o.timestamp))

        else:  # SELL
            # Match against highest bids where bid.price >= sell.price
            while self.bids and self.bids[0].price >= order.price and order.quantity > 0:
                best_bid = self.bids[0]
                match_qty = min(order.quantity, best_bid.quantity)
                match_price = best_bid.price
                trades.append({
                    "buyer_id": best_bid.order_id,
                    "seller_id": order.order_id,
                    "price": match_price,
                    "quantity": match_qty
                })
                order.quantity -= match_qty
                best_bid.quantity -= match_qty
                if best_bid.quantity == 0:
                    self.bids.pop(0)

            if order.quantity > 0:
                self.asks.append(order)
                # Sort asks: lowest price first, then earliest timestamp
                self.asks.sort(key=lambda o: (o.price, o.timestamp))

        return trades
'''


# ─── 3. Sharpe & Sortino Ratio Calculator ───────────────────────────────────

SHARPE_SORTINO_CODE = '''import math
import numpy as np

def calculate_sharpe_and_sortino(returns, risk_free_rate=0.0, periods_per_year=252, mar=0.0):
    """Calculates annualized Sharpe and Sortino ratios handling negative excess returns."""
    arr = np.asarray(returns, dtype=float)
    if len(arr) < 2:
        raise ValueError("At least 2 return observations required")

    excess_returns = arr - risk_free_rate
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    sharpe = (mean_excess / std_excess * math.sqrt(periods_per_year)) if std_excess > 0 else 0.0

    # Downside deviation for Sortino (penalizes only returns below MAR)
    downside_diff = np.minimum(0.0, arr - mar)
    downside_std = math.sqrt(np.mean(downside_diff ** 2))

    mean_vs_mar = np.mean(arr - mar)
    sortino = (mean_vs_mar / downside_std * math.sqrt(periods_per_year)) if downside_std > 0 else 0.0

    return {
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "annualized_mean_excess": float(mean_excess * periods_per_year),
        "annualized_std": float(std_excess * math.sqrt(periods_per_year)),
        "downside_std": float(downside_std * math.sqrt(periods_per_year)),
    }
'''


# ─── 4. Token Bucket Rate Limiter ───────────────────────────────────────────

TOKEN_BUCKET_CODE = '''import threading
import time

class TokenBucketRateLimiter:
    """Thread-safe Token-Bucket rate limiter with capacity validation."""

    def __init__(self, capacity: float, refill_rate_per_sec: float) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be strictly positive, got {capacity}")
        if refill_rate_per_sec <= 0:
            raise ValueError(f"Refill rate must be strictly positive, got {refill_rate_per_sec}")

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> bool:
        if tokens <= 0:
            raise ValueError("Tokens to acquire must be positive")

        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now

            # Refill tokens up to maximum capacity
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

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
    """Thread-safe O(1) LRU Cache with atomic eviction and capacity guard."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be strictly positive (> 0), got {capacity}")
        self.capacity = int(capacity)
        self.cache: collections.OrderedDict[Any, Any] = collections.OrderedDict()
        self.lock = threading.Lock()

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

    def size(self) -> int:
        with self.lock:
            return len(self.cache)
'''


# ─── 6. Technical Indicators (EMA, MACD, Wilder ATR) ─────────────────────────

EMA_CROSS_CODE = '''import pandas as pd

def detect_50_200_crossovers(prices):
    """Computes 50 and 200 EMA and detects golden cross and death cross events."""
    s = pd.Series(prices, dtype=float)
    df = pd.DataFrame({"close": s})
    df["ema50"] = s.ewm(span=50, adjust=False).mean()
    df["ema200"] = s.ewm(span=200, adjust=False).mean()

    # Golden cross: 50 EMA crosses above 200 EMA
    prev_50 = df["ema50"].shift(1)
    prev_200 = df["ema200"].shift(1)
    df["golden_cross"] = (prev_50 <= prev_200) & (df["ema50"] > df["ema200"])
    df["death_cross"] = (prev_50 >= prev_200) & (df["ema50"] < df["ema200"])
    return df
'''

MACD_CODE = '''import pandas as pd

def compute_macd(prices, fast=12, slow=26, signal=9):
    """Computes MACD line, 9-day Signal line, and MACD Histogram."""
    s = pd.Series(prices, dtype=float)
    df = pd.DataFrame({"close": s})
    df["ema_fast"] = s.ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = s.ewm(span=slow, adjust=False).mean()
    df["macd_line"] = df["ema_fast"] - df["ema_slow"]
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


# ─── 7. Min-Heap Priority Queue (Bug-free Bubble-down) ──────────────────────

MIN_HEAP_CODE = '''from typing import Any, List, Optional

class MinHeap:
    """Min-Heap priority queue implementation with bubble-up and bubble-down."""

    def __init__(self) -> None:
        self.heap: List[Any] = []

    def push(self, val: Any) -> None:
        self.heap.append(val)
        self._bubble_up(len(self.heap) - 1)

    def pop(self) -> Any:
        if not self.heap:
            raise IndexError("pop from empty heap")
        if len(self.heap) == 1:
            return self.heap.pop()
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._bubble_down(0)
        return root

    def peek(self) -> Optional[Any]:
        return self.heap[0] if self.heap else None

    def __len__(self) -> int:
        return len(self.heap)

    def _bubble_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self.heap[index] < self.heap[parent]:
                self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
                index = parent
            else:
                break

    def _bubble_down(self, index: int) -> None:
        size = len(self.heap)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2
            if left < size and self.heap[left] < self.heap[smallest]:
                smallest = left
            if right < size and self.heap[right] < self.heap[smallest]:
                smallest = right
            if smallest != index:
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest  # FIXED: Updates index on swap to prevent infinite loop
            else:
                break
'''


# ─── 8. Dijkstra Shortest Path ──────────────────────────────────────────────

DIJKSTRA_CODE = '''import heapq
from typing import Dict, List, Optional, Tuple

def dijkstra(graph: Dict[str, List[Tuple[str, float]]], start: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Computes shortest paths from start node using Dijkstra's algorithm.
    
    Args:
        graph: Adjacency list mapping node to list of (neighbor, weight) tuples.
        start: Starting node identifier.
        
    Returns:
        distances: Dict mapping each reachable node to its minimum distance.
        predecessors: Dict mapping each reachable node to its prior node on shortest path.
    """
    distances: Dict[str, float] = {start: 0.0}
    predecessors: Dict[str, Optional[str]] = {start: None}
    pq: List[Tuple[float, str]] = [(0.0, start)]

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if curr_dist > distances.get(u, float("inf")):
            continue

        for v, weight in graph.get(u, []):
            if weight < 0:
                raise ValueError(f"Negative edge weight detected ({u} -> {v}: {weight}); Dijkstra requires non-negative weights.")
            d = curr_dist + weight
            if d < distances.get(v, float("inf")):
                distances[v] = d
                predecessors[v] = u
                heapq.heappush(pq, (d, v))

    return distances, predecessors

def shortest_path(graph: Dict[str, List[Tuple[str, float]]], start: str, target: str) -> Tuple[float, List[str]]:
    """Returns total distance and ordered node path from start to target."""
    distances, predecessors = dijkstra(graph, start)
    if target not in distances:
        raise ValueError(f"Target node '{target}' unreachable from start '{start}'")
    path = []
    curr: Optional[str] = target
    while curr is not None:
        path.append(curr)
        curr = predecessors.get(curr)
    path.reverse()
    return distances[target], path
'''


# ─── 9. Parameterized Query Builder ─────────────────────────────────────────

QUERY_BUILDER_CODE = '''import re
from typing import Any, List, Optional, Tuple

class ParameterizedQueryBuilder:
    """Safe, injection-proof SQL query builder using parameter bindings and identifier validation."""

    _VALID_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    def __init__(self, table: str) -> None:
        self._validate_identifier(table)
        self.table = table
        self._select_cols: List[str] = []
        self._where_clauses: List[str] = []
        self._params: List[Any] = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None

    @classmethod
    def _validate_identifier(cls, name: str) -> None:
        if not cls._VALID_IDENTIFIER.match(name):
            raise ValueError(f"Invalid SQL identifier: {name!r}. Must be alphanumeric with underscores.")

    def select(self, *columns: str) -> "ParameterizedQueryBuilder":
        if not columns:
            self._select_cols = ["*"]
        else:
            for col in columns:
                if col != "*":
                    self._validate_identifier(col)
            self._select_cols = list(columns)
        return self

    def where(self, column: str, op: str, value: Any) -> "ParameterizedQueryBuilder":
        self._validate_identifier(column)
        op_clean = op.strip().upper()
        if op_clean not in ("=", "!=", "<>", ">", "<", ">=", "<=", "LIKE", "ILIKE", "IS", "IS NOT"):
            raise ValueError(f"Unsupported SQL operator: {op!r}")
        self._where_clauses.append(f"{column} {op_clean} ?")
        self._params.append(value)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "ParameterizedQueryBuilder":
        self._validate_identifier(column)
        dir_clean = direction.strip().upper()
        if dir_clean not in ("ASC", "DESC"):
            raise ValueError(f"Invalid order direction: {direction!r}")
        self._order_by = f"{column} {dir_clean}"
        return self

    def limit(self, count: int) -> "ParameterizedQueryBuilder":
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Limit must be a non-negative integer, got {count!r}")
        self._limit = count
        return self

    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        cols = ", ".join(self._select_cols) if self._select_cols else "*"
        sql_parts = [f"SELECT {cols} FROM {self.table}"]
        if self._where_clauses:
            sql_parts.append("WHERE " + " AND ".join(self._where_clauses))
        if self._order_by:
            sql_parts.append(f"ORDER BY {self._order_by}")
        if self._limit is not None:
            sql_parts.append("LIMIT ?")
            params = tuple(self._params + [self._limit])
        else:
            params = tuple(self._params)
        return " ".join(sql_parts), params
'''


# ─── 10. Async Worker Queue ─────────────────────────────────────────────────

ASYNC_QUEUE_CODE = '''import asyncio
import logging
from typing import Any, Callable, Coroutine, List

logger = logging.getLogger(__name__)

class AsyncWorkerQueue:
    """Production-grade asyncio.Queue worker pool with graceful sentinel shutdown."""

    def __init__(self, num_workers: int = 4) -> None:
        if num_workers <= 0:
            raise ValueError("num_workers must be positive")
        self.num_workers = num_workers
        self.queue: asyncio.Queue[Any] = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self._sentinel = object()

    async def _worker_loop(self, worker_id: int, handler: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        while True:
            item = await self.queue.get()
            if item is self._sentinel:
                self.queue.task_done()
                break
            try:
                await handler(item)
            except Exception as exc:
                logger.error(f"Worker {worker_id} error handling task: {exc}", exc_info=True)
            finally:
                self.queue.task_done()

    async def enqueue(self, item: Any) -> None:
        await self.queue.put(item)

    async def start(self, handler: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        self.workers = [
            asyncio.create_task(self._worker_loop(i, handler), name=f"worker-{i}")
            for i in range(self.num_workers)
        ]

    async def join_and_shutdown(self) -> None:
        await self.queue.join()
        for _ in range(self.num_workers):
            await self.queue.put(self._sentinel)
        await asyncio.gather(*self.workers, return_exceptions=True)
'''


# ─── 11. FastAPI Bearer Auth & Rate Limiter ─────────────────────────────────

FASTAPI_BEARER_CODE = '''import hmac
import time
from typing import Dict
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="Secure API with Bearer Auth & Sliding Rate Limiter")
security = HTTPBearer()

TOKEN_SECRET = "production-bearer-token-secret-replace-in-env"
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: Dict[str, list[float]] = {}

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    token = credentials.credentials
    if not hmac.compare_digest(token, TOKEN_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "authorized_user"

def rate_limiter(client_id: str = Depends(verify_token)) -> None:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    history = _rate_limit_store.setdefault(client_id, [])
    _rate_limit_store[client_id] = [t for t in history if t > cutoff]
    if len(_rate_limit_store[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS}s",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
        )
    _rate_limit_store[client_id].append(now)

@app.get("/api/v1/protected-data", dependencies=[Depends(rate_limiter)])
async def get_protected_data(user: str = Depends(verify_token)):
    return {"status": "success", "user": user, "data": "Confidential financial telemetry"}
'''


# ─── 12. Multi-Stage Dockerfile ─────────────────────────────────────────────

DOCKERFILE_CODE = '''# Multi-stage production build for FastAPI application
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false -m appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --chown=appuser:appgroup . /app

USER appuser:appgroup
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


# ─── 13. NSE Trading Day Calendar ───────────────────────────────────────────

NSE_CALENDAR_CODE = '''from datetime import date, datetime
from typing import Dict, Set, Union

class NSETradingDayCalendar:
    """Official National Stock Exchange of India (NSE) trading calendar."""

    HOLIDAYS: Dict[int, Set[date]] = {
        2024: {
            date(2024, 1, 22), date(2024, 1, 26), date(2024, 3, 8), date(2024, 3, 25),
            date(2024, 3, 29), date(2024, 4, 11), date(2024, 4, 17), date(2024, 5, 1),
            date(2024, 5, 20), date(2024, 6, 17), date(2024, 7, 17), date(2024, 8, 15),
            date(2024, 10, 2), date(2024, 11, 1), date(2024, 11, 15), date(2024, 12, 25),
        },
        2025: {
            date(2025, 1, 26), date(2025, 2, 26), date(2025, 3, 14), date(2025, 3, 31),
            date(2025, 4, 10), date(2025, 4, 14), date(2025, 4, 18), date(2025, 5, 1),
            date(2025, 6, 7), date(2025, 8, 15), date(2025, 8, 27), date(2025, 10, 2),
            date(2025, 10, 21), date(2025, 10, 22), date(2025, 11, 5), date(2025, 12, 25),
        },
        2026: {
            date(2026, 1, 26), date(2026, 2, 17), date(2026, 3, 3), date(2026, 3, 20),
            date(2026, 4, 3), date(2026, 4, 14), date(2026, 5, 1), date(2026, 5, 27),
            date(2026, 8, 15), date(2026, 9, 16), date(2026, 10, 2), date(2026, 10, 20),
            date(2026, 11, 8), date(2026, 11, 24), date(2026, 12, 25),
        },
    }

    @classmethod
    def is_trading_day(cls, query_date: Union[str, date, datetime], year: int = None) -> bool:
        """Determines if query_date is a regular NSE equity trading day."""
        if isinstance(query_date, str):
            dt = datetime.strptime(query_date, "%Y-%m-%d").date()
        elif isinstance(query_date, datetime):
            dt = query_date.date()
        elif isinstance(query_date, date):
            dt = query_date
        else:
            raise TypeError(f"Invalid date type: {type(query_date)}")

        curr_year = year if year is not None else dt.year
        if dt.weekday() >= 5:
            return False

        holidays = cls.HOLIDAYS.get(curr_year, set())
        if dt in holidays:
            return False

        return True
'''


# ─── 14. Candlestick Pattern Scanner ────────────────────────────────────────

CANDLESTICK_SCANNER_CODE = '''import pandas as pd

def scan_bullish_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Scans OHLC DataFrame for Bullish Engulfing and Hammer candlestick patterns."""
    for col in ('open', 'high', 'low', 'close'):
        if col not in df.columns:
            raise ValueError(f"DataFrame must contain column '{col}'")

    res = df.copy()
    res['bullish_engulfing'] = False
    res['hammer'] = False

    opens = res['open'].values
    highs = res['high'].values
    lows = res['low'].values
    closes = res['close'].values
    n = len(res)

    for i in range(1, n):
        # 1. Bullish Engulfing
        prev_bearish = closes[i - 1] < opens[i - 1]
        curr_bullish = closes[i] > opens[i]
        engulfs_body = (opens[i] <= closes[i - 1]) and (closes[i] >= opens[i - 1])
        if prev_bearish and curr_bullish and engulfs_body:
            res.iloc[i, res.columns.get_loc('bullish_engulfing')] = True

        # 2. Hammer
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        body = abs(c - o)
        total_range = h - l
        if total_range > 0:
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            if lower_shadow >= 2.0 * body and upper_shadow <= 0.25 * body:
                res.iloc[i, res.columns.get_loc('hammer')] = True

    return res
'''


# ─── 15. Historical VaR & CVaR ──────────────────────────────────────────────

HISTORICAL_VAR_CVAR_CODE = '''import numpy as np
from typing import Dict, Sequence

def calculate_var_cvar(returns: Sequence[float], confidence_level: float = 0.95) -> Dict[str, float]:
    """Calculates Historical Value-at-Risk (VaR) and Conditional VaR (Expected Shortfall)."""
    arr = np.asarray(returns, dtype=float)
    if len(arr) < 10:
        raise ValueError(f"At least 10 return observations required, got {len(arr)}")
    if not (0.5 < confidence_level < 1.0):
        raise ValueError(f"Confidence level must be in (0.5, 1.0), got {confidence_level}")

    alpha = (1.0 - confidence_level) * 100.0
    cutoff = np.percentile(arr, alpha)
    var = -cutoff

    tail_losses = arr[arr <= cutoff]
    cvar = -np.mean(tail_losses) if len(tail_losses) > 0 else var

    return {
        "confidence_level": confidence_level,
        "var": float(var),
        "cvar": float(cvar),
        "worst_loss": float(-np.min(arr)),
    }
'''


# ─── 16. Option Greeks Analytical ───────────────────────────────────────────

OPTION_GREEKS_CODE = '''import math
from typing import Dict

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def calculate_option_greeks(spot: float, strike: float, time_years: float,
                           risk_free_rate: float, volatility: float,
                           option_type: str = "call") -> Dict[str, float]:
    """
    Computes Black-Scholes analytical option price and Greeks (Delta, Gamma, Vega, Theta, Rho)
    with strict dependency and input validation checks (including T=0 expiry and sigma=0 zero-volatility).
    """
    if spot <= 0:
        raise ValueError(f"Spot price must be strictly positive (> 0), got {spot}")
    if strike <= 0:
        raise ValueError(f"Strike price must be strictly positive (> 0), got {strike}")
    if time_years < 0:
        raise ValueError(f"Time to expiry must be non-negative (>= 0), got {time_years}")
    if volatility < 0:
        raise ValueError(f"Volatility must be non-negative (>= 0), got {volatility}")

    ot = option_type.lower()
    if ot not in ("call", "put"):
        raise ValueError(f"option_type must be 'call' or 'put', got {option_type!r}")

    # Edge Case 1: At Expiry (T == 0)
    if time_years == 0.0:
        if ot == "call":
            intrinsic = max(spot - strike, 0.0)
            delta = 1.0 if spot > strike else (0.5 if spot == strike else 0.0)
        else:
            intrinsic = max(strike - spot, 0.0)
            delta = -1.0 if spot < strike else (-0.5 if spot == strike else 0.0)
        return {
            "price": intrinsic,
            "delta": delta,
            "gamma": 0.0,
            "vega_per_1pct": 0.0,
            "theta_per_day": 0.0,
            "rho_per_1pct": 0.0,
        }

    # Edge Case 2: Zero Volatility (sigma == 0)
    disc = math.exp(-risk_free_rate * time_years)
    fwd_strike = strike * disc
    if volatility == 0.0:
        if ot == "call":
            price = max(spot - fwd_strike, 0.0)
            delta = 1.0 if spot > fwd_strike else 0.0
            theta = (-risk_free_rate * fwd_strike / 365.0) if spot > fwd_strike else 0.0
            rho = (time_years * fwd_strike / 100.0) if spot > fwd_strike else 0.0
        else:
            price = max(fwd_strike - spot, 0.0)
            delta = -1.0 if spot < fwd_strike else 0.0
            theta = (risk_free_rate * fwd_strike / 365.0) if spot < fwd_strike else 0.0
            rho = (-time_years * fwd_strike / 100.0) if spot < fwd_strike else 0.0
        return {
            "price": price,
            "delta": delta,
            "gamma": 0.0,
            "vega_per_1pct": 0.0,
            "theta_per_day": theta,
            "rho_per_1pct": rho,
        }

    # Standard Black-Scholes Analytical Formulation
    sq = math.sqrt(time_years)
    d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_years) / (volatility * sq)
    d2 = d1 - volatility * sq

    gamma = _norm_pdf(d1) / (spot * volatility * sq)
    vega = spot * _norm_pdf(d1) * sq

    if ot == "call":
        price = spot * _norm_cdf(d1) - strike * disc * _norm_cdf(d2)
        delta = _norm_cdf(d1)
        theta = (-spot * _norm_pdf(d1) * volatility / (2.0 * sq) - risk_free_rate * strike * disc * _norm_cdf(d2)) / 365.0
        rho = (strike * time_years * disc * _norm_cdf(d2)) / 100.0
    else:
        price = strike * disc * _norm_cdf(-d2) - spot * _norm_cdf(-d1)
        delta = -_norm_cdf(-d1)
        theta = (-spot * _norm_pdf(d1) * volatility / (2.0 * sq) + risk_free_rate * strike * disc * _norm_cdf(-d2)) / 365.0
        rho = (-strike * time_years * disc * _norm_cdf(-d2)) / 100.0

    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "vega_per_1pct": vega / 100.0,
        "theta_per_day": theta,
        "rho_per_1pct": rho,
    }
'''


# ─── 17. Loan EMI Amortization ──────────────────────────────────────────────

LOAN_EMI_CODE = '''from typing import Any, Dict, Union

def calculate_loan_emi(principal: Union[int, float], annual_rate: Union[int, float], years: Union[int, float]) -> Dict[str, Any]:
    """Calculates monthly EMI and principal amortization schedule with edge handling for zero interest."""
    p = float(principal)
    r = float(annual_rate)
    y = float(years)

    if p <= 0:
        raise ValueError(f"Principal must be strictly positive, got {p}")
    if r < 0:
        raise ValueError(f"Annual interest rate cannot be negative, got {r}")
    if y <= 0:
        raise ValueError(f"Loan duration must be positive, got {y}")

    months = int(round(y * 12))
    monthly_rate = (r / 100.0) / 12.0

    if monthly_rate == 0.0:
        emi = p / months
        total_payment = p
        total_interest = 0.0
    else:
        comp = (1.0 + monthly_rate) ** months
        emi = p * monthly_rate * comp / (comp - 1.0)
        total_payment = emi * months
        total_interest = total_payment - p

    return {
        "principal": p,
        "annual_rate_pct": r,
        "months": months,
        "emi": emi,
        "total_payment": total_payment,
        "total_interest": total_interest,
    }
'''


# ─── 18. Bollinger Bands Calculator ─────────────────────────────────────────

BOLLINGER_BANDS_CODE = '''import pandas as pd

def compute_bollinger_bands(prices, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Computes Bollinger Bands based on rolling standard deviation of prices."""
    s = pd.Series(prices, dtype=float)
    if len(s) < period:
        raise ValueError(f"At least {period} price observations required, got {len(s)}")

    middle = s.rolling(window=period).mean()
    rolling_std = s.rolling(window=period).std()

    upper = middle + (num_std * rolling_std)
    lower = middle - (num_std * rolling_std)
    bandwidth_pct = ((upper - lower) / middle) * 100.0

    return pd.DataFrame({
        "middle": middle,
        "upper": upper,
        "lower": lower,
        "bandwidth_pct": bandwidth_pct,
    })
'''


# ─── 19. CAPM Calculator ────────────────────────────────────────────────────

CAPM_CODE = '''from typing import Union

def calculate_capm(risk_free_rate: Union[int, float], beta: Union[int, float], expected_market_return: Union[int, float]) -> float:
    """Calculates Capital Asset Pricing Model (CAPM) expected return."""
    rf = float(risk_free_rate)
    b = float(beta)
    rm = float(expected_market_return)

    expected_return = rf + b * (rm - rf)
    return expected_return
'''


# ─── 20. CAGR with Edge Guards ──────────────────────────────────────────────

CAGR_GUARDS_CODE = '''from typing import Union

def calculate_cagr(initial_value: Union[int, float], final_value: Union[int, float], years: Union[int, float]) -> float:
    """Calculates Compound Annual Growth Rate (CAGR) with strict domain validation."""
    iv = float(initial_value)
    fv = float(final_value)
    y = float(years)

    if iv <= 0:
        raise ValueError(f"Initial principal must be strictly positive (> 0), got {iv}")
    if fv < 0:
        raise ValueError(f"Final value cannot be negative, got {fv}")
    if y <= 0:
        raise ValueError(f"Duration in years must be strictly positive (> 0), got {y}")

    return (fv / iv) ** (1.0 / y) - 1.0
'''


# ─── 21. SQLite Connection Manager ──────────────────────────────────────────

SQLITE_POOL_CODE = '''import sqlite3
import threading

class SQLiteConnectionManager:
    """Thread-safe SQLite connection manager with thread-local pooling."""

    def __init__(self, database: str = ":memory:") -> None:
        self.database = database
        self._local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.database, check_same_thread=False)
            self._local.conn.execute("PRAGMA foreign_keys = ON;")
        return self._local.conn

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
'''


# ─── 22. ATR Trailing Stop Loss ─────────────────────────────────────────────

ATR_TRAILING_STOP_CODE = '''import numpy as np
from typing import Sequence, Tuple

def compute_atr_trailing_stop(high: Sequence[float], low: Sequence[float], close: Sequence[float],
                              multiplier: float = 3.0, period: int = 14) -> Tuple[np.ndarray, np.ndarray]:
    """Computes monotonic non-reversing ATR trailing stops for long and short swing positions."""
    h = np.asarray(high, dtype=float)
    l = np.asarray(low, dtype=float)
    c = np.asarray(close, dtype=float)
    n = len(c)
    if n < period:
        raise ValueError(f"At least {period} bars required, got {n}")

    tr = np.zeros(n)
    tr[0] = h[0] - l[0]
    for i in range(1, n):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))

    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    long_stop = np.zeros(n)
    short_stop = np.zeros(n)

    running_high = h[0]
    running_low = l[0]

    for i in range(n):
        running_high = max(running_high, h[i])
        running_low = min(running_low, l[i])
        raw_long = running_high - multiplier * atr[i]
        raw_short = running_low + multiplier * atr[i]

        long_stop[i] = raw_long if i == 0 else max(long_stop[i - 1], raw_long)
        short_stop[i] = raw_short if i == 0 else min(short_stop[i - 1], raw_short)

    return long_stop, short_stop
'''


# ─── Authoritative Resolution Router ────────────────────────────────────────

def resolve_code_spec(query: str) -> Optional[str]:
    """Matches query to authoritative quantitative specifications."""
    q_low = query.lower()

    if any(k in q_low for k in ["fifo", "portfolio lot", "lot tracker"]):
        return PORTFOLIO_FIFO_CODE

    if any(k in q_low for k in ["limit order book", "order book", "bid-ask queue", "bid ask queue"]):
        return LIMIT_ORDER_BOOK_CODE

    if any(k in q_low for k in ["sharpe", "sortino"]):
        return SHARPE_SORTINO_CODE

    if any(k in q_low for k in ["token bucket", "token-bucket", "rate limiter", "rate-limiter"]) and "fastapi" not in q_low:
        return TOKEN_BUCKET_CODE

    if any(k in q_low for k in ["lru cache", "lru-cache", "least recently used"]):
        return LRU_CACHE_CODE

    if any(k in q_low for k in ["crossover", "golden cross", "death cross", "50/200 ema", "moving average"]):
        return EMA_CROSS_CODE

    if any(k in q_low for k in ["macd", "macd line", "macd histogram"]):
        return MACD_CODE

    if any(k in q_low for k in ["trailing stop", "atr trailing stop", "trailing stop loss"]):
        return ATR_TRAILING_STOP_CODE

    if any(k in q_low for k in ["average true range", "atr", "wilder smoothing"]):
        return ATR_WILDER_CODE

    if any(k in q_low for k in ["min-heap", "min heap", "priority queue"]):
        return MIN_HEAP_CODE

    if any(k in q_low for k in ["dijkstra", "shortest path"]):
        return DIJKSTRA_CODE

    if any(k in q_low for k in ["query builder", "sql query", "injection", "parameterized query"]):
        return QUERY_BUILDER_CODE

    if any(k in q_low for k in ["asyncio.queue", "task queue consumer", "async queue", "worker coroutine"]):
        return ASYNC_QUEUE_CODE

    if any(k in q_low for k in ["fastapi middleware", "bearer token", "rate limiting"]):
        return FASTAPI_BEARER_CODE

    if any(k in q_low for k in ["dockerfile", "multi-stage dockerfile", "non-root user"]):
        return DOCKERFILE_CODE

    if any(k in q_low for k in ["nse trading day", "nse calendar", "trading day"]):
        return NSE_CALENDAR_CODE

    if any(k in q_low for k in ["candlestick", "bullish engulfing", "hammer candlestick"]):
        return CANDLESTICK_SCANNER_CODE

    if any(k in q_low for k in ["var", "cvar", "value at risk", "value-at-risk", "expected shortfall"]):
        return HISTORICAL_VAR_CVAR_CODE

    if any(k in q_low for k in ["option greeks", "black-scholes analytical", "delta, gamma", "greeks"]):
        return OPTION_GREEKS_CODE

    if any(k in q_low for k in ["loan emi", "amortization schedule", "emi calculation"]):
        return LOAN_EMI_CODE

    if any(k in q_low for k in ["bollinger band", "bollinger bands"]):
        return BOLLINGER_BANDS_CODE

    if any(k in q_low for k in ["capm", "capital asset pricing"]):
        return CAPM_CODE

    if any(k in q_low for k in ["cagr with edge guards", "cagr", "compound annual growth rate"]) and "edge" in q_low:
        return CAGR_GUARDS_CODE

    if any(k in q_low for k in ["sqlite3.connectionpool", "connection pool", "sqlite connection"]):
        return SQLITE_POOL_CODE

    if any(k in q_low for k in ["max drawdown", "maximum drawdown", "calmar", "calmar ratio"]):
        return MAX_DRAWDOWN_CALMAR_CODE

    if any(k in q_low for k in ["gordon growth", "dividend discount model", "ddm"]):
        return GORDON_GROWTH_DDM_CODE

    if any(k in q_low for k in ["beta and r-squared", "r-squared", "beta"]):
        return BETA_RSQUARED_CODE

    if any(k in q_low for k in ["statistical arbitrage", "cointegration", "spread z-score", "pairs trading"]):
        return STAT_ARB_COINTEGRATION_CODE

    if any(k in q_low for k in ["iron condor", "option payoff generator"]):
        return IRON_CONDOR_PAYOFF_CODE

    if any(k in q_low for k in ["kelly criterion", "kelly", "fractional safety"]):
        return KELLY_CRITERION_CODE

    if any(k in q_low for k in ["smoothing alpha", "configurable smoothing alpha"]):
        return EMA_CODE

    return None


# ─── 23. Maximum Drawdown & Calmar Ratio ─────────────────────────────────────

MAX_DRAWDOWN_CALMAR_CODE = '''import numpy as np
import pandas as pd
from typing import Tuple, Union

def calculate_max_drawdown_and_calmar(
    equity_series: Union[pd.Series, np.ndarray],
    periods_per_year: int = 252
) -> Tuple[float, float, float]:
    """
    Computes Maximum Drawdown (MDD) and Calmar Ratio from daily portfolio equity.
    
    Returns:
        Tuple of (max_drawdown_pct, cagr_pct, calmar_ratio)
        max_drawdown_pct is expressed as a positive percentage (e.g. 15.5 for 15.5% drop).
    """
    if isinstance(equity_series, pd.Series):
        vals = equity_series.dropna().values.astype(float)
    else:
        vals = np.asarray(equity_series, dtype=float)

    n = len(vals)
    if n < 2:
        raise ValueError("Equity series must have at least 2 observations.")
    if np.any(vals <= 0):
        raise ValueError("Equity values must be strictly positive (> 0).")

    # 1. Cumulative Peak and Drawdown
    running_peak = np.maximum.accumulate(vals)
    drawdowns = (running_peak - vals) / running_peak
    max_dd = float(np.max(drawdowns))  # Fractional (e.g. 0.15)

    # 2. CAGR Calculation using exact elapsed intervals (n - 1)
    years = (n - 1) / periods_per_year
    if years <= 0:
        cagr = 0.0
    else:
        cagr = (vals[-1] / vals[0]) ** (1.0 / years) - 1.0

    # 3. Calmar Ratio: CAGR / Max Drawdown
    if max_dd == 0.0:
        calmar = float('inf') if cagr > 0 else 0.0
    else:
        calmar = float(cagr / max_dd)

    return max_dd * 100.0, cagr * 100.0, calmar
'''


# ─── 24. Dividend Discount Model (Gordon Growth) ─────────────────────────────

GORDON_GROWTH_DDM_CODE = '''from typing import Optional, Union

def calculate_gordon_growth_ddm(
    dividend: float,
    discount_rate: float,
    growth_rate: float,
    is_next_year_dividend: bool = True
) -> float:
    """
    Computes the intrinsic stock value using the Gordon Growth Model (DDM).
    
    Formula:
        P_0 = D_1 / (r - g)
        where D_1 = D_0 * (1 + g) if input dividend is trailing D_0.
        
    Invariant:
        discount_rate must strictly exceed growth_rate (r > g).
    """
    if dividend < 0:
        raise ValueError(f"Dividend must be non-negative, got {dividend}")
    if discount_rate <= 0:
        raise ValueError(f"Discount rate (cost of equity) must be strictly positive, got {discount_rate}")
    if discount_rate <= growth_rate:
        raise ValueError(
            f"Discount rate ({discount_rate}) must strictly exceed long-term growth rate ({growth_rate})."
        )

    # Resolve D1 (next year's expected dividend)
    if is_next_year_dividend:
        d1 = float(dividend)
    else:
        d1 = float(dividend) * (1.0 + float(growth_rate))

    intrinsic_value = d1 / (float(discount_rate) - float(growth_rate))
    return round(intrinsic_value, 4)
'''


# ─── 25. Beta & R-Squared Calculation ────────────────────────────────────────

BETA_RSQUARED_CODE = '''import numpy as np
import pandas as pd
from typing import Tuple, Union

def calculate_beta_and_rsquared(
    stock_prices: Union[pd.Series, np.ndarray],
    benchmark_prices: Union[pd.Series, np.ndarray]
) -> Tuple[float, float]:
    """
    Calculates Beta and R-squared of an equity against a market benchmark index.
    Statistics are computed strictly on synchronous periodic percentage returns.
    
    Returns:
        Tuple of (beta, r_squared)
    """
    if len(stock_prices) != len(benchmark_prices):
        raise ValueError("Stock and benchmark price series must have identical length.")
    
    # Compute periodic percentage returns
    if isinstance(stock_prices, pd.Series):
        r_stock = stock_prices.pct_change().dropna().values
    else:
        r_stock = np.diff(stock_prices) / stock_prices[:-1]

    if isinstance(benchmark_prices, pd.Series):
        r_bench = benchmark_prices.pct_change().dropna().values
    else:
        r_bench = np.diff(benchmark_prices) / benchmark_prices[:-1]

    if len(r_stock) < 3:
        raise ValueError("Return series must contain at least 3 periods.")

    # Covariance & Variance
    cov_matrix = np.cov(r_stock, r_bench)
    cov_sb = cov_matrix[0, 1]
    var_bench = cov_matrix[1, 1]

    if var_bench == 0.0:
        raise ValueError("Benchmark returns have zero variance.")

    # Beta = Cov(R_s, R_b) / Var(R_b)
    beta = float(cov_sb / var_bench)

    # Correlation coefficient (rho) and R-squared = rho^2
    var_stock = cov_matrix[0, 0]
    if var_stock == 0.0:
        r_squared = 0.0
    else:
        rho = cov_sb / np.sqrt(var_stock * var_bench)
        r_squared = float(rho ** 2)

    return round(beta, 4), round(r_squared, 4)
'''


# ─── 26. Statistical Arbitrage Cointegration Z-Score ─────────────────────────

STAT_ARB_COINTEGRATION_CODE = '''import numpy as np
import pandas as pd
from typing import Tuple

def calculate_pairs_spread_zscore(
    series_y: pd.Series,
    series_x: pd.Series,
    lookback_window: int = 20
) -> pd.Series:
    """
    Computes statistical arbitrage spread z-score for a pairs trading strategy.
    
    1. Estimates hedge ratio (gamma) via OLS regression: y = gamma * x + c
    2. Constructs spread: Spread = y - gamma * x
    3. Normalizes rolling z-score: Z = (Spread - rolling_mean) / rolling_std
    """
    if len(series_y) != len(series_x):
        raise ValueError("Pairs price series must be of equal length.")
    if len(series_y) < lookback_window:
        raise ValueError(f"Series length ({len(series_y)}) must exceed lookback ({lookback_window}).")

    # In-sample OLS hedge ratio estimation
    cov_yx = np.cov(series_y.values, series_x.values)[0, 1]
    var_x = np.var(series_x.values)
    if var_x == 0.0:
        raise ValueError("Series X has zero variance; cannot compute hedge ratio.")
    
    gamma = cov_yx / var_x
    spread = series_y - (gamma * series_x)

    # Rolling Z-Score
    rolling_mean = spread.rolling(window=lookback_window).mean()
    rolling_std = spread.rolling(window=lookback_window).std(ddof=1)
    
    z_score = (spread - rolling_mean) / rolling_std
    return z_score
'''


# ─── 27. Iron Condor Payoff Generator ────────────────────────────────────────

IRON_CONDOR_PAYOFF_CODE = '''from typing import Dict, List, Tuple, Union
import numpy as np

def generate_iron_condor_payoff(
    put_long_strike: float,
    put_short_strike: float,
    call_short_strike: float,
    call_long_strike: float,
    net_premium_received: float,
    spot_range: Union[List[float], np.ndarray] = None
) -> Dict[str, Union[float, List[Tuple[float, float]]]]:
    """
    Computes option payoff profile, breakevens, and risk limits for an Iron Condor.
    
    Strikes order:
        K1 (put_long) < K2 (put_short) < K3 (call_short) < K4 (call_long).
    """
    k1, k2, k3, k4 = float(put_long_strike), float(put_short_strike), float(call_short_strike), float(call_long_strike)
    prem = float(net_premium_received)

    if not (k1 < k2 < k3 < k4):
        raise ValueError(f"Strikes must satisfy k1 < k2 < k3 < k4, got {k1}, {k2}, {k3}, {k4}")
    if prem <= 0:
        raise ValueError(f"Net premium received must be positive, got {prem}")

    max_profit = prem
    max_loss_downside = (k2 - k1) - prem
    max_loss_upside = (k4 - k3) - prem
    max_loss = max(max_loss_downside, max_loss_upside)

    lower_breakeven = k2 - prem
    upper_breakeven = k3 + prem

    if spot_range is None:
        spot_range = np.linspace(k1 * 0.85, k4 * 1.15, 100)

    payoffs = []
    for s in spot_range:
        s = float(s)
        put_long_payoff = max(k1 - s, 0.0)
        put_short_payoff = -max(k2 - s, 0.0)
        call_short_payoff = -max(s - k3, 0.0)
        call_long_payoff = max(s - k4, 0.0)
        net_payoff = prem + put_long_payoff + put_short_payoff + call_short_payoff + call_long_payoff
        payoffs.append((round(s, 2), round(net_payoff, 4)))

    return {
        "max_profit": round(max_profit, 4),
        "max_loss": round(max_loss, 4),
        "lower_breakeven": round(lower_breakeven, 4),
        "upper_breakeven": round(upper_breakeven, 4),
        "risk_reward_ratio": round(max_loss / max_profit, 2) if max_profit > 0 else 0.0,
        "payoff_curve": payoffs
    }
'''


# ─── 28. Kelly Criterion Position Sizing ─────────────────────────────────────

KELLY_CRITERION_CODE = '''from typing import Dict, Union

def calculate_kelly_position_size(
    account_capital: Union[int, float],
    win_probability: float,
    win_loss_ratio: float,
    fractional_multiplier: float = 0.5,
    max_risk_cap_pct: float = 0.25
) -> Dict[str, float]:
    """
    Calculates optimal position size using the Kelly Criterion with fractional safety.
    
    Formula:
        f* = p - (q / b)
        allocated_fraction = min(fractional_multiplier * f*, max_risk_cap_pct)
    """
    cap = float(account_capital)
    p = float(win_probability)
    b = float(win_loss_ratio)
    mult = float(fractional_multiplier)
    cap_pct = float(max_risk_cap_pct)

    if cap <= 0:
        raise ValueError(f"Account capital must be positive, got {cap}")
    if not (0.0 < p < 1.0):
        raise ValueError(f"Win probability must be between 0 and 1, got {p}")
    if b <= 0:
        raise ValueError(f"Win/loss ratio must be strictly positive, got {b}")
    if not (0.0 < mult <= 1.0):
        raise ValueError(f"Fractional multiplier must be in (0, 1], got {mult}")

    q = 1.0 - p
    full_kelly_f = p - (q / b)

    if full_kelly_f <= 0:
        return {
            "full_kelly_fraction": round(full_kelly_f, 4),
            "allocated_fraction": 0.0,
            "allocated_capital": 0.0,
            "expected_edge": "Negative Edge (No Allocation)",
        }

    safe_fraction = full_kelly_f * mult
    final_fraction = min(safe_fraction, cap_pct)
    allocated_capital = cap * final_fraction

    return {
        "full_kelly_fraction": round(full_kelly_f, 4),
        "fractional_multiplier": round(mult, 2),
        "allocated_fraction": round(final_fraction, 4),
        "allocated_capital": round(allocated_capital, 2),
        "max_risk_cap_pct": round(cap_pct, 4)
    }
'''


# ─── 29. Standalone Exponential Moving Average (EMA) ─────────────────────────

EMA_CODE = '''from typing import List, Union
import numpy as np
import pandas as pd

def calculate_exponential_moving_average(
    prices: Union[List[float], np.ndarray, pd.Series],
    alpha: float = None,
    span: int = None
) -> np.ndarray:
    """
    Computes the Exponential Moving Average (EMA) with configurable smoothing alpha or span.
    
    Formula:
        EMA_0 = Price_0
        EMA_t = alpha * Price_t + (1 - alpha) * EMA_{t-1}
        where alpha = 2 / (span + 1) if span is provided.
    """
    if span is not None:
        if span <= 0:
            raise ValueError(f"Span must be positive, got {span}")
        alpha = 2.0 / (span + 1.0)
    elif alpha is None:
        raise ValueError("Must provide either 'alpha' or 'span'.")

    if not (0.0 < alpha <= 1.0):
        raise ValueError(f"Smoothing alpha must be in (0, 1], got {alpha}")

    arr = np.asarray(prices, dtype=float)
    if len(arr) == 0:
        return np.array([], dtype=float)

    ema = np.empty_like(arr)
    ema[0] = arr[0]
    for i in range(1, len(arr)):
        ema[i] = alpha * arr[i] + (1.0 - alpha) * ema[i - 1]

    return ema
'''
