/**
 * WebSocket client for real-time slot event streaming.
 * Auto-reconnects with exponential backoff on disconnect.
 */
import * as SecureStore from "expo-secure-store";

const WS_BASE = process.env.EXPO_PUBLIC_WS_URL ?? "ws://localhost:8000/api/v1";

export type SlotEvent = {
  event: "slot_available" | "slot_filled";
  slot_id: string;
  clinic_id: string;
  clinic_name: string;
  start_time: string;
  duration_minutes: number;
  notified_count?: number;
};

type EventHandler = (event: SlotEvent) => void;

class SlotWebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Set<EventHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30_000;

  async connect(): Promise<void> {
    const token = await SecureStore.getItemAsync("access_token");
    if (!token) {
      console.warn("[WS] No auth token — skipping connection");
      return;
    }

    const url = `${WS_BASE}/ws?token=${encodeURIComponent(token)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("[WS] Connected to slot event stream");
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data: SlotEvent = JSON.parse(event.data as string);
        this.handlers.forEach((handler) => handler(data));
      } catch {
        console.warn("[WS] Failed to parse message:", event.data);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code ${event.code})`);
      if (event.code !== 4001) {
        // 4001 = auth failure, don't retry
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error("[WS] Error:", error);
    };
  }

  private scheduleReconnect(): void {
    const delay = Math.min(
      1000 * 2 ** this.reconnectAttempts,
      this.maxReconnectDelay
    );
    this.reconnectAttempts++;
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close(1000, "Client disconnect");
    this.ws = null;
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }
}

export const slotWebSocket = new SlotWebSocketService();
