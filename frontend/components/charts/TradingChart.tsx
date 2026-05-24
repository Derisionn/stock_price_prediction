'use client';

import React, { useEffect, useRef, useCallback } from 'react';
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  AreaSeries,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from 'lightweight-charts';
import { useChartStore } from '@/store/chartStore';
import { OHLCTooltip } from './OHLCTooltip';
import { FloatingTooltip } from './FloatingTooltip';
import type { Candle } from '@/types/candle';

// ─── Constants ────────────────────────────────────────────────────────────────

/** Hard minimum visible bars — prevents zooming past the 5m timeframe */
const MIN_VISIBLE_BARS = 50;

const CHART_COLORS = {
  background:    'transparent',
  gridLines:     '#1e2329',
  border:        '#2b2f35',
  text:          '#848e9c',
  crosshair:     '#485563',
  upColor:       '#0ecb81',
  downColor:     '#f6465d',
  wickUpColor:   '#0ecb81',
  wickDownColor: '#f6465d',
  volumeUp:      'rgba(14, 203, 129, 0.3)',
  volumeDown:    'rgba(246, 70, 93, 0.3)',
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

// Browser timezone offset in seconds. 
// e.g., IST is +05:30, so getTimezoneOffset() is -330. Offset in seconds is -19800.
// We subtract it to shift the UTC timestamp to Local Time before feeding to the chart.
const tzOffset = new Date().getTimezoneOffset() * 60;

function toChartCandle(c: Candle) {
  return {
    time:  (c.time - tzOffset) as UTCTimestamp,
    open:  c.open,
    high:  c.high,
    low:   c.low,
    close: c.close,
  };
}

function toChartArea(c: Candle) {
  return {
    time:  (c.time - tzOffset) as UTCTimestamp,
    value: c.close,
  };
}

function toChartVolume(c: Candle) {
  return {
    time:  (c.time - tzOffset) as UTCTimestamp,
    value: c.volume,
    color: c.close >= c.open ? CHART_COLORS.volumeUp : CHART_COLORS.volumeDown,
  };
}

// ─── Component ────────────────────────────────────────────────────────────────

export function TradingChart() {
  const containerRef    = useRef<HTMLDivElement>(null);
  const chartRef        = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const areaSeriesRef   = useRef<ISeriesApi<'Area'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const prevLenRef      = useRef(0);
  const candlesRef      = useRef<Candle[]>([]);
  const isPanningRef    = useRef(false);
  const isClampingRef   = useRef(false); // re-entrant guard for range clamp

  const { chartType, candles, isLoading, autoScroll, setAutoScroll, setHoveredCandle, setCrosshairPoint } =
    useChartStore();

  const [showLatestButton, setShowLatestButton] = React.useState(false);
  const isLatestVisibleRef = useRef(true);

  // ── Chart initialisation (runs once) ────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background:  { type: ColorType.Solid, color: CHART_COLORS.background },
        textColor:   CHART_COLORS.text,
        fontFamily:  "'JetBrains Mono', 'Fira Code', monospace",
        fontSize:    11,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: CHART_COLORS.crosshair, width: 1, style: 2, labelBackgroundColor: '#2b2f35' },
        horzLine: { color: CHART_COLORS.crosshair, width: 1, style: 2, labelBackgroundColor: '#2b2f35' },
      },
      leftPriceScale: {
        visible: true,
        borderVisible: true,
        borderColor: CHART_COLORS.border,
        textColor:   CHART_COLORS.text,
        scaleMargins: { top: 0.1, bottom: 0.3 },
      },
      rightPriceScale: {
        visible: false,
      },
      timeScale: {
        borderVisible: true,
        borderColor:    CHART_COLORS.border,
        timeVisible:    true,
        secondsVisible: false,
        rightOffset:    8,
        barSpacing:     8,
        minBarSpacing:  2,
        fixLeftEdge:    false,
        fixRightEdge:   false,
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true },
      handleScale:  { mouseWheel: true, pinch: true },
      width:  containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      priceScaleId: 'left',
      upColor:       CHART_COLORS.upColor,
      downColor:     CHART_COLORS.downColor,
      borderVisible: false,
      wickUpColor:   CHART_COLORS.wickUpColor,
      wickDownColor: CHART_COLORS.wickDownColor,
    });

    // Area series (gold theme)
    const areaSeries = chart.addSeries(AreaSeries, {
      priceScaleId: 'left',
      lineColor: '#f0b90b', // Gold line
      topColor: 'rgba(240, 185, 11, 0.4)', // Gold gradient top
      bottomColor: 'rgba(240, 185, 11, 0)', // Transparent bottom
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      crosshairMarkerBorderColor: '#fff',
      crosshairMarkerBackgroundColor: '#f0b90b',
    });

    // Volume histogram — bottom 22% of pane
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color:        CHART_COLORS.volumeUp,
      priceFormat:  { type: 'volume' },
      priceScaleId: 'volume',
    });
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });

    chartRef.current        = chart;
    candleSeriesRef.current = candleSeries;
    areaSeriesRef.current   = areaSeries;
    volumeSeriesRef.current = volumeSeries;

    // ── Zoom clamp & visibility tracking ─────────────────────────────────
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range || isClampingRef.current) return;

      const visibleBars = range.to - range.from;

      if (visibleBars < MIN_VISIBLE_BARS) {
        isClampingRef.current = true;
        chart.timeScale().setVisibleLogicalRange({
          from: range.to - MIN_VISIBLE_BARS,
          to:   range.to,
        });
        isClampingRef.current = false;
      }

      if (isPanningRef.current) setAutoScroll(false);

      // Check if latest candle is visible
      if (candleSeriesRef.current) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const barsInfo = candleSeriesRef.current.barsInLogicalRange(range as any);
        if (barsInfo !== null) {
          const currentlyVisible = barsInfo.barsAfter <= 0;
          if (currentlyVisible !== isLatestVisibleRef.current) {
            isLatestVisibleRef.current = currentlyVisible;
            setShowLatestButton(!currentlyVisible);
          }
        }
      }
    });

    // ── Crosshair → OHLC tooltip ─────────────────────────────────────────
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData || !param.point) { 
        setHoveredCandle(null); 
        setCrosshairPoint(null);
        return; 
      }
      
      const realUtcTime = (param.time as number) + tzOffset;
      // Search for exact candle to show correct OHLC regardless of series type
      // Using reverse find since we usually hover near the end of the chart
      const matchingCandle = [...candlesRef.current].reverse().find(c => c.time === realUtcTime);
      
      if (matchingCandle) {
        setHoveredCandle(matchingCandle);
        setCrosshairPoint(param.point);
      }
    });

    // ── Mouse/touch tracking for panning detection ───────────────────────
    const el           = containerRef.current;
    const onDown       = () => { isPanningRef.current = true; };
    const onUp         = () => { isPanningRef.current = false; };
    el.addEventListener('mousedown',  onDown);
    el.addEventListener('mouseup',    onUp);
    el.addEventListener('touchstart', onDown);
    el.addEventListener('touchend',   onUp);

    // ── Responsive resize ────────────────────────────────────────────────
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry && chartRef.current) {
        chartRef.current.applyOptions({ width: entry.contentRect.width, height: entry.contentRect.height });
      }
    });
    observer.observe(el);

    return () => {
      observer.disconnect();
      el.removeEventListener('mousedown',  onDown);
      el.removeEventListener('mouseup',    onUp);
      el.removeEventListener('touchstart', onDown);
      el.removeEventListener('touchend',   onUp);
      chart.remove();
      chartRef.current = candleSeriesRef.current = areaSeriesRef.current = volumeSeriesRef.current = null;
    };
  }, [setAutoScroll, setHoveredCandle, setCrosshairPoint]);

  // ── Sync visibility based on chartType ───────────────────────────────────
  useEffect(() => {
    if (!candleSeriesRef.current || !areaSeriesRef.current || !volumeSeriesRef.current) return;
    
    if (chartType === 'candlestick') {
      candleSeriesRef.current.applyOptions({ visible: true });
      areaSeriesRef.current.applyOptions({ visible: false });
      volumeSeriesRef.current.applyOptions({ visible: true });
    } else {
      candleSeriesRef.current.applyOptions({ visible: false });
      areaSeriesRef.current.applyOptions({ visible: true });
      volumeSeriesRef.current.applyOptions({ visible: false });
    }
  }, [chartType]);

  // ── Sync candle data → chart (incremental, O(1) per tick) ───────────────
  useEffect(() => {
    if (!candleSeriesRef.current || !areaSeriesRef.current || !volumeSeriesRef.current) return;

    candlesRef.current = candles;

    if (candles.length === 0) {
      // Clear data and reset previous length reference on empty array
      candleSeriesRef.current.setData([]);
      areaSeriesRef.current.setData([]);
      volumeSeriesRef.current.setData([]);
      prevLenRef.current = 0;
      return;
    }

    const prevLen = prevLenRef.current;
    const currLen = candles.length;

    if (prevLen === 0 || currLen < prevLen) {
      // Full load or timeframe switch
      candleSeriesRef.current.setData(candles.map(toChartCandle));
      areaSeriesRef.current.setData(candles.map(toChartArea));
      volumeSeriesRef.current.setData(candles.map(toChartVolume));
      chartRef.current?.timeScale().fitContent();
    } else if (currLen === prevLen) {
      // Active candle update — touch last bar only
      const last = candles[currLen - 1];
      candleSeriesRef.current.update(toChartCandle(last));
      areaSeriesRef.current.update(toChartArea(last));
      volumeSeriesRef.current.update(toChartVolume(last));
    } else {
      // New candle appended
      const last = candles[currLen - 1];
      candleSeriesRef.current.update(toChartCandle(last));
      areaSeriesRef.current.update(toChartArea(last));
      volumeSeriesRef.current.update(toChartVolume(last));
      if (autoScroll) chartRef.current?.timeScale().scrollToRealTime();
    }

    prevLenRef.current = currLen;
  }, [candles, autoScroll]);

  const scrollToLatest = useCallback(() => {
    setAutoScroll(true);
    chartRef.current?.timeScale().scrollToRealTime();
  }, [setAutoScroll]);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="relative w-full h-full flex flex-col bg-[#0b0e11]">
      {/* Chart Canvas Area */}
      <div className="flex-1 w-full min-h-0 relative">
        <div ref={containerRef} className="w-full h-full" />

        <OHLCTooltip />
        <FloatingTooltip />

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#0b0e11]/80 backdrop-blur-sm z-20">
            <div className="flex flex-col items-center gap-3">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-2 border-[#f0b90b]/20" />
                <div className="absolute inset-0 rounded-full border-2 border-t-[#f0b90b] animate-spin" />
              </div>
              <span className="text-[#848e9c] text-sm">Loading chart data...</span>
            </div>
          </div>
        )}

        {showLatestButton && !isLoading && (
          <button
            onClick={scrollToLatest}
            style={{ padding: '5px 10px' }}
            className="absolute bottom-8 right-4 z-10 flex items-center gap-1.5 bg-[#f0b90b] text-black text-xs font-black rounded-md shadow hover:bg-[#d4a017] transition-colors duration-150"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
            Latest
          </button>
        )}
      </div>
    </div>
  );
}
