// src/components/health/HealthCard.jsx

import Card from "../common/Card";
import LiveDot from "../common/LiveDot";

import { COLORS } from "../../styles/colors";

export default function HealthCard({
  health,
}) {

  if (!health)
    return null;

  return (

    <Card
      style={{
        padding: 24,
      }}
    >

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 16,
        }}
      >

        <LiveDot
          color={
            health.status === "ok"
              ? COLORS.green
              : COLORS.red
          }
        />

        <h3>
          System Health
        </h3>

      </div>

      <div>
        Status:
        {" "}
        {health.status}
      </div>

      <div>
        Redis:
        {" "}
        {health.redis}
      </div>

      <div>
        Monitoring:
        {" "}
        {JSON.stringify(
          health.monitoring
        )}
      </div>

      <div>
        WebSockets:
        {" "}
        {JSON.stringify(
          health.websockets
        )}
      </div>

    </Card>

  );
}