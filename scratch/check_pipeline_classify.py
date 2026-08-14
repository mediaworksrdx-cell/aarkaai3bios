import sys
sys.path.insert(0, '/workspace/aarkaai3b')
from modules import semantic_filter
import pipeline
# pipeline imports semantic_filter locally or dynamically
# Let's call pipeline.process_query mock
import asyncio
class DummyUser:
    pass

async def test():
    # Call the classifier directly inside semantic_filter
    res = semantic_filter.classify("Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method.")
    print("Direct Classify result:", res)

asyncio.run(test())
