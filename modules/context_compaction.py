"""
AARKAAI - Context Compaction Module (v2)

Token-budget-aware 5-layer compaction pipeline with structured
checkpoint emission and configurable generation reserve.

Layers:
  1. ANSI escape / progress bar cleanup
  2. Source buffer middle-truncation
  3. Semantic line deduplication
  4. Conditional LLM-driven summarization with structured checkpoint
  5. Turn-aware sliding window truncation (ReAct + ChatML formats)
"""
import re
import logging
from typing import List, Dict, Tuple, Optional, Any

from config import (
    COMPACTION_ENABLED,
    COMPACTION_TRIGGER_RATIO,
    COMPACTION_PRESERVE_TURNS,
    RESERVED_OUTPUT_TOKENS,
    MODEL_CONTEXT_WINDOW,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dynamic feature flag check
# ---------------------------------------------------------------------------

def is_compaction_enabled() -> bool:
    """Check if compaction is enabled, prioritizing runtime AARKAAI_COMPACTION_ENABLED env var."""
    import os
    env_val = os.getenv("AARKAAI_COMPACTION_ENABLED")
    if env_val is not None:
        return env_val.lower() == "true"
    import config
    return getattr(config, "COMPACTION_ENABLED", True)

# ---------------------------------------------------------------------------
# Token budget helpers
# ---------------------------------------------------------------------------


def _compute_usable_budget(context_window: int = MODEL_CONTEXT_WINDOW,
                           reserved_output: int = RESERVED_OUTPUT_TOKENS) -> int:
    """Compute usable prompt token budget after reserving output headroom."""
    return max(1024, context_window - reserved_output)


def _compute_trigger_threshold(usable_budget: int,
                               ratio: float = COMPACTION_TRIGGER_RATIO) -> int:
    """Token count at which compaction activates."""
    return int(usable_budget * ratio)


def _tokenize_len(text: str, model_instance: Any) -> int:
    """Return exact token count using the model tokenizer, or character
    estimate (chars / 3.5) when the model instance is unavailable."""
    if model_instance is None:
        return int(len(text) / 3.5)
    try:
        tokens = model_instance.tokenize(text.encode("utf-8"), special=True)
        return len(tokens)
    except Exception:
        return int(len(text) / 3.5)


def _token_slice(text: str, max_tokens: int, model_instance: Any) -> str:
    """Slice text to approximately max_tokens using the tokenizer.
    Falls back to character-ratio estimate when tokenizer is unavailable."""
    if model_instance is None:
        max_chars = int(max_tokens * 3.5)
        return text[:max_chars]
    try:
        tokens = model_instance.tokenize(text.encode("utf-8"), special=True)
        if len(tokens) <= max_tokens:
            return text
        sliced = tokens[:max_tokens]
        return model_instance.detokenize(sliced).decode("utf-8", errors="replace")
    except Exception:
        max_chars = int(max_tokens * 3.5)
        return text[:max_chars]


# ---------------------------------------------------------------------------
# Layer 1: ANSI escape / progress bar cleanup
# ---------------------------------------------------------------------------

def clean_ansi_escapes(text: str) -> str:
    """Layer 1: Clean up ANSI escape sequences and terminal formatting."""
    ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    # Remove progress bars e.g. [========>] or similar
    text = re.sub(r'\[[=#->\s]+\]\s*\d+%', '', text)
    return text


# ---------------------------------------------------------------------------
# Layer 2: Source buffer middle-truncation
# ---------------------------------------------------------------------------

def truncate_source_code_buffers(text: str, max_lines: int = 100) -> str:
    """Layer 2: Truncate intermediate long file reads or outputs in the middle."""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text

    keep = max_lines // 2
    first_part = lines[:keep]
    last_part = lines[-keep:]

    truncated_msg = f"\n... [Truncated {len(lines) - max_lines} lines of verbose output/code] ...\n"
    return "\n".join(first_part) + truncated_msg + "\n".join(last_part)


# ---------------------------------------------------------------------------
# Layer 3: Semantic line deduplication
# ---------------------------------------------------------------------------

def semantic_deduplicate(text: str) -> str:
    """Layer 3: Prune identical or extremely similar adjacent log lines."""
    lines = text.splitlines()
    if not lines:
        return text

    deduped: list[str] = []
    prev_line: Optional[str] = None
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            deduped.append(line)
            continue
        # Deduplicate exact consecutive duplicates
        if prev_line == cleaned:
            continue
        deduped.append(line)
        prev_line = cleaned

    return "\n".join(deduped)


# ---------------------------------------------------------------------------
# Layer 4: Conditional LLM-driven summarization with structured checkpoint
# ---------------------------------------------------------------------------

def _extract_checkpoint_fields(context_text: str) -> Dict[str, str]:
    """Best-effort extraction of goal, modified files, decisions, and state
    from the context block. Returns only fields that can be validated as
    actually present in the text - does not fabricate or assume."""
    fields: Dict[str, str] = {}

    # Extract file paths (validated: must contain path separators or extensions)
    file_pattern = re.compile(
        r'(?:["\']|\b)([\w./\\-]+\.(?:py|js|ts|go|rs|java|yaml|yml|json|toml|md|txt|html|css|sh|sql))(?:["\']|\b)',
        re.IGNORECASE
    )
    file_matches = list(set(file_pattern.findall(context_text)))
    if file_matches:
        fields["Modified Files"] = ", ".join(sorted(file_matches[:10]))

    # Extract error indicators (validated: actual error strings present)
    error_lines = []
    for line in context_text.splitlines():
        stripped = line.strip()
        if any(marker in stripped.lower() for marker in [
            "error:", "traceback", "exception", "failed", "errno",
            "syntaxerror", "typeerror", "valueerror", "importerror",
        ]):
            error_lines.append(stripped[:150])
    if error_lines:
        fields["Errors Encountered"] = "; ".join(error_lines[:5])

    return fields


def _format_checkpoint(summary: str, fields: Dict[str, str]) -> str:
    """Format a structured checkpoint block from LLM summary and extracted fields."""
    lines = ["[SESSION CHECKPOINT \u2014 Auto-Compacted]"]
    for key, value in fields.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- Summary: {summary.strip()[:2000]}")
    return "\n".join(lines)


def cond_llm_summarize(prompt_str: str, current_tokens: int,
                       trigger_threshold: int, model_instance: Any,
                       usable_budget: int) -> str:
    """Layer 4: Conditional LLM-Driven Summarization of historical turns.

    Summarizes the context block and emits a structured [SESSION CHECKPOINT]
    containing only validated, actually-present fields.
    """
    if current_tokens <= trigger_threshold or model_instance is None:
        return prompt_str

    logger.info(
        "Context exceeds trigger threshold (%d > %d). Running Layer 4 LLM Summarization.",
        current_tokens, trigger_threshold
    )

    # Locate context block
    ctx_idx = prompt_str.find("Context:\n")
    if ctx_idx == -1:
        return prompt_str

    header = prompt_str[:ctx_idx + 9]
    rest = prompt_str[ctx_idx + 9:]

    # Token-aware slicing: use 60% of usable budget for summarization input
    summarization_input = _token_slice(rest, int(usable_budget * 0.6), model_instance)

    # Extract validated checkpoint fields BEFORE summarization
    checkpoint_fields = _extract_checkpoint_fields(summarization_input)

    from modules.aarkaa_engine import generate_raw
    summarization_prompt = (
        "Summarize the following tool execution context and command outputs into a dense, "
        "extremely concise factual summary highlighting the outcomes of each step. "
        "Preserve all errors, file paths, and key facts. Do not invent information "
        "not present in the input:\n\n" + summarization_input
    )

    try:
        summary = generate_raw(summarization_prompt, max_new_tokens=512)
        checkpoint = _format_checkpoint(summary, checkpoint_fields)
        return header + checkpoint
    except Exception as e:
        logger.error("Failed to run Layer 4 Summarization: %s", e)
        return prompt_str


# ---------------------------------------------------------------------------
# Layer 5: Turn-aware sliding window truncation
# ---------------------------------------------------------------------------

_REACT_TURN_PATTERN = re.compile(r'\nThought: ', re.IGNORECASE)
_CHATML_TURN_PATTERN = re.compile(r'<\|im_start\|>(?:user|assistant)\n')


def _detect_turn_format(text: str) -> str:
    """Detect whether the text uses ReAct or ChatML turn format."""
    react_count = len(_REACT_TURN_PATTERN.findall(text))
    chatml_count = len(_CHATML_TURN_PATTERN.findall(text))
    return "react" if react_count >= chatml_count else "chatml"


def _sliding_window_truncate(text: str, preserve_turns: int = COMPACTION_PRESERVE_TURNS) -> str:
    """Layer 5: Turn-aware sliding window truncation.

    Detects whether the text uses ReAct (Thought/Action) or ChatML
    (<|im_start|>) format and drops oldest turns while preserving
    the system preamble and the most recent N turns.
    """
    fmt = _detect_turn_format(text)

    if fmt == "react":
        parts = _REACT_TURN_PATTERN.split(text)
    else:
        parts = _CHATML_TURN_PATTERN.split(text)

    if len(parts) <= preserve_turns + 1:
        return text

    system_part = parts[0]
    preserved = parts[-preserve_turns:]

    sep = "\nThought: " if fmt == "react" else "<|im_start|>assistant\n"
    return (
        system_part
        + "\n\n...[older execution steps truncated for length]...\n\n"
        + sep.join(preserved)
    )


# ---------------------------------------------------------------------------
# Chat history compaction (for _build_chatml_multi)
# ---------------------------------------------------------------------------

def compact_history(
    history: List[Dict[str, str]],
    token_budget: int,
    model_instance: Any,
    preserve_turns: int = COMPACTION_PRESERVE_TURNS
) -> List[Dict[str, str]]:
    """Token-aware chat history compaction.

    Operates on a list of {"role": ..., "message"/"content": ...} dicts.
    Drops oldest turns first while preserving the most recent
    `preserve_turns` exchanges. Uses the tokenizer for exact token counts.

    Args:
        history: Chronological list of conversation messages.
        token_budget: Maximum total tokens for the history block.
        model_instance: llama-cpp model instance for tokenization.
        preserve_turns: Minimum number of recent turns to always keep.

    Returns:
        Compacted history list, chronological order, within budget.
    """
    if not history:
        return []

    # Always preserve the most recent turns unconditionally
    guaranteed = history[-preserve_turns:] if len(history) > preserve_turns else history[:]
    candidate_pool = history[:-preserve_turns] if len(history) > preserve_turns else []

    # Calculate token cost of guaranteed turns
    guaranteed_tokens = 0
    for msg in guaranteed:
        content = msg.get("message") or msg.get("content", "")
        guaranteed_tokens += _tokenize_len(content, model_instance)

    if guaranteed_tokens >= token_budget:
        # Even the guaranteed turns exceed budget - truncate individual messages
        per_turn_budget = max(100, token_budget // max(len(guaranteed), 1))
        compacted = []
        for msg in guaranteed:
            content = msg.get("message") or msg.get("content", "")
            sliced = _token_slice(content, per_turn_budget, model_instance)
            entry = dict(msg)
            if "message" in entry:
                entry["message"] = sliced
            else:
                entry["content"] = sliced
            compacted.append(entry)
        return compacted

    remaining_budget = token_budget - guaranteed_tokens

    # Add older turns from most recent to oldest until budget exhausted
    included_older: list[Dict[str, str]] = []
    for msg in reversed(candidate_pool):
        content = msg.get("message") or msg.get("content", "")
        msg_tokens = _tokenize_len(content, model_instance)
        if msg_tokens <= remaining_budget:
            included_older.append(msg)
            remaining_budget -= msg_tokens
        else:
            break

    # Restore chronological order
    included_older.reverse()
    return included_older + guaranteed


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def compact_prompt(
    prompt_str: str,
    model_instance: Any,
    prompt_token_budget: int = 0,
    max_tokens: int = 12000  # Legacy parameter - used as fallback
) -> str:
    """Run the complete 5-Layer Context Compaction pipeline.

    Args:
        prompt_str: Full prompt string to compact.
        model_instance: llama-cpp model instance (or None for stub mode).
        prompt_token_budget: Explicit usable prompt token budget.
            If 0, computed from MODEL_CONTEXT_WINDOW - RESERVED_OUTPUT_TOKENS.
        max_tokens: Legacy parameter for backward compatibility.
            Used only when prompt_token_budget is 0 and COMPACTION_ENABLED is False.
    """
    if not is_compaction_enabled():
        # Rollback path: use safe token-aware fallback, NOT old character-based truncation.
        # This still applies Layers 1-3 (cheap text cleanup) and Layer 5 (turn truncation)
        # but skips the LLM summarization in Layer 4.
        cleaned = clean_ansi_escapes(prompt_str)
        cleaned = truncate_source_code_buffers(cleaned, max_lines=120)
        cleaned = semantic_deduplicate(cleaned)
        budget = prompt_token_budget or _compute_usable_budget()
        token_len = _tokenize_len(cleaned, model_instance)
        if token_len > budget:
            cleaned = _sliding_window_truncate(cleaned)
        return cleaned

    # Compute budget
    usable_budget = prompt_token_budget if prompt_token_budget > 0 else _compute_usable_budget()
    trigger_threshold = _compute_trigger_threshold(usable_budget)

    # Layer 1 & Layer 2: Pre-process prompt content
    cleaned = clean_ansi_escapes(prompt_str)
    cleaned = truncate_source_code_buffers(cleaned, max_lines=120)
    cleaned = semantic_deduplicate(cleaned)

    # Compute token count
    token_len = _tokenize_len(cleaned, model_instance)

    # Layer 4: Conditional LLM-driven summarization with structured checkpoint
    if token_len > trigger_threshold:
        cleaned = cond_llm_summarize(
            cleaned, token_len, trigger_threshold,
            model_instance, usable_budget
        )
        token_len = _tokenize_len(cleaned, model_instance)

    # Layer 5: Turn-aware sliding window truncation (fallback)
    if token_len > usable_budget:
        logger.info(
            "Applying Layer 5 sliding window truncation (tokens=%d > budget=%d).",
            token_len, usable_budget
        )
        cleaned = _sliding_window_truncate(cleaned)

    return cleaned
