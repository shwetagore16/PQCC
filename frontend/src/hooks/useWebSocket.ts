// frontend/src/hooks/useWebSocket.ts — Generic, auto-reconnecting WebSocket hook.

import { useCallback, useEffect, useRef, useState } from "react";

type WSStatus = "connecting" | "open" | "closed" | "error";

interface UseWebSocketOptions<T> {
  /** WebSocket URL. Pass null/undefined to disable. */
  url: string | null | undefined;
  /** Called for every parsed JSON message received. */
  onMessage: (data: T) => void;
  /** Auto-reconnect after this many ms (0 to disable). Default: 3000 */
  reconnectDelay?: number;
  /** Maximum reconnect attempts (0 = infinite). Default: 0 */
  maxRetries?: number;
}

interface UseWebSocketReturn {
  status:    WSStatus;
  send:      (payload: unknown) => void;
  reconnect: () => void;
}

export function useWebSocket<T = unknown>({
  url,
  onMessage,
  reconnectDelay = 3000,
  maxRetries = 0,
}: UseWebSocketOptions<T>): UseWebSocketReturn {
  const [status, setStatus] = useState<WSStatus>("closed");
  const wsRef       = useRef<WebSocket | null>(null);
  const retryRef    = useRef<number>(0);
  const timerRef    = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onMsgRef    = useRef(onMessage);

  // Keep onMessage stable across renders
  useEffect(() => { onMsgRef.current = onMessage; }, [onMessage]);

  const connect = useCallback(() => {
    if (!url) return;

    wsRef.current?.close();
    setStatus("connecting");

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen  = () => { setStatus("open");  retryRef.current = 0; };
    ws.onerror = () => { setStatus("error"); };
    ws.onclose = () => {
      setStatus("closed");
      if (reconnectDelay > 0 && (maxRetries === 0 || retryRef.current < maxRetries)) {
        retryRef.current += 1;
        timerRef.current = setTimeout(connect, reconnectDelay);
      }
    };
    ws.onmessage = (ev: MessageEvent) => {
      try {
        const parsed = JSON.parse(ev.data) as T;
        onMsgRef.current(parsed);
      } catch {
        /* ignore non-JSON frames */
      }
    };
  }, [url, reconnectDelay, maxRetries]);

  useEffect(() => {
    connect();
    return () => {
      timerRef.current && clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((payload: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  return { status, send, reconnect: connect };
}
