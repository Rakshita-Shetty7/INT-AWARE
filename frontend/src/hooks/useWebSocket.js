import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Reusable WebSocket hook for live streaming telemetry and threat alerts.
 * Automatically manages connection state, reconnects on drop, and handles ping/pong keepalive.
 */
export function useWebSocket(endpointPath, onMessage) {
  const [status, setStatus] = useState('CONNECTING'); // 'CONNECTING' | 'LIVE' | 'DISCONNECTED'
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Keep callback reference updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    // Clear any existing reconnect timer
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Use current window.location.host so it seamlessly routes via Vite proxy
      const wsUrl = `${protocol}//${window.location.host}${endpointPath}`;

      setStatus('CONNECTING');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('LIVE');
        // Setup ping keepalive every 15s
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const parsed = JSON.parse(event.data);
          if (onMessageRef.current) {
            onMessageRef.current(parsed);
          }
        } catch (err) {
          console.debug('[WS] Non-JSON message received:', event.data);
        }
      };

      ws.onerror = (err) => {
        console.debug(`[WS] Connection error on ${endpointPath}`);
      };

      ws.onclose = () => {
        setStatus('DISCONNECTED');
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        // Attempt reconnection after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (e) {
      setStatus('DISCONNECTED');
      reconnectTimeoutRef.current = setTimeout(connect, 4000);
    }
  }, [endpointPath]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { status };
}

export default useWebSocket;
