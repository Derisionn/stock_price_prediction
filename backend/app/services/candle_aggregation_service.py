"""
Candle Aggregation Service
Aggregates raw trade ticks into OHLCV candles for multiple timeframes.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Timeframe in seconds
TIMEFRAME_SECONDS: Dict[str, int] = {
    "1s": 1,
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


@dataclass
class Candle:
    time: int        # Unix timestamp (start of candle interval, seconds)
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CandleState:
    """Holds active candle + completed candles for a (symbol, interval) pair."""
    symbol: str
    interval: str
    completed: List[Candle] = field(default_factory=list)
    active: Optional[Candle] = None

    # Keep only last N completed candles in memory
    MAX_CANDLES = 2000


class CandleAggregationService:
    """
    Aggregates trade ticks into OHLCV candles.
    Thread-safe via asyncio (single-threaded event loop).
    """

    def __init__(self) -> None:
        # Key: (symbol, interval) -> CandleState
        self._states: Dict[Tuple[str, str], CandleState] = {}
        self._on_candle_callbacks: list = []

    def register_callback(self, callback) -> None:
        """Register an async callback called on every candle update."""
        self._on_candle_callbacks.append(callback)

    def _get_candle_start(self, timestamp_ms: int, interval: str) -> int:
        """Round down timestamp to the start of the candle interval."""
        ts_sec = timestamp_ms // 1000
        interval_sec = TIMEFRAME_SECONDS[interval]
        return (ts_sec // interval_sec) * interval_sec

    def _get_or_create_state(self, symbol: str, interval: str) -> CandleState:
        key = (symbol, interval)
        if key not in self._states:
            self._states[key] = CandleState(symbol=symbol, interval=interval)
        return self._states[key]

    async def process_trade(
        self,
        symbol: str,
        price: float,
        volume: float,
        timestamp_ms: int,
    ) -> None:
        """
        Process a single trade tick and update candles for all timeframes.
        Fires callbacks with candle update info.
        """
        for interval in TIMEFRAME_SECONDS:
            await self._update_candle(symbol, interval, price, volume, timestamp_ms)

    async def _update_candle(
        self,
        symbol: str,
        interval: str,
        price: float,
        volume: float,
        timestamp_ms: int,
    ) -> None:
        state = self._get_or_create_state(symbol, interval)
        candle_start = self._get_candle_start(timestamp_ms, interval)

        if state.active is None:
            # No active candle yet — create one
            state.active = Candle(
                time=candle_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
            )
            is_new = True
        elif candle_start > state.active.time:
            # New interval started — close active candle
            state.completed.append(state.active)
            # Trim memory
            if len(state.completed) > CandleState.MAX_CANDLES:
                state.completed = state.completed[-CandleState.MAX_CANDLES:]
            # Open new candle
            state.active = Candle(
                time=candle_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
            )
            is_new = True
        else:
            # Update existing active candle
            c = state.active
            c.high = max(c.high, price)
            c.low = min(c.low, price)
            c.close = price
            c.volume += volume
            is_new = False

        # Fire callbacks
        for cb in self._on_candle_callbacks:
            try:
                await cb(
                    symbol=symbol,
                    interval=interval,
                    candle=state.active,
                    is_new=is_new,
                )
            except Exception as e:
                logger.error(f"Candle callback error: {e}")

    def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ) -> List[Candle]:
        """Return completed + active candles for a symbol/interval."""
        state = self._states.get((symbol, interval))
        if not state:
            return []
        candles = list(state.completed[-limit:])
        if state.active:
            candles.append(state.active)
        return candles

    def seed_historical(
        self,
        symbol: str,
        interval: str,
        candles: List[dict],
    ) -> None:
        """
        Seed the aggregation state with historical candle data from REST API.
        candles: list of dicts with keys: time, open, high, low, close, volume
        """
        state = self._get_or_create_state(symbol, interval)
        if candles:
            completed = [
                Candle(
                    time=c["time"],
                    open=c["open"],
                    high=c["high"],
                    low=c["low"],
                    close=c["close"],
                    volume=c["volume"],
                )
                for c in candles[:-1]  # all but last become completed
            ]
            state.completed = completed
            # Last candle becomes active (will be updated by live trades)
            last = candles[-1]
            state.active = Candle(
                time=last["time"],
                open=last["open"],
                high=last["high"],
                low=last["low"],
                close=last["close"],
                volume=last["volume"],
            )
        logger.info(f"Seeded {len(candles)} historical candles for {symbol}/{interval}")


# Global singleton
candle_service = CandleAggregationService()
