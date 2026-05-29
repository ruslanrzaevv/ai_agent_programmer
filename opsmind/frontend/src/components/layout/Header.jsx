// src/components/layout/Header.jsx

import NotificationBell
from "./NotificationBell";

import { COLORS }
from "../../styles/colors";

export default function Header({
  title,
  user,
}) {

  return (
    <div
      style={{
        height: 70,

        borderBottom:
          `1px solid ${COLORS.border}`,

        display: "flex",

        alignItems:
          "center",

        justifyContent:
          "space-between",

        padding:
          "0 24px",

        background:
          COLORS.surface,
      }}
    >

      <div>

        <h2
          style={{
            color:
              COLORS.textPrimary,
          }}
        >
          {title}
        </h2>

      </div>

      <div
        style={{
          display: "flex",

          alignItems:
            "center",

          gap: 20,
        }}
      >

        <NotificationBell
          count={0}
        />

        <div>

          <div
            style={{
              fontSize: 13,
            }}
          >
            {user?.email}
          </div>

        </div>

      </div>

    </div>
  );
}