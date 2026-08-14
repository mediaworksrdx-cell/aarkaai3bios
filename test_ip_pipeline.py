import sys
import os
import logging

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable INFO logs to see the pipeline processing steps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)

from pipeline import process_query
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
import modules.rag as rag
from modules import aarkaa_engine

print("Initializing RAG engine...")
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)
rag.init(embed_fn)

print("Initializing AARKAA-3B engine...")
aarkaa_engine.init()



query = "You have 5 billion log entries. Need to find the top 100 most frequent IP addresses. Only 2 GB RAM available. How would you solve it?"

print("\n=== STARTING PIPELINE TEST ===")
try:
    result = process_query(query)
    print("\n=== PIPELINE RESPONSE ===")
    print("Sources Used:", result.sources)
    print("Detected Language:", result.detected_language)
    print("Processing Time:", result.processing_time)
    print("\nResponse:")
    print(result.response)
    print("=========================")
except Exception as e:
    print("Pipeline execution failed:", e)
