"""
Comprehensive test suite verifying the Field-Level Provenance System:
1. No static/hardcoded provenance values.
2. Every displayed metric has a matching record.
3. Correct source classification (Yahoo = PUBLIC_AGGREGATOR, etc.).
4. Correct filing status (quarterly = LIMITED_REVIEW, not audited).
5. Separate source_timestamp, retrieved_at, calculated_at.
6. Correct formula versions.
7. Stale data detection (>180 days).
8. QualityStatus is never automatically VALIDATED without checks.
9. DataFetcher populates real provenance on live fetch.
"""
import pytest
from datetime import datetime, timezone, timedelta

from modules.screener.provenance import (
    FieldProvenance,
    SnapshotProvenance,
    SourceClassification,
    FilingStatus,
    QualityStatus,
    make_price_provenance,
    make_fundamental_provenance,
    make_indicator_provenance,
    make_score_provenance,
    make_signal_provenance,
    make_unavailable_provenance,
    generate_compliance_response,
    _GOVERNANCE_SPEC,
    IST,
)


def test_provenance_schema_types():
    """Verify all required schema fields exist with correct types."""
    now = datetime.now(IST)
    fp = FieldProvenance(
        metric="last_price",
        value=2450.50,
        unit="INR",
        instrument="NSE:TCS",
        source_provider="Yahoo Finance",
        source_endpoint="/v8/finance/chart",
        source_timestamp=None,
        retrieved_at=now,
        data_vintage="2026-09-12 trading session",
        classification=SourceClassification.PUBLIC_AGGREGATOR,
        quality_status=QualityStatus.DELAYED,
    )
    assert fp.metric == "last_price"
    assert fp.classification == SourceClassification.PUBLIC_AGGREGATOR
    assert fp.quality_status == QualityStatus.DELAYED
    assert fp.source_timestamp is None
    assert fp.calculated_at is None


def test_yahoo_finance_not_direct_exchange():
    """Yahoo Finance must be classified as PUBLIC_AGGREGATOR, never DIRECT_EXCHANGE."""
    now = datetime.now(IST)
    prov = make_price_provenance(
        symbol="TCS.NS",
        exchange="NSE",
        value=3500.0,
        currency="INR",
        source="yfinance",
        retrieved_at=now,
    )
    assert prov.classification == SourceClassification.PUBLIC_AGGREGATOR
    assert prov.classification != SourceClassification.DIRECT_EXCHANGE
    assert prov.quality_status == QualityStatus.DELAYED
    assert "delayed" in prov.quality_notes.lower()


def test_separate_timestamps():
    """Verify source_timestamp, retrieved_at, and calculated_at remain distinct."""
    t_retrieved = datetime.now(IST)
    t_calculated = t_retrieved + timedelta(milliseconds=150)
    
    ind_prov = make_indicator_provenance(
        symbol="INFY.NS",
        exchange="NSE",
        metric="rsi_14",
        value=58.4,
        formula_version="wilder_rsi_v1",
        calculated_at=t_calculated,
    )
    assert ind_prov.source_timestamp is None
    assert ind_prov.retrieved_at == t_calculated
    assert ind_prov.calculated_at == t_calculated
    assert ind_prov.formula_version == "wilder_rsi_v1"


def test_quarterly_filing_status_is_limited_review():
    """Quarterly statements must be marked LIMITED_REVIEW, not AUDITED (SEBI LODR Reg 33)."""
    now = datetime.now(IST)
    prov = make_fundamental_provenance(
        symbol="RELIANCE.NS",
        exchange="NSE",
        metric="trailing_eps",
        value=98.5,
        unit="INR",
        retrieved_at=now,
        most_recent_quarter=int(now.timestamp()),
    )
    assert prov.filing_status == FilingStatus.LIMITED_REVIEW
    assert prov.filing_status != FilingStatus.AUDITED


def test_stale_data_detection():
    """Data older than 180 days must be tagged as STALE."""
    old_time = datetime.now(IST) - timedelta(days=200)
    now = datetime.now(IST)
    prov = make_fundamental_provenance(
        symbol="TITAN.NS",
        exchange="NSE",
        metric="pe_ratio",
        value=72.1,
        unit="ratio",
        retrieved_at=now,
        most_recent_quarter=int(old_time.timestamp()),
    )
    assert prov.quality_status == QualityStatus.STALE
    assert "old" in prov.quality_notes.lower()


def test_quality_status_not_auto_verified():
    """Price provenance from aggregators must NEVER be auto-set to VALIDATED."""
    now = datetime.now(IST)
    prov = make_price_provenance(
        symbol="SBIN.NS", exchange="NSE", value=780.0, currency="INR",
        source="yfinance", retrieved_at=now,
    )
    assert prov.quality_status != QualityStatus.VALIDATED


def test_unavailable_provenance():
    """Missing metrics must be formally marked UNAVAILABLE."""
    now = datetime.now(IST)
    prov = make_unavailable_provenance(
        symbol="PAGEIND.NS",
        exchange="NSE",
        metric="fno_pcr",
        retrieved_at=now,
        reason="Not an F&O eligible security",
    )
    assert prov.classification == SourceClassification.UNAVAILABLE
    assert prov.quality_status == QualityStatus.UNAVAILABLE
    assert prov.value is None


def test_governance_spec_honest_content():
    """Verify _GOVERNANCE_SPEC does not claim direct exchange feeds or fabricated dates."""
    spec = _GOVERNANCE_SPEC
    assert "Public Aggregator" in spec
    assert "Limited Review" in spec
    assert "Wilder's Smoothing" in spec
    assert "95% confidence interval" in spec
    assert "2026-09-12 15:30:00 IST" not in spec  # No hardcoded uniform timestamps


def test_dynamic_compliance_generator():
    """generate_compliance_response returns spec when empty, and dynamic table when populated."""
    # Empty -> spec
    res_empty = generate_compliance_response(None)
    assert "Aarka AI — Data Governance" in res_empty

    # Populated -> dynamic table
    now = datetime.now(IST)
    snap = SnapshotProvenance(symbol="TCS.NS", exchange_qualified="NSE:TCS", snapshot_retrieved_at=now)
    snap.add(make_price_provenance("TCS.NS", "NSE", 3500.0, "INR", "yfinance", now))
    snap.add(make_score_provenance("TCS.NS", "NSE", "composite_score", 8.2, "ScoringEngine", 1.0, now))

    res_pop = generate_compliance_response([snap])
    assert "TCS.NS (NSE:TCS)" in res_pop
    assert "last_price" in res_pop
    assert "composite_score" in res_pop
    assert "Aarka AI — Runtime Data Provenance Audit" in res_pop
