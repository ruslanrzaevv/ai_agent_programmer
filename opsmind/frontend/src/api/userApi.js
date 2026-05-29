// src/api/userApi.js

import api from "./axios";

export const getMe =
  () =>
    api.get(
      "/users/me"
    );

export const updateMe =
  (data) =>
    api.patch(
      "/users/me",
      data
    );

export const deleteMe =
  () =>
    api.delete(
      "/users/me"
    );