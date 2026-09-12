from __future__ import annotations
import logging
import math
from modules.screener.schemas import StrategyResult, StrategyCategory, ScoreBreakdown

logger = logging.getLogger(__name__)

def safe_float(val, default=0.0):
    if val is None or isinstance(val, (float, int)) and math.isnan(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

class GoldenCrossMomentum:
    name = "golden_cross_momentum"
    display_name = "Golden Cross Momentum"
    category = StrategyCategory.BULLISH
    description = "EMA50 > EMA200 (crossed recently or aligned) + RSI 50-70 + MACD histogram > 0 + ADX > 25."
    required_indicators = ["ema50", "ema200", "rsi", "macd_histogram", "adx", "volume_ratio"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        ema50 = safe_float(indicators.get("ema50"))
        ema200 = safe_float(indicators.get("ema200"))
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        adx = safe_float(indicators.get("adx"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))

        if ema50 > 0 and ema200 > 0 and ema50 > ema200:
            score += 3.0
            evidence.append("EMA alignment: EMA50 > EMA200 (+3)")
        
        if 50 <= rsi <= 70:
            score += 2.0
            evidence.append(f"RSI sweet spot: {rsi:.2f} (+2)")
            
        if macd_hist > 0:
            score += 2.0
            evidence.append("MACD positive (+2)")
            
        if adx > 25:
            score += 2.0
            evidence.append(f"ADX trending: {adx:.2f} (+2)")
            
        if vol_ratio > 1.0:
            score += 1.0
            evidence.append(f"Volume confirmation: ratio {vol_ratio:.2f} (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class BreakoutVolumeSurge:
    name = "breakout_volume_surge"
    display_name = "Breakout Volume Surge"
    category = StrategyCategory.BULLISH
    description = "Price > BB upper band + Volume > 2x SMA(20) + RSI < 75."
    required_indicators = ["price", "bb_upper", "volume_ratio", "rsi", "macd_histogram", "ema20"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        price = safe_float(indicators.get("price"))
        bb_upper = safe_float(indicators.get("bb_upper"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        ema20 = safe_float(indicators.get("ema20"))

        if price > 0 and bb_upper > 0 and price > bb_upper:
            score += 3.0
            evidence.append("BB breakout: Price > BB upper (+3)")
            
        if vol_ratio > 2.0:
            score += 3.0
            evidence.append(f"Volume surge: {vol_ratio:.2f}x SMA (+3)")
            
        if 0 < rsi < 75:
            score += 2.0
            evidence.append(f"RSI not overbought: {rsi:.2f} (+2)")
            
        if macd_hist > 0:
            score += 1.0
            evidence.append("MACD positive (+1)")
            
        if price > 0 and ema20 > 0 and price > ema20:
            score += 1.0
            evidence.append("Price > EMA20 (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class EarningsMomentum:
    name = "earnings_momentum"
    display_name = "Earnings Momentum"
    category = StrategyCategory.BULLISH
    description = "EPS > 0 + P/E < 25 + Price > EMA50 + MACD bullish crossover."
    required_indicators = ["price", "ema50", "macd_crossover"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        eps = safe_float(fundamentals.get("eps"))
        pe = safe_float(fundamentals.get("pe"))
        roe = safe_float(fundamentals.get("roe"))
        price = safe_float(indicators.get("price"))
        ema50 = safe_float(indicators.get("ema50"))
        macd_cross = indicators.get("macd_crossover")

        if eps > 0:
            score += 2.0
            evidence.append("Positive EPS (+2)")
            
        if 0 < pe < 25:
            score += 2.0
            evidence.append(f"Reasonable P/E: {pe:.2f} (+2)")
            
        if price > 0 and ema50 > 0 and price > ema50:
            score += 2.0
            evidence.append("Above EMA50 (+2)")
            
        if macd_cross == "bullish":
            score += 2.0
            evidence.append("MACD crossover (+2)")
            
        if roe > 0.15:
            score += 2.0
            evidence.append(f"ROE > 15%: {roe:.1%} (+2)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence
        )


class SupertrendBuy:
    name = "supertrend_buy"
    display_name = "Supertrend Buy"
    category = StrategyCategory.BULLISH
    description = "Supertrend direction = +1 + RSI 45-65 + ADX > 20."
    required_indicators = ["supertrend_direction", "rsi", "adx", "price", "ema20", "volume_ratio", "macd_histogram"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        st_dir = safe_float(indicators.get("supertrend_direction"))
        rsi = safe_float(indicators.get("rsi"))
        adx = safe_float(indicators.get("adx"))
        price = safe_float(indicators.get("price"))
        ema20 = safe_float(indicators.get("ema20"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        macd_hist = safe_float(indicators.get("macd_histogram"))

        if st_dir == 1:
            score += 3.0
            evidence.append("Supertrend bullish (+3)")
            
        if 45 <= rsi <= 65:
            score += 2.0
            evidence.append(f"RSI range: {rsi:.2f} (+2)")
            
        if adx > 20:
            score += 2.0
            evidence.append(f"ADX trending: {adx:.2f} (+2)")
            
        if price > 0 and ema20 > 0 and price > ema20:
            score += 1.0
            evidence.append("Price > EMA20 (+1)")
            
        if vol_ratio > 1.0:
            score += 1.0
            evidence.append(f"Volume ratio > 1: {vol_ratio:.2f} (+1)")
            
        if macd_hist > 0:
            score += 1.0
            evidence.append("MACD positive (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class AccumulationBreakout:
    name = "accumulation_breakout"
    display_name = "Accumulation Breakout"
    category = StrategyCategory.BULLISH
    description = "EMA20 > EMA50 > EMA200 (stacked) + Volume rising + Price > EMA20."
    required_indicators = ["ema20", "ema50", "ema200", "volume_ratio", "price", "rsi", "macd_histogram"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        ema20 = safe_float(indicators.get("ema20"))
        ema50 = safe_float(indicators.get("ema50"))
        ema200 = safe_float(indicators.get("ema200"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        price = safe_float(indicators.get("price"))
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))

        if ema20 > 0 and ema50 > 0 and ema200 > 0 and ema20 > ema50 > ema200:
            score += 4.0
            evidence.append("Triple EMA stack (+4)")
            
        if vol_ratio > 1.2:
            score += 2.0
            evidence.append(f"Volume expanding: {vol_ratio:.2f} (+2)")
            
        if price > 0 and ema20 > 0 and price > ema20:
            score += 1.0
            evidence.append("Price above EMA20 (+1)")
            
        if 45 <= rsi <= 65:
            score += 2.0
            evidence.append(f"RSI 45-65: {rsi:.2f} (+2)")
            
        if macd_hist > 0:
            score += 1.0
            evidence.append("MACD histogram growing (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class DeathCrossDistribution:
    name = "death_cross_distribution"
    display_name = "Death Cross Distribution"
    category = StrategyCategory.BEARISH
    description = "EMA50 < EMA200 + RSI < 45 + MACD histogram < 0 + ADX > 25."
    required_indicators = ["ema50", "ema200", "rsi", "macd_histogram", "adx", "volume_ratio"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        ema50 = safe_float(indicators.get("ema50"))
        ema200 = safe_float(indicators.get("ema200"))
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        adx = safe_float(indicators.get("adx"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))

        if ema50 > 0 and ema200 > 0 and ema50 < ema200:
            score += 3.0
            evidence.append("Death cross: EMA50 < EMA200 (+3)")
            
        if 0 < rsi < 45:
            score += 2.0
            evidence.append(f"RSI weak: {rsi:.2f} (+2)")
            
        if macd_hist < 0:
            score += 2.0
            evidence.append("MACD negative (+2)")
            
        if adx > 25:
            score += 2.0
            evidence.append(f"ADX trending: {adx:.2f} (+2)")
            
        if vol_ratio > 1.0:
            score += 1.0
            evidence.append("Volume on down days (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class BreakdownVolumeSurge:
    name = "breakdown_volume_surge"
    display_name = "Breakdown Volume Surge"
    category = StrategyCategory.BEARISH
    description = "Price < BB lower band + Volume > 2x SMA(20) + RSI > 25."
    required_indicators = ["price", "bb_lower", "volume_ratio", "rsi", "macd_histogram", "ema20"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        price = safe_float(indicators.get("price"))
        bb_lower = safe_float(indicators.get("bb_lower"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        ema20 = safe_float(indicators.get("ema20"))

        if price > 0 and bb_lower > 0 and price < bb_lower:
            score += 3.0
            evidence.append("BB breakdown: Price < BB lower (+3)")
            
        if vol_ratio > 2.0:
            score += 3.0
            evidence.append(f"Volume surge: {vol_ratio:.2f}x SMA (+3)")
            
        if rsi > 25:
            score += 2.0
            evidence.append(f"RSI not oversold yet: {rsi:.2f} (+2)")
            
        if macd_hist < 0:
            score += 1.0
            evidence.append("MACD negative (+1)")
            
        if price > 0 and ema20 > 0 and price < ema20:
            score += 1.0
            evidence.append("Price < EMA20 (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class EarningsDeterioration:
    name = "earnings_deterioration"
    display_name = "Earnings Deterioration"
    category = StrategyCategory.BEARISH
    description = "EPS declining or negative + P/E > 30 or negative + Price < EMA50 + MACD bearish."
    required_indicators = ["price", "ema50", "macd_crossover", "macd_histogram"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        eps = safe_float(fundamentals.get("eps"), default=1.0) # assume positive if unknown to avoid false flags
        pe = safe_float(fundamentals.get("pe"), default=15.0)
        roe = safe_float(fundamentals.get("roe"), default=0.15)
        price = safe_float(indicators.get("price"))
        ema50 = safe_float(indicators.get("ema50"))
        macd_cross = indicators.get("macd_crossover")
        macd_hist = safe_float(indicators.get("macd_histogram"))

        # Actual EPS negative check, since we don't have historical eps to check decline reliably
        if eps <= 0 and "eps" in fundamentals and fundamentals["eps"] is not None:
            score += 2.0
            evidence.append("Weak EPS (+2)")
            
        if (pe > 30 or pe < 0) and "pe" in fundamentals and fundamentals["pe"] is not None:
            score += 2.0
            evidence.append(f"High/neg P/E: {pe:.2f} (+2)")
            
        if price > 0 and ema50 > 0 and price < ema50:
            score += 2.0
            evidence.append("Below EMA50 (+2)")
            
        if macd_cross == "bearish" or macd_hist < 0:
            score += 2.0
            evidence.append("Bearish MACD (+2)")
            
        if roe < 0.10 and "roe" in fundamentals and fundamentals["roe"] is not None:
            score += 2.0
            evidence.append(f"ROE < 10%: {roe:.1%} (+2)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence
        )


class SupertrendSell:
    name = "supertrend_sell"
    display_name = "Supertrend Sell"
    category = StrategyCategory.BEARISH
    description = "Supertrend direction = -1 + RSI 35-55 + ADX > 20."
    required_indicators = ["supertrend_direction", "rsi", "adx", "price", "ema20", "macd_histogram", "volume_ratio"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        st_dir = safe_float(indicators.get("supertrend_direction"))
        rsi = safe_float(indicators.get("rsi"))
        adx = safe_float(indicators.get("adx"))
        price = safe_float(indicators.get("price"))
        ema20 = safe_float(indicators.get("ema20"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))

        if st_dir == -1:
            score += 3.0
            evidence.append("Supertrend bearish (+3)")
            
        if 35 <= rsi <= 55:
            score += 2.0
            evidence.append(f"RSI weak range: {rsi:.2f} (+2)")
            
        if adx > 20:
            score += 2.0
            evidence.append(f"ADX trending: {adx:.2f} (+2)")
            
        if price > 0 and ema20 > 0 and price < ema20:
            score += 1.0
            evidence.append("Price < EMA20 (+1)")
            
        if macd_hist < 0:
            score += 1.0
            evidence.append("MACD negative (+1)")
            
        if vol_ratio > 1.0:
            score += 1.0
            evidence.append("Volume confirmation (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class DistributionBreakdown:
    name = "distribution_breakdown"
    display_name = "Distribution Breakdown"
    category = StrategyCategory.BEARISH
    description = "EMA20 < EMA50 < EMA200 (inverse stack) + RSI declining + Price < EMA20."
    required_indicators = ["ema20", "ema50", "ema200", "rsi", "price", "volume_ratio", "macd_histogram"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        ema20 = safe_float(indicators.get("ema20"))
        ema50 = safe_float(indicators.get("ema50"))
        ema200 = safe_float(indicators.get("ema200"))
        rsi = safe_float(indicators.get("rsi"))
        price = safe_float(indicators.get("price"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        macd_hist = safe_float(indicators.get("macd_histogram"))

        if ema20 > 0 and ema50 > 0 and ema200 > 0 and ema20 < ema50 < ema200:
            score += 4.0
            evidence.append("Inverse EMA stack (+4)")
            
        if 0 < rsi < 45:
            score += 2.0
            evidence.append(f"RSI below 45: {rsi:.2f} (+2)")
            
        if price > 0 and ema20 > 0 and price < ema20:
            score += 1.0
            evidence.append("Price below EMA20 (+1)")
            
        if vol_ratio < 1.0:
            score += 2.0
            evidence.append(f"Volume declining: {vol_ratio:.2f} (+2)")
            
        if macd_hist < 0:
            score += 1.0
            evidence.append("MACD histogram shrinking (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class RangeBoundMeanReversion:
    name = "range_bound_mean_reversion"
    display_name = "Range Bound Mean Reversion"
    category = StrategyCategory.NEUTRAL
    description = "BB %B between 0.3-0.7 + ADX < 20 + RSI 40-60."
    required_indicators = ["bb_position", "adx", "rsi", "macd_histogram", "atr", "price"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        bb_pos = safe_float(indicators.get("bb_position"))
        adx = safe_float(indicators.get("adx"))
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        atr = safe_float(indicators.get("atr"))
        price = safe_float(indicators.get("price"))

        if 0.3 <= bb_pos <= 0.7:
            score += 3.0
            evidence.append(f"BB mid-range: {bb_pos:.2f} (+3)")
            
        if 0 < adx < 20:
            score += 3.0
            evidence.append(f"Low ADX: {adx:.2f} (+3)")
            
        if 40 <= rsi <= 60:
            score += 2.0
            evidence.append(f"Neutral RSI: {rsi:.2f} (+2)")
            
        if abs(macd_hist) < 0.5:
            score += 1.0
            evidence.append("MACD near zero (+1)")
            
        if price > 0 and (atr / price) < 0.03:
            score += 1.0
            evidence.append("Low ATR relative to price (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class FairValueZone:
    name = "fair_value_zone"
    display_name = "Fair Value Zone"
    category = StrategyCategory.NEUTRAL
    description = "P/E between 12-22 + Price between EMA50 and EMA200 + Low volatility."
    required_indicators = ["price", "ema50", "ema200", "atr", "rsi", "volume_ratio"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        pe = safe_float(fundamentals.get("pe"), default=0.0)
        price = safe_float(indicators.get("price"))
        ema50 = safe_float(indicators.get("ema50"))
        ema200 = safe_float(indicators.get("ema200"))
        atr = safe_float(indicators.get("atr"))
        rsi = safe_float(indicators.get("rsi"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))

        if 12 <= pe <= 22 and "pe" in fundamentals and fundamentals["pe"] is not None:
            score += 3.0
            evidence.append(f"Fair P/E: {pe:.2f} (+3)")
            
        if price > 0 and ema50 > 0 and ema200 > 0:
            lower = min(ema50, ema200)
            upper = max(ema50, ema200)
            if lower <= price <= upper:
                score += 3.0
                evidence.append("Price in EMA corridor (+3)")
                
        if price > 0 and (atr / price) < 0.02:
            score += 2.0
            evidence.append("Low ATR/price ratio (+2)")
            
        if 40 <= rsi <= 60:
            score += 1.0
            evidence.append(f"RSI 40-60: {rsi:.2f} (+1)")
            
        if 0.5 <= vol_ratio <= 1.5:
            score += 1.0
            evidence.append("Moderate volume (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence
        )


class LowVolatilityDividend:
    name = "low_volatility_dividend"
    display_name = "Low Volatility Dividend"
    category = StrategyCategory.NEUTRAL
    description = "ATR/Price < 2% + Dividend yield > 1% + RSI 40-60 + Price near EMA200."
    required_indicators = ["atr", "price", "rsi", "ema200"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        atr = safe_float(indicators.get("atr"))
        price = safe_float(indicators.get("price"))
        div_yield = safe_float(fundamentals.get("dividend_yield"))
        rsi = safe_float(indicators.get("rsi"))
        ema200 = safe_float(indicators.get("ema200"))
        beta = safe_float(fundamentals.get("beta"), default=1.0)

        if price > 0 and (atr / price) < 0.02:
            score += 3.0
            evidence.append("Low vol: ATR/Price < 2% (+3)")
            
        if div_yield > 0.01:
            score += 2.0
            evidence.append(f"Has dividend: {div_yield:.1%} (+2)")
            
        if 40 <= rsi <= 60:
            score += 2.0
            evidence.append(f"Neutral RSI: {rsi:.2f} (+2)")
            
        if price > 0 and ema200 > 0 and 0.95 <= (price / ema200) <= 1.05:
            score += 2.0
            evidence.append("Near EMA200 (+2)")
            
        if 0 < beta < 0.8:
            score += 1.0
            evidence.append(f"Low beta: {beta:.2f} (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class ConsolidationSqueeze:
    name = "consolidation_squeeze"
    display_name = "Consolidation Squeeze"
    category = StrategyCategory.NEUTRAL
    description = "Tight BBands + Volume declining + ADX < 15 + MACD near zero."
    required_indicators = ["bb_upper", "bb_lower", "price", "volume_ratio", "adx", "macd_histogram", "rsi"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        bb_upper = safe_float(indicators.get("bb_upper"))
        bb_lower = safe_float(indicators.get("bb_lower"))
        price = safe_float(indicators.get("price"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        adx = safe_float(indicators.get("adx"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        rsi = safe_float(indicators.get("rsi"))

        if bb_upper > 0 and bb_lower > 0 and price > 0:
            bb_width = (bb_upper - bb_lower) / price
            if bb_width < 0.05:
                score += 3.0
                evidence.append(f"Tight BBands: {bb_width:.2%} width (+3)")
                
        if vol_ratio < 0.8:
            score += 2.0
            evidence.append(f"Declining volume: {vol_ratio:.2f} (+2)")
            
        if 0 < adx < 15:
            score += 3.0
            evidence.append(f"Very low ADX: {adx:.2f} (+3)")
            
        if abs(macd_hist) < 0.5:
            score += 1.0
            evidence.append("MACD flat (+1)")
            
        if 45 <= rsi <= 55:
            score += 1.0
            evidence.append(f"Neutral RSI: {rsi:.2f} (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class SectorRelativeStability:
    name = "sector_relative_stability"
    display_name = "Sector Relative Stability"
    category = StrategyCategory.NEUTRAL
    description = "Beta < 0.8 + RSI 45-55 + Stable price + Reasonable market cap."
    required_indicators = ["rsi", "atr", "price"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        beta = safe_float(fundamentals.get("beta"), default=1.0)
        rsi = safe_float(indicators.get("rsi"))
        mcap = safe_float(fundamentals.get("market_cap"))
        atr = safe_float(indicators.get("atr"))
        price = safe_float(indicators.get("price"))

        if 0 < beta < 0.8 and "beta" in fundamentals and fundamentals["beta"] is not None:
            score += 3.0
            evidence.append(f"Low beta: {beta:.2f} (+3)")
            
        if 45 <= rsi <= 55:
            score += 2.0
            evidence.append(f"Tight RSI: {rsi:.2f} (+2)")
            
        if price > 0 and (atr / price) < 0.02:
            score += 2.0
            evidence.append("Stable price (+2)")
            
        if mcap > 1e9: # > 1 billion
            score += 2.0
            evidence.append("Decent market cap (+2)")
            
        if price > 0 and (atr / price) < 0.015:
            score += 1.0
            evidence.append("Low ATR (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence
        )


class BullishRSIDivergence:
    name = "bullish_rsi_divergence"
    display_name = "Bullish RSI Divergence"
    category = StrategyCategory.REVERSAL
    description = "RSI < 40 + MACD histogram turning positive + Volume spike."
    required_indicators = ["rsi", "macd_histogram", "volume_ratio", "price", "bb_lower", "ema200", "patterns"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        price = safe_float(indicators.get("price"))
        bb_lower = safe_float(indicators.get("bb_lower"))
        ema200 = safe_float(indicators.get("ema200"))
        patterns = indicators.get("patterns", [])

        if 0 < rsi < 40:
            score += 3.0
            evidence.append(f"Oversold RSI: {rsi:.2f} (+3)")
            
        if macd_hist > -0.5:
            score += 2.0
            evidence.append("MACD improving (+2)")
            
        if vol_ratio > 1.5:
            score += 2.0
            evidence.append(f"Volume confirmation: {vol_ratio:.2f}x (+2)")
            
        if price > 0 and (bb_lower > 0 and price <= bb_lower * 1.02) or (ema200 > 0 and 0.98 <= price/ema200 <= 1.02):
            score += 2.0
            evidence.append("Price at support (+2)")
            
        if patterns:
            bullish_patterns = [p for p in patterns if "bullish" in p.get("type", "").lower() or "hammer" in p.get("type", "").lower()]
            if bullish_patterns:
                score += 1.0
                evidence.append(f"Candlestick pattern: {bullish_patterns[0].get('type')} (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class BearishRSIDivergence:
    name = "bearish_rsi_divergence"
    display_name = "Bearish RSI Divergence"
    category = StrategyCategory.REVERSAL
    description = "RSI > 70 + MACD histogram turning negative + Price at resistance."
    required_indicators = ["rsi", "macd_histogram", "price", "bb_upper", "volume_ratio", "patterns"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        rsi = safe_float(indicators.get("rsi"))
        macd_hist = safe_float(indicators.get("macd_histogram"))
        price = safe_float(indicators.get("price"))
        bb_upper = safe_float(indicators.get("bb_upper"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        patterns = indicators.get("patterns", [])

        if rsi > 70:
            score += 3.0
            evidence.append(f"Overbought RSI: {rsi:.2f} (+3)")
            
        if macd_hist < 0.5:
            score += 2.0
            evidence.append("MACD deteriorating (+2)")
            
        if price > 0 and bb_upper > 0 and price >= bb_upper * 0.98:
            score += 2.0
            evidence.append("Near BB upper (+2)")
            
        if vol_ratio > 1.5:
            score += 2.0
            evidence.append("Volume divergence (+2)")
            
        if patterns:
            bearish_patterns = [p for p in patterns if "bearish" in p.get("type", "").lower() or "star" in p.get("type", "").lower()]
            if bearish_patterns:
                score += 1.0
                evidence.append(f"Bearish candle pattern: {bearish_patterns[0].get('type')} (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class HammerEngulfingReversal:
    name = "hammer_engulfing_reversal"
    display_name = "Hammer Engulfing Reversal"
    category = StrategyCategory.REVERSAL
    description = "Bullish candlestick pattern + RSI < 35 + Volume > 1.5x average."
    required_indicators = ["patterns", "rsi", "volume_ratio", "price", "bb_lower", "ema200", "macd_histogram"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        patterns = indicators.get("patterns", [])
        rsi = safe_float(indicators.get("rsi"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))
        price = safe_float(indicators.get("price"))
        bb_lower = safe_float(indicators.get("bb_lower"))
        ema200 = safe_float(indicators.get("ema200"))
        macd_hist = safe_float(indicators.get("macd_histogram"))

        has_pattern = False
        if patterns:
            target_patterns = [p for p in patterns if p.get("type", "").lower() in ["hammer", "bullish_engulfing"]]
            if target_patterns:
                has_pattern = True
                score += 3.0
                evidence.append(f"Pattern detected: {target_patterns[0].get('type')} (+3)")
                
        if 0 < rsi < 35:
            score += 3.0
            evidence.append(f"Oversold RSI: {rsi:.2f} (+3)")
            
        if vol_ratio > 1.5:
            score += 2.0
            evidence.append(f"Volume confirmation: {vol_ratio:.2f}x (+2)")
            
        if price > 0 and (bb_lower > 0 and price <= bb_lower * 1.02) or (ema200 > 0 and 0.98 <= price/ema200 <= 1.02):
            score += 1.0
            evidence.append("Near support (+1)")
            
        if macd_hist > -1.0:
            score += 1.0
            evidence.append("MACD flattening (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0 and has_pattern,
            evidence=evidence,
        )


class OverboughtReversal:
    name = "overbought_reversal"
    display_name = "Overbought Reversal"
    category = StrategyCategory.REVERSAL
    description = "RSI > 80 + Price > BB upper + MACD bearish + Bearish candle pattern."
    required_indicators = ["rsi", "price", "bb_upper", "macd_crossover", "macd_histogram", "patterns", "volume_ratio"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        rsi = safe_float(indicators.get("rsi"))
        price = safe_float(indicators.get("price"))
        bb_upper = safe_float(indicators.get("bb_upper"))
        macd_cross = indicators.get("macd_crossover")
        macd_hist = safe_float(indicators.get("macd_histogram"))
        patterns = indicators.get("patterns", [])
        vol_ratio = safe_float(indicators.get("volume_ratio"))

        if rsi > 80:
            score += 3.0
            evidence.append(f"Extreme RSI: {rsi:.2f} (+3)")
            
        if price > 0 and bb_upper > 0 and price > bb_upper:
            score += 2.0
            evidence.append("Above BB upper (+2)")
            
        if macd_cross == "bearish" or macd_hist < 0:
            score += 2.0
            evidence.append("MACD weakening (+2)")
            
        if patterns:
            bearish_patterns = [p for p in patterns if p.get("type", "").lower() in ["bearish_engulfing", "shooting_star"]]
            if bearish_patterns:
                score += 2.0
                evidence.append(f"Pattern detected: {bearish_patterns[0].get('type')} (+2)")
                
        if vol_ratio > 1.5:
            score += 1.0
            evidence.append("High volume on reversal (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )


class VWAPReclaimReversal:
    name = "vwap_reclaim_reversal"
    display_name = "VWAP Reclaim Reversal"
    category = StrategyCategory.REVERSAL
    description = "Price crosses above VWAP + RSI > 40 + Supertrend bullish + ADX rising."
    required_indicators = ["price", "vwap", "rsi", "supertrend_direction", "adx", "volume_ratio"]

    def score(self, indicators: dict, fundamentals: dict) -> StrategyResult:
        score = 0.0
        evidence = []
        
        price = safe_float(indicators.get("price"))
        vwap = safe_float(indicators.get("vwap"))
        rsi = safe_float(indicators.get("rsi"))
        st_dir = safe_float(indicators.get("supertrend_direction"))
        adx = safe_float(indicators.get("adx"))
        vol_ratio = safe_float(indicators.get("volume_ratio"))

        if price > 0 and vwap > 0 and price > vwap:
            score += 3.0
            evidence.append("VWAP reclaim (+3)")
            
        if rsi > 40:
            score += 2.0
            evidence.append(f"RSI improving: {rsi:.2f} (+2)")
            
        if st_dir == 1:
            score += 2.0
            evidence.append("Supertrend flip (+2)")
            
        if adx > 20:
            score += 2.0
            evidence.append(f"ADX rising: {adx:.2f} (+2)")
            
        if vol_ratio > 1.2:
            score += 1.0
            evidence.append(f"Volume expanding: {vol_ratio:.2f} (+1)")
            
        score = min(10.0, score)
        return StrategyResult(
            strategy_name=self.name,
            score=score,
            category=self.category,
            triggered=score >= 6.0,
            evidence=evidence,
        )
