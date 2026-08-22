import sys
sys.path.insert(0, "/home/ubuntu/aarkaai3b")
from llama_cpp import Llama

print("Testing direct Llama instantiation...")
m = Llama(
    model_path="/home/ubuntu/aarkaai3b/aarkaa-7b-f16.gguf",
    n_ctx=16384,
    n_gpu_layers=99,
    verbose=True
)
print("SUCCESS! Model loaded:", m)
