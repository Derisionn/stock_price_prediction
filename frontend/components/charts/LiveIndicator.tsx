'use client';

import React from 'react';
import { useChartStore } from '@/store/chartStore';
import clsx from 'clsx';

export function LiveIndicator() {
  const { isConnected, isLive, marketState } = useChartStore();

  const isMarketOpen = marketState?.is_open ?? true;

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-[#161a1e]/90 border border-white/[0.06] select-none text-[#848e9c]" style={{ padding: '8px 14px' }}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#848e9c] animate-pulse" />
        <span className="text-xs font-semibold tracking-wider font-mono">CONNECTING</span>
      </div>
    );
  }

  if (!isMarketOpen) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-[#241517]/40 border border-[#f6465d]/20 select-none text-[#f6465d]" style={{ padding: '8px 14px' }}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#f6465d] shadow-[0_0_8px_rgba(246,70,93,0.5)]" />
        <span className="text-xs font-semibold tracking-wider font-mono uppercase">
          {marketState?.message || 'MARKET CLOSED'}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 rounded-lg bg-[#0d1f16]/60 border border-[#0ecb81]/20 select-none text-[#0ecb81] shadow-[0_0_15px_rgba(14,203,129,0.05)]" style={{ padding: '8px 14px' }}>
      <span
        className={clsx(
          'w-1.5 h-1.5 rounded-full bg-[#0ecb81]',
          isLive && 'animate-pulse shadow-[0_0_8px_rgba(14,203,129,0.6)]'
        )}
      />
      <span className="text-xs font-bold tracking-widest font-mono">
        {isLive ? 'LIVE FEED' : 'MARKET OPEN'}
      </span>
    </div>
  );
}
