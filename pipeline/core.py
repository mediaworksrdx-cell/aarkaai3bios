"""
AARKAAI Pipeline – Core orchestration functions.

This module provides the public API entry points:
    - process_query: Synchronous query processing (full pipeline)
    - stream_query: Async SSE streaming query processing

Implementation note:
    The function bodies are large (800+ lines each) with deeply interleaved
    module calls, conditional branching, and yield statements (for streaming).
    They remain in the original pipeline.py for now — this module re-exports them.

    Future refactors will:
    1. Extract the shared ~400-line context-gathering block into pipeline.context
    2. Move process_query here as pipeline.sync
    3. Move stream_query here as pipeline.streaming
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

# Load the original pipeline.py as a private module to avoid circular imports.
# The pipeline/ package (__init__.py) shadows the old pipeline.py module name,
# so we load it explicitly by file path.
_legacy_path = Path(__file__).resolve().parent.parent / "_pipeline_legacy.py"

_legacy_spec = importlib.util.spec_from_file_location(
    "_pipeline_legacy", str(_legacy_path)
)
if _legacy_spec and _legacy_spec.loader:
    _legacy_mod = importlib.util.module_from_spec(_legacy_spec)
    # Do NOT register in sys.modules — we only need the two functions
    _legacy_spec.loader.exec_module(_legacy_mod)
    process_query = _legacy_mod.process_query
    stream_query = _legacy_mod.stream_query
else:
    raise ImportError(
        f"Cannot load legacy pipeline.py from {_legacy_path}. "
        "Ensure the file exists alongside the pipeline/ package."
    )

__all__ = ["process_query", "stream_query"]
