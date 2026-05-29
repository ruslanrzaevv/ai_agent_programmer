// src/components/common/LiveDot.jsx

import { COLORS }
from "../../styles/colors";

export default function LiveDot({
  color = COLORS.green,
}) {

  return (
    <span
      style={{
        display:
          "inline-block",

        width: 7,

        height: 7,

        borderRadius:
          "50%",

        background:
          color,

        animation:
          "pulse-dot 2s ease-in-out infinite",

        boxShadow:
          `0 0 6px ${color}`,
      }}
    />
  );
}