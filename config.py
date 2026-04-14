"""
AARKAAI Backend – Central Configuration

All sensitive values are loaded from environment variables.
See .env.example for the full template.
"""
import os
from pathlib import Path

# ─── Environment ──────────────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("AARKAAI_ENV", "development")  # "development" | "production"
IS_PRODUCTION = ENVIRONMENT == "production"

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "aarkaa-3b"
DB_PATH = BASE_DIR / "aarkaai.db"

# ─── Database ─────────────────────────────────────────────────────────────────
DB_URL = os.getenv("AARKAAI_DB_URL", f"sqlite:///{DB_PATH}")

# ─── Security & Authentication ──────────────────────────────────────────────────
SECRET_KEY = os.getenv("AARKAAI_SECRET_KEY", "dev-secret-key-do-not-use-in-prod-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AARKAAI_ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days default
API_KEY = os.getenv("AARKAAI_API_KEY", "")  # Empty = no global auth (dev only)
API_KEY_HEADER = "X-API-Key"

# Routes that don't require API key authentication (or JWT)
PUBLIC_ROUTES = {"/", "/health", "/docs", "/openapi.json", "/redoc", "/auth/register", "/auth/login"}

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
MAX_QUERY_LENGTH = int(os.getenv("AARKAAI_MAX_QUERY_LENGTH", "2000"))

# ─── Embedding Model ─────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

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

CONFIDENCE_THRESHOLD = 0.7  # Above this → return AARKAA-3B primary answer directly

# ─── Auto-Learning ───────────────────────────────────────────────────────────
AUTO_LEARN_INTERVAL = 15  # Trigger auto-learn every N messages

# ─── Finance ─────────────────────────────────────────────────────────────────
# Common ticker patterns for extraction
CRYPTO_SUFFIXES = ["-USD", "-EUR", "-GBP"]
INDIA_SUFFIX = ".NS"
COMMODITY_TICKERS = {
    "gold": "GC=F",
    "silver": "SI=F",
    "oil": "CL=F",
    "crude": "CL=F",
    "natural gas": "NG=F",
    "platinum": "PL=F",
    "copper": "HG=F",
}
FOREX_PAIRS = {
    "eurusd": "EURUSD=X",
    "gbpusd": "GBPUSD=X",
    "usdjpy": "USDJPY=X",
    "usdcad": "USDCAD=X",
    "audusd": "AUDUSD=X",
    "usdinr": "USDINR=X",
}

# ─── Web Search ───────────────────────────────────────────────────────────────
WEB_SEARCH_MAX_RESULTS = 5
WIKIPEDIA_SENTENCES = 5

# ─── Tool Sandboxing ─────────────────────────────────────────────────────────
# Agent tools can only operate within this directory
SAFE_WORK_DIR = Path(os.getenv("AARKAAI_SAFE_DIR", str(BASE_DIR / "workspace")))
BASH_TIMEOUT = int(os.getenv("AARKAAI_BASH_TIMEOUT", "30"))

# Commands that are NEVER allowed through BashTool
BASH_BLOCKLIST = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=",
    "shutdown", "reboot", "halt", "poweroff",
    "chmod 777", "curl | bash", "wget | bash",
    "curl | sh", "wget | sh", "> /dev/sda",
    ":(){ :|:& };:", "fork bomb",
    "passwd", "useradd", "userdel", "groupadd",
    "iptables", "ufw", "systemctl disable",
]

# ─── Server ───────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("AARKAAI_BASE_URL", "http://3.108.34.65:5000")
HOST = os.getenv("AARKAAI_HOST", "0.0.0.0")
PORT = int(os.getenv("AARKAAI_PORT", "5000"))
WORKERS = int(os.getenv("AARKAAI_WORKERS", "1"))  # uvicorn workers (keep 1 for llama.cpp)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("AARKAAI_LOG_LEVEL", "INFO").upper()
LOG_FORMAT_JSON = IS_PRODUCTION  # JSON logs in production for parsing
