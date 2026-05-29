// src/api/projectApi.js

import api from "./axios";

export const getProjects =
  () =>
    api.get(
      "/projects"
    );

export const createProject =
  (data) =>
    api.post(
      "/projects",
      data
    );

export const getProject =
  (id) =>
    api.get(
      `/projects/${id}`
    );

export const updateProject =
  (
    id,
    data
  ) =>
    api.patch(
      `/projects/${id}`,
      data
    );

export const deleteProject =
  (id) =>
    api.delete(
      `/projects/${id}`
    );

export const pauseProject =
  (id) =>
    api.post(
      `/projects/${id}/pause`
    );

export const resumeProject =
  (id) =>
    api.post(
      `/projects/${id}/resume`
    );