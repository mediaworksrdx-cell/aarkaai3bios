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

from config import MODEL_PATH, MAX_TOKENS

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

        logical_cores = os.cpu_count() or 2
        n_threads = logical_cores if logical_cores <= 4 else logical_cores // 2

        logger.info("Loading AARKAA-3B from %s (threads=%d)", gguf_file, n_threads)

        _model = Llama(
            model_path=str(gguf_file),
            n_ctx=8192,
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
    
    stop_tokens = ["\nContext:", "\nQuestion:", "Context:", "Question:", "User:", "AARKAA:", "\nUser:", "\nAARKAA:"]
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


def _generate_stream(prompt, max_new_tokens=150, stop=None):
    """Run generation via llama.cpp and yield tokens."""
    if _is_stub or _model is None:
        yield _stub_response(prompt)
        return

    stop_tokens = ["\nContext:", "\nQuestion:", "Context:", "Question:", "User:", "AARKAA:", "\nUser:", "\nAARKAA:", "[User Input]", "\n[User Input]"]
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


def generate_raw(prompt, max_new_tokens=300, stop=None):
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
    
    # Strip out hallucinated markers
    text = text.replace("[end of web search results]", "").strip()
    text = text.replace("[End of web search results]", "").strip()

    # Do not truncate if text contains code blocks to avoid corrupting code syntax.
    if "```" in text:
        # If the code block is unclosed, close it cleanly
        if text.count("```") % 2 != 0:
            return text + "\n```"
        return text
        
    # If it naturally ends in a punctuation mark (and isn't a dangling list number like "5."), leave it alone!
    if text[-1] in ".!?" and not (text[-1] == "." and len(text) > 1 and text[-2].isdigit()):
        return text

    # Otherwise, it might be an unfinished sentence. Find the last complete sentence.
    for end_char in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
        last_pos = text.rfind(end_char)
        if last_pos > len(text) * 0.5:
            return text[:last_pos + 1]
            
    return text + "."


def _stub_response(query, context=""):
    """Placeholder response when model is unavailable."""
    if context:
        # Prioritize finance data over stale conversation history
        summary = ""
        if "[Finance Data]" in context:
            # Extract the finance section specifically
            fin_start = context.index("[Finance Data]")
            fin_end = context.find("\n\n---\n\n", fin_start)
            finance_section = context[fin_start:fin_end] if fin_end > 0 else context[fin_start:]
            summary = finance_section
        else:
            summary = context[:1500]

        return (
            "Based on the latest real-time data:\n\n"
            + summary + "\n\n"
            "Would you like to know more about any specific asset?"
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
            tokens = MAX_TOKENS
        else:
            prompt = (
                "You are AARKAA, a helpful and precise multilingual AI assistant. "
                "Always respond in the same language the user uses. "
                "Answer the following question concisely:\n\n"
                + query + "\n\nAnswer:"
            )
            tokens = MAX_TOKENS
        response = _generate(prompt, max_new_tokens=tokens)
        confidence = min(0.9, 0.5 + len(response.split()) / 150)
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
    is_continue = query.lower().strip() in ["continue", "next phase", "continue code", "continue the code", "go on"]
    if is_continue:
        prompt = (
            "You are AARKAA, a highly intelligent programming and multilingual AI assistant.\n"
            "The previous response was cut off due to token limits. Complete the previous response starting from exactly where it was truncated.\n\n"
        )
        if context:
            prompt += "Context:\n" + context + "\n\n"
        prompt += "Continuation of AARKAA's previous response:"
        tokens = MAX_TOKENS
        return prompt, tokens

    is_code = intent == "coding_help" or any(
        w in query.lower()
        for w in ["code", "program", "function", "script", "write", "implement"]
    )
    if is_code:
        prompt = (
            "You are AARKAA, an expert programming AI assistant. "
            "You have the ability to execute code and bash commands if the user asks you to 'run' or 'execute' them. "
            "Respond in the same language the user writes in. "
            "Provide working code with a clear explanation.\n\n"
        )
        if context:
            prompt += "Context:\n" + context + "\n\n"
        prompt += "Request: " + query + "\n\nCode and Explanation:"
        tokens = MAX_TOKENS
    else:
        is_chat_or_greeting = any(
            w in query.lower()
            for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you"]
        )
        if is_chat_or_greeting:
            prompt = (
                "You are AARKAA, a highly intelligent, warm and friendly multilingual AI assistant.\n"
                "Respond naturally and warmly to the user.\n\n"
            )
            if context:
                prompt += "Context:\n" + context + "\n\n"
            prompt += "User: " + query + "\n\nAARKAA:"
        else:
            # Detect self-referential questions about AarkAI itself
            _self_keywords = [
                "security feature", "built-in", "your feature", "your capabilit",
                "what can you", "about yourself", "about aark", "about you",
                "how do you work", "your architecture", "what are you",
                "your security", "are you safe", "how are you built",
                "aarka ai capabilit", "aarkaa capabilit", "explain aarka",
                "who are you"
            ]
            is_self_question = any(kw in query.lower() for kw in _self_keywords)

            AARKAA_IDENTITY = (
                "You are AARKAA (Autonomous Adaptive Reasoning Kernel for Augmented AI), "
                "a production-grade AI assistant built by Synthetix Analytics. "
                "You have advanced capabilities including real-time web search, code execution in a sandboxed environment, "
                "and multilingual support.\n\n"
                "Your built-in security features include:\n"
                "- API Key authentication for all endpoints\n"
                "- Per-IP rate limiting to prevent abuse\n"
                "- Sandboxed code execution (commands run in an isolated workspace with a blocklist of dangerous operations)\n"
                "- Command timeout enforcement to prevent infinite loops\n"
                "- CORS origin whitelisting\n"
                "- Request tracking and logging with unique request IDs\n"
                "- Circuit breakers on external services (web search, finance API) to gracefully handle failures\n"
                "- Input sanitization and prompt injection guards\n\n"
                "Your key capabilities:\n"
                "- Multilingual responses (auto-detects user language)\n"
                "- Real-time web search via DuckDuckGo and Wikipedia\n"
                "- Code writing, testing, and execution via BashTool\n"
                "- File read/write operations in a sandboxed workspace\n"
                "- RAG (Retrieval-Augmented Generation) from a local knowledge base\n"
                "- Conversation memory and context continuity\n"
                "- Finance/market data retrieval\n"
                "- Autonomous agent mode with ReAct reasoning loop\n\n"
                "Always respond in the same language the user uses.\n\n"
            )

            if is_self_question:
                prompt = AARKAA_IDENTITY
                # Deliberately skip conversation context for self-questions
                # to prevent the model from anchoring on previous unrelated topics
                prompt += "The user is asking about YOU (AARKAA) and YOUR platform's features. Answer based on the system description above, NOT based on any previous code or conversation.\n\n"
                prompt += "Question: " + query + "\n\nAnswer:"
                tokens = MAX_TOKENS
            else:
                prompt = (
                    "You are AARKAA, a highly intelligent multilingual AI assistant. "
                    "You have advanced capabilities including real-time web search and the ability to execute code if asked to 'run' or 'execute' it. "
                    "Always respond in the same language the user uses.\n\n"
                )
                if context:
                    has_finance = "[Finance Data]" in context
                    if has_finance:
                        prompt += (
                            "IMPORTANT: The context below contains LIVE, REAL-TIME financial data fetched just now from Yahoo Finance. "
                            "You MUST use the exact prices, values, and percentages from the [Finance Data] section. "
                            "Do NOT use any prices from your training data or prior knowledge — they are outdated.\n\n"
                        )
                    prompt += (
                        "Context information:\n"
                        "---------------------\n"
                        + context + "\n"
                        "---------------------\n"
                        "Answer the question using ONLY the context above. "
                        "If the context contains specific numbers, prices, or data, use those exact values.\n\n"
                    )
                prompt += "Question: " + query + "\n\nAnswer:"
                tokens = MAX_TOKENS
    return prompt, tokens


def is_available():
    """Whether the real model is loaded."""
    return not _is_stub
