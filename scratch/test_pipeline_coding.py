import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s",
    stream=sys.stdout
)

from database import init_db
init_db()

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
from modules import semantic_filter

print("Loading embedding model...")
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)
print("Initializing semantic filter...")
semantic_filter.init(embed_fn)

import modules.aarkaa_engine as engine
print("Initializing engine...")
engine.init()

from pipeline import process_query

query = """What is the output?

def test():
    x = [1, 2, 3]
    y = x
    y.append(4)
    print(x)

test()"""

print("Running pipeline...")
result = process_query(query, user_id="test_user", session_id="test_session")
print("Response:")
print(result.response)
print("Intent:", result.intent)
print("Sources:", result.sources)
