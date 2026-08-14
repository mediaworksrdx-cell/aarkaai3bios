from modules.subagents.base import CognitiveSubagent, SubagentResult
import json

class MemoryAgent(CognitiveSubagent):
    name = 'MemoryAgent'
    description = 'Manages conversation context, extracts key facts, and tracks user preferences.'
    system_prompt = """You are a Memory and Context Management Agent.
Your job is to analyze the user's query and the provided conversation history to extract key facts, state, and user preferences.
You must structure this information clearly so other agents can easily digest the current context.
Focus on identifying entities, constraints, and implicit/explicit user preferences."""
    allowed_tools = ['MemoryTool']
    max_tokens = 512
    temperature = 0.1

    def _execute(self, query: str, context: dict) -> str:
        convo_history = context.get('conversation_history', [])
        
        prompt = f"Analyze the following query and conversation history to extract key facts and user preferences.\n\n"
        prompt += f"Query: {query}\n"
        prompt += f"Conversation History: {json.dumps(convo_history, indent=2)}\n\n"
        prompt += "Please provide a structured summary including:\n1. Key Facts extracted\n2. User Preferences/Interests\n3. Conversation State Summary"
        
        return self._invoke_model(self.system_prompt, prompt)
