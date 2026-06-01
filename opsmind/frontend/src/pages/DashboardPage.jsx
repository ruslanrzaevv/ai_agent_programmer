import { useEffect, useState } from "react";
import { COLORS, SEV_CONFIG, STATUS_CONFIG } from "../utils/constants";
import { timeAgo } from "../utils/helpers";
import { Card, Badge, LiveDot, SectionTitle } from "../components/ui";
import { useProjectStore } from "../store/projectStore";
import { useIncidentStore } from "../store/incidentStore";
import { useLogStore } from "../store/logStore";
import { useWebSocket } from "../hooks/useWebSocket";
import IncidentDetail from "../components/incidents/IncidentDetail";
import IncidentReplay from "../components/incidents/IncidentReplay";
import { LOG_COLORS } from "../utils/constants";
import { healthAPI } from "../services/api";

function MetricCard({ label, value, unit, color, delta, icon }) {
  return (
    <Card style={{ padding: "20px 22px", flex: 1, minWidth: 0 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>{label}</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
            <span style={{ fontSize: 30, fontWeight: 600, color: color || COLORS.textPrimary,
              letterSpacing: "-0.02em", lineHeight: 1 }}>{value}</span>
            {unit && <span style={{ fontSize: 13, color: COLORS.textMuted }}>{unit}</span>}
          </div>
          {delta !== undefined && (
            <div style={{ fontSize: 11, color: delta > 0 ? COLORS.red : COLORS.green, marginTop: 5 }}>
              {delta > 0 ? "▲" : "▼"} {Math.abs(delta)}% vs yesterday
            </div>
          )}
        </div>
        <span style={{ fontSize: 22, opacity: 0.5 }}>{icon}</span>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const { activeProject } = useProjectStore();
  const { incidents, fetch: fetchIncidents, select, selected } = useIncidentStore();
  const { logs } = useLogStore();
  const [replay, setReplay] = useState(null);
  const [health, setHealth] = useState(null);
  const { connected } = useWebSocket(activeProject?.id);

  useEffect(() => {
    if (activeProject?.id) fetchIncidents(activeProject.id);
    healthAPI.get().then(r => setHealth(r.data)).catch(() => {});
  }, [activeProject?.id]);

  const open = incidents.filter(i => i.status !== "resolved" && i.status !== "ignored");
  const critical = incidents.filter(i => i.severity === "critical" && i.status !== "resolved");
  const errorLogs = logs.filter(l => l.level === "error" || l.level === "critical").slice(0, 5);

  return (
    <div style={{ padding: "32px 36px", maxWidth: 1100, animation: "fade-in 0.3s ease" }}>
      {/* Title */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 600, color: COLORS.textPrimary,
          letterSpacing: "-0.02em", marginBottom: 4 }}>Dashboard</h1>
        <div style={{ fontSize: 13, color: COLORS.textMuted, display: "flex", alignItems: "center", gap: 8 }}>
          {activeProject ? (
            <><LiveDot color={connected ? COLORS.green : COLORS.textMuted} />
              <span>{activeProject.name} · {activeProject.environment}</span></>
          ) : (
            <span>No project selected</span>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div style={{ display: "flex", gap: 12, marginBottom: 28, flexWrap: "wrap" }}>
        <MetricCard label="Open Incidents" value={open.length}
          color={open.length > 0 ? COLORS.red : COLORS.green} delta={open.length > 0 ? 2 : -1} icon="⚠" />
        <MetricCard label="Critical" value={critical.length}
          color={critical.length > 0 ? COLORS.red : COLORS.green} icon="🔴" />
        <MetricCard label="Live Errors" value={errorLogs.length}
          color={errorLogs.length > 0 ? COLORS.orange : COLORS.green} icon="⚡" />
        <MetricCard label="WS Status" value={connected ? "Live" : "Off"}
          color={connected ? COLORS.green : COLORS.textMuted} icon="◎" />
      </div>

      {/* Active Incidents */}
      <div style={{ marginBottom: 28 }}>
        <SectionTitle right={<Badge color={COLORS.red} glow={COLORS.redGlow} small>{open.length} open</Badge>}>
          Active Incidents
        </SectionTitle>
        {open.length === 0 ? (
          <Card style={{ padding: "32px", textAlign: "center" }}>
            <div style={{ fontSize: 28, marginBottom: 10, opacity: 0.3 }}>✓</div>
            <div style={{ color: COLORS.textMuted, fontSize: 13 }}>No active incidents</div>
          </Card>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {open.slice(0, 4).map(inc => {
              const sev = SEV_CONFIG[inc.severity] || SEV_CONFIG.low;
              return (
                <Card key={inc.id} hoverable onClick={() => select(inc)} style={{ padding: "15px 20px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", gap: 7, alignItems: "center", marginBottom: 5 }}>
                        <div style={{ width: 7, height: 7, borderRadius: "50%", background: sev.color,
                          boxShadow: `0 0 5px ${sev.color}`,
                          animation: "pulse-dot 2s infinite" }} />
                        <Badge color={sev.color} glow={sev.glow} small>{sev.label}</Badge>
                        <span style={{ fontSize: 11, color: COLORS.textMuted }}>{timeAgo(inc.started_at)}</span>
                      </div>
                      <div style={{ fontSize: 14, color: COLORS.textPrimary, fontWeight: 500,
                        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {inc.title}
                      </div>
                    </div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: sev.color,
                      fontFamily: "'Space Mono', monospace", marginLeft: 12 }}>
                      {inc.error_count}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Live error stream */}
      <div>
        <SectionTitle right={
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <LiveDot color={connected ? COLORS.red : COLORS.textMuted} />
            <span style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace" }}>
              {connected ? "realtime" : "paused"}
            </span>
          </div>
        }>
          Live Error Stream
        </SectionTitle>
        <Card style={{ padding: "8px 0" }}>
          {errorLogs.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: COLORS.textMuted, fontSize: 13 }}>
              No errors in stream
            </div>
          ) : errorLogs.map((log, i) => (
            <div key={log.id || i} style={{
              display: "flex", gap: 0, padding: "6px 18px",
              borderBottom: `1px solid ${COLORS.border}20`,
              fontFamily: "'Space Mono', monospace", fontSize: 11,
              animation: i === 0 ? "fade-in 0.3s ease" : "none",
            }}>
              <span style={{ color: COLORS.textMuted, width: 72, flexShrink: 0 }}>
                {new Date(log.timestamp).toLocaleTimeString("en", { hour12: false })}
              </span>
              <span style={{ color: LOG_COLORS[log.level] || COLORS.textMuted, width: 58,
                flexShrink: 0, textTransform: "uppercase", fontWeight: 700 }}>{log.level}</span>
              <span style={{ color: COLORS.accent, width: 100, flexShrink: 0 }}>{log.container_name}</span>
              <span style={{ color: COLORS.textSecondary, flex: 1,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{log.message}</span>
            </div>
          ))}
        </Card>
      </div>

      {/* Modals */}
      {selected && (
        <IncidentDetail incident={selected}
          onClose={() => useIncidentStore.getState().clearSelected()}
          onReplay={(inc) => { useIncidentStore.getState().clearSelected(); setReplay(inc); }} />
      )}
      {replay && <IncidentReplay incident={replay} onClose={() => setReplay(null)} />}
    </div>
  );
}