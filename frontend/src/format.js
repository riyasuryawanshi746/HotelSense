// format.js - small helpers to display numbers consistently.

// Occupancy is a percentage; ADR and RevPAR are money (Qatari riyal).
export function fmtValue(value, metric, digits = 1) {
  if (value === null || value === undefined) return "–";
  if (metric === "occupancy") return `${value.toFixed(digits)}%`;
  return `QAR ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

// A plain number with a fixed number of decimals.
export function fmtNum(value, digits = 1) {
  if (value === null || value === undefined) return "–";
  return value.toFixed(digits);
}

// A signed percentage such as "+4.2%" or "-1.0%".
export function fmtSigned(value, digits = 1, unit = "%") {
  if (value === null || value === undefined) return "–";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}${unit}`;
}

// A p-value: very small ones are shown as "< 0.001".
export function fmtP(p) {
  if (p === null || p === undefined) return "–";
  return p < 0.001 ? "< 0.001" : p.toFixed(3);
}

// One fixed colour per model, so a model looks the same on every chart.
export const MODEL_COLORS = {
  "Seasonal Naive": "#94a3b8",
  "Holt-Winters": "#f59e0b",
  SARIMA: "#8b5cf6",
  Combination: "#0d9488",
};

// Month numbers 1..12 to short names for the seasonal profile chart.
export const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Scope labels for backtest metrics, used everywhere so they stay consistent.
// A horizon-h result pools forecast steps 1..h (e.g. the 6-month horizon = months 1-6 ahead).
export const ALL_HORIZONS = "All horizons";
export function horizonLabel(h) {
  return `${h}-month horizon`;
}
export function horizonDetail(h) {
  return `${h}-month horizon (months 1–${h} ahead)`;
}

// Axis unit for chart titles.
export function unitOf(metric) {
  return metric === "occupancy" ? "%" : "QAR";
}
