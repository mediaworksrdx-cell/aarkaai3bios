import sys
sys.path.insert(0, "/workspace/aarkaai3b")
import importlib.util
spec = importlib.util.find_spec("pipeline")
print("pipeline path:", spec.origin if spec else "None")
try:
    import pipeline
except Exception as e:
    import traceback
    traceback.print_exc()
