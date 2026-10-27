# AARKA Infer — Dedicated Inference Serving Subsystem for AARKAA-3B

AARKA Infer is a unified, high-performance inference-serving subsystem engineered specifically around **AARKAA-3B** (Qwen2 3B architecture). It transforms the fragmented inference paths across GGUF/llama.cpp, Modal GPU, and vLLM into a single decoupled, production-grade serving architecture.

---

## 1. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AARKAAI Application Ecosystem                        │
│        (FastAPI Backend · RAG · Finance · Memory · Multi-Agents)       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        AARKA Infer API Layer                           │
│   • OpenAI-Compatible Endpoints (/v1/chat/completions, /v1/models)     │
│   • Server-Sent Events (SSE) Streaming Engine                          │
│   • Tiered Production Readiness (/health/ready)                        │
│   • Prometheus & JSON Observability Telemetry (/metrics)               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      AARKA Infer Core Runtime                          │
│   • Architectural Verifier (Validates Qwen2 3B: 36 Layers, 16/2 Heads) │
│   • Asynchronous Request Scheduler (Priority Queue & Concurrency Pool) │
│   • Radix Prefix Tree KV Cache (Active Prompt Prefix Reuse & LRU)      │
│   • Deterministic PRNG Sampler (Seed Control & Repetition Penalties)   │
│   • Precision Metrics Tracker (TTFT, ITL, Output TPS, VRAM/RAM)        │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
       ┌────────────────────────┐       ┌────────────────────────┐
       │   GGUF / llama.cpp     │       │    vLLM Continuous     │
       │   Local CPU/GPU Node   │       │   Batching GPU Node    │
       │ (aarkaa-3b-q8/f16.gguf)│       │  (rthshr/aarkaa-3b-v1) │
       └────────────┬───────────┘       └────────────┬───────────┘
                    │                                │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │      AARKAA-3B Checkpoint      │
                    │   Config · Fast Tokenizer      │
                    │      Jinja2 Chat Template      │
                    └────────────────────────────────┘
```

---

## 2. Solutions to Key Identified Issues

| # | Finding in Legacy Code | Root Cause | AARKA Infer Resolution |
|---|------------------------|------------|------------------------|
| **1** | Model Selection | `aarkaa_engine.py` prioritized 7B GGUF files before 3B. | Prioritizes `aarkaa-3b-q8.gguf`, `aarkaa-3b-f16.gguf`, and `aarkaa-3b-q4_k_m.gguf`. 7B is strictly relegated to optional auxiliary status. |
| **2** | Modal Routing | `modal_server.py` defaulted `model="7b"` for general queries. | Canonical default is standardized to `"3b"`. Router dispatches general queries to AARKAA-3B. |
| **3** | Model Verification | Checkpoints unverified against config. | `ModelVerifier` inspects `config.json` and GGUF headers, ensuring 36 layers, 16 attention heads, 2 KV heads, 2048 hidden size, and 151936 vocab size. |
| **4** | Deployment Naming | Split between `aarkaa-ai/aarkaa-3b` and `rthshr/aarkaa-3b-v1`. | Aliases reconciled in `config.py` with automatic resolution across local paths and remote repositories. |
| **5** | Routing Integration | `ai_router.py` defined dispatcher without application callers. | Built `InferRouterDispatcher` in `aarka_infer/adapters/router_adapter.py` providing unified routing into the runtime. |
| **6** | Lock Contention | Single `threading.RLock()` serialized concurrent streaming requests. | Built `AsyncRequestScheduler` with non-blocking priority queues, concurrency semaphores, and cancellation tokens. |
| **7** | KV Cache | `_measure_prefix_cache_hit()` only measured string similarity. | Implemented `KVCacheManager` featuring an active Radix Prefix Tree, cache hit tracking, token savings, and LRU eviction. |
| **8** | Production Health | Startup returned `ok (stub)`, allowing empty stubs into production. | Implemented strict `/health/ready` check: returns HTTP 503 if real model weights are not loaded in production. |

---

## 3. DeepInfer Techniques Adopted

1. **Asynchronous Scheduling:** Priority queueing (`HIGH` for interactive chat, `NORMAL` for agents, `BACKGROUND` for batch tasks) with client disconnection cancellation tokens.
2. **Active Prefix Tree KV Cache:** Radix prefix tracking for common system prompts, eliminating redundant prefill computation.
3. **Deterministic Sampling:** Seeded PRNG for reproducible inference across research and quantitative finance regressions.
4. **Continuous Telemetry:** Real-time collection of:
   - **TTFT (Time To First Token):** Prefill and queue latency in milliseconds (p50, p90, p95).
   - **ITL (Inter-Token Latency):** Milliseconds per generated token.
   - **Output TPS:** Generated tokens per second per request and aggregate server throughput.
   - **Memory Footprint:** Host RAM and GPU VRAM utilization.

---

## 4. Quick Start & Deployment

### Standalone Server

Launch the independent high-performance serving microservice:

```bash
# Default (port 8008, auto-backend detection)
python -m aarka_infer.server

# Custom port and backend
python -m aarka_infer.server --port 8008 --backend llama_cpp --host 0.0.0.0
```

### In-Process Application Integration

Import AARKA Infer directly into your FastAPI application (`main.py` or `modules/aarkaa_engine.py`):

```python
from aarka_infer import AarkaInferEngine, SamplingParams

engine = AarkaInferEngine.get_instance()
await engine.initialize()

# Async Streaming Chat
messages = [
    {"role": "system", "content": "You are Aarkaa AI quantitative analyst."},
    {"role": "user", "content": "Analyze Reliance ROCE and debt profile."}
]

async for token in engine.chat_stream(messages, params=SamplingParams(temperature=0.7)):
    print(token, end="", flush=True)
```

---

## 5. API Reference

### OpenAI-Compatible Chat Completions
`POST /v1/chat/completions`

```json
{
  "model": "rthshr/aarkaa-3b-v1",
  "messages": [
    {"role": "system", "content": "You are Aarkaa AI."},
    {"role": "user", "content": "Explain VWAP calculation."}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": true,
  "seed": 42
}
```

### Strict Readiness Check
`GET /health/ready`
- Returns `HTTP 200` with `{"ready": true}` when model weights are validated.
- Returns `HTTP 503` if running on a mock/stub in a production environment.

### Performance Telemetry
`GET /metrics`
Returns TTFT percentiles (p50/p95), aggregate tokens-per-second, KV cache hit rate, and VRAM utilization.

---

## 6. Running Tests & Benchmarks

```bash
# Execute unit and integration tests (17 passed)
python -m pytest aarka_infer/tests

# Execute concurrency and throughput benchmark
python -m aarka_infer.benchmarks.benchmark_suite
```
