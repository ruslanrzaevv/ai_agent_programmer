// src/components/projects/ProjectCard.jsx

import Card from "../common/Card";

export default function ProjectCard({
  project,
  onClick,
}) {

  return (
    <Card
      hoverable
      onClick={() =>
        onClick?.(project)
      }
      style={{
        padding: 20,
      }}
    >

      <h3>
        {project.name}
      </h3>

      <div
        style={{
          marginTop: 10,
        }}
      >
        Environment:
        {" "}
        {project.environment}
      </div>

      <div>
        Monitoring:
        {" "}
        {
          project.monitoring_enabled
            ? "🟢 Enabled"
            : "🔴 Disabled"
        }
      </div>

      <div>
        Threshold:
        {" "}
        {
          project.error_threshold_per_minute
        }
        /min
      </div>

    </Card>
  );
}