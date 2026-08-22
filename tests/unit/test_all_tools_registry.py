"""
AARKAAI – Complete Tool Registry Validation
Validates ALL 64 registered tools: metadata, schema, and execute method.
"""
import sys

def safe_print(s):
    print(s.encode('ascii', errors='replace').decode('ascii'))

def main():
    from modules.tools import registry

    total = len(registry.tools)
    print(f"Total tools registered: {total}")
    print()

    VALID_RISKS = {"SAFE", "LOW", "HIGH", "CRITICAL"}
    passed = 0
    failed = 0
    failures = []

    header = f"{'#':<4} {'Tool Name':<30} {'Risk':<10} {'Conf':<6} {'Lat':<6} {'Cost':<6} {'Exec?':<6} {'Status'}"
    print(header)
    print("-" * len(header))

    for idx, (name, tool) in enumerate(sorted(registry.tools.items()), 1):
        errors = []

        # 1. name
        if not tool.name or not isinstance(tool.name, str):
            errors.append("missing name")

        # 2. description
        if not tool.description or not isinstance(tool.description, str):
            errors.append("missing description")

        # 3. execute is callable method
        if not hasattr(tool, 'execute') or not callable(tool.execute):
            errors.append("execute not callable")

        # 4. risk_level
        risk = getattr(tool, 'risk_level', None)
        if risk not in VALID_RISKS:
            errors.append(f"bad risk_level: {risk}")

        # 5. base_confidence
        conf = getattr(tool, 'base_confidence', None)
        if conf is None or not (0.0 <= conf <= 1.0):
            errors.append(f"bad confidence: {conf}")

        # 6. latency_weight
        lat = getattr(tool, 'latency_weight', None)
        if lat is None or lat <= 0:
            errors.append(f"bad latency: {lat}")

        # 7. cost_weight
        cost = getattr(tool, 'cost_weight', None)
        if cost is None or cost <= 0:
            errors.append(f"bad cost: {cost}")

        has_exec = "Y" if hasattr(tool, 'execute') and callable(tool.execute) else "N"

        if errors:
            failed += 1
            status = f"FAIL ({', '.join(errors)})"
            failures.append((name, errors))
        else:
            passed += 1
            status = "PASS"

        safe_print(f"{idx:<4} {name:<30} {str(risk):<10} {str(conf):<6} {str(lat):<6} {str(cost):<6} {has_exec:<6} {status}")

    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {total} tools")

    if failures:
        print(f"\nFailed tools:")
        for name, errs in failures:
            print(f"  {name}: {', '.join(errs)}")
    else:
        print("All tools PASSED validation! [OK]")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
