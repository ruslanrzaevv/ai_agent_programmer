import { useState } from "react";
import { COLORS, SEV_CONFIG, STATUS_CONFIG } from "../../utils/constants";
import { timeAgo, durationMinutes } from "../../utils/helpers";
import { Badge, Button, Card, Modal, Alert, Spinner } from "../ui";
import { useIncidentStore } from "../../store/incidentStore";

const MODES = [
  { key: "junior", label: "Junior Dev" },
  { key: "senior", label: "Senior Dev" },
  { key: "ceo",    label: "CEO View"   },
];

export default function IncidentDetail({ incident, onClose, onReplay }) {
  const [mode, setMode] = useState("senior");
  const [aiContent, setAiContent] = useState({
    junior: incident.ai_explanation_junior,
    senior: incident.ai_explanation_senior,
    ceo: incident.ai_explanation_ceo,
  });
  const [loadingMode, setLoadingMode] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [askLoading, setAskLoading] = useState(false);
  const [fixResult, setFixResult] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const {
    acknowledge,
    resolve,
    explain,
    ask,
    applyFix,
    generateCodeFix,
    fetchIncident,
  } = useIncidentStore();
  const sev = SEV_CONFIG[incident.severity] || SEV_CONFIG.low;
  const st = STATUS_CONFIG[incident.status] || STATUS_CONFIG.open;
  const duration = durationMinutes(incident.started_at, incident.resolved_at);

  const selected = useIncidentStore((s) => s.selected);

  console.log(
    "ROOT",
    selected?.orbit_root_cause
  );
  
  console.log(
    "GRAPH",
    selected?.orbit_dependency_graph
  );

  console.log("INCIDENT =", incident);
  console.log("SELECTED =", selected);

  async function handleExplain(m) {
    if (aiContent[m]) {
      setMode(m);
      return;
    }
    setMode(m);
    setLoadingMode(m);
    const res = await explain(incident.id, m);
    setAiContent((prev) => ({ ...prev, [m]: res.content }));
    setLoadingMode(null);
  }

  async function handleAsk() {
    if (!question.trim()) return;
    setAskLoading(true);
    const res = await ask(incident.id, question);
    setAnswer(res.content);
    setAskLoading(false);
  }

  async function handleFix(confirmed) {
    setActionLoading(true);
    const res = await applyFix(incident.id, confirmed);
    setFixResult(res);
    setActionLoading(false);
  }

  return (
    <Modal onClose={onClose} width={680}>
      <Card style={{ padding: 30 }} glow={sev.glow}>
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 22,
          }}
        >
          <div style={{ flex: 1, paddingRight: 16 }}>
            <div
              style={{
                display: "flex",
                gap: 7,
                flexWrap: "wrap",
                marginBottom: 10,
              }}
            >
              <Badge color={sev.color} glow={sev.glow}>
                {sev.label}
              </Badge>
              <Badge color={st.color}>{st.label}</Badge>
              <span style={{ fontSize: 12, color: COLORS.textMuted }}>
                {timeAgo(incident.started_at)}
              </span>
            </div>
            <h2
              style={{
                fontSize: 17,
                fontWeight: 500,
                color: COLORS.textPrimary,
                lineHeight: 1.45,
              }}
            >
              {incident.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: `1px solid ${COLORS.border}`,
              color: COLORS.textSecondary,
              width: 32,
              height: 32,
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 16,
              flexShrink: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            ✕
          </button>
        </div>

        {/* Stats */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3,1fr)",
            gap: 10,
            marginBottom: 22,
          }}
        >
          {[
            { label: "Errors", value: incident.error_count, color: COLORS.red },
            { label: "Duration", value: `${duration}m`, color: COLORS.accent },
            {
              label: "Containers",
              value: incident.affected_containers?.length || 0,
              color: COLORS.orange,
            },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                background: COLORS.bg,
                borderRadius: 9,
                padding: "13px 16px",
                border: `1px solid ${COLORS.border}`,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: COLORS.textMuted,
                  fontFamily: "'Space Mono', monospace",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  marginBottom: 4,
                }}
              >
                {s.label}
              </div>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 600,
                  color: s.color,
                  fontFamily: "'Space Mono', monospace",
                }}
              >
                {s.value}
              </div>
            </div>
          ))}
        </div>

        {/* AI explain */}
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontSize: 11,
              color: COLORS.textMuted,
              fontFamily: "'Space Mono', monospace",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: 10,
            }}
          >
            🤖 AI Explanation
          </div>
          <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
            {MODES.map((m) => (
              <button
                key={m.key}
                onClick={() => handleExplain(m.key)}
                style={{
                  padding: "6px 14px",
                  borderRadius: 7,
                  cursor: "pointer",
                  fontFamily: "'Space Mono', monospace",
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.05em",
                  transition: "all 0.15s",
                  background: mode === m.key ? COLORS.accent : "transparent",
                  color: mode === m.key ? "#fff" : COLORS.textSecondary,
                  border:
                    mode === m.key ? "none" : `1px solid ${COLORS.border}`,
                }}
              >
                {m.label}
              </button>
            ))}
          </div>
          <div
            style={{
              background: COLORS.bg,
              borderRadius: 10,
              padding: "14px 16px",
              border: `1px solid ${COLORS.borderLight}`,
              minHeight: 80,
              fontSize: 13.5,
              color: COLORS.textSecondary,
              lineHeight: 1.7,
              display: "flex",
              alignItems: loadingMode === mode ? "center" : "flex-start",
              justifyContent: loadingMode === mode ? "center" : "flex-start",
            }}
          >
            {loadingMode === mode ? (
              <Spinner />
            ) : (
              aiContent[mode] || "Click a mode above to generate explanation"
            )}
          </div>
        </div>

        <Card style={{ marginBottom: 20, padding: 16 }}>
          {/* Orbit Analysis */}
<div style={{ marginBottom: 20, background: COLORS.bg, borderRadius: 12, padding: 18, border: `1px solid ${COLORS.border}` }}>
  <div style={{ fontSize: 11, color: COLORS.accent, fontFamily: "'Space Mono', monospace", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 14 }}>
    🛰 Orbit Analysis
  </div>
  
  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 14 }}>
    {[
      { label: "Root Cause", value: incident?.orbit_root_cause || "Unknown", color: COLORS.red },
      { label: "Error Line", value: incident?.orbit_error_line ? `line ${incident.orbit_error_line}` : "—", color: COLORS.orange },
      { label: "Risk Score", value: incident?.orbit_risk_score || 0, color: COLORS.yellow },
      { label: "Blast Radius", value: incident?.orbit_blast_radius || 0, color: COLORS.red },
      { label: "Definitions", value: incident?.orbit_definitions || 0, color: COLORS.accent },
      { label: "Imports", value: incident?.orbit_imports || 0, color: COLORS.accent },
      { label: "Calls", value: incident?.orbit_calls || 0, color: COLORS.green },
    ].map(s => (
      <div key={s.label} style={{ background: COLORS.surface, borderRadius: 8, padding: "10px 12px", border: `1px solid ${COLORS.border}` }}>
        <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
          {s.label}
        </div>
        <div style={{ fontSize: 15, fontWeight: 600, color: s.color, fontFamily: "'Space Mono', monospace" }}>
          {s.value}
        </div>
      </div>
    ))}
  </div>

  {incident?.orbit_affected_files?.length > 0 && (
    <div>
      <div style={{ fontSize: 10, color: COLORS.textMuted, fontFamily: "'Space Mono', monospace", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
        Affected Files
      </div>
      {incident.orbit_affected_files.map(f => (
        <div key={f} style={{ fontSize: 12, color: COLORS.accent, fontFamily: "monospace", padding: "3px 0" }}>📄 {f}</div>
      ))}
    </div>
  )}
</div>

{/* Repository Impact */}
<div style={{ marginBottom: 20, background: COLORS.bg, borderRadius: 12, padding: 18, border: `1px solid ${COLORS.border}` }}>
  <div style={{ fontSize: 11, color: COLORS.accent, fontFamily: "'Space Mono', monospace", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 14 }}>
    🔗 Repository Impact
  </div>

  {(() => {
    const graph = selected?.orbit_dependency_graph?.graph?.graph;
    if (!graph || typeof graph !== "string") return <div style={{ color: COLORS.textMuted, fontSize: 12 }}>No dependency data</div>;
    const lines = graph.split("\n").filter(l =>
      l.includes("|") && !l.includes("---") &&
      !l.includes("relationship_kind") && l.trim()
    );
    if (!lines.length) return <div style={{ color: COLORS.textMuted, fontSize: 12 }}>No dependencies found</div>;
    return lines.map((line, i) => {
      const parts = line.split("|").map(p => p.trim()).filter(Boolean);
      if (parts.length < 3) return null;
      const [kind, targetFile, targetName] = parts;
      const color = kind === "CALLS" ? COLORS.orange : kind === "IMPORTS" ? COLORS.accent : COLORS.green;
      return (
        <div key={i} style={{ display: "flex", gap: 8, alignItems: "center", padding: "5px 0", borderBottom: `1px solid ${COLORS.border}15` }}>
          <span style={{ background: `${color}20`, color, padding: "2px 8px", borderRadius: 4, fontFamily: "monospace", fontSize: 10, fontWeight: 700, flexShrink: 0, minWidth: 60, textAlign: "center" }}>
            {kind}
          </span>
          <span style={{ color: COLORS.textSecondary, fontFamily: "monospace", fontSize: 11, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {targetFile}
          </span>
          {targetName && <span style={{ color: COLORS.textMuted, fontFamily: "monospace", fontSize: 11, flexShrink: 0 }}>→ {targetName}</span>}
        </div>
      );
    });
  })()}
</div>
        </Card>
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontSize: 11,
              color: COLORS.textMuted,
              fontFamily: "'Space Mono', monospace",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: 10,
            }}
          >
            🔧 Suggested Fix
            <Button
              small
              primary
              onClick={async () => {
                const result = await generateCodeFix(selected.id);
                console.log(result);
                if (result.ok) {
                  const updated = await fetchIncident(selected.id);
                  console.log("UPDATED INCIDENT =", updated);
                  console.log("AI-FIX =", updated?.ai_fix_new_code);
                }
                console.log("FIX RESULT =", JSON.stringify(result, null, 2));
              }}
            >
              Generate AI Fix
            </Button>
          </div>
          <div
            style={{
              background: `${COLORS.green}10`,
              border: `1px solid ${COLORS.green}30`,
              borderRadius: 10,
              padding: "12px 16px",
              fontSize: 13,
              color: COLORS.green,
              lineHeight: 1.6,
              marginBottom: 10,
            }}
          >
            {selected?.ai_fix_suggestion}
          </div>
          {selected?.ai_fix_new_code && !selected?.ai_fix_applied && (
            <>
              <Card style={{ padding: 12 }}>
                <div>📄 {selected.ai_fix_file}</div>

                <pre>{selected.ai_fix_new_code}</pre>
              </Card>

              <Button small primary onClick={() => handleFix(true)}>
                Apply Fix
              </Button>
            </>
          )}
          {selected?.ai_fix_applied && (
            <Alert type="success">
              ✓ AI fix was applied at{" "}
              {new Date(selected?.ai_fix_applied_at).toLocaleString()}
            </Alert>
          )}
        </div>

        {/* Ask AI */}
        <div style={{ marginBottom: 22 }}>
          <div
            style={{
              fontSize: 11,
              color: COLORS.textMuted,
              fontFamily: "'Space Mono', monospace",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: 10,
            }}
          >
            💬 Ask AI
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder="Why did this happen? How to prevent it?"
              style={{
                flex: 1,
                padding: "9px 12px",
                borderRadius: 8,
                background: COLORS.bg,
                border: `1px solid ${COLORS.border}`,
                color: COLORS.textPrimary,
                fontSize: 13,
                outline: "none",
                fontFamily: "'DM Sans', sans-serif",
              }}
            />
            <Button
              small
              primary
              onClick={handleAsk}
              disabled={askLoading || !question.trim()}
            >
              {askLoading ? <Spinner size={14} /> : "Ask"}
            </Button>
          </div>
          {answer && (
            <div
              style={{
                marginTop: 10,
                background: COLORS.bg,
                borderRadius: 8,
                padding: "12px 14px",
                fontSize: 13,
                color: COLORS.textSecondary,
                lineHeight: 1.65,
                border: `1px solid ${COLORS.border}`,
                animation: "fade-in 0.3s ease",
              }}
            >
              {answer}
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button
            primary
            onClick={() => {
              onClose();
              onReplay(incident);
            }}
            style={{ flex: 1 }}
          >
            ⏮ Incident Replay
          </Button>
          {incident.status === "open" && (
            <Button
              onClick={() => acknowledge(incident.id)}
              style={{ flex: 1 }}
            >
              ✓ Acknowledge
            </Button>
          )}
          {["open", "acknowledged", "resolving"].includes(incident.status) && (
            <Button onClick={() => resolve(incident.id)} style={{ flex: 1 }}>
              ✅ Resolve
            </Button>
          )}
        </div>
      </Card>
    </Modal>
  );
}