export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export const COLORS = {
  bg: "#080B14",
  surface: "#0D1220",
  surfaceHover: "#121828",
  border: "#1C2538",
  borderLight: "#243047",
  accent: "#4F8EF7",
  accentGlow: "rgba(79,142,247,0.15)",
  accentDim: "#2A5DB8",
  green: "#22D3A0",
  greenGlow: "rgba(34,211,160,0.15)",
  orange: "#F97316",
  orangeGlow: "rgba(249,115,22,0.15)",
  red: "#F43F5E",
  redGlow: "rgba(244,63,94,0.15)",
  yellow: "#EAB308",
  textPrimary: "#E8EDF8",
  textSecondary: "#8A9BBE",
  textMuted: "#4A5A7A",
};

export const SEV_CONFIG = {
  critical: { color: COLORS.red,    glow: COLORS.redGlow,    label: "CRITICAL" },
  high:     { color: COLORS.orange, glow: COLORS.orangeGlow, label: "HIGH"     },
  medium:   { color: COLORS.yellow, glow: "rgba(234,179,8,0.15)", label: "MEDIUM" },
  low:      { color: COLORS.green,  glow: COLORS.greenGlow,  label: "LOW"      },
};

export const STATUS_CONFIG = {
  open:         { color: COLORS.red,    label: "Open"     },
  acknowledged: { color: COLORS.orange, label: "Ack'd"    },
  resolving:    { color: COLORS.accent, label: "Fixing"   },
  resolved:     { color: COLORS.green,  label: "Resolved" },
  ignored:      { color: COLORS.textMuted, label: "Ignored" },
};

export const LOG_COLORS = {
  critical: COLORS.red,
  error:    COLORS.orange,
  warning:  COLORS.yellow,
  info:     COLORS.textSecondary,
  debug:    COLORS.textMuted,
};