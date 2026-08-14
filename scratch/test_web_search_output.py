import logging
from modules import web_search

logging.basicConfig(level=logging.INFO)

query = "How many Engineering colleges are there in Tamilnadu?"
print("Running web search for:", query)
results = web_search.get_web_context(query)
print("\n=== Web Search Context ===")
print(results)
