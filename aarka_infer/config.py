"""
AARKA Infer Configuration Module
Centralized, validated configuration for the AARKAA-3B inference engine.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root path of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent

# Official AARKAA-3B checkpoint directory containing config.json, tokenizer.json, chat_template.jinja
AARKAA_3B_DIR = REPO_ROOT / "aarkaai 3b"


class InferConfig(BaseSettings):
    """Configuration settings for AARKA Infer serving engine."""

    # ── Model Identity & Identification ───────────────────────────────────────
    # Reconciles rthshr/aarkaa-3b-v1 and aarkaa-ai/aarkaa-3b aliases
    model_id: str = Field(
        default="rthshr/aarkaa-3b-v1",
        description="Canonical model identifier"
    )
    model_aliases: List[str] = Field(
        default=["aarkaa-ai/aarkaa-3b", "aarkaa-3b", "aarkaa-3b-v1", "default"],
        description="Recognized aliases that route to AARKAA-3B"
    )

    # ── Model Checkpoint & Architecture ──────────────────────────────────────
    config_json_path: Path = Field(
        default=AARKAA_3B_DIR / "config.json",
        description="Path to Qwen2ForCausalLM config.json"
    )
    tokenizer_json_path: Path = Field(
        default=AARKAA_3B_DIR / "tokenizer.json",
        description="Path to official tokenizer.json"
    )
    chat_template_path: Path = Field(
        default=AARKAA_3B_DIR / "chat_template.jinja",
        description="Path to Jinja2 chat template"
    )

    # ── GGUF Prioritized Search Paths (Strictly 3B Focused) ───────────────────
    # Prioritizes 3B quantized & fp16 models over any legacy 7B artifacts
    gguf_search_directories: List[Path] = Field(
        default=[
            AARKAA_3B_DIR,
            REPO_ROOT / "models",
            REPO_ROOT,
            Path.home() / ".cache" / "huggingface" / "hub" / "models--rthshr--aarkaa-3b" / "snapshots",
            Path.home() / "models",
        ]
    )
    gguf_candidates_3b: List[str] = Field(
        default=[
            # 7B Primary Models -- priority 1
            "aarkaa-7b-q8.gguf",
            "aarkaa-7b-f16.gguf",
            "aarkaa-7b-q16.gguf",
            "aarkaa-7b.gguf",
            # 3B Auxiliary Models -- priority 2
            "aarkaa-3b-q8.gguf",
            "aarkaa-3b-f16.gguf",
            "aarkaa-3b-q4_k_m.gguf",
            "aarkaa-3b-q16.gguf",
            "aarkaa-3b-f32.gguf",
            "aarkaa-3b.gguf",
        ],
        description="Prioritized list of GGUF filenames (7B first, 3B fallback)"
    )

    # ── Backend Selection ────────────────────────────────────────────────────
    # Options: "auto", "llama_cpp", "vllm", "mock"
    backend: str = Field(
        default=os.getenv("AARKA_INFER_BACKEND", "auto"),
        description="Inference backend choice"
    )
    vllm_api_url: Optional[str] = Field(
        default=os.getenv("VLLM_3B_URL", "http://localhost:8000/v1"),
        description="vLLM server endpoint if running as standalone microservice"
    )

    # ── Hardware & Performance Settings ──────────────────────────────────────
    n_threads: int = Field(
        default=int(os.getenv("AARKA_INFER_THREADS", "4")),
        description="Number of CPU threads for llama.cpp"
    )
    n_gpu_layers: int = Field(
        default=int(os.getenv("AARKA_INFER_GPU_LAYERS", "-1")),  # -1 = all layers to GPU if available
        description="Number of layers to offload to GPU (-1 = all, 0 = CPU only)"
    )
    context_window: int = Field(
        default=32768,  # Architectural maximum supported by Qwen2 3B config
        description="Max context tokens"
    )
    default_max_tokens: int = Field(
        default=2048,
        description="Default generation token limit"
    )

    # ── Concurrency & Queue Scheduler ─────────────────────────────────────────
    max_concurrent_requests: int = Field(
        default=int(os.getenv("AARKA_MAX_CONCURRENT", "8")),
        description="Max concurrent generation tasks before queueing"
    )
    queue_max_size: int = Field(
        default=int(os.getenv("AARKA_QUEUE_MAX_SIZE", "64")),
        description="Max request queue depth"
    )
    queue_timeout_seconds: float = Field(
        default=float(os.getenv("AARKA_QUEUE_TIMEOUT", "30.0")),
        description="Max wait time in queue before returning 429/504"
    )

    # ── KV Cache Management ──────────────────────────────────────────────────
    kv_cache_max_blocks: int = Field(
        default=2048,
        description="Maximum KV cache blocks"
    )
    kv_cache_block_size: int = Field(
        default=16,
        description="Tokens per KV cache block"
    )
    enable_prefix_caching: bool = Field(
        default=True,
        description="Enable active Radix prefix tree caching for system prompts"
    )

    # ── Server & Health ──────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8008, description="API port")
    environment: str = Field(
        default=os.getenv("ENVIRONMENT", "development"),
        description="Runtime environment: development | staging | production"
    )
    strict_production_health: bool = Field(
        default=True,
        description="Require real verified weights to pass /health/ready in production"
    )

    model_config = SettingsConfigDict(
        env_prefix="AARKA_INFER_",
        extra="ignore"
    )


# Global singleton configuration
settings = InferConfig()
