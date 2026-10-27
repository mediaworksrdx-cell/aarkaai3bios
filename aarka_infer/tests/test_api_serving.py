"""
Test suite for AARKA Infer FastAPI HTTP and Streaming Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from aarka_infer.server import create_app
from aarka_infer.runtime.engine import AarkaInferEngine


@pytest.fixture(scope="module")
def client():
    # Pre-initialize engine with mock backend for deterministic test execution
    engine = AarkaInferEngine.get_instance()
    import asyncio
    asyncio.run(engine.initialize(force_backend="mock"))

    app = create_app()
    with TestClient(app) as tc:
        yield tc


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["architecture_valid"] is True


def test_models_endpoint(client):
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    model_ids = [m["id"] for m in data["data"]]
    assert any("aarkaa-3b" in mid for mid in model_ids)


def test_chat_completion_non_streaming(client):
    payload = {
        "model": "rthshr/aarkaa-3b-v1",
        "messages": [
            {"role": "user", "content": "Explain P/E ratio"}
        ],
        "temperature": 0.5,
        "max_tokens": 128,
        "stream": False,
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
    choice = data["choices"][0]
    assert choice["message"]["role"] == "assistant"
    assert len(choice["message"]["content"]) > 0
    assert "usage" in data
    assert data["usage"]["total_tokens"] > 0


def test_chat_completion_streaming(client):
    payload = {
        "model": "aarkaa-3b",
        "messages": [
            {"role": "user", "content": "Write a python function"}
        ],
        "stream": True,
    }
    resp = client.post("/v1/chat/completions", json=payload)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    lines = [line for line in resp.text.split("\n") if line.strip()]
    data_lines = [l for l in lines if l.startswith("data: ")]
    assert len(data_lines) >= 2
    assert data_lines[-1] == "data: [DONE]"


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "requests" in data
    assert "tokens" in data
    assert "ttft_ms" in data
    assert "kv_cache" in data
