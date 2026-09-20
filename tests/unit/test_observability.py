"""
Unit Tests for AARKAAI Observability, Prometheus Metrics & Audit Chain Verification.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from modules.observability import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    REGISTRY,
    GATEWAY_REQUESTS,
    GATEWAY_DENIALS,
)
from modules.tool_gateway import (
    ToolGateway,
    ToolGatewayError,
    OperationNotPermittedError,
)
from scripts.verify_audit_chain import verify_chain


def test_counter_metrics():
    registry = MetricsRegistry()
    counter = registry.register(Counter("test_counter_total", "Test counter doc", ["method", "status"]))
    counter.inc(method="GET", status="200")
    counter.inc(2.0, method="GET", status="200")
    counter.inc(method="POST", status="500")

    output = registry.generate_latest()
    assert "# HELP test_counter_total Test counter doc" in output
    assert "# TYPE test_counter_total counter" in output
    assert 'test_counter_total{method="GET",status="200"} 3.0' in output
    assert 'test_counter_total{method="POST",status="500"} 1.0' in output


def test_gauge_metrics():
    registry = MetricsRegistry()
    gauge = registry.register(Gauge("test_gauge_val", "Test gauge doc", ["instance"]))
    gauge.set(42.5, instance="app1")
    gauge.inc(2.5, instance="app1")
    gauge.dec(5.0, instance="app1")

    output = registry.generate_latest()
    assert "# HELP test_gauge_val Test gauge doc" in output
    assert "# TYPE test_gauge_val gauge" in output
    assert 'test_gauge_val{instance="app1"} 40.0' in output


def test_histogram_metrics():
    registry = MetricsRegistry()
    hist = registry.register(Histogram("test_duration_seconds", "Test histogram doc", ["endpoint"], buckets=(0.1, 0.5, 1.0)))
    hist.observe(0.05, endpoint="/prompt")
    hist.observe(0.4, endpoint="/prompt")
    hist.observe(0.9, endpoint="/prompt")
    hist.observe(2.5, endpoint="/prompt")

    output = registry.generate_latest()
    assert 'test_duration_seconds_bucket{endpoint="/prompt",le="0.1"} 1' in output
    assert 'test_duration_seconds_bucket{endpoint="/prompt",le="0.5"} 2' in output
    assert 'test_duration_seconds_bucket{endpoint="/prompt",le="1.0"} 3' in output
    assert 'test_duration_seconds_bucket{endpoint="/prompt",le="+Inf"} 4' in output
    assert 'test_duration_seconds_count{endpoint="/prompt"} 4' in output


def test_gateway_increments_observability_metrics(tmp_path):
    mock_reg = MagicMock()
    mock_reg.execute_tool.return_value = "Read success"

    gateway = ToolGateway(
        registry=mock_reg,
        workspace_dir=str(tmp_path),
        user_id="user_obs",
        session_id="sess_obs",
        approval_context={},
    )

    # 1. Successful read-only dispatch
    gateway.dispatch("FileReadTool", {"path": "test.txt"})
    output = REGISTRY.generate_latest()
    assert 'aarkaai_gateway_requests_total{tool="FileReadTool",classification="READ_ONLY",status="success"}' in output

    # 2. Blocked EXEC tool
    with pytest.raises(OperationNotPermittedError):
        gateway.dispatch("BashTool", {"command": "echo blocked"})

    output_after_denial = REGISTRY.generate_latest()
    assert 'aarkaai_gateway_denials_total{tool="BashTool",reason="no_approval_mechanism"}' in output_after_denial


def test_verify_audit_chain_tool(tmp_path):
    import hashlib
    log_file = tmp_path / "test_audit.jsonl"

    rec1 = {
        "event_type": "test.event.one",
        "timestamp": 1000.0,
        "prev_record_hash": "0" * 64,
        "details": {"key": "val1"},
    }
    rec1["record_hash"] = hashlib.sha256(json.dumps(rec1, sort_keys=True).encode("utf-8")).hexdigest()

    rec2 = {
        "event_type": "test.event.two",
        "timestamp": 1005.0,
        "prev_record_hash": rec1["record_hash"],
        "details": {"key": "val2"},
    }
    rec2["record_hash"] = hashlib.sha256(json.dumps(rec2, sort_keys=True).encode("utf-8")).hexdigest()

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec1) + "\n")
        f.write(json.dumps(rec2) + "\n")

    is_valid, report = verify_chain(log_file)
    assert is_valid is True
    assert report["valid_records"] == 2
    assert report["invalid_records"] == 0
    assert report["chain_head_hash"] == rec2["record_hash"]

    # 1. Test Content Tampering (modify details without updating hash)
    tampered_log = tmp_path / "test_tampered.jsonl"
    tampered_rec2 = dict(rec2)
    tampered_rec2["details"] = {"key": "TAMPERED_VAL"}
    with open(tampered_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec1) + "\n")
        f.write(json.dumps(tampered_rec2) + "\n")

    is_valid_tampered, report_tampered = verify_chain(tampered_log)
    assert is_valid_tampered is False
    assert report_tampered["invalid_records"] == 1
    assert "Tampered record content" in report_tampered["errors"][0]

    # 2. Test Break in Chain Linkage
    broken_log = tmp_path / "test_broken.jsonl"
    broken_rec2 = dict(rec2)
    broken_rec2["prev_record_hash"] = "1" * 64
    broken_rec2["record_hash"] = hashlib.sha256(json.dumps(broken_rec2, sort_keys=True).encode("utf-8")).hexdigest()
    with open(broken_log, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec1) + "\n")
        f.write(json.dumps(broken_rec2) + "\n")

    is_valid_broken, report_broken = verify_chain(broken_log)
    assert is_valid_broken is False
    assert "Break in hash chain" in report_broken["errors"][0]

