import json
from typing import List, Dict, Any, Optional
from modules.subagents.base import CognitiveSubagent, SubagentResult

class ReasonerAgent(CognitiveSubagent):
    name: str = 'ReasonerAgent'
    description: str = 'Chain-of-thought decomposition for complex multi-step queries.'
    system_prompt: str = """You are a highly analytical Reasoner Agent. Your primary function is to break down complex, multi-step queries into manageable sub-questions, solve them systematically, and synthesize a coherent, logically sound final answer.

When presented with a query, you must rigorously follow this process:
1. Identify the core question: State clearly what the user is ultimately asking for.
2. Break into numbered sub-questions: Deconstruct the core question into sequential or logical sub-questions.
3. Solve each sub-question step-by-step: Provide a detailed, logical answer for each sub-question. Show your work and assumptions.
4. Check for logical consistency: Review your intermediate answers to ensure they do not contradict each other and that they logically lead to the final answer.
5. Synthesize final answer: Combine the insights from the sub-questions into a concise, accurate, and direct response to the original query.

Your output should clearly delineate these stages. Focus purely on logical reasoning.
"""
    allowed_tools: List[str] = []
    max_tokens: int = 2048
    temperature: float = 0.0

    def _execute(self, query: str, context: dict) -> str:
        prompt = f"Query: {query}\n"
        if context:
            prompt += f"\nPrior Context: {json.dumps(context, indent=2)}\n"
        prompt += "\nPlease provide your reasoning trace and final answer following the requested steps."
        
        response = self._invoke_model(self.system_prompt, prompt)
        
        context['_reasoning_trace'] = response
        
        return response

    def _estimate_confidence(self, output: str, context: dict) -> float:
        # Check if the output contains the required reasoning steps
        steps = ["1.", "2.", "3.", "4.", "5."]
        matches = sum(1 for step in steps if step in output)
        
        if matches == 5:
            return 0.95
        elif matches >= 3:
            return 0.75
        else:
            return 0.5
