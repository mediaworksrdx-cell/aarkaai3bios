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
