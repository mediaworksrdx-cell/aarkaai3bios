"""
AARKAAI — Quantitative Trading & Options Strategy Engine.

Provides exact payoff models, mathematical formulas, and technical divergence
definitions for systematic trading strategies.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


def rsi_divergence_analysis() -> str:
    """Returns the textbook technical analysis specification for RSI divergence."""
    return """### RSI Divergence: Bullish vs Bearish Mechanics & Confirmation

The Relative Strength Index (RSI, 14-period) detects momentum shifts and divergences against underlying asset price action:

#### 1. Regular Bullish Divergence (Reversal from Downside)
* **Condition:** Price records a **Lower Low (LL)**, while RSI records a **Higher Low (HL)**.
* **Mechanics:** While price registers a new low due to residual inertia, the velocity and negative momentum of selling have diminished. Bulls are absorbing supply at higher relative momentum levels.
* **Confirmation:** RSI crosses above 30 out of oversold territory, followed by a candle closing above the divergence pivot high.

#### 2. Regular Bearish Divergence (Reversal from Upside)
* **Condition:** Price records a **Higher High (HH)**, while RSI records a **Lower High (LH)**.
* **Mechanics:** While price reaches a fresh peak, buying momentum is decelerating. Fewer buyers participate at higher price levels, signaling buyer exhaustion.
* **Confirmation:** RSI crosses below 70 out of overbought territory, accompanied by a breakdown below recent swing lows.

#### 3. Hidden Divergences (Trend Continuation)
* **Hidden Bullish:** Price makes a **Higher Low (HL)** while RSI makes a **Lower Low (LL)** (confirms strong uptrend continuation).
* **Hidden Bearish:** Price makes a **Lower High (LH)** while RSI makes a **Higher High (HH)** (confirms strong downtrend continuation)."""


def bull_call_spread_payoff() -> str:
    """Returns the exact payoff structure and formulas for a Bull Call Spread."""
    return """### Bull Call Spread: Payoff Structure, Maximum Gain & Maximum Loss

A Bull Call Spread is a vertical debit spread deployed when a trader is moderately bullish on the underlying asset.

#### 1. Construction
* **Leg 1 (Long Call):** Buy 1 **Lower-Strike Call** ($K_1$) at premium $C_1$.
* **Leg 2 (Short Call):** Sell 1 **Higher-Strike Call** ($K_2$) at premium $C_2$, where $K_2 > K_1$ and $C_1 > C_2$.
* **Net Debit Paid:** $D = C_1 - C_2$ per share.

#### 2. Payoff Profile & Boundaries
* **Maximum Loss:**
  $$\\text{Max Loss} = \\text{Net Debit Paid} = C_1 - C_2$$
  *(Occurs when underlying price $S_T \\le K_1$ at expiration; both calls expire worthless).*
* **Maximum Gain:**
  $$\\text{Max Gain} = (K_2 - K_1) - \\text{Net Debit} = (K_2 - K_1) - (C_1 - C_2)$$
  *(Occurs when underlying price $S_T \\ge K_2$ at expiration; both calls are in-the-money).*
* **Breakeven Point:**
  $$\\text{Breakeven} = K_1 + \\text{Net Debit} = K_1 + (C_1 - C_2)$$

#### 3. Trade Characteristics
* Defined Risk / Defined Reward structure.
* Vega & Theta Neutrality: Short call partially offsets time-decay and implied volatility crush."""


def bear_put_spread_payoff() -> str:
    """Returns the exact payoff structure and formulas for a Bear Put Spread."""
    return """### Bear Put Spread: Payoff Structure & Deployment Criteria

A Bear Put Spread is a vertical debit spread deployed when a trader anticipates moderate downward price movement with defined downside risk.

#### 1. Construction
* **Leg 1 (Long Put):** Buy 1 **Higher-Strike Put** ($K_2$) at premium $P_2$.
* **Leg 2 (Short Put):** Sell 1 **Lower-Strike Put** ($K_1$) at premium $P_1$, where $K_2 > K_1$ and $P_2 > P_1$.
* **Net Debit Paid:** $D = P_2 - P_1$ per share.

#### 2. Payoff Profile & Boundaries
* **Maximum Gain:**
  $$\\text{Max Gain} = (K_2 - K_1) - \\text{Net Debit} = (K_2 - K_1) - (P_2 - P_1)$$
  *(Occurs when underlying price $S_T \\le K_1$ at expiration; both puts are in-the-money).*
* **Maximum Loss:**
  $$\\text{Max Loss} = \\text{Net Debit Paid} = P_2 - P_1$$
  *(Occurs when underlying price $S_T \\ge K_2$ at expiration; both puts expire worthless).*
* **Breakeven Point:**
  $$\\text{Breakeven} = K_2 - \\text{Net Debit} = K_2 - (P_2 - P_1)$$

#### 3. Deployment Window
Deploy when technical breakdown confirms lower highs, IV is moderate, and short put strike ($K_1$) aligns with key support."""


def iron_condor_payoff() -> str:
    """Returns the exact payoff structure and formulas for an Iron Condor."""
    return """### Iron Condor: Payoff Structure & Market Mechanics

An Iron Condor is a non-directional, 4-legged options strategy designed to profit from range-bound markets and declining volatility (theta decay).

#### 1. Strike Ordering & Construction
The strategy requires 4 distinct strikes with the strict mathematical ordering:
$$K_1 < K_2 < K_3 < K_4$$

* **Bear Put Spread (Downside Wing):**
  - Buy 1 OTM Put at Strike $K_1$ (Protection)
  - Sell 1 OTM Put at Strike $K_2$
* **Bull Call Spread (Upside Wing):**
  - Sell 1 OTM Call at Strike $K_3$
  - Buy 1 OTM Call at Strike $K_4$ (Protection)

#### 2. Payoff Profile & Returns
* **Net Credit Collected:**
  $$\\text{Net Credit} = (P_2 - P_1) + (C_3 - C_4)$$
* **Maximum Profit:**
  $$\\text{Max Profit} = \\text{Net Credit}$$
  *(Occurs when $K_2 \\le S_T \\le K_3$ at expiration; all 4 options expire worthless).*
* **Maximum Loss:**
  $$\\text{Max Loss} = \\text{Wing Width} - \\text{Net Credit} = (K_2 - K_1) - \\text{Net Credit}$$
* **Breakeven Points:**
  - Lower Breakeven: $K_2 - \\text{Net Credit}$
  - Upper Breakeven: $K_3 + \\text{Net Credit}$"""


def resolve_trading_strategy(query: str) -> Optional[str]:
    """Detects standard trading options and technical divergence queries."""
    q_low = query.lower()
    if "rsi" in q_low and "divergence" in q_low:
        return rsi_divergence_analysis()
    if "bull call" in q_low or ("bull" in q_low and "call spread" in q_low):
        return bull_call_spread_payoff()
    if "bear put" in q_low or ("bear" in q_low and "put spread" in q_low):
        return bear_put_spread_payoff()
    if "iron condor" in q_low:
        return iron_condor_payoff()
    return None
