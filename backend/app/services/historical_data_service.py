import logging
import os
import time
from typing import List, Optional

from app.config.settings import FINNHUB_API_KEY, FINNHUB_REST_BASE
from app.services.candle_aggregation_service import candle_service, TIMEFRAME_SECONDS

logger = logging.getLogger(__name__)

# Finnhub resolution mapping
INTERVAL_TO_RESOLUTION = {
    "1s":  "1", # Finnhub doesn't support 1s, we use 1m resolution but bypass finnhub call
    "1m":  "1",
    "5m":  "5",
    "15m": "15",
    "1h":  "60",
    "4h":  "240",
    "1d":  "D",
}

def generate_simulated_candles(symbol: str, interval: str, count: int = 500) -> List[dict]:
    """Generate realistic simulated candle data for demo mode."""
    import random
    import math

    interval_sec = TIMEFRAME_SECONDS.get(interval, 60)
    now = int(time.time())
    # Align to interval boundary
    now_aligned = (now // interval_sec) * interval_sec

    base_prices = {
        "AAPL": 185.0, "TSLA": 240.0, "MSFT": 420.0,
        "GOOGL": 175.0, "AMZN": 195.0, "NVDA": 950.0,
        "META": 520.0, "BRK.B": 420.0, "JPM": 200.0, "V": 280.0,
    }
    base_price = base_prices.get(symbol, 100.0)

    candles = []
    price = base_price * random.uniform(0.85, 1.15)

    for i in range(count):
        ts = now_aligned - (count - 1 - i) * interval_sec
        # Add sinusoidal trend + noise
        trend = math.sin(i / 50) * base_price * 0.02
        change = random.gauss(0, base_price * 0.005) + trend * 0.01
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + abs(random.gauss(0, base_price * 0.002))
        low_price = min(open_price, close_price) - abs(random.gauss(0, base_price * 0.002))
        volume = random.uniform(50000, 500000)

        candles.append({
            "time": ts,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 0),
        })
        price = close_price

    return candles

async def get_historical_candles(
    symbol: str, 
    interval: str, 
    from_ts: Optional[int], 
    to_ts: Optional[int], 
    limit: int
) -> dict:
    """Fetch historical candles from memory, Finnhub, or simulation."""
    if interval not in INTERVAL_TO_RESOLUTION:
        raise ValueError(f"Invalid interval. Use: {list(INTERVAL_TO_RESOLUTION.keys())}")

    # Check if we have live/seeded data in memory
    in_memory = candle_service.get_candles(symbol, interval, limit=limit)
    if in_memory:
        return {
            "symbol": symbol,
            "interval": interval,
            "candles": [c.to_dict() for c in in_memory],
            "source": "live",
        }

    # Try Finnhub REST API
    if interval != "1s" and FINNHUB_API_KEY and FINNHUB_API_KEY != "your_finnhub_api_key_here":
        try:
            resolution = INTERVAL_TO_RESOLUTION[interval]
            now = int(time.time())
            interval_sec = TIMEFRAME_SECONDS[interval]
            from_time = from_ts or (now - interval_sec * limit)
            to_time = to_ts or now

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{FINNHUB_REST_BASE}/stock/candle",
                    params={
                        "symbol": symbol,
                        "resolution": resolution,
                        "from": from_time,
                        "to": to_time,
                        "token": FINNHUB_API_KEY,
                    },
                )
                data = resp.json()

            if data.get("s") == "ok":
                candles = []
                for i, ts in enumerate(data["t"]):
                    candles.append({
                        "time": ts,
                        "open": data["o"][i],
                        "high": data["h"][i],
                        "low": data["l"][i],
                        "close": data["c"][i],
                        "volume": data["v"][i],
                    })

                # Seed the aggregation service
                candle_service.seed_historical(symbol, interval, candles)
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "candles": candles,
                    "source": "finnhub",
                }
            else:
                logger.warning(f"Finnhub returned no data for {symbol}/{interval}: {data.get('s')}")
        except Exception as e:
            logger.error(f"Finnhub REST error: {e}")

    # Fallback: simulate data
    candles = generate_simulated_candles(symbol, interval, count=min(limit, 500))
    candle_service.seed_historical(symbol, interval, candles)

    return {
        "symbol": symbol,
        "interval": interval,
        "candles": candles,
        "source": "simulated",
    }
