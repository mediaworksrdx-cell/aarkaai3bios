import sys
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas import PromptResponse
from modules.query_understanding import QueryPlan, SubQuery, DataSource, SourceResult
from modules.context_fusion import FusedContext
from modules.hybrid_router import RouterResult


@pytest.fixture(autouse=True)
def mock_all_services():
    """Mock heavy external dependencies during integration testing."""
    with patch("modules.semantic_filter.classify", return_value={"domain": "finance", "confidence": 0.95, "intent": "general_query"}), \
         patch("modules.memory.store_conversation"), \
         patch("modules.memory.extract_user_facts"), \
         patch("modules.memory.get_chat_context", return_value=[]), \
         patch("modules.memory.get_user_facts_prompt", return_value=""), \
         patch("modules.aarkaa_engine.final_response", return_value="Synthesized final answer from AARKAA"):
        yield


def test_pipeline_with_hqr_disabled():
    """When HQR_ENABLED is False, pipeline should fall through to standard waterfall without error."""
    import pipeline
    with patch("config.HQR_ENABLED", False), \
         patch("modules.tool_router.process_with_tools") as mock_tool_router, \
         patch("modules.aarkaa_engine.final_response", return_value="Waterfall answer"):
        
        mock_tool_router.return_value = MagicMock(permission_denied=False, final_answer="Tool answer", tool_results=[], total_time_ms=50.0)
        
        response = pipeline.process_query("Why is SBI falling today?", user_id="test_user")
        assert isinstance(response, PromptResponse)
        assert response.response == "Tool answer"
        assert "hybrid_router" not in response.sources


def test_pipeline_with_hqr_enabled():
    """When HQR_ENABLED is True, pipeline routes query via hybrid router."""
    import pipeline
    
    mock_router_result = RouterResult(
        final_answer="SBI is falling due to sector correction.",
        fused_context=FusedContext(
            context="[Market Data]\nSBI down 2%",
            sources_used=["market_api", "news_search"],
            total_chars=40,
            source_count=2
        ),
        total_time_ms=120.0,
        model_used="aarkaa-7b"
    )

    with patch("config.HQR_ENABLED", True), \
         patch("modules.hybrid_router.execute_hybrid", return_value=mock_router_result), \
         patch("modules.finance.extract_tickers", return_value=["SBIN.NS"]):
        
        response = pipeline.process_query("Why is SBI falling today?", user_id="test_user")
        assert isinstance(response, PromptResponse)
        assert response.response == "SBI is falling due to sector correction."
        assert "hybrid_router" in response.sources
        assert "market_api" in response.sources
        assert "news_search" in response.sources


def test_pipeline_stream_query_hqr_enabled():
    """Test that stream_query yields status events and content tokens when HQR is enabled."""
    import pipeline

    mock_router_result = RouterResult(
        final_answer="SBI fell 2% today on profit booking.",
        fused_context=FusedContext(
            context="[Market Data]\nSBI: 800",
            sources_used=["market_api"],
            total_chars=20,
            source_count=1
        ),
        total_time_ms=80.0,
        model_used="aarkaa-7b"
    )

    async def _run_stream():
        events = []
        async for event in pipeline.stream_query("Why is SBI falling today?", user_id="test_user"):
            events.append(event)
        return events

    with patch("config.HQR_ENABLED", True), \
         patch("modules.hybrid_router.execute_hybrid", return_value=mock_router_result), \
         patch("modules.finance.extract_tickers", return_value=["SBIN.NS"]):

        events = asyncio.run(_run_stream())

        event_types = [e.get("type") for e in events]
        assert "status" in event_types
        assert "metadata" in event_types
        assert "content" in event_types
        assert "final" in event_types

        # Verify streamed content reconstructs full response
        content_tokens = [e.get("token", "") for e in events if e.get("type") == "content"]
        reconstructed = "".join(content_tokens)
        assert reconstructed == "SBI fell 2% today on profit booking."
