import { useEffect, useRef } from "react";
import { COLORS, LOG_COLORS } from "../utils/constants";
import { Button, Card, LiveDot } from "../components/ui";
import { useLogStore } from "../store/logStore";
import { useProjectStore } from "../store/projectStore";
import { useWebSocket } from "../hooks/useWebSocket";

const LEVELS = ["all", "critical", "error", "warning", "info", "debug"];

export default function LogsPage() {
  const { activeProject }  = useProjectStore();
  const {
    logs, loading, filter, paused,
    fetch, setFilter, setPaused, clear,
  } = useLogStore();
  const { connected } = useWebSocket(activeProject?.id);
  const bottomRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (activeProject?.id) fetch(activeProject.id);
  }, [activeProject?.id]);

  useEffect(() => {
    if (!paused && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs.length, paused]);

  const filtered = filter === "all"
    ? logs
    : logs.filter(l => l.level === filter);

  return (
    <div style={{ padding: "32px 36px", maxWidth: 1100, animation: "fade-in 0.3s ease" }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        alignItems: "flex-start", marginBottom: 20,
      }}>
        <div>
          <h1 style={{
            fontSize: 26, fontWeight: 600, color: COLORS.textPrimary,
            letterSpacing: "-0.02em", marginBottom: 6,
          }}>Live Logs</h1>

          <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
            {/* Статус соединения */}
            {connected && !paused ? (
              <>
                <LiveDot />
                <span style={{ color: COLORS.green }}>Streaming in real-time</span>
              </>
            ) : paused ? (
              <span style={{ color: COLORS.yellow }}>⏸ Paused</span>
            ) : (
              <>
                <LiveDot color={COLORS.textMuted} />
                <span style={{ color: COLORS.textMuted }}>Connecting...</span>
              </>
            )}

            <span style={{ color: COLORS.border }}>·</span>
            <span style={{ color: COLORS.textMuted }}>
              {filtered.length} entries
            </span>

            {/* Мигающий индикатор новых логов */}
            {connected && !paused && logs.length > 0 && (
              <span style={{
                fontSize: 10, color: COLORS.accent,
                fontFamily: "'Space Mono', monospace",
                animation: "pulse-dot 1.5s infinite",
              }}>
                LIVE
              </span>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <Button small onClick={() => setPaused(!paused)}>
            {paused ? "▶ Resume" : "⏸ Pause"}
          </Button>
          <Button small onClick={clear}>Clear</Button>
        </div>
      </div>

      {/* Level filters */}
      <div style={{ display: "flex", gap: 7, marginBottom: 14, flexWrap: "wrap" }}>
        {LEVELS.map(l => (
          <button key={l} onClick={() => setFilter(l)} style={{
            padding: "4px 12px", borderRadius: 6, cursor: "pointer",
            fontFamily: "'Space Mono', monospace", fontSize: 10, fontWeight: 700,
            letterSpacing: "0.08em", textTransform: "uppercase", transition: "all 0.15s",
            background: filter === l
              ? `${LOG_COLORS[l] || COLORS.accent}20`
              : "transparent",
            color: filter === l
              ? (LOG_COLORS[l] || COLORS.accent)
              : COLORS.textMuted,
            border: `1px solid ${filter === l
              ? (LOG_COLORS[l] || COLORS.accent) + "50"
              : COLORS.border}`,
          }}>{l}</button>
        ))}
      </div>

      {/* Log stream */}
      <Card style={{
        maxHeight: "calc(100vh - 260px)",
        overflow: "auto",
        padding: "4px 0",
      }} ref={containerRef}>
        {filtered.length === 0 ? (
          <div style={{
            padding: 40, textAlign: "center",
            color: COLORS.textMuted, fontSize: 13,
          }}>
            {loading
              ? "Loading..."
              : connected
                ? "Waiting for logs..."
                : "No log entries"}
          </div>
        ) : (
          filtered.map((log, i) => (
            <div key={log.id || i} style={{
              display: "flex", gap: 0, padding: "5px 18px",
              borderBottom: `1px solid ${COLORS.border}15`,
              background: i % 2 === 0 ? "transparent" : `${COLORS.bg}50`,
              // Анимация только для самых новых логов
              animation: i < 3 && !paused ? "fade-in 0.2s ease" : "none",
              alignItems: "flex-start",
            }}>
              {/* Время */}
              <span style={{
                fontFamily: "'Space Mono', monospace", fontSize: 10,
                color: COLORS.textMuted, flexShrink: 0, width: 76, paddingTop: 1,
              }}>
                {new Date(log.timestamp).toLocaleTimeString("en", { hour12: false })}
              </span>

              {/* Уровень */}
              <span style={{
                fontFamily: "'Space Mono', monospace", fontSize: 10, fontWeight: 700,
                color: LOG_COLORS[log.level] || COLORS.textMuted,
                textTransform: "uppercase", flexShrink: 0, width: 60, paddingTop: 1,
              }}>
                {log.level}
              </span>

              {/* Контейнер */}
              <span style={{
                fontFamily: "'Space Mono', monospace", fontSize: 10,
                color: COLORS.accent, flexShrink: 0, width: 110, paddingTop: 1,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>
                {log.container_name || log.service_name || "—"}
              </span>

              {/* Сообщение */}
              <span style={{
                fontFamily: "'Space Mono', monospace", fontSize: 11, flex: 1,
                color: ["error", "critical"].includes(log.level)
                  ? COLORS.textPrimary
                  : COLORS.textSecondary,
                lineHeight: 1.5, wordBreak: "break-word",
              }}>
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </Card>
    </div>
  );
}