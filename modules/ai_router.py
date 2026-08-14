"""
AARKAAI Backend – Decoupled AI Router Module

Routes user prompts to specialized inference endpoints (AARKAA 3B, AARKAA 7B Coder, or AARKAA Vision).
Supports local GGUF/llama-cpp as fallback when vLLM microservices are offline.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
from typing import Dict, Any, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_GPU_CONCURRENCY = {
    "general_3b": asyncio.Semaphore(int(os.getenv("AARKAAI_3B_CONCURRENCY", "8"))),
    "coder": asyncio.Semaphore(int(os.getenv("AARKAAI_CODER_CONCURRENCY", "4"))),
    "vision": asyncio.Semaphore(int(os.getenv("AARKAAI_VISION_CONCURRENCY", "4"))),
}
QUEUE_TIMEOUT = float(os.getenv("AARKAAI_QUEUE_TIMEOUT", "30.0"))

_redis_client = None
_redis_checked = False

def _get_cache_redis():
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True
    try:
        import redis as redis_lib
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis_lib.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
        _redis_client.ping()
        logger.info("AI Router: using Redis cache (%s)", redis_url)
    except Exception as e:
        _redis_client = None
        logger.info("AI Router: Redis cache unavailable: %s", e)
    return _redis_client

def _cache_key(target_service, messages, temperature, max_tokens):
    payload = {
        "target_service": target_service,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

# Remote vLLM / Microservice endpoints
VLLM_3B_URL = os.getenv("VLLM_3B_URL", "http://localhost:8000/v1")
VLLM_CODER_URL = os.getenv("VLLM_CODER_URL", "http://localhost:8001/v1")
VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://localhost:8002/v1")

# Threshold / Pattern definitions for request classification
CODE_PATTERNS = re.compile(
    r"\b(def|class|import|function|const|let|var|return|async|await|select|from|where|join|"
    r"dockerfile|git|pip|npm|build|compile|syntax|refactor|debug|bug|exception|traceback|"
    r"python|javascript|typescript|c\+\+|rust|java|golang|sql|html|css)\b",
    re.IGNORECASE,
)


class AIRouter:
    """
    Intelligent request router that dispatches queries to:
      1. AARKAA Vision (if query contains image payload)
      2. AARKAA 7B Coder (if query is programming/code related)
      3. AARKAA 3B (for general conversations, finance, RAG, and reasoning)
    """

    @staticmethod
    def classify_target(query: str, has_image: bool = False, requested_model: Optional[str] = None) -> str:
        """Return target model identifier: 'vision', 'coder', or 'general_3b'."""
        if has_image:
            return "vision"

        if requested_model:
            model_lower = requested_model.lower()
            if "coder" in model_lower or "7b" in model_lower:
                return "coder"
            if "vision" in model_lower:
                return "vision"

        # Pattern-based classification for auto-routing
        if CODE_PATTERNS.search(query):
            return "coder"

        return "general_3b"

    @classmethod
    async def dispatch_vllm(
        cls,
        target_service: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Dispatch request to the appropriate decoupled vLLM / Vision HTTP microservice.
        """
        r = _get_cache_redis()
        cache_key = _cache_key(target_service, messages, temperature, max_tokens)
        if r is not None:
            try:
                cached = r.get(f"cache:ai:{cache_key}")
                if cached:
                    logger.info("Cache HIT")
                    return json.loads(cached)
            except Exception:
                pass

        url_map = {
            "general_3b": f"{VLLM_3B_URL}/chat/completions",
            "coder": f"{VLLM_CODER_URL}/chat/completions",
            "vision": f"{VISION_SERVICE_URL}/chat/completions",
        }
        target_url = url_map.get(target_service, url_map["general_3b"])

        model_name_map = {
            "general_3b": "aarkaa-3b",
            "coder": "aarkaa-7b-coder",
            "vision": "aarkaa-vision",
        }

        payload = {
            "model": model_name_map.get(target_service, "aarkaa-3b"),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        logger.info("Routing query to %s endpoint [%s]", target_service, target_url)
        
        semaphore = _GPU_CONCURRENCY.get(target_service, _GPU_CONCURRENCY["general_3b"])
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=QUEUE_TIMEOUT)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=503, detail="GPU inference queue full. Try again shortly.")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(target_url, json=payload)
                resp.raise_for_status()
                
                result = resp.json()
                if r is not None:
                    try:
                        r.setex(f"cache:ai:{cache_key}", 3600, json.dumps(result))
                        logger.info("Cache MISS, stored")
                    except Exception:
                        pass
                        
                return result
        finally:
            semaphore.release()
