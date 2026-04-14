"""
AARKAAI - AARKAA-3B Core Engine (llama.cpp / GGUF)

High-performance CPU inference using llama-cpp-python.
Falls back to a stub when the GGUF model is not present.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from config import MODEL_PATH

logger = logging.getLogger(__name__)

_model = None
_is_stub = True

_GGUF_CANDIDATES = [
    Path(MODEL_PATH).parent / "aarkaa-3b-q8.gguf",
    Path(MODEL_PATH).parent / "aarkaa-3b-f16.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-q8.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-f16.gguf",
]


def init():
    """Load the AARKAA-3B GGUF model if available."""
    global _model, _is_stub

    gguf_file = None
    for candidate in _GGUF_CANDIDATES:
        if candidate.exists():
            gguf_file = candidate
            break

    if gguf_file is None:
        logger.warning("GGUF model not found - running in STUB mode.")
        _is_stub = True
        return

    try:
        from llama_cpp import Llama

        # Use physical cores, not logical vCPUs, for optimal CPU inference speed
        logical_cores = os.cpu_count() or 8
        n_threads = max(1, logical_cores // 2)

        logger.info("Loading AARKAA-3B from %s (threads=%d)", gguf_file, n_threads)

        _model = Llama(
            model_path=str(gguf_file),
            n_ctx=4096,
            n_threads=n_threads,
            n_threads_batch=n_threads,
            n_gpu_layers=0,
            verbose=False,
        )
        _is_stub = False
        logger.info("AARKAA-3B loaded (llama.cpp, GGUF, %d threads).", n_threads)
    except Exception as exc:
        logger.error("Failed to load AARKAA-3B: %s - falling back to stub", exc)
        _is_stub = True


def _generate(prompt, max_new_tokens=150, stop=None):
    """Run generation via llama.cpp."""
    if _is_stub or _model is None:
        return _stub_response(prompt)
    
    stop_tokens = ["\nContext:", "\nQuestion:", "Context:", "Question:"]
    if stop:
        stop_tokens.extend(stop)

    output = _model(
        prompt,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=stop_tokens
    )
    text = output["choices"][0]["text"].strip()
    return _clean_response(text)


def _generate_stream(prompt, max_new_tokens=250, stop=None):
    """Run generation via llama.cpp and yield tokens."""
    if _is_stub or _model is None:
        yield _stub_response(prompt)
        return

    stop_tokens = ["\nContext:", "\nQuestion:", "Context:", "Question:", "User:", "AARKAA:"]
    if stop:
        stop_tokens.extend(stop)

    stream = _model(
        prompt,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=stop_tokens,
        stream=True
    )
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            yield token


def generate_raw(prompt, max_new_tokens=500, stop=None):
    """Raw generation for the agent loop (no truncation)."""
    if _is_stub or _model is None:
        return 'Final Answer: I am running in stub mode.'
    
    if stop is None:
        stop = []

    output = _model(
        prompt,
        max_tokens=max_new_tokens,
        temperature=0.2,
        top_p=0.9,
        stop=stop,
        repeat_penalty=1.1,
    )
    return output["choices"][0]["text"].strip()


def _clean_response(text):
    """Truncate at the last complete sentence to avoid unfinished answers."""
    if not text:
        return text
    for end_char in [". ", "! ", "? "]:
        last_pos = text.rfind(end_char)
        if last_pos > len(text) * 0.5:
            return text[:last_pos + 1]
    if text[-1] in ".!?":
        return text
    return text + "."


def _stub_response(query, context=""):
    """Placeholder response when model is unavailable."""
    if context:
        return (
            "[AARKAA-3B Stub] Based on the retrieved context, "
            "here is a synthesized answer to your question "
            '"' + query + '":\n\n'
            "Context summary: " + context[:500] + "\n\n"
            "Note: This is a placeholder response."
        )
    return (
        '[AARKAA-3B Stub] I received your query: "' + query + '". '
        "The full AARKAA-3B model is not loaded; this is a placeholder response."
    )


def primary_check(query):
    """Quick first-pass answer. Returns (response, confidence)."""
    if _is_stub:
        return _stub_response(query), 0.3

    try:
        is_code = any(
            w in query.lower()
            for w in ["code", "program", "function", "script", "write", "implement", "create a"]
        )
        if is_code:
            prompt = (
                "You are AARKAA, an expert programming AI assistant. "
                "Respond in the same language the user writes in. "
                "Provide working code with a brief explanation.\n\n"
                "Request: " + query + "\n\nCode and Explanation:"
            )
            tokens = 500
        else:
            prompt = (
                "You are AARKAA, a helpful and precise multilingual AI assistant. "
                "Always respond in the same language the user uses. "
                "Answer the following question concisely:\n\n"
                + query + "\n\nAnswer:"
            )
            tokens = 100
        response = _generate(prompt, max_new_tokens=tokens)
        confidence = min(0.9, 0.5 + len(response.split()) / 200)
        return response, confidence
    except Exception as exc:
        logger.error("primary_check failed: %s", exc)
        return _stub_response(query), 0.3


def final_response(query, context, intent=""):
    """Full reasoning pass with fused context from external modules."""
    if _is_stub:
        return _stub_response(query, context)

    try:
        prompt, tokens = _build_final_prompt(query, context, intent)
        return _generate(prompt, max_new_tokens=tokens)
    except Exception as exc:
        logger.error("final_response failed: %s", exc)
        return _stub_response(query, context)


def stream_final_response(query, context, intent=""):
    """Stream tokens for the final response pass."""
    if _is_stub:
        yield _stub_response(query, context)
        return

    try:
        prompt, tokens = _build_final_prompt(query, context, intent)
        yield from _generate_stream(prompt, max_new_tokens=tokens)
    except Exception as exc:
        logger.error("stream_final_response failed: %s", exc)
        yield _stub_response(query, context)


def _build_final_prompt(query, context, intent=""):
    is_code = intent == "coding_help" or any(
        w in query.lower()
        for w in ["code", "program", "function", "script", "write", "implement"]
    )
    if is_code:
        prompt = (
            "You are AARKAA, an expert programming AI assistant. "
            "Respond in the same language the user writes in. "
            "Provide working code with a clear explanation.\n\n"
        )
        if context:
            prompt += "Context:\n" + context + "\n\n"
        prompt += "Request: " + query + "\n\nCode and Explanation:"
        tokens = 500
    else:
        prompt = (
            "You are AARKAA, a highly intelligent multilingual AI assistant. "
            "Always respond in the same language the user uses. "
            "Use the following context to provide a comprehensive answer.\n\n"
        )
        if context:
            prompt += "Context:\n" + context + "\n\n"
        prompt += "Question: " + query + "\n\nDetailed Answer:"
        tokens = 250
    return prompt, tokens


def is_available():
    """Whether the real model is loaded."""
    return not _is_stub
