"""
AARKAAI – Technical Analysis Engine

Computes real-time technical indicators from yfinance historical data:
  RSI (14), MACD (12,26,9), EMA 20/50/200, Bollinger Bands (20,2),
  ATR (14), Volume SMA (20).

Produces a consensus signal (BULLISH / BEARISH / NEUTRAL) and a
human-readable summary for LLM context injection.

No new dependencies — uses pandas + numpy (already installed).
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


# ─── Core Indicator Functions ────────────────────────────────────────────────


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's smoothed RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=span, adjust=False).mean()


def _macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, histogram."""
    macd_line = _ema(series, fast) - _ema(series, slow)
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Upper band, middle (SMA), lower band."""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def _atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period).mean()


# ─── Main Compute Function ──────────────────────────────────────────────────


def compute_indicators(
    symbol: str,
    period: str = "6mo",
) -> Optional[dict]:
    """
    Fetch historical data from yfinance and compute all technical indicators.

    Returns a dict with the latest values, or None on failure.
    """
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period=period)
        if hist.empty or len(hist) < 50:
            logger.warning("Insufficient history for %s (%d rows)", symbol, len(hist))
            return None

        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        volume = hist["Volume"]

        # RSI
        rsi_series = _rsi(close, 14)
        rsi_val = round(float(rsi_series.iloc[-1]), 2)

        # MACD
        macd_line, signal_line, histogram = _macd(close)
        macd_val = round(float(macd_line.iloc[-1]), 2)
        macd_signal_val = round(float(signal_line.iloc[-1]), 2)
        macd_hist_val = round(float(histogram.iloc[-1]), 2)
        # Check for crossover (current bar vs previous)
        macd_crossover = (
            "bullish"
            if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0
            else "bearish"
            if histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0
            else "none"
        )

        # EMAs
        ema20 = round(float(_ema(close, 20).iloc[-1]), 2)
        ema50 = round(float(_ema(close, 50).iloc[-1]), 2)
        ema200 = round(float(_ema(close, 200).iloc[-1]), 2) if len(close) >= 200 else None

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = _bollinger_bands(close)
        bb_upper_val = round(float(bb_upper.iloc[-1]), 2)
        bb_middle_val = round(float(bb_middle.iloc[-1]), 2)
        bb_lower_val = round(float(bb_lower.iloc[-1]), 2)

        # ATR
        atr_series = _atr(high, low, close)
        atr_val = round(float(atr_series.iloc[-1]), 2)

        # Volume
        vol_sma = round(float(volume.rolling(20).mean().iloc[-1]), 0)
        current_vol = int(volume.iloc[-1])

        # Current price
        current_price = round(float(close.iloc[-1]), 2)
        prev_close_price = round(float(close.iloc[-2]), 2)

        # Price position relative to Bollinger Bands (0–1 scale)
        bb_width = bb_upper_val - bb_lower_val
        bb_position = round((current_price - bb_lower_val) / bb_width, 2) if bb_width > 0 else 0.5

        return {
            "symbol": symbol,
            "current_price": current_price,
            "prev_close": prev_close_price,
            # RSI
            "rsi": rsi_val,
            # MACD
            "macd": macd_val,
            "macd_signal": macd_signal_val,
            "macd_histogram": macd_hist_val,
            "macd_crossover": macd_crossover,
            # EMAs
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            # Bollinger Bands
            "bb_upper": bb_upper_val,
            "bb_middle": bb_middle_val,
            "bb_lower": bb_lower_val,
            "bb_position": bb_position,
            # ATR
            "atr": atr_val,
            # Volume
            "volume": current_vol,
            "volume_sma20": vol_sma,
            "volume_ratio": round(current_vol / vol_sma, 2) if vol_sma > 0 else 1.0,
            # Trend flags
            "price_above_ema20": current_price > ema20,
            "price_above_ema50": current_price > ema50,
            "price_above_ema200": current_price > ema200 if ema200 else None,
            "ema20_above_ema50": ema20 > ema50,
        }

    except Exception as exc:
        logger.error("Technical analysis failed for %s: %s", symbol, exc)
        return None


# ─── Signal Generation ───────────────────────────────────────────────────────


def get_signal(indicators: dict) -> str:
    """
    Multi-indicator consensus signal.

    Returns: 'BULLISH', 'BEARISH', or 'NEUTRAL'
    """
    score = 0  # positive = bullish, negative = bearish

    rsi = indicators["rsi"]
    if rsi < 40:
        score += 2  # oversold → bullish opportunity
    elif rsi < 50:
        score += 1
    elif rsi > 70:
        score -= 2  # overbought → bearish risk
    elif rsi > 60:
        score -= 1

    # MACD
    if indicators["macd_histogram"] > 0:
        score += 1
    else:
        score -= 1
    if indicators["macd_crossover"] == "bullish":
        score += 2
    elif indicators["macd_crossover"] == "bearish":
        score -= 2

    # EMA alignment
    if indicators["price_above_ema20"]:
        score += 1
    else:
        score -= 1
    if indicators["ema20_above_ema50"]:
        score += 1
    else:
        score -= 1

    # Bollinger position
    bb_pos = indicators["bb_position"]
    if bb_pos < 0.2:
        score += 1  # near lower band → potential bounce
    elif bb_pos > 0.8:
        score -= 1  # near upper band → potential reversal

    # Volume confirmation
    if indicators["volume_ratio"] > 1.5:
        # High volume amplifies the current trend signal
        if score > 0:
            score += 1
        elif score < 0:
            score -= 1

    if score >= 3:
        return "BULLISH"
    elif score <= -3:
        return "BEARISH"
    else:
        return "NEUTRAL"


# ─── Formatted Summary for LLM Context ──────────────────────────────────────


def format_technical_summary(symbol: str, indicators: dict, signal: str) -> str:
    """Human-readable technical analysis summary for context injection."""
    price = indicators["current_price"]
    currency = "₹" if ".NS" in symbol else "$"

    rsi = indicators["rsi"]
    rsi_label = (
        "OVERSOLD" if rsi < 30
        else "oversold zone" if rsi < 40
        else "neutral" if rsi < 60
        else "overbought zone" if rsi < 70
        else "OVERBOUGHT"
    )

    ema200_line = ""
    if indicators["ema200"] is not None:
        trend = "above" if indicators["price_above_ema200"] else "below"
        ema200_line = f"  EMA 200: {currency}{indicators['ema200']} (price {trend})\n"

    macd_desc = f"MACD: {indicators['macd']} | Signal: {indicators['macd_signal']} | Histogram: {indicators['macd_histogram']}"
    if indicators["macd_crossover"] != "none":
        macd_desc += f" [⚡ {indicators['macd_crossover'].upper()} CROSSOVER]"

    vol_desc = "above average" if indicators["volume_ratio"] > 1.2 else "below average" if indicators["volume_ratio"] < 0.8 else "average"

    return (
        f"📊 TECHNICAL ANALYSIS — {symbol}\n"
        f"{'='*45}\n"
        f"  Price: {currency}{price}\n"
        f"  Signal: {'🟢' if signal == 'BULLISH' else '🔴' if signal == 'BEARISH' else '🟡'} {signal}\n"
        f"\n"
        f"  RSI (14): {rsi} — {rsi_label}\n"
        f"  {macd_desc}\n"
        f"\n"
        f"  EMA 20: {currency}{indicators['ema20']}\n"
        f"  EMA 50: {currency}{indicators['ema50']}\n"
        f"{ema200_line}"
        f"\n"
        f"  Bollinger Bands: {currency}{indicators['bb_lower']} – {currency}{indicators['bb_upper']}\n"
        f"  Band Position: {indicators['bb_position']:.0%} (0%=lower, 100%=upper)\n"
        f"\n"
        f"  ATR (14): {currency}{indicators['atr']}\n"
        f"  Volume: {indicators['volume']:,} ({vol_desc}, {indicators['volume_ratio']:.1f}x avg)\n"
    )
