"""
WebSocket Connection Manager
Manages all active frontend WebSocket connections.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections from frontend clients."""

    def __init__(self) -> None:
        # Map of symbol -> set of WebSocket connections subscribed to it
        self._subscriptions: Dict[str, Set[WebSocket]] = {}
        # Map of websocket -> set of symbols it's subscribed to
        self._client_symbols: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self._client_symbols[websocket] = set()
        logger.info(f"Client connected. Total clients: {len(self._client_symbols)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and clean up subscriptions."""
        symbols = self._client_symbols.pop(websocket, set())
        for symbol in symbols:
            self._subscriptions.get(symbol, set()).discard(websocket)
            if not self._subscriptions.get(symbol):
                self._subscriptions.pop(symbol, None)
        logger.info(f"Client disconnected. Total clients: {len(self._client_symbols)}")

    def subscribe(self, websocket: WebSocket, symbol: str) -> None:
        """Subscribe a client to a symbol."""
        if symbol not in self._subscriptions:
            self._subscriptions[symbol] = set()
        self._subscriptions[symbol].add(websocket)
        self._client_symbols[websocket].add(symbol)
        logger.debug(f"Client subscribed to {symbol}")

    def unsubscribe(self, websocket: WebSocket, symbol: str) -> None:
        """Unsubscribe a client from a symbol."""
        self._subscriptions.get(symbol, set()).discard(websocket)
        self._client_symbols.get(websocket, set()).discard(symbol)

    def get_all_subscribed_symbols(self) -> Set[str]:
        """Return all symbols that any client is subscribed to."""
        return set(self._subscriptions.keys())

    async def broadcast_to_symbol(self, symbol: str, data: dict) -> None:
        """Send a message to all clients subscribed to a symbol."""
        subscribers = self._subscriptions.get(symbol, set()).copy()
        if not subscribers:
            return
        message = json.dumps(data)
        dead_connections: list[WebSocket] = []
        for websocket in subscribers:
            try:
                await websocket.send_text(message)
            except Exception:
                dead_connections.append(websocket)

        for ws in dead_connections:
            self.disconnect(ws)

    async def broadcast_all(self, data: dict) -> None:
        """Send a message to all connected clients."""
        message = json.dumps(data)
        dead: list[WebSocket] = []
        for websocket in list(self._client_symbols.keys()):
            try:
                await websocket.send_text(message)
            except Exception:
                dead.append(websocket)
        for ws in dead:
            self.disconnect(ws)

    @property
    def active_connections_count(self) -> int:
        return len(self._client_symbols)


# Global singleton
manager = ConnectionManager()
