"""
AARKAAI – Architecture Knowledge Base
Comprehensive internal documentation indexed into RAG for self-aware responses.

Called once during startup to populate ChromaDB with AARKAA's own architecture docs.
Uses RAG's built-in cosine deduplication (distance ≤ 0.12) to avoid re-indexing on restart.
"""
from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

# ─── Architecture Documentation Entries ──────────────────────────────────────
# Each entry has a topic (used for RAG retrieval matching) and content
# (the actual knowledge the model should use when answering).

ARCHITECTURE_DOCUMENTS = [
    # ── Goal Planner ──────────────────────────────────────────────────────
    {
        "topic": "AARKAA Goal Planner Overview",
        "content": (
            "AARKAA's Goal Planner decomposes complex user requests into a strict Task DAG "
            "(Directed Acyclic Graph) JSON schema. It uses Pydantic models (TaskNode and TaskDAG) "
            "to enforce schema validation. Each TaskNode has fields: id (unique short ID like 't1'), "
            "name (human-readable title), description (detailed operations), tool_hint (suggested tool "
            "from Tool Registry), dependencies (list of task IDs that must complete first), "
            "exit_criteria (deterministic verification statement), retry_budget (0-4, default 2), "
            "approval_required (boolean for human gate), and status (pending/running/completed/failed/paused). "
            "The planner supports semantic caching via regex pattern matching against PLANNER_CACHE "
            "to bypass LLM planning latency for common query patterns. If no cache hit, it prompts "
            "AARKAA-3B with a structured template containing available tools metadata, then parses "
            "the JSON response. It retries up to 3 times on parse failures. If all retries fail, "
            "it falls back to a single-task DAG with a generic execution task."
        ),
    },
    {
        "topic": "AARKAA Planner Output Validation",
        "content": (
            "AARKAA validates planner output through a multi-step verification pipeline: "
            "1. Validate JSON schema — extract JSON bounds from raw LLM response using '{' and '}' delimiters. "
            "2. Validate Pydantic model — parse the JSON into TaskDAG(goal, tasks[TaskNode]) using strict Pydantic validation. "
            "3. Check unique task IDs — each TaskNode.id must be unique within the DAG. "
            "4. Verify DAG has no cycles — run _is_acyclic() which performs a standard topological cycle check "
            "using DFS with 3-state coloring (unvisited, visiting=0, visited=1). If any back-edge is detected, "
            "the plan is rejected. "
            "5. Ensure dependencies exist — each dependency ID in a task's dependencies list must reference "
            "a valid task ID in the DAG. Missing dependencies are safely ignored. "
            "6. Verify tool names are registered — tool_hint values are cross-referenced against the Tool Registry "
            "metadata (registry.get_all_tool_metadata()). "
            "7. Check tool permissions and risk levels — each tool has risk_level and latency_weight metadata. "
            "8. Validate retry budgets — retry_budget must be between 0 and 4 (enforced by Pydantic Field ge=0, le=4). "
            "9. Run supervisor policy checks — the Supervisor monitors execution for infinite loops and global retry exhaustion. "
            "10. If validation fails: the planner retries generation (up to 3 attempts). If all retries fail, "
            "it falls back to a single-task sequential DAG. If that also fails, the system uses assistant mode "
            "(direct AARKAA-3B generation without planning)."
        ),
    },
    # ── Execution Engine ──────────────────────────────────────────────────
    {
        "topic": "AARKAA Execution Engine",
        "content": (
            "AARKAA's Execution Engine is a topological DAG scheduler that executes validated task plans. "
            "It processes tasks in dependency order: for each iteration, it finds the next runnable task "
            "(all dependencies satisfied), checks human approval gates, verifies with the Supervisor for "
            "loop detection, then executes the task. Execution uses the Tool Registry to dispatch to the "
            "correct tool (WebSearch, FileEditTool, FileReadTool, BashTool, etc.). If no tool_hint is "
            "specified, it falls back to AARKAA-3B raw text generation. Each task has a retry_budget "
            "(default 2). On failure, the Supervisor records the retry and checks the global retry limit. "
            "Results are accumulated in a scratchpad containing: facts (completed task summaries), "
            "assumptions, unknowns, and evidence (task outputs keyed by task ID). The scratchpad is "
            "persisted to the database via Task Memory after each state change. When all tasks complete, "
            "the engine runs a final compilation step where AARKAA-3B consolidates all task results "
            "into a cohesive answer."
        ),
    },
    # ── Supervisor ────────────────────────────────────────────────────────
    {
        "topic": "AARKAA Supervisor",
        "content": (
            "AARKAA's Supervisor monitors DAG execution to prevent infinite tool loops and resource "
            "exhaustion. It has two core mechanisms: "
            "1. Loop Detection (check_loop): Uses a sliding window of size 4 over the execution history. "
            "Each invocation is recorded as (task_id, tool_name, params_hash). If all 4 entries in the "
            "window have identical tool_name and params_hash, the Supervisor flags an infinite loop and "
            "halts execution immediately. "
            "2. Global Retry Budget (check_retry_budget): Tracks total retries across the entire DAG "
            "execution. The default global limit is 5 retries. When exceeded, the Supervisor forces "
            "execution to abort. The global timeout is 120 seconds by default. "
            "The Supervisor is instantiated per-execution in the Execution Engine and operates as a "
            "stateful guard that prevents runaway agent behavior."
        ),
    },
    # ── Reflection ────────────────────────────────────────────────────────
    {
        "topic": "AARKAA Reflection and Self-Evaluation",
        "content": (
            "AARKAA's Reflection module provides execution feedback and triggers replanning checkpoints. "
            "The check_evidence_replanning() function analyzes the scratchpad (accumulated facts from "
            "completed tasks) against the original plan goals. It prompts AARKAA-3B to evaluate whether "
            "newly discovered evidence contradicts current DAG assumptions and whether the plan needs "
            "restructuring. The model outputs 'YES' (replan needed) or 'NO' (plan is fine). If replanning "
            "is triggered, the Goal Planner generates a new DAG incorporating the new evidence. This "
            "creates a self-correcting execution loop: Plan → Execute → Reflect → Replan if needed."
        ),
    },
    # ── Task Memory ───────────────────────────────────────────────────────
    {
        "topic": "AARKAA Task Memory",
        "content": (
            "AARKAA's Task Memory manages persistent state for goal execution using SQLAlchemy and a "
            "relational database. It provides three operations: "
            "1. save_goal(user_id, session_id, goal_text, plan) — creates a new TaskGoal record with "
            "the serialized task DAG and an empty scratchpad. Returns the goal ID. "
            "2. get_goal(goal_id) — retrieves the full goal state including task_dag, scratchpad, and status. "
            "3. update_goal_state(goal_id, plan, scratchpad, status) — updates the database with current "
            "execution progress. Called after every task state change (pending→running→completed/failed). "
            "The scratchpad is serialized as JSON containing facts, assumptions, unknowns, and evidence. "
            "This persistence enables execution resumption after approval gates or system restarts."
        ),
    },
    # ── Tool Registry ─────────────────────────────────────────────────────
    {
        "topic": "AARKAA Tool Registry",
        "content": (
            "AARKAA's Tool Registry manages all available tools that the agent can invoke during "
            "execution. Each tool is registered with metadata including: name, description, risk_level "
            "(low/medium/high), and latency_weight. Available tools include: "
            "- BashTool: Executes shell commands in a sandboxed workspace directory. "
            "- FileEditTool: Creates or overwrites files in the workspace. "
            "- FileReadTool: Reads file contents from the workspace. "
            "- WebSearch: Performs web searches using DuckDuckGo. "
            "- ImageGenTool: Generates images using AARKAA-VISION (Stable Diffusion). "
            "- ListSkillsTool: Lists all available skill documents. "
            "- GetSkillTool: Retrieves detailed skill instructions by name. "
            "- CreateSkillTool, UpdateSkillTool, DeleteSkillTool, ValidateSkillTool, TestSkillTool: "
            "Skill management tools (only exposed when skill-creator context is active). "
            "The registry provides execute_tool(name, params) for dispatching and "
            "get_all_tool_metadata() for injecting tool descriptions into planner prompts."
        ),
    },
    # ── Semantic Filter ───────────────────────────────────────────────────
    {
        "topic": "AARKAA Semantic Filter and Domain Classification",
        "content": (
            "AARKAA's Semantic Filter classifies incoming queries into domains with confidence scores. "
            "It uses a 3-layer scoring approach: "
            "1. Keyword Heuristic Scoring: Multilingual keyword dictionaries for 7 domains "
            "(general, finance, technology, science, health, history, web_search) compute overlap scores. "
            "2. Embedding-Based Cosine Similarity: Domain prototype embeddings (averaged keyword embeddings) "
            "are compared against the query embedding using cosine similarity. "
            "3. TensorFlow Neural Scoring: A small dense classifier (128→64→n_classes with dropout) "
            "predicts domain probabilities from query embeddings. "
            "Scores are fused with weights: prototype 45%, TF 35%, keyword 20% (when all available). "
            "The result includes: domain, confidence, intent (refined sub-intent like price_check, "
            "coding_help, news_search), and per-domain scores. Coding syntax detection overrides "
            "classification to technology/coding_help with confidence ≥ 0.9."
        ),
    },
    # ── Coordinator (ReAct Loop) ──────────────────────────────────────────
    {
        "topic": "AARKAA Coordinator and ReAct Loop",
        "content": (
            "AARKAA's Coordinator manages the ReAct (Reasoning and Acting) agent loop. It formats a "
            "system prompt with tool descriptions and runs up to 10 iterations of: "
            "1. Generate: AARKAA-3B produces a response with 'Thought:', 'Action:', 'Action Input:' format. "
            "2. Parse: The coordinator extracts the tool name and JSON parameters using regex matching "
            "with multiple fallback strategies (exact match, fuzzy substring, robust key extraction). "
            "3. Execute: The tool is dispatched via the Tool Registry. Observations are capped at 1000 chars. "
            "4. Append: The full Thought+Action+Observation is appended to the prompt for the next iteration. "
            "Anti-repetition measures include: action deduplication (prevents identical tool calls), "
            "paragraph-level output deduplication, and loop-specific error messages that guide the model "
            "toward different approaches. The loop terminates when 'Final Answer:' is detected or "
            "max iterations are reached."
        ),
    },
    # ── Pipeline ──────────────────────────────────────────────────────────
    {
        "topic": "AARKAA Main Pipeline and Request Flow",
        "content": (
            "AARKAA's main pipeline (pipeline.py) orchestrates the full request lifecycle: "
            "0. Query sanitization (strip control chars, ChatML tokens) + language detection (langid). "
            "1. Semantic Filter classifies domain + confidence. Greetings and reasoning puzzles bypass classification. "
            "2. If confidence < 0.45 and not a special intent, fallback to 'general' domain. "
            "3. RAG retrieval from ChromaDB knowledge base (skipped for greetings, puzzles, coding, creative writing). "
            "4. Domain-specific routing: Finance (yfinance live data), Technical Analysis (RSI/MACD/Bollinger), "
            "Options Strategy generation, Web Search (DuckDuckGo with circuit breaker). "
            "5. Context fusion: merge all external sources (RAG, finance, web search, technical analysis). "
            "6. AARKAA-3B final generation with full context. "
            "7. Store conversation in Memory. "
            "8. Auto-learn trigger check. "
            "Production features include: circuit breakers for web_search (3 consecutive failures → 5min cooldown) "
            "and finance (3 failures → 2min cooldown), per-module error isolation, and query deduplication."
        ),
    },
    # ── RAG Engine ────────────────────────────────────────────────────────
    {
        "topic": "AARKAA RAG Engine and Knowledge Retrieval",
        "content": (
            "AARKAA's RAG (Retrieval-Augmented Generation) engine uses ChromaDB with HNSW-indexed "
            "cosine similarity search. It stores knowledge entries with embeddings from "
            "paraphrase-multilingual-MiniLM-L12-v2 (384-dim). Retrieval pipeline: "
            "Phase 1: ChromaDB similarity search with user scoping (user's own + global entries). "
            "Phase 2: Filter by cosine similarity threshold (default 0.50). "
            "Phase 3: Keyword overlap validation (Jaccard containment) + domain consistency check. "
            "Phase 4: Cross-encoder reranking using ms-marco-MiniLM-L6-v2 (if available). "
            "Hardening: cosine deduplication on storage (distance ≤ 0.12 blocks duplicates), "
            "context budget cap to prevent prompt bloat, and configurable thresholds."
        ),
    },
    # ── AARKAA-3B Model Engine ────────────────────────────────────────────
    {
        "topic": "AARKAA-3B Model Engine and Inference",
        "content": (
            "AARKAA-3B is a custom fine-tuned Qwen2.5-3B-Instruct model served via llama-cpp-python "
            "in GGUF format (F16 quantization, ~5.8GB). The engine supports both CPU and GPU inference. "
            "Model selection follows a priority cascade: F32 → F16 → Q8 GGUF files. "
            "During daytime IST hours, the model is pre-warmed on GPU for instant responses. "
            "During nighttime (1-7 AM IST), it uses CPU-only inference to reduce power consumption. "
            "The engine provides: generate_raw() for direct text generation with configurable "
            "max_new_tokens and stop sequences, and clean_response() for post-processing "
            "(stripping artifacts, deduplication). Thread safety is ensured via a model lock. "
            "The model is initialized with n_ctx=16384 tokens context window."
        ),
    },
    # ── AARKAA-VISION ─────────────────────────────────────────────────────
    {
        "topic": "AARKAA Vision Image Generation",
        "content": (
            "AARKAA-VISION is a Stable Diffusion v1.4 model fine-tuned with a custom LoRA adapter "
            "(rthshr/aarkaa-ai-vision). The LoRA weights are fused permanently into the base model "
            "parameters and saved as a standalone pipeline at /workspace/aarkaai3b/aarkaa-vision-standalone. "
            "The fused model is ~2.6GB and includes: UNet (1.7GB), Safety Checker (580MB), "
            "Text Encoder (235MB), VAE (160MB), and tokenizer. It generates images at 512x512 resolution "
            "with 30 inference steps using the EulerDiscreteScheduler. The vision pipeline is loaded "
            "on-demand and cached in memory for subsequent requests."
        ),
    },
    # ── Architecture Overview ─────────────────────────────────────────────
    {
        "topic": "AARKAA System Architecture Overview",
        "content": (
            "AARKAA (Autonomous Adaptive Reasoning and Knowledge-Augmented Agent) is a production AI platform "
            "with the following architecture: "
            "Frontend: Next.js web application (aarkaweb) served on port 3000. "
            "Backend: FastAPI/Uvicorn server on port 5000 with the following module stack: "
            "- Semantic Filter: TensorFlow + embedding-based domain classifier (7 domains). "
            "- AARKAA-3B Engine: Custom Qwen2.5-3B-Instruct GGUF model via llama-cpp-python. "
            "- RAG Engine: ChromaDB vector store with cross-encoder reranking. "
            "- Goal Planner: LLM-driven DAG decomposition with Pydantic validation. "
            "- Execution Engine: Topological DAG scheduler with tool dispatch. "
            "- Supervisor: Loop detection and retry budget enforcement. "
            "- Reflection: Evidence-based replanning checkpoints. "
            "- Task Memory: SQLAlchemy-based goal state persistence. "
            "- Tool Registry: BashTool, FileEditTool, FileReadTool, WebSearch, ImageGenTool, Skills. "
            "- Coordinator: ReAct agent loop (max 10 iterations). "
            "- Pipeline: Main orchestrator with circuit breakers and domain routing. "
            "- AARKAA-VISION: Stable Diffusion + LoRA for image generation. "
            "- Finance Module: yfinance live data + technical analysis + options strategy. "
            "- Gamma PDF: Premium multi-page PDF generation with matplotlib charts. "
            "- Memory: Conversation history storage. "
            "- Auto-Learn: Automatic knowledge extraction and RAG indexing. "
            "Infrastructure: AWS EC2 instance with Nginx reverse proxy (HTTPS on port 443)."
        ),
    },
    # ── Auto-Learn System ─────────────────────────────────────────────────
    {
        "topic": "AARKAA Auto-Learn System",
        "content": (
            "AARKAA's Auto-Learn system automatically extracts knowledge from high-quality model "
            "responses and indexes them into the RAG knowledge base. It runs on a configurable "
            "interval (default 15 interactions) and evaluates response quality using length, "
            "structure, and domain relevance heuristics. Extracted knowledge is stored via "
            "rag.store_knowledge() with source='auto_learn'. Auto-learn entries are excluded "
            "from RAG retrieval by default (filtered out in the ChromaDB where clause) to prevent "
            "feedback loops where the model retrieves its own previous outputs as authoritative sources."
        ),
    },
    # ── Circuit Breakers ──────────────────────────────────────────────────
    {
        "topic": "AARKAA Circuit Breakers",
        "content": (
            "AARKAA implements circuit breaker patterns for external module resilience: "
            "1. Web Search Circuit Breaker: Opens after 3 consecutive failures, cooldown 300 seconds (5 min). "
            "2. Finance Circuit Breaker: Opens after 3 consecutive failures, cooldown 120 seconds (2 min). "
            "When a circuit breaker is open, the module is skipped entirely and the pipeline proceeds "
            "without that data source. Each successful call resets the failure counter. After the cooldown "
            "period, the breaker allows one retry attempt. This prevents cascading failures when external "
            "services (DuckDuckGo, yfinance) are temporarily unavailable."
        ),
    },
]


def index_architecture_knowledge(embed_fn: Callable) -> None:
    """
    Index all AARKAA architecture documents into the RAG knowledge base.
    Called once during server startup, after RAG initialization.
    Uses RAG's built-in cosine deduplication to skip already-indexed entries.
    """
    from modules import rag

    if rag._collection is None:
        logger.warning("RAG not initialised — skipping architecture knowledge indexing")
        return

    indexed = 0
    skipped = 0
    for doc in ARCHITECTURE_DOCUMENTS:
        try:
            # store_knowledge handles deduplication internally (cosine distance ≤ 0.12)
            rag.store_knowledge(
                topic=doc["topic"],
                content=doc["content"],
                source="architecture",
                user_id=None,  # Global knowledge
            )
            indexed += 1
        except Exception as exc:
            logger.warning("Failed to index architecture doc '%s': %s", doc["topic"], exc)
            skipped += 1

    logger.info(
        "Architecture knowledge indexing complete: %d indexed, %d skipped/failed",
        indexed, skipped,
    )
