"""
Backward-compatibility shim.

The pipeline has been refactored into the ``pipeline/`` package.
This module re-exports the public API so existing callers
(``from pipeline import process_query``) continue to work unchanged.

The original monolithic source is preserved as ``_pipeline_legacy.py``.
"""
from pipeline.core import process_query, stream_query  # noqa: F401

__all__ = ["process_query", "stream_query"]
