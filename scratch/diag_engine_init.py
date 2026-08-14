import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import modules.aarkaa_engine as ae
import logging

logging.basicConfig(level=logging.INFO)
print("Running engine init diagnostics...")
try:
    ae.init()
except Exception as e:
    print("Init exception:", e)

print("_is_stub final status:", ae._is_stub)
print("Loaded cpu model:", ae._model_cpu)
