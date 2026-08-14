"""
Shared test fixtures for the AARKAAI test suite.

Mocks heavy dependencies (llama-cpp, ChromaDB, MongoDB, yfinance, etc.)
so tests can run without any running services.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_heavy_imports(monkeypatch):
    """
    Pre-mock modules that require external services or hardware
    so that importing any AARKAAI module never fails in CI.
    """
    # Stub out sentence_transformers if not installed
    if "sentence_transformers" not in sys.modules:
        monkeypatch.setitem(sys.modules, "sentence_transformers", MagicMock())

    # Stub out llama_cpp if not installed
    if "llama_cpp" not in sys.modules:
        monkeypatch.setitem(sys.modules, "llama_cpp", MagicMock())

    # Stub out chromadb if not installed
    if "chromadb" not in sys.modules:
        monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
