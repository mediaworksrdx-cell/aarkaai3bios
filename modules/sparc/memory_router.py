"""
Dual-Tier Hybrid Memory Router for Aarka Backend.
Fuses symbolic Knowledge Graph observations with associative RuVector embeddings via Reciprocal Rank Fusion.
"""

import json
import os
from typing import Any, Dict, List, Optional
from modules.sparc.ruvector import RuVectorEngine, SearchResult


class HybridMemoryRouter:
    """
    Coordinates symbolic queries against MCP knowledge storage and associative queries
    against RuVector, merging results via Reciprocal Rank Fusion (k=60).
    """

    def __init__(self, memory_file_path: Optional[str] = None, dimension: int = 384) -> None:
        self.dimension = dimension
        self.vector_engine = RuVectorEngine(dimension=dimension)

        if memory_file_path:
            self.memory_file = os.path.abspath(memory_file_path)
        else:
            home_dir = os.path.expanduser("~")
            self.memory_file = os.path.join(home_dir, ".gemini", "memory", "memory.jsonl")

        self.symbolic_entities: Dict[str, Dict[str, Any]] = {}
        self.load_symbolic_memory()

    def load_symbolic_memory(self) -> None:
        """Reads symbolic entities and observations from persistent JSONL file."""
        if not os.path.exists(self.memory_file):
            return

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") == "entity":
                            name = record.get("name", "")
                            self.symbolic_entities[name] = record
                            # Index into RuVector for associative recall
                            text_corpus = f"{name} {record.get('entityType', '')} {' '.join(record.get('observations', []))}"
                            vec = self.vector_engine.embed_text_deterministic(text_corpus)
                            self.vector_engine.insert(
                                record_id=f"sym:{name}",
                                vector=vec,
                                metadata={
                                    "source": "mcp_graph",
                                    "name": name,
                                    "entityType": record.get("entityType", "Entity"),
                                    "observations": record.get("observations", [])
                                }
                            )
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    def add_memory_item(self, item_id: str, text: str, entity_type: str = "General", metadata: Optional[Dict[str, Any]] = None) -> None:
        """Adds an item into the vector engine and records it."""
        vec = self.vector_engine.embed_text_deterministic(text)
        meta = metadata or {}
        meta["entityType"] = entity_type
        meta["text"] = text
        self.vector_engine.insert(record_id=item_id, vector=vec, metadata=meta)

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Dispatches parallel semantic and symbolic queries and fuses using Reciprocal Rank Fusion.
        """
        k_rrf = 60
        q_vec = self.vector_engine.embed_text_deterministic(query_text)
        vector_hits = self.vector_engine.search(q_vec, top_k=top_k * 2)

        # Keyword match against symbolic store
        query_words = set(query_text.lower().split())
        symbolic_hits: List[tuple] = []
        for name, ent in self.symbolic_entities.items():
            content = (name + " " + " ".join(ent.get("observations", []))).lower()
            matches = sum(1 for w in query_words if w in content)
            if matches > 0:
                symbolic_hits.append((matches, name, ent))

        symbolic_hits.sort(key=lambda x: x[0], reverse=True)

        # RRF Fusion dictionary
        scores: Dict[str, float] = {}
        items: Dict[str, Dict[str, Any]] = {}

        # 1. Rank vector hits
        for rank, hit in enumerate(vector_hits):
            doc_id = hit.id
            weight = 1.0
            entity_type = hit.metadata.get("entityType", "")
            if entity_type in ("Architecture", "Convention", "SecurityRule"):
                weight = 1.5  # Hard architectural constraint multiplier

            rrf = weight / (k_rrf + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf
            items[doc_id] = {
                "id": doc_id,
                "score": hit.score,
                "source": hit.metadata.get("source", "ruvector"),
                "metadata": hit.metadata
            }

        # 2. Rank symbolic hits
        for rank, (_, name, ent) in enumerate(symbolic_hits[:top_k * 2]):
            doc_id = f"sym:{name}"
            weight = 1.5 if ent.get("entityType") in ("Architecture", "Convention", "SecurityRule") else 1.0
            rrf = weight / (k_rrf + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf
            if doc_id not in items:
                items[doc_id] = {
                    "id": doc_id,
                    "score": 1.0,
                    "source": "mcp_graph",
                    "metadata": ent
                }

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results: List[Dict[str, Any]] = []
        for doc_id in sorted_ids[:top_k]:
            res = items[doc_id]
            res["rrf_score"] = scores[doc_id]
            results.append(res)

        return results
