import os
from typing import List
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# API Configuration
BINANCE_REST_BASE: str = "https://api.binance.com/api/v3"
BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8000")

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
    "BTCUSDT"
]
