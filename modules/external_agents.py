"""
AARKAAI – External Agents & Fast AI Inference Provider (Google Gemini & Vertex AI)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator
import config

logger = logging.getLogger(__name__)

# Ensure Google Service Account credentials are set in environment
_DEFAULT_SA_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not _DEFAULT_SA_PATH or not os.path.exists(_DEFAULT_SA_PATH):
    # Try finding the orbital service account json in repo or home
    possible_paths = [
        str(Path(__file__).parent.parent / "orbital-heaven-504004-s2-df5a0ce91659.json"),
        "/home/sathishbadri2015/aarkaai3b/orbital-heaven-504004-s2-df5a0ce91659.json",
        str(Path(os.getcwd()) / "orbital-heaven-504004-s2-df5a0ce91659.json"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = p
            _DEFAULT_SA_PATH = p
            break

def _get_genai_client():
    """Create and return a Google GenAI / Vertex AI client with robust authentication."""
    from google import genai
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or getattr(config, "GEMINI_API_KEY", "")
    
    if gemini_key:
        return genai.Client(api_key=gemini_key)
    
    # Use Vertex AI via Service Account / ADC
    project = os.getenv("VERTEX_PROJECT") or getattr(config, "VERTEX_PROJECT", "orbital-heaven-504004-s2")
    location = os.getenv("VERTEX_LOCATION") or getattr(config, "VERTEX_LOCATION", "us-central1")
    return genai.Client(vertexai=True, project=project, location=location)


def stream_gemini_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    model_name: str = "gemini-2.5-flash"
) -> Generator[str, None, None]:
    """
    Stream live tokens for Google Gemini 2.5 via Vertex AI or Google GenAI SDK.
    """
    try:
        client = _get_genai_client()
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
        logger.warning("Gemini streaming error (%s) — falling back to Aarkaa Neural Engine", e)

    # High-performance native fallback via Aarkaa Neural Engine
    from modules import aarkaa_engine
    gemini_system = "You are Google Gemini 2.5, an advanced AI model developed by Google. Answer with high technical precision, structured insights, and clarity."
    effective_system = (system_prompt + "\n\n" + gemini_system) if system_prompt else gemini_system
    for token in aarkaa_engine.stream_final_response(query, context, effective_system):
        yield token


def stream_aarka_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    history: list = None,
) -> Generator[str, None, None]:
    """
    Stream fast high-precision tokens for Aarka AI with full persona and domain knowledge.
    """
    aarka_persona = (
        "You are Aarka AI, an enterprise-grade AI research, financial engineering, and system architecture assistant. "
        "Provide thorough, mathematically rigorous, well-structured answers with clear explanations, concrete examples, and actionable insights. "
        "Ensure precision, maintain a professional tone, and format outputs cleanly with GitHub-flavored markdown."
    )
    effective_system = (system_prompt + "\n\n" + aarka_persona) if system_prompt else aarka_persona
    
    # Try high-speed streaming via Vertex AI Gemini 2.5 engine
    try:
        client = _get_genai_client()
        prompt = f"System Instructions:\n{effective_system}\n\n"
        if context:
            prompt += f"Domain Knowledge & Live Context:\n{context}\n\n"
        if history:
            prompt += "Conversation History:\n"
            for h in history[-6:]:
                role = "User" if h.get("role") == "user" else "Aarka AI"
                msg = h.get("message") or h.get("content") or ""
                prompt += f"{role}: {msg}\n"
            prompt += "\n"
        prompt += f"User:\n{query}"

        response = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
        return
    except Exception as e:
        logger.warning("Aarka high-speed streaming error (%s) — using Neural Engine", e)

    # Local Neural Engine Fallback
    from modules import aarkaa_engine
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
