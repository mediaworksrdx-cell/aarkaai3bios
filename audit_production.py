"""AARKAAI Pre-Production Audit: Imports + Runtime + Edge Cases"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

passed = 0
failed = 0
warnings = []

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  PASS: {name}")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {name} -> {type(e).__name__}: {e}")

def safe(s):
    return str(s).encode('ascii', errors='replace').decode('ascii')[:120]

# ═══════════════════════════════════════════════════════════════
print("\n=== 1. Import Chain Audit ===")
imports = [
    "import config", "import schemas", "import database",
    "from modules import finance", "from modules import technical",
    "from modules import web_search", "from modules import semantic_filter",
    "from modules import memory", "from modules import rag",
    "from modules import permissions", "from modules import auto_learn",
    "from modules import financial_calculator", "from modules import fundamentals",
    "from modules import market_datetime", "from modules import portfolio",
    "from modules import fno_analytics", "from modules import notifications",
    "from modules import document_parser", "from modules import tool_router",
    "from modules import subscription",
    "from modules.tools import registry",
    "from modules.subagents import SUBAGENT_REGISTRY, list_subagents",
    "from modules.subagents.orchestrator import get_orchestrator",
    "from modules.subagents.base import CognitiveSubagent, SubagentResult",
]
for stmt in imports:
    t0 = time.time()
    try:
        exec(stmt, globals())
        dt = time.time() - t0
        tag = "[SLOW]" if dt > 3.0 else "[PASS]"
        print(f"  {tag} {stmt} ({dt:.2f}s)")
        passed += 1
        if dt > 3.0:
            warnings.append(f"Slow import: {stmt} ({dt:.1f}s)")
    except Exception as e:
        dt = time.time() - t0
        print(f"  [FAIL] {stmt} -> {e}")
        failed += 1

# ═══════════════════════════════════════════════════════════════
print("\n=== 2. Pipeline Edge Cases ===")
from pipeline import _sanitize_query, _detect_language, _is_reasoning_query

edge_inputs = [
    ("empty", ""),
    ("long_10k", "A" * 10000),
    ("unicode", "こんにちは世界 🚀 TCS price"),
    ("sql_injection", "'; DROP TABLE users; --"),
    ("xss", "<script>alert('XSS')</script>"),
    ("null_bytes", "hello\x00world"),
]
for label, inp in edge_inputs:
    test(f"_sanitize_query({label})", lambda i=inp: _sanitize_query(i))
    test(f"_detect_language({label})", lambda i=inp: _detect_language(i))
    test(f"_is_reasoning_query({label})", lambda i=inp: _is_reasoning_query(i))

# ═══════════════════════════════════════════════════════════════
print("\n=== 3. Tool Router Edge Cases ===")
from modules.tool_router import _heuristic_route

router_inputs = [
    ("empty", ""),
    ("numbers_only", "1234567890"),
    ("special_chars", "!@#$%^&*()"),
    ("long_10k", "stock " * 2000),
]
for label, inp in router_inputs:
    test(f"_heuristic_route({label})", lambda i=inp: _heuristic_route(i))

# ═══════════════════════════════════════════════════════════════
print("\n=== 4. Orchestrator Edge Cases ===")
from modules.subagents.orchestrator import CognitiveOrchestrator
o = CognitiveOrchestrator()

test("classify_complexity(empty)", lambda: o.classify_complexity(""))
test("classify_complexity(None domain)", lambda: o.classify_complexity("test", None, None))
test("orchestrate(empty, None ctx)", lambda: o.orchestrate("", None))
test("orchestrate(simple, missing keys)", lambda: o.orchestrate("hello", {"wrong": "val"}))
test("orchestrate(empty, empty ctx)", lambda: o.orchestrate("", {}))

# ═══════════════════════════════════════════════════════════════
print("\n=== 5. Finance Edge Cases ===")
from modules.finance import extract_tickers

test("extract_tickers(empty)", lambda: extract_tickers(""))
test("extract_tickers(no_tickers)", lambda: extract_tickers("hello world"))
test("extract_tickers(garbage)", lambda: extract_tickers("!@#$%^&*()"))
test("extract_tickers(sql)", lambda: extract_tickers("'; DROP TABLE;--"))

# ═══════════════════════════════════════════════════════════════
print("\n=== 6. Financial Calculator Edge Cases ===")
from modules.financial_calculator import calculate_cagr, calculate_sip

test("cagr(0,0,0)", lambda: calculate_cagr(0, 0, 0))
test("cagr(negative)", lambda: calculate_cagr(-100, -200, 5))
test("cagr(huge)", lambda: calculate_cagr(1e100, 1e200, 50))
test("cagr(div_by_zero_years)", lambda: calculate_cagr(100, 200, 0))
test("sip(0,0,0)", lambda: calculate_sip(0, 0, 0))
test("sip(negative)", lambda: calculate_sip(-100, -5, -1))

# ═══════════════════════════════════════════════════════════════
print("\n=== 7. SubagentResult Edge Cases ===")
from modules.subagents.base import SubagentResult

def assert_true(v):
    assert v, f"Expected True, got {v}"
def assert_false(v):
    assert not v, f"Expected False, got {v}"

test("SubagentResult(empty)", lambda: SubagentResult(agent_name="", output=""))
test("SubagentResult(valid).is_valid", lambda: assert_true(SubagentResult(agent_name="t", output="hi").is_valid))
test("SubagentResult(error).is_valid", lambda: assert_false(SubagentResult(agent_name="t", output="hi", error="e").is_valid))

# ═══════════════════════════════════════════════════════════════
print("\n=== 8. Security Quick Checks ===")
import config

test("config.MODEL_PATH exists", lambda: assert_true(hasattr(config, 'MODEL_PATH')))
test("config.MAX_TOKENS exists", lambda: assert_true(hasattr(config, 'MAX_TOKENS')))
test("config.MAX_QUERY_LENGTH exists", lambda: assert_true(hasattr(config, 'MAX_QUERY_LENGTH')))

# Check for dangerous defaults
if hasattr(config, 'DEBUG') and config.DEBUG:
    warnings.append("CRITICAL: DEBUG=True in production config")
if hasattr(config, 'CORS_ORIGINS'):
    origins = config.CORS_ORIGINS
    if origins == ["*"] or "*" in str(origins):
        warnings.append("HIGH: CORS allows all origins (*)")

# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"RESULTS: {passed} passed, {failed} failed")
if warnings:
    print(f"\nWARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  [WARN] {w}")
if failed == 0 and not warnings:
    print("All checks PASSED! [OK]")
print(f"{'='*60}")
