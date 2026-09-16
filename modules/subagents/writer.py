from modules.subagents.base import CognitiveSubagent, SubagentResult

class WriterAgent(CognitiveSubagent):
    name = 'WriterAgent'
    description = 'Synthesizes research and data into comprehensive, authoritative, fully-written responses.'
    system_prompt = """You are Aarkaa AI, a principal research writer and financial editor built by Synthetix Analytics.
Your task is to take research content and analytical data and synthesize it into a comprehensive, authoritative, fully-written response answering the user's question in depth.
REQUIREMENTS:
- Write complete, thorough paragraphs with in-depth analysis.
- Use structured headings, numbered lists, bullet points, and comparison tables where appropriate.
- NEVER output only a title, summary stub, outline, or incomplete bullet list.
- Fully elaborate on all key concepts, differences, pros/cons, and mechanics.
- Maintain an objective, institutional-grade tone without marketing fluff or conversational filler."""
    allowed_tools = []
    max_tokens = 3800
    temperature = 0.4

    def _execute(self, query: str, context: dict) -> str:
        raw_content = context.get('raw_content', query)
        
        prompt = (
            f"User Question: {query}\n\n"
            f"Reference Research Content:\n{raw_content}\n\n"
            "Instructions:\n"
            "Synthesize the reference content above into a thorough, comprehensive, and complete response answering the user's question in full detail. "
            "Write out all sections, explanations, definitions, and comparisons completely. "
            "Do NOT output just a title, summary stub, or brief outline. Provide the full exhaustive response."
        )
        
        return self._invoke_model(self.system_prompt, prompt)

