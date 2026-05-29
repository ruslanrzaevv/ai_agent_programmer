// src/api/authApi.js

import api from "./axios";

export const register = (data) =>
  api.post(
    "/auth/register",
    data
  );

export const login = (data) =>
  api.post(
    "/auth/login",
    data
  );

export const googleLogin = (
  data
) =>
  api.post(
    "/auth/google",
    data
  );

export const refreshToken = (
  refresh_token
) =>
  api.post(
    "/auth/refresh",
    {
      refresh_token,
    }
  );

export const sendCode = (
  target,
  purpose
) =>
  api.post(
    "/auth/send-code",
    null,
    {
      params: {
        target,
        purpose,
      },
    }
  );

export const verifyCode = (
  data
) =>
  api.post(
    "/auth/verify",
    data
  );

export const me = () =>
  api.get("/auth/me");