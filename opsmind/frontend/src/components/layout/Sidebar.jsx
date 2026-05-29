// src/components/layout/Sidebar.jsx

import LiveDot from "../common/LiveDot";

import { COLORS }
from "../../styles/colors";

export default function Sidebar({
  active,
  setActive,
}) {

  const items = [
    {
      id: "dashboard",
      icon: "⬡",
      label: "Dashboard",
    },

    {
      id: "incidents",
      icon: "⚠",
      label: "Incidents",
    },

    {
      id: "logs",
      icon: "≡",
      label: "Live Logs",
    },

    {
      id: "projects",
      icon: "◈",
      label: "Projects",
    },

    {
      id: "health",
      icon: "♥",
      label: "Health",
    },

    {
      id: "settings",
      icon: "⊙",
      label: "Settings",
    },
  ];

  return (
    <div
      style={{
        width: 220,

        flexShrink: 0,

        background:
          COLORS.surface,

        borderRight:
          `1px solid ${COLORS.border}`,

        display: "flex",

        flexDirection:
          "column",

        minHeight:
          "100vh",

        padding:
          "0 0 20px",
      }}
    >

      <div
        style={{
          padding:
            "24px 20px 20px",

          borderBottom:
            `1px solid ${COLORS.border}`,
        }}
      >

        <div
          style={{
            display: "flex",

            alignItems:
              "center",

            gap: 9,
          }}
        >

          <div
            style={{
              width: 30,

              height: 30,

              borderRadius: 8,

              background:
                COLORS.accent,

              display: "flex",

              alignItems:
                "center",

              justifyContent:
                "center",

              fontSize: 15,

              boxShadow:
                `0 0 14px ${COLORS.accent}50`,
            }}
          >
            ⚡
          </div>

          <span
            style={{
              fontFamily:
                "'Space Mono', monospace",

              fontSize: 16,

              fontWeight: 700,

              color:
                COLORS.textPrimary,
            }}
          >
            OpsMind
          </span>

        </div>

        <div
          style={{
            display: "flex",

            alignItems:
              "center",

            gap: 6,

            marginTop: 10,
          }}
        >

          <LiveDot />

          <span
            style={{
              fontSize: 11,

              color:
                COLORS.textMuted,

              fontFamily:
                "'Space Mono', monospace",
            }}
          >
            monitoring 24/7
          </span>

        </div>

      </div>

      <nav
        style={{
          flex: 1,

          padding:
            "16px 12px",

          display: "flex",

          flexDirection:
            "column",

          gap: 2,
        }}
      >

        {items.map(
          (item) => (

            <button
              key={item.id}

              onClick={() =>
                setActive(
                  item.id
                )
              }

              style={{
                display:
                  "flex",

                alignItems:
                  "center",

                gap: 10,

                padding:
                  "9px 10px",

                borderRadius:
                  8,

                border:
                  "none",

                cursor:
                  "pointer",

                textAlign:
                  "left",

                background:
                  active === item.id
                    ? `${COLORS.accent}15`
                    : "transparent",

                color:
                  active === item.id
                    ? COLORS.accent
                    : COLORS.textSecondary,

                fontSize: 13,

                transition:
                  "all .15s",
              }}
            >

              <span>
                {item.icon}
              </span>

              {item.label}

            </button>

          )
        )}

      </nav>

      <div
        style={{
          padding:
            "0 12px",
        }}
      >

        <div
          style={{
            padding:
              "12px 10px",

            borderRadius:
              8,

            background:
              COLORS.bg,

            border:
              `1px solid ${COLORS.border}`,
          }}
        >

          <div
            style={{
              fontSize: 11,

              color:
                COLORS.textMuted,

              marginBottom: 4,
            }}
          >
            API Status
          </div>

          <div
            style={{
              display: "flex",

              alignItems:
                "center",

              gap: 6,
            }}
          >

            <LiveDot
              color={
                COLORS.green
              }
            />

            <span
              style={{
                color:
                  COLORS.green,

                fontSize: 12,
              }}
            >
              Online
            </span>

          </div>

        </div>

      </div>

    </div>
  );
}