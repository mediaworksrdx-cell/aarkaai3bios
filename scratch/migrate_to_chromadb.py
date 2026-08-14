"""
AARKAAI – SQLite → ChromaDB Migration Script

Migrates all KnowledgeEntry rows from SQLite (with binary blob embeddings)
to the new ChromaDB persistent collection. Reuses existing embeddings
directly — no re-embedding needed.

Usage:
    python scratch/migrate_to_chromadb.py
"""
import struct
import sys
import os
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np


def _deserialize(blob: bytes) -> np.ndarray:
    """Deserialize a float32 binary blob back to numpy array."""
    n = len(blob) // 4  # float32 = 4 bytes
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


def migrate():
    from config import CHROMA_PERSIST_DIR, EMBEDDING_DIM
    from database import KnowledgeEntry, SessionLocal
    import chromadb

    print(f"ChromaDB target directory: {CHROMA_PERSIST_DIR}")
    print(f"Expected embedding dim: {EMBEDDING_DIM}")

    # ── 1. Read all entries from SQLite ──
    from database import init_db
    init_db()
    session = SessionLocal()
    try:
        entries = session.query(KnowledgeEntry).all()
        print(f"\nFound {len(entries)} knowledge entries in SQLite.")
    finally:
        session.close()

    if not entries:
        print("Nothing to migrate.")
        return

    # ── 2. Initialize ChromaDB ──
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name="aarkaai_knowledge",
        metadata={"hnsw:space": "cosine"},
    )

    existing_count = collection.count()
    if existing_count > 0:
        print(f"\n⚠ ChromaDB already has {existing_count} entries.")
        if not sys.stdin.isatty():
            print("  Non-interactive terminal detected. Auto-confirming purge and re-migration.")
            response = "y"
        else:
            response = input("  Purge existing and re-migrate? [y/N]: ").strip().lower()
        if response == "y":
            client.delete_collection("aarkaai_knowledge")
            collection = client.create_collection(
                name="aarkaai_knowledge",
                metadata={"hnsw:space": "cosine"},
            )
            print("  Purged existing collection.")
        else:
            print("  Skipping migration (existing data preserved).")
            return

    # ── 3. Migrate entries ──
    migrated = 0
    skipped_no_embedding = 0
    skipped_error = 0

    # ChromaDB supports batch add — collect in batches
    BATCH_SIZE = 100
    batch_ids = []
    batch_embeddings = []
    batch_documents = []
    batch_metadatas = []

    for entry in entries:
        if entry.embedding is None:
            skipped_no_embedding += 1
            continue

        try:
            vec = _deserialize(entry.embedding)
            if len(vec) != EMBEDDING_DIM:
                print(f"  ⚠ Entry {entry.id} has dim {len(vec)} (expected {EMBEDDING_DIM}), skipping")
                skipped_error += 1
                continue

            doc_id = str(uuid.uuid4())
            effective_user = entry.user_id if entry.user_id else "__global__"

            batch_ids.append(doc_id)
            batch_embeddings.append(vec.tolist())
            batch_documents.append(entry.content)
            batch_metadatas.append({
                "user_id": effective_user,
                "topic": entry.topic,
                "source": entry.source or "auto_learn",
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else "",
            })

            if len(batch_ids) >= BATCH_SIZE:
                collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                )
                migrated += len(batch_ids)
                print(f"  Migrated {migrated}/{len(entries)} entries...")
                batch_ids, batch_embeddings, batch_documents, batch_metadatas = [], [], [], []

        except Exception as exc:
            print(f"  ✗ Entry {entry.id} failed: {exc}")
            skipped_error += 1

    # Flush remaining batch
    if batch_ids:
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )
        migrated += len(batch_ids)

    # ── 4. Report ──
    print(f"\n{'='*50}")
    print(f"Migration complete!")
    print(f"  ✓ Migrated:            {migrated}")
    print(f"  ⚠ Skipped (no embed):  {skipped_no_embedding}")
    print(f"  ✗ Skipped (errors):    {skipped_error}")
    print(f"  Total in ChromaDB:     {collection.count()}")
    print(f"  ChromaDB path:         {CHROMA_PERSIST_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    migrate()
