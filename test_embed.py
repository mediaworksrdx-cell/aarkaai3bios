import time
start = time.perf_counter()
print("Importing sentence_transformers...")
from sentence_transformers import SentenceTransformer
print(f"Imported in {time.perf_counter() - start:.2f}s")

start = time.perf_counter()
print("Loading model paraphrase-multilingual-MiniLM-L12-v2...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print(f"Loaded model in {time.perf_counter() - start:.2f}s")

start = time.perf_counter()
print("Encoding test query...")
vec = model.encode("Hello world")
print(f"Encoded in {time.perf_counter() - start:.2f}s, shape: {vec.shape}")
