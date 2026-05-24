"""
WebSocket Routes — Handles frontend WebSocket connections.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket

from app.websocket.handler import handle_websocket_connection

router = APIRouter()

@router.websocket("/ws/stocks")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for frontend clients.
    
    Protocol:
      Client sends: { "type": "subscribe", "symbol": "AAPL" }
      Client sends: { "type": "unsubscribe", "symbol": "AAPL" }
      Server sends: { "type": "candle_update", "symbol": ..., "interval": ..., "candle": {...}, "is_new": bool }
    """
    await handle_websocket_connection(websocket)

