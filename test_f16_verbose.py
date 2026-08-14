import sys
sys.path.insert(0, "/home/ubuntu/aarkaai3b")
import logging
logging.basicConfig(level=logging.INFO)
from llama_cpp import Llama

try:
    print("Testing Llama with n_ctx=8192...")
    m = Llama(
        model_path="/home/ubuntu/aarkaai3b/aarkaa-7b-f16.gguf",
        n_ctx=8192,
        n_gpu_layers=99,
        verbose=True
    )
    print("F16 SUCCESS:", m)
except Exception as e:
    print("F16 ERROR:", e)
