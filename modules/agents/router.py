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
            return normalized
    except Exception as exc:
        logger.error("route_query failed to score: %s. Fallback to default.", exc)
    
    # Fallback default
    return {
        "coding": 0.0,
        "debugging": 0.0,
        "finance": 0.0,
        "trading": 0.0,
        "marketing": 0.0,
        "research": 0.0,
        "customer_support": 0.0
    }


def select_agents(query: str, threshold: float = 0.5) -> List[Tuple[str, float]]:
    """Selects all agents exceeding the confidence threshold, sorted by score descending."""
    scores = route_query(query)
    selected = [(k, v) for k, v in scores.items() if v >= threshold]
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected
