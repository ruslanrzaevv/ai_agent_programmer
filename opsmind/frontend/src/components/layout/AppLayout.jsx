import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import { COLORS } from "../../utils/constants";

export default function AppLayout() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: COLORS.bg }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: "auto", minWidth: 0 }}>
        <Outlet />
      </main>
    </div>
  );
}