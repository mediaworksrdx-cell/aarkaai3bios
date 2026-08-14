#!/bin/bash
cd /workspace/aarkaai3b
python3.13 - <<'EOF'
import sys
sys.path.insert(0, '/workspace/aarkaai3b')
from modules import semantic_filter

queries = [
    "Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method.",
    "implement a binary search tree in python",
    "write a quicksort algorithm",
]

for q in queries:
    r = semantic_filter.classify(q)
    print(f"Query: {q[:60]}...")
    print(f"  domain={r['domain']}, confidence={r['confidence']:.3f}, intent={r['intent']}")
    print()
EOF
