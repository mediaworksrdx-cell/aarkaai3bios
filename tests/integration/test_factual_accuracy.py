import sys
import logging
from pipeline import process_query

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

queries = [
    "How many engineering colleges are there in Tamilnadu?",
    "How many engineering colleges are there in Mangalore?"
]

for idx, query in enumerate(queries, 1):
    print(f"\n========================================")
    print(f"TEST {idx}: '{query}'")
    print(f"========================================")
    try:
        res = process_query(query)
        print(f"Sources: {res.sources}")
        print(f"Detected Language: {res.detected_language}")
        print(f"Response:\n{res.response}")
    except Exception as e:
        print(f"Error executing query: {e}")
