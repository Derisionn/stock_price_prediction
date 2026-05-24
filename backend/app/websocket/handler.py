import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.websocket.connection_manager import manager
from app.providers.finnhub_ws_client import finnhub_client

logger = logging.getLogger(__name__)

async def handle_websocket_connection(websocket: WebSocket) -> None:
    """Handle incoming WebSocket connection messages from frontend clients."""
    await manager.connect(websocket)
    logger.info("Frontend WebSocket client connected")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            symbol = msg.get("symbol", "").upper()

            if msg_type == "subscribe" and symbol:
                manager.subscribe(websocket, symbol)
                finnhub_client.add_symbol(symbol)
                logger.info(f"Client subscribed to symbol: {symbol}")
                # Send acknowledgment
                await websocket.send_text(
                    json.dumps({
                        "type": "subscribed",
                        "symbol": symbol,
                        "message": f"Subscribed to {symbol}",
                    })
                )

            elif msg_type == "unsubscribe" and symbol:
                manager.unsubscribe(websocket, symbol)
                logger.info(f"Client unsubscribed from symbol: {symbol}")

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Frontend WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
