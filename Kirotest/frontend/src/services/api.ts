/**
 * Axios API client with JWT auth interceptor.
 * All requests automatically attach the Bearer token from SecureStore.
 */
import axios, { AxiosInstance } from "axios";
import * as SecureStore from "expo-secure-store";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach JWT ──────────────────────────────────────────
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 ─────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      await SecureStore.deleteItemAsync("access_token");
      // Emit a global logout event — the navigation layer listens and redirects
      authEventEmitter.emit("logout");
    }
    return Promise.reject(error);
  }
);

// Simple event emitter for cross-module auth signalling
class AuthEventEmitter extends EventTarget {
  emit(event: string) {
    this.dispatchEvent(new Event(event));
  }
  on(event: string, handler: () => void) {
    this.addEventListener(event, handler);
  }
}
export const authEventEmitter = new AuthEventEmitter();

// ── API service functions ─────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; phone?: string }) =>
    api.post("/auth/register", data),

  login: (email: string, password: string) =>
    api.post<{ access_token: string; user: User }>("/auth/login", { email, password }),

  updateFcmToken: (fcm_token: string) =>
    api.post("/auth/fcm-token", { fcm_token }),

  me: () => api.get<User>("/auth/me"),
};

export const slotsApi = {
  getNearby: (lat: number, lng: number, radius_meters = 5000, appointment_type?: string) =>
    api.get<Slot[]>("/slots/nearby", {
      params: { lat, lng, radius_meters, appointment_type },
    }),

  activateStandby: (lat: number, lng: number, radius_meters = 5000, duration_seconds = 7200) =>
    api.post("/standby/activate", { lat, lng, radius_meters, duration_seconds }),

  deactivateStandby: () => api.post("/standby/deactivate"),
};

export const bookingsApi = {
  claim: (slot_id: string) =>
    api.post<ClaimResponse>("/bookings/claim", { slot_id }),

  confirm: (slot_id: string, notes?: string) =>
    api.post<BookingConfirmation>("/bookings/confirm", { slot_id, notes }),

  myBookings: () => api.get<BookingSummary[]>("/bookings/my"),

  cancel: (booking_id: string) =>
    api.post(`/bookings/${booking_id}/cancel`),
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: "patient" | "clinic_staff" | "clinic_admin";
  is_active: boolean;
  created_at: string;
}

export interface Slot {
  id: string;
  clinic_id: string;
  provider_id: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  appointment_type: string;
  status: string;
  provider_name?: string;
  clinic_name?: string;
  distance_meters?: number;
}

export interface ClaimResponse {
  status: "pending";
  slot_id: string;
  expires_in_seconds: number;
  message: string;
}

export interface BookingConfirmation {
  booking_id: string;
  slot_id: string;
  status: string;
  confirmed_at: string;
}

export interface BookingSummary {
  booking_id: string;
  slot_id: string;
  status: string;
  notes?: string;
  confirmed_at: string;
}
