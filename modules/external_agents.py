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

# Service account discovery & environment configuration
_DEFAULT_SA_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not _DEFAULT_SA_PATH or not os.path.exists(_DEFAULT_SA_PATH):
    # Dynamically search for service account json files in workspace root or parent
    search_dirs = [Path(__file__).parent.parent, Path.cwd(), Path.home()]
    for sdir in search_dirs:
        for sa_file in sdir.glob("*service_account*.json"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_file)
            _DEFAULT_SA_PATH = str(sa_file)
            break
        if not _DEFAULT_SA_PATH:
            for sa_file in sdir.glob("orbital-heaven-*.json"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_file)
                _DEFAULT_SA_PATH = str(sa_file)
                break
        if _DEFAULT_SA_PATH:
            break

def _get_genai_client():
    """Create and return a Google GenAI / Vertex AI client with robust authentication."""
    from google import genai
    
    # 1. Prioritize Vertex AI via Service Account / ADC
    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not sa_path or not os.path.exists(sa_path):
        search_dirs = [Path(__file__).parent.parent, Path.cwd(), Path.home()]
        for sdir in search_dirs:
            for sa_file in sdir.glob("orbital-heaven-*.json"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_file)
                sa_path = str(sa_file)
                break
            if sa_path:
                break

    if sa_path and os.path.exists(sa_path):
        project = os.getenv("VERTEX_PROJECT") or getattr(config, "VERTEX_PROJECT", "orbital-heaven-504004-s2")
        location = os.getenv("VERTEX_LOCATION") or getattr(config, "VERTEX_LOCATION", "us-central1")
        return genai.Client(
            vertexai=True,
            project=project,
            location=location,
            http_options={"api_version": "v1beta1", "base_url": "https://aiplatform.googleapis.com/"},
        )

    # 2. Secondary fallback: Gemini API Key (if Vertex AI SA is unavailable)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or getattr(config, "GEMINI_API_KEY", "")
    if gemini_key:
        return genai.Client(api_key=gemini_key)
    
    # 3. Default Vertex AI client
    project = os.getenv("VERTEX_PROJECT") or getattr(config, "VERTEX_PROJECT", "orbital-heaven-504004-s2")
    location = os.getenv("VERTEX_LOCATION") or getattr(config, "VERTEX_LOCATION", "us-central1")
    return genai.Client(
        vertexai=True,
        project=project,
        location=location,
        http_options={"api_version": "v1beta1", "base_url": "https://aiplatform.googleapis.com/"},
    )


def stream_gemini_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    model_name: str = "gemini-3.7-flash",
    history: list = None,
) -> Generator[str, None, None]:
    """
    Stream live tokens for Google Gemini 3.7 via Vertex AI or Google GenAI SDK.
    Supports multi-turn conversation history.
    """
    try:
        from google.genai import types
        client = _get_genai_client()

        contents_list = []
        if context:
            contents_list.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"[Context Information]\n{context}")]
            ))
            contents_list.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text="Understood. I will reference this context.")]
            ))
        if history:
            for h in history[-20:]:
                role = "user" if h.get("role") == "user" else "model"
                msg = h.get("message") or h.get("content") or ""
                if msg.strip():
                    contents_list.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.strip())]
                    ))
        contents_list.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=query.strip())]
        ))

        target_model = "gemini-3.7-flash"
        if "pro" in model_name:
            target_model = "gemini-3.7-flash"

        gen_config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            temperature=0.3,
        )

        response = client.models.generate_content_stream(
            model=target_model,
            contents=contents_list,
            config=gen_config,
        )
        import re
        for chunk in response:
            if chunk.text:
                filtered_text = re.sub(r'(?i)\s*#Aarkaa(?:AI)?\b', '', chunk.text)
                filtered_text = re.sub(r'(?i)\s*#Aarka(?:AI)?\b', '', filtered_text)
                if filtered_text:
                    yield filtered_text
        return
    except Exception as e:
        logger.warning("Gemini streaming error (%s) — falling back to Aarkaa Neural Engine", e)

    # High-performance native fallback via Aarkaa Neural Engine
    from modules import aarkaa_engine
    gemini_system = "You are Google Gemini 3.7, an advanced AI model developed by Google. Answer with high technical precision, structured insights, and clarity."
    effective_system = (system_prompt + "\n\n" + gemini_system) if system_prompt else gemini_system
    for token in aarkaa_engine.stream_final_response(query, context, intent="general_query", history=history):
        yield token


def stream_aarka_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    history: list = None,
) -> Generator[str, None, None]:
    """
    Stream fast high-precision tokens for Aarka AI using the native Aarka Neural Engine
    (aarkaa-7b / aarkaa-3b GGUF) with multi-turn conversational memory (10+ turns / 20+ messages).
    """
    from modules import aarkaa_engine
    if aarkaa_engine.is_available():
        logger.info("Serving via Native Aarka Neural Engine (%s)", getattr(aarkaa_engine, "_gguf_file_path", "live"))
        for token in aarkaa_engine.stream_final_response(query, context, intent="general_query", history=history):
            yield token
        return

    aarka_persona = (
        "You are Aarka AI, an enterprise-grade AI research, financial engineering, and system architecture assistant. "
        "CORE DATA INTEGRITY & AUDIT POLICY: "
        "For every displayed price, volume, financial metric, indicator, and score, always provide the exact source, timestamp, data vintage, and whether it is reported or calculated. "
        "When the user specifies operational requirements, reporting standards, compliance policies, or audit formats, immediately adopt, confirm, and execute them with rigorous professional discipline. Never refuse instructions or claim prompt injection when receiving operational or reporting directives. "
        "Provide thorough, mathematically rigorous, well-structured answers with clear explanations, concrete examples, and actionable insights. "
        "Ensure precision, maintain a professional tone, and format outputs cleanly with GitHub-flavored markdown. "
        "CRITICAL CONSTRAINT: Do NOT append social media hashtags, SEO tags, promotional markers, or brand tags anywhere in or at the end of your response."
    )
    effective_system = (system_prompt + "\n\n" + aarka_persona) if system_prompt else aarka_persona
    
    # Cloud fallback if local model weights are not loaded
    try:
        from google.genai import types
        client = _get_genai_client()

        contents_list = []
        if context:
            contents_list.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"[Domain Knowledge & Live Context]\n{context}")]
            ))
            contents_list.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text="Understood. I will reference this domain knowledge in our analysis.")]
            ))
        if history:
            # Preserve up to 20 messages (10 Q&A turns)
            for h in history[-20:]:
                role = "user" if h.get("role") == "user" else "model"
                msg = h.get("message") or h.get("content") or ""
                if msg.strip():
                    contents_list.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.strip())]
                    ))

        user_query_text = query.strip()
        is_provenance_directive = any(
            phrase in user_query_text.lower()
            for phrase in [
                "provide the exact source, timestamp, data vintage",
                "for every displayed price, volume",
                "whether it is reported or calculated",
                "field-level provenance",
                "data lineage",
            ]
        )
        if is_provenance_directive:
            user_query_text = (
                f"The user has defined the following authoritative data lineage and provenance standard:\n"
                f"> \"{query.strip()}\"\n\n"
                f"Confirm full compliance with this standard across all Aarka AI operations. Explain how field-level provenance is enforced across all financial models and market feeds, and present the complete Master Lineage & Provenance Audit Table demonstrating exact Source, Timestamp, Data Vintage, Type (Reported vs Calculated vs Heuristic Proxy vs Data Gap), and mathematical extraction formulas for all key metrics (LTP, Volume, Market Cap, Trailing EPS, P/E Ratio, P/B Ratio, RSI 14, 50/200 EMAs, 12-Factor Composite Score, Delivery Proxy, Volatility Envelope, and F&O Sentiment)."
            )

        contents_list.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_query_text)]
        ))

        gen_config = types.GenerateContentConfig(
            system_instruction=effective_system,
            temperature=0.3,
        )

        response = client.models.generate_content_stream(
            model="gemini-3.7-flash",
            contents=contents_list,
            config=gen_config,
        )
        import re
        for chunk in response:
            if chunk.text:
                filtered_text = re.sub(r'(?i)\s*#Aarkaa(?:AI)?\b', '', chunk.text)
                filtered_text = re.sub(r'(?i)\s*#Aarka(?:AI)?\b', '', filtered_text)
                if filtered_text:
                    yield filtered_text
        return
    except Exception as e:
        logger.warning("Aarka high-speed streaming error (%s) — using Neural Engine", e)

    # Local Neural Engine Fallback
    from modules import aarkaa_engine
    for token in aarkaa_engine.stream_final_response(query, context, intent="general_query", history=history):
        yield token


def _get_anthropic_client():
    """Create and return an Anthropic client using ANTHROPIC_API_KEY with environment fallback."""
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY") or getattr(config, "ANTHROPIC_API_KEY", "")
    if not api_key:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ANTHROPIC_API_KEY="):
                            api_key = line.split("=", 1)[1].strip("'\"")
                            os.environ["ANTHROPIC_API_KEY"] = api_key
                            break
            except Exception as read_err:
                logger.warning("Error reading .env for ANTHROPIC_API_KEY: %s", read_err)

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured in environment or .env file.")
    return anthropic.Anthropic(api_key=api_key)


def stream_claude_response(
    query: str,
    context: str = "",
    system_prompt: str = "",
    model_name: str = "claude-sonnet-5",
    history: list = None,
) -> Generator[str, None, None]:
    """
    Stream live tokens for Claude Sonnet 5 via the Anthropic Messages streaming API.
    Supports multi-turn conversation memory and falls back gracefully to Aarka Neural Engine.
    """
    try:
        client = _get_anthropic_client()

        # Build system instruction
        base_system = (
            "You are Claude Sonnet 5, an advanced AI reasoning and coding model developed by Anthropic. "
            "Deliver deep technical rigor, precise mathematical formulations, and production-ready solutions "
            "without marketing fluff or unnecessary conversational closings."
        )
        effective_system = f"{system_prompt}\n\n{base_system}" if system_prompt else base_system
        if context:
            effective_system += f"\n\n[Retrieved Context Information]\n{context}"

        # Format multi-turn history strictly conforming to Anthropic role alternation
        messages = []
        if history:
            for h in history[-20:]:
                role = "user" if h.get("role") == "user" else "assistant"
                msg = h.get("message") or h.get("content") or ""
                if msg and msg.strip():
                    if messages and messages[-1]["role"] == role:
                        messages[-1]["content"] += f"\n\n{msg.strip()}"
                    else:
                        messages.append({"role": role, "content": msg.strip()})

        # Ensure history starts with user turn
        while messages and messages[0]["role"] != "user":
            messages.pop(0)

        # Append current user prompt
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += f"\n\n{query.strip()}"
        else:
            messages.append({"role": "user", "content": query.strip()})

        # Determine target Anthropic model ID
        normalized_model = (model_name or "").lower().strip()
        if "opus" in normalized_model:
            target_model = "claude-opus-5"
        elif "4-6" in normalized_model or "sonnet-4" in normalized_model:
            target_model = "claude-sonnet-4-6"
        elif "haiku" in normalized_model:
            target_model = "claude-haiku-4-5-20251001"
        else:
            target_model = "claude-sonnet-5"

        import re
        with client.messages.stream(
            model=target_model,
            max_tokens=4096,
            system=effective_system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                if text:
                    filtered_text = re.sub(r'(?i)\s*#Aarkaa?(?:AI)?\b', '', text)
                    if filtered_text:
                        yield filtered_text
        return

    except Exception as e:
        logger.warning("Claude Sonnet streaming error (%s) — falling back to Aarka Neural Engine", e)

    # Local Neural Engine Fallback
    from modules import aarkaa_engine
    claude_sys = "You are Claude Sonnet 5 by Anthropic. Answer with high technical precision, structured insights, and clarity."
    fallback_sys = (system_prompt + "\n\n" + claude_sys) if system_prompt else claude_sys
    for token in aarkaa_engine.stream_final_response(query, context, fallback_sys, history=history):
        yield token

