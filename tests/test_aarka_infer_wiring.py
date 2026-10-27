"""
AARKAAI — AARKA Infer End-to-End Wiring Verification Suite
Tests the seamless in-process integration between aarka_infer,
modules/aarkaa_engine.py, and modules/ai_router.py.
"""
import asyncio
import pytest
from unittest.mock import patch

from aarka_infer.adapters.engine_adapter import AarkaaLegacyAdapter
from aarka_infer.adapters.router_adapter import InferRouterDispatcher
from aarka_infer.runtime.engine import AarkaInferEngine
from aarka_infer.runtime.scheduler import RequestPriority
from modules import aarkaa_engine
from modules.ai_router import AIRouter


@pytest.fixture(autouse=True)
def ensure_infer_engine():
    """Ensures AarkaInferEngine singleton is available."""
    engine = AarkaInferEngine.get_instance()
    yield engine


def test_gguf_candidates_prioritize_7b():
    """Verify that 7B candidate models are prioritized over 3B models."""
    from pathlib import Path
    candidate_names = [Path(c).name.lower() for c in aarkaa_engine._GGUF_CANDIDATES]
    first_7b_idx = next(i for i, name in enumerate(candidate_names) if "7b" in name)
    first_3b_idx = next(i for i, name in enumerate(candidate_names) if "3b" in name)
    assert first_7b_idx < first_3b_idx, "7B models must precede 3B models in search priority"


def test_aarkaa_engine_adapter_initialization():
    """Verify that aarkaa_engine correctly resolves the AARKA Infer adapter."""
    adapter = aarkaa_engine._get_infer_adapter()
    assert adapter is not None
    assert isinstance(adapter, AarkaaLegacyAdapter)
    assert adapter.engine is not None


def test_aarkaa_engine_generate_stream_wired():
    """Verify that aarkaa_engine._generate_stream yields tokens through AARKA Infer."""
    prompt = "<|im_start|>system\nYou are AARKAA Financial Analyst.<|im_end|>\n<|im_start|>user\nAnalyze ROCE and PE ratio.<|im_end|>\n<|im_start|>assistant\n"
    tokens = list(aarkaa_engine._generate_stream(prompt, max_new_tokens=100))
    assert len(tokens) > 0, "Tokens must be yielded from generation stream"
    full_text = "".join(tokens)
    assert len(full_text.strip()) > 0
    assert "AARKAA" in full_text or "ROCE" in full_text or "P/E" in full_text


def test_aarkaa_engine_generate_raw_wired():
    """Verify that aarkaa_engine.generate_raw executes via AARKA Infer."""
    prompt = "<|im_start|>user\nWrite a python function to compute CAGR.<|im_end|>\n<|im_start|>assistant\n"
    result = aarkaa_engine.generate_raw(prompt, max_new_tokens=120)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_aarkaa_engine_is_available():
    """Verify that aarkaa_engine.is_available() reflects backend readiness."""
    available = aarkaa_engine.is_available()
    assert isinstance(available, bool)
    assert available is True, "is_available() must report True when AARKA Infer backend is healthy"


@pytest.mark.anyio
async def test_ai_router_direct_infer_dispatch_general_3b():
    """Verify that AIRouter.dispatch_vllm directs general_3b queries in-process to AARKA Infer."""
    messages = [
        {"role": "system", "content": "You are AARKAA Quantitative Engine."},
        {"role": "user", "content": "What is the capital allocation strategy for Reliance?"},
    ]
    resp = await AIRouter.dispatch_vllm(
        target_service="general_3b",
        messages=messages,
        max_tokens=150,
        temperature=0.3,
        stream=False,
    )
    assert isinstance(resp, dict)
    assert "choices" in resp
    assert len(resp["choices"]) > 0
    message_content = resp["choices"][0]["message"]["content"]
    assert len(message_content.strip()) > 0
    assert "content" in resp
    assert resp["content"] == message_content


@pytest.mark.anyio
async def test_aarka_infer_radix_kv_cache_prefix_hit():
    """Verify that repetitive system prompt prefixes trigger Radix KV cache hits."""
    engine = AarkaInferEngine.get_instance()
    await engine.initialize()

    system_prefix = "You are AARKAA-3B, a high-frequency algorithmic quantitative researcher."
    prompt1 = f"<|im_start|>system\n{system_prefix}<|im_end|>\n<|im_start|>user\nCalculate Sharpe ratio for 12% return and 4% risk-free.<|im_end|>\n<|im_start|>assistant\n"
    prompt2 = f"<|im_start|>system\n{system_prefix}<|im_end|>\n<|im_start|>user\nCalculate Sortino ratio with downside deviation 3%.<|im_end|>\n<|im_start|>assistant\n"

    # First query populates Radix prefix tree
    _ = await engine.generate(prompt1, priority=RequestPriority.HIGH)
    stats_before = engine.kv_cache.get_stats()

    # Second query shares the identical system prefix
    _ = await engine.generate(prompt2, priority=RequestPriority.HIGH)
    stats_after = engine.kv_cache.get_stats()

    assert stats_after["total_requests"] > stats_before["total_requests"]
    assert stats_after["cache_hits"] >= 1, "Second request must hit the Radix prefix tree"
    assert stats_after["reused_tokens"] > 0, "Prefix caching must save evaluated tokens"


@pytest.mark.anyio
async def test_aarkaa_legacy_adapter_async_streaming():
    """Verify that AarkaaLegacyAdapter.generate_stream_async yields tokens cleanly."""
    adapter = AarkaaLegacyAdapter()
    prompt = "Explain PE valuation."
    tokens = []
    async for tok in adapter.generate_stream_async(prompt, max_tokens=50):
        tokens.append(tok)
    assert len(tokens) > 0
    assert len("".join(tokens).strip()) > 0
