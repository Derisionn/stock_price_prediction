"""
Broadcaster — convenience functions that bridge the aggregation service
and the connection manager. Called from candle callbacks.
"""
from __future__ import annotations

import logging

from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)


async def broadcast_candle_update(
    symbol: str,
    interval: str,
    candle,
    is_new: bool,
) -> None:
    """
    Called by CandleAggregationService whenever a candle is updated.
    Broadcasts the update to all subscribed frontend clients.
    """
    message = {
        "type": "candle_update",
        "symbol": symbol,
        "interval": interval,
        "candle": candle.to_dict(),
        "is_new": is_new,
    }
    await manager.broadcast_to_symbol(symbol, message)


async def broadcast_prediction_update(
    symbol: str,
    predictions: list,
) -> None:
    """
    Called by MLIntegrationService when new predictions are available.
    Broadcasts the future predicted candles to all subscribed clients.
    """
    message = {
        "type": "ml_prediction_update",
        "symbol": symbol,
        "predictions": predictions,
    }
    await manager.broadcast_to_symbol(symbol, message)
