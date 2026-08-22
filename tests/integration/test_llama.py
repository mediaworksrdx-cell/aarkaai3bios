import sys
import os

try:
    print("Python executable:", sys.executable)
    print("Python version:", sys.version)
    print("Attempting to import llama_cpp...")
    from llama_cpp import Llama
    print("Successfully imported llama_cpp!")
    
    model_path = "aarkaa-3b-q8.gguf"
    if os.path.exists(model_path):
        print(f"GGUF model found at: {model_path}. Loading...")
        llm = Llama(
            model_path=model_path,
            n_ctx=512,
            n_threads=2,
            verbose=True
        )
        print("Model loaded successfully!")
    else:
        print(f"GGUF model not found at {model_path}")
except Exception as e:
    print("Error during llama_cpp import/loading:", e)
