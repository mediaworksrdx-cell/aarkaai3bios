"""Print web search results for Earth rotation query."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import web_search

query = "1. If the Earth suddenly stopped rotating, what would happen in the first 24 hours?"
print("Running web search...")
context = web_search.get_web_context(query)
print("--- SEARCH CONTEXT START ---")
print(context)
print("--- SEARCH CONTEXT END ---")
