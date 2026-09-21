"""
AARKAAI Pipeline – Shared Context Result

Dataclass used by both sync and streaming pipeline paths to carry
context-gathering results without duplicating field definitions.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextResult:
    """Shared state container for pipeline context-gathering results.

    Both ``process_query`` and ``stream_query`` populate instances of this
    class during context gathering.  Having a single definition here
    eliminates the risk of the two paths drifting out of sync.
    """

    query: str
    clean_query: str
    detected_lang: str
    domain: str
    intent: str
    filter_confidence: float
    filter_result: dict
    is_greeting: bool
    is_reasoning: bool
    skill_name: Optional[str]
    skill_content: Optional[str]
    context_parts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    chat_ctx: Optional[list] = None
    fused_context: str = ""
    user_facts: str = ""
    is_followup_query: bool = False
    fu_score: float = 0.0
    has_finance_context: bool = False
    is_fin_intent: bool = False
    fin_tickers: list[str] = field(default_factory=list)
    is_knowledge: bool = False
    is_coding_output: bool = False
    screener_direct_report: Optional[str] = None
    needs_agent: bool = False
    has_mutating_action_intent: bool = False
    is_strategy_query: bool = False
    finance_strategy_req: Optional[dict] = None
    needs_web: bool = False
    is_coding_query: bool = False

    # TODO: Full gather_context() extraction in next refactor phase.
    # Currently both sync.py and streaming.py inline the context-gathering
    # logic.  A future step will extract the shared ~400-line block into
    # a _gather_context() function here.
