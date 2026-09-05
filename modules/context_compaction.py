"""
AARKAAI – Context Compaction Module
Implements the 5-Layer Context Compaction Pipeline from Claude Code's architecture.
"""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def clean_ansi_escapes(text: str) -> str:
    """Layer 1: Clean up ANSI escape sequences and terminal formatting."""
    ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    # Remove progress bars e.g. [========>] or similar
    text = re.sub(r'\[[=#->\s]+\]\s*\d+%', '', text)
    return text

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

def semantic_deduplicate(text: str) -> str:
    """Layer 3: Prune identical or extremely similar adjacent log lines."""
    lines = text.splitlines()
    if not lines:
        return text
    
    deduped = []
    prev_line = None
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

def cond_llm_summarize(prompt_str: str, current_tokens: int, threshold_tokens: int, model_instance) -> str:
    """Layer 4: Conditional LLM-Driven Summarization of historical turns."""
    if current_tokens <= threshold_tokens or model_instance is None:
        return prompt_str
    
    logger.info("Context exceeds threshold (%d > %d). Running Layer 4 LLM Summarization.", current_tokens, threshold_tokens)
    
    # We want to identify the "Context" or historical tool executions section.
    # Locate context block
    ctx_idx = prompt_str.find("Context:\n")
    if ctx_idx == -1:
        return prompt_str
        
    header = prompt_str[:ctx_idx + 9]
    rest = prompt_str[ctx_idx + 9:]
    
    # We ask the local model to summarize the history
    from modules.aarkaa_engine import generate_raw
    summarization_prompt = (
        "Summarize the following tool execution context and command outputs into a dense, "
        "extremely concise factual summary highlighting the outcomes of each step. Do not lose "
        "errors, file paths, or key facts:\n\n" + rest[:8000]
    )
    
    try:
        summary = generate_raw(summarization_prompt, max_new_tokens=512)
        return header + summary
    except Exception as e:
        logger.error("Failed to run Layer 4 Summarization: %s", e)
        return prompt_str

def compact_prompt(prompt_str: str, model_instance, max_tokens: int = 12000) -> str:
    """Run the complete 5-Layer Context Compaction pipeline."""
    # Layer 1 & Layer 2: Pre-process prompt content
    # We will clean and truncate parts of the prompt string that represent large tool logs or files
    cleaned = clean_ansi_escapes(prompt_str)
    cleaned = truncate_source_code_buffers(cleaned, max_lines=120)
    cleaned = semantic_deduplicate(cleaned)
    
    if model_instance is None:
        return cleaned
        
    # Layer 3 & Layer 4: Compute token counts and conditionally run LLM summaries
    tokens = model_instance.tokenize(cleaned.encode("utf-8"), special=True)
    token_len = len(tokens)
    
    # Layer 4 threshold set to 75% of max_tokens
    threshold = int(max_tokens * 0.75)
    if token_len > threshold:
        cleaned = cond_llm_summarize(cleaned, token_len, threshold, model_instance)
        # Recalculate length
        tokens = model_instance.tokenize(cleaned.encode("utf-8"), special=True)
        token_len = len(tokens)
        
    # Layer 5: Sliding Window Truncation (Fallback)
    if token_len > max_tokens:
        logger.info("Applying Layer 5 sliding window truncation.")
        # Find where historical thought/action loops start and prune the oldest
        parts = cleaned.split("\nThought: ")
        if len(parts) > 3:
            system_part = parts[0]
            last_turns = parts[-2:]
            cleaned = system_part + "\n\n...[older execution steps truncated for length]...\n\n" + "\nThought: ".join(last_turns)
            
    return cleaned
