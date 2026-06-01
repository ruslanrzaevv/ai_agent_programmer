import { useEffect, useState } from "react";
import { COLORS } from "../utils/constants";
import { Badge, Button, Empty, SectionTitle } from "../components/ui";
import IncidentCard from "../components/incidents/IncidentCard";
import IncidentDetail from "../components/incidents/IncidentDetail";
import IncidentReplay from "../components/incidents/IncidentReplay";
import { useIncidentStore } from "../store/incidentStore";
import { useProjectStore } from "../store/projectStore";

const FILTERS = ["all", "critical", "high", "medium", "low", "open", "acknowledged", "resolved"];

export default function IncidentsPage() {
  const { activeProject } = useProjectStore();
  const { incidents, selected, filter, fetch, select, setFilter } = useIncidentStore();
  const [replay, setReplay] = useState(null);

  useEffect(() => {
    if (activeProject?.id) fetch(activeProject.id);
  }, [activeProject?.id, filter]);

  return (
    <div style={{ padding: "32px 36px", maxWidth: 900, animation: "fade-in 0.3s ease" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 600, color: COLORS.textPrimary,
          letterSpacing: "-0.02em", marginBottom: 4 }}>Incidents</h1>
        <div style={{ fontSize: 13, color: COLORS.textMuted }}>
          {incidents.length} incidents · {activeProject?.name || "no project selected"}
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 7, marginBottom: 20, flexWrap: "wrap" }}>
        {FILTERS.map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: "5px 13px", borderRadius: 7, border: "none", cursor: "pointer",
            fontFamily: "'Space Mono', monospace", fontSize: 10, fontWeight: 700,
            letterSpacing: "0.08em", textTransform: "uppercase", transition: "all 0.15s",
            background: filter === f ? COLORS.accent : COLORS.surface,
            color: filter === f ? "#fff" : COLORS.textSecondary,
            outline: filter === f ? "none" : `1px solid ${COLORS.border}`,
          }}>{f}</button>
        ))}
      </div>

      {/* List */}
      {!activeProject ? (
        <Empty icon="◈" title="No project selected"
          description="Select or create a project to see incidents" />
      ) : incidents.length === 0 ? (
        <Empty icon="✓" title="No incidents" description="All clear — no incidents match this filter" />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {incidents.map(inc => (
            <IncidentCard key={inc.id} incident={inc} onClick={select} />
          ))}
        </div>
      )}

      {/* Modals */}
      {selected && (
        <IncidentDetail
          incident={selected}
          onClose={() => useIncidentStore.getState().clearSelected()}
          onReplay={(inc) => { useIncidentStore.getState().clearSelected(); setReplay(inc); }}
        />
      )}
      {replay && <IncidentReplay incident={replay} onClose={() => setReplay(null)} />}
    </div>
  );
}