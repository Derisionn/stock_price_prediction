'use client';

import React from 'react';
import { TIMEFRAME_LABELS, type Timeframe } from '@/types/candle';
import { useChartStore } from '@/store/chartStore';
import clsx from 'clsx';

const TIMEFRAMES: Timeframe[] = ['1m', '5m', '15m', '1h', '4h', '1d'];

export function TimeframeSwitcher() {
  const { timeframe, setTimeframe } = useChartStore();

  return (
    <div className="flex items-center gap-1">
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf}
          id={`timeframe-${tf}`}
          onClick={() => setTimeframe(tf)}
          style={{
            padding: '8px 14px',
            borderRadius: '6px',
          }}
          className={clsx(
            'text-sm font-medium transition-colors duration-150 select-none',
            timeframe === tf
              ? 'bg-[#2b3139] text-[#eaecef]'
              : 'text-[#848e9c] hover:text-[#eaecef] hover:bg-[#2b3139]/50'
          )}
        >
          {TIMEFRAME_LABELS[tf]}
        </button>
      ))}
    </div>
  );
}
