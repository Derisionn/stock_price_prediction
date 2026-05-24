"""
Finnhub WebSocket Client
Connects to Finnhub's realtime trade stream and feeds ticks to the aggregation service.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time as time_module
from typing import Set

import websockets
from websockets.exceptions import ConnectionClosed

from app.config.settings import FINNHUB_API_KEY, FINNHUB_WS_URL
from app.services.candle_aggregation_service import candle_service

logger = logging.getLogger(__name__)




class FinnhubWSClient:
    """
    Persistent async WebSocket client that connects to Finnhub's trade stream.
    Automatically reconnects on disconnect with exponential backoff.
    """

    def __init__(self) -> None:
        self._api_key: str = FINNHUB_API_KEY
        self._subscribed_symbols: Set[str] = set()
        self._websocket = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self._task: asyncio.Task | None = None

    def add_symbol(self, symbol: str) -> None:
        self._subscribed_symbols.add(symbol)

    def remove_symbol(self, symbol: str) -> None:
        self._subscribed_symbols.discard(symbol)

    async def start(self) -> None:
        """Start the Finnhub WebSocket client as a background task."""
        if not self._api_key or self._api_key == "your_finnhub_api_key_here":
            logger.warning(
                "FINNHUB_API_KEY not set. Real-time data will be simulated. "
                "Set your key in backend/.env to enable live data."
            )
            self._task = asyncio.create_task(self._simulate_trades())
        else:
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
                logger.error(f"Finnhub WS error: {e}. Reconnecting in {self._reconnect_delay}s")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )

    async def _connect(self) -> None:
        """Establish connection and process messages."""
        url = f"{FINNHUB_WS_URL}?token={self._api_key}"
        logger.info("Connecting to Finnhub WebSocket...")

        async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
            self._websocket = ws
            logger.info("Connected to Finnhub WebSocket")

            # Subscribe to all current symbols
            for symbol in self._subscribed_symbols:
                await self._subscribe(ws, symbol)

            async for message in ws:
                await self._handle_message(message)

    async def _subscribe(self, ws, symbol: str) -> None:
        """Send subscription message for a symbol."""
        payload = json.dumps({"type": "subscribe", "symbol": symbol})
        await ws.send(payload)
        logger.debug(f"Subscribed to Finnhub symbol: {symbol}")

    async def _handle_message(self, raw: str) -> None:
        """Parse and process a Finnhub trade message."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "trade":
            trades = data.get("data", [])
            for trade in trades:
                symbol = trade.get("s", "")
                price = float(trade.get("p", 0))
                volume = float(trade.get("v", 0))
                timestamp_ms = int(trade.get("t", time_module.time() * 1000))

                if price > 0 and symbol:
                    await candle_service.process_trade(
                        symbol=symbol,
                        price=price,
                        volume=volume,
                        timestamp_ms=timestamp_ms,
                    )

        elif msg_type == "error":
            logger.error(f"Finnhub error: {data.get('msg')}")

        elif msg_type == "ping":
            if self._websocket:
                await self._websocket.send(json.dumps({"type": "pong"}))

    async def _simulate_trades(self) -> None:
        """
        Simulate realistic trade data when no API key is configured.
        Generates trades for default symbols using a random walk.
        """
        import random

        logger.info("Starting trade simulation (no Finnhub API key configured)")

        # Initial prices
        prices = {
            "AAPL": 185.0,
            "TSLA": 240.0,
            "MSFT": 420.0,
            "GOOGL": 175.0,
            "AMZN": 195.0,
            "NVDA": 950.0,
            "BTC": 67000.0,
        }

        while True:
            now_ms = int(time_module.time() * 1000)
            for symbol, price in prices.items():
                # Random walk: ±0.05% per tick
                change_pct = random.uniform(-0.0005, 0.0005)
                new_price = price * (1 + change_pct)
                prices[symbol] = round(new_price, 2)
                volume = random.uniform(10, 500)

                await candle_service.process_trade(
                    symbol=symbol,
                    price=new_price,
                    volume=volume,
                    timestamp_ms=now_ms,
                )

            await asyncio.sleep(0.5)  # 2 ticks/second


# Global singleton
finnhub_client = FinnhubWSClient()
