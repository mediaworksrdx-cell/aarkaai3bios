"""Complete remaining audit sections that were missed."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  PASS: {name}")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {name} -> {type(e).__name__}: {e}")

print("=== 6. Financial Calculator Edge Cases ===")
from modules.financial_calculator import cagr, sip_future_value, position_size, emi_calculator

test("cagr(0,0,0)", lambda: cagr(0, 0, 0))
test("cagr(-100,-200,5)", lambda: cagr(-100, -200, 5))
test("cagr(1e100,1e200,50)", lambda: cagr(1e100, 1e200, 50))
test("cagr(100,200,0)", lambda: cagr(100, 200, 0))
test("sip(0,0,0)", lambda: sip_future_value(0, 0, 0))
test("sip(-100,-5,-1)", lambda: sip_future_value(-100, -5, -1))
test("sip(1e50,10,50)", lambda: sip_future_value(1e50, 10, 50))
test("position_size(0,0,0)", lambda: position_size(0, 0, 0))
test("emi(0,0,0)", lambda: emi_calculator(0, 0, 0))

print("\n=== 7. SubagentResult Edge Cases ===")
from modules.subagents.base import SubagentResult

test("SubagentResult(empty)", lambda: SubagentResult(agent_name="", output=""))
r1 = SubagentResult(agent_name="t", output="hi")
test("valid result is_valid=True", lambda: None if r1.is_valid else (_ for _ in ()).throw(AssertionError("expected True")))
r2 = SubagentResult(agent_name="t", output="hi", error="e")
test("error result is_valid=False", lambda: None if not r2.is_valid else (_ for _ in ()).throw(AssertionError("expected False")))
r3 = SubagentResult(agent_name="t", output="", confidence=-1.0)
test("negative confidence no crash", lambda: r3)

print("\n=== 8. Config Security Checks ===")
import config
warnings = []

if hasattr(config, 'DEBUG') and getattr(config, 'DEBUG', False):
    warnings.append("CRITICAL: DEBUG=True in config")
    print("  WARN: DEBUG=True")
else:
    print("  PASS: DEBUG is not True")

if hasattr(config, 'CORS_ORIGINS'):
    origins = getattr(config, 'CORS_ORIGINS', [])
    if "*" in str(origins):
        warnings.append("HIGH: CORS allows wildcard origins")
        print("  WARN: CORS has wildcard")
    else:
        print(f"  PASS: CORS origins configured ({len(origins)} entries)")

if hasattr(config, 'MAX_QUERY_LENGTH'):
    mql = config.MAX_QUERY_LENGTH
    print(f"  PASS: MAX_QUERY_LENGTH = {mql}")
else:
    print("  WARN: No MAX_QUERY_LENGTH set")

# Check for print statements in production modules
print("\n=== 9. Print Statement Check ===")
import glob
prod_prints = []
for f in glob.glob("modules/**/*.py", recursive=True):
    if "test" in f or "__pycache__" in f:
        continue
    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
        for i, line in enumerate(fh, 1):
            stripped = line.strip()
            if stripped.startswith("print(") and not stripped.startswith("#"):
                prod_prints.append(f"  {f}:{i}: {stripped[:80]}")
if prod_prints:
    print(f"  WARN: {len(prod_prints)} print() calls in production modules")
    for p in prod_prints[:10]:
        print(p)
else:
    print("  PASS: No print() in production modules")

print(f"\n{'='*60}")
print(f"RESULTS: {passed} passed, {failed} failed")
if warnings:
    for w in warnings:
        print(f"  WARNING: {w}")
print(f"{'='*60}")
