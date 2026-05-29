// src/pages/LogsPage.jsx

import {
  useState,
} from "react";

import useLogs
from "../hooks/useLogs";

import Loading
from "../components/common/Loading";

export default function LogsPage() {

  const [
    projectId,
    setProjectId,
  ] = useState("");

  const {
    logs,
    loading,
  } = useLogs(
    projectId
  );

  if (loading) {
    return <Loading />;
  }

  return (

    <div
      style={{
        padding:
          "32px 36px",
      }}
    >

      <h1>
        Logs
      </h1>

      {logs.map(
        log => (

          <div
            key={log.id}
          >
            {log.message}
          </div>

        )
      )}

    </div>

  );
}