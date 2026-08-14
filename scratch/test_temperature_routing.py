import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from modules.aarkaa_engine import _get_temperature

test_cases = [
    # 1. General Chat (temp: 0.7)
    {
        "query": "hello there, how are you?",
        "intent": "general_query",
        "context": "",
        "expected": 0.7,
        "category": "General Chat"
    },
    {
        "query": "what is the capital of France?",
        "intent": "general_query",
        "context": "",
        "expected": 0.7,
        "category": "General Chat"
    },
    # 2. Coding (temp: 0.2)
    {
        "query": "write a python function to reverse a string",
        "intent": "coding_help",
        "context": "",
        "expected": 0.2,
        "category": "Coding"
    },
    {
        "query": "how do I fix a TypeError in JavaScript?",
        "intent": "coding_help",
        "context": "",
        "expected": 0.2,
        "category": "Coding"
    },
    # 3. Finance (temp: 0.15)
    {
        "query": "what is the price of BTC-USD?",
        "intent": "price_check",
        "context": "",
        "expected": 0.15,
        "category": "Finance"
    },
    {
        "query": "show me AAPL's latest dividend and revenue",
        "intent": "finance_general",
        "context": "",
        "expected": 0.15,
        "category": "Finance"
    },
    {
        "query": "analyze this stock",
        "intent": "general_query",
        "context": "[Finance Data]\nAAPL price is 180.0",
        "expected": 0.15,
        "category": "Finance"
    },
    # 4. Reasoning / Math (temp: 0.0)
    {
        "query": "if a clock shows 3:15, what is the angle between the hands?",
        "intent": "reasoning_puzzle",
        "context": "",
        "expected": 0.0,
        "category": "Reasoning/Math"
    },
    {
        "query": "you have 8 balls and one is heavier. find it in 2 weighings",
        "intent": "general_query",
        "context": "",
        "expected": 0.0,
        "category": "Reasoning/Math"
    },
    {
        "query": "calculate the value of 25 * 4 + 10",
        "intent": "general_query",
        "context": "",
        "expected": 0.0,
        "category": "Reasoning/Math"
    },
    # 5. Creative Writing (temp: 0.9)
    {
        "query": "write a short story about a brave astronaut",
        "intent": "general_query",
        "context": "",
        "expected": 0.9,
        "category": "Creative Writing"
    },
    {
        "query": "compose a beautiful poem about the autumn leaves",
        "intent": "general_query",
        "context": "",
        "expected": 0.9,
        "category": "Creative Writing"
    },
    {
        "query": "draft a professional email to request a meeting",
        "intent": "general_query",
        "context": "",
        "expected": 0.9,
        "category": "Creative Writing"
    }
]

failed = 0
for i, tc in enumerate(test_cases, 1):
    res = _get_temperature(tc["query"], tc["intent"], tc["context"])
    status = "PASS" if res == tc["expected"] else "FAIL"
    if status == "FAIL":
        failed += 1
    print(f"Test {i} [{tc['category']}]: '{tc['query']}' -> Got {res} (Expected {tc['expected']}) - {status}")

print(f"\nTotal test cases: {len(test_cases)}")
print(f"Passed: {len(test_cases) - failed}")
print(f"Failed: {failed}")

sys.exit(failed)
