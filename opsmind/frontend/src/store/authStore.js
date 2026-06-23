import { create } from "zustand";
import { authAPI } from "../services/api";

export const useAuthStore = create((set, get) => ({
  user: null,
  loading: false,
  error: null,
  initialized: false,

  // ── Init ────────────────────────────────────────────────────────────────────
  init: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) { set({ initialized: true }); return; }
    try {
      const { data } = await authAPI.me();
      set({ user: data, initialized: true });
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ initialized: true });
    }
  },

  // ── Register ────────────────────────────────────────────────────────────────
  register: async (formData) => {
    set({ loading: true, error: null });
  
    try {
      const { data } = await authAPI.register(formData);
  
      set({ loading: false });
  
      return {
        ok: true,
        target: data.target,
      };
    } catch (e) {
      const msg = e.response?.data?.detail || "Registration failed";
  
      set({
        error: msg,
        loading: false,
      });
  
      return {
        ok: false,
        error: msg,
      };
    }
  },
  // ── Login ───────────────────────────────────────────────────────────────────
  login: async (identifier, password) => {
    set({ loading: true, error: null });
  
    try {
      const { data } = await authAPI.login(identifier, password);
  
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
  
      const me = await authAPI.me();
  
      set({
        user: me.data,
        loading: false,
      });
  
      return { ok: true };
    } catch (e) {
      const msg = e.response?.data?.detail || "Invalid credentials";
  
      set({
        error: msg,
        loading: false,
      });
  
      return {
        ok: false,
        error: msg,
      };
    }
  },  // ── Google ──────────────────────────────────────────────────────────────────
  googleLogin: async (idToken) => {
    set({ loading: true, error: null });
    try {
      const { data } = await authAPI.google(idToken);
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      const me = await authAPI.me();
      set({ user: me.data, loading: false });
      return { ok: true };
    } catch (e) {
      set({ error: "Google auth failed", loading: false });
      return { ok: false };
    }
  },

  // ── Logout ──────────────────────────────────────────────────────────────────
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null });
  },

  clearError: () => set({ error: null }),
}));