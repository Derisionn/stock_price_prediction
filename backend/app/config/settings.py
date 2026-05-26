import os
from typing import List
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# API Configuration
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_REST_BASE: str = "https://finnhub.io/api/v1"
FINNHUB_WS_URL: str = "wss://ws.finnhub.io"

# CORS Configuration
# In production, set CORS_ALLOW_ORIGINS env var as a comma-separated list.
# e.g. "https://tradepro.vercel.app,https://my-custom-domain.com"
_raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
CORS_ALLOW_ORIGINS: List[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins
    else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]
)

# Default Trading Symbols
DEFAULT_SYMBOLS: List[str] = [
    "TSLA"
]
