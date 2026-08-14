import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import pipeline
print("Reasoning checks:", [x for x in dir(pipeline) if "reasoning" in x.lower()])
print("is_greeting:", pipeline._sanitize_query("hello"))
