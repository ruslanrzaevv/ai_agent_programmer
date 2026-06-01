import { create } from "zustand";
import { projectsAPI } from "../services/api";

export const useProjectStore = create((set, get) => ({
  projects: [],
  activeProject: null,
  loading: false,
  error: null,

  fetch: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await projectsAPI.list();
      const projects = data;
      set({
        projects,
        activeProject: get().activeProject || projects[0] || null,
        loading: false,
      });
    } catch (e) {
      set({ error: e.response?.data?.detail || "Failed to load projects", loading: false });
    }
  },

  create: async (formData) => {
    set({ loading: true, error: null });
    try {
      const { data } = await projectsAPI.create(formData);
      set((s) => ({ projects: [...s.projects, data], loading: false, activeProject: data }));
      return { ok: true, project: data };
    } catch (e) {
      const msg = e.response?.data?.detail || "Failed to create project";
      set({ error: msg, loading: false });
      return { ok: false, error: msg };
    }
  },

  update: async (id, formData) => {
    try {
      const { data } = await projectsAPI.update(id, formData);
      set((s) => ({
        projects: s.projects.map((p) => (p.id === id ? data : p)),
        activeProject: s.activeProject?.id === id ? data : s.activeProject,
      }));
      return { ok: true };
    } catch (e) {
      return { ok: false, error: e.response?.data?.detail };
    }
  },

  delete: async (id) => {
    try {
      await projectsAPI.delete(id);
      set((s) => {
        const projects = s.projects.filter((p) => p.id !== id);
        return {
          projects,
          activeProject: s.activeProject?.id === id ? projects[0] || null : s.activeProject,
        };
      });
      return { ok: true };
    } catch (e) {
      return { ok: false };
    }
  },

  setActive: (project) => set({ activeProject: project }),
}));