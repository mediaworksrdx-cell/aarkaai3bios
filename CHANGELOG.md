# Changelog

All notable changes to AARKAAI are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.0] — 2026-09

### Added
- Hybrid Query Router (HQR): parallel multi-source context gathering with configurable timeouts
- Tool Router Pipeline: 3B intent detection → permission gate → tool execution → 7B polish pass
- Cognitive Subagent Orchestrator: deep research multi-agent mode (`mode=deep`)
- Knowledge-First probe: high-confidence distilled answer fast-path (feature-flagged)
- Autonomous Planner: goal decomposition with DAG execution engine
- Two-step Finance Strategy Approval Gate with human-in-the-loop selection
- ScreenerAgent: institutional-grade multi-factor equity screening (20 strategies, regime detection)
- External agent support: Gemini, Claude, GPT streaming via `model_override` header
- `/prompt/stream` SSE endpoint with per-source status events and approval gate events
- PKCE + CSRF state cookie for Google OAuth flow
- Prometheus metrics at `/metrics` (JSON + `text/plain` Prometheus exposition)
- Skill CRUD API: create, read, update, delete, version history (`/skills/*`)
- User settings API with per-user model / style / theme preferences (`/settings`)
- MongoDB dual-backend support alongside SQLite (switched via `MONGODB_URI`)
- Architecture self-awareness: RAG-powered internal architecture queries
- MCP router (`routers/mcp.py`) for Model Context Protocol integration
- Code Mode: structured tool-calling pipeline with Docker sandbox
- `modules/query_understanding.py`: query decomposition into typed sub-queries
- `modules/hybrid_router.py`: parallel execution across data sources with context fusion
- `modules/approval_store.py`: action approval gate with hash verification and timeout
- `modules/subagents/orchestrator.py`: multi-agent orchestration with streaming
- `modules/screener/`: institutional equity screener with provenance tracking

### Changed
- Pipeline reorganized: single model call at end with full fused context (≈2× throughput)
- Rate limiter upgraded to sliding-window with Redis backend (in-memory fallback)
- Response cache keyed by `sha256(body + auth_header)` for correctness
- `pipeline.py` refactored into `pipeline/` package (sync, streaming, helpers, circuit_breaker)
- `main.py` refactored into FastAPI `APIRouter` modules under `routers/`
- Version bumped from 2.x to 3.0.0 — now derived from `pyproject.toml` via `importlib.metadata`
- Docker Compose: removed deprecated `version` key, fixed DB volume mount, added log rotation

### Fixed
- Version string drift: all endpoints now report consistent `3.0.0`
- SSE streaming blocked the event loop by calling sync I/O directly (wrapped in `asyncio.to_thread`)
- Bare `except: pass` silently swallowing errors replaced with `logger.debug` throughout
- Regex patterns in hot-path helpers pre-compiled at module load (reduces per-request overhead)
- In-memory rate limiter per-IP list unbounded growth → replaced with `deque(maxlen=RPM_LIMIT)`
- Docker DB file mount created as directory on first run → changed to directory mount

### Infrastructure
- `.dockerignore` added: model files, scratch, `__pycache__`, DB files excluded from build context
- `.env.example` added: full template for all 60+ environment variables
- `CHANGELOG.md` added
- `requirements-dev.txt` added: pytest, pytest-asyncio, ruff, bandit separated from production deps
- `tests/` directory added with unit and integration test scaffolding

## [2.0.0] — Earlier

- Initial production release with 7-agent architecture
- FastAPI backend, SQLite / SQLAlchemy, ChromaDB RAG
- GitHub and Google OAuth
- Finance module with yfinance integration
- Premium Gamma-style PDF generation
- RLHF feedback collection
- Auto-learning from high-confidence responses
