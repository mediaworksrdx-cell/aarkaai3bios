"""
AARKAAI – Evaluation Harness and Content-Level Assertion Verifier.
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Authoritative ground-truth assertions for flagged audit items
_AUDIT_ASSERTIONS: Dict[Tuple[str, int], List[str]] = {
    ("FinanceAgent", 2): ["cash", "subtract", "ebitda"],
    ("FinanceAgent", 5): ["24.47%"],
    ("FinanceAgent", 8): ["equity multiplier", "assets", "equity"],
    ("FinanceAgent", 9): ["net borrowing"],
    ("FinanceAgent", 16): ["1.2", "1.4", "3.3", "0.6"],
    ("FinanceAgent", 17): ["2019", "right-of-use", "lease liability"],
    ("TradingAgent", 1): ["lower low", "higher low", "higher high"],
    ("TradingAgent", 4): ["open interest", "volume"],
    ("TradingAgent", 9): ["final upper band", "final lower band", "atr"],
    ("TradingAgent", 11): ["lower shadow", "confirmation"],
    ("TradingAgent", 12): ["lower-strike", "higher-strike", "net debit"],
    ("TradingAgent", 13): ["net credit", "four-leg"],
    ("TradingAgent", 14): ["09:15", "15:30", "09:00", "09:08"],
    ("TradingAgent", 19): ["higher-strike put", "lower-strike put", "net debit"],
    ("ReasonerAgent", 4): ["goat", "wolf", "cabbage"],
    ("ReasonerAgent", 16): ["366", "wednesday"],
    ("ReasonerAgent", 18): ["75 miles", "1.0 hour"],
    ("ReasonerAgent", 19): ["50.73%", "253"],
    ("ReasonerAgent", 20): ["6 coins", "2 quarters", "1 dime", "3 pennies"],
}


def verify_answer_correctness(agent_name: str, query_idx: int, output: str, is_code_agent: bool = False) -> Tuple[bool, str]:
    """
    Rigorous content, mathematical, and AST verification replacing naive len checks.
    """
    if not output or not output.strip():
        return False, "Empty output"

    out_low = output.lower().replace("\\%", "%").replace("\\text{ ", " ")

    # 1. Check specific mathematical / factual assertions if registered
    req_tokens = _AUDIT_ASSERTIONS.get((agent_name, query_idx), [])
    for tok in req_tokens:
        if tok.lower() not in out_low:
            return False, f"Missing required verified token: {tok!r}"

    # 2. ScreenerAgent must return actual screened symbols & ISINs, not just strategy label
    if agent_name == "ScreenerAgent":
        if "isin" not in out_low or "pass" not in out_low or "|" not in output:
            return False, "Screener output missing auditable table / ISIN / timestamps"

    # 3. AnalystAgent must resolve ticker & currency and never fail with 'No specific tickers'
    if agent_name == "AnalystAgent":
        if "no specific tickers" in out_low or "unable to fetch" in out_low:
            return False, "Analyst failed to resolve ticker"
        if "isin" not in out_low or "ind as" not in out_low:
            return False, "Analyst output missing ISIN / Ind AS provenance"

    # 4. Code agents must pass AST parsing
    if is_code_agent or agent_name in ("AarkaCoderPipeline", "CoderAgent", "CodingAgent"):
        blocks = re.findall(r"```(?:python)?\s*(.*?)\s*```", output, re.DOTALL)
        code_to_check = blocks[0] if blocks else (output if agent_name == "AarkaCoderPipeline" else "")
        if code_to_check:
            try:
                ast.parse(code_to_check)
            except SyntaxError as exc:
                return False, f"AST SyntaxError: {exc}"

    return True, "VERIFIED"
