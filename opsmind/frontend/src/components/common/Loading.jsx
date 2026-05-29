// src/components/common/Loading.jsx

import {
    COLORS,
  } from "../../styles/colors";
  
  export default function Loading() {
  
    return (
      <div
        style={{
          minHeight: "300px",
  
          display: "flex",
  
          alignItems: "center",
  
          justifyContent: "center",
  
          color:
            COLORS.textMuted,
  
          fontFamily:
            "'Space Mono', monospace",
        }}
      >
  
        Loading...
  
      </div>
    );
  }