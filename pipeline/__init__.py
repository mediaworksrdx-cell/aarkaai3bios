"""
AARKAAI Backend – Request Processing Pipeline Package

Decomposition of the monolithic pipeline.py into focused modules:
- preprocessor: Input normalization, language detection, sanitization
- context_builder: Memory + RAG + profile compilation
- executor: LLM invocation, streaming, token management  
- postprocessor: Response formatting, tool result integration
- classifiers: Intent classification, keyword heuristics
- orchestrator: Top-level pipeline coordination

Preserves full backward compatibility with the legacy pipeline.py.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

# Load legacy pipeline.py functions and symbols seamlessly
_legacy_path = Path(__file__).resolve().parent.parent / "pipeline.py"
if _legacy_path.is_file():
    _spec = importlib.util.spec_from_file_location("pipeline_legacy", _legacy_path)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        for _attr in dir(_mod):
            if not _attr.startswith("__"):
                globals()[_attr] = getattr(_mod, _attr)

# Export submodules
from pipeline import preprocessor
from pipeline import context_builder

__all__ = [
    "process_query",
    "process_query_stream",
    "preprocessor",
    "context_builder",
]
