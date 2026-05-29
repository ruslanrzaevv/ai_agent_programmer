// src/styles/constants.js

import { COLORS } from "./colors";

export const SEV_CONFIG = {

  critical: {
    color: COLORS.red,
    glow: COLORS.redGlow,
    label: "CRITICAL",
    dot: "🔴",
  },

  high: {
    color: COLORS.orange,
    glow: COLORS.orangeGlow,
    label: "HIGH",
    dot: "🟠",
  },

  medium: {
    color: COLORS.yellow,
    glow:
      "rgba(234,179,8,0.15)",
    label: "MEDIUM",
    dot: "🟡",
  },

  low: {
    color: COLORS.green,
    glow: COLORS.greenGlow,
    label: "LOW",
    dot: "🟢",
  },

};

export const STATUS_CONFIG = {

  open: {
    color: COLORS.red,
    label: "Open",
  },

  acknowledged: {
    color: COLORS.orange,
    label: "Ack'd",
  },

  resolving: {
    color: COLORS.accent,
    label: "Fixing",
  },

  resolved: {
    color: COLORS.green,
    label: "Resolved",
  },

};

export const LOG_COLORS = {

  critical:
    COLORS.red,

  error:
    COLORS.orange,

  warning:
    COLORS.yellow,

  info:
    COLORS.textSecondary,

  debug:
    COLORS.textMuted,

};