// src/App.jsx

import {
  useState,
} from "react";

import {
  useAuth,
} from "./context/AuthContext";

import Sidebar from "./components/layout/Sidebar";

import AuthPage from "./pages/AuthPage";

import Dashboard from "./pages/Dashboard";

import LogsPage from "./pages/LogsPage";

import ProjectsPage from "./pages/ProjectsPage";

import SettingsPage from "./pages/SettingsPage";

export default function App() {
  const { user } =
    useAuth();

  const [page, setPage] =
    useState(
      "dashboard"
    );

  if (!user) {
    return (
      <AuthPage />
    );
  }

  return (
    <div
      style={{
        display: "flex",
      }}
    >
      <Sidebar
        active={page}
        setActive={
          setPage
        }
      />

      <main
        style={{
          flex: 1,
        }}
      >
        {page ===
          "dashboard" && (
          <Dashboard />
        )}

        {page ===
          "projects" && (
          <ProjectsPage />
        )}

        {page ===
          "logs" && (
          <LogsPage />
        )}

        {page ===
          "settings" && (
          <SettingsPage
            user={user}
          />
        )}
      </main>
    </div>
  );
}