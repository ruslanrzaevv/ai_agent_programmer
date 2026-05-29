// src/context/AuthContext.jsx

import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { me } from "../api/authApi";

const AuthContext =
  createContext();

export function AuthProvider({
  children,
}) {

  const [user,
    setUser] =
    useState(null);

  const [loading,
    setLoading] =
    useState(true);

  async function loadUser() {

    const token =
      localStorage.getItem(
        "access_token"
      );

    if (!token) {
      setLoading(false);
      return;
    }

    try {

      const response =
        await me();

      setUser(
        response.data
      );

    } catch (error) {

      localStorage.removeItem(
        "access_token"
      );

      localStorage.removeItem(
        "refresh_token"
      );

      setUser(null);
    }

    setLoading(false);
  }

  useEffect(() => {
    loadUser();
  }, []);

  function logout() {

    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "refresh_token"
    );

    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        logout,
        loading,
        loadUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(
    AuthContext
  );
}