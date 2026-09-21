"""
Shared pytest fixtures for the AARKAAI test suite.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_pipeline():
    """Mock process_query so HTTP tests never touch the real inference engine."""
    from schemas import PromptResponse

    dummy = PromptResponse(
        response="test response",
        intent="general_query",
        confidence=0.9,
        sources=["aarkaa-3b"],
        detected_language="en",
        processing_time=0.1,
    )
    with patch("pipeline.process_query", return_value=dummy) as mock:
        yield mock


@pytest.fixture
def mock_db_session():
    """Provide a lightweight in-memory SQLite session for unit tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_client(mock_pipeline):
    """FastAPI TestClient with the pipeline mocked out."""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
