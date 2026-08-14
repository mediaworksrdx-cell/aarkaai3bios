"""
AARKAAI – External Agents Provider (Gemini & Claude)

Provides unified streaming interface for:
  - Google Gemini Agent (via Vertex AI / google-genai with vertexai=True)
  - Anthropic Claude Agent (via anthropic)

NOTE: Gemini calls are routed through Vertex AI (project: orbital-heaven-504004-s2)
      to use GCP $300 free trial credits, NOT the Gemini Developer API quota.
"""
from __future__ import annotations

import logging
from typing import Generator
import config

logger = logging.getLogger(__name__)

# ─── Vertex AI Configuration ──────────────────────────────────────────────────
# Project and location are sourced from config (env vars VERTEX_PROJECT / VERTEX_LOCATION).
# GOOGLE_APPLICATION_CREDENTIALS is set automatically by config.py on import.



def stream_gemini_response(query: str, context: str = "", system_prompt: str = "", model_name: str = "gemini-2.5-flash") -> Generator[str, None, None]:
    """
    Stream live tokens from Google Gemini via Vertex AI.

    Uses vertexai=True so requests are routed through Vertex AI endpoints
    (aiplatform.googleapis.com), consuming GCP credits — NOT the Developer API quota.
    Requires Application Default Credentials (ADC) or a service account configured
    on the server (run `gcloud auth application-default login` locally, or attach
    a service account with 'Vertex AI User' role in production).
    """
    try:
        from google import genai

        # ✅ vertexai=True routes through aiplatform.googleapis.com (uses GCP credits)
        client = genai.Client(
            vertexai=True,
            project=config.VERTEX_PROJECT,
            location=config.VERTEX_LOCATION,
        )

        prompt = ""
        if system_prompt:
            prompt += system_prompt + "\n\n"
        if context:
            prompt += f"Context:\n{context}\n\n"
        prompt += f"User:\n{query}"

        # Map legacy/internal aliases → valid Vertex AI model IDs
        target_model = model_name or "gemini-2.5-flash"
        if "3.6" in target_model or "3.5" in target_model:
            # gemini-3.x does not exist on Vertex; fall back to latest stable
            target_model = "gemini-2.5-flash"
        elif "2.5" in target_model:
            target_model = "gemini-2.5-flash"
        elif "2.0" in target_model:
            target_model = "gemini-2.0-flash"
        elif "1.5" in target_model:
            target_model = "gemini-1.5-flash"
        else:
            target_model = "gemini-2.5-flash"  # safe default

        logger.info("Gemini Vertex AI request | project=%s location=%s model=%s",
                    config.VERTEX_PROJECT, config.VERTEX_LOCATION, target_model)

        response = client.models.generate_content_stream(
            model=target_model,
            contents=prompt,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        logger.exception("Gemini Vertex AI Error: %s", e)
        yield f"\n\n❌ **Gemini API Error**:\n{str(e)}"


def stream_claude_response(query: str, context: str = "", system_prompt: str = "", model_name: str = "") -> Generator[str, None, None]:
    """
    Stream live tokens from Anthropic Claude API.
    """
    if not config.CLAUDE_API_KEY:
        yield "⚠️ **Claude Agent API key is not configured.**\n\nPlease add `CLAUDE_API_KEY` to your backend `.env` file on the server."
        return

    # Map model name aliases
    api_model = config.CLAUDE_MODEL
    if "opus" in model_name:
        api_model = "claude-3-opus-20240229"
    elif "sonnet" in model_name or "claude" in model_name:
        api_model = "claude-3-5-sonnet-20241022"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
        
        sys_instruction = system_prompt or (
            f"You are Aarka AI powered by Anthropic {model_name or 'Claude'}. "
            "Provide production-grade, mathematically exact, highly polished, and structured answers."
        )
        
        prompt_text = f"Context:\n{context}\n\nUser Request: {query}" if context else query
        
        with client.messages.stream(
            model=api_model,
            max_tokens=4096,
            temperature=0.7,
            system=sys_instruction,
            messages=[{"role": "user", "content": prompt_text}]
        ) as stream:
            for text in stream.text_stream:
                yield text
    except ImportError:
        logger.error("anthropic package is not installed.")
        yield "⚠️ `anthropic` library is not installed on the server backend. Run `pip install anthropic`."
    except Exception as exc:
        logger.error("Claude stream error: %s", exc)
        yield f"\n\n❌ **Claude Error**: {str(exc)}"
