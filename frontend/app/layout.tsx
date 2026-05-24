import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'TradePro — Professional Realtime Trading Charts',
  description:
    'Professional Binance-style realtime stock and crypto trading charts with live WebSocket streaming, candlestick analysis, and smart timeframe switching.',
  keywords: ['trading', 'chart', 'stocks', 'crypto', 'realtime', 'candlestick', 'TradingView'],
  openGraph: {
    title: 'TradePro — Professional Realtime Trading Charts',
    description: 'Binance-style realtime trading charts powered by TradingView Lightweight Charts',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-[#0b0e11] text-[#eaecef] font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
