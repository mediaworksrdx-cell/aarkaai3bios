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
MAX_TOKENS = int(os.getenv("AARKAAI_MAX_TOKENS", "2048"))

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
    "brent": "BZ=F", "brent crude": "BZ=F",
    "natural gas": "NG=F", "heating oil": "HO=F", "gasoline": "RB=F",
    # Industrial metals
    "copper": "HG=F", "aluminium": "ALI=F", "aluminum": "ALI=F",
    "zinc": "ZN=F", "nickel": "NI=F", "tin": "TIN=F", "lead": "LE=F",
    # Agricultural
    "corn": "ZC=F", "wheat": "ZW=F", "soybean": "ZS=F", "soybeans": "ZS=F",
    "rice": "ZR=F", "oats": "ZO=F",
    "sugar": "SB=F", "coffee": "KC=F", "cocoa": "CC=F", "cotton": "CT=F",
    "orange juice": "OJ=F",
    # Livestock
    "cattle": "LE=F", "live cattle": "LE=F", "lean hogs": "HE=F", "feeder cattle": "GF=F",
}
FOREX_PAIRS = {
    # Major pairs
    "eurusd": "EURUSD=X", "eur/usd": "EURUSD=X", "euro dollar": "EURUSD=X",
    "gbpusd": "GBPUSD=X", "gbp/usd": "GBPUSD=X", "pound dollar": "GBPUSD=X",
    "usdjpy": "USDJPY=X", "usd/jpy": "USDJPY=X", "dollar yen": "USDJPY=X",
    "usdchf": "USDCHF=X", "usd/chf": "USDCHF=X",
    "audusd": "AUDUSD=X", "aud/usd": "AUDUSD=X",
    "usdcad": "USDCAD=X", "usd/cad": "USDCAD=X",
    "nzdusd": "NZDUSD=X", "nzd/usd": "NZDUSD=X",
    # INR pairs (India focused)
    "usdinr": "USDINR=X", "usd/inr": "USDINR=X", "dollar rupee": "USDINR=X",
    "usd to inr": "USDINR=X", "dollar to rupee": "USDINR=X",
    "inr": "USDINR=X", "rupee": "USDINR=X",
    "eurinr": "EURINR=X", "eur/inr": "EURINR=X", "euro rupee": "EURINR=X",
    "gbpinr": "GBPINR=X", "gbp/inr": "GBPINR=X", "pound rupee": "GBPINR=X",
    "jpyinr": "JPYINR=X", "jpy/inr": "JPYINR=X", "yen rupee": "JPYINR=X",
    # Cross pairs
    "eurgbp": "EURGBP=X", "eur/gbp": "EURGBP=X",
    "eurjpy": "EURJPY=X", "eur/jpy": "EURJPY=X",
    "gbpjpy": "GBPJPY=X", "gbp/jpy": "GBPJPY=X",
    "eurchf": "EURCHF=X", "eur/chf": "EURCHF=X",
    "audjpy": "AUDJPY=X", "aud/jpy": "AUDJPY=X",
    "cadjpy": "CADJPY=X", "cad/jpy": "CADJPY=X",
    # Exotic
    "usdsgd": "USDSGD=X", "usd/sgd": "USDSGD=X",
    "usdhkd": "USDHKD=X", "usd/hkd": "USDHKD=X",
    "usdcny": "USDCNY=X", "usd/cny": "USDCNY=X", "dollar yuan": "USDCNY=X",
    "usdtry": "USDTRY=X", "usd/try": "USDTRY=X",
    "usdzar": "USDZAR=X", "usd/zar": "USDZAR=X",
    "usdmxn": "USDMXN=X", "usd/mxn": "USDMXN=X",
    "usdrub": "USDRUB=X", "usd/rub": "USDRUB=X",
    "usdaed": "USDAED=X", "usd/aed": "USDAED=X", "dollar dirham": "USDAED=X",
    "usdsar": "USDSAR=X", "usd/sar": "USDSAR=X",
    # DXY index
    "dxy": "DX-Y.NYB", "dollar index": "DX-Y.NYB", "us dollar index": "DX-Y.NYB",
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
BASE_URL = os.getenv("AARKAAI_BASE_URL", "http://43.204.153.162:5000")
HOST = os.getenv("AARKAAI_HOST", "0.0.0.0")
PORT = int(os.getenv("AARKAAI_PORT", "5000"))
WORKERS = int(os.getenv("AARKAAI_WORKERS", "1"))  # uvicorn workers (keep 1 for llama.cpp)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("AARKAAI_LOG_LEVEL", "INFO").upper()
LOG_FORMAT_JSON = IS_PRODUCTION  # JSON logs in production for parsing
