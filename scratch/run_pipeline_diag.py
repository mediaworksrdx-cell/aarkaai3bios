import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import pipeline

def test_full_pipeline():
    res = pipeline.process_query(
        query="Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method.",
        user_id="20e565fb-1ae8-4f6d-976a-9e0fb6350003",
        session_id="test-session-diag",
    )
    print("Pipeline Response type:", type(res))
    print("Pipeline response field:", res.response)

test_full_pipeline()
