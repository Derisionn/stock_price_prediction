"""
Binance WebSocket Client
Connects to Binance's realtime trade stream and feeds ticks to the aggregation service.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time as time_module
from typing import Set

import websockets

from app.config.settings import BINANCE_WS_URL
from app.services.candle_aggregation_service import candle_service

logger = logging.getLogger(__name__)

class BinanceWSClient:
    """
    Persistent async WebSocket client that connects to Binance's trade stream.
    Automatically reconnects on disconnect with exponential backoff.
    """

    def __init__(self) -> None:
        self._subscribed_symbols: Set[str] = set()
        self._websocket = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self._task: asyncio.Task | None = None
        self._subscription_id = 1

    def add_symbol(self, symbol: str) -> None:
        self._subscribed_symbols.add(symbol.upper())

    def remove_symbol(self, symbol: str) -> None:
        self._subscribed_symbols.discard(symbol.upper())

    async def start(self) -> None:
        """Start the Binance WebSocket client as a background task."""
        self._running = True
        self._task = asyncio.create_task(self._run_with_reconnect())

    async def stop(self) -> None:
        """Stop the client gracefully."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
        if self._task:
            self._task.cancel()

    async def _run_with_reconnect(self) -> None:
        """Connect and reconnect with exponential backoff."""
        while self._running:
            try:
                await self._connect()
                self._reconnect_delay = 1.0  # reset on successful connection
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Binance WS error: {e}. Reconnecting in {self._reconnect_delay}s")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )

    async def _connect(self) -> None:
        """Establish connection and process messages."""
        logger.info("Connecting to Binance WebSocket...")

        async with websockets.connect(BINANCE_WS_URL, ping_interval=20, ping_timeout=10) as ws:
            self._websocket = ws
            logger.info("Connected to Binance WebSocket")

            # Subscribe to all current symbols
            if self._subscribed_symbols:
                await self._subscribe_all(ws)

            async for message in ws:
                await self._handle_message(message)

    async def _subscribe_all(self, ws) -> None:
        """Send subscription message for all symbols."""
        params = [f"{sym.lower()}@aggTrade" for sym in self._subscribed_symbols]
        payload = json.dumps({
            "method": "SUBSCRIBE",
            "params": params,
            "id": self._subscription_id
        })
        self._subscription_id += 1
        await ws.send(payload)
        logger.debug(f"Subscribed to Binance streams: {params}")

    async def _handle_message(self, raw: str) -> None:
        """Parse and process a Binance trade message."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("e")

        if msg_type == "aggTrade":
            symbol = data.get("s", "")
            price = float(data.get("p", 0))
            volume = float(data.get("q", 0))
            timestamp_ms = int(data.get("T", time_module.time() * 1000))

            if price > 0 and symbol:
                await candle_service.process_trade(
                    symbol=symbol,
                    price=price,
                    volume=volume,
                    timestamp_ms=timestamp_ms,
                )

# Global singleton
binance_client = BinanceWSClient()
