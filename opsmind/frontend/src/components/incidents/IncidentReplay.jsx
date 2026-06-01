import { useState, useEffect, useRef } from "react";
import { COLORS, SEV_CONFIG } from "../../utils/constants";
import { Button, Card, Modal, Spinner } from "../ui";
import { useIncidentStore } from "../../store/incidentStore";

export default function IncidentReplay({ incident, onClose }) {
  const [timeline, setTimeline] = useState([]);
  const [currentMinute, setCurrentMinute] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);
  const { fetchReplay } = useIncidentStore();

  useEffect(() => {
    setLoading(true);
    fetchReplay(incident.id).then((data) => {
      setTimeline(data || []);
      setLoading(false);
    });
  }, [incident.id]);

  const maxMinute = timeline.length > 0 ? Math.max(...timeline.map(t => t.minute)) : 0;
  const current = timeline.find(t => t.minute === currentMinute) || timeline[0];
  const sev = SEV_CONFIG[incident.severity] || SEV_CONFIG.low;
  const maxErr = Math.max(...timeline.map(t => t.error_count || 0), 1);

  useEffect(() => {
    if (playing) {
      timerRef.current = setInterval(() => {
        setCurrentMinute(m => {
          if (m >= maxMinute) { setPlaying(false); return m; }
          return m + 1;
        });
      }, 700);
    }
    return () => clearInterval(timerRef.current);
  }, [playing, maxMinute]);

  return (
    <Modal onClose={onClose} width={720}>
      <Card style={{ padding: 30 }} glow="rgba(79,142,247,0.07)">
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
          <div>
            <div style={{ fontSize: 11, color: COLORS.accent, fontFamily: "'Space Mono', monospace",
              letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 6 }}>⏮ Incident Replay</div>
            <div style={{ fontSize: 15, fontWeight: 500, color: COLORS.textPrimary, maxWidth: 500 }}>
              {incident.title}
            </div>
          </div>
          <button onClick={onClose} style={{
            background: "none", border: `1px solid ${COLORS.border}`,
            color: COLORS.textSecondary, width: 32, height: 32, borderRadius: 8,
            cursor: "pointer", fontSize: 16, flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>✕</button>
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}><Spinner size={32} /></div>
        ) : timeline.length === 0 ? (
          <div style={{ textAlign: "center", padding: 40, color: COLORS.textMuted }}>No timeline data available</div>
        ) : (
          <>
            {/* Stats */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 22 }}>
              {[
                { label: "Minute",   value: `+${currentMinute}`,              color: COLORS.accent  },
                { label: "Errors",   value: current?.error_count || 0,        color: (current?.error_count || 0) > 10 ? COLORS.red : COLORS.orange },
                { label: "CPU",      value: `${current?.cpu_percent ?? "?"}%`, color: (current?.cpu_percent || 0) > 80 ? COLORS.red : COLORS.green  },
                { label: "Memory",   value: current?.memory_mb ? `${Math.round(current.memory_mb)}MB` : "—", color: COLORS.textSecondary },
              ].map(s => (
                <div key={s.label} style={{ background: COLORS.bg, borderRadius: 9, padding: "12px",
                  border: `1px solid ${COLORS.border}`, textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
                    textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 600, color: s.color,
                    fontFamily: "'Space Mono', monospace" }}>{s.value}</div>
                </div>
              ))}
            </div>

            {/* Event label */}
            {current?.event && (
              <div style={{ background: COLORS.bg, borderRadius: 8, padding: "9px 14px",
                border: `1px solid ${COLORS.border}`, marginBottom: 20,
                fontSize: 12, color: COLORS.textSecondary, fontFamily: "'Space Mono', monospace" }}>
                <span style={{ color: COLORS.textMuted }}>event › </span>{current.event}
              </div>
            )}

            {/* Error bars */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace",
                textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Error rate</div>
              <div style={{ display: "flex", gap: 3, alignItems: "flex-end", height: 56 }}>
                {timeline.map((t, i) => {
                  const h = Math.max((t.error_count / maxErr) * 52, 4);
                  const active = t.minute === currentMinute;
                  const past = t.minute <= currentMinute;
                  return (
                    <div key={i} onClick={() => { setPlaying(false); setCurrentMinute(t.minute); }}
                      title={`+${t.minute}min — ${t.error_count} errors`}
                      style={{
                        flex: 1, height: h, borderRadius: 3, cursor: "pointer", transition: "all 0.25s",
                        background: active ? COLORS.red : past ? `${COLORS.red}55` : COLORS.border,
                        boxShadow: active ? `0 0 10px ${COLORS.red}70` : "none",
                      }} />
                  );
                })}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5 }}>
                <span style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace" }}>+0m</span>
                <span style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace" }}>+{maxMinute}m</span>
              </div>
            </div>

            {/* Scrubber */}
            <input type="range" min={0} max={maxMinute} value={currentMinute}
              onChange={e => { setPlaying(false); setCurrentMinute(Number(e.target.value)); }}
              style={{ width: "100%", accentColor: COLORS.accent, cursor: "pointer", marginBottom: 20 }} />

            {/* Controls */}
            <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
              <Button small onClick={() => { setPlaying(false); setCurrentMinute(0); }}>⏮ Reset</Button>
              <Button small primary onClick={() => setPlaying(p => !p)} style={{ minWidth: 90 }}>
                {playing ? "⏸ Pause" : "▶ Play"}
              </Button>
              <Button small onClick={() => setCurrentMinute(m => Math.min(m + 1, maxMinute))}>Step ›</Button>
            </div>
          </>
        )}
      </Card>
    </Modal>
  );
}