"""
skill_registry.py

Backend implementation of the skill routing system.
Exposes get_skill() and list_skills() as callable tools
for your LLM via function/tool calling.

Requirements:
    pip install sentence-transformers faiss-cpu pyyaml

Usage:
    registry = SkillRegistry("./skills")
    registry.build_index()

    # At query time:
    relevant = registry.search("convert csv to excel", top_k=3)
    docs = [registry.get_skill(s["name"]) for s in relevant]
"""

import os
import json
import yaml
import numpy as np
from pathlib import Path
from typing import Optional


class SkillRegistry:
    def __init__(self, skills_dir: str):
        """
        skills_dir: path to folder containing skill subdirectories,
                    each with a SKILL.md file.

        Expected structure:
            skills/
            ├── pdf/SKILL.md
            ├── xlsx/SKILL.md
            └── sql-formatter/SKILL.md
        """
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, dict] = {}  # name -> {description, path}
        self._index = None
        self._embedder = None
        self._names: list[str] = []

        self._load_registry()

    def _load_registry(self):
        """Scan skills_dir and load all SKILL.md frontmatter."""
        for skill_path in self.skills_dir.rglob("SKILL.md"):
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse YAML frontmatter between --- markers
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        meta = yaml.safe_load(parts[1])
                        name = meta.get("name")
                        description = meta.get("description", "")
                        if name:
                            self.skills[name] = {
                                "name": name,
                                "description": description,
                                "path": str(skill_path),
                            }
                    except yaml.YAMLError:
                        pass

    def build_index(self):
        """
        Embed all skill descriptions and build a FAISS index.
        Call once at startup (or after adding new skills).
        """
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
        except ImportError:
            raise ImportError(
                "Run: pip install sentence-transformers faiss-cpu"
            )

        self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self._names = list(self.skills.keys())
        descriptions = [self.skills[n]["description"] for n in self._names]

        embeddings = self._embedder.encode(descriptions, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype="float32")

        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # inner product = cosine on normalized
        self._index.add(embeddings)

        print(f"[SkillRegistry] Indexed {len(self._names)} skills.")

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Find the top-k most relevant skills for a query.
        Returns list of {name, description, score}.
        """
        if self._index is None:
            raise RuntimeError("Call build_index() before searching.")

        query_vec = self._embedder.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype="float32")

        scores, indices = self._index.search(query_vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._names):
                name = self._names[idx]
                results.append({
                    "name": name,
                    "description": self.skills[name]["description"],
                    "score": float(score),
                })
        return results

    def get_skill(self, name: str) -> str:
        """
        Fetch the full SKILL.md content for a given skill name.
        This is the function your LLM tool call maps to.
        """
        if name not in self.skills:
            return f"Error: skill '{name}' not found. Call list_skills() to see available skills."

        path = self.skills[name]["path"]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def list_skills(self) -> list[dict]:
        """
        Return all skills with name + description.
        This is the function your LLM tool call maps to.
        """
        return [
            {"name": s["name"], "description": s["description"]}
            for s in self.skills.values()
        ]

    def save_index(self, path: str):
        """Persist the FAISS index and skill names to disk."""
        import faiss
        faiss.write_index(self._index, path + ".faiss")
        with open(path + ".names.json", "w") as f:
            json.dump(self._names, f)

    def load_index(self, path: str):
        """Load a previously saved FAISS index."""
        import faiss
        from sentence_transformers import SentenceTransformer
        self._index = faiss.read_index(path + ".faiss")
        with open(path + ".names.json") as f:
            self._names = json.load(f)
        self._embedder = SentenceTransformer("all-MiniLM-L6-v2")


# --- Tool call definitions for your LLM ---
# Register these with your model's function-calling interface.

TOOL_DEFINITIONS = [
    {
        "name": "list_skills",
        "description": "List all available skills with their names and descriptions. Call this to find the right skill name before calling get_skill.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_skill",
        "description": "Fetch the full documentation for a skill by name. Read it before attempting the task it covers.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The skill name from list_skills()",
                }
            },
            "required": ["name"],
        },
    },
]


# --- Example: wiring into an OpenAI-compatible API ---

def handle_tool_call(registry: SkillRegistry, tool_name: str, tool_args: dict) -> str:
    """Route a tool call from your LLM to the registry."""
    if tool_name == "list_skills":
        skills = registry.list_skills()
        return json.dumps(skills, indent=2)
    elif tool_name == "get_skill":
        name = tool_args.get("name", "")
        return registry.get_skill(name)
    else:
        return f"Unknown tool: {tool_name}"


# --- Quick test ---
if __name__ == "__main__":
    import sys

    skills_dir = sys.argv[1] if len(sys.argv) > 1 else "./skills"
    registry = SkillRegistry(skills_dir)
    registry.build_index()

    query = input("Enter a query to test skill search: ")
    results = registry.search(query, top_k=3)
    print("\nTop matches:")
    for r in results:
        print(f"  [{r['score']:.3f}] {r['name']}: {r['description'][:80]}...")
