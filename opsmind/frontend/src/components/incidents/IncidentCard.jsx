import { COLORS, SEV_CONFIG, STATUS_CONFIG } from "../../utils/constants";
import { timeAgo } from "../../utils/helpers";
import { Badge, Card } from "../ui";

export default function IncidentCard({ incident, onClick }) {
  const sev = SEV_CONFIG[incident.severity] || SEV_CONFIG.low;
  const st = STATUS_CONFIG[incident.status] || STATUS_CONFIG.open;

  return (
    <Card hoverable onClick={() => onClick?.(incident)} style={{ padding: "18px 22px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Badges row */}
          <div style={{ display: "flex", gap: 7, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%", background: sev.color, flexShrink: 0,
              boxShadow: `0 0 6px ${sev.color}`,
              animation: incident.status === "open" ? "pulse-dot 2s infinite" : "none",
            }} />
            <Badge color={sev.color} glow={sev.glow} small>{sev.label}</Badge>
            <Badge color={st.color} small>{st.label}</Badge>
            <span style={{ fontSize: 11, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace" }}>
              {timeAgo(incident.started_at)}
            </span>
          </div>

          {/* Title */}
          <div style={{ fontSize: 14, color: COLORS.textPrimary, fontWeight: 500, marginBottom: 6,
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {incident.title}
          </div>

          {/* Meta */}
          <div style={{ fontSize: 12, color: COLORS.textMuted, display: "flex", gap: 14, flexWrap: "wrap" }}>
            <span>⚡ {incident.error_count} errors</span>
            {incident.affected_containers?.length > 0 && (
              <span>📦 {incident.affected_containers.slice(0, 2).join(", ")}
                {incident.affected_containers.length > 2 ? ` +${incident.affected_containers.length - 2}` : ""}
              </span>
            )}
            {incident.ai_explanation_senior && <span style={{ color: COLORS.accent }}>🤖 AI ready</span>}
          </div>
        </div>

        {/* Error count */}
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: sev.color,
            fontFamily: "'Space Mono', monospace" }}>{incident.error_count}</div>
          <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>errors</div>
        </div>
      </div>
    </Card>
  );
}