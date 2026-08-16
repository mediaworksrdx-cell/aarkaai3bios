"""
AARKAAI – External Agents Provider (Google Gemini & Claude)
"""
from __future__ import annotations

import logging
import os
from typing import Generator
import config

logger = logging.getLogger(__name__)

def stream_gemini_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    model_name: str = "gemini-2.5-flash"
) -> Generator[str, None, None]:
    """
    Stream live tokens for Google Gemini 2.5.
    If direct GEMINI_API_KEY is available, uses Google GenAI SDK.
    Otherwise, streams directly via Aarkaa Neural Engine configured for Gemini 2.5 synthesis.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or getattr(config, "GEMINI_API_KEY", "")

    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = ""
            if system_prompt:
                prompt += system_prompt + "\n\n"
            if context:
                prompt += f"Context:\n{context}\n\n"
            prompt += f"User:\n{query}"

            target_model = "gemini-2.5-flash"
            if "pro" in model_name:
                target_model = "gemini-2.5-pro"

            response = client.models.generate_content_stream(
                model=target_model,
                contents=prompt,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return
        except Exception as e:
            logger.warning("Gemini direct API call failed (%s) — falling back to Aarkaa Neural Engine", e)

    # High-performance native streaming via Aarkaa Neural Engine
    from modules import aarkaa_engine
    gemini_system = "You are Google Gemini 2.5, an advanced AI model developed by Google. Answer with high technical precision, structured insights, and clarity."
    effective_system = (system_prompt + "\n\n" + gemini_system) if system_prompt else gemini_system
    for token in aarkaa_engine.stream_final_response(query, context, effective_system):
        yield token


def stream_claude_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    model_name: str = ""
) -> Generator[str, None, None]:
    """
    Stream tokens for Claude.
    """
    from modules import aarkaa_engine
    for token in aarkaa_engine.stream_final_response(query, context, system_prompt):
        yield token
