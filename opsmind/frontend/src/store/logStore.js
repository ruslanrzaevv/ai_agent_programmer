import { create } from "zustand";
import { logsAPI } from "../services/api";

const MAX_LOGS = 500;

export const useLogStore = create((set, get) => ({
  logs: [],
  loading: false,
  filter: "all",
  search: "",
  paused: false,

  fetch: async (projectId, params = {}) => {
    if (!projectId) return;
    set({ loading: true });
    try {
      const { data } = await logsAPI.list(projectId, {
        limit: 100,
        level: get().filter !== "all" ? get().filter : undefined,
        search: get().search || undefined,
        ...params,
      });
      set({ logs: data.items || [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  // Push one realtime log entry (from WebSocket)
  pushRealtime: (entry) => {
    if (get().paused) return;
    set((s) => ({
      logs: [entry, ...s.logs].slice(0, MAX_LOGS),
    }));
  },

  setFilter: (filter) => set({ filter }),
  setSearch: (search) => set({ search }),
  setPaused: (paused) => set({ paused }),
  clear: () => set({ logs: [] }),
}));