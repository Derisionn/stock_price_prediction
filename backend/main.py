"""
FastAPI Application — Main entrypoint.
Wires together: CORS, routes, WebSocket, Finnhub client, candle service.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import CORS_ALLOW_ORIGINS, DEFAULT_SYMBOLS

from app.routes.candle_routes import router as candle_router
from app.routes.websocket_routes import router as ws_router
from app.providers.binance_ws_client import binance_client
from app.services.candle_aggregation_service import candle_service
from app.services.ml_integration_service import ml_service_client
from app.websocket.broadcaster import broadcast_candle_update

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan: start Finnhub stream on startup, stop on shutdown."""
    logger.info("Starting Trading Chart Backend...")

    # Wire candle updates to the broadcaster
    candle_service.register_callback(broadcast_candle_update)

    # Start ML integration client (registers its own callback)
    await ml_service_client.start()

    # Pre-subscribe to default symbols
    for symbol in DEFAULT_SYMBOLS:
        binance_client.add_symbol(symbol)

    # Start Binance WebSocket client
    await binance_client.start()

    logger.info("Backend ready. Binance client started.")
    yield

    # Shutdown
    logger.info("Shutting down Binance client...")
    await binance_client.stop()
    await ml_service_client.stop()
    logger.info("Backend shutdown complete.")


app = FastAPI(
    title="Trading Chart API",
    description="Professional realtime stock chart backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(candle_router, prefix="/api", tags=["candles"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/health")
async def health() -> dict:
    return {
        "status": "online",
        "binance_connected": binance_client._running,
        "default_symbols": DEFAULT_SYMBOLS
    }
