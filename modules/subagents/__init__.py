from modules.subagents.base import CognitiveSubagent, SubagentResult
from modules.subagents.reasoner import ReasonerAgent
from modules.subagents.researcher import ResearcherAgent
from modules.subagents.analyst import AnalystAgent
from modules.subagents.coder import CoderAgent
from modules.subagents.critic import CriticAgent
from modules.subagents.writer import WriterAgent
from modules.subagents.planner import PlannerAgent
from modules.subagents.memory_agent import MemoryAgent

SUBAGENT_REGISTRY = {
    'reasoner': ReasonerAgent(),
    'researcher': ResearcherAgent(),
    'analyst': AnalystAgent(),
    'coder': CoderAgent(),
    'critic': CriticAgent(),
    'writer': WriterAgent(),
    'planner': PlannerAgent(),
    'memory': MemoryAgent(),
}

def get_subagent(name: str) -> CognitiveSubagent:
    return SUBAGENT_REGISTRY.get(name)

def list_subagents() -> list:
    return list(SUBAGENT_REGISTRY.keys())
