'use client';

import React from 'react';
import { useChartStore } from '@/store/chartStore';
import clsx from 'clsx';

function formatPrice(price: number): string {
  if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return price.toFixed(2);
}

function formatChange(change: number): string {
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(2)}`;
}

function formatPercent(pct: number): string {
  const sign = pct >= 0 ? '+' : '';
  return `${sign}${pct.toFixed(2)}%`;
}

export function PriceHeader() {
  const { symbol, priceInfo } = useChartStore();

  if (!priceInfo) {
    return (
      <div className="flex items-center gap-4 animate-pulse">
        <div className="h-9 w-32 bg-[#1e2329] rounded-lg" />
        <div className="h-9 w-40 bg-[#1e2329] rounded-lg" />
      </div>
    );
  }

  const isPositive = priceInfo.change >= 0;

  return (
    <div className="flex items-center gap-6 flex-wrap">
      {/* Symbol Block */}
      <div className="flex items-center gap-3 select-none">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#f0b90b] to-[#d4a017] flex items-center justify-center shadow-md">
          <span className="text-black text-xs font-black">{symbol.charAt(0)}</span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-baseline gap-1">
            <span className="text-[#eaecef] text-lg font-black tracking-wide leading-none">{symbol}</span>
            <span className="text-[#848e9c] text-xs font-medium">/USD</span>
          </div>
          <span className="text-[#485563] text-[9px] uppercase font-bold tracking-wider leading-none mt-1">
            US Equity
          </span>
        </div>
      </div>

      {/* Separator Line */}
      <div className="h-8 w-[1px] bg-[#1e2329] hidden sm:block" />

      {/* Price & Change Block */}
      <div className="flex items-center gap-3.5 flex-wrap">
        {/* Large Price */}
        <span
          className={clsx(
            'text-3xl font-black font-mono tracking-tight transition-colors duration-300 select-all',
            isPositive ? 'text-[#0ecb81]' : 'text-[#f6465d]'
          )}
        >
          {formatPrice(priceInfo.price)}
        </span>

        {/* Change Badge */}
        <div
          className={clsx(
            'px-2.5 py-1 rounded-md text-xs font-bold font-mono flex items-center gap-1.5 shadow-inner select-all',
            isPositive 
              ? 'bg-[#0ecb81]/10 text-[#0ecb81]' 
              : 'bg-[#f6465d]/10 text-[#f6465d]'
          )}
        >
          <span>{formatChange(priceInfo.change)}</span>
          <span>({formatPercent(priceInfo.changePercent)})</span>
        </div>
      </div>
    </div>
  );
}
