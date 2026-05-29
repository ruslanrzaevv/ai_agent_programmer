// src/api/logApi.js

import api from "./axios";

export const getLogs =
  (
    projectId
  ) =>
    api.get(
      `/projects/${projectId}/logs`
    );