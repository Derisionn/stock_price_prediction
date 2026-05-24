'use client';

/* eslint-disable react-hooks/refs */

import React from 'react';
import { useChartStore } from '@/store/chartStore';

function formatTime(timestamp: number): { date: string; time: string } {
  const d = new Date(timestamp * 1000);
  const date = d.toISOString().split('T')[0];
  const time = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  return { date, time };
}

function fmtPrice(n: number | undefined): string {
  if (n === undefined) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
}

export function FloatingTooltip() {
  const { hoveredCandle, crosshairPoint } = useChartStore();
  const ref = React.useRef<HTMLDivElement>(null);

  if (!hoveredCandle || !crosshairPoint) return null;

  const { date, time } = formatTime(hoveredCandle.time);

  // Measure parent container and tooltip itself dynamically
  const parentWidth = ref.current?.parentElement?.clientWidth || 800;
  const parentHeight = ref.current?.parentElement?.clientHeight || 500;
  const tooltipWidth = ref.current?.clientWidth || 200;
  const tooltipHeight = ref.current?.clientHeight || 80;

  // Smart flip horizontal
  let left = crosshairPoint.x + 15;
  if (left + tooltipWidth > parentWidth) {
    left = crosshairPoint.x - tooltipWidth - 15; // Flip to the left side of the cursor
  }

  // Smart flip vertical
  let top = crosshairPoint.y + 15;
  if (top + tooltipHeight > parentHeight) {
    top = crosshairPoint.y - tooltipHeight - 15; // Flip upward
  }

  const tooltipStyle: React.CSSProperties = {
    left,
    top,
    padding: '12px 18px',
    borderRadius: '8px',
  };

  return (
    <div
      ref={ref}
      style={tooltipStyle}
      className="absolute z-20 flex flex-col gap-2.5 bg-[#2b3139]/95 backdrop-blur-md text-xs pointer-events-none shadow-2xl min-w-[200px] font-sans transition-all duration-75"
    >
      <div className="flex justify-between items-center text-[#848e9c]">
        <span>{date}</span>
        <span>{time}</span>
      </div>
      <div className="text-[#eaecef] font-bold text-base">
        {fmtPrice(hoveredCandle.close)}
      </div>
    </div>
  );
}
