# AarkaCoderPipeline — Complete 20 Production Queries & Answers

*Aarka AI Technical Reference Encyclopedia*

---

## [Q01] Write a Python FIFO stock portfolio lot tracker class with realize_pnl and buy_lot methods.

### Portfolio FIFO Lot Tracker

```python
import collections
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

```

---

## [Q02] Write a Python function to compute Black-Scholes call option price and analytical Delta.

### Black-Scholes Call Price & Analytical Delta

```python
import math
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

```

---

## [Q03] Write a Python function to calculate Maximum Drawdown and Calmar Ratio from daily equity series.

### Maximum Drawdown & Calmar Ratio from Daily Equity

```python
import numpy as np
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

```

---

## [Q04] Write a Python script to compute Exponential Moving Average (EMA) and 50/200 EMA crossovers.

### Exponential Moving Average (EMA) & 50/200 Crossovers

```python
import pandas as pd

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

```

---

## [Q05] Write a Python class for a limit order book bid-ask queue with market order matching.

### Limit Order Book Bid-Ask Queue & Market Order Matching

```python
from dataclasses import dataclass, field
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

```

---

## [Q06] Write a Python function to calculate Historical Value at Risk (VaR) at 99% confidence level.

### Historical Value at Risk (VaR) at 99% Confidence

```python
import numpy as np
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

```

---

## [Q07] Write a Python function to compute the Sharpe Ratio and Sortino Ratio for portfolio returns.

### Sharpe Ratio & Sortino Ratio for Portfolio Returns

```python
import math
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

```

---

## [Q08] Write a Python script to detect candlestick Morning Star and Evening Star reversal patterns.

### Candlestick Pattern Scanner: Morning Star & Reversals

```python
import pandas as pd

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

```

---

## [Q09] Write a Python function to compute Bollinger Bands (Upper, Lower) and BandWidth percentage.

### Bollinger Bands (Upper, Lower) & BandWidth Percentage

```python
import pandas as pd

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

```

---

## [Q10] Write a Python class implementing a Token-Bucket Rate Limiter with thread-safe acquisition.

### Token-Bucket Rate Limiter with Thread-Safe Acquisition

```python
import threading
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

```

---

## [Q11] Write a Python function to calculate the Capital Asset Pricing Model (CAPM) expected return.

### Capital Asset Pricing Model (CAPM) Expected Return

```python
from typing import Union

def calculate_capm(risk_free_rate: Union[int, float], beta: Union[int, float], expected_market_return: Union[int, float]) -> float:
    """Calculates Capital Asset Pricing Model (CAPM) expected return."""
    rf = float(risk_free_rate)
    b = float(beta)
    rm = float(expected_market_return)

    expected_return = rf + b * (rm - rf)
    return expected_return

```

---

## [Q12] Write a Python script to compute Average True Range (ATR) with 14-period Wilder smoothing.

### Average True Range (ATR) with 14-Period Wilder Smoothing

```python
import numpy as np

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

```

---

## [Q13] Write a Python function to calculate monthly loan EMI and principal amortization schedule.

### Monthly Loan EMI & Principal Amortization Schedule

```python
from typing import Any, Dict, Union

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

```

---

## [Q14] Write a Python function to check whether a given date is a valid NSE trading day.

### Valid NSE Trading Day Calendar Check

```python
from datetime import date, datetime
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

```

---

## [Q15] Write a Python function to compute MACD line, 9-day Signal line, and MACD Histogram.

### MACD Line, 9-Day Signal Line & Histogram

```python
import pandas as pd

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

```

---

## [Q16] Write a Python script to compute the Dividend Discount Model (Gordon Growth) intrinsic value.

### Dividend Discount Model (Gordon Growth DDM) Intrinsic Value

```python
from typing import Optional, Union

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

```

---

## [Q17] Write a Python class implementing a thread-safe LRU Cache with O(1) get and put.

### Thread-Safe LRU Cache with O(1) Get and Put

```python
import collections
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

```

---

## [Q18] Write a Python function to calculate Beta and R-squared of an equity against a market index.

### Beta and R-Squared of Equity against Market Index

```python
import numpy as np
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

```

---

## [Q19] Write a Python script to compute statistical arbitrage spread z-score for cointegrated pairs.

### Statistical Arbitrage Spread Z-Score for Cointegrated Pairs

```python
import numpy as np
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

```

---

## [Q20] Write a Python function to calculate Compound Annual Growth Rate (CAGR) with edge guards.

### Compound Annual Growth Rate (CAGR) with Edge Guards

```python
from typing import Union

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

```

---

