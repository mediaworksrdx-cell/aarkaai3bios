import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.query_understanding import analyze, DataSource, SubQuery, QueryPlan


@pytest.fixture(autouse=True)
def mock_extract_tickers():
    with patch('modules.finance.extract_tickers') as mock:
        mock.return_value = []
        yield mock


def test_simple_price_query(mock_extract_tickers):
    mock_extract_tickers.return_value = ["SBIN.NS"]
    plan = analyze("SBI price", domain="finance", intent="general_query")
    assert any(sq.source_type == DataSource.MARKET_API for sq in plan.sub_queries)
    assert plan.bypass_llm is True
    assert plan.complexity == "simple"


def test_compound_query_why_falling(mock_extract_tickers):
    mock_extract_tickers.return_value = ["SBIN.NS"]
    plan = analyze("Why is SBI falling today?", domain="finance", intent="general_query")
    sources = [sq.source_type for sq in plan.sub_queries]
    assert DataSource.MARKET_API in sources
    assert DataSource.NEWS_SEARCH in sources
    assert plan.complexity in ("compound", "complex")
    assert plan.requires_synthesis is True
    assert plan.bypass_llm is False


def test_greeting_query():
    plan = analyze("Hello", domain="general", intent="greeting")
    assert any(sq.source_type == DataSource.MODEL_ONLY for sq in plan.sub_queries)
    assert plan.complexity == "simple"


def test_coding_query():
    plan = analyze("Write a Python function to sort a list", domain="technology", intent="coding_help")
    assert any(sq.source_type == DataSource.CODER for sq in plan.sub_queries)
    assert plan.model_target == "coder"


def test_code_execution_query():
    plan = analyze("What is the output of this code: ```python\nprint(1+1)\n```", domain="technology", intent="coding_help")
    assert any(sq.source_type == DataSource.CODE_EXECUTION for sq in plan.sub_queries)


def test_financial_tool_query():
    plan = analyze("Calculate CAGR for investment from 10000 to 25000 in 5 years", domain="finance", intent="general_query")
    assert any(sq.source_type == DataSource.FINANCIAL_TOOL for sq in plan.sub_queries)


def test_mongodb_portfolio_query():
    plan = analyze("Show my portfolio holdings", domain="finance", intent="general_query")
    assert any(sq.source_type == DataSource.MONGODB for sq in plan.sub_queries)


def test_news_query():
    plan = analyze("Latest news about RBI interest rate decision", domain="web_search", intent="news_search")
    assert any(sq.source_type == DataSource.NEWS_SEARCH for sq in plan.sub_queries)


def test_reasoning_query():
    plan = analyze("A bat and ball cost $1.10. The bat costs $1 more than the ball. How much does the ball cost?", domain="general", intent="reasoning")
    assert any(sq.source_type == DataSource.MODEL_ONLY for sq in plan.sub_queries)
    assert plan.complexity == "simple"


def test_web_search_factual():
    plan = analyze("Who is the CEO of Google?", domain="general", intent="general_query")
    assert any(sq.source_type == DataSource.WEB_SEARCH for sq in plan.sub_queries)


def test_rag_for_knowledge_query():
    plan = analyze("Explain what PE ratio means in stock valuation", domain="finance", intent="general_query")
    assert any(sq.source_type == DataSource.RAG for sq in plan.sub_queries)


def test_empty_query():
    plan = analyze("")
    assert any(sq.source_type == DataSource.MODEL_ONLY for sq in plan.sub_queries)
    assert plan.complexity == "simple"


def test_complex_multi_source_query(mock_extract_tickers):
    mock_extract_tickers.return_value = ["SBIN.NS"]
    plan = analyze("Analyze my SBI holdings performance with latest news and technical analysis", domain="finance", intent="general_query")
    sources = set(sq.source_type for sq in plan.sub_queries)
    assert len(sources) >= 3
    assert plan.complexity in ("compound", "complex")


def test_to_dict_serialization():
    plan = QueryPlan(
        domain="finance",
        intent="general_query",
        complexity="simple",
        sub_queries=[SubQuery(query_text="SBI price", source_type=DataSource.MARKET_API, priority=1)],
        requires_synthesis=False,
        bypass_llm=True,
        model_target="general_3b"
    )
    d = plan.to_dict()
    assert isinstance(d, dict)
    assert d["domain"] == "finance"
    assert d["intent"] == "general_query"
    assert d["complexity"] == "simple"
    assert len(d["sub_queries"]) == 1
    assert d["sub_queries"][0]["source_type"] == "market_api"


def test_bypass_llm_only_for_single_market(mock_extract_tickers):
    mock_extract_tickers.return_value = ["TCS.NS"]
    plan_single = analyze("TCS price", domain="finance", intent="general_query")
    assert plan_single.bypass_llm is True

    plan_compound = analyze("Why is TCS falling today?", domain="finance", intent="general_query")
    assert plan_compound.bypass_llm is False
