"""
ML Integration Service
Handles on-demand prediction requests to the external ML model API.
"""
from __future__ import annotations

import logging
import asyncio
import httpx
from datetime import datetime
from typing import Optional

from app.config.settings import ML_SERVICE_URL
from app.services.candle_aggregation_service import candle_service

logger = logging.getLogger(__name__)

class MLIntegrationService:
    def __init__(self):
        # We will use an async httpx client
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Initialize HTTP client."""
        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"MLIntegrationService started. ML_SERVICE_URL={ML_SERVICE_URL}")
        print(f"🚀 ML Integration Service connected. URL: {ML_SERVICE_URL}")

    async def stop(self):
        """Clean up HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("MLIntegrationService stopped.")

    async def fetch_predictions(self, symbol: str) -> list[dict]:
        """
        Fetches predictions from the ML service on demand.
        Returns the formatted prediction candles.
        """
        # Fetch up to 350 completed candles + 1 active.
        limit = 350
        all_candles = candle_service.get_candles(symbol, "1m", limit=limit)
        
        # We exclude the very last candle if it's the newly started active candle
        if len(all_candles) > 1:
            completed_candles = all_candles[:-1]
        else:
            completed_candles = []

        # The ML model needs at least 250-300 candles
        if len(completed_candles) < 250:
            raise ValueError(f"Not enough 1m candles for {symbol} to run ML prediction (have {len(completed_candles)}, need 250+)")

        # Ensure we send the most recent 300 candles
        recent_candles = completed_candles[-300:]
        
        payload_candles = []
        for c in recent_candles:
            # Convert timestamp to ISO string as expected by ML service
            ts_iso = datetime.utcfromtimestamp(c.time).isoformat() + "Z"
            payload_candles.append({
                "timestamp": ts_iso,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume
            })

        payload = {
            "candles": payload_candles
        }

        if not self._client:
            raise Exception("ML Integration Service HTTP client not initialized")
            
        print(f"⏱️ Fetching ML predictions for {symbol} on demand...")
        
        try:
            response = await self._client.post(f"{ML_SERVICE_URL}/predict", json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success" and "predictions" in data:
                raw_predictions = data["predictions"]
                
                # Map to standard Candle format expected by frontend
                formatted_predictions = []
                for p in raw_predictions:
                    # Parse timestamp (e.g. "2023-01-01 00:01:00") and assume it's UTC
                    dt = datetime.strptime(p["timestamp"], "%Y-%m-%d %H:%M:%S")
                    from datetime import timezone
                    unix_time = int(dt.replace(tzinfo=timezone.utc).timestamp())
                    
                    formatted_predictions.append({
                        "time": unix_time,
                        "open": p.get("Open", 0.0),
                        "high": p.get("High", 0.0),
                        "low": p.get("Low", 0.0),
                        "close": p.get("Close", 0.0),
                        "volume": p.get("Volume", 0.0),
                    })
                    
                print(f"🎯 Successfully mapped {len(formatted_predictions)} predictions for {symbol}.")
                return formatted_predictions
            else:
                logger.warning(f"ML prediction failed or invalid format: {data}")
                raise Exception(f"ML Prediction invalid format: {data}")
                
        except Exception as e:
            logger.error(f"Error fetching ML predictions for {symbol}: {e}")
            raise e

# Global singleton
ml_service_client = MLIntegrationService()
