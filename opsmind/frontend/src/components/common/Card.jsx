// src/components/common/Card.jsx

import { useState } from "react";

import { COLORS } from "../../styles/colors";

export default function Card({
  children,
  style,
  glow,
  onClick,
  hoverable,
}) {

  const [hovered,
    setHovered] =
    useState(false);

  return (
    <div
      onClick={onClick}

      onMouseEnter={() =>
        hoverable &&
        setHovered(true)
      }

      onMouseLeave={() =>
        hoverable &&
        setHovered(false)
      }

      style={{
        background:
          COLORS.surface,

        border:
          `1px solid ${
            hovered
              ? COLORS.borderLight
              : COLORS.border
          }`,

        borderRadius: 12,

        transition:
          "all .2s ease",

        cursor:
          onClick
            ? "pointer"
            : "default",

        boxShadow:
          glow
            ? `0 0 30px ${glow}`
            : hovered
            ? "0 4px 24px rgba(0,0,0,.4)"
            : "none",

        transform:
          hoverable &&
          hovered
            ? "translateY(-1px)"
            : "none",

        ...style,
      }}
    >
      {children}
    </div>
  );
}