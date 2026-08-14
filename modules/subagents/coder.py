from modules.subagents.base import CognitiveSubagent, SubagentResult
import json

class CoderAgent(CognitiveSubagent):
    name: str = 'CoderAgent'
    description: str = 'Code generation with self-review.'
    system_prompt: str = """You are an expert software engineer and a highly skilled AI coding assistant.
Your goal is to generate clean, robust, and well-documented code based on user requirements.

When writing code, you must:
1. Understand requirements precisely before writing code.
2. Generate clean, documented code that adheres to standard best practices.
3. Self-review your code for bugs, edge cases, and security vulnerabilities.
4. Add comprehensive error handling.
5. Use type hints and docstrings for all functions, classes, and methods.

Produce code that is ready for production, well-structured, and highly maintainable."""
    allowed_tools: list = ['FinanceCodeTool', 'BashTool', 'FileReadTool']
    max_tokens: int = 2048
    temperature: float = 0.2

    def _execute(self, query: str, context: dict) -> str:
        prompt = f"Requirements: {query}\n\nPlease generate the required code."
        if context:
            prompt += f"\nContext: {json.dumps(context)}"
        
        output = self._invoke_model(self.system_prompt, prompt)
        
        if context.get('execute_code', False):
            # Assuming FinanceCodeTool can execute the code
            tool_results = self._invoke_tools([('FinanceCodeTool', 'execute', {'code': output})])
            return f"Code:\n{output}\n\nExecution Output:\n{tool_results}"
        
        return output

    def _estimate_confidence(self, output: str, context: dict) -> float:
        if '"""' in output or "'''" in output:
            return 0.85
        return 0.60
