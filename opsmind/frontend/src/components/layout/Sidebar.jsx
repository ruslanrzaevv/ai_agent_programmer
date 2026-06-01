import { NavLink } from "react-router-dom";
import { COLORS } from "../../utils/constants";
import { LiveDot } from "../ui";
import { useProjectStore } from "../../store/projectStore";
import { useWebSocket } from "../../hooks/useWebSocket";

const NAV_ITEMS = [
  { path: "/",          icon: "⬡", label: "Dashboard"  },
  { path: "/incidents", icon: "⚠",  label: "Incidents"  },
  { path: "/logs",      icon: "≡",  label: "Live Logs"  },
  { path: "/projects",  icon: "◈",  label: "Projects"   },
  { path: "/settings",  icon: "⊙",  label: "Settings"   },
];

export default function Sidebar() {
  const { projects, activeProject, setActive } = useProjectStore();
  const { connected } = useWebSocket(activeProject?.id);

  return (
    <aside style={{
      width: 220, flexShrink: 0,
      background: COLORS.surface,
      borderRight: `1px solid ${COLORS.border}`,
      display: "flex", flexDirection: "column",
      minHeight: "100vh",
    }}>
      {/* Logo */}
      <div style={{ padding: "22px 20px 18px", borderBottom: `1px solid ${COLORS.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 10 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8,
            background: COLORS.accent, fontSize: 15,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: `0 0 14px ${COLORS.accent}50`,
          }}>⚡</div>
          <span style={{
            fontFamily: "'Space Mono', monospace", fontSize: 16,
            fontWeight: 700, color: COLORS.textPrimary, letterSpacing: "-0.01em",
          }}>OpsMind</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <LiveDot color={connected ? COLORS.green : COLORS.textMuted} />
          <span style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace" }}>
            {connected ? "live" : "connecting..."}
          </span>
        </div>
      </div>

      {/* Project switcher */}
      {projects.length > 0 && (
        <div style={{ padding: "12px 12px 0" }}>
          <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6, paddingLeft: 4 }}>
            Project
          </div>
          <select
            value={activeProject?.id || ""}
            onChange={(e) => setActive(projects.find((p) => p.id === e.target.value))}
            style={{
              width: "100%", padding: "7px 10px", borderRadius: 7,
              background: COLORS.bg, border: `1px solid ${COLORS.border}`,
              color: COLORS.textPrimary, fontSize: 12,
              fontFamily: "'DM Sans', sans-serif", cursor: "pointer", outline: "none",
            }}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Nav */}
      <nav style={{ flex: 1, padding: "14px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            style={({ isActive }) => ({
              display: "flex", alignItems: "center", gap: 10,
              padding: "9px 10px", borderRadius: 8,
              color: isActive ? COLORS.accent : COLORS.textSecondary,
              fontSize: 13, fontFamily: "'DM Sans', sans-serif",
              fontWeight: isActive ? 600 : 400,
              background: isActive ? `${COLORS.accent}15` : "transparent",
              borderLeft: isActive ? `2px solid ${COLORS.accent}` : "2px solid transparent",
              transition: "all 0.15s", textDecoration: "none",
            })}
          >
            <span style={{ fontSize: 15, width: 18, textAlign: "center" }}>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Status */}
      <div style={{ padding: "0 12px 20px" }}>
        <div style={{
          padding: "11px 12px", borderRadius: 8,
          background: COLORS.bg, border: `1px solid ${COLORS.border}`,
        }}>
          <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
            textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 5 }}>
            System
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <LiveDot color={COLORS.green} />
            <span style={{ fontSize: 11, color: COLORS.green }}>Operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
}