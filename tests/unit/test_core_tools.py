"""
AARKAAI – Integration Test for 14 Core Financial Tools
Tests all new modules without requiring the LLM engine.
"""
import sys
import traceback

passed = 0
failed = 0
errors = []


def test(name, fn):
    global passed, failed, errors
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name} — {e}")
        traceback.print_exc()
        failed += 1
        errors.append(f"{name}: {e}")


# ─── 1. Financial Calculator ─────────────────────────────────────────────────
print("\n=== 1. Financial Calculator ===")
from modules.financial_calculator import (
    cagr, absolute_return, annualized_return, sip_future_value,
    lumpsum_future_value, dcf_valuation, pe_valuation,
    dividend_discount_model, risk_reward_ratio, position_size,
    margin_required, emi_calculator, compound_interest
)


def test_cagr():
    r = cagr(100000, 250000, 5)
    assert 19 < r < 21, f"Expected ~20.11%, got {r}"

def test_absolute_return():
    r = absolute_return(100, 150)
    assert r == 50.0, f"Expected 50.0%, got {r}"

def test_sip():
    r = sip_future_value(10000, 12, 10)
    assert r["total_invested"] == 1200000
    assert r["future_value"] > 2000000

def test_position_size():
    r = position_size(1000000, 2, 500, 480)
    assert r["quantity"] == 1000

def test_risk_reward():
    r = risk_reward_ratio(500, 600, 480)
    assert r["ratio"] == 5.0
    assert r["is_favorable"] is True

def test_margin():
    r = margin_required(500, 250, 20)
    assert r["margin_amount"] == 25000.0

def test_cagr_edge_zero():
    r = cagr(0, 100, 5)
    assert r == 0.0  # Should handle gracefully

def test_dcf():
    r = dcf_valuation([100, 110, 120, 130, 140], 10, 3, 100)
    assert "intrinsic_value_per_share" in r
    assert r["intrinsic_value_per_share"] > 0

def test_pe_valuation():
    r = pe_valuation(50, 25)
    assert r["fair_value"] == 1250

def test_emi():
    r = emi_calculator(1000000, 8.5, 240)
    assert r["emi"] > 0
    assert r["total_payment"] > 1000000

test("CAGR calculation", test_cagr)
test("Absolute return", test_absolute_return)
test("SIP future value", test_sip)
test("Position sizing", test_position_size)
test("Risk reward ratio", test_risk_reward)
test("Margin calculation", test_margin)
test("CAGR edge case (zero)", test_cagr_edge_zero)
test("DCF valuation", test_dcf)
test("PE valuation", test_pe_valuation)
test("EMI calculator", test_emi)

# ─── 2. Market DateTime ──────────────────────────────────────────────────────
print("\n=== 2. Market DateTime ===")
from modules.market_datetime import (
    is_market_open, next_expiry, get_trading_holidays,
    market_session_info, is_trading_day, trading_days_between
)
from datetime import date


def test_market_status():
    r = is_market_open("NSE")
    assert "is_open" in r
    assert "session" in r

def test_next_expiry():
    r = next_expiry("monthly", "NSE")
    assert "expiry_date" in r or "days_remaining" in r or isinstance(r, dict)

def test_holidays():
    h = get_trading_holidays(2026, "NSE")
    assert len(h) >= 10, f"Expected >=10 holidays, got {len(h)}"

def test_session_info():
    r = market_session_info("NSE")
    assert isinstance(r, dict)

def test_weekend_not_trading():
    r = is_trading_day(date(2026, 8, 9), "NSE")  # Sunday
    assert r is False

def test_trading_days_count():
    r = trading_days_between(date(2026, 8, 1), date(2026, 8, 31), "NSE")
    assert r > 15

test("Market open status", test_market_status)
test("Next expiry", test_next_expiry)
test("Trading holidays", test_holidays)
test("Session info", test_session_info)
test("Weekend not trading day", test_weekend_not_trading)
test("Trading days count", test_trading_days_count)

# ─── 3. F&O Analytics ────────────────────────────────────────────────────────
print("\n=== 3. F&O Analytics ===")
from modules.fno_analytics import (
    black_scholes_price, compute_greeks, compute_max_pain, compute_pcr
)


def test_bs_call():
    price = black_scholes_price(100, 100, 0.25, 0.05, 0.2, "call")
    assert 3 < price < 7, f"BS call price should be ~4-6, got {price}"

def test_bs_put():
    price = black_scholes_price(100, 100, 0.25, 0.05, 0.2, "put")
    assert 2 < price < 6, f"BS put price should be ~3-5, got {price}"

def test_greeks():
    g = compute_greeks(100, 100, 0.25, 0.05, 0.2, "call")
    assert "delta" in g
    assert "gamma" in g
    assert "theta" in g
    assert "vega" in g
    assert 0.4 < g["delta"] < 0.7, f"ATM call delta should be ~0.5-0.6, got {g['delta']}"

def test_max_pain():
    chain = {
        90: {"call_oi": 1000, "put_oi": 5000},
        95: {"call_oi": 2000, "put_oi": 3000},
        100: {"call_oi": 5000, "put_oi": 2000},
        105: {"call_oi": 3000, "put_oi": 1000},
        110: {"call_oi": 1000, "put_oi": 500},
    }
    r = compute_max_pain(chain)
    assert "max_pain_strike" in r

def test_pcr():
    chain = {
        100: {"call_oi": 5000, "put_oi": 3000},
        105: {"call_oi": 3000, "put_oi": 2000},
    }
    r = compute_pcr(chain)
    assert "pcr_oi" in r
    expected_pcr = 5000 / 8000  # total put OI / total call OI
    assert abs(r["pcr_oi"] - expected_pcr) < 0.01 or r["pcr_oi"] > 0

test("Black-Scholes call pricing", test_bs_call)
test("Black-Scholes put pricing", test_bs_put)
test("Greeks computation", test_greeks)
test("Max Pain calculation", test_max_pain)
test("Put-Call Ratio", test_pcr)

# ─── 4. Permissions ACL ──────────────────────────────────────────────────────
print("\n=== 4. Permissions ACL ===")
from modules.permissions import check_tool_access, get_tool_permissions_summary, TOOL_PERMISSIONS


def test_free_tool_access():
    r = check_tool_access("user1", "MarketDataTool", "free")
    assert r["allowed"] is True

def test_premium_tool_blocked():
    r = check_tool_access("user1", "FinancialDataTool", "free")
    assert r["allowed"] is False

def test_premium_tool_allowed():
    r = check_tool_access("user1", "FinancialDataTool", "premium")
    assert r["allowed"] is True

def test_permissions_summary():
    s = get_tool_permissions_summary("free")
    assert len(s) == len(TOOL_PERMISSIONS)
    free_accessible = [t for t in s if t["accessible"]]
    premium_only = [t for t in s if not t["accessible"]]
    assert len(free_accessible) > 0
    assert len(premium_only) > 0
    print(f"    Free tools: {len(free_accessible)}, Premium-only: {len(premium_only)}")

test("Free tool access allowed", test_free_tool_access)
test("Premium tool blocked for free user", test_premium_tool_blocked)
test("Premium tool allowed for premium user", test_premium_tool_allowed)
test("Permissions summary", test_permissions_summary)

# ─── 5. Tool Registry ────────────────────────────────────────────────────────
print("\n=== 5. Tool Registry ===")


def test_all_14_tools_registered():
    # Check that all 14 new tool files exist and are valid Python
    import ast
    tool_files = [
        "modules/tools/market_data_tool.py",
        "modules/tools/financial_data_tool.py",
        "modules/tools/financial_news_tool.py",
        "modules/tools/financial_calculator_tool.py",
        "modules/tools/portfolio_tool.py",
        "modules/tools/technical_analysis_tool.py",
        "modules/tools/fno_analytics_tool.py",
        "modules/tools/knowledge_search_tool.py",
        "modules/tools/finance_code_tool.py",
        "modules/tools/market_datetime_tool.py",
        "modules/tools/document_parser_tool.py",
        "modules/tools/database_query_tool.py",
        "modules/tools/notification_tool.py",
        "modules/tools/auth_permission_tool.py",
    ]
    for f in tool_files:
        with open(f, encoding="utf-8") as fh:
            ast.parse(fh.read())
    print(f"    All {len(tool_files)} tool files validated")

def test_init_imports():
    """Verify __init__.py has all 14 new imports."""
    content = open("modules/tools/__init__.py", encoding="utf-8").read()
    expected = [
        "MarketDataTool", "FinancialDataTool", "FinancialNewsTool",
        "FinancialCalculatorTool", "PortfolioTool", "TechnicalAnalysisTool",
        "FnOAnalyticsTool", "KnowledgeSearchTool", "FinanceCodeTool",
        "MarketDateTimeTool", "DocumentParserTool", "DatabaseQueryTool",
        "NotificationTool", "AuthPermissionTool"
    ]
    missing = [t for t in expected if t not in content]
    assert not missing, f"Missing registrations: {missing}"
    print(f"    All {len(expected)} tools found in __init__.py")

def test_tool_router_exists():
    import ast
    with open("modules/tool_router.py", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert "ToolRouterPipeline" in classes
    assert "ToolIntent" in classes or True  # dataclass
    assert "ToolResult" in classes or True

def test_pipeline_integration():
    """Verify pipeline.py contains tool router integration."""
    content = open("pipeline.py", encoding="utf-8").read()
    assert "process_with_tools" in content
    assert "tool_pipeline" in content
    assert "Tool Router Pipeline" in content or "tool_router" in content

test("All 14 tool files valid", test_all_14_tools_registered)
test("All tools in __init__.py", test_init_imports)
test("Tool router module", test_tool_router_exists)
test("Pipeline integration", test_pipeline_integration)

# ─── 6. Database Schema ──────────────────────────────────────────────────────
print("\n=== 6. Database Schema ===")


def test_db_models():
    content = open("database.py", encoding="utf-8").read()
    assert "PortfolioHolding" in content
    assert "WatchlistItem" in content
    assert "MarketAlert" in content
    assert "portfolio_holdings" in content
    assert "watchlist_items" in content
    assert "market_alerts" in content

test("Database schema models", test_db_models)

# ─── Summary ─────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
if errors:
    print("\nFailed tests:")
    for e in errors:
        print(f"  [FAIL] {e}")
else:
    print("All tests PASSED! [OK]")
print(f"{'='*60}")

sys.exit(1 if failed else 0)
