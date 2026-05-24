'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, X, ChevronDown } from 'lucide-react';
import { useChartStore } from '@/store/chartStore';
import { fetchSymbols } from '@/services/api';
import type { Symbol } from '@/types/candle';
import clsx from 'clsx';

export function SymbolSearch() {
  const { symbol, setSymbol } = useChartStore();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load symbols
  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await fetchSymbols(query || undefined);
        setSymbols(data);
      } catch {
        // fallback
      } finally {
        setLoading(false);
      }
    }
    if (isOpen) load();
  }, [query, isOpen]);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setTimeout(() => setQuery(''), 0);
    }
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleSelect(sym: string) {
    setSymbol(sym);
    setIsOpen(false);
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger button */}
      <button
        id="symbol-search-trigger"
        onClick={() => setIsOpen(!isOpen)}
        style={{ padding: '8px 14px' }}
        className={clsx(
          "flex items-center gap-3 bg-[#161a1e]/90 hover:bg-[#1a2026] border text-sm font-semibold transition-all duration-300 rounded-lg shadow-sm hover:shadow-md",
          isOpen 
            ? "border-[#f0b90b] shadow-[0_0_12px_rgba(240,185,11,0.15)] text-white" 
            : "border-white/[0.06] hover:border-[#f0b90b]/40 text-[#eaecef]"
        )}
      >
        <span className="flex items-center gap-1.5 select-none">
          <span className="text-[#f0b90b] font-bold font-mono tracking-wider">{symbol}</span>
          <span className="text-white/20 text-xs font-mono">/</span>
          <span className="text-[#848e9c] text-xs font-semibold font-mono">USD</span>
        </span>
        <div className="w-[1px] h-3.5 bg-white/10 mx-0.5" />
        <ChevronDown
          className={clsx(
            'w-3.5 h-3.5 text-[#848e9c] transition-transform duration-300',
            isOpen && 'rotate-180 text-[#f0b90b]'
          )}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-72 bg-[#1a1e26] border border-[#2b2f35] rounded-xl shadow-2xl shadow-black/50 z-50 overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-2 px-3 py-2.5 border-b border-[#2b2f35]">
            <Search className="w-4 h-4 text-[#848e9c] flex-shrink-0" />
            <input
              ref={inputRef}
              id="symbol-search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search symbols..."
              className="flex-1 bg-transparent text-[#eaecef] text-sm placeholder:text-[#485563] outline-none"
            />
            {query && (
              <button onClick={() => setQuery('')}>
                <X className="w-3.5 h-3.5 text-[#848e9c] hover:text-[#eaecef]" />
              </button>
            )}
          </div>

          {/* Results */}
          <div className="max-h-60 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-6">
                <div className="w-5 h-5 border-2 border-[#f0b90b]/30 border-t-[#f0b90b] rounded-full animate-spin" />
              </div>
            ) : symbols.length === 0 ? (
              <div className="text-center text-[#848e9c] text-sm py-6">No results found</div>
            ) : (
              symbols.map((s) => (
                <button
                  key={s.symbol}
                  id={`symbol-option-${s.symbol}`}
                  onClick={() => handleSelect(s.symbol)}
                  className={clsx(
                    'w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-[#2b2f35] transition-colors duration-100',
                    s.symbol === symbol && 'bg-[#f0b90b]/10'
                  )}
                >
                  <div>
                    <div className="text-sm font-semibold text-[#eaecef]">{s.symbol}</div>
                    <div className="text-xs text-[#848e9c]">{s.description}</div>
                  </div>
                  <span className="text-[#485563] text-xs uppercase">{s.type}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
