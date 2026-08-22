import logging
from pipeline import process_query

logging.basicConfig(level=logging.INFO)

print("=== TEST 1: Finance Query (Should bypass tools) ===")
res1 = process_query("What is the price of Apple?")
print(f"Sources: {res1.sources}")
print(f"Response: {res1.response}\n")

print("=== TEST 2: Complex Coding Task (Should use tools) ===")
# Note: we use a simple task so it doesn't take forever, like reading a file.
res2 = process_query("Can you write a python script called hello.py that prints hello, and then read it to verify?")
print(f"Sources: {res2.sources}")
print(f"Response: {res2.response}\n")
