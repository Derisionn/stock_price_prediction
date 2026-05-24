'use client';

import React from 'react';
import { useChartStore } from '@/store/chartStore';
import clsx from 'clsx';

export function ChartTypeSwitcher() {
  const { chartType, setChartType } = useChartStore();

  return (
    <div className="flex items-center gap-1.5">
      <button
        onClick={() => setChartType('candlestick')}
        style={{
          padding: '8px 14px',
          borderRadius: '6px',
        }}
        className={clsx(
          'text-sm font-medium transition-colors duration-150 select-none',
          chartType === 'candlestick'
            ? 'bg-[#2b3139] text-[#eaecef]'
            : 'text-[#848e9c] hover:text-[#eaecef] hover:bg-[#2b3139]/50'
        )}
      >
        Candles
      </button>
      <button
        onClick={() => setChartType('area')}
        style={{
          padding: '8px 14px',
          borderRadius: '6px',
        }}
        className={clsx(
          'text-sm font-medium transition-colors duration-150 select-none',
          chartType === 'area'
            ? 'bg-[#2b3139] text-[#f0b90b]'
            : 'text-[#848e9c] hover:text-[#eaecef] hover:bg-[#2b3139]/50'
        )}
      >
        Area
      </button>
    </div>
  );
}
