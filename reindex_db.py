"""
AARKAAI – Database Reindex Script

Run this after switching to the multilingual embedding model
to re-embed all existing knowledge entries with the new model.

Usage:
    python reindex_db.py
"""
import struct
import sys
import logging

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from config import EMBEDDING_MODEL_NAME
from database import KnowledgeEntry, SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reindex")


def _serialize(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def main():
    logger.info("=" * 60)
    logger.info("  AARKAAI – Knowledge Base Reindex Tool")
    logger.info("  New embedding model: %s", EMBEDDING_MODEL_NAME)
    logger.info("=" * 60)

    # Load the new multilingual embedding model
    logger.info("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embed_fn = lambda text: model.encode(text, normalize_embeddings=True)

    session: Session = SessionLocal()

    try:
        entries = session.query(KnowledgeEntry).all()
        total = len(entries)

        if total == 0:
            logger.info("No knowledge entries found – nothing to reindex.")
            return

        logger.info("Found %d knowledge entries to reindex.", total)

        updated = 0
        failed = 0
        for i, entry in enumerate(entries, 1):
            try:
                # Re-embed using the content field
                text = entry.content or entry.topic or ""
                if not text.strip():
                    logger.warning("[%d/%d] Skipping empty entry id=%d", i, total, entry.id)
                    continue

                vec = embed_fn(text)
                entry.embedding = _serialize(vec)
                updated += 1

                if i % 50 == 0 or i == total:
                    session.commit()
                    logger.info("[%d/%d] Progress: %d updated", i, total, updated)

            except Exception as exc:
                failed += 1
                logger.error("[%d/%d] Failed entry id=%d: %s", i, total, entry.id, exc)

        # Final commit
        session.commit()

        logger.info("=" * 60)
        logger.info("  Reindex complete!")
        logger.info("  Total entries:   %d", total)
        logger.info("  Updated:         %d", updated)
        logger.info("  Failed:          %d", failed)
        logger.info("=" * 60)

    except Exception as exc:
        session.rollback()
        logger.error("Reindex failed: %s", exc)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
