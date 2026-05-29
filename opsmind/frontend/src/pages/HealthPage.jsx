// src/pages/HealthPage.jsx

import useHealth
from "../hooks/useHealth";

export default function HealthPage() {

  const health =
    useHealth();

  return (

    <div
      style={{
        padding:
          "32px 36px",
      }}
    >

      <h1>
        Health
      </h1>

      <pre>
        {JSON.stringify(
          health,
          null,
          2
        )}
      </pre>

    </div>

  );
}