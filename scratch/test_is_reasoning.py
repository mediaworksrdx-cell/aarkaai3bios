import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import pipeline
q = "Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method."
is_r = pipeline._is_reasoning_query(q)
print("is_reasoning:", is_r)
