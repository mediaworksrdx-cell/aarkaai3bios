import sys
import os

# Ensure the parent directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
import modules.rag as rag

print("Loading embedding model:", EMBEDDING_MODEL_NAME)
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)

# Initialize RAG engine
rag.init(embed_fn)

query = "You have 5 billion log entries. Need to find the top 100 most frequent IP addresses. Only 2 GB RAM available. How would you solve it?"
print(f"\nQuerying RAG with: {query}")
context = rag.get_context(query)
print("\n--- RAG RETRIEVED CONTEXT ---")
print(context)
print("----------------------------")
