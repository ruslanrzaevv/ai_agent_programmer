import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { useProjectStore } from "./store/projectStore";
import { useLogStore } from "./store/logStore";
import { useIncidentStore } from "./store/incidentStore";
import { wsService } from "./services/websocket";
import AppLayout from "./components/layout/AppLayout";
import AuthPage from "./components/auth/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import IncidentsPage from "./pages/IncidentsPage";
import LogsPage from "./pages/LogsPage";
import ProjectsPage from "./pages/ProjectsPage";
import SettingsPage from "./pages/SettingsPage";
import { Spinner } from "./components/ui";
import { COLORS } from "./utils/constants";

// ─── Глобальный WebSocket — работает на всех страницах ────────────────────────
function GlobalWebSocket() {
  const { activeProject } = useProjectStore();
  const pushLog     = useLogStore((s) => s.pushRealtime);
  const addIncident = useIncidentStore((s) => s.addRealtime);

  useEffect(() => {
    if (!activeProject?.id) return;

    // Подключаемся глобально — соединение НЕ рвётся при смене страницы
    wsService.connect(activeProject.id);

    const offLog = wsService.on("log", (msg) => {
      if (msg.data) pushLog(msg.data);
    });

    const offIncident = wsService.on("incident_created", (msg) => {
      if (msg) addIncident(msg);
    });

    // Держим соединение живым
    const ping = setInterval(() => wsService.ping(), 25000);

    return () => {
      offLog();
      offIncident();
      clearInterval(ping);
      // НЕ вызываем wsService.disconnect() — соединение остаётся
    };
  }, [activeProject?.id, pushLog, addIncident]);

  return null; // Не рендерит ничего
}

// ─── Auth guard ────────────────────────────────────────────────────────────────
function ProtectedRoute({ children }) {
  const { user, initialized } = useAuthStore();
  if (!initialized) {
    return (
      <div style={{
        minHeight: "100vh", display: "flex",
        alignItems: "center", justifyContent: "center",
        background: COLORS.bg,
      }}>
        <Spinner size={32} />
      </div>
    );
  }
  return user ? children : <Navigate to="/login" replace />;
}

// ─── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const { init, user }          = useAuthStore();
  const { fetch: fetchProjects } = useProjectStore();

  useEffect(() => { init(); }, []);

  useEffect(() => {
    if (user) fetchProjects();
  }, [user]);

  return (
    <>
      {user && <GlobalWebSocket />}

      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" replace /> : <AuthPage />}
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index          element={<DashboardPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="logs"      element={<LogsPage />} />
          <Route path="projects"  element={<ProjectsPage />} />
          <Route path="settings"  element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}