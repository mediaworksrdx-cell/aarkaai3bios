import re
from pipeline import _is_reasoning_query

query = "You have 5 billion log entries. Need to find the top 100 most frequent IP addresses. Only 2 GB RAM available. How would you solve it?"

is_reasoning = _is_reasoning_query(query)
print("Query:", query)
print("is_reasoning:", is_reasoning)
