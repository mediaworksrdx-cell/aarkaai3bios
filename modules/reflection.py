"""
AARKAAI – Verification self-reflection loop
Provides execution feedback and triggers replanning checkpoints.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List

from modules import aarkaa_engine

logger = logging.getLogger(__name__)

def check_evidence_replanning(plan: Dict[str, Any], scratchpad: Dict[str, Any]) -> bool:
    """Analyze scratchpad to determine if new findings contradict current DAG assumptions."""
    facts_str = "\n".join(scratchpad.get("facts", []))
    
    # Prompt the model to evaluate if plan requires restructuring
    prompt = (
        "You are AARKAAI Supervisor. Given the original plan and the current completed steps, "
        "determine if we need to modify or append new tasks to satisfy the user request.\n\n"
        f"Original Plan Goals: {plan.get('goal')}\n"
        f"Completed Steps:\n{facts_str}\n\n"
        "If yes (we need to replan), output 'YES'. If no (current plan is fine), output 'NO'.\n"
        "Output ONLY 'YES' or 'NO'."
    )
    
    try:
        response = aarkaa_engine.generate_raw(prompt, max_new_tokens=10).strip().upper()
        logger.info("Self-reflection result: %s", response)
        return "YES" in response
    except Exception as exc:
        logger.error("Self-reflection validation failed: %s", exc)
        return False
