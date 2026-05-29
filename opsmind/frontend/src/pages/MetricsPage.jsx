// src/pages/MetricsPage.jsx

import useMetrics
from "../hooks/useMetrics";

export default function MetricsPage() {

  const metrics =
    useMetrics();

  return (

    <div
      style={{
        padding:
          "32px 36px",
      }}
    >

      <h1>
        Metrics
      </h1>

      <pre>
        {metrics}
      </pre>

    </div>

  );
}