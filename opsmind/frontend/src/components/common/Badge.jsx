// src/components/common/Badge.jsx

export default function Badge({
  color,
  glow,
  children,
  small,
}) {

  return (
    <span
      style={{
        display:
          "inline-flex",

        alignItems:
          "center",

        gap: 4,

        padding:
          small
            ? "2px 8px"
            : "3px 10px",

        borderRadius: 4,

        background:
          glow ||
          "transparent",

        border:
          `1px solid ${color}40`,

        color,

        fontSize:
          small
            ? 10
            : 11,

        fontFamily:
          "'Space Mono', monospace",

        fontWeight:
          700,

        letterSpacing:
          ".08em",

        textTransform:
          "uppercase",
      }}
    >
      {children}
    </span>
  );
}