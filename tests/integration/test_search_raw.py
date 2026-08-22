from modules.web_search import get_web_context

queries = [
    "How many engineering colleges are there in Tamilnadu?",
    "How many engineering colleges are there in Mangalore?"
]

for idx, q in enumerate(queries, 1):
    print(f"\n========================================")
    print(f"SEARCH {idx}: '{q}'")
    print(f"========================================")
    ctx = get_web_context(q)
    print(ctx)
