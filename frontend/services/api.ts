import type { Candle, Timeframe, MarketState, Symbol } from '@/types/candle';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHistoricalCandles(
  symbol: string,
  interval: Timeframe,
  limit = 500,
  from?: number,
  to?: number,
): Promise<Candle[]> {
  const params = new URLSearchParams({
    symbol,
    interval,
    limit: String(limit),
  });
  if (from) params.set('from', String(from));
  if (to) params.set('to', String(to));

  const res = await fetch(`${API_BASE}/api/candles?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch candles: ${res.statusText}`);

  const data = await res.json();
  return data.candles as Candle[];
}

export async function fetchMarketState(): Promise<MarketState> {
  const res = await fetch(`${API_BASE}/api/market-state`);
  if (!res.ok) throw new Error('Failed to fetch market state');
  return res.json();
}

export async function fetchSymbols(query?: string): Promise<Symbol[]> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);

  const res = await fetch(`${API_BASE}/api/symbols?${params}`);
  if (!res.ok) throw new Error('Failed to fetch symbols');

  const data = await res.json();
  return data.symbols as Symbol[];
}
