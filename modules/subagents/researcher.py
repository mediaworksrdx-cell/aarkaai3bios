from modules.subagents.base import CognitiveSubagent, SubagentResult

class ResearcherAgent(CognitiveSubagent):
    name = 'ResearcherAgent'
    description = 'Deep information retrieval and multi-source synthesis.'
    system_prompt = """You are a highly capable Research Agent responsible for deep information retrieval and multi-source synthesis.

Your primary objective is to synthesize information from multiple sources into comprehensive, well-structured reports.

Guidelines:
1. Synthesize information from multiple sources clearly and logically.
2. Cite sources whenever possible for transparency.
3. Clearly distinguish between verified facts and inferences or assumptions.
4. Provide a structured output with clear headings and bullet points for readability."""
    allowed_tools = ['KnowledgeSearchTool', 'WebSearch', 'RAGTool']
    max_tokens = 2048
    temperature = 0.3

    def _execute(self, query: str, context: dict) -> str:
        # 1. Extract key search terms from query
        extraction_prompt = "Extract key search terms from the following query. Return only the search terms separated by spaces."
        search_terms = self._invoke_model(extraction_prompt, query, max_tokens=50, temperature=0.1)
        search_terms = search_terms.strip() if search_terms else query

        # 2. Try RAG knowledge base via self._invoke_tools
        rag_results = self._invoke_tools([('KnowledgeSearchTool', 'search', {'query': search_terms})])
        
        # 3. Try web search via self._invoke_tools
        web_results = self._invoke_tools([('WebSearch', 'search', {'query': search_terms})])

        # 4. Combine tool results into a research context string
        research_context = f"--- RAG Results ---\n{rag_results}\n\n--- Web Results ---\n{web_results}"

        # 5. Call self._invoke_model() with the research context to synthesize findings
        synthesis_prompt = self.system_prompt
        user_prompt = f"User Query: {query}\n\nResearch Context:\n{research_context}\n\nPlease synthesize the findings based on the provided context according to your system prompt instructions."
        synthesized_output = self._invoke_model(synthesis_prompt, user_prompt)

        # 6. Store sources in context['_tools_used']
        if '_tools_used' not in context:
            context['_tools_used'] = []
        context['_tools_used'].extend(['KnowledgeSearchTool', 'WebSearch'])

        # 7. Return synthesized research output
        return synthesized_output
