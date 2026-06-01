import { create } from "zustand";
import { incidentsAPI } from "../services/api";

export const useIncidentStore = create((set, get) => ({
  incidents: [],
  selected: null,
  replay: null,
  loading: false,
  error: null,
  filter: "all",

  fetch: async (projectId) => {
    if (!projectId) return;
    set({ loading: true, error: null });
    try {
      const params = {};
      const f = get().filter;
      if (f !== "all" && ["critical","high","medium","low"].includes(f)) params.severity = f;
      if (f !== "all" && ["open","acknowledged","resolved"].includes(f)) params.status_filter = f;

      const { data } = await incidentsAPI.list(projectId, params);
      set({ incidents: data.items || [], loading: false });
    } catch (e) {
      set({ error: "Failed to load incidents", loading: false });
    }
  },

  // Called from WebSocket when new incident arrives
  addRealtime: (incident) => {
    set((s) => ({ incidents: [incident, ...s.incidents] }));
  },

  select: async (incident) => {
    set({ selected: incident });
    // Fetch full details if needed
    try {
      const { data } = await incidentsAPI.get(incident.id);
      set({ selected: data });
    } catch {}
  },

  acknowledge: async (id) => {
    try {
      const { data } = await incidentsAPI.acknowledge(id);
      set((s) => ({
        incidents: s.incidents.map((i) => (i.id === id ? data : i)),
        selected: s.selected?.id === id ? data : s.selected,
      }));
      return { ok: true };
    } catch (e) {
      return { ok: false, error: e.response?.data?.detail };
    }
  },

  resolve: async (id) => {
    try {
      const { data } = await incidentsAPI.resolve(id);
      set((s) => ({
        incidents: s.incidents.map((i) => (i.id === id ? data : i)),
        selected: s.selected?.id === id ? data : s.selected,
      }));
      return { ok: true };
    } catch (e) {
      return { ok: false };
    }
  },

  explain: async (id, mode) => {
    try {
      const { data } = await incidentsAPI.explain(id, mode);
      return { ok: true, content: data.content };
    } catch {
      return { ok: false, content: "AI analysis unavailable" };
    }
  },

  ask: async (id, question) => {
    try {
      const { data } = await incidentsAPI.ask(id, question);
      return { ok: true, content: data.content };
    } catch {
      return { ok: false, content: "AI unavailable" };
    }
  },

  fetchReplay: async (id) => {
    try {
      const { data } = await incidentsAPI.replay(id);
      set({ replay: data });
      return data;
    } catch {
      return [];
    }
  },

  applyFix: async (id, confirmed) => {
    try {
      const { data } = await incidentsAPI.applyFix(id, confirmed);
      return { ok: true, ...data };
    } catch (e) {
      return { ok: false, error: e.response?.data?.detail };
    }
  },

  setFilter: (filter) => set({ filter }),
  clearSelected: () => set({ selected: null, replay: null }),
}));