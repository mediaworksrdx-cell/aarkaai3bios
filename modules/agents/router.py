"""
AARKAAI – Multi-Agent Router
Classifies user queries dynamically and scores confidence levels for each agent.
Supports hybrid team synthesis for scores exceeding a threshold.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Tuple

from modules import aarkaa_engine

logger = logging.getLogger(__name__)

SYSTEM_ROUTER_PROMPT = """You are AARKAAI Agent Selector. Your job is to analyze the user request and determine the confidence level (a float from 0.0 to 1.0) for each of the following agent profiles:
- coding: Expert software architect, linter, and programmer.
- debugging: Expert debugger, traceback analyzer, and bug resolver.
- finance: Expert financial analyst, modeler, and corporate strategist.
- trading: Quantitative trading strategist, technical indicators, risk management.
- marketing: Creative copywriter, SEO, growth marketer, branding.
- research: Academic researcher, data collector, literature synthesis.
- customer_support: Empathetic customer support specialist.

Output ONLY a JSON block containing the agent names as keys and the confidence floats as values. Do NOT include any conversational text. Example:
{
  "coding": 0.9,
  "debugging": 0.8,
  "finance": 0.0,
  "trading": 0.0,
  "marketing": 0.0,
  "research": 0.2,
  "customer_support": 0.0
}"""


_KEYWORD_FALLBACKS = {
    "coding": ["code", "coding", "python", "javascript", "function", "class", "algorithm", "tree", "avl", "git", "sql", "bug", "syntax", "compile", "script", "balanced"],
    "debugging": ["debug", "debugging", "traceback", "error", "exception", "failed", "crash", "stack trace", "null pointer", "undefined"],
    "finance": ["cagr", "irr", "sip", "emi", "portfolio", "balance sheet", "pnl", "valuation", "ratio", "revenue", "ebitda", "financial", "earnings"],
    "trading": ["trading", "ohlc", "candlestick", "rsi", "macd", "supertrend", "option", "strike", "call", "put", "oi", "vwap", "indicator", "nifty"],
    "marketing": ["marketing", "campaign", "seo", "branding", "copywriting", "social media", "content strategy", "brand"],
    "research": ["research", "paper", "literature", "study", "history of", "overview", "survey", "cite", "deep dive"],
    "customer_support": ["support", "help", "account", "login", "password", "subscription", "contact", "billing"],
    "screener": ["screener", "screen", "filter stocks", "high roe", "low pe", "undervalued stocks", "quant screen"]
}


def _heuristic_route_query(query: str) -> Dict[str, float]:
    """Fallback heuristic scoring based on domain keywords."""
    q_lower = query.lower()
    scores = {}
    for agent_name, keywords in _KEYWORD_FALLBACKS.items():
        match_count = sum(1 for kw in keywords if kw in q_lower)
        if match_count > 0:
            scores[agent_name] = min(round(0.45 + (match_count * 0.2), 2), 0.95)
        else:
            scores[agent_name] = 0.0
    return scores


def route_query(query: str) -> Dict[str, float]:
    """Scores confidence levels for all agents based on the query."""
    formatted_prompt = aarkaa_engine._build_chatml(SYSTEM_ROUTER_PROMPT, query)
    try:
        response = aarkaa_engine._generate(
            formatted_prompt,
            max_new_tokens=256,
            temperature=0.0
        )
        # Handle cleanup of model response if any formatting leakage occurs
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx + 1]
            scores = json.loads(json_str)
            # Normalize keys and values
            normalized = {}
            for k, v in scores.items():
                if isinstance(v, (int, float)):
                    normalized[k.lower().strip()] = float(v)
            if any(v > 0.0 for v in normalized.values()):
                return normalized
    except Exception as exc:
        logger.error("route_query failed to score: %s. Fallback to heuristic.", exc)

    return _heuristic_route_query(query)


def select_agents(query: str, threshold: float = 0.5) -> List[Tuple[str, float]]:
    """Selects all agents exceeding the confidence threshold, sorted by score descending."""
    scores = route_query(query)
    selected = [(k, v) for k, v in scores.items() if v >= threshold]
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected
