'use client';

import React from 'react';
import { useChartStore } from '@/store/chartStore';
import clsx from 'clsx';

export function SymbolSearch() {
  const { symbol } = useChartStore();

  return (
    <div className="relative">
      <div
        style={{ padding: '8px 14px' }}
        className={clsx(
          "flex items-center gap-3 bg-[#161a1e]/90 border border-white/[0.06] text-sm font-semibold rounded-lg shadow-sm text-[#eaecef]"
        )}
      >
        <span className="flex items-center gap-1.5 select-none">
          <span className="text-[#f0b90b] font-bold font-mono tracking-wider">{symbol}</span>
          <span className="text-white/20 text-xs font-mono">/</span>
          <span className="text-[#848e9c] text-xs font-semibold font-mono">USD</span>
        </span>
      </div>
    </div>
  );
}

