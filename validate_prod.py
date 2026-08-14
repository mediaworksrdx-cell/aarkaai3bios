"""Quick production validation for subagent framework."""
from modules.subagents import list_subagents, SUBAGENT_REGISTRY
from modules.subagents.orchestrator import get_orchestrator

print(f"Subagents loaded: {len(SUBAGENT_REGISTRY)}")
print(f"Names: {list_subagents()}")

o = get_orchestrator()
tests = [
    ("What is TCS price?", "simple"),
    ("Compare TCS Infosys Wipro fundamentals", "complex"),
    ("Explain PE ratio of TCS and whether overvalued", "moderate"),
]
for q, expected in tests:
    result = o.classify_complexity(q)
    status = "PASS" if result == expected else f"FAIL (got {result})"
    print(f"  {status}: '{q}' -> {result}")

print("Production validation complete.")
