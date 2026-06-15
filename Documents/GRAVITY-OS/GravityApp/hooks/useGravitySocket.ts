import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const WS_BASE = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');

type GravityEvent =
  | { event: 'HEARTBEAT'; data: { ts: string; connected?: boolean } }
  | { event: 'NUDGE'; data: NudgeData }
  | { event: 'HABIT_COMPLETED'; data: HabitCompletedData }
  | { event: 'LAYOUT_UPDATE'; data: object }
  | { event: 'CYCLE_REVIEW_READY'; data: { goal_id: number; cycle_end: string } };

interface NudgeData {
  id: number;
  category: string;
  intensity: string;
  message: string;
  sub_message: string | null;
  action_label: string;
  sent_at: string;
}

interface HabitCompletedData {
  habit_id: number;
  habit_name: string;
  is_non_negotiable: boolean;
  date: string;
}

interface UseGravitySocketOptions {
  onNudge?: (data: NudgeData) => void;
  onCycleReviewReady?: (data: { goal_id: number; cycle_end: string }) => void;
}

export function useGravitySocket(options: UseGravitySocketOptions = {}) {
  const { token, userId } = useAuthStore();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelayRef = useRef(2000);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!token || !userId || !mountedRef.current) return;

    const url = `${WS_BASE}/ws/${userId}?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectDelayRef.current = 2000;
    };

    ws.onmessage = (event) => {
      try {
        const msg: GravityEvent = JSON.parse(event.data);

        switch (msg.event) {
          case 'HEARTBEAT':
            // Send heartbeat back
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ event: 'HEARTBEAT' }));
            }
            break;

          case 'HABIT_COMPLETED':
            // Invalidate habits query so the list refreshes
            queryClient.invalidateQueries({ queryKey: ['habits'] });
            break;

          case 'NUDGE':
            // Invalidate nudge list + call optional handler
            queryClient.invalidateQueries({ queryKey: ['nudges'] });
            options.onNudge?.(msg.data);
            break;

          case 'LAYOUT_UPDATE':
            queryClient.invalidateQueries({ queryKey: ['device_state'] });
            break;

          case 'CYCLE_REVIEW_READY':
            options.onCycleReviewReady?.(msg.data);
            break;
        }
      } catch {
        // malformed message — ignore
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onclose = () => {
      wsRef.current = null;
      if (!mountedRef.current) return;
      // Exponential backoff: 2s → 4s → 8s → ... → 300s max
      const delay = Math.min(reconnectDelayRef.current, 300_000);
      reconnectDelayRef.current = delay * 2;
      reconnectTimeoutRef.current = setTimeout(() => {
        if (mountedRef.current) connect();
      }, delay);
    };
  }, [token, userId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendEvent = useCallback((event: string, data: object = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event, data }));
    }
  }, []);

  return { sendEvent };
}
