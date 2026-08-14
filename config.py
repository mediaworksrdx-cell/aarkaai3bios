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

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # Must be a valid Vertex AI model ID
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

# Guard against insecure default secret key in production
_DEFAULT_KEY = "dev-secret-key-do-not-use-in-prod-change-me"
if ENVIRONMENT == "production" and SECRET_KEY == _DEFAULT_KEY:
    raise RuntimeError(
        "FATAL: AARKAAI_SECRET_KEY is using the default insecure value in production! "
        "Set a strong random secret key via the AARKAAI_SECRET_KEY environment variable."
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
    "/auth/register", "/auth/login",
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

# ─── Input Validation ────────────────────────────────────────────────────────
MAX_QUERY_LENGTH = int(os.getenv("AARKAAI_MAX_QUERY_LENGTH", "32000"))
MAX_TOKENS = int(os.getenv("AARKAAI_MAX_TOKENS", "1536"))

# ─── Embedding Model ─────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# ─── RAG Retrieval ───────────────────────────────────────────────────────────
RAG_SIMILARITY_THRESHOLD = float(os.getenv("AARKAAI_RAG_SIM_THRESHOLD", "0.50"))
RAG_RERANKER_THRESHOLD = float(os.getenv("AARKAAI_RAG_RERANK_THRESHOLD", "0.25"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("AARKAAI_RAG_MAX_CHARS", "1500"))
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

CONFIDENCE_THRESHOLD = 1.1  # 1.1 guarantees all final answers are generated by the 7B model (3B acts purely as router/helper)

# ─── Auto-Learning ───────────────────────────────────────────────────────────
AUTO_LEARN_INTERVAL = 15  # Trigger auto-learn every N messages

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
BASH_BLOCKLIST = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){ :|:& };:", 
    "chmod -R 777 /", "shutdown", "reboot", "poweroff"
]

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
HQR_MARKET_TIMEOUT = float(os.getenv("AARKAAI_HQR_MARKET_TIMEOUT", "5.0"))
HQR_WEB_TIMEOUT = float(os.getenv("AARKAAI_HQR_WEB_TIMEOUT", "8.0"))
HQR_NEWS_TIMEOUT = float(os.getenv("AARKAAI_HQR_NEWS_TIMEOUT", "6.0"))
HQR_DB_TIMEOUT = float(os.getenv("AARKAAI_HQR_DB_TIMEOUT", "3.0"))
HQR_RAG_TIMEOUT = float(os.getenv("AARKAAI_HQR_RAG_TIMEOUT", "3.0"))
HQR_TOOL_TIMEOUT = float(os.getenv("AARKAAI_HQR_TOOL_TIMEOUT", "10.0"))
HQR_CONTEXT_BUDGET = int(os.getenv("AARKAAI_HQR_CONTEXT_BUDGET", "6000"))
HQR_ENABLE_PARALLEL = os.getenv("AARKAAI_HQR_PARALLEL", "true").lower() == "true"
# Confidence threshold below which simple data-only queries (e.g. "SBI price")
# can return tool results directly without a 7B synthesis pass.
HQR_BYPASS_LLM_THRESHOLD = float(os.getenv("AARKAAI_HQR_BYPASS_THRESHOLD", "0.92"))
