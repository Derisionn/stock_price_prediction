'use client';

import React, { useEffect } from 'react';
import { TradingChart } from '@/components/charts/TradingChart';
import { TimeframeSwitcher } from '@/components/charts/TimeframeSwitcher';
import { ChartTypeSwitcher } from '@/components/charts/ChartTypeSwitcher';
import { PriceHeader } from '@/components/charts/PriceHeader';
import { LiveIndicator } from '@/components/charts/LiveIndicator';
import { SymbolSearch } from '@/components/ui/SymbolSearch';
import { useRealtimeCandles } from '@/hooks/useRealtimeCandles';
import { useChartStore } from '@/store/chartStore';
import { fetchMarketState } from '@/services/api';

function MarketStatsBar() {
  const { candles, symbol } = useChartStore();

  // Compute 24h stats from candle data
  const stats = React.useMemo(() => {
    if (candles.length === 0) return null;
    const last = candles[candles.length - 1];
    const high24 = Math.max(...candles.map((c) => c.high));
    const low24 = Math.min(...candles.map((c) => c.low));
    const vol24 = candles.reduce((s, c) => s + c.volume, 0);
    return { last, high24, low24, vol24 };
  }, [candles]);

  if (!stats) return null;

  const fmt = (n: number) => n.toFixed(2);
  const fmtVol = (n: number) => {
    if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(2) + 'K';
    return n.toFixed(0);
  };

  return (
    <div className="flex items-center gap-5 text-xs overflow-x-auto scrollbar-hide select-none">
      {/* 24h High */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-white/40 font-medium font-mono">24H HIGH</span>
        <span className="text-[#0ecb81] font-mono font-semibold tracking-tight">{fmt(stats.high24)}</span>
      </div>

      {/* Divider */}
      <div className="h-3 w-[1px] bg-white/10 hidden sm:block" />

      {/* 24h Low */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-white/40 font-medium font-mono">24H LOW</span>
        <span className="text-[#f6465d] font-mono font-semibold tracking-tight">{fmt(stats.low24)}</span>
      </div>

      {/* Divider */}
      <div className="h-3 w-[1px] bg-white/10 hidden sm:block" />

      {/* 24h Volume */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-white/40 font-medium font-mono">24H VOL</span>
        <span className="text-[#eaecef] font-mono font-semibold tracking-tight">{fmtVol(stats.vol24)}</span>
      </div>

      {/* Divider */}
      <div className="h-3 w-[1px] bg-white/10 hidden sm:block" />

      {/* Symbol Tag */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-white/40 font-medium font-mono font-bold">SYM</span>
        <span className="text-[#f0b90b] font-semibold tracking-wider font-mono">{symbol}/USD</span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { setMarketState } = useChartStore();

  // Start realtime candle streaming
  useRealtimeCandles();

  // Fetch market state periodically
  useEffect(() => {
    async function loadMarketState() {
      try {
        const state = await fetchMarketState();
        setMarketState(state);
      } catch {}
    }
    loadMarketState();
    const interval = setInterval(loadMarketState, 30_000);
    return () => clearInterval(interval);
  }, [setMarketState]);

  return (
    <div className="flex flex-col h-screen bg-[#0b0e11] overflow-hidden">
      {/* ─── Top Navigation Bar ─── */}
      <header className="h-[72px] flex-shrink-0 relative z-50 backdrop-blur-xl bg-[#0b0e11]/85 transition-all duration-300 hover:bg-[#0b0e11]/90">
        {/* Subtle premium gold top gradient accent */}
        <div className="absolute top-0 left-0 right-0 h-[1.5px] bg-gradient-to-r from-transparent via-[#f0b90b]/25 to-transparent opacity-85 pointer-events-none" />
        
        {/* Soft inner glow */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/[0.01] to-transparent pointer-events-none" />

        <div className="h-full flex items-center justify-between px-[28px]">
          {/* Left Side: Logo + Divider + Ticker */}
          <div className="flex items-center">
            {/* Logo */}
            <div className="flex items-center gap-3.5 cursor-pointer group py-2 px-3 rounded-lg border border-transparent hover:border-white/[0.05] hover:bg-white/[0.02] transition-all duration-300 select-none">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#f0b90b] to-[#d4a017] flex items-center justify-center shadow-[0_0_12px_rgba(240,185,11,0.25)] transition-all duration-500 group-hover:scale-105 group-hover:shadow-[0_0_20px_rgba(240,185,11,0.45)] group-hover:rotate-3">
                <svg className="w-4.5 h-4.5 text-[#0b0e11] transition-transform duration-500 group-hover:scale-105" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span className="bg-gradient-to-r from-[#eaecef] via-[#eaecef] to-[#f0b90b] bg-clip-text text-transparent font-bold text-lg tracking-tight hidden sm:block transition-all duration-300 group-hover:opacity-90">
                Trade<span className="text-[#f0b90b] font-black">Pro</span>
              </span>
            </div>

            {/* Gap between logo and divider: 20px */}
            <div className="w-[20px] hidden sm:block" />

            {/* Vertical Separator */}
            <div className="h-6 w-[1px] bg-white/10 hidden sm:block" />

            {/* Gap between divider and ticker selector: 16px */}
            <div className="w-[16px] hidden sm:block" />

            {/* Symbol Selector */}
            <SymbolSearch />
          </div>

          {/* Right Side: Market Stats + Live Indicator */}
          <div className="flex items-center gap-6">
            {/* Market Stats */}
            <div className="hidden lg:flex">
              <MarketStatsBar />
            </div>

            {/* Live Indicator */}
            <LiveIndicator />
          </div>
        </div>
      </header>

      {/* ─── Chart Area ─── */}
      <main className="flex-1 min-h-0 px-6 pt-4 pb-3 overflow-hidden flex flex-col justify-start items-center gap-3">
        {/* Graph Header (Price + Timeframes) */}
        <div className="w-full max-w-5xl flex items-center justify-between px-1 mb-2">
          <PriceHeader />
          <div className="flex items-center gap-4">
            <ChartTypeSwitcher />
            <div className="w-[1px] h-6 bg-[#2b2f35]" />
            <TimeframeSwitcher />
          </div>
        </div>

        {/* Graph Canvas */}
        <div className="w-full max-w-5xl h-[520px] rounded-xl overflow-hidden">
          <TradingChart />
        </div>
      </main>

      {/* ─── Footer ─── */}
      <footer className="flex-shrink-0 flex items-center justify-between px-6 py-1.5 border-t border-[#2b2f35]/30 bg-[#0b0e11]">
        <span className="text-[#485563] text-xs">
          Powered by TradingView Lightweight Charts · Finnhub Realtime Data
        </span>
        <span className="text-[#485563] text-xs font-mono">
          {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
        </span>
      </footer>
    </div>
  );
}
