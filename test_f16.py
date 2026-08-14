import sys
sys.path.insert(0, "/home/ubuntu/aarkaai3b")
import logging
logging.basicConfig(level=logging.INFO)

from modules.aarkaa_engine import _get_model
m = _get_model(force_gpu=True)
print("F16 MODEL RESULT:", m)
