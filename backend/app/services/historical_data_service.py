import logging
import time
from typing import List, Optional
import httpx

from app.config.settings import BINANCE_REST_BASE
from app.services.candle_aggregation_service import candle_service

logger = logging.getLogger(__name__)

# Binance resolution mapping
INTERVAL_TO_RESOLUTION = {
    "1s":  "1s",
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "1h":  "1h",
    "4h":  "4h",
    "1d":  "1d",
}

async def get_historical_candles(
    symbol: str, 
    interval: str, 
    from_ts: Optional[int], 
    to_ts: Optional[int], 
    limit: int
) -> dict:
    """Fetch historical candles from memory or Binance."""
    if interval not in INTERVAL_TO_RESOLUTION:
        raise ValueError(f"Invalid interval. Use: {list(INTERVAL_TO_RESOLUTION.keys())}")

    # Check if we have live/seeded data in memory (at least 100 candles)
    in_memory = candle_service.get_candles(symbol, interval, limit=limit)
    if len(in_memory) >= 100:
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": [c.to_dict() for c in in_memory],
            "source": "live",
        }

    # Fetch historical data using Binance REST API
    binance_interval = INTERVAL_TO_RESOLUTION[interval]
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            params = {
                "symbol": symbol.upper(),
                "interval": binance_interval,
                "limit": min(limit, 1000)
            }
            if from_ts:
                params["startTime"] = from_ts * 1000
            if to_ts:
                params["endTime"] = to_ts * 1000
                
            resp = await client.get(f"{BINANCE_REST_BASE}/klines", params=params)
            resp.raise_for_status()
            data = resp.json()
            
            candles = []
            for row in data:
                # row[0] is open time in ms
                ts = int(row[0]) // 1000
                candles.append({
                    "time": ts,
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                })
            
            # Seed the aggregation service
            if candles:
                candle_service.seed_historical(symbol, interval, candles)
                
            return {
                "symbol": symbol,
                "interval": interval,
                "candles": candles,
                "source": "binance",
            }
    except Exception as e:
        logger.error(f"Binance API error: {e}")

    # If no data is available, return empty
    return {
        "symbol": symbol,
        "interval": interval,
        "candles": [],
        "source": "none",
    }
