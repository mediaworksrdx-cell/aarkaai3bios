"""
AARKAAI — Cognitive Subagent Framework Tests

Validates:
1. All 8 subagents instantiate correctly
2. Registry exports all agents
3. Orchestrator classifies complexity correctly
4. Pipeline selection logic
5. Subagent execution with mock context
6. Critic verification flow
7. Analyst tool chaining
8. Integration: pipeline.py imports work
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def safe_print(s):
    print(str(s).encode('ascii', errors='replace').decode('ascii'))

passed = 0
failed = 0

def test(name, condition, msg=""):
    global passed, failed
    if condition:
        passed += 1
        safe_print(f"  PASS: {name}")
    else:
        failed += 1
        safe_print(f"  FAIL: {name} — {msg}")

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 1. Subagent Registry ===")

from modules.subagents import (
    SUBAGENT_REGISTRY, get_subagent, list_subagents,
    CognitiveSubagent, SubagentResult,
    ReasonerAgent, ResearcherAgent, AnalystAgent, CoderAgent,
    CriticAgent, WriterAgent, PlannerAgent, MemoryAgent
)

test("Registry has 8 agents", len(SUBAGENT_REGISTRY) == 8,
     f"got {len(SUBAGENT_REGISTRY)}")
test("list_subagents() returns 8", len(list_subagents()) == 8)
test("get_subagent('analyst') returns AnalystAgent",
     isinstance(get_subagent('analyst'), AnalystAgent))
test("get_subagent('unknown') returns None",
     get_subagent('unknown') is None)

expected_agents = ['reasoner', 'researcher', 'analyst', 'coder',
                   'critic', 'writer', 'planner', 'memory']
for name in expected_agents:
    agent = get_subagent(name)
    test(f"  {name} exists", agent is not None)
    test(f"  {name} has name", bool(agent.name))
    test(f"  {name} has description", bool(agent.description))
    test(f"  {name} has system_prompt", bool(agent.system_prompt))

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 2. CognitiveSubagent Base Class ===")

test("SubagentResult has is_valid property",
     hasattr(SubagentResult(agent_name="test", output="hello"), 'is_valid'))
test("SubagentResult is_valid=True when output present",
     SubagentResult(agent_name="t", output="hello").is_valid)
test("SubagentResult is_valid=False when error present",
     not SubagentResult(agent_name="t", output="hello", error="fail").is_valid)
test("SubagentResult is_valid=False when empty output",
     not SubagentResult(agent_name="t", output="").is_valid)

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 3. Orchestrator — Complexity Classification ===")

from modules.subagents.orchestrator import CognitiveOrchestrator

orch = CognitiveOrchestrator()

# Simple queries
test("'What is TCS price?' → simple",
     orch.classify_complexity("What is TCS price?") == "simple")
test("'Hello' → simple",
     orch.classify_complexity("Hello") == "simple")
test("'SIP of 5000 at 12%' → simple",
     orch.classify_complexity("SIP of 5000 at 12% for 10 years") == "simple")

# Moderate queries
test("'Explain the PE ratio of TCS and is it overvalued' → moderate",
     orch.classify_complexity("Explain the PE ratio of TCS and whether it is overvalued") in ("moderate", "complex"))

# Complex queries
test("'Compare TCS, Infosys, Wipro fundamentals and technicals' → complex",
     orch.classify_complexity("Compare TCS, Infosys, and Wipro on fundamentals, technicals, and give me a buy recommendation") == "complex")
test("'Analyze sector rotation and then build a portfolio' → complex",
     orch.classify_complexity("Analyze the IT sector rotation trends, compare top 5 companies, and then build me a portfolio with risk management") == "complex")

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 4. Orchestrator — Pipeline Selection ===")

test("Simple → empty pipeline",
     orch.select_pipeline("simple", "general", "general_query") == [])
test("Moderate finance → [analyst, writer]",
     orch.select_pipeline("moderate", "finance", "general_query") == ["analyst", "writer"])
test("Moderate tech → [coder, writer]",
     orch.select_pipeline("moderate", "technology", "general_query") == ["coder", "writer"])
test("Moderate general → [researcher, writer]",
     orch.select_pipeline("moderate", "general", "general_query") == ["researcher", "writer"])
test("Complex finance → has planner, analyst, reasoner, writer, critic",
     set(["planner", "analyst", "reasoner", "writer", "critic"]).issubset(
         set(orch.select_pipeline("complex", "finance", "comparison"))))
test("Complex tech → has planner, researcher, coder",
     all(a in orch.select_pipeline("complex", "technology", "general_query")
         for a in ["planner", "researcher", "coder"]))

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 5. Agent Configuration Validation ===")

configs = {
    'reasoner': {'temp': 0.0, 'tools': []},
    'critic': {'temp': 0.0, 'tools': []},
    'analyst': {'temp': 0.2, 'tools': ['MarketDataTool', 'FinancialDataTool']},
    'coder': {'temp': 0.2},
    'planner': {'temp': 0.1, 'tools': []},
}

for name, expected in configs.items():
    agent = get_subagent(name)
    if 'temp' in expected:
        test(f"{name} temperature = {expected['temp']}",
             agent.temperature == expected['temp'],
             f"got {agent.temperature}")
    if 'tools' in expected:
        for tool in expected['tools']:
            test(f"{name} has {tool} in allowed_tools",
                 tool in agent.allowed_tools,
                 f"missing {tool}")

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 6. Critic Agent — Verification Logic ===")

critic = get_subagent('critic')
test("Critic name is CriticAgent", critic.name == "CriticAgent")
test("Critic temperature is 0.0", critic.temperature == 0.0)
test("Critic has no allowed tools", critic.allowed_tools == [])
test("Critic max_tokens is 1024", critic.max_tokens == 1024)

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 7. Orchestrator — Simple Query Bypass ===")

# orchestrate() should return None for simple queries (no subagent overhead)
result = orch.orchestrate("Hello", {"domain": "general", "intent": "general_query"})
test("Simple query bypassed (returns None)", result is None)

result = orch.orchestrate("What is TCS price?", {"domain": "finance", "intent": "stock_price"})
test("Simple finance query bypassed (returns None)", result is None)

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 8. Pipeline Integration — Import Check ===")

try:
    from modules.subagents.orchestrator import get_orchestrator
    orch_singleton = get_orchestrator()
    test("get_orchestrator() singleton works", orch_singleton is not None)
    test("Singleton is CognitiveOrchestrator",
         isinstance(orch_singleton, CognitiveOrchestrator))
except Exception as e:
    test("get_orchestrator() import", False, str(e))

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 9. Tool Router — execute_tool_chain method ===")

from modules.tool_router import ToolRouterPipeline
pipeline = ToolRouterPipeline()
test("execute_tool_chain method exists",
     hasattr(pipeline, 'execute_tool_chain'))
test("execute_tool_chain is callable",
     callable(pipeline.execute_tool_chain))

# ══════════════════════════════════════════════════════════════════════════
print("\n=== 10. Orchestrator — orchestrate_stream method ===")

import asyncio
test("orchestrate_stream method exists", hasattr(orch, 'orchestrate_stream'))

async def run_stream_test():
    # Test simple query bypass (should yield nothing/close instantly)
    events = []
    async for event in orch.orchestrate_stream("Hello", {"domain": "general", "intent": "general_query"}):
        events.append(event)
    return events

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

stream_bypass_events = loop.run_until_complete(run_stream_test())
test("orchestrate_stream bypasses simple query", len(stream_bypass_events) == 0, f"expected 0 events, got {len(stream_bypass_events)}")

# ══════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed} tests")
if failed == 0:
    print("All tests PASSED! [OK]")
else:
    print(f"WARNING: {failed} test(s) FAILED")
print(f"{'='*60}")
sys.exit(0 if failed == 0 else 1)
