import sys
import os
sys.path.append(os.getcwd())

from modules import aarkaa_engine
aarkaa_engine.init()

from pipeline import process_query

queries = [
    "You have 8 balls. One is heavier. Find it in 2 weighings.",
    "A clock shows 3:15. What is the angle between the hour hand and minute hand?",
    "In a race, you overtake the second person. What position are you in?"
]

for query in queries:
    print(f"\n========================================\nTesting query: {query}\n========================================\n")
    try:
        res = process_query(query)
        print("AI Response:\n")
        print(res.response)
    except Exception as e:
        print("Error:", e)


