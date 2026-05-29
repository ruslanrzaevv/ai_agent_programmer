// src/api/incidentApi.js

import api from "./axios";

export const getIncidents =
  () =>
    api.get(
      "/incidents"
    );

export const getIncident =
  (id) =>
    api.get(
      `/incidents/${id}`
    );

export const acknowledgeIncident =
  (id) =>
    api.post(
      `/incidents/${id}/acknowledge`
    );

export const resolveIncident =
  (id) =>
    api.post(
      `/incidents/${id}/resolve`
    );

export const getReplay =
  (id) =>
    api.get(
      `/incidents/${id}/replay`
    );

export const explainIncident =
  (
    id,
    level
  ) =>
    api.post(
      `/incidents/${id}/explain`,
      {
        level,
      }
    );

export const askAI =
  (
    id,
    question
  ) =>
    api.post(
      `/incidents/${id}/ask`,
      {
        question,
      }
    );

export const applyFix =
  (id) =>
    api.post(
      `/incidents/${id}/apply-fix`
    );