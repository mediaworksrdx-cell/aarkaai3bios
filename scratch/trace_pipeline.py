import sys
sys.path.insert(0, '/workspace/aarkaai3b')
from modules import semantic_filter
import pipeline
import re
q = "Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method."

res = semantic_filter.classify(q)
print("classify res:", res)

domain = res["domain"]
filter_confidence = res["confidence"]
intent = res["intent"]

_has_design_keywords = any(w in q.lower() for w in ["design a", "design an", "system design", "architecture", "explain:"])
if _has_design_keywords:
    domain = "technology"
    intent = "tech_info"
    filter_confidence = max(filter_confidence, 0.90)
elif filter_confidence < 0.45 and intent not in ["persuasion", "debate", "comparison", "roleplay"]:
    domain = "general"
    intent = "general_query"

print("Final mapped domain:", domain, "confidence:", filter_confidence, "intent:", intent)
