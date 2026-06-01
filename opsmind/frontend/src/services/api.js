import axios from "axios";
import { API_URL } from "../utils/constants";

// ─── Axios instance ────────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const aiAPI = {
  setupWizard: (category, message) =>
    api.post("/ai/setup-wizard", {
      category,
      message,
    }),

  analyzeSetup: (formData) =>
    api.post("/ai/analyze-setup", {
      form_data: formData,
    }),
    
  explainIssue: (issue, level) =>
      api.post("/ai/explain", {
        issue,
        level,
      }),
};

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        if (!refresh) throw new Error("No refresh token");
        const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: refresh,
        });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// ─── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (identifier, password) => api.post("/auth/login", { identifier, password }),
  google: (id_token) => api.post("/auth/google", { id_token }),
  refresh: (refresh_token) => api.post("/auth/refresh", { refresh_token }),
  me: () => api.get("/auth/me"),
  sendCode: (target, purpose = "register") =>
    api.post(`/auth/send-code?target=${encodeURIComponent(target)}&purpose=${purpose}`),
  verify: (target, code, purpose) =>
    api.post("/auth/verify", { target, code, purpose }),
};

// ─── Users ─────────────────────────────────────────────────────────────────────
export const usersAPI = {
  getMe: () => api.get("/users/me"),
  updateMe: (data) => api.patch("/users/me", data),
  deleteMe: () => api.delete("/users/me"),
};

// ─── Projects ──────────────────────────────────────────────────────────────────
export const projectsAPI = {
  list: () => api.get("/projects/"),
  create: (data) => api.post("/projects/", data),
  get: (id) => api.get(`/projects/${id}`),
  update: (id, data) => api.patch(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  pause: (id) => api.post(`/projects/${id}/pause`),
  resume: (id) => api.post(`/projects/${id}/resume`),
};

// ─── Incidents ─────────────────────────────────────────────────────────────────
export const incidentsAPI = {
  list: (projectId, params = {}) =>
    api.get("/incidents/", { params: { project_id: projectId, ...params } }),
  get: (id) => api.get(`/incidents/${id}`),
  acknowledge: (id) => api.post(`/incidents/${id}/acknowledge`),
  resolve: (id, note) => api.post(`/incidents/${id}/resolve`, { resolution_note: note }),
  replay: (id) => api.get(`/incidents/${id}/replay`),
  explain: (id, mode) => api.post(`/incidents/${id}/explain`, { mode, incident_id: id }),
  ask: (id, question) => api.post(`/incidents/${id}/ask`, { question, incident_id: id }),
  applyFix: (id, confirmed) => api.post(`/incidents/${id}/apply-fix`, { confirmed }),
};

// ─── Logs ──────────────────────────────────────────────────────────────────────
export const logsAPI = {
  list: (projectId, params = {}) =>
    api.get(`/projects/${projectId}/logs`, { params }),
};

// ─── Health ────────────────────────────────────────────────────────────────────
export const healthAPI = {
  get: () => api.get("/health"),
};

export default api;