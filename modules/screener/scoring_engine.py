"""
AARKAAI – Multi-Factor Scoring Engine

Combines all individual engine scores (strategy, fundamental, technical,
momentum, valuation, risk, institutional, F&O, SMC, regime, forecast)
into a weighted composite score with regime-adaptive weight adjustment.

Produces a final signal (STRONG_BUY to STRONG_SELL) and conviction level
(HIGH, MEDIUM, LOW) based on composite score and data quality.
"""
from __future__ import annotations

import logging
from typing import Optional

from modules.screener.schemas import (
    ConvictionLevel,
    DataQuality,
    MarketRegime,
    ScoreBreakdown,
    SignalType,
)

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Weighted multi-factor composite scoring with regime-adaptive weights.

    Default weights sum to 1.0 across all engines. When certain engines
    report DataQuality.UNAVAILABLE, their weight is redistributed
    proportionally to the remaining engines.

    Market regime can shift weight emphasis:
      - BULL_TREND: heavier momentum + technical
      - BEAR_TREND: heavier fundamental + valuation + risk
      - RANGE_BOUND: heavier valuation + institutional
      - HIGH_VOLATILITY: heavier risk + regime + F&O
      - CRISIS: heavier risk + fundamental + valuation
    """

    # Default engine weights (sum = 1.0)
    DEFAULT_WEIGHTS: dict[str, float] = {
        "strategy": 0.15,
        "fundamental": 0.15,
        "technical": 0.12,
        "momentum": 0.12,
        "valuation": 0.10,
        "risk": 0.10,
        "institutional": 0.08,
        "fno": 0.05,
        "smc": 0.05,
        "regime": 0.04,
        "forecast": 0.04,
    }

    # Regime-specific weight overrides (partial — only override changed weights)
    REGIME_WEIGHT_OVERRIDES: dict[MarketRegime, dict[str, float]] = {
        MarketRegime.BULL_TREND: {
            "momentum": 0.18,
            "technical": 0.15,
            "fundamental": 0.12,
            "valuation": 0.08,
        },
        MarketRegime.BEAR_TREND: {
            "fundamental": 0.20,
            "valuation": 0.15,
            "risk": 0.15,
            "momentum": 0.08,
            "technical": 0.08,
        },
        MarketRegime.RANGE_BOUND: {
            "valuation": 0.18,
            "institutional": 0.12,
            "strategy": 0.12,
            "momentum": 0.08,
        },
        MarketRegime.HIGH_VOLATILITY: {
            "risk": 0.20,
            "regime": 0.10,
            "fno": 0.10,
            "momentum": 0.08,
            "strategy": 0.10,
        },
        MarketRegime.CRISIS: {
            "risk": 0.25,
            "fundamental": 0.20,
            "valuation": 0.15,
            "momentum": 0.05,
            "technical": 0.05,
            "strategy": 0.08,
            "institutional": 0.05,
            "fno": 0.03,
            "smc": 0.03,
            "regime": 0.07,
            "forecast": 0.04,
        },
    }

    # Signal classification thresholds
    SIGNAL_THRESHOLDS: list[tuple[float, SignalType]] = [
        (8.5, SignalType.STRONG_BUY),
        (7.0, SignalType.BUY),
        (6.0, SignalType.ACCUMULATE),
        (4.5, SignalType.HOLD),
        (3.5, SignalType.REDUCE),
        (2.0, SignalType.SELL),
        (0.0, SignalType.STRONG_SELL),
    ]

    def _get_effective_weights(
        self,
        scores: dict[str, ScoreBreakdown],
        regime: MarketRegime,
    ) -> dict[str, float]:
        """Compute effective weights considering regime and data availability.

        1. Start with regime-adjusted weights.
        2. Identify engines with UNAVAILABLE data quality.
        3. Strictly renormalize available weights so their sum equals 1.0000.
        """
        # Start with default, apply regime overrides
        weights = dict(self.DEFAULT_WEIGHTS)
        overrides = self.REGIME_WEIGHT_OVERRIDES.get(regime, {})
        for key, val in overrides.items():
            if key in weights:
                weights[key] = val

        # Identify available engines
        available: dict[str, float] = {}
        for key, weight in weights.items():
            score_breakdown = scores.get(key)
            if score_breakdown is not None and score_breakdown.data_quality != DataQuality.UNAVAILABLE:
                available[key] = weight

        # Strictly renormalize available weights to sum to 1.0000
        total_available = sum(available.values())
        if total_available > 0:
            available = {k: round(w / total_available, 4) for k, w in available.items()}
            diff = round(1.0 - sum(available.values()), 4)
            if diff != 0 and available:
                first_k = next(iter(available))
                available[first_k] = round(available[first_k] + diff, 4)

        return available

    def compute_composite(
        self,
        scores: dict[str, ScoreBreakdown],
        regime: MarketRegime = MarketRegime.RANGE_BOUND,
    ) -> tuple[float, SignalType, ConvictionLevel]:
        """Compute weighted composite score, signal, and conviction.

        Args:
            scores: Dict mapping engine name to ScoreBreakdown.
            regime: Current market regime for adaptive weighting.

        Returns:
            Tuple of (composite_score, signal, conviction).
        """
        effective_weights = self._get_effective_weights(scores, regime)

        if not effective_weights:
            logger.warning("No engine scores available for composite computation")
            return 5.0, SignalType.HOLD, ConvictionLevel.LOW

        # Compute weighted composite directly from normalized effective weights
        # Ensures 100% independent mathematical reproducibility from matrix table rows
        composite = 0.0
        for key, weight in effective_weights.items():
            score_bd = scores.get(key)
            if score_bd is not None:
                composite += score_bd.score * weight

        composite = round(min(10.0, max(0.0, composite)), 2)

        # Determine signal
        signal = SignalType.HOLD
        for threshold, sig_type in self.SIGNAL_THRESHOLDS:
            if composite >= threshold:
                signal = sig_type
                break

        # Determine conviction
        avg_confidence = 0.0
        full_quality_count = 0
        total_scores = 0

        for key in effective_weights:
            score_bd = scores.get(key)
            if score_bd is not None:
                avg_confidence += score_bd.confidence
                total_scores += 1
                if score_bd.data_quality == DataQuality.FULL:
                    full_quality_count += 1

        if total_scores > 0:
            avg_confidence /= total_scores

        if avg_confidence >= 0.8 and full_quality_count >= total_scores * 0.7:
            conviction = ConvictionLevel.HIGH
        elif avg_confidence >= 0.5:
            conviction = ConvictionLevel.MEDIUM
        else:
            conviction = ConvictionLevel.LOW

        # Data gap guardrail: Without F&O derivatives confirmation, conviction cannot be HIGH
        fno_score = scores.get("fno")
        if fno_score is None or fno_score.data_quality == DataQuality.UNAVAILABLE:
            if conviction == ConvictionLevel.HIGH:
                conviction = ConvictionLevel.MEDIUM

        return composite, signal, conviction

    def compute_data_quality_score(
        self,
        scores: dict[str, ScoreBreakdown],
    ) -> ScoreBreakdown:
        """Compute overall data completeness score across all engines.

        Used as the `data_quality_score` dimension in ScreenResult.
        """
        evidence: list[str] = []
        total_engines = len(self.DEFAULT_WEIGHTS)
        full_count = 0
        partial_count = 0
        unavailable_count = 0

        for key in self.DEFAULT_WEIGHTS:
            score_bd = scores.get(key)
            if score_bd is None or score_bd.data_quality == DataQuality.UNAVAILABLE:
                unavailable_count += 1
                evidence.append(f"{key}: UNAVAILABLE")
            elif score_bd.data_quality == DataQuality.PARTIAL:
                partial_count += 1
                evidence.append(f"{key}: PARTIAL")
            else:
                full_count += 1

        # Score: 10 = all full, 0 = all unavailable
        raw = (full_count * 10 + partial_count * 5) / total_engines
        quality_score = round(min(10.0, max(0.0, raw)), 2)

        if full_count > 0:
            evidence.insert(0, f"{full_count}/{total_engines} engines have full data coverage")

        if unavailable_count == total_engines:
            quality = DataQuality.UNAVAILABLE
        elif unavailable_count > total_engines * 0.5:
            quality = DataQuality.PARTIAL
        else:
            quality = DataQuality.FULL

        return ScoreBreakdown(
            score=quality_score,
            weight=0.0,  # Data quality score has no weight in composite
            confidence=1.0,  # We always know our own data quality
            data_quality=quality,
            evidence=evidence,
        )

    def generate_analyst_summary(
        self,
        composite: float,
        signal: SignalType,
        conviction: ConvictionLevel,
        scores: dict[str, ScoreBreakdown],
        name: str = "",
        sector: str = "",
    ) -> str:
        """Generate a concise analyst summary from score components.

        This is a deterministic text assembly — NOT LLM-generated.
        """
        parts: list[str] = []

        # Opening line
        parts.append(
            f"{name} receives a composite score of {composite:.1f}/10 "
            f"({signal.value}) with {conviction.value} conviction."
        )

        # Top strengths (scores >= 7.0)
        strengths = [
            (k, s) for k, s in scores.items()
            if s is not None and s.score >= 7.0 and s.data_quality != DataQuality.UNAVAILABLE
        ]
        if strengths:
            strength_names = [k.replace("_", " ").title() for k, _ in strengths[:3]]
            parts.append(f"Key strengths: {', '.join(strength_names)}.")

        # Top weaknesses (scores < 4.0)
        weaknesses = [
            (k, s) for k, s in scores.items()
            if s is not None and s.score < 4.0 and s.data_quality != DataQuality.UNAVAILABLE
        ]
        if weaknesses:
            weakness_names = [k.replace("_", " ").title() for k, _ in weaknesses[:3]]
            parts.append(f"Areas of concern: {', '.join(weakness_names)}.")

        # Fundamental highlight
        fund = scores.get("fundamental")
        if fund and fund.data_quality != DataQuality.UNAVAILABLE and fund.evidence:
            parts.append(fund.evidence[0])

        # Momentum highlight
        mom = scores.get("momentum")
        if mom and mom.data_quality != DataQuality.UNAVAILABLE and mom.evidence:
            parts.append(mom.evidence[0])

        return " ".join(parts)

    def extract_key_catalysts(self, scores: dict[str, ScoreBreakdown]) -> list[str]:
        """Extract positive catalysts from high-scoring engines."""
        catalysts: list[str] = []
        for key in ("fundamental", "momentum", "strategy", "institutional"):
            bd = scores.get(key)
            if bd and bd.score >= 6.0:
                for ev in bd.evidence:
                    if any(w in ev.lower() for w in ("strong", "excellent", "bullish", "surge", "positive", "attractive")):
                        catalysts.append(ev)
                        if len(catalysts) >= 5:
                            return catalysts
        return catalysts

    def extract_key_risks(self, scores: dict[str, ScoreBreakdown]) -> list[str]:
        """Extract risk factors from low-scoring engines."""
        risks: list[str] = []
        for key in ("risk", "valuation", "fundamental", "momentum"):
            bd = scores.get(key)
            if bd and bd.score < 5.0:
                for ev in bd.evidence:
                    if any(w in ev.lower() for w in ("concern", "negative", "decline", "high", "elevated", "weak", "loss", "risk", "bearish")):
                        risks.append(ev)
                        if len(risks) >= 5:
                            return risks
        return risks
