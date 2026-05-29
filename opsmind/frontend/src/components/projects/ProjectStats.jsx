// src/components/projects/ProjectStats.jsx

import MetricCard from "../common/MetricCard";

import { COLORS }
from "../../styles/colors";

export default function ProjectStats({
  incidentsCount,
  activeCount,
}) {

  return (

    <div
      style={{
        display: "flex",
        gap: 14,
        marginBottom: 24,
      }}
    >

      <MetricCard
        label="Projects"
        value={
          activeCount
        }
        color={
          COLORS.green
        }
        icon="◈"
      />

      <MetricCard
        label="Incidents"
        value={
          incidentsCount
        }
        color={
          COLORS.red
        }
        icon="⚠"
      />

    </div>

  );
}