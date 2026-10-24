/**
 * Zustand auth store — persists token in SecureStore (encrypted on-device).
 */
import * as SecureStore from "expo-secure-store";
import { create } from "zustand";
import { authApi, User } from "../services/api";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: true,

  login: async (email, password) => {
    const { data } = await authApi.login(email, password);
    await SecureStore.setItemAsync("access_token", data.access_token);
    set({ user: data.user, token: data.access_token });
  },

  logout: async () => {
    await SecureStore.deleteItemAsync("access_token");
    set({ user: null, token: null });
  },

  restoreSession: async () => {
    try {
      const token = await SecureStore.getItemAsync("access_token");
      if (token) {
        const { data: user } = await authApi.me();
        set({ user, token, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      await SecureStore.deleteItemAsync("access_token");
      set({ user: null, token: null, isLoading: false });
    }
  },
}));
