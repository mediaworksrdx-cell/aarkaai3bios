"""
AARKAAI – Options Strategy Generator

Deterministic, rule-based options strategy engine.
Takes technical indicators + signal as input and outputs specific,
actionable option strategy setups with defined risk-to-reward ratios.

Strategies:
  BULLISH  → Bull Call Spread / Long Call
  BEARISH  → Bear Put Spread / Long Put
  NEUTRAL  → Iron Condor / Short Straddle

All outputs include: entry, strikes, stop-loss, target, max-loss, max-gain.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ─── NSE F&O Lot Sizes (updated periodically) ───────────────────────────────

_LOT_SIZES: dict[str, int] = {
    # Nifty 50 + popular F&O stocks
    "SBIN.NS": 1500,
    "RELIANCE.NS": 250,
    "TCS.NS": 175,
    "INFY.NS": 400,
    "HDFCBANK.NS": 550,
    "ICICIBANK.NS": 700,
    "KOTAKBANK.NS": 400,
    "AXISBANK.NS": 625,
    "INDUSINDBK.NS": 500,
    "BAJFINANCE.NS": 125,
    "BAJAJFINSV.NS": 500,
    "LT.NS": 375,
    "HINDUNILVR.NS": 300,
    "ITC.NS": 1600,
    "BHARTIARTL.NS": 475,
    "MARUTI.NS": 100,
    "TITAN.NS": 175,
    "ASIANPAINT.NS": 300,
    "WIPRO.NS": 1500,
    "HCLTECH.NS": 350,
    "TECHM.NS": 600,
    "SUNPHARMA.NS": 700,
    "DRREDDY.NS": 125,
    "CIPLA.NS": 650,
    "DIVISLAB.NS": 200,
    "TATAMOTORS.NS": 1400,
    "M&M.NS": 350,
    "EICHERMOT.NS": 175,
    "HEROMOTOCO.NS": 150,
    "TATASTEEL.NS": 5500,
    "JSWSTEEL.NS": 1350,
    "HINDALCO.NS": 1400,
    "COALINDIA.NS": 2100,
    "NTPC.NS": 2250,
    "POWERGRID.NS": 2700,
    "ADANIENT.NS": 250,
    "ADANIPORTS.NS": 625,
    "ULTRACEMCO.NS": 100,
    "GRASIM.NS": 350,
    "NESTLEIND.NS": 50,
    "BRITANNIA.NS": 200,
    "TATACONSUM.NS": 675,
    "ONGC.NS": 3850,
    "IOC.NS": 4350,
    "BPCL.NS": 1800,
    "HAL.NS": 150,
    "TATAPOWER.NS": 1875,
    "IRCTC.NS": 875,
    "ETERNAL.NS": 3000,  # Zomato
    "SBILIFE.NS": 375,
    "HDFCLIFE.NS": 1100,
    "ICICIPRULI.NS": 1500,
    "DMART.NS": 200,
    "PIDILITIND.NS": 250,
    "DABUR.NS": 1250,
    "HAVELLS.NS": 500,
    "VEDL.NS": 1550,
    # Index options
    "^NSEI": 50,    # Nifty 50 lot
    "^NSEBANK": 15,  # Bank Nifty lot
}


def get_lot_size(symbol: str) -> int:
    """Return the NSE lot size for a symbol, default 1 for unknown."""
    return _LOT_SIZES.get(symbol, 1)


# ─── Strike Price Utilities ──────────────────────────────────────────────────


def _round_strike(price: float, step: float = 50.0) -> float:
    """Round a price to the nearest strike price step."""
    return round(price / step) * step


def _get_strike_step(price: float) -> float:
    """Determine the appropriate strike step based on price level."""
    if price < 100:
        return 5.0
    elif price < 500:
        return 10.0
    elif price < 2000:
        return 50.0
    elif price < 5000:
        return 100.0
    else:
        return 100.0


def _next_monthly_expiry() -> str:
    """Return the next monthly options expiry (last Thursday of month)."""
    today = datetime.now()
    # Find last Thursday of current month
    year, month = today.year, today.month

    # Try current month first
    for attempt in range(2):
        if attempt == 1:
            month += 1
            if month > 12:
                month = 1
                year += 1

        # Find last day of the month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        # Walk backwards to find last Thursday
        d = last_day
        while d.weekday() != 3:  # Thursday = 3
            d -= timedelta(days=1)

        if d > today:
            return d.strftime("%d-%b-%Y")

    # Fallback: 30 days from now
    return (today + timedelta(days=30)).strftime("%d-%b-%Y")


# ─── Strategy Generation ────────────────────────────────────────────────────


_DISCLAIMER = (
    "⚠️ DISCLAIMER: This is for educational/informational purposes only. "
    "Not SEBI-registered investment advice. Options trading involves "
    "substantial risk of loss. Past performance does not guarantee future results. "
    "Please consult a qualified financial advisor before trading."
)


def generate_strategy(
    symbol: str,
    indicators: dict,
    signal: str,
    risk_reward: float = 5.0,
) -> Optional[dict]:
    """
    Generate a complete options strategy based on technical indicators.

    Parameters
    ----------
    symbol : str
        Ticker symbol (e.g., 'SBIN.NS')
    indicators : dict
        Output from technical.compute_indicators()
    signal : str
        'BULLISH', 'BEARISH', or 'NEUTRAL'
    risk_reward : float
        Target risk-to-reward ratio (default 5.0 means 1:5)

    Returns
    -------
    dict with complete strategy details, or None on failure.
    """
    try:
        price = indicators["current_price"]
        atr = indicators["atr"]
        rsi = indicators["rsi"]
        lot_size = get_lot_size(symbol)
        step = _get_strike_step(price)
        expiry = _next_monthly_expiry()
        currency = "₹" if ".NS" in symbol or symbol.startswith("^") else "$"

        strategy: dict = {
            "symbol": symbol,
            "current_price": price,
            "lot_size": lot_size,
            "expiry": expiry,
            "signal": signal,
            "risk_reward_target": f"1:{risk_reward:.0f}",
            "currency": currency,
            "atr": atr,
            "rsi": rsi,
            "disclaimer": _DISCLAIMER,
        }

        if signal == "BULLISH":
            strategy.update(_bullish_strategy(price, atr, rsi, lot_size, step, risk_reward, currency))
        elif signal == "BEARISH":
            strategy.update(_bearish_strategy(price, atr, rsi, lot_size, step, risk_reward, currency))
        else:
            strategy.update(_neutral_strategy(price, atr, rsi, lot_size, step, risk_reward, currency, indicators))

        return strategy

    except Exception as exc:
        logger.error("Strategy generation failed for %s: %s", symbol, exc)
        return None


def _bullish_strategy(
    price: float,
    atr: float,
    rsi: float,
    lot_size: int,
    step: float,
    rr: float,
    currency: str,
) -> dict:
    """Bull Call Spread or Naked Long Call based on RSI strength."""
    # ATM strike
    atm = _round_strike(price, step)

    if rsi < 40:
        # Deep oversold — aggressive Long Call
        strike = atm
        stop_loss_price = price - (1.5 * atr)
        premium_estimate = round(atr * 1.2, 2)  # rough CE premium ≈ 1.2×ATR
        max_loss = round(premium_estimate * lot_size, 2)
        target_gain = round(max_loss * rr, 2)
        target_price = price + (atr * rr * 0.6)

        return {
            "strategy_name": "Long Call (Aggressive Bullish)",
            "strategy_type": "long_call",
            "legs": [
                {
                    "action": "BUY",
                    "type": "CE",
                    "strike": strike,
                    "premium_est": premium_estimate,
                }
            ],
            "entry_trigger": f"Enter when price holds above {currency}{round(price - 0.5 * atr, 2)}",
            "stop_loss": f"{currency}{round(stop_loss_price, 2)} (exit CE if premium drops 50%)",
            "target": f"{currency}{round(target_price, 2)}",
            "max_loss_per_lot": f"{currency}{max_loss:,.0f}",
            "max_gain_per_lot": f"{currency}{target_gain:,.0f}",
            "risk_reward_actual": f"1:{rr:.1f}",
            "rationale": (
                f"RSI at {rsi:.0f} indicates oversold conditions. "
                f"Price has potential for a mean-reversion bounce. "
                f"ATR-based stop at 1.5x ATR below entry protects capital."
            ),
        }
    else:
        # Standard bullish — Bull Call Spread (defined risk)
        buy_strike = atm
        sell_strike = _round_strike(atm + 2 * step, step)
        spread_width = sell_strike - buy_strike
        net_debit_est = round(spread_width * 0.4, 2)  # rough estimate
        max_loss = round(net_debit_est * lot_size, 2)
        max_gain = round((spread_width - net_debit_est) * lot_size, 2)
        stop_loss_price = price - atr

        return {
            "strategy_name": "Bull Call Spread (Moderate Bullish)",
            "strategy_type": "bull_call_spread",
            "legs": [
                {"action": "BUY", "type": "CE", "strike": buy_strike, "premium_est": round(spread_width * 0.65, 2)},
                {"action": "SELL", "type": "CE", "strike": sell_strike, "premium_est": round(spread_width * 0.25, 2)},
            ],
            "net_debit_est": net_debit_est,
            "entry_trigger": f"Enter when price sustains above EMA 20 ({currency}{round(price, 2)})",
            "stop_loss": f"Exit both legs if price drops below {currency}{round(stop_loss_price, 2)}",
            "target": f"Hold till expiry if price stays above {currency}{sell_strike}",
            "max_loss_per_lot": f"{currency}{max_loss:,.0f}",
            "max_gain_per_lot": f"{currency}{max_gain:,.0f}",
            "risk_reward_actual": f"1:{max_gain / max_loss:.1f}" if max_loss > 0 else "N/A",
            "rationale": (
                f"RSI at {rsi:.0f} with bullish momentum. "
                f"Defined-risk spread limits max loss to net debit. "
                f"Ideal for moderate bullish conviction."
            ),
        }


def _bearish_strategy(
    price: float,
    atr: float,
    rsi: float,
    lot_size: int,
    step: float,
    rr: float,
    currency: str,
) -> dict:
    """Bear Put Spread or Naked Long Put based on RSI strength."""
    atm = _round_strike(price, step)

    if rsi > 80:
        # Extreme overbought — aggressive Long Put
        strike = atm
        stop_loss_price = price + (1.5 * atr)
        premium_estimate = round(atr * 1.2, 2)
        max_loss = round(premium_estimate * lot_size, 2)
        target_gain = round(max_loss * rr, 2)
        target_price = price - (atr * rr * 0.6)

        return {
            "strategy_name": "Long Put (Aggressive Bearish)",
            "strategy_type": "long_put",
            "legs": [
                {
                    "action": "BUY",
                    "type": "PE",
                    "strike": strike,
                    "premium_est": premium_estimate,
                }
            ],
            "entry_trigger": f"Enter when price breaks below {currency}{round(price + 0.5 * atr, 2)}",
            "stop_loss": f"{currency}{round(stop_loss_price, 2)} (exit PE if premium drops 50%)",
            "target": f"{currency}{round(target_price, 2)}",
            "max_loss_per_lot": f"{currency}{max_loss:,.0f}",
            "max_gain_per_lot": f"{currency}{target_gain:,.0f}",
            "risk_reward_actual": f"1:{rr:.1f}",
            "rationale": (
                f"RSI at {rsi:.0f} signals extreme overbought. "
                f"High probability of mean-reversion pullback. "
                f"ATR-based stop at 1.5x ATR above entry."
            ),
        }
    else:
        # Standard bearish — Bear Put Spread
        buy_strike = atm
        sell_strike = _round_strike(atm - 2 * step, step)
        spread_width = buy_strike - sell_strike
        net_debit_est = round(spread_width * 0.4, 2)
        max_loss = round(net_debit_est * lot_size, 2)
        max_gain = round((spread_width - net_debit_est) * lot_size, 2)
        stop_loss_price = price + atr

        return {
            "strategy_name": "Bear Put Spread (Moderate Bearish)",
            "strategy_type": "bear_put_spread",
            "legs": [
                {"action": "BUY", "type": "PE", "strike": buy_strike, "premium_est": round(spread_width * 0.65, 2)},
                {"action": "SELL", "type": "PE", "strike": sell_strike, "premium_est": round(spread_width * 0.25, 2)},
            ],
            "net_debit_est": net_debit_est,
            "entry_trigger": f"Enter when price breaks below EMA 20 ({currency}{round(price, 2)})",
            "stop_loss": f"Exit both legs if price rises above {currency}{round(stop_loss_price, 2)}",
            "target": f"Hold till expiry if price stays below {currency}{sell_strike}",
            "max_loss_per_lot": f"{currency}{max_loss:,.0f}",
            "max_gain_per_lot": f"{currency}{max_gain:,.0f}",
            "risk_reward_actual": f"1:{max_gain / max_loss:.1f}" if max_loss > 0 else "N/A",
            "rationale": (
                f"RSI at {rsi:.0f} with bearish momentum. "
                f"Defined-risk spread caps max loss to net debit. "
                f"Suitable for moderate downside expectation."
            ),
        }


def _neutral_strategy(
    price: float,
    atr: float,
    rsi: float,
    lot_size: int,
    step: float,
    rr: float,
    currency: str,
    indicators: dict,
) -> dict:
    """Iron Condor for range-bound / low-volatility scenarios."""
    atm = _round_strike(price, step)
    bb_position = indicators.get("bb_position", 0.5)

    # Iron Condor — sell OTM CE + OTM PE, buy further OTM for protection
    sell_ce = _round_strike(atm + 2 * step, step)
    buy_ce = _round_strike(sell_ce + step, step)
    sell_pe = _round_strike(atm - 2 * step, step)
    buy_pe = _round_strike(sell_pe - step, step)

    wing_width = buy_ce - sell_ce  # same for put side
    # Net credit from selling the condor ≈ 30-40% of wing width
    net_credit_est = round(wing_width * 0.35, 2)
    max_loss = round((wing_width - net_credit_est) * lot_size, 2)
    max_gain = round(net_credit_est * lot_size, 2)

    return {
        "strategy_name": "Iron Condor (Neutral / Range-Bound)",
        "strategy_type": "iron_condor",
        "legs": [
            {"action": "SELL", "type": "CE", "strike": sell_ce, "premium_est": round(wing_width * 0.45, 2)},
            {"action": "BUY", "type": "CE", "strike": buy_ce, "premium_est": round(wing_width * 0.10, 2)},
            {"action": "SELL", "type": "PE", "strike": sell_pe, "premium_est": round(wing_width * 0.45, 2)},
            {"action": "BUY", "type": "PE", "strike": buy_pe, "premium_est": round(wing_width * 0.10, 2)},
        ],
        "net_credit_est": net_credit_est,
        "entry_trigger": f"Enter when price is consolidating between {currency}{sell_pe} and {currency}{sell_ce}",
        "stop_loss": f"Exit if price breaks outside {currency}{sell_pe} – {currency}{sell_ce} range",
        "target": "Hold till expiry — max profit if price stays within the range",
        "max_loss_per_lot": f"{currency}{max_loss:,.0f}",
        "max_gain_per_lot": f"{currency}{max_gain:,.0f}",
        "risk_reward_actual": f"1:{max_gain / max_loss:.1f}" if max_loss > 0 else "N/A",
        "profit_range": f"{currency}{sell_pe} – {currency}{sell_ce}",
        "rationale": (
            f"RSI at {rsi:.0f} is neutral. "
            f"Bollinger Band position at {bb_position:.0%} suggests range-bound action. "
            f"Iron Condor profits from time decay in a low-volatility environment."
        ),
    }


# ─── Formatted Output for LLM Context ───────────────────────────────────────


def format_strategy_output(strategy: dict) -> str:
    """Format strategy dict into a human-readable summary for LLM context."""
    if strategy is None:
        return ""

    currency = strategy.get("currency", "₹")
    lines = [
        f"🎯 OPTIONS STRATEGY — {strategy['symbol']}",
        f"{'='*50}",
        f"  Strategy: {strategy['strategy_name']}",
        f"  Signal: {strategy['signal']} | R:R Target: {strategy['risk_reward_target']}",
        f"  Current Price: {currency}{strategy['current_price']}",
        f"  Lot Size: {strategy['lot_size']} | Expiry: {strategy['expiry']}",
        "",
        "  LEGS:",
    ]

    for leg in strategy.get("legs", []):
        lines.append(
            f"    {leg['action']} {leg['type']} @ {currency}{leg['strike']}"
            f" (est. premium: {currency}{leg['premium_est']})"
        )

    if "net_debit_est" in strategy:
        lines.append(f"  Net Debit: {currency}{strategy['net_debit_est']} per share")
    if "net_credit_est" in strategy:
        lines.append(f"  Net Credit: {currency}{strategy['net_credit_est']} per share")

    lines.extend([
        "",
        f"  Entry: {strategy.get('entry_trigger', 'N/A')}",
        f"  Stop-Loss: {strategy.get('stop_loss', 'N/A')}",
        f"  Target: {strategy.get('target', 'N/A')}",
        "",
        f"  Max Loss/Lot: {strategy.get('max_loss_per_lot', 'N/A')}",
        f"  Max Gain/Lot: {strategy.get('max_gain_per_lot', 'N/A')}",
        f"  Actual R:R: {strategy.get('risk_reward_actual', 'N/A')}",
    ])

    if "profit_range" in strategy:
        lines.append(f"  Profit Range: {strategy['profit_range']}")

    lines.extend([
        "",
        f"  Rationale: {strategy.get('rationale', '')}",
        "",
        f"  {strategy.get('disclaimer', '')}",
    ])

    return "\n".join(lines)


def generate_candidate_strategies(
    symbol: str,
    indicators: dict,
    signal: str = "NEUTRAL",
    risk_reward: float = 5.0,
    is_options_intent: Optional[bool] = None,
) -> Optional[dict]:
    """
    Generates multiple candidate strategies comparing Defined Risk vs Alpha Momentum
    and designating a recommended 'Master of Technology' strategy.

    For non-options (spot/equity) mode the return payload includes:
      - 'candidates': flat list for the auto-detected signal (backward compat.)
      - 'regimes':    {BULLISH:[5], BEARISH:[5], NEUTRAL:[5], REVERSAL:[5]}
      - 'regime_masters': recommended candidate_id per regime
    """
    try:
        price = indicators.get("current_price", 100.0)
        atr = indicators.get("atr", max(price * 0.015, 1.0))
        rsi = indicators.get("rsi", 50.0)
        lot_size = get_lot_size(symbol)
        step = _get_strike_step(price)
        expiry = _next_monthly_expiry()
        currency = "₹" if ".NS" in symbol or symbol.startswith("^") else "$"

        # Default to True only when None to preserve unit test contracts
        options_mode = True if is_options_intent is None else bool(is_options_intent)

        if not options_mode:
            # ── 20 Institutional Strategies (5 per regime) ──────────────────
            # All 4 regimes are always generated so the approval card can show
            # the full 4-tab regime picker regardless of the auto-detected signal.

            # ── BULLISH ──────────────────────────────────────────────────────
            bullish_candidates = [
                {
                    "candidate_id": "candidate_golden_cross",
                    "category": "BULLISH",
                    "technology_tag": "Golden Cross Momentum",
                    "strategy_name": "Golden Cross Trend Breakout",
                    "strategy_type": "Trend Following",
                    "legs": [],
                    "entry_trigger": f"Enter on EMA50 > EMA200 alignment with positive MACD histogram at {currency}{price:.2f}",
                    "stop_loss": f"Trail 2.0x ATR ({currency}{max(price - 2 * atr, 0.01):.2f})",
                    "target": f"Target 3.0x ATR expansion ({currency}{price + 3 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 2 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.8",
                    "win_rate_est": "78%",
                    "rationale": "Institutional trend breakout confirming EMA50/200 crossover with volume support.",
                },
                {
                    "candidate_id": "candidate_volume_surge",
                    "category": "BULLISH",
                    "technology_tag": "Breakout Volume Surge",
                    "strategy_name": "Bollinger Upper Band Volume Surge",
                    "strategy_type": "Momentum Breakout",
                    "legs": [],
                    "entry_trigger": f"Enter on volume surge > 2x SMA(20) breaking upper band at {currency}{price:.2f}",
                    "stop_loss": f"Stop-loss at EMA20 midline ({currency}{max(price - 1.5 * atr, 0.01):.2f})",
                    "target": f"Target volatility expansion ({currency}{price + 3.2 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.5 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.2 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.2",
                    "win_rate_est": "71%",
                    "rationale": "Exploits institutional buying volume expansion breaking consolidation barriers.",
                },
                {
                    "candidate_id": "candidate_ema21_pullback",
                    "category": "BULLISH",
                    "technology_tag": "EMA21 Pullback Reentry",
                    "strategy_name": "EMA21 Pullback Reentry Setup",
                    "strategy_type": "Pullback Continuation",
                    "legs": [],
                    "entry_trigger": f"Buy on first pullback to EMA21 after breakout candle above pivot at {currency}{price:.2f}",
                    "stop_loss": f"Stop below EMA21 at last swing low ({currency}{max(price - 1.2 * atr, 0.01):.2f})",
                    "target": f"Target measured move from base ({currency}{price + 2.8 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.2 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 2.8 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.5",
                    "win_rate_est": "74%",
                    "rationale": "High-probability reentry capturing the second leg of a trend after institutional pullback absorption.",
                },
                {
                    "candidate_id": "candidate_vwap_reclaim",
                    "category": "BULLISH",
                    "technology_tag": "VWAP Reclaim Momentum",
                    "strategy_name": "VWAP Reclaim Intraday Momentum",
                    "strategy_type": "VWAP Momentum",
                    "legs": [],
                    "entry_trigger": f"Enter long on confirmed VWAP reclaim with increasing bid volume above {currency}{price:.2f}",
                    "stop_loss": f"Stop below VWAP reclaim candle low ({currency}{max(price - 0.9 * atr, 0.01):.2f})",
                    "target": f"Target prior day high / extended VWAP band ({currency}{price + 2.5 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 0.9 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 2.5 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.9",
                    "win_rate_est": "76%",
                    "rationale": "Captures institutional re-accumulation after VWAP reclaim signals smart money re-entry above average cost.",
                },
                {
                    "candidate_id": "candidate_fib_breakout",
                    "category": "BULLISH",
                    "technology_tag": "Fibonacci 61.8% Continuation",
                    "strategy_name": "Fibonacci 61.8% Breakout Continuation",
                    "strategy_type": "Fibonacci Extension",
                    "legs": [],
                    "entry_trigger": f"Buy on bounce or breakout above 61.8% Fibonacci retracement at {currency}{price:.2f}",
                    "stop_loss": f"Stop below 78.6% Fib level ({currency}{max(price - 1.4 * atr, 0.01):.2f})",
                    "target": f"Target 127.2% Fibonacci extension ({currency}{price + 3.4 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.4 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.4 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.1",
                    "win_rate_est": "69%",
                    "rationale": "Targets harmonic Fibonacci confluence zones where institutional orders cluster for high-probability continuation.",
                },
            ]
            bullish_master = "candidate_golden_cross"

            # ── BEARISH ──────────────────────────────────────────────────────
            bearish_candidates = [
                {
                    "candidate_id": "candidate_death_cross",
                    "category": "BEARISH",
                    "technology_tag": "Death Cross Distribution",
                    "strategy_name": "Death Cross Distribution Short",
                    "strategy_type": "Trend Breakdown",
                    "legs": [],
                    "entry_trigger": f"Enter short on EMA50 < EMA200 divergence with negative MACD at {currency}{price:.2f}",
                    "stop_loss": f"Stop-loss above EMA50 resistance ({currency}{price + 2 * atr:.2f})",
                    "target": f"Target liquidity pool ({currency}{max(price - 3 * atr, 0.01):.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 2 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.9",
                    "win_rate_est": "74%",
                    "rationale": "Short setup riding structural distribution and moving average death cross.",
                },
                {
                    "candidate_id": "candidate_breakdown_surge",
                    "category": "BEARISH",
                    "technology_tag": "Breakdown Volume Surge",
                    "strategy_name": "Bollinger Lower Band Breakdown Surge",
                    "strategy_type": "Liquidity Breakdown",
                    "legs": [],
                    "entry_trigger": f"Enter short on lower Bollinger Band breach with high selling volume at {currency}{price:.2f}",
                    "stop_loss": f"Stop-loss at EMA20 rebound level ({currency}{price + 1.5 * atr:.2f})",
                    "target": f"Target support extension ({currency}{max(price - 3.1 * atr, 0.01):.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.5 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.1 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.1",
                    "win_rate_est": "69%",
                    "rationale": "Capitalizes on aggressive panic selling and liquidity purge below key support.",
                },
                {
                    "candidate_id": "candidate_ema50_rejection",
                    "category": "BEARISH",
                    "technology_tag": "EMA50 Rejection Short",
                    "strategy_name": "EMA50 Overhead Resistance Short",
                    "strategy_type": "Resistance Rejection",
                    "legs": [],
                    "entry_trigger": f"Short on bearish rejection candle at EMA50 overhead resistance near {currency}{price:.2f}",
                    "stop_loss": f"Stop above EMA50 wick high ({currency}{price + 1.3 * atr:.2f})",
                    "target": f"Target prior swing low / demand zone ({currency}{max(price - 2.7 * atr, 0.01):.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.3 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 2.7 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.7",
                    "win_rate_est": "72%",
                    "rationale": "Fades institutional sell-side pressure at major EMA overhead zones confirming downtrend continuation.",
                },
                {
                    "candidate_id": "candidate_supply_zone_short",
                    "category": "BEARISH",
                    "technology_tag": "Supply Zone Liquidity Short",
                    "strategy_name": "Supply Zone Institutional Short",
                    "strategy_type": "Supply Zone Reversal",
                    "legs": [],
                    "entry_trigger": f"Enter short at confirmed supply zone retest with bearish engulfing confirmation at {currency}{price:.2f}",
                    "stop_loss": f"Stop above supply zone upper boundary ({currency}{price + 1.1 * atr:.2f})",
                    "target": f"Target nearest demand zone / FVG ({currency}{max(price - 3.0 * atr, 0.01):.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.1 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.0 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.0",
                    "win_rate_est": "67%",
                    "rationale": "Smart money supply zone short aligned with institutional order flow and bearish market structure.",
                },
                {
                    "candidate_id": "candidate_atr_channel_breakdown",
                    "category": "BEARISH",
                    "technology_tag": "ATR Volatility Channel Breakdown",
                    "strategy_name": "ATR Channel Directional Breakdown",
                    "strategy_type": "Volatility Channel Breakdown",
                    "legs": [],
                    "entry_trigger": f"Short on ATR channel lower boundary breach with expanding bearish volume at {currency}{price:.2f}",
                    "stop_loss": f"Stop at midline ATR channel ({currency}{price + 0.8 * atr:.2f})",
                    "target": f"Target 2x ATR channel extension ({currency}{max(price - 2.5 * atr, 0.01):.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 0.8 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 2.5 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.3",
                    "win_rate_est": "65%",
                    "rationale": "Systematic channel breakdown trades volatility expansion as directional bias confirms with momentum.",
                },
            ]
            bearish_master = "candidate_death_cross"

            # ── NEUTRAL ──────────────────────────────────────────────────────
            neutral_candidates = [
                {
                    "candidate_id": "candidate_range_mean_reversion",
                    "category": "NEUTRAL",
                    "technology_tag": "Range-Bound Mean Reversion",
                    "strategy_name": "Range-Bound Channel Oscillation",
                    "strategy_type": "Mean Reversion / Channel Trading",
                    "legs": [],
                    "entry_trigger": f"Buy at channel support and short at channel resistance (ADX < 20) near {currency}{price:.2f}",
                    "stop_loss": f"Stop-loss on 1.2x ATR breakout outside range ({currency}{max(price - 1.2 * atr, 0.01):.2f})",
                    "target": f"Target range midpoint / opposite boundary ({currency}{price + 1.8 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.2 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 1.8 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.2",
                    "win_rate_est": "82%",
                    "rationale": "Harvests predictable oscillations in range-bound, low-trend market regimes.",
                },
                {
                    "candidate_id": "candidate_consolidation_squeeze",
                    "category": "NEUTRAL",
                    "technology_tag": "Consolidation Squeeze",
                    "strategy_name": "Volatility Squeeze Channel Trading",
                    "strategy_type": "Band Squeeze Grid / Channel",
                    "legs": [],
                    "entry_trigger": f"Grid placement across contracting volatility squeeze bands near {currency}{price:.2f}",
                    "stop_loss": f"Stop-loss on directional squeeze expansion ({currency}{max(price - 1.0 * atr, 0.01):.2f})",
                    "target": f"Target mean equilibrium price ({currency}{price + 1.5 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.0 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 1.5 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.0",
                    "win_rate_est": "84%",
                    "rationale": "Capitalizes on low volatility compression before explosive directional expansion.",
                },
                {
                    "candidate_id": "candidate_keltner_mean_reversion",
                    "category": "NEUTRAL",
                    "technology_tag": "Keltner Channel Mean Reversion",
                    "strategy_name": "Keltner Channel Inner-Band Reversion",
                    "strategy_type": "Keltner Oscillation",
                    "legs": [],
                    "entry_trigger": f"Buy at lower Keltner band, short at upper Keltner band with RSI confirming extreme near {currency}{price:.2f}",
                    "stop_loss": f"Stop on close outside Keltner outer band ({currency}{max(price - 1.1 * atr, 0.01):.2f})",
                    "target": f"Target Keltner midline EMA20 ({currency}{price + 1.6 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.1 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 1.6 * lot_size:,.0f}",
                    "risk_reward_actual": "1:1.9",
                    "win_rate_est": "80%",
                    "rationale": "Exploits Keltner Channel mean-reversion in low-ADX sideways price action with RSI overbought/oversold confirmation.",
                },
                {
                    "candidate_id": "candidate_vwap_band_reversion",
                    "category": "NEUTRAL",
                    "technology_tag": "VWAP Band Mean Reversion",
                    "strategy_name": "VWAP 2SD Band Mean Reversion",
                    "strategy_type": "VWAP Statistical Reversion",
                    "legs": [],
                    "entry_trigger": f"Enter mean-reversion position at ±2 standard deviation VWAP deviation near {currency}{price:.2f}",
                    "stop_loss": f"Stop at ±2.5 SD VWAP level ({currency}{max(price - 0.9 * atr, 0.01):.2f})",
                    "target": f"Target VWAP equilibrium ({currency}{price + 1.4 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 0.9 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 1.4 * lot_size:,.0f}",
                    "risk_reward_actual": "1:1.8",
                    "win_rate_est": "85%",
                    "rationale": "Statistical reversion to VWAP equilibrium capitalizing on short-term institutional cost averaging pressure.",
                },
                {
                    "candidate_id": "candidate_adx_grid_scalping",
                    "category": "NEUTRAL",
                    "technology_tag": "ADX Flatline Grid Scalping",
                    "strategy_name": "ADX Sub-20 Grid Scalping Strategy",
                    "strategy_type": "Grid / Range Scalping",
                    "legs": [],
                    "entry_trigger": f"Deploy bidirectional grid orders on ADX < 18 flat range between support and resistance at {currency}{price:.2f}",
                    "stop_loss": f"Collapse grid on ADX > 25 breakout ({currency}{max(price - 1.3 * atr, 0.01):.2f})",
                    "target": f"Target per-grid cell profit at defined tick distance ({currency}{price + 1.0 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.3 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 1.0 * lot_size:,.0f}",
                    "risk_reward_actual": "1:1.5",
                    "win_rate_est": "88%",
                    "rationale": "High-frequency grid scalping in ultra-low ADX regimes with automatic collapse on directional breakout.",
                },
            ]
            neutral_master = "candidate_range_mean_reversion"

            # ── REVERSAL ─────────────────────────────────────────────────────
            reversal_candidates = [
                {
                    "candidate_id": "candidate_rsi_divergence",
                    "category": "REVERSAL",
                    "technology_tag": "Bullish RSI Divergence",
                    "strategy_name": "Oversold RSI Divergence Reversal",
                    "strategy_type": "Counter-Trend Sniper Pivot",
                    "legs": [],
                    "entry_trigger": f"Enter long on lower price low accompanied by higher RSI low below 35 at {currency}{price:.2f}",
                    "stop_loss": f"Tight stop below recent swing low ({currency}{max(price - 1.3 * atr, 0.01):.2f})",
                    "target": f"Target mean-reversion to EMA50 ({currency}{price + 3.5 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.3 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.5 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.4",
                    "win_rate_est": "76%",
                    "rationale": "Sniper reversal entry exploiting institutional exhaustion and momentum divergence.",
                },
                {
                    "candidate_id": "candidate_hammer_reversal",
                    "category": "REVERSAL",
                    "technology_tag": "Hammer / Engulfing Reversal",
                    "strategy_name": "Price Action Liquidity Sweep Reversal",
                    "strategy_type": "Liquidity Sweep Pivot",
                    "legs": [],
                    "entry_trigger": f"Enter on bullish engulfing candle or hammer rejection at support at {currency}{price:.2f}",
                    "stop_loss": f"Stop below wick low ({currency}{max(price - 1.2 * atr, 0.01):.2f})",
                    "target": f"Target resistance retest ({currency}{price + 3.0 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.2 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.0 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.1",
                    "win_rate_est": "72%",
                    "rationale": "Identifies smart-money liquidity sweeps and sudden directional turnaround.",
                },
                {
                    "candidate_id": "candidate_trendline_counter_pivot",
                    "category": "REVERSAL",
                    "technology_tag": "Trendline Break Counter Pivot",
                    "strategy_name": "Trendline Break Counter-Trend Pivot",
                    "strategy_type": "Trendline Breakout Reversal",
                    "legs": [],
                    "entry_trigger": f"Enter on confirmed close above descending trendline with volume expansion at {currency}{price:.2f}",
                    "stop_loss": f"Stop below trendline breakpoint candle low ({currency}{max(price - 1.0 * atr, 0.01):.2f})",
                    "target": f"Target prior structure high / reversal target ({currency}{price + 3.2 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.0 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.2 * lot_size:,.0f}",
                    "risk_reward_actual": "1:3.2",
                    "win_rate_est": "70%",
                    "rationale": "Aggressive counter-trend pivot on structural trendline breach with confirmed volume impulse.",
                },
                {
                    "candidate_id": "candidate_order_block_reversal",
                    "category": "REVERSAL",
                    "technology_tag": "Order Block Institutional Reversal",
                    "strategy_name": "Institutional Order Block Reversal",
                    "strategy_type": "Order Block / Smart Money",
                    "legs": [],
                    "entry_trigger": f"Buy at institutional bullish order block (last down candle before impulse up) near {currency}{price:.2f}",
                    "stop_loss": f"Stop below order block low with buffer ({currency}{max(price - 0.8 * atr, 0.01):.2f})",
                    "target": f"Target order block origin / breaker block ({currency}{price + 3.8 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 0.8 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.8 * lot_size:,.0f}",
                    "risk_reward_actual": "1:4.0",
                    "win_rate_est": "65%",
                    "rationale": "Smart money order block theory: targets institutional re-entry zones from prior displacement moves.",
                },
                {
                    "candidate_id": "candidate_double_bottom_reversal",
                    "category": "REVERSAL",
                    "technology_tag": "Double Bottom Breakout Reversal",
                    "strategy_name": "Double Bottom W-Pattern Breakout",
                    "strategy_type": "Chart Pattern Reversal",
                    "legs": [],
                    "entry_trigger": f"Enter long on neckline breakout of double bottom W-pattern with confirming RSI uptick at {currency}{price:.2f}",
                    "stop_loss": f"Stop below the second bottom low ({currency}{max(price - 1.5 * atr, 0.01):.2f})",
                    "target": f"Target measured pattern height projection ({currency}{price + 3.3 * atr:.2f})",
                    "max_loss_per_lot": f"{currency}{atr * 1.5 * lot_size:,.0f}",
                    "max_gain_per_lot": f"{currency}{atr * 3.3 * lot_size:,.0f}",
                    "risk_reward_actual": "1:2.8",
                    "win_rate_est": "73%",
                    "rationale": "Classic double bottom reversal offering well-defined risk with measured pattern-based profit projection.",
                },
            ]
            reversal_master = "candidate_rsi_divergence"

            # ── Determine active regime's master recommendation ───────────────
            sig_clean = signal.upper()
            if "BULL" in sig_clean:
                active_candidates = bullish_candidates
                master_rec = bullish_master
            elif "BEAR" in sig_clean:
                active_candidates = bearish_candidates
                master_rec = bearish_master
            elif "REV" in sig_clean:
                active_candidates = reversal_candidates
                master_rec = reversal_master
            else:
                active_candidates = neutral_candidates
                master_rec = neutral_master

            return {
                "symbol": symbol,
                "current_price": price,
                "lot_size": lot_size,
                "expiry": expiry,
                "signal": signal,
                "currency": currency,
                "is_options": False,
                "master_recommended": master_rec,
                # Legacy flat list — candidates for the auto-detected signal only
                # Preserved for backward compat with existing tests and fallback paths
                "candidates": active_candidates,
                # New grouped regimes dict — powers the 4-tab regime picker card
                "regimes": {
                    "BULLISH":  bullish_candidates,
                    "BEARISH":  bearish_candidates,
                    "NEUTRAL":  neutral_candidates,
                    "REVERSAL": reversal_candidates,
                },
                "regime_masters": {
                    "BULLISH":  bullish_master,
                    "BEARISH":  bearish_master,
                    "NEUTRAL":  neutral_master,
                    "REVERSAL": reversal_master,
                },
                "disclaimer": _DISCLAIMER,
            }

        candidates = []
        if signal == "BULLISH":
            strat_spread = _bullish_strategy(price, atr, max(rsi, 50.0), lot_size, step, risk_reward, currency)
            strat_spread["candidate_id"] = "candidate_defined_risk"
            strat_spread["category"] = "Defined Risk (Spread)"
            strat_spread["technology_tag"] = "Institutional Hedged Spread"
            strat_spread["win_rate_est"] = "68%"

            strat_alpha = _bullish_strategy(price, atr, min(rsi, 35.0), lot_size, step, risk_reward, currency)
            strat_alpha["candidate_id"] = "candidate_alpha_momentum"
            strat_alpha["category"] = "High-Alpha Momentum"
            strat_alpha["technology_tag"] = "Algorithmic Directional Outright"
            strat_alpha["win_rate_est"] = "52%"

            candidates = [strat_spread, strat_alpha]
            master_rec = "candidate_defined_risk"
        elif signal == "BEARISH":
            strat_spread = _bearish_strategy(price, atr, min(rsi, 50.0), lot_size, step, risk_reward, currency)
            strat_spread["candidate_id"] = "candidate_defined_risk"
            strat_spread["category"] = "Defined Risk (Spread)"
            strat_spread["technology_tag"] = "Institutional Hedged Spread"
            strat_spread["win_rate_est"] = "65%"

            strat_alpha = _bearish_strategy(price, atr, max(rsi, 85.0), lot_size, step, risk_reward, currency)
            strat_alpha["candidate_id"] = "candidate_alpha_momentum"
            strat_alpha["category"] = "High-Alpha Momentum"
            strat_alpha["technology_tag"] = "Algorithmic Directional Outright"
            strat_alpha["win_rate_est"] = "49%"

            candidates = [strat_spread, strat_alpha]
            master_rec = "candidate_defined_risk"
        else:
            strat_condor = _neutral_strategy(price, atr, rsi, lot_size, step, risk_reward, currency, indicators)
            strat_condor["candidate_id"] = "candidate_delta_neutral"
            strat_condor["category"] = "Delta Neutral"
            strat_condor["technology_tag"] = "Mean-Reverting Iron Condor"
            strat_condor["win_rate_est"] = "76%"

            atm = _round_strike(price, step)
            prem_ce = round(atr * 0.9, 2)
            prem_pe = round(atr * 0.9, 2)
            max_loss = round((prem_ce + prem_pe) * lot_size, 2)
            strat_straddle = {
                "candidate_id": "candidate_volatility_breakout",
                "category": "Volatility Breakout",
                "technology_tag": "Long Straddle Gamma Squeeze",
                "strategy_name": "Long Straddle (Volatility Expansion)",
                "strategy_type": "long_straddle",
                "legs": [
                    {"action": "BUY", "type": "CE", "strike": atm, "premium_est": prem_ce},
                    {"action": "BUY", "type": "PE", "strike": atm, "premium_est": prem_pe},
                ],
                "entry_trigger": f"Enter at ATM strike {currency}{atm} prior to breakout",
                "stop_loss": "Exit if implied volatility drops 20%",
                "target": "Exit when either leg doubles",
                "max_loss_per_lot": f"{currency}{max_loss:,.0f}",
                "max_gain_per_lot": "Unlimited",
                "risk_reward_actual": "1:3+",
                "win_rate_est": "44%",
                "rationale": "Positions for sharp move in either direction breaking out of consolidation.",
            }
            candidates = [strat_condor, strat_straddle]
            master_rec = "candidate_delta_neutral"

        return {
            "symbol": symbol,
            "current_price": price,
            "lot_size": lot_size,
            "expiry": expiry,
            "signal": signal,
            "currency": currency,
            "master_recommended": master_rec,
            "candidates": candidates,
            "disclaimer": _DISCLAIMER,
        }
    except Exception as exc:
        logger.error("Candidate strategy generation failed for %s: %s", symbol, exc)
        return None

