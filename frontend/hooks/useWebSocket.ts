'use client';

import { useEffect, useState, useCallback } from 'react';
import { wsService } from '@/services/websocket';

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: unknown | null;
  send: (data: object) => void;
  subscribe: (symbol: string) => void;
  unsubscribe: (symbol: string) => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(() => wsService.isConnected);
  const [lastMessage, setLastMessage] = useState<unknown | null>(null);

  useEffect(() => {
    // Connect on mount
    wsService.connect();

    // Register handlers
    const offMessage = wsService.onMessage((data) => {
      setLastMessage(data);
    });

    const offStatus = wsService.onStatus((connected) => {
      setIsConnected(connected);
    });

    return () => {
      offMessage();
      offStatus();
    };
  }, []);

  const send = useCallback((data: object) => {
    wsService.send(data);
  }, []);

  const subscribe = useCallback((symbol: string) => {
    wsService.subscribe(symbol);
  }, []);

  const unsubscribe = useCallback((symbol: string) => {
    wsService.unsubscribe(symbol);
  }, []);

  return { isConnected, lastMessage, send, subscribe, unsubscribe };
}
