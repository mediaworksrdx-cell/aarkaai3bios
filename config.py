"""
AARKAAI Backend – Central Configuration

All sensitive values are loaded from environment variables.
See .env.example for the full template.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

# ─── Environment ──────────────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("AARKAAI_ENV", "development")  # "development" | "production"
IS_PRODUCTION = ENVIRONMENT == "production"
HOST = os.getenv("AARKAAI_HOST", "0.0.0.0")
PORT = int(os.getenv("AARKAAI_PORT", "5000"))
LOG_LEVEL = os.getenv("AARKAAI_LOG_LEVEL", "INFO")
WORKERS = int(os.getenv("AARKAAI_WORKERS", "1"))

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "aarkaa-3b"
DB_PATH = BASE_DIR / "aarkaai.db"
SAFE_WORK_DIR = BASE_DIR / "workspace"

# ─── Base URL & Auth Keys ──────────────────────────────────────────────────
BASE_URL = os.getenv("AARKAAI_BASE_URL", "https://synthetixanalytics.com")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

# ─── Database ─────────────────────────────────────────────────────────────────
DB_URL = os.getenv("AARKAAI_DB_URL", f"sqlite:///{DB_PATH}")
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "aarkaai")

# ─── Security & Authentication ──────────────────────────────────────────────────
SECRET_KEY = os.getenv("AARKAAI_SECRET_KEY", "dev-secret-key-do-not-use-in-prod-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AARKAAI_ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days default
API_KEY = os.getenv("AARKAAI_API_KEY", "")  # Empty = no global auth (dev only)
API_KEY_HEADER = "X-API-Key"

# ─── External AI & Search Provider Keys ───────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Not used for Vertex AI; kept for legacy fallback only
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# ─── Vertex AI / GCP Credentials ──────────────────────────────────────────────
# Path to the GCP service account JSON key file.
# The google-genai SDK (and all google-cloud-* libraries) will automatically
# pick this up via Application Default Credentials (ADC) when set.
# MUST be set via environment variable — no hardcoded fallback.
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
if GOOGLE_APPLICATION_CREDENTIALS:
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", GOOGLE_APPLICATION_CREDENTIALS)

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "orbital-heaven-504004-s2")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # Must be a valid Vertex AI model ID
# WARNING: Default changed from 'gemini-3.7-flash' (non-standard alias) to 'gemini-2.5-flash'.
# Verify the model ID is listed in your GCP Vertex AI region before deployment.
# Override via GEMINI_MODEL env var for custom internal aliases.

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

# Guard against insecure default secret key in production
_DEFAULT_KEY = "dev-secret-key-do-not-use-in-prod-change-me"
if ENVIRONMENT == "production" and SECRET_KEY == _DEFAULT_KEY:
    raise RuntimeError(
        "FATAL: AARKAAI_SECRET_KEY is using the default insecure value in production! "
        "Set a strong random secret key via the AARKAAI_SECRET_KEY environment variable."
    )

# Enforce minimum key entropy in all environments
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "FATAL: AARKAAI_SECRET_KEY is too short (minimum 32 characters). "
        "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )

# Warn if GCP credentials are missing in production
if IS_PRODUCTION and not GOOGLE_APPLICATION_CREDENTIALS:
    import warnings
    warnings.warn(
        "GOOGLE_APPLICATION_CREDENTIALS not set — Vertex AI features will be unavailable.",
        RuntimeWarning,
        stacklevel=2,
    )

# ─── OAuth Redirect Base URL ──────────────────────────────────────────────────
OAUTH_REDIRECT_BASE_URL = os.getenv("AARKAAI_OAUTH_REDIRECT_URL", BASE_URL)

# Routes that don't require API key authentication (or JWT)
PUBLIC_ROUTES = {
    "/", "/health", "/docs", "/openapi.json", "/redoc",
    "/auth/register", "/auth/login", "/auth/visitor-token",
    "/auth/github/login", "/auth/github/callback",
    "/auth/google/login", "/auth/google/callback", "/auth/google/verify", "/auth/google",
    "/download",
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
_origins_env = os.getenv("AARKAAI_ALLOWED_ORIGINS", "")
if _origins_env:
    ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",")]
elif IS_PRODUCTION:
    ALLOWED_ORIGINS = []  # Must be explicitly set in production
else:
    ALLOWED_ORIGINS = ["*"]

# ─── Rate Limiting ────────────────────────────────────────────────────────────
RATE_LIMIT_RPM = int(os.getenv("AARKAAI_RATE_LIMIT_RPM", "30"))  # Requests per minute per IP
RATE_LIMIT_ENABLED = IS_PRODUCTION or os.getenv("AARKAAI_RATE_LIMIT_ENABLED", "false").lower() == "true"

# ─── Input Validation & Generation Limits ──────────────────────────────────
MAX_QUERY_LENGTH = int(os.getenv("AARKAAI_MAX_QUERY_LENGTH", "32000"))
MAX_TOKENS = int(os.getenv("AARKAAI_MAX_TOKENS", "8192"))
TEMPERATURE = float(os.getenv("AARKAAI_TEMPERATURE", "0.7"))
RESPONSE_CACHE_TTL = int(os.getenv("AARKAAI_RESPONSE_CACHE_TTL", "60"))
VERIFIER_ENABLED = os.getenv("AARKAAI_VERIFIER_ENABLED", "false").lower() == "true"
MODEL_CONTEXT_WINDOW = int(os.getenv("AARKAAI_MODEL_CONTEXT_WINDOW", "16384"))
CONTEXT_BUDGET = int(os.getenv("AARKAAI_CONTEXT_BUDGET", "8000"))
MAX_HISTORY_CHARS = int(os.getenv("AARKAAI_MAX_HISTORY_CHARS", "6000"))

# ─── Embedding Model ─────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# ─── RAG Retrieval ───────────────────────────────────────────────────────────
RAG_SIMILARITY_THRESHOLD = float(os.getenv("AARKAAI_RAG_SIM_THRESHOLD", "0.50"))
RAG_RERANKER_THRESHOLD = float(os.getenv("AARKAAI_RAG_RERANK_THRESHOLD", "0.25"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("AARKAAI_RAG_MAX_CHARS", "6000"))
RAG_CANDIDATE_POOL_SIZE = int(os.getenv("AARKAAI_RAG_POOL_SIZE", "10"))
RAG_KEYWORD_OVERLAP_MIN = float(os.getenv("AARKAAI_RAG_KW_OVERLAP", "0.10"))
RERANKER_MODEL_NAME = os.getenv("AARKAAI_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# ─── ChromaDB Vector Store ───────────────────────────────────────────────────
CHROMA_PERSIST_DIR = os.getenv("AARKAAI_CHROMA_DIR", str(BASE_DIR / "chroma_db"))

# ─── Semantic Filter ─────────────────────────────────────────────────────────
DOMAIN_LABELS = [
    "general",
    "finance",
    "technology",
    "science",
    "health",
    "history",
    "web_search",
]

CONFIDENCE_THRESHOLD = float(os.getenv("AARKAAI_CONFIDENCE_THRESHOLD", "0.85"))
# NOTE: Values must be in [0.0, 1.0] (cosine similarity range).
# At 0.85, queries classified with ≥85% domain confidence skip the 7B synthesis pass
# and return tool/router results directly. Lower = more 7B usage, Higher = more direct returns.
# Former value was 1.1 (mathematically unreachable → dead code). Fixed.

# ─── Auto-Learning ───────────────────────────────────────────────────────────
AUTO_LEARN_INTERVAL = 15  # Trigger auto-learn every N messages
AUTO_LEARN_MIN_RESPONSE_CHARS = int(os.getenv("AARKAAI_AUTO_LEARN_MIN_RESPONSE_CHARS", "200"))
AUTO_LEARN_MIN_CONFIDENCE = float(os.getenv("AARKAAI_AUTO_LEARN_MIN_CONFIDENCE", "0.70"))

# ─── Knowledge-First Resolution (Beta — Feature-Flagged) ─────────────────────
KNOWLEDGE_FIRST_ENABLED = os.getenv("AARKAAI_KNOWLEDGE_FIRST_ENABLED", "false").lower() == "true"
KNOWLEDGE_FIRST_THRESHOLD = float(os.getenv("AARKAAI_KNOWLEDGE_FIRST_THRESHOLD", "0.75"))
KNOWLEDGE_FIRST_HISTORY_KEEPALIVE = int(os.getenv("AARKAAI_KNOWLEDGE_FIRST_HISTORY_KEEPALIVE", "5"))

# ─── Freemium / Subscription ─────────────────────────────────────────────────
FREE_TIER_STRATEGY_LIMIT = int(os.getenv("AARKAAI_FREE_STRATEGY_LIMIT", "15"))
FREE_TIER_RESET_HOURS = int(os.getenv("AARKAAI_FREE_RESET_HOURS", "5"))

# ─── Finance ─────────────────────────────────────────────────────────────────
# Common ticker patterns for extraction
CRYPTO_SUFFIXES = ["-USD", "-EUR", "-GBP"]
INDIA_SUFFIX = ".NS"
COMMODITY_TICKERS = {
    # Precious metals
    "gold": "GC=F", "silver": "SI=F", "platinum": "PL=F", "palladium": "PA=F",
    # Energy
    "oil": "CL=F", "crude": "CL=F", "crude oil": "CL=F", "wti": "CL=F",
    "brent": "BZ=F", "natural gas": "NG=F", "gas": "NG=F",
    # Agriculture
    "wheat": "ZW=F", "corn": "ZC=F", "soybeans": "ZS=F", "sugar": "SB=F", "coffee": "KC=F",
    # Industrial
    "copper": "HG=F",
}

DEFAULT_CURRENCY = "USD"

# Forex pair mapping
FOREX_PAIRS = {
    "eurusd": "EURUSD=X", "eur/usd": "EURUSD=X",
    "gbpusd": "GBPUSD=X", "gbp/usd": "GBPUSD=X",
    "usdjpy": "JPY=X",    "usd/jpy": "JPY=X",
    "usdinr": "INR=X",    "usd/inr": "INR=X",
    "audusd": "AUDUSD=X", "aud/usd": "AUDUSD=X",
}

# ─── Security Blocklist for Agent Tools ─────────────────────────────────────
BASH_TIMEOUT = float(os.getenv("AARKAAI_BASH_TIMEOUT", "30.0"))
# DEPRECATED: Blocklist replaced by allowlist architecture in modules/tools/bash.py
# Kept as empty list for backward compatibility with any code referencing it.
BASH_BLOCKLIST: list[str] = []

# ─── Upload Restrictions ─────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = int(os.getenv("AARKAAI_MAX_UPLOAD_SIZE_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".csv", ".xlsx", ".xls", ".txt", ".json", ".md",
    ".png", ".jpg", ".jpeg", ".docx", ".html",
}

# ─── Hybrid Query Router ─────────────────────────────────────────────────────
# Feature flag: when False, the existing pipeline.py waterfall is used unchanged.
# When True, queries are routed through the new HybridQueryRouter with parallel
# data source execution.  Default is False for safe, gradual rollout.
HQR_ENABLED = os.getenv("AARKAAI_HQR_ENABLED", "false").lower() == "true"
HQR_MAX_WORKERS = int(os.getenv("AARKAAI_HQR_MAX_WORKERS", "6"))
HQR_MARKET_TIMEOUT = float(os.getenv("AARKAAI_HQR_MARKET_TIMEOUT", "8.0"))
HQR_WEB_TIMEOUT = float(os.getenv("AARKAAI_HQR_WEB_TIMEOUT", "8.0"))
HQR_NEWS_TIMEOUT = float(os.getenv("AARKAAI_HQR_NEWS_TIMEOUT", "6.0"))
HQR_DB_TIMEOUT = float(os.getenv("AARKAAI_HQR_DB_TIMEOUT", "3.0"))
HQR_RAG_TIMEOUT = float(os.getenv("AARKAAI_HQR_RAG_TIMEOUT", "8.0"))
HQR_TOOL_TIMEOUT = float(os.getenv("AARKAAI_HQR_TOOL_TIMEOUT", "10.0"))
HQR_CONTEXT_BUDGET = int(os.getenv("AARKAAI_HQR_CONTEXT_BUDGET", "24000"))
HQR_ENABLE_PARALLEL = os.getenv("AARKAAI_HQR_PARALLEL", "true").lower() == "true"
# Confidence threshold below which simple data-only queries (e.g. "SBI price")
# can return tool results directly without a 7B synthesis pass.
HQR_BYPASS_LLM_THRESHOLD = float(os.getenv("AARKAAI_HQR_BYPASS_THRESHOLD", "0.92"))

# ─── Modal Serverless GPU Engine ─────────────────────────────────────────────
MODAL_GPU_ENDPOINT = os.getenv(
    "MODAL_GPU_ENDPOINT",
    "https://mediaworksr--aarkaa-inference-aarkaagpu-endpoint.modal.run"
)
MODAL_GPU_ENABLED = os.getenv("MODAL_GPU_ENABLED", "true").lower() == "true"

# ─── Context Compaction ──────────────────────────────────────────────────────
COMPACTION_ENABLED = os.getenv("AARKAAI_COMPACTION_ENABLED", "true").lower() == "true"
COMPACTION_TRIGGER_RATIO = float(os.getenv("AARKAAI_COMPACTION_TRIGGER", "0.80"))
COMPACTION_PRESERVE_TURNS = int(os.getenv("AARKAAI_COMPACTION_PRESERVE_TURNS", "3"))
RESERVED_OUTPUT_TOKENS = int(os.getenv("AARKAAI_RESERVED_OUTPUT_TOKENS", "2048"))

# ─── KV-Cache Prefix Stability ──────────────────────────────────────────────
KV_PREFIX_CACHE_ENABLED = os.getenv("AARKAAI_KV_PREFIX_CACHE", "true").lower() == "true"
KV_CACHE_DIAGNOSTICS = os.getenv("AARKAAI_KV_CACHE_DIAGNOSTICS", "false").lower() == "true"

# ─── Code Mode / Programmatic Tool Calling (Stage 1 Hardened) ───────────────
CODE_MODE_ENABLED = os.getenv("AARKAAI_CODE_MODE_ENABLED", "false").lower() == "true"
CODE_MODE_TIMEOUT = float(os.getenv("AARKAAI_CODE_MODE_TIMEOUT", "30.0"))
CODE_MODE_MAX_TOOL_CALLS = int(os.getenv("AARKAAI_CODE_MODE_MAX_CALLS", "15"))
CODE_MODE_SANDBOX_BACKEND = os.getenv("AARKAAI_CODE_MODE_SANDBOX", "docker")
CODE_MODE_MAX_OUTPUT_BYTES = int(os.getenv("AARKAAI_CODE_MODE_MAX_OUTPUT", str(1024 * 1024)))
CODE_MODE_MAX_MEMORY_MB = int(os.getenv("AARKAAI_CODE_MODE_MAX_MEMORY", "512"))
CODE_MODE_DOCKER_IMAGE = os.getenv(
    "AARKAAI_CODE_MODE_IMAGE",
    "aarkaa-sandbox:3.11.8-hardened"
)
CODE_MODE_CONTAINER_USER = "10001:10001"
CODE_MODE_CPU_LIMIT = "1.0"
CODE_MODE_PIDS_LIMIT = 32
CODE_MODE_MAX_SCRIPT_BYTES = 65536  # 64 KB
CODE_MODE_MAX_WORKSPACE_BYTES = 104857600  # 100 MB
CODE_MODE_MAX_WORKSPACE_FILES = 1000
CODE_MODE_CI_SIGNING_KEY = os.getenv("AARKAAI_CI_SIGNING_KEY", "")
CODE_MODE_CI_NONCE_DB = str(BASE_DIR / "var" / "ci_nonces.db")

# ─── MCP Client (Stage 1 Hardened) ──────────────────────────────────────────
MCP_ENABLED = os.getenv("AARKAAI_MCP_ENABLED", "false").lower() == "true"
MCP_CONFIG_PATH = os.getenv("AARKAAI_MCP_CONFIG", str(BASE_DIR / "mcp_config.yaml"))
MCP_ADMIN_ALLOWED_BINARIES = {
    # Populated by system administrator in production deployments
}
MCP_SSRF_BLOCKED_CIDRS = [
    "127.0.0.0/8", "::1/128",
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "169.254.0.0/16", "fe80::/10",
    "224.0.0.0/4", "ff00::/8",
    "fd00::/8", "169.254.169.254/32"
]

