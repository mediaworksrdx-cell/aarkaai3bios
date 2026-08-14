import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.query_understanding import DataSource, SubQuery, QueryPlan, SourceResult
from modules.context_fusion import ContextFusion, FusedContext
from modules.hybrid_router import HybridQueryRouter, RouterResult, _CircuitBreaker


class TestContextFusion:
    def test_fusion_empty_results(self):
        fusion = ContextFusion()
        plan = QueryPlan(original_query="test", sub_queries=[])
        result = fusion.fuse([], plan)
        assert result.context == ""
        assert len(result.sources_used) == 0

    def test_fusion_single_market_data(self):
        fusion = ContextFusion()
        res = SourceResult(
            source=DataSource.MARKET_API,
            data="SBIN.NS: ₹812.50 -2.3%",
            is_valid=True,
            metadata={"symbol": "SBIN.NS"}
        )
        plan = QueryPlan(
            original_query="price",
            sub_queries=[SubQuery(source_type=DataSource.MARKET_API, query_text="SBIN.NS", priority=1, required=True)]
        )
        result = fusion.fuse([res], plan)
        assert "[Market Data" in result.context
        sources_str = [str(s).lower() for s in result.sources_used]
        assert any("market" in s for s in sources_str)

    def test_fusion_multiple_sources_priority_ordering(self):
        fusion = ContextFusion()
        res_web = SourceResult(source=DataSource.WEB_SEARCH, data="Web data unique facts", is_valid=True)
        res_market = SourceResult(source=DataSource.MARKET_API, data="Market data live stats", is_valid=True)
        res_news = SourceResult(source=DataSource.NEWS_SEARCH, data="News data latest update", is_valid=True)
        
        plan = QueryPlan(original_query="test", sub_queries=[])
        result = fusion.fuse([res_web, res_market, res_news], plan)
        
        idx_market = result.context.find("Market data")
        idx_news = result.context.find("News data")
        idx_web = result.context.find("Web data")
        
        assert idx_market != -1 and idx_news != -1 and idx_web != -1
        assert idx_market < idx_news < idx_web

    def test_fusion_deduplication_by_overlap(self):
        fusion = ContextFusion()
        data1 = "The Indian stock market showed strong performance today with Sensex rallying over 500 points."
        data2 = "The Indian stock market showed strong performance today with Sensex rallying over 500 points."
        res1 = SourceResult(source=DataSource.NEWS_SEARCH, data=data1, is_valid=True)
        res2 = SourceResult(source=DataSource.WEB_SEARCH, data=data2, is_valid=True)
        
        plan = QueryPlan(original_query="test", sub_queries=[])
        result = fusion.fuse([res1, res2], plan)
        
        assert "dedup_count" in result.metadata
        assert result.metadata["dedup_count"] > 0

    def test_fusion_context_budget_truncation(self):
        fusion = ContextFusion()
        large_data = "word " * 15000
        res = SourceResult(source=DataSource.WEB_SEARCH, data=large_data, is_valid=True)
        plan = QueryPlan(original_query="test", sub_queries=[])
        result = fusion.fuse([res], plan)
        
        assert "truncated_sources" in result.metadata
        assert len(result.metadata["truncated_sources"]) > 0

    def test_fusion_chat_history_injection(self):
        fusion = ContextFusion()
        chat_history = [
            {"role": "user", "message": "What is SBI?"},
            {"role": "assistant", "message": "SBI is State Bank of India."}
        ]
        plan = QueryPlan(original_query="price", sub_queries=[])
        res = SourceResult(source=DataSource.MARKET_API, data="Price: 800", is_valid=True)
        result = fusion.fuse([res], plan, chat_history=chat_history)
        assert "[Conversation History]" in result.context
        assert result.context.find("[Conversation History]") < result.context.find("[Market Data")

    def test_fusion_user_facts_injection(self):
        fusion = ContextFusion()
        user_facts = "User holds 100 shares of SBI"
        plan = QueryPlan(original_query="price", sub_queries=[])
        res = SourceResult(source=DataSource.MARKET_API, data="Price: 800", is_valid=True)
        result = fusion.fuse([res], plan, user_facts=user_facts)
        assert "[User Profile]" in result.context
        assert user_facts in result.context

    def test_fusion_skips_invalid_results(self):
        fusion = ContextFusion()
        res_valid = SourceResult(source=DataSource.MARKET_API, data="Valid market data", is_valid=True)
        res_invalid = SourceResult(source=DataSource.WEB_SEARCH, data="Invalid data", is_valid=False, error="Error")
        plan = QueryPlan(original_query="test", sub_queries=[])
        result = fusion.fuse([res_valid, res_invalid], plan)
        assert "Valid market data" in result.context
        assert "Invalid data" not in result.context


class TestCircuitBreaker:
    def test_circuit_breaker_opens_after_threshold(self):
        cb = _CircuitBreaker(name="test_source", threshold=3, cooldown=60.0)
        assert not cb.is_open
        cb.record_failure()
        cb.record_failure()
        assert not cb.is_open
        cb.record_failure()
        assert cb.is_open

    def test_circuit_breaker_resets_on_success(self):
        cb = _CircuitBreaker(name="test_source", threshold=3, cooldown=60.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert not cb.is_open
        cb.record_failure()
        assert not cb.is_open

    def test_circuit_breaker_cooldown_recovery(self):
        cb = _CircuitBreaker(name="test_source", threshold=3, cooldown=10.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open
        cb._last_failure = time.time() - 15.0
        assert not cb.is_open


class TestHybridQueryRouter:
    def test_router_parallel_execution(self):
        router = HybridQueryRouter()
        plan = QueryPlan(
            original_query="Why is SBI falling?",
            sub_queries=[
                SubQuery(query_text="SBI price", source_type=DataSource.MARKET_API, priority=1),
                SubQuery(query_text="SBI news", source_type=DataSource.NEWS_SEARCH, priority=1)
            ]
        )

        def mock_market(sq, uid):
            time.sleep(0.05)
            return SourceResult(source=DataSource.MARKET_API, data="Price: 800", is_valid=True)

        def mock_news(sq, uid):
            time.sleep(0.05)
            return SourceResult(source=DataSource.NEWS_SEARCH, data="News: SBI quarterly report", is_valid=True)

        with patch.object(router._handlers, "fetch_market_data", side_effect=mock_market), \
             patch.object(router._handlers, "fetch_news", side_effect=mock_news), \
             patch("modules.aarkaa_engine.final_response", return_value="Analyzed answer"):
            
            start = time.perf_counter()
            result = router.execute(plan)
            elapsed = time.perf_counter() - start
            
            assert len(result.source_results) == 2
            assert result.final_answer == "Analyzed answer"
            assert elapsed < 0.25

    def test_router_empty_plan_returns_empty(self):
        router = HybridQueryRouter()
        plan = QueryPlan(original_query="Hello", sub_queries=[SubQuery(query_text="Hello", source_type=DataSource.MODEL_ONLY, priority=1)])
        result = router.execute(plan)
        assert result.final_answer == ""

    def test_router_bypass_llm_for_price_query(self):
        router = HybridQueryRouter()
        plan = QueryPlan(
            original_query="SBI price",
            bypass_llm=True,
            requires_synthesis=False,
            sub_queries=[SubQuery(query_text="SBI price", source_type=DataSource.MARKET_API, priority=1)]
        )

        with patch.object(router._handlers, "fetch_market_data", return_value=SourceResult(source=DataSource.MARKET_API, data="SBI Live Price: 812.50", is_valid=True)), \
             patch("modules.aarkaa_engine.final_response") as mock_llm:
            
            result = router.execute(plan)
            assert result.bypassed_llm is True
            assert "SBI Live Price: 812.50" in result.final_answer
            mock_llm.assert_not_called()

    def test_router_calls_llm_for_compound_query(self):
        router = HybridQueryRouter()
        plan = QueryPlan(
            original_query="Why is SBI falling today?",
            bypass_llm=False,
            requires_synthesis=True,
            sub_queries=[
                SubQuery(query_text="SBI price", source_type=DataSource.MARKET_API, priority=1),
                SubQuery(query_text="SBI news", source_type=DataSource.NEWS_SEARCH, priority=1)
            ]
        )

        with patch.object(router._handlers, "fetch_market_data", return_value=SourceResult(source=DataSource.MARKET_API, data="Price: 800", is_valid=True)), \
             patch.object(router._handlers, "fetch_news", return_value=SourceResult(source=DataSource.NEWS_SEARCH, data="News: Loss reported", is_valid=True)), \
             patch("modules.aarkaa_engine.final_response", return_value="SBI is down due to quarterly loss.") as mock_llm:
            
            result = router.execute(plan)
            assert result.bypassed_llm is False
            assert result.final_answer == "SBI is down due to quarterly loss."
            mock_llm.assert_called_once()

    def test_router_handles_source_failure_gracefully(self):
        router = HybridQueryRouter()
        plan = QueryPlan(
            original_query="SBI update",
            requires_synthesis=False,
            sub_queries=[
                SubQuery(query_text="SBI price", source_type=DataSource.MARKET_API, priority=1),
                SubQuery(query_text="SBI news", source_type=DataSource.NEWS_SEARCH, priority=1)
            ]
        )

        with patch.object(router._handlers, "fetch_market_data", side_effect=Exception("API down")), \
             patch.object(router._handlers, "fetch_news", return_value=SourceResult(source=DataSource.NEWS_SEARCH, data="News is fine", is_valid=True)), \
             patch("modules.aarkaa_engine.final_response", return_value="Synthesized news only"):
            
            result = router.execute(plan)
            assert len(result.source_results) == 2
            sources_valid = {r.source: r.is_valid for r in result.source_results}
            assert sources_valid[DataSource.MARKET_API] is False
            assert sources_valid[DataSource.NEWS_SEARCH] is True

    def test_router_status_callback(self):
        router = HybridQueryRouter()
        plan = QueryPlan(
            original_query="SBI price",
            bypass_llm=True,
            sub_queries=[SubQuery(query_text="SBI price", source_type=DataSource.MARKET_API, priority=1)]
        )

        callback_messages = []
        def status_cb(msg):
            callback_messages.append(msg)

        with patch.object(router._handlers, "fetch_market_data", return_value=SourceResult(source=DataSource.MARKET_API, data="Price: 800", is_valid=True)):
            router.execute(plan, status_callback=status_cb)
            assert len(callback_messages) > 0
            assert any("Querying" in msg for msg in callback_messages)
