"""
Shared test fixtures for the AARKAAI test suite.

Mocks heavy dependencies (llama-cpp, ChromaDB, MongoDB, yfinance, passlib, etc.)
so tests can run cleanly without any running external services.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Immediate top-level stubs for collection-time imports of optional heavy dependencies
_STUB_MODULES = [
    "sentence_transformers",
    "llama_cpp",
    "yfinance",
    "passlib",
    "passlib.context",
    "google.genai",
    "google",
]

for mod in _STUB_MODULES:
    if mod not in sys.modules:
        try:
            __import__(mod)
        except ImportError:
            stub = MagicMock()
            if mod == "passlib.context":
                ctx_mock = MagicMock()
                ctx_mock.CryptContext.return_value.verify.return_value = True
                ctx_mock.CryptContext.return_value.hash.return_value = "hashed_pw"
                stub.CryptContext = ctx_mock.CryptContext
            sys.modules[mod] = stub


@pytest.fixture(autouse=True)
def mock_heavy_imports(monkeypatch):
    """
    Ensure modules that require external services or hardware
    are safely mocked during test execution.
    """
    for mod in _STUB_MODULES:
        if mod not in sys.modules:
            monkeypatch.setitem(sys.modules, mod, MagicMock())

