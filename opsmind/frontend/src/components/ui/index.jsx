import { useState } from "react";
import { COLORS } from "../../utils/constants";

// ─── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, style, glow, onClick, hoverable, padding }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => hoverable && setHovered(true)}
      onMouseLeave={() => hoverable && setHovered(false)}
      style={{
        background: COLORS.surface,
        border: `1px solid ${hovered ? COLORS.borderLight : COLORS.border}`,
        borderRadius: 12,
        transition: "all 0.18s ease",
        cursor: onClick ? "pointer" : "default",
        boxShadow: glow ? `0 0 28px ${glow}` : hovered && hoverable ? "0 4px 24px rgba(0,0,0,0.35)" : "none",
        transform: hoverable && hovered ? "translateY(-1px)" : "none",
        padding: padding ?? undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// ─── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ color, glow, children, small }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      padding: small ? "2px 8px" : "3px 10px",
      borderRadius: 4,
      background: glow || "transparent",
      border: `1px solid ${color}40`,
      color,
      fontSize: small ? 10 : 11,
      fontFamily: "'Space Mono', monospace",
      fontWeight: 700,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      whiteSpace: "nowrap",
    }}>
      {children}
    </span>
  );
}

// ─── LiveDot ───────────────────────────────────────────────────────────────────
export function LiveDot({ color = COLORS.green, size = 7 }) {
  return (
    <span style={{
      display: "inline-block", width: size, height: size,
      borderRadius: "50%", background: color, flexShrink: 0,
      animation: "pulse-dot 2s ease-in-out infinite",
      boxShadow: `0 0 6px ${color}`,
    }} />
  );
}

// ─── Button ────────────────────────────────────────────────────────────────────
export function Button({ children, onClick, primary, danger, disabled, small, style, type = "button" }) {
  const [hovered, setHovered] = useState(false);
  const bg = danger ? COLORS.red : primary ? COLORS.accent : "transparent";
  const color = primary || danger ? "#fff" : COLORS.textSecondary;
  const border = primary || danger ? "none" : `1px solid ${COLORS.border}`;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 6,
        padding: small ? "6px 14px" : "10px 20px",
        borderRadius: 8, border, cursor: disabled ? "not-allowed" : "pointer",
        fontFamily: "'Space Mono', monospace",
        fontSize: small ? 11 : 12, fontWeight: 700, letterSpacing: "0.05em",
        transition: "all 0.15s",
        background: disabled ? `${bg}80` : hovered && primary ? COLORS.accentDim : bg,
        color: disabled ? `${color}80` : color,
        boxShadow: primary && !disabled ? `0 0 18px ${COLORS.accent}30` : "none",
        ...style,
      }}
    >
      {children}
    </button>
  );
}

// ─── Input ─────────────────────────────────────────────────────────────────────
export function Input({ label, error, style, ...props }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {label && (
        <label style={{
          fontSize: 11, color: COLORS.textMuted,
          fontFamily: "'Space Mono', monospace",
          textTransform: "uppercase", letterSpacing: "0.08em",
        }}>{label}</label>
      )}
      <input
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          padding: "10px 13px", borderRadius: 8,
          background: COLORS.bg,
          border: `1px solid ${error ? COLORS.red : focused ? COLORS.accent : COLORS.border}`,
          color: COLORS.textPrimary, fontSize: 14,
          fontFamily: "'DM Sans', sans-serif",
          outline: "none", transition: "border-color 0.15s",
          width: "100%",
          ...style,
        }}
        {...props}
      />
      {error && (
        <span style={{ fontSize: 12, color: COLORS.red }}>{error}</span>
      )}
    </div>
  );
}

// ─── Select ────────────────────────────────────────────────────────────────────
export function Select({ label, children, style, ...props }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {label && (
        <label style={{
          fontSize: 11, color: COLORS.textMuted,
          fontFamily: "'Space Mono', monospace",
          textTransform: "uppercase", letterSpacing: "0.08em",
        }}>{label}</label>
      )}
      <select style={{
        padding: "10px 13px", borderRadius: 8,
        background: COLORS.bg, border: `1px solid ${COLORS.border}`,
        color: COLORS.textPrimary, fontSize: 14,
        fontFamily: "'DM Sans', sans-serif",
        outline: "none", cursor: "pointer", width: "100%",
        ...style,
      }} {...props}>
        {children}
      </select>
    </div>
  );
}

// ─── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = 20, color = COLORS.accent }) {
  return (
    <div style={{
      width: size, height: size, border: `2px solid ${color}30`,
      borderTopColor: color, borderRadius: "50%",
      animation: "spin 0.7s linear infinite", flexShrink: 0,
    }} />
  );
}

// ─── Empty State ───────────────────────────────────────────────────────────────
export function Empty({ icon, title, description, action }) {
  return (
    <div style={{ textAlign: "center", padding: "60px 32px" }}>
      <div style={{ fontSize: 40, marginBottom: 16, opacity: 0.3 }}>{icon || "◈"}</div>
      <div style={{ fontSize: 15, color: COLORS.textSecondary, marginBottom: 8, fontWeight: 500 }}>{title}</div>
      {description && (
        <div style={{ fontSize: 13, color: COLORS.textMuted, marginBottom: 20 }}>{description}</div>
      )}
      {action}
    </div>
  );
}

// ─── Modal ─────────────────────────────────────────────────────────────────────
export function Modal({ children, onClose, width = 640 }) {
  return (
    <div
      onClick={(e) => e.target === e.currentTarget && onClose?.()}
      style={{
        position: "fixed", inset: 0, zIndex: 200,
        background: "rgba(8,11,20,0.92)",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 20, backdropFilter: "blur(8px)",
        animation: "fade-in 0.2s ease",
      }}
    >
      <div style={{ width: `min(${width}px, 100%)`, animation: "slide-in 0.25s ease", maxHeight: "90vh", overflow: "auto" }}>
        {children}
      </div>
    </div>
  );
}

// ─── Alert ─────────────────────────────────────────────────────────────────────
export function Alert({ type = "error", children }) {
  const color = type === "error" ? COLORS.red : type === "success" ? COLORS.green : COLORS.yellow;
  return (
    <div style={{
      padding: "10px 14px", borderRadius: 8,
      background: `${color}12`, border: `1px solid ${color}30`,
      color, fontSize: 13, lineHeight: 1.5,
    }}>
      {children}
    </div>
  );
}

// ─── Section Header ────────────────────────────────────────────────────────────
export function SectionTitle({ children, right }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
      <h2 style={{
        fontSize: 11, fontWeight: 700, color: COLORS.textMuted,
        fontFamily: "'Space Mono', monospace",
        letterSpacing: "0.1em", textTransform: "uppercase",
      }}>
        {children}
      </h2>
      {right}
    </div>
  );
}