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
import logging
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


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

    CORE_SKILLS = {
        "pdf", "docx", "xlsx", "pptx", "html", 
        "file-reading", "frontend-design", "skill-router", "premium-report", "skill-creator"
    }

    def _load_registry(self):
        """Scan skills_dir and load all SKILL.md frontmatter."""
        self.skills = {}
        # Make sure user-skills folder exists
        user_skills_dir = self.skills_dir / "user-skills"
        user_skills_dir.mkdir(parents=True, exist_ok=True)

        for skill_path in self.skills_dir.rglob("SKILL.md"):
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (IOError, OSError) as exc:
                logger.warning("Failed to read skill file %s: %s", skill_path, exc)
                continue

            # Parse YAML frontmatter between --- markers
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        meta = yaml.safe_load(parts[1])
                        name = meta.get("name")
                        description = meta.get("description", "")
                        if name:
                            # Flag core skills correctly based on name or directory path
                            name_clean = name.strip().lower().replace(" ", "-")
                            is_core = name_clean in self.CORE_SKILLS and "user-skills" not in str(skill_path)
                            self.skills[name_clean] = {
                                "name": name_clean,
                                "description": description,
                                "path": str(skill_path),
                                "is_core": is_core,
                            }
                    except yaml.YAMLError:
                        pass

    def validate_skill_content(self, content: str) -> tuple[bool, str]:
        """Validate content is structured as markdown with YAML frontmatter containing 'name' and 'description'."""
        if not content.startswith("---"):
            return False, "Error: Content must start with '---' for frontmatter."
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False, "Error: Frontmatter must be enclosed by '---' markers."
        try:
            meta = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            return False, f"Error: Invalid YAML frontmatter: {e}"

        if not meta or not isinstance(meta, dict):
            return False, "Error: Frontmatter must be a key-value dictionary."
        if "name" not in meta or not meta["name"]:
            return False, "Error: Frontmatter is missing a 'name' field."
        if "description" not in meta or not meta["description"]:
            return False, "Error: Frontmatter is missing a 'description' field."
        return True, meta["name"]

    def create_skill(self, name: str, content: str, user_id: str = "default_user", permissions: dict = None) -> str:
        """Create a new skill in a user-partitioned subdirectory with versioning support."""
        name_clean = name.strip().lower().replace(" ", "-")
        if name_clean in self.CORE_SKILLS:
            return f"Error: '{name_clean}' matches a protected system skill name."

        is_valid, validation_res = self.validate_skill_content(content)
        if not is_valid:
            return validation_res

        # Namespaced save structure: skills/user-skills/{user_id}/{name_clean}/
        skill_dir = self.skills_dir / "user-skills" / str(user_id) / name_clean
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Versioning: Scan directories inside skill_dir to find next vN
        version = 1
        existing_versions = [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")]
        if existing_versions:
            try:
                version = max(int(d.name[1:]) for d in existing_versions) + 1
            except ValueError:
                pass

        v_dir = skill_dir / f"v{version}"
        v_dir.mkdir(parents=True, exist_ok=True)

        # Write versioned file and main latest file
        skill_path = skill_dir / "SKILL.md"
        v_path = v_dir / "SKILL.md"

        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(v_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Handle permissions
        if permissions is None:
            permissions = {"web_access": True, "file_access": False, "shell_access": False}
        with open(skill_dir / "permissions.json", "w", encoding="utf-8") as f:
            json.dump(permissions, f, indent=2)

        self._load_registry()
        try:
            self.build_index()
        except Exception:
            pass
        return f"Success: Skill '{name_clean}' version v{version} created successfully."

    def update_skill(self, name: str, content: str, user_id: str = "default_user", permissions: dict = None) -> str:
        """Update an existing skill with a new version snapshot."""
        name_clean = name.strip().lower().replace(" ", "-")
        if name_clean in self.CORE_SKILLS:
            return f"Error: Cannot update core skill '{name_clean}'."

        is_valid, validation_res = self.validate_skill_content(content)
        if not is_valid:
            return validation_res

        skill_dir = self.skills_dir / "user-skills" / str(user_id) / name_clean
        if not skill_dir.exists():
            # Fallback if created without namespaces
            skill_dir = self.skills_dir / "user-skills" / name_clean
            if not skill_dir.exists():
                return f"Error: Skill '{name_clean}' does not exist for this user. Create it first."

        # Increment version
        version = 1
        existing_versions = [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")]
        if existing_versions:
            try:
                version = max(int(d.name[1:]) for d in existing_versions) + 1
            except ValueError:
                pass

        v_dir = skill_dir / f"v{version}"
        v_dir.mkdir(parents=True, exist_ok=True)

        skill_path = skill_dir / "SKILL.md"
        v_path = v_dir / "SKILL.md"

        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(v_path, "w", encoding="utf-8") as f:
            f.write(content)

        if permissions is not None:
            with open(skill_dir / "permissions.json", "w", encoding="utf-8") as f:
                json.dump(permissions, f, indent=2)

        self._load_registry()
        try:
            self.build_index()
        except Exception:
            pass
        return f"Success: Skill '{name_clean}' updated successfully to v{version}."

    def delete_skill(self, name: str, user_id: str = "default_user") -> str:
        """Delete an existing custom skill."""
        name_clean = name.strip().lower().replace(" ", "-")
        if name_clean in self.CORE_SKILLS:
            return f"Error: Cannot delete core skill '{name_clean}'."

        skill_dir = self.skills_dir / "user-skills" / str(user_id) / name_clean
        if not skill_dir.exists():
            skill_dir = self.skills_dir / "user-skills" / name_clean

        if not skill_dir.exists():
            return f"Error: Skill '{name_clean}' does not exist."

        import shutil
        shutil.rmtree(skill_dir)

        self._load_registry()
        try:
            self.build_index()
        except Exception:
            pass
        return f"Success: Skill '{name_clean}' deleted successfully."

    def get_skill_versions(self, name: str, user_id: str = "default_user") -> list[dict]:
        """Return list of version snapshots for a user skill."""
        name_clean = name.strip().lower().replace(" ", "-")
        skill_dir = self.skills_dir / "user-skills" / str(user_id) / name_clean
        if not skill_dir.exists():
            skill_dir = self.skills_dir / "user-skills" / name_clean
        if not skill_dir.exists():
            return []

        versions = []
        for d in sorted(skill_dir.iterdir()):
            if d.is_dir() and d.name.startswith("v"):
                try:
                    version_num = int(d.name[1:])
                    skill_file = d / "SKILL.md"
                    size = skill_file.stat().st_size if skill_file.exists() else 0
                    versions.append({
                        "version": d.name,
                        "version_number": version_num,
                        "size_bytes": size,
                    })
                except (ValueError, OSError):
                    continue
        return versions

    @property
    def skill_count(self) -> int:
        """Return the number of registered skills."""
        return len(self.skills)

    def build_index(self):
        """
        Embed all skill descriptions and build a FAISS index.
        Call once at startup (or after adding new skills).
        """
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
        except ImportError:
            # Skip build if sentence-transformers/faiss is not available/needed
            return

        self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self._names = list(self.skills.keys())
        descriptions = [self.skills[n]["description"] for n in self._names]

        embeddings = self._embedder.encode(descriptions, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype="float32")

        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # inner product = cosine on normalized
        self._index.add(embeddings)

        logger.info("Indexed %d skills", len(self._names))

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
        name_clean = name.strip().lower().replace(" ", "-")
        if name_clean not in self.skills:
            return f"Error: skill '{name_clean}' not found. Call list_skills() to see available skills."

        path = self.skills[name_clean]["path"]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def list_skills(self) -> list[dict]:
        """
        Return all skills with name + description + is_core.
        This is the function your LLM tool call maps to.
        """
        return [
            {
                "name": s["name"],
                "description": s["description"],
                "is_core": s.get("is_core", False)
            }
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

