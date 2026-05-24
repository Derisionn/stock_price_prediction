import { create } from 'zustand';
import type { Candle, Timeframe, MarketState, PriceInfo } from '@/types/candle';

interface ChartState {
  // Symbol, timeframe & type
  symbol: string;
  timeframe: Timeframe;
  chartType: 'candlestick' | 'area';

  // Candle data
  candles: Candle[];
  isLoading: boolean;

  // Live state
  isConnected: boolean;
  isLive: boolean;
  marketState: MarketState | null;

  // Chart interactions
  autoScroll: boolean;
  hoveredCandle: Candle | null;
  crosshairPoint: { x: number; y: number } | null;

  // Price info
  priceInfo: PriceInfo | null;

  // Actions
  setSymbol: (symbol: string) => void;
  setTimeframe: (timeframe: Timeframe) => void;
  setChartType: (type: 'candlestick' | 'area') => void;
  setCandles: (candles: Candle[]) => void;
  updateActiveCandle: (candle: Candle) => void;
  appendCandle: (candle: Candle) => void;
  setIsLoading: (loading: boolean) => void;
  setIsConnected: (connected: boolean) => void;
  setIsLive: (live: boolean) => void;
  setMarketState: (state: MarketState) => void;
  setAutoScroll: (auto: boolean) => void;
  setHoveredCandle: (candle: Candle | null) => void;
  setCrosshairPoint: (point: { x: number; y: number } | null) => void;
  setPriceInfo: (info: PriceInfo) => void;
}

export const useChartStore = create<ChartState>((set, get) => ({
  symbol: 'AAPL',
  timeframe: '5m' as Timeframe,
  chartType: 'candlestick' as const,
  candles: [],
  isLoading: false,
  isConnected: false,
  isLive: false,
  marketState: null,
  autoScroll: true,
  hoveredCandle: null,
  crosshairPoint: null,
  priceInfo: null,

  setSymbol: (symbol) => set({ symbol, candles: [], isLoading: true }),

  setTimeframe: (timeframe) => set({ timeframe, candles: [], isLoading: true }),

  setChartType: (chartType) => set({ chartType }),

  setCandles: (candles) => {
    set({ candles, isLoading: false });
    // Update price info from last candle
    const last = candles[candles.length - 1];
    const first = candles[0];
    if (last && first) {
      const change = last.close - first.open;
      const changePercent = (change / first.open) * 100;
      set({ priceInfo: { price: last.close, change, changePercent } });
    }
  },

  updateActiveCandle: (candle) => {
    const { candles } = get();
    if (candles.length === 0) return;
    const last = candles[candles.length - 1];
    if (last.time === candle.time) {
      // Update last candle in place (immutable)
      const updated = [...candles.slice(0, -1), candle];
      set({ candles: updated });
    } else if (candle.time > last.time) {
      // New candle
      set({ candles: [...candles, candle] });
    }
    // Always update price
    const firstCandle = candles[0];
    if (firstCandle) {
      const change = candle.close - firstCandle.open;
      const changePercent = (change / firstCandle.open) * 100;
      set({ priceInfo: { price: candle.close, change, changePercent } });
    }
  },

  appendCandle: (candle) => {
    const { candles } = get();
    set({ candles: [...candles, candle] });
  },

  setIsLoading: (isLoading) => set({ isLoading }),
  setIsConnected: (isConnected) => set({ isConnected }),
  setIsLive: (isLive) => set({ isLive }),
  setMarketState: (marketState) => set({ marketState }),
  setAutoScroll: (autoScroll) => set({ autoScroll }),
  setHoveredCandle: (hoveredCandle) => set({ hoveredCandle }),
  setCrosshairPoint: (crosshairPoint) => set({ crosshairPoint }),
  setPriceInfo: (priceInfo) => set({ priceInfo }),
}));
