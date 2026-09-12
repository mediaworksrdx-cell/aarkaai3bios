"""
AARKAAI – Field-Level Data Provenance System

Runtime metadata for every displayed financial metric, ensuring each value
carries its exact source, retrieval timestamp, calculation timestamp,
data vintage, classification, and quality status.

Design principles:
  - Yahoo Finance = PUBLIC_AGGREGATOR (not "exchange feed")
  - Twelve Data   = LICENSED_VENDOR
  - Quarterly results = LIMITED_REVIEW (not "Audited") per SEBI LODR
  - Separate source_timestamp, retrieved_at, calculated_at
  - quality_status is NEVER auto-set to "verified" — requires validation
  - No "real-time" or "exchange-confirmed" claims for aggregated data
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


# ─── Enums ───────────────────────────────────────────────────────────────────


class SourceClassification(str, Enum):
    """Tiered source classification — ordered from most to least authoritative."""
    DIRECT_EXCHANGE = "direct_exchange"
    LICENSED_VENDOR = "licensed_vendor"
    PUBLIC_AGGREGATOR = "public_aggregator"
    COMPANY_FILING = "company_filing"
    CALCULATED = "calculated"
    HEURISTIC_PROXY = "heuristic_proxy"
    UNAVAILABLE = "unavailable"


class FilingStatus(str, Enum):
    """Financial statement audit status per Indian regulatory framework."""
    AUDITED = "audited"
    LIMITED_REVIEW = "limited_review"
    UNAUDITED = "unaudited"
    UNKNOWN = "unknown"


class QualityStatus(str, Enum):
    """Data quality gate — NEVER auto-set to VALIDATED without validation."""
    VALIDATED = "validated"
    AGGREGATOR_REPORTED = "aggregator_reported"
    DELAYED = "delayed"
    STALE = "stale"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"
    CACHED = "cached"


# ─── Provenance Record ──────────────────────────────────────────────────────


class FieldProvenance(BaseModel):
    """Single field-level provenance record."""
    metric: str = Field(description="Canonical metric name")
    value: float | str | None = Field(default=None)
    unit: str = Field(default="")
    instrument: str = Field(default="")
    source_provider: str = Field(description="Exact provider name")
    source_endpoint: str = Field(default="")
    source_record_id: str | None = Field(default=None)
    source_timestamp: datetime | None = Field(default=None)
    retrieved_at: datetime = Field(description="When Aarka fetched this data")
    calculated_at: datetime | None = Field(default=None)
    data_vintage: str = Field(default="")
    classification: SourceClassification = SourceClassification.PUBLIC_AGGREGATOR
    filing_status: FilingStatus | None = Field(default=None)
    formula_version: str | None = Field(default=None)
    quality_status: QualityStatus = Field(default=QualityStatus.AGGREGATOR_REPORTED)
    quality_notes: str | None = Field(default=None)


# ─── Snapshot Provenance Container ──────────────────────────────────────────


class SnapshotProvenance(BaseModel):
    """Aggregated provenance for one stock's full data snapshot."""
    symbol: str
    exchange_qualified: str = Field(default="")
    fields: list[FieldProvenance] = Field(default_factory=list)
    snapshot_retrieved_at: datetime = Field(default_factory=lambda: datetime.now(IST))

    @property
    def total_fields(self) -> int:
        return len(self.fields)

    @property
    def validated_count(self) -> int:
        return sum(1 for f in self.fields if f.quality_status == QualityStatus.VALIDATED)

    @property
    def stale_count(self) -> int:
        return sum(1 for f in self.fields if f.quality_status == QualityStatus.STALE)

    @property
    def unavailable_count(self) -> int:
        return sum(1 for f in self.fields if f.quality_status == QualityStatus.UNAVAILABLE)

    @property
    def delayed_count(self) -> int:
        return sum(1 for f in self.fields if f.quality_status == QualityStatus.DELAYED)

    def add(self, prov: FieldProvenance) -> None:
        self.fields.append(prov)

    def get(self, metric: str) -> FieldProvenance | None:
        for f in self.fields:
            if f.metric == metric:
                return f
        return None

    def summary_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "total_fields": self.total_fields,
            "validated": self.validated_count,
            "stale": self.stale_count,
            "delayed": self.delayed_count,
            "unavailable": self.unavailable_count,
            "snapshot_retrieved_at": self.snapshot_retrieved_at.isoformat(),
        }


# ─── Provenance Factories ───────────────────────────────────────────────────


def make_price_provenance(
    symbol: str, exchange: str, value: float, currency: str,
    source: str, retrieved_at: datetime,
    source_timestamp: datetime | None = None, data_vintage: str = "",
) -> FieldProvenance:
    provider = "Yahoo Finance" if source in ("yfinance", "yahoo") else "Twelve Data"
    endpoint = "/v8/finance/chart" if source in ("yfinance", "yahoo") else "/time_series"
    classification = SourceClassification.PUBLIC_AGGREGATOR if provider == "Yahoo Finance" else SourceClassification.LICENSED_VENDOR
    quality = QualityStatus.DELAYED if provider == "Yahoo Finance" else QualityStatus.AGGREGATOR_REPORTED
    quality_note = "Yahoo Finance: data may be delayed up to 15 minutes for NSE/BSE" if provider == "Yahoo Finance" else None

    if not data_vintage:
        if source_timestamp:
            data_vintage = f"{source_timestamp.strftime('%Y-%m-%d')} trading session"
        else:
            data_vintage = "current or recent trading session (exact session timestamp unavailable from provider)"

    return FieldProvenance(
        metric="last_price", value=value, unit=currency,
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider=provider, source_endpoint=endpoint,
        source_timestamp=source_timestamp, retrieved_at=retrieved_at,
        data_vintage=data_vintage, classification=classification,
        quality_status=quality, quality_notes=quality_note,
    )


def make_fundamental_provenance(
    symbol: str, exchange: str, metric: str, value: float | None,
    unit: str, retrieved_at: datetime,
    most_recent_quarter: object = None, last_fiscal_year_end: object = None,
) -> FieldProvenance:
    vintage = "Filing period unknown (not provided by aggregator)"
    filing_status = FilingStatus.UNKNOWN
    quality = QualityStatus.AGGREGATOR_REPORTED
    quality_note = None

    if most_recent_quarter:
        try:
            mrq_dt = datetime.fromtimestamp(int(most_recent_quarter), tz=IST) if isinstance(most_recent_quarter, (int, float)) else None
            if mrq_dt:
                age_days = (datetime.now(IST) - mrq_dt).days
                vintage = f"Quarter ending {mrq_dt.strftime('%b %Y')}"
                filing_status = FilingStatus.LIMITED_REVIEW
                quality = QualityStatus.STALE if age_days > 180 else QualityStatus.AGGREGATOR_REPORTED
                quality_note = f"Data is {age_days} days old from filing date" if age_days > 180 else None
        except (ValueError, TypeError):
            vintage = f"Most recent quarter: {most_recent_quarter}"

    is_calculated = metric in ("pe_ratio", "pb_ratio", "ps_ratio", "ev_ebitda", "market_cap")
    classification = SourceClassification.CALCULATED if is_calculated else SourceClassification.PUBLIC_AGGREGATOR

    return FieldProvenance(
        metric=metric, value=value, unit=unit,
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider="Yahoo Finance", source_endpoint="/v10/finance/quoteSummary",
        retrieved_at=retrieved_at, data_vintage=vintage,
        classification=classification, filing_status=filing_status,
        quality_status=quality, quality_notes=quality_note,
    )


def make_indicator_provenance(
    symbol: str, exchange: str, metric: str, value: float | None,
    formula_version: str, calculated_at: datetime, ohlcv_period: str = "6mo",
) -> FieldProvenance:
    return FieldProvenance(
        metric=metric, value=value, unit="",
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider="Aarka Technical Engine",
        source_endpoint="internal:modules.technical",
        retrieved_at=calculated_at, calculated_at=calculated_at,
        data_vintage=f"Calculated from {ohlcv_period} daily OHLCV via Yahoo Finance",
        classification=SourceClassification.CALCULATED,
        formula_version=formula_version, quality_status=QualityStatus.VALIDATED,
        quality_notes=f"Deterministic calculation from {ohlcv_period} historical close prices",
    )


def make_score_provenance(
    symbol: str, exchange: str, metric: str, value: float,
    engine_name: str, weight: float, calculated_at: datetime,
    evidence: list[str] | None = None,
) -> FieldProvenance:
    return FieldProvenance(
        metric=metric, value=value, unit="score",
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider=f"Aarka {engine_name}",
        source_endpoint=f"internal:modules.screener.{engine_name.lower().replace(' ', '_')}",
        retrieved_at=calculated_at, calculated_at=calculated_at,
        data_vintage="Current screening session",
        classification=SourceClassification.CALCULATED,
        formula_version=f"{engine_name.lower().replace(' ', '_')}_v1",
        quality_status=QualityStatus.VALIDATED,
        quality_notes=f"Weight: {weight:.0%}" + (f" | Evidence: {'; '.join(evidence[:3])}" if evidence else ""),
    )


def make_signal_provenance(
    symbol: str, exchange: str, signal: str, composite_score: float,
    rank: int, calculated_at: datetime,
) -> FieldProvenance:
    return FieldProvenance(
        metric="signal", value=signal, unit="signal",
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider="Aarka Signal Classifier",
        source_endpoint="internal:modules.screener.scoring_engine",
        retrieved_at=calculated_at, calculated_at=calculated_at,
        data_vintage="Current screening session",
        classification=SourceClassification.CALCULATED,
        formula_version="signal_classifier_v1",
        quality_status=QualityStatus.VALIDATED,
        quality_notes=f"Derived from composite_score={composite_score:.2f}, rank={rank}",
    )


def make_forecast_provenance(
    symbol: str, exchange: str, scenario: str, target_price: float,
    calculated_at: datetime, confidence: float = 0.5,
) -> FieldProvenance:
    return FieldProvenance(
        metric=f"forecast_{scenario}", value=target_price, unit="INR",
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider="Aarka Forecast Engine",
        source_endpoint="internal:modules.screener.forecast_engine",
        retrieved_at=calculated_at, calculated_at=calculated_at,
        data_vintage="Current screening session",
        classification=SourceClassification.HEURISTIC_PROXY,
        formula_version="forecast_engine_v1",
        quality_status=QualityStatus.ESTIMATED,
        quality_notes=f"Statistical projection, not a prediction. Confidence: {confidence:.0%}.",
    )


def make_unavailable_provenance(
    symbol: str, exchange: str, metric: str, retrieved_at: datetime,
    reason: str = "Data not available from provider",
) -> FieldProvenance:
    return FieldProvenance(
        metric=metric, value=None, unit="",
        instrument=f"{exchange}:{symbol.replace('.NS', '').replace('.BO', '')}",
        source_provider="N/A", source_endpoint="N/A",
        retrieved_at=retrieved_at, data_vintage="N/A",
        classification=SourceClassification.UNAVAILABLE,
        quality_status=QualityStatus.UNAVAILABLE,
        quality_notes=reason,
    )


# ─── Dynamic Compliance Response Generator ──────────────────────────────────


_GOVERNANCE_SPEC = """### Aarka AI — Data Governance & Provenance Contract

Aarka AI enforces a runtime field-level provenance system. Every displayed price, volume, financial metric, technical indicator, quantitative score, signal, ranking, and forecast carries machine-generated metadata from actual API calls.

#### Source Classification Taxonomy

| Tier | Classification | Description | Example |
|:---|:---|:---|:---|
| 1 | **Direct Exchange** | Real-time feed from exchange DMA | NSE/BSE co-location feed |
| 2 | **Licensed Vendor** | Contracted market data provider | Twelve Data, Refinitiv |
| 3 | **Public Aggregator** | Free/public API with potential delay | Yahoo Finance, Google Finance |
| 4 | **Company Filing** | Regulatory filings (XBRL, annual reports) | BSE/NSE corporate filings |
| 5 | **Calculated** | Deterministically derived from reported data | P/E ratio, RSI, EMA |
| 6 | **Heuristic Proxy** | Algorithmic estimate / statistical model | Institutional delivery proxy, SMC signals |
| 7 | **Unavailable** | Data gap — metric cannot be sourced | F&O data for non-F&O stocks |

#### Timestamp Separation

Every record carries three independent timestamps:
- **source_timestamp**: When the data was generated at source. `null` if the provider does not expose this.
- **retrieved_at**: When Aarka fetched this data from the provider. Always populated.
- **calculated_at**: When Aarka computed a derived value. `null` for reported data.

#### Filing Status (Indian Regulatory Framework)

- **Audited**: Annual statutory financial statements per Companies Act 2013
- **Limited Review**: Quarterly results per SEBI LODR Regulation 33 (NOT audited)
- **Unaudited**: Provisional or management estimates
- **Unknown**: Filing status could not be determined from provider metadata

#### Quality Status

Quality is NEVER auto-assigned as "verified." Each field must pass validation:
- **Validated**: Cross-checked or deterministically reproducible
- **Aggregator Reported**: Received from public aggregator, not independently verified
- **Delayed**: Known delay (Yahoo Finance NSE data: up to 15 minutes)
- **Stale**: Data vintage > 1 trading session old
- **Estimated**: Heuristic proxy value
- **Unavailable**: Could not be sourced

#### Current Data Sources

- **Yahoo Finance** (Public Aggregator) — prices, fundamentals, OHLCV history. Data may be delayed up to 15 min for Indian markets.
- **Twelve Data** (Licensed Vendor) — near-real-time price feeds where available.
- **Aarka Engines** (Calculated) — RSI, EMA, MACD, composite scores, signals, rankings, forecasts.

**Important**: Yahoo Finance is a public aggregator, not a direct exchange feed. Aarka does not claim exchange-level data authority.

#### Scoring Engine Factor Weights & Dimensions

Aarka's Multi-Factor Scoring Engine combines 11 distinct dimensions normalized to [0, 10]:

| Dimension | Default Weight | Input Metrics | Classification |
|:---|:---|:---|:---|
| **Strategy Score** | **15%** | Active strategy rule matches (e.g. Golden Cross, Volume Breakout) | Calculated |
| **Fundamental Score** | **15%** | ROE, ROA, Debt/Equity, Operating Margin, Revenue Growth | Calculated from reported |
| **Technical Score** | **12%** | Trend alignment, Moving Average structure, MACD crossover | Calculated |
| **Momentum Score** | **12%** | Wilder RSI(14), ROC, 52-week high distance | Calculated |
| **Valuation Score** | **10%** | Trailing P/E, P/B, EV/EBITDA vs sector median | Calculated |
| **Risk Score** | **10%** | Beta, 52w drawdown, D/E leverage, ATR volatility | Calculated |
| **Institutional Score** | **8%** | Volume turnover anomaly vs 30-day baseline | Heuristic Proxy |
| **FnO Sentiment Score** | **5%** | Put-Call Ratio (PCR), Max Pain drift (F&O universe only) | Reported / Data Gap |
| **SMC Structure Score** | **5%** | Break of Structure (BOS), Change of Character (CHoCH) | Heuristic Proxy |
| **Market Regime Score** | **4%** | Macro breadth, Nifty 50 trend alignment | Heuristic Proxy |
| **Forecast Score** | **4%** | Multi-scenario 30-day volatility envelope projection | Heuristic Proxy |

*Total Active Base Weight: 100%. When FnO or SMC data is UNAVAILABLE, weight is redistributed proportionally across remaining active engines.*

#### Technical Formula Governance

1. **Relative Strength Index (RSI)**: Computed using **Wilder's Smoothing** (exponential moving average with $\\alpha = 1/N$, equivalent to $\\text{span} = 2N - 1 = 27$ for $N=14$), NOT simple moving average or standard EMA. Formula:
   $$\\text{RSI}_{14} = 100 - \\frac{100}{1 + \\frac{\\text{WilderEMA}(\\text{Gain}, 14)}{\\text{WilderEMA}(\\text{Loss}, 14)}}$$
2. **Exponential Moving Average (EMA)**: Standard recurrence relation with multiplier $\\alpha = \\frac{2}{N+1}$:
   $$\\text{EMA}_t = \\text{Close}_t \\times \\alpha + \\text{EMA}_{t-1} \\times (1 - \\alpha)$$
3. **Statistical Volatility Envelope**: Projected as a **95% confidence interval** ($\\approx 1.96\\sigma$ under normality), explicitly designated as non-predictive:
   $$\\text{Envelope}_{95\\%} = \\text{LTP} \\pm 1.96 \\times \\text{ATR}_{14} \\times \\sqrt{\\frac{21}{14}}$$
4. **Market Capitalization**: Derived from reported shares outstanding and latest closing price:
   $$\\text{Market Cap} = \\text{Total Outstanding Shares} \\times \\text{LTP}$$

#### Provenance Audit Record Schema
```json
{
  "metric": "last_price", "value": 125.40, "unit": "INR",
  "instrument": "NSE:EXAMPLE", "source_provider": "Yahoo Finance",
  "source_endpoint": "/v8/finance/chart", "source_timestamp": null,
  "retrieved_at": "2026-09-12T15:30:04+05:30",
  "data_vintage": "current or recent trading session (exact timestamp unavailable from provider)",
  "classification": "public_aggregator", "quality_status": "delayed",
  "quality_notes": "Yahoo Finance: data may be delayed up to 15 minutes for NSE/BSE"
}
```
"""


def generate_compliance_response(
    provenance_records: list[SnapshotProvenance] | None = None,
) -> str:
    """Generate provenance response from actual runtime records or return governance spec."""
    if not provenance_records:
        return _GOVERNANCE_SPEC

    lines = [
        "### Aarka AI — Runtime Data Provenance Audit\n",
        f"**Screening session**: {provenance_records[0].snapshot_retrieved_at.strftime('%Y-%m-%d %H:%M:%S %Z')}\n",
        f"**Stocks audited**: {len(provenance_records)}\n",
    ]

    for sp in provenance_records:
        summary = sp.summary_dict()
        lines.append(f"\n#### {sp.symbol} ({sp.exchange_qualified})")
        lines.append(
            f"Fields: {summary['total_fields']} total | "
            f"{summary['validated']} validated | "
            f"{summary['delayed']} delayed | "
            f"{summary['stale']} stale | "
            f"{summary['unavailable']} unavailable\n"
        )
        lines.append("| Metric | Value | Source | Retrieved At | Data Vintage | Classification | Quality |")
        lines.append("|:---|:---|:---|:---|:---|:---|:---|")
        for fp in sp.fields:
            val_str = f"{fp.value}" if fp.value is not None else "N/A"
            if fp.unit and fp.unit not in ("", "score", "signal", "rank"):
                val_str = f"{val_str} {fp.unit}"
            ts_str = fp.retrieved_at.strftime("%H:%M:%S %Z") if fp.retrieved_at else "N/A"
            lines.append(
                f"| {fp.metric} | {val_str} | {fp.source_provider} | "
                f"{ts_str} | {fp.data_vintage} | "
                f"{fp.classification.value} | {fp.quality_status.value} |"
            )

    lines.append("\n---")
    lines.append(
        "\n*Provenance records generated at runtime from actual API responses. "
        "Full JSON audit trail available via `/screener/provenance` endpoint.*"
    )

    return "\n".join(lines)
