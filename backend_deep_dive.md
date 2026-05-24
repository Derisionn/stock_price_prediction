# Backend Deep-Dive — How It Works

## Big Picture

```
Finnhub (internet)
    │
    │  wss://ws.finnhub.io?token=KEY
    │  { type:"trade", data:[{ s:"AAPL", p:185.23, v:120, t:1716400512345 }] }
    ▼
┌──────────────────────────────────────────────┐
│              FastAPI Backend                 │
│                                              │
│  finnhub_ws_client.py ──► candle_aggregation │
│                                ──► broadcaster
│                                      ──► connection_manager
└──────────────────────────────────────────────┘
    │
    │  ws://localhost:8000/ws/stocks
    │  { type:"candle_update", symbol:"AAPL", interval:"5m", candle:{...}, is_new:false }
    ▼
Browser (Next.js frontend)
```

There are **two independent WebSocket connections**:
- **Upstream**: Backend ↔ Finnhub (your server is the *client*)
- **Downstream**: Browser ↔ Backend (your server is the *host*)

---

## Step 1 — App Startup (`main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    candle_service.register_callback(broadcast_candle_update)  # wire A → B
    for symbol in DEFAULT_SYMBOLS:
        finnhub_client.add_symbol(symbol)                      # queue subscriptions
    await finnhub_client.start()                               # launch background task
    yield                                                      # app runs
    await finnhub_client.stop()                                # graceful shutdown
```

### What happens in order:

| # | Action | Why |
|---|--------|-----|
| 1 | `register_callback(broadcast_candle_update)` | Wires the aggregation engine to the broadcaster so every completed candle update is forwarded to connected browsers |
| 2 | `finnhub_client.add_symbol("AAPL")` × 7 | Pre-loads the default watchlist before the connection opens |
| 3 | `await finnhub_client.start()` | Spawns an `asyncio.Task` in the background — **does not block startup** |

> [!NOTE]
> If `FINNHUB_API_KEY` is missing or is the placeholder string, `start()` launches `_simulate_trades()` instead. The rest of the system is identical — only the data source changes.

---

## Step 2 — Finnhub WebSocket Client (`finnhub_ws_client.py`)

This is a **long-lived background coroutine** that runs the entire time the server is up.

### Connection loop

```python
async def _run_with_reconnect(self):
    while self._running:
        try:
            await self._connect()          # blocks until disconnected
            self._reconnect_delay = 1.0    # reset on success
        except Exception:
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(delay * 2, 60)  # exponential backoff
```

### What `_connect()` does

```python
async def _connect(self):
    async with websockets.connect("wss://ws.finnhub.io?token=KEY") as ws:
        self._websocket = ws

        # Subscribe to every symbol in the watchlist
        for symbol in self._subscribed_symbols:
            await ws.send('{"type":"subscribe","symbol":"AAPL"}')

        # Infinite receive loop
        async for message in ws:
            await self._handle_message(message)
```

### Message from Finnhub

```json
{
  "type": "trade",
  "data": [
    { "s": "AAPL", "p": 185.23, "v": 120,  "t": 1716400512345 },
    { "s": "AAPL", "p": 185.25, "v": 55,   "t": 1716400512401 },
    { "s": "TSLA", "p": 240.10, "v": 300,  "t": 1716400512510 }
  ]
}
```

Finnhub batches multiple trades into a single message. Each trade has:
- `s` — symbol
- `p` — price
- `v` — volume
- `t` — timestamp in **milliseconds**

### `_handle_message()` unpacks and routes

```python
for trade in data["data"]:
    await candle_service.process_trade(
        symbol       = trade["s"],   # "AAPL"
        price        = trade["p"],   # 185.23
        volume       = trade["v"],   # 120
        timestamp_ms = trade["t"],   # 1716400512345
    )
```

---

## Step 3 — Candle Aggregation (`candle_aggregation_service.py`)

This is the **brain of the backend**. It converts raw tick prices into OHLCV candles, for *all six timeframes simultaneously*.

### Data structure

```python
# One CandleState per (symbol, interval) pair
states = {
    ("AAPL", "1m"):  CandleState(completed=[...500 candles], active=Candle(...)),
    ("AAPL", "5m"):  CandleState(completed=[...500 candles], active=Candle(...)),
    ("AAPL", "15m"): CandleState(...),
    ("AAPL", "1h"):  CandleState(...),
    ("AAPL", "4h"):  CandleState(...),
    ("AAPL", "1d"):  CandleState(...),
    ("TSLA", "1m"):  CandleState(...),
    ...
}
```

### `process_trade()` — called on every tick

```python
async def process_trade(self, symbol, price, volume, timestamp_ms):
    # Updates ALL six timeframes for this symbol in one call
    for interval in ["1m", "5m", "15m", "1h", "4h", "1d"]:
        await self._update_candle(symbol, interval, price, volume, timestamp_ms)
```

### `_update_candle()` — the core logic

```python
candle_start = (timestamp_ms // 1000 // interval_seconds) * interval_seconds
```

This arithmetic **floors the timestamp** to the start of the current candle interval.

**Example for 5m (300s):**
```
timestamp = 1716400512  (seconds)
1716400512 // 300 = 5721335   (which 5-min slot?)
5721335 * 300 = 1716400500   (start of that slot)
```

Then three cases:

```
Case 1: No active candle yet
    → Create new candle: O=H=L=C=price, V=volume
    → is_new = True

Case 2: Trade is in a NEW interval (candle_start > active.time)
    → Close the active candle → move to completed[]
    → Open a new active candle
    → is_new = True

Case 3: Trade is in the SAME interval (most common)
    → active.high = max(active.high, price)
    → active.low  = min(active.low,  price)
    → active.close = price
    → active.volume += volume
    → is_new = False
```

After updating, it fires **all registered callbacks**:

```python
for callback in self._on_candle_callbacks:
    await callback(symbol, interval, candle=active, is_new=is_new)
```

---

## Step 4 — Broadcasting (`broadcaster.py` + `connection_manager.py`)

The callback registered in Step 1 is `broadcast_candle_update`:

```python
async def broadcast_candle_update(symbol, interval, candle, is_new):
    message = {
        "type":     "candle_update",
        "symbol":   symbol,         # "AAPL"
        "interval": interval,       # "5m"
        "candle":   candle.to_dict(),
        "is_new":   is_new,
    }
    await manager.broadcast_to_symbol(symbol, message)
```

### ConnectionManager — who gets what

```python
# Internal state:
_subscriptions = {
    "AAPL": { ws_client_1, ws_client_2 },
    "TSLA": { ws_client_1 },
    "MSFT": { ws_client_3 },
}
_client_symbols = {
    ws_client_1: {"AAPL", "TSLA"},
    ws_client_2: {"AAPL"},
    ws_client_3: {"MSFT"},
}
```

`broadcast_to_symbol("AAPL", message)` sends **only** to `{ws_client_1, ws_client_2}` — not to `ws_client_3` who only watches MSFT.

Dead connections are silently removed during the broadcast attempt.

---

## Step 5 — Frontend WebSocket Route (`websocket_routes.py`)

This is how a **browser tab** enters the system:

```
Browser opens: ws://localhost:8000/ws/stocks
    ↓
manager.connect(websocket)   ← registered, but no subscriptions yet
    ↓
Browser sends: {"type":"subscribe","symbol":"AAPL"}
    ↓
manager.subscribe(ws, "AAPL")
finnhub_client.add_symbol("AAPL")   ← tells Finnhub WS to subscribe if not already
    ↓
Now: any AAPL candle_update → broadcast → this browser tab
```

```
Browser sends: {"type":"unsubscribe","symbol":"AAPL"}
    ↓
manager.unsubscribe(ws, "AAPL")

Browser disconnects (tab closed)
    ↓
WebSocketDisconnect caught → manager.disconnect(ws)
    ↓
All subscriptions for this ws cleaned up
```

---

## Step 6 — REST API (`candle_routes.py`)

Used by the frontend **once** on load to get historical candles before live data starts.

### `GET /api/candles?symbol=AAPL&interval=5m`

```
Request arrives
    ↓
Check: do we have in-memory candles for (AAPL, 5m)?
    ├── YES → return them immediately (fastest path)
    └── NO  →
         ├── FINNHUB_API_KEY set?
         │    ├── YES → call Finnhub REST /stock/candle
         │    │          → seed aggregation service with results
         │    │          → return to browser
         │    └── NO  → generate_simulated_candles()
         │               → seed aggregation service
         │               → return to browser
```

**Why seed the aggregation service?**
So that the first live tick updates the *correct* active candle rather than starting from scratch. If the last historical candle ends at 14:35:00 and the first live trade arrives at 14:36:23, the service knows it's a new candle.

---

## Complete Data Flow — One Tick End to End

```
Finnhub sends:
  { "type":"trade", "data":[{ "s":"AAPL","p":185.23,"v":120,"t":1716400512345 }] }

finnhub_ws_client._handle_message()
  └─► candle_service.process_trade("AAPL", 185.23, 120, 1716400512345)
          │
          ├─► _update_candle("AAPL", "1m",  ...)  → fires callback
          ├─► _update_candle("AAPL", "5m",  ...)  → fires callback  ◄── browser subscribed to this
          ├─► _update_candle("AAPL", "15m", ...)  → fires callback
          ├─► _update_candle("AAPL", "1h",  ...)  → fires callback
          ├─► _update_candle("AAPL", "4h",  ...)  → fires callback
          └─► _update_candle("AAPL", "1d",  ...)  → fires callback

Each callback → broadcast_candle_update("AAPL", "5m", candle, is_new=False)
  └─► manager.broadcast_to_symbol("AAPL", {
        "type":     "candle_update",
        "symbol":   "AAPL",
        "interval": "5m",
        "candle":   { "time":1716400500, "open":185.10, "high":185.23, "low":185.05, "close":185.23, "volume":4320 },
        "is_new":   false
      })
        └─► websocket.send_text(json) → browser tab

Browser (useRealtimeCandles.ts):
  msg.interval === currentTimeframe ("5m") ?
    └─► updateActiveCandle(candle)
          └─► Zustand store updates candles[-1] in place
                └─► TradingChart useEffect fires
                      └─► candleSeries.update({ time, open, high, low, close })
                            └─► Canvas redraws only the last bar  ✓
```

**Total latency**: Finnhub trade → browser canvas repaint ≈ 5–50ms

---

## Simulation Mode (No API Key)

When `FINNHUB_API_KEY` is not set, `_simulate_trades()` runs instead:

```python
prices = { "AAPL": 185.0, "TSLA": 240.0, ... }

while True:
    for symbol, price in prices.items():
        change = random.uniform(-0.0005, 0.0005)   # ±0.05% per tick
        new_price = price * (1 + change)
        volume    = random.uniform(10, 500)

        await candle_service.process_trade(symbol, new_price, volume, now_ms)

    await asyncio.sleep(0.5)   # 2 ticks/second
```

The **rest of the pipeline is 100% identical** — same aggregation, same broadcaster, same WebSocket route. The only difference is where the raw prices come from.

---

## Memory & Performance

| Concern | How it's handled |
|---------|-----------------|
| Candle memory | Max 2,000 completed candles per `(symbol, interval)` pair. Oldest are trimmed. |
| Dead WS clients | Detected during `broadcast_to_symbol` — silently removed, no crash |
| Re-entrant updates | Single-threaded asyncio — no locks needed; updates are sequential |
| Slow browsers | `send_text` failures caught per-client; one slow client can't block others |
| Reconnect | Exponential backoff: 1s → 2s → 4s → ... → 60s max |
