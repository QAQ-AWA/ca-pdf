import { PropsWithChildren } from "react";

import { useTheme } from "../ThemeProvider";

type CardProps = PropsWithChildren<{
  title?: string;
  action?: React.ReactNode;
  style?: React.CSSProperties;
}>;

export const Card = ({ title, action, children, style }: CardProps) => {
  const theme = useTheme();

  return (
    <section
      style={{
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius,
        boxShadow: theme.shadow,
        padding: theme.spacing.xl,
        display: "grid",
        gap: theme.spacing.md,
        ...style,
      }}
    >
      {(title || action) && (
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: theme.spacing.sm,
          }}
        >
          {title ? (
            <h2 style={{ margin: 0, fontSize: theme.font.size.lg }}>{title}</h2>
          ) : (
            <span />
          )}
          {action ?? null}
        </header>
      )}
<div style={{ display: "grid", gap: theme.spacing.md }}>{children}</div>
    </section>
  );
};
