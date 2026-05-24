'use client';

import React from 'react';
import { useChartStore } from '@/store/chartStore';

function fmt(n: number | undefined): string {
  if (n === undefined || n === null) return '—';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(2) + 'K';
  return n.toFixed(2);
}

function fmtPrice(n: number | undefined): string {
  if (n === undefined) return '—';
  return n.toFixed(2);
}

export function OHLCTooltip() {
  const { hoveredCandle, chartType } = useChartStore();

  if (!hoveredCandle) return null;

  const isGreen = hoveredCandle.close >= hoveredCandle.open;
  const color = isGreen ? '#0ecb81' : '#f6465d';

  if (chartType === 'area') {
    return (
      <div
        style={{ padding: '12px 24px' }}
        className="absolute top-4 left-[76px] z-10 flex items-center gap-3.5 bg-[#131722]/80 backdrop-blur-md rounded-lg text-[13px] font-mono pointer-events-none shadow-md"
      >
        <div className="flex items-center gap-1.5">
          <span className="text-[#787b86]">Price</span>
          <span style={{ color: '#f0b90b' }}>{fmtPrice(hoveredCandle.close)}</span>
        </div>
        <div className="flex items-center gap-1.5 ml-1">
          <span className="text-[#787b86]">V</span>
          <span className="text-[#d1d4dc]">{fmt(hoveredCandle.volume)}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{ padding: '12px 24px' }}
      className="absolute top-4 left-[76px] z-10 flex items-center gap-3.5 bg-[#131722]/80 backdrop-blur-md rounded-lg text-[13px] font-mono pointer-events-none shadow-md"
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[#787b86]">O</span>
        <span style={{ color }}>{fmtPrice(hoveredCandle.open)}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-[#787b86]">H</span>
        <span style={{ color }}>{fmtPrice(hoveredCandle.high)}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-[#787b86]">L</span>
        <span style={{ color }}>{fmtPrice(hoveredCandle.low)}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-[#787b86]">C</span>
        <span style={{ color }}>{fmtPrice(hoveredCandle.close)}</span>
      </div>
      <div className="flex items-center gap-1.5 ml-1">
        <span className="text-[#787b86]">V</span>
        <span className="text-[#d1d4dc]">{fmt(hoveredCandle.volume)}</span>
      </div>
    </div>
  );
}
