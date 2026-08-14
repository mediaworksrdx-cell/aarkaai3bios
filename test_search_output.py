from modules import web_search

query = "A clock shows 3:15. What is the angle between the hour hand and minute hand?"
results = web_search.search_ddg(query)
print("WEB SEARCH RESULTS:")
for idx, res in enumerate(results):
    print(f"\nResult {idx+1}:")
    print("Title:", res.get("title"))
    print("Snippet:", res.get("snippet"))
