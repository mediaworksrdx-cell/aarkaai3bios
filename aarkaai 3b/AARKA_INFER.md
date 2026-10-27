# AARKA Infer — Serving Subsystem for AARKAA-3B

The dedicated inference-serving project for this model is located at:
`../aarka_infer`

## Features
- **Architectural Verifier:** Validates `config.json` against canonical Qwen2 3B specs (36 layers, 16 attention heads, 2 KV heads, 2048 hidden size, 151936 vocab).
- **Fast Tokenizer:** Loads `tokenizer.json` and renders `chat_template.jinja`.
- **Asynchronous Scheduler:** Continuous non-blocking request queue, concurrency control, and cancellation tokens.
- **Radix Prefix Tree KV Cache:** Active prefix reuse and LRU memory management.
- **Serving API:** OpenAI-compatible `/v1/chat/completions`, SSE streaming, strict `/health/ready`, and `/metrics`.

## Running the Server
```bash
# From repository root:
python -m aarka_infer.server --port 8008
```

## Running Tests
```bash
python -m pytest aarka_infer/tests
```
