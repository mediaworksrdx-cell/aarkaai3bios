from modules.web_search import search_google_cse
res = search_google_cse("latest AI news today", max_results=3)
print(f"Found {len(res)} results from Google CSE:")
for r in res:
    print("-", r['title'], "-->", r['url'])
