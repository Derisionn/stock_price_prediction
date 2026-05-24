'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useChartStore } from '@/store/chartStore';
import { fetchHistoricalCandles } from '@/services/api';
import { wsService } from '@/services/websocket';
import type { CandleUpdate } from '@/types/candle';

export function useRealtimeCandles() {
  const {
    symbol,
    timeframe,
    setCandles,
    setIsLoading,
    updateActiveCandle,
    setIsConnected,
    setIsLive,
  } = useChartStore();

  const currentSymbolRef = useRef(symbol);
  const currentTimeframeRef = useRef(timeframe);

  // Load historical candles when symbol or timeframe changes
  const loadHistorical = useCallback(async () => {
    setIsLoading(true);
    try {
      const candles = await fetchHistoricalCandles(symbol, timeframe, 500);
      setCandles(candles);
    } catch (err) {
      console.error('[useRealtimeCandles] Failed to load historical:', err);
      setIsLoading(false);
    }
  }, [symbol, timeframe, setCandles, setIsLoading]);

  useEffect(() => {
    currentSymbolRef.current = symbol;
    currentTimeframeRef.current = timeframe;
    loadHistorical();
  }, [symbol, timeframe, loadHistorical]);

  // Handle incoming WebSocket candle updates
  useEffect(() => {
    wsService.connect();
    wsService.subscribe(symbol);

    const offMessage = wsService.onMessage((raw) => {
      const msg = raw as CandleUpdate;
      if (
        msg.type === 'candle_update' &&
        msg.symbol === currentSymbolRef.current &&
        msg.interval === currentTimeframeRef.current
      ) {
        updateActiveCandle(msg.candle);
        setIsLive(true);
      }
    });

    const offStatus = wsService.onStatus((connected) => {
      setIsConnected(connected);
      if (!connected) setIsLive(false);
    });

    setIsConnected(wsService.isConnected);

    return () => {
      offMessage();
      offStatus();
      wsService.unsubscribe(symbol);
    };
  }, [symbol, updateActiveCandle, setIsConnected, setIsLive]);

  // Switch timeframe subscription
  useEffect(() => {
    // Re-subscribe with new timeframe
    wsService.subscribe(symbol);
  }, [symbol, timeframe]);
}
