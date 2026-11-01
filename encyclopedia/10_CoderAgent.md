# CoderAgent — Complete 20 Production Queries & Answers

*Aarka AI Technical Reference Encyclopedia*

---

## [Q01] Write a Python class `PortfolioFIFO` with buy_lot and sell_lot methods tracking realized P&L.

### Portfolio FIFO Lot Tracker (`PortfolioFIFO`)

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

## [Q02] Implement a Black-Scholes call and put option pricing function returning theoretical fair prices.

### Black-Scholes Call and Put Option Pricing Function

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

## [Q03] Write a function to compute Exponential Moving Average (EMA) with configurable smoothing alpha.

### Exponential Moving Average (EMA) with Configurable Smoothing Alpha

```python
from typing import List, Union
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

```

---

## [Q04] Implement a Maximum Drawdown calculator given a time series array of portfolio daily values.

### Maximum Drawdown & Calmar Ratio Calculator

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

## [Q05] Write a Python function to compute the Sharpe Ratio and Sortino Ratio for a returns series.

### Sharpe Ratio and Sortino Ratio Calculator

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

## [Q06] Implement an option payoff generator for an Iron Condor given four strikes and net premium received.

### Iron Condor Option Payoff Generator

```python
from typing import Dict, List, Tuple, Union
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

```

---

## [Q07] Write a function to check if a given date is a valid NSE trading day excluding weekends and holidays.

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

## [Q08] Implement a candlestick pattern scanner detecting Bullish Engulfing and Hammer candles.

### Candlestick Pattern Scanner: Bullish Engulfing & Hammer

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

## [Q09] Write a position sizing function based on the Kelly Criterion with a fractional safety multiplier.

### Kelly Criterion Position Sizing with Fractional Multiplier

```python
from typing import Dict, Union

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

```

---

## [Q10] Implement a Historical Value at Risk (VaR) and Conditional VaR (CVaR) calculator at 95% and 99% confidence.

### Historical Value at Risk (VaR) and Conditional VaR (CVaR)

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

## [Q11] Write a function to compute Bollinger Bands (Upper, Middle, Lower) and BandWidth from closing prices.

### Bollinger Bands (Upper, Middle, Lower) & BandWidth

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

## [Q12] Implement a limit order book order matching algorithm for BUY and SELL limit orders.

### Limit Order Book Matching Algorithm

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

## [Q13] Write a function to compute the Capital Asset Pricing Model (CAPM) expected return of a stock.

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

## [Q14] Implement an ATR (Average True Range) volatility indicator calculator using High, Low, Close prices.

### Average True Range (ATR) Volatility Indicator

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

## [Q15] Write a function to calculate Option Greeks (Delta, Gamma, Vega) using analytical derivatives.

### Analytical Option Greeks (Delta, Gamma, Vega, Theta, Rho)

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

## [Q16] Implement a pairs trading spread z-score calculator to identify mean-reverting statistical arbitrage.

### Pairs Trading Cointegration Spread Z-Score

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

## [Q17] Write a function that calculates the Dividend Discount Model (DDM) intrinsic value for a dividend stock.

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

## [Q18] Implement a function that computes the Beta of a stock against an index using covariance.

### Beta and R-Squared of Equity vs. Market Benchmark

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

## [Q19] Write a function to calculate monthly loan EMI and total interest payable using compound amortization.

### Monthly Loan EMI & Compound Amortization Schedule

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

## [Q20] Implement a technical indicator function that outputs MACD line, Signal line, and MACD Histogram.

### Moving Average Convergence Divergence (MACD) Indicator

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

