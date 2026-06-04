import sys
import os

# Set python path to find modules
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
from database import KnowledgeEntry, SessionLocal
from modules import rag

# 1. Clear existing system & auto-learn knowledge entries to prevent duplicates and clean pollution
print("Clearing existing system & auto-learn knowledge entries...")
session = SessionLocal()
try:
    deleted_system = session.query(KnowledgeEntry).filter(KnowledgeEntry.source == "system").delete()
    deleted_auto = session.query(KnowledgeEntry).filter(KnowledgeEntry.source == "auto_learn").delete()
    session.commit()
    print(f"Cleared {deleted_system} system and {deleted_auto} auto-learn knowledge entries.")
except Exception as e:
    session.rollback()
    print("Error clearing system knowledge:", e)
finally:
    session.close()

# 2. Load model and init RAG
print("Loading sentence-transformers to compute embedding...")
_st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)

print("Initializing RAG...")
rag.init(embed_fn)

# 3. Define seed knowledge entries
seeds = [
    {
        "topic": "Moses Ark riddle",
        "content": (
            "Moses did not take any animals on the Ark. In the biblical story (Book of Genesis), "
            "it was Noah who built the Ark and saved the animals from the Great Flood. "
            "Moses is a completely different biblical figure who lived centuries later."
        )
    },
    {
        "topic": "EBITDA vs Free Cash Flow divergence",
        "content": (
            "EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization) represents "
            "operating profitability, while Free Cash Flow (FCF) represents the actual cash generated "
            "by a company after capital expenditures (CapEx). FCF is calculated as Operating Cash Flow "
            "minus CapEx. EBITDA can rise while FCF falls due to: "
            "1. Increased Capital Expenditures (CapEx): Large CapEx spends directly reduce FCF but do "
            "not affect EBITDA because CapEx is capitalized and depreciated over time, and depreciation "
            "is excluded from EBITDA. "
            "2. Working Capital Needs: Increases in accounts receivable (uncollected revenues) or "
            "inventory consume cash and decrease FCF, even as revenue and EBITDA increase. "
            "3. Increased Cash Payments: Interest and taxes are cash expenses that reduce FCF, but they "
            "are not subtracted when calculating EBITDA. Note that interest and taxes are actual cash expenses, "
            "while depreciation and amortization are non-cash expenses."
        )
    }
]

print("Storing knowledge...")
for seed in seeds:
    rag.store_knowledge(topic=seed["topic"], content=seed["content"], source="system")
print("Knowledge stored successfully!")
