from modules.web_search import get_web_context

ctx = get_web_context("latest AI news today", max_results=3)
print("=== WEB SEARCH CONTEXT RESULT ===")
print(ctx)
