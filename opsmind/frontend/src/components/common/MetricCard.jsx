// src/components/common/MetricCard.jsx

import Card from "./Card";

import {
  COLORS,
} from "../../styles/colors";

export default function MetricCard({
  label,
  value,
  unit,
  color,
  delta,
  icon,
}) {

  return (
    <Card
      style={{
        padding:
          "20px 24px",

        flex: 1,

        minWidth: 0,
      }}
    >

      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          alignItems:
            "flex-start",
        }}
      >

        <div>

          <div
            style={{
              fontSize: 11,

              color:
                COLORS.textMuted,

              fontFamily:
                "'Space Mono', monospace",

              textTransform:
                "uppercase",

              letterSpacing:
                ".1em",

              marginBottom: 8,
            }}
          >
            {label}
          </div>

          <div
            style={{
              display:
                "flex",

              alignItems:
                "baseline",

              gap: 4,
            }}
          >

            <span
              style={{
                fontSize: 32,

                fontWeight: 600,

                color:
                  color ||
                  COLORS.textPrimary,

                letterSpacing:
                  "-0.02em",

                lineHeight: 1,
              }}
            >
              {value}
            </span>

            {unit && (
              <span
                style={{
                  fontSize: 14,

                  color:
                    COLORS.textMuted,
                }}
              >
                {unit}
              </span>
            )}

          </div>

          {delta && (
            <div
              style={{
                fontSize: 12,

                color:
                  delta > 0
                    ? COLORS.red
                    : COLORS.green,

                marginTop: 6,
              }}
            >
              {delta > 0
                ? "▲"
                : "▼"}

              {" "}

              {Math.abs(delta)}%

            </div>
          )}

        </div>

        <div
          style={{
            fontSize: 24,
            opacity: .7,
          }}
        >
          {icon}
        </div>

      </div>

    </Card>
  );
}