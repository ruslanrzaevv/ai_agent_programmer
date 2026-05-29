// src/components/health/MetricsCard.jsx

import Card from "../common/Card";

export default function MetricsCard({
  metrics,
}) {

  return (

    <Card
      style={{
        padding: 24,
      }}
    >

      <h3>
        Prometheus Metrics
      </h3>

      <pre
        style={{
          marginTop: 16,
          whiteSpace:
            "pre-wrap",
          overflow:
            "auto",
        }}
      >
        {metrics}
      </pre>

    </Card>

  );
}