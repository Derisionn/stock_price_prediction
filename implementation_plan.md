# Professional Realtime Trading Chart — Implementation Plan

## Overview

Build a production-grade Binance/TradingView-style trading chart with:
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + TradingView Lightweight Charts + Zustand
- **Backend**: FastAPI + Python + AsyncIO + WebSockets + Finnhub live feed
- **Data Flow**: Finnhub WebSocket → FastAPI (aggregation) → Frontend WebSocket → Canvas chart

---

## Open Questions

> [!IMPORTANT]
> **Finnhub API Key**: You will need a Finnhub API key (free at https://finnhub.io/). Please provide it or set it as an env variable `FINNHUB_API_KEY`. The plan will include `.env` support so you can plug it in.

> [!IMPORTANT]
> **Symbols**: The default symbol will be `AAPL`. The UI will include a search/selector to switch between symbols. Should we support crypto symbols (e.g., `BINANCE:BTCUSDT`) or only US stocks?

> [!NOTE]
> **Historical Data**: Finnhub's free tier provides limited historical candle data via REST API (`/stock/candle`). The plan uses this for initial load. If you have a premium key, more history is available.

---

## Architecture Overview

```
Finnhub WebSocket (wss://ws.finnhub.io)
        ↓  raw trades (price, volume, timestamp)
FastAPI Backend (port 8000)
  ├── finnhub_ws_client.py     → connects to Finnhub
  ├── candle_aggregation_service.py → builds OHLCV candles per timeframe
  ├── connection_manager.py    → manages frontend WebSocket clients
  └── broadcaster.py           → pushes updates to all connected clients
        ↓  JSON candle updates
Frontend (Next.js, port 3000)
  ├── useWebSocket.ts          → reconnecting WebSocket hook
  ├── useRealtimeCandles.ts    → merges historical + live candles
  ├── chartStore.ts (Zustand)  → global chart state
  └── TradingChart.tsx         → TradingView Lightweight Charts canvas
```

---

## Proposed Changes

### Backend — FastAPI

#### [MODIFY] [main.py](file:///c:/Users/harsh/OneDrive/Desktop/stockprice%20prediction/backend/main.py)
Full FastAPI app entrypoint with CORS, lifespan startup (launch Finnhub WS client), and route mounting.

#### [NEW] `backend/app/main.py`
Core application factory with lifespan that starts Finnhub streaming on startup.

#### [NEW] `backend/app/routes/candle_routes.py`
```
GET /candles?symbol=AAPL&interval=1m&from=<unix>&to=<unix>
GET /candles?symbol=AAPL&interval=1h
GET /symbols        → searchable list of supported symbols
```

#### [NEW] `backend/app/routes/websocket_routes.py`
```
WS /ws/stocks       → streams live candle updates to browser clients
```

#### [NEW] `backend/app/services/candle_aggregation_service.py`
- Maintains in-memory candle state per `(symbol, interval)`
- On each trade tick: updates `high`, `low`, `close`, `volume` of active candle
- On interval boundary: closes current candle, opens new one
- Timeframes: 1m, 5m, 15m, 1h, 4h, 1d

#### [NEW] `backend/app/services/websocket_broadcast_service.py`
- Holds `ConnectionManager` (set of active WebSocket connections)
- `broadcast(message)` → send to all connected clients

#### [NEW] `backend/app/services/market_state_service.py`
- Checks if US market is currently open (9:30am–4pm ET, Mon–Fri)
- Returns `{ "is_open": bool, "next_open": timestamp }`

#### [NEW] `backend/app/providers/finnhub_ws_client.py`
- Async WebSocket client connecting to `wss://ws.finnhub.io?token=API_KEY`
- Subscribes to symbols on connect
- On trade message: routes to `CandleAggregationService`
- Auto-reconnects on disconnect

#### [NEW] `backend/app/websocket/connection_manager.py`
- `connect(ws)` / `disconnect(ws)` / `broadcast(data)`
- Handles per-subscription filtering (by symbol)

#### [NEW] `backend/requirements.txt`
```
fastapi
uvicorn[standard]
websockets
httpx
python-dotenv
finnhub-python
```

#### [NEW] `backend/.env.example`
```
FINNHUB_API_KEY=your_key_here
```

---

### Frontend — Next.js 15

#### [NEW] Initialize Next.js 15 app
```bash
npx create-next-app@latest ./ --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

#### [NEW] Install additional packages
```bash
npm install lightweight-charts zustand lucide-react clsx
```

#### [NEW] `frontend/types/candle.ts`
```typescript
export interface Candle {
  time: number;       // Unix timestamp (seconds)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type Timeframe = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

export interface MarketState {
  isOpen: boolean;
  nextOpen?: string;
}
```

#### [NEW] `frontend/store/chartStore.ts`
Zustand store managing:
- `symbol`, `timeframe`, `candles[]`
- `isLive`, `marketState`
- `autoScroll`, `hoveredCandle`
- `setTimeframe()`, `updateActiveCandle()`, `appendCandle()`

#### [NEW] `frontend/services/api.ts`
- `fetchHistoricalCandles(symbol, interval, from?, to?)`
- `fetchSymbols()`
- `fetchMarketState()`

#### [NEW] `frontend/services/websocket.ts`
- Singleton WebSocket manager
- Auto-reconnect with exponential backoff
- Message parsing and routing

#### [NEW] `frontend/hooks/useWebSocket.ts`
- React hook wrapping the WS service
- Returns `{ isConnected, lastMessage, send }`

#### [NEW] `frontend/hooks/useRealtimeCandles.ts`
- Fetches historical candles on mount/symbol/timeframe change
- Merges live WS updates into candle array
- Handles active candle update vs. new candle append
- Returns `{ candles, isLoading }`

#### [NEW] `frontend/hooks/useChartZoom.ts`
- Detects visible range changes on chart
- Maps visible bar count → appropriate timeframe
- Triggers timeframe change when zoom crosses threshold

#### [NEW] `frontend/components/charts/TradingChart.tsx`
Main chart component:
- Initializes `createChart()` from lightweight-charts
- Adds `CandlestickSeries` + `HistogramSeries` (volume)
- Handles resize via `ResizeObserver`
- Subscribes to visible range changes for smart zoom
- Auto-scrolls unless user is panning
- Crosshair move → updates `hoveredCandle`

#### [NEW] `frontend/components/charts/TimeframeSwitcher.tsx`
- Row of buttons: 1m | 5m | 15m | 1h | 4h | 1D
- Highlights active timeframe
- Binance-style design

#### [NEW] `frontend/components/charts/OHLCTooltip.tsx`
- Displays O/H/L/C/V on hover
- Shown in top-left of chart area
- Color-coded (green if close > open, red otherwise)

#### [NEW] `frontend/components/charts/LiveIndicator.tsx`
- 🟢 LIVE / 🔴 Market Closed badge
- Animated pulse dot for live state

#### [NEW] `frontend/components/charts/PriceHeader.tsx`
- Current price, 24h change %, change amount
- Binance-style with large price display

#### [NEW] `frontend/components/ui/SymbolSearch.tsx`
- Dropdown with search for switching symbols

#### [NEW] `frontend/app/dashboard/page.tsx`
Main dashboard assembling all components in Binance-style layout.

#### [NEW] `frontend/app/layout.tsx`
Root layout with dark theme, Inter/JetBrains Mono fonts, meta tags.

#### [NEW] `frontend/app/globals.css`
Dark Binance-inspired design tokens, chart container styles.

---

## WebSocket Protocol

### Backend → Frontend message format:
```json
{
  "type": "candle_update",
  "symbol": "AAPL",
  "interval": "1m",
  "candle": {
    "time": 1716400800,
    "open": 185.20,
    "high": 185.45,
    "low": 185.10,
    "close": 185.38,
    "volume": 12400
  },
  "is_new": false
}
```

### Frontend → Backend (subscribe/unsubscribe):
```json
{ "type": "subscribe", "symbol": "AAPL", "interval": "1m" }
{ "type": "unsubscribe", "symbol": "AAPL" }
```

---

## Smart Zoom → Timeframe Mapping

| Visible Bars | Auto-selected Timeframe |
|---|---|
| > 500 | 1d |
| 200–500 | 4h |
| 100–200 | 1h |
| 50–100 | 15m |
| 20–50 | 5m |
| < 20 | 1m |

---

## UI Design Details

- **Background**: `#0b0e11` (Binance black)
- **Card/Panel**: `#161a1e`
- **Border**: `#2b2f35`
- **Green candle**: `#0ecb81` (Binance green)
- **Red candle**: `#f6465d` (Binance red)
- **Yellow accent**: `#f0b90b` (Binance yellow)
- **Text primary**: `#eaecef`
- **Text secondary**: `#848e9c`
- **Font**: Inter for UI, JetBrains Mono for prices

---

## Verification Plan

### Backend Tests
- `uvicorn app.main:app --reload` starts without errors
- `GET /candles?symbol=AAPL&interval=1m` returns candle array
- `ws://localhost:8000/ws/stocks` connects and streams updates

### Frontend Tests
- `npm run dev` starts without errors
- Chart renders with historical candles
- WebSocket connects and updates candle in real time
- Timeframe switcher changes data correctly
- Smart zoom changes timeframe automatically
- Market closed state shows correct indicator

### Manual Verification
- Open dashboard, confirm Binance-dark UI
- Hover crosshair, confirm OHLCV tooltip appears
- Switch timeframes, confirm chart reloads
- Zoom in/out, confirm timeframe auto-changes
- Close/reopen browser tab, confirm WebSocket reconnects
