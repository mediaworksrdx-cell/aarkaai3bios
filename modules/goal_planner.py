"""
AARKAAI – Goal Planner & Schema Validation
Decomposes user queries into a strict Task DAG JSON schema.
Includes semantic caching using cosine similarity matching.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from modules import aarkaa_engine
from modules.tools import registry

logger = logging.getLogger(__name__)

# Strict plan model definitions for verification
class TaskNode(BaseModel):
    id: str = Field(description="Unique short task ID, e.g. 't1'")
    name: str = Field(description="Short human-readable task title")
    description: str = Field(description="Detailed operations mapping")
    tool_hint: Optional[str] = Field(None, description="Suggested tool name from Tool Registry")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must finish before this task starts")
    exit_criteria: str = Field(description="Deterministic verification statement for completion")
    retry_budget: int = Field(default=2, ge=0, le=4)
    approval_required: bool = Field(default=False)
    status: str = Field(default="pending")

class TaskDAG(BaseModel):
    goal: str
    tasks: List[TaskNode]

# Basic semantic planner cache for common analytics targets
PLANNER_CACHE: List[Dict[str, Any]] = [
    {
        "query_pattern": r"\b(research|analyze|report|trends)\b.*\b(nvidia|apple|tesla|microsoft|google|amazon|meta)\b",
        "dag_template": {
            "goal": "Conduct detailed analysis on {entity}",
            "tasks": [
                {
                    "id": "t1",
                    "name": "Retrieve financial stock metrics",
                    "description": "Fetch live market price data, PE ratio, dividend yields, and target levels for {entity}.",
                    "tool_hint": "WebSearch",
                    "dependencies": [],
                    "exit_criteria": "Retrieved latest quotes or metrics for the ticker",
                    "retry_budget": 2,
                    "approval_required": False
                },
                {
                    "id": "t2",
                    "name": "Search latest strategic news",
                    "description": "Collect recent news articles, executive announcements, and macro trends about {entity} for 2026.",
                    "tool_hint": "WebSearch",
                    "dependencies": [],
                    "exit_criteria": "Found at least 3 relevant recent news sources",
                    "retry_budget": 2,
                    "approval_required": False
                },
                {
                    "id": "t3",
                    "name": "Synthesize competitor positions",
                    "description": "Cross-reference recent market trends to map competitor dynamics.",
                    "tool_hint": "FileEditTool",
                    "dependencies": ["t1", "t2"],
                    "exit_criteria": "Competitor summary table formatted in markdown",
                    "retry_budget": 1,
                    "approval_required": False
                },
                {
                    "id": "t4",
                    "name": "Generate final intelligence summary",
                    "description": "Consolidate all findings into a structured report document with disclaimers.",
                    "tool_hint": "FileEditTool",
                    "dependencies": ["t3"],
                    "exit_criteria": "Created detailed summary report file in workspace",
                    "retry_budget": 1,
                    "approval_required": False
                }
            ]
        }
    }
]

PLANNER_PROMPT_TEMPLATE = """You are AARKAAI Goal Planner. Your task is to decompose a complex user request into a sequence of tasks structured as a Directed Acyclic Graph (DAG) using the strict JSON schema.

Available Tools in Registry:
{tools_metadata}

Strict JSON output format:
{{
  "goal": "<Overall goal summary>",
  "tasks": [
    {{
      "id": "t1",
      "name": "Task Name",
      "description": "Specific operations description",
      "tool_hint": "ToolName" or null,
      "dependencies": [],
      "exit_criteria": "Deterministic completion checks",
      "retry_budget": 2,
      "approval_required": false,
      "status": "pending"
    }}
  ]
}}

Request: {query}
Context: {context}

Return ONLY the valid JSON block. Do NOT include conversational text or headers. Ensure all task dependencies form a valid DAG with no circular loops.
"""

def needs_planning(query: str, filter_result: Dict[str, Any], chat_ctx: Optional[List[Dict[str, Any]]] = None) -> bool:
    """Heuristic decision whether query requires multi-step autonomous execution planning.

    Only returns True for queries that need actual tool execution (file writes, web
    searches, code compilation). Pure knowledge/design/explanation queries must go
    through the normal LLM response path to avoid execution_engine returning stale
    file content as the answer.
    """
    q_low = query.lower()

    # ── Hard exclusions: never plan pure knowledge/design queries ──────────
    # These are answered by the LLM directly — no tool execution needed.
    _knowledge_signals = [
        "design a", "design an", "explain", "describe", "what is", "how does",
        "provide architecture", "provide an architecture", "provide a", "give me",
        "what are", "how would you", "walk me through", "tell me about",
        "compare", "difference between", "pros and cons", "trade-off", "trade offs",
        "system design", "architecture for", "high level", "high-level",
        "for 1 million", "for 1m users", "for million users",
    ]
    if any(sig in q_low for sig in _knowledge_signals):
        return False

    # Short queries and general-domain non-puzzle queries skip planning
    if len(q_low) < 25 or (
        filter_result.get("domain") == "general"
        and "puzzle" not in filter_result.get("intent", "")
    ):
        return False

    # ── Allowlist: only trigger for true autonomous execution tasks ─────────
    # These require actual tool calls: file writes, web research pipelines,
    # code execution, report compilation, or targeted debugging sessions.
    _execution_keywords = [
        "generate report", "compile report", "audit the", "run the", "execute the",
        "debug the", "test the code", "run tests", "write a script to",
        "create a file", "build and run", "deploy", "benchmark the",
        "search and summarize", "research and analyze",
    ]
    if any(k in q_low for k in _execution_keywords):
        return True

    return False

def check_cache(query: str) -> Optional[Dict[str, Any]]:
    """Verify if query matches cached patterns to bypass LLM planning latency."""
    for item in PLANNER_CACHE:
        match = re.search(item["query_pattern"], query, re.IGNORECASE)
        if match:
            # Extract entity or use a default
            entity = match.group(2) if len(match.groups()) >= 2 else "target entity"
            template_str = json.dumps(item["dag_template"])
            # Format entity variables dynamically
            dag_json = json.loads(template_str.replace("{entity}", entity))
            logger.info("Planner cache hit for query '%s' with entity '%s'", query, entity)
            return dag_json
    return None

def create_plan(query: str, context: str = "", chat_ctx: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Generate and validate a Task DAG from model output or cache."""
    cached_dag = check_cache(query)
    if cached_dag:
        return cached_dag

    # Format tools metadata for prompt injection
    tools_info = ""
    for name, meta in registry.get_all_tool_metadata().items():
        tools_info += f"- {name}: {meta['description']} (Risk: {meta['risk_level']}, Latency: {meta['latency_weight']})\n"

    prompt = PLANNER_PROMPT_TEMPLATE.format(
        tools_metadata=tools_info,
        query=query,
        context=context
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info("Generating planning DAG. Attempt %d/%d", attempt + 1, max_retries)
            response = aarkaa_engine.generate_raw(prompt, max_new_tokens=1536)
            
            # Clean response text
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON bounds found in planner response.")
                
            clean_json = response[start_idx:end_idx + 1]
            dag_data = json.loads(clean_json)
            
            # Strict schema validation using Pydantic
            validated = TaskDAG(**dag_data)
            dag_dict = validated.model_dump()
            
            # Validate DAG acyclic property (no cycles)
            if not _is_acyclic(dag_dict["tasks"]):
                raise ValueError("Circular dependencies detected in generated task plan.")
                
            return dag_dict
        except Exception as exc:
            logger.warning("Planner generation failed on attempt %d: %s", attempt + 1, exc)
            
    # Absolute fallback DAG if model fails after retries
    return {
        "goal": f"Analyze: {query}",
        "tasks": [
            {
                "id": "t1",
                "name": "General Execution Task",
                "description": f"Process query: {query}",
                "tool_hint": "WebSearch" if "search" in query.lower() else "BashTool",
                "dependencies": [],
                "exit_criteria": "Task execution output received",
                "retry_budget": 2,
                "approval_required": False,
                "status": "pending"
            }
        ]
    }

def _is_acyclic(tasks: List[Dict[str, Any]]) -> bool:
    """Standard topological cycle check for DAG validation."""
    adj = {t["id"]: t.get("dependencies", []) for t in tasks}
    visited = {} # id -> state (0 = visiting, 1 = visited)
    
    def has_cycle(node):
        visited[node] = 0
        for neighbor in adj.get(node, []):
            if neighbor not in adj:
                continue # Ignore missing optional dependencies safely
            if visited.get(neighbor) == 0:
                return True
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
        visited[node] = 1
        return False

    for t in tasks:
        node_id = t["id"]
        if node_id not in visited:
            if has_cycle(node_id):
                return False
    return True
