// Candle and trading types

export interface Candle {
  time: number;   // Unix timestamp in seconds
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type Timeframe = '1s' | '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

export const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  '1s':  '1s',
  '1m':  '1m',
  '5m':  '5m',
  '15m': '15m',
  '1h':  '1H',
  '4h':  '4H',
  '1d':  '1D',
};

export const TIMEFRAME_SECONDS: Record<Timeframe, number> = {
  '1s':  1,
  '1m':  60,
  '5m':  300,
  '15m': 900,
  '1h':  3600,
  '4h':  14400,
  '1d':  86400,
};

export interface MarketState {
  is_open: boolean;
  current_time_et: string;
  message: string;
}

export interface CandleUpdate {
  type: 'candle_update';
  symbol: string;
  interval: string;
  candle: Candle;
  is_new: boolean;
}

export interface Symbol {
  symbol: string;
  description: string;
  type: string;
}

export interface PriceInfo {
  price: number;
  change: number;
  changePercent: number;
}
