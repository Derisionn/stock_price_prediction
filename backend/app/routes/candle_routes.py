"""
Candle REST Routes — Serves historical candle data and market state.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.historical_data_service import get_historical_candles
from app.services.market_state_service import get_market_state
from app.services.symbol_service import get_supported_symbols

router = APIRouter()

@router.get("/candles")
async def get_candles(
    symbol: str = Query(..., description="Stock symbol, e.g. AAPL"),
    interval: str = Query("1m", description="Candle interval: 1m, 5m, 15m, 1h, 4h, 1d"),
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


@router.get("/market-state")
async def market_state() -> dict:
    """Returns current market open/closed state."""
    return get_market_state()


@router.get("/symbols")
async def get_symbols(q: Optional[str] = Query(None, description="Search query")) -> dict:
    """Return list of supported symbols."""
    return {"symbols": get_supported_symbols(q)}

@router.get("/predict")
async def get_prediction(
    symbol: str = Query(..., description="Stock symbol, e.g. AAPL"),
    interval: str = Query("1m", description="Candle interval"),
    steps: int = Query(15, description="Number of future candles to predict")
) -> dict:
    """Predict future candles using ML LSTM model."""
    symbol = symbol.upper()
    try:
        from app.ml.service import ml_service
        # fetch last 150 candles for training/prediction
        data = await get_historical_candles(symbol, interval, None, None, limit=150)
        candles = data["candles"]
        
        predictions = ml_service.predict(symbol, interval, candles, steps=steps)
        return {
            "symbol": symbol,
            "interval": interval,
            "predictions": predictions
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
