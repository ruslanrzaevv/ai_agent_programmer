// src/pages/Dashboard.jsx

import useIncidents from "../hooks/useIncidents";

import MetricCard from "../components/common/MetricCard";
import IncidentCard from "../components/incidents/IncidentCard";
import Loading from "../components/common/Loading";

import { COLORS } from "../styles/colors";

export default function Dashboard({
  onIncidentClick,
}) {

  const {
    incidents,
    loading,
  } = useIncidents();

  if (loading) {
    return <Loading />;
  }

  const openIncidents =
    incidents.filter(
      i => i.status !== "resolved"
    );

  const criticalIncidents =
    incidents.filter(
      i => i.severity === "critical"
    );

  return (
    <div
      style={{
        padding: "32px 36px",
      }}
    >

      <h1>
        Dashboard
      </h1>

      <div
        style={{
          display: "flex",
          gap: 14,
          marginTop: 24,
          marginBottom: 24,
        }}
      >

        <MetricCard
          label="Open"
          value={
            openIncidents.length
          }
          color={COLORS.red}
          icon="⚠"
        />

        <MetricCard
          label="Critical"
          value={
            criticalIncidents.length
          }
          color={COLORS.orange}
          icon="🔥"
        />

      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >

        {incidents.map(
          incident => (
            <IncidentCard
              key={
                incident.id
              }
              incident={
                incident
              }
              onClick={
                onIncidentClick
              }
            />
          )
        )}

      </div>

    </div>
  );
}