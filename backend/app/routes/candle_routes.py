"""
Candle REST Routes — Serves historical candle data and market state.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.historical_data_service import get_historical_candles

router = APIRouter()

@router.get("/candles")
async def get_candles(
    symbol: str = Query(..., description="Stock symbol, e.g. BTCUSDT"),
    interval: str = Query("1m", description="Candle interval:  1m, 5m, 15m, 1h, 4h, 1d"),
    from_ts: Optional[int] = Query(None, alias="from", description="Start Unix timestamp"),
    to_ts: Optional[int] = Query(None, alias="to", description="End Unix timestamp"),
    limit: int = Query(500, description="Max number of candles"),
) -> dict:
    """Fetch historical candles for a symbol and interval."""
    symbol = symbol.upper()
    try:
        data = await get_historical_candles(symbol, interval, from_ts, to_ts, limit)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/predict")
async def predict_candles(
    symbol: str = Query(..., description="Stock symbol, e.g. BTCUSDT")
) -> dict:
    """Fetch next 15 predicted 1m candles on demand from the ML service."""
    symbol = symbol.upper()
    try:
        from app.services.ml_integration_service import ml_service_client
        predictions = await ml_service_client.fetch_predictions(symbol)
        return {"status": "success", "predictions": predictions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Service Error: {str(e)}")

