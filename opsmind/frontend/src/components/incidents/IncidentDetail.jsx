// src/components/incidents/IncidentDetail.jsx

import {
    useState,
  } from "react";
  
  export default function IncidentDetail({
    incident,
    onClose,
  }) {
  
    const [mode,
      setMode] =
      useState(
        "senior"
      );
  
    const explanation =
      mode === "junior"
        ? incident.ai_explanation_junior
        : mode === "ceo"
        ? incident.ai_explanation_ceo
        : incident.ai_explanation_senior;
  
    return (
      <div
        style={{
          position:
            "fixed",
  
          inset: 0,
  
          background:
            "rgba(0,0,0,.8)",
  
          display:
            "flex",
  
          justifyContent:
            "center",
  
          alignItems:
            "center",
        }}
      >
        <div
          style={{
            width: 700,
  
            background:
              "#0D1220",
  
            padding: 30,
  
            borderRadius: 12,
          }}
        >
          <button
            onClick={
              onClose
            }
          >
            X
          </button>
  
          <h2>
            {
              incident.title
            }
          </h2>
  
          <p>
            Severity:
            {" "}
            {
              incident.severity
            }
          </p>
  
          <p>
            Status:
            {" "}
            {
              incident.status
            }
          </p>
  
          <hr />
  
          <button
            onClick={() =>
              setMode(
                "junior"
              )
            }
          >
            Junior
          </button>
  
          <button
            onClick={() =>
              setMode(
                "senior"
              )
            }
          >
            Senior
          </button>
  
          <button
            onClick={() =>
              setMode(
                "ceo"
              )
            }
          >
            CEO
          </button>
  
          <div
            style={{
              marginTop:
                20,
            }}
          >
            {
              explanation
            }
          </div>
  
          <div
            style={{
              marginTop:
                20,
            }}
          >
            <strong>
              AI Fix:
            </strong>
  
            <p>
              {
                incident.ai_fix_suggestion
              }
            </p>
          </div>
        </div>
      </div>
    );
  }