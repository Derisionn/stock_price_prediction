'use client';

import { useCallback, useRef } from 'react';
import type { IChartApi } from 'lightweight-charts';
import type { Timeframe } from '@/types/candle';
import { useChartStore } from '@/store/chartStore';

// Map visible bar count -> timeframe (minimum zoom = 5m)
const ZOOM_BREAKPOINTS: Array<{ maxBars: number; timeframe: Timeframe }> = [
  { maxBars: 30, timeframe: '1s' },
  { maxBars: 60, timeframe: '1m' },
  { maxBars: 120, timeframe: '5m' },
  { maxBars: 240, timeframe: '15m' },
  { maxBars: 500, timeframe: '1h' },
  { maxBars: 1000, timeframe: '4h' },
  { maxBars: Infinity, timeframe: '1d' },
];

function getBarsToTimeframe(visibleBars: number): Timeframe {
  for (const { maxBars, timeframe } of ZOOM_BREAKPOINTS) {
    if (visibleBars <= maxBars) return timeframe;
  }
  return '1d';
}

export function useChartZoom(chartRef: React.RefObject<IChartApi | null>) {
  const { timeframe, setTimeframe } = useChartStore();
  const lastTimeframeRef = useRef(timeframe);
  const isChangingRef = useRef(false);

  const handleVisibleRangeChange = useCallback(() => {
    if (!chartRef.current || isChangingRef.current) return;

    const logicalRange = chartRef.current.timeScale().getVisibleLogicalRange();
    if (!logicalRange) return;

    const visibleBars = Math.round(logicalRange.to - logicalRange.from);
    const newTimeframe = getBarsToTimeframe(visibleBars);

    if (newTimeframe !== lastTimeframeRef.current) {
      lastTimeframeRef.current = newTimeframe;
      isChangingRef.current = true;
      setTimeframe(newTimeframe);
      // Prevent rapid switching
      setTimeout(() => { isChangingRef.current = false; }, 1000);
    }
  }, [chartRef, setTimeframe]);

  return { handleVisibleRangeChange };
}
