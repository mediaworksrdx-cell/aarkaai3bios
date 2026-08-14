import json
import re
from typing import List, Dict, Any, Optional
from modules.subagents.base import CognitiveSubagent, SubagentResult

class PlannerAgent(CognitiveSubagent):
    name: str = 'PlannerAgent'
    description: str = 'Task decomposition for compound/multi-part queries.'
    system_prompt: str = """You are a precise Planner Agent. Your role is to decompose complex user queries into a sequence of actionable subtasks for other specialized agents to execute.

When analyzing a query, follow these steps:
1. Detect if the query has multiple distinct parts or requires multiple steps to fulfill.
2. Extract each subtask as a discrete action.
3. Identify dependencies between subtasks (e.g., Task 2 requires output from Task 1).
4. Assign an appropriate agent type to each task. Valid agent types are typically 'analyst', 'researcher', or 'coder', but you can specify others if needed based on the task context.

You MUST output your final execution plan strictly as a JSON object with the following schema:
{
  "subtasks": [
    {
      "id": 1,
      "task": "Description of the first task",
      "agent": "researcher",
      "depends_on": []
    },
    {
      "id": 2,
      "task": "Description of the second task",
      "agent": "coder",
      "depends_on": [1]
    }
  ]
}

If the query is a single, simple task, output a plan with just one subtask. Ensure the JSON is well-formed and valid. Do not wrap the JSON in markdown code blocks or add additional conversational text outside the JSON.
"""
    allowed_tools: List[str] = []
    max_tokens: int = 1024
    temperature: float = 0.1

    def _execute(self, query: str, context: dict) -> str:
        prompt = f"Analyze and decompose the following query:\n\n{query}\n\nOutput only the JSON execution plan."
        
        response = self._invoke_model(self.system_prompt, prompt)
        
        plan_json_str = response
        
        # Try to parse the JSON
        try:
            # Handle potential markdown wrappers if the model ignores the instruction
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                plan_json_str = match.group(1)
            
            plan_data = json.loads(plan_json_str)
        except json.JSONDecodeError:
            # Fallback for single task if parsing fails completely
            plan_data = {
                "subtasks": [
                    {
                        "id": 1,
                        "task": query,
                        "agent": "general",
                        "depends_on": []
                    }
                ]
            }
        
        if '_metadata' not in context:
            context['_metadata'] = {}
        context['_metadata']['plan'] = plan_data
        
        return json.dumps(plan_data, indent=2)

    def _estimate_confidence(self, output: str, context: dict) -> float:
        try:
            json.loads(output)
            return 0.9  # Valid JSON plan
        except json.JSONDecodeError:
            return 0.1  # Failed to produce valid JSON
