from modules.subagents.base import CognitiveSubagent, SubagentResult

class WriterAgent(CognitiveSubagent):
    name = 'WriterAgent'
    description = 'Synthesizes information into well-formatted, professional natural language.'
    system_prompt = """You are an expert professional financial writer and editor.
Your task is to take raw content and synthesize it into a polished, well-structured, and highly readable format.
You must use appropriate headers, bullet points, and tables where applicable to present data clearly.
Your tone should be authoritative yet accessible.
When dealing with financial data or investment analysis, you must include appropriate disclaimers stating that the information is not financial advice.
Always be clear, concise, and prioritize readability and professional formatting."""
    allowed_tools = []
    max_tokens = 2048
    temperature = 0.4

    def _execute(self, query: str, context: dict) -> str:
        raw_content = context.get('raw_content', query)
        format_hint = context.get('format', 'auto')
        
        prompt = f"Please format and rewrite the following raw content into a professional presentation.\n\n"
        prompt += f"Requested Format: {format_hint}\n"
        prompt += f"Raw Content:\n{raw_content}\n"
        
        return self._invoke_model(self.system_prompt, prompt)
