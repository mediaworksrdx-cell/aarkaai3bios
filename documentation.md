# AARKAAI Backend Architecture Documentation

## Overview
AARKAAI is a high-performance, single-service intelligent backend built with FastAPI. It leverages a quantized 3B parameter model (GGUF format) running natively on CPU using `llama-cpp-python`. The system features an ultra-low latency routing pipeline, an autonomous ReAct loop for executing system commands and managing files, and a self-improving RAG (Retrieval-Augmented Generation) memory block driven by user RLHF (Reinforcement Learning from Human Feedback).

---

## 1. System Components

### 1.1 The Orchestrator (`pipeline.py`)
This is the heart of the system. Every POST request to `/prompt` hits `process_query()`.
- **Semantic Routing:** The query is immediately sent to `semantic_filter.py` which categorizes it (e.g., `finance`, `rag`, `coding`, `general_query`).
- **Context Gathering:** 
  - If it's a finance query, it injects real-time Yahoo Finance data.
  - If it matches the knowledge base, it securely injects internal RAG documents.
  - If it triggers the news/current events criteria, it pulls from DuckDuckGo/Wikipedia bounds.
- **Path Selection:** 
  - **Fast Path:** General queries drop into `final_response` directly, completing in ~15-20s.
  - **Agent Path:** Queries containing action verbs (e.g., *execute*, *run*, *create a file*) bypass standard generation and trigger the Autonomous Agent loop.

### 1.2 The Inference Engine (`aarkaa_engine.py`)
A highly optimized adapter for local execution of the AARKAA-3B GGUF.
- **Physical Core Mapping:** CPU inference evaluates drastically slower when hyperthreads are used due to memory bandwidth starvation. The engine computes exactly `logical_cores // 2` to lock generation strictly to physical CPU clusters, maximizing throughput.
- **Dynamic Token Limits:** Capped conservatively (200 tokens for generation, ~500 for code) to ensure generation consistently remains under 25 seconds for general tasks.

### 1.3 The RAG & RLHF System (`rag.py` & `memory.py`)
- **Self-Learning (`auto_learn.py`):** Periodically runs in the background. It reads the conversation SQLite database to extract user insights and stores them as knowledge vectors.
- **Cosine Similarity Thresholding:** `rag.py` compares mathematical distance between a query and previous RLHF corrections. Critically, it enforces a hard `>= 0.35` cutoff. This guarantees that large blocks of RLHF data do not bloat the prompt LLM window for irrelevant questions, protecting context evaluation speed.

### 1.4 The Autonomous Agent (`coordinator.py`)
A pure-CPU ReAct (Reasoning and Acting) loop. The agent evaluates its own actions repetitively until a user task is satisfied.
- **Action Sandbox (`modules/tools/`):** Contains `BashTool` (terminal execution), `FSManager` (modifying OS files), and Web tools.
- **Error Forgiveness:** If the agent triggers a terminal error (e.g., running the wrong file path), it feeds the `stderr` standard output directly back into the ReAct loop so the AI can realize its mistake and gracefully summarize the issue to the end-user instead of crashing.

---

## 2. Hardware scaling limits

To ensure robust performance, note these hardware-specific considerations specific to AWS Compute environments and local scaling:
1. **CPU Burst Capacity Limits:** Standard Lightsail or T3 EC2 instances rely on "Burst Credits" for their 100% processing speed. A 4-minute complex autonomous coding loop will rapidly deplete these credits. When credits reach 0, you will be throttled down to a ~15% baseline cycle and experience generation blocks. Move to dedicated `C6i` or `C7g` AWS instances for scale, as they run 100% capacity continuously.
2. **Context Window Limitations:** `n_ctx` evaluates exponentially heavier upon the CPU. Pushing the engine past 4,096 context bounds sequentially loads massive vector requirements. All tools are designed to filter string outputs (like truncation in file/web scraping) to respect these buffer bounds natively.

---

## 3. Multilingual Support

AARKAAI natively supports 29+ languages through a full-stack multilingual pipeline:

### 3.1 Language Detection
The pipeline uses `langdetect` to identify the user's language (ISO 639-1 code) at the start of every request. The detected language is:
- Logged for analytics
- Passed to Wikipedia for localized article retrieval
- Returned in the API response as `detected_language`

### 3.2 Multilingual Embeddings
The embedding model is `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions), which supports 50+ languages. This powers:
- **Semantic Filter**: Classifies domains correctly regardless of input language
- **RAG Engine**: Retrieves knowledge entries even when queries and stored content are in different languages
- **Auto-Learn**: Extracts topics from conversations in any script (Hindi, Chinese, Arabic, etc.)

### 3.3 Language-Adaptive Prompts
All system prompts (primary_check, final_response, coordinator) instruct the model to:
- Respond in the same language the user writes in
- Translate context from other languages if needed

### 3.4 Multilingual Routing
The semantic filter's keyword heuristics include terms in English, Hindi, Spanish, French, German, Arabic, Japanese, and Chinese for all domain categories.

### 3.5 Supported Languages (Tier 1)
English, Chinese, Spanish, French, German, Japanese, Korean, Portuguese, Russian, Arabic, Hindi

### 3.6 Migration
When switching to multilingual embeddings, run `python reindex_db.py` to re-embed existing knowledge entries.

---

## 4. Extending the System

To add a new tool or logical condition to the backend:
1. Write a new class inside `modules/tools/` inheriting from `Tool`.
2. Map it cleanly inside the `get_tools()` dictionary in `coordinator.py`.
3. Inform the semantic filter `semantic_filter.py` by adding domain-specific heuristic words to its core logic to route efficiently.

*Updated 2026-04-13 — Multilingual Support Added*
