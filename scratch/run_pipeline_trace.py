import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import pipeline
import logging

# Direct logging output to stdout so we see the trace logs
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
for logger_name in ["pipeline", "modules.semantic_filter", "modules.aarkaa_engine"]:
    l = logging.getLogger(logger_name)
    l.setLevel(logging.INFO)
    l.propagate = True

print("=== START PIPELINE PROCESS ===")
res = pipeline.process_query(
    query="Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method.",
    user_id="20e565fb-1ae8-4f6d-976a-9e0fb6350003",
    session_id="test-session-diag",
)
print("=== END PIPELINE PROCESS ===")
print("Response:", res.response)
