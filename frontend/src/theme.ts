export const theme = {
  colors: {
    primary: "#2563eb",
    secondary: "#64748b",
    background: "#f8fafc",
    surface: "#ffffff",
    text: "#0f172a",
    muted: "#94a3b8",
    success: "#16a34a",
    warning: "#f59e0b",
    danger: "#dc2626",
  },
  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
  },
  font: {
    family:
      '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    size: {
      sm: "0.875rem",
      base: "1rem",
      lg: "1.125rem",
    },
    weight: {
      regular: 400,
      medium: 500,
      bold: 700,
    },
  },
  borderRadius: "0.75rem",
  shadow: "0 20px 45px rgba(15, 23, 42, 0.1)",
} as const;

export type Theme = typeof theme;
