import { forwardRef } from "react";

import { useTheme } from "../ThemeProvider";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ children, variant = "primary", style, ...props }, ref) => {
  const theme = useTheme();

  const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
    primary: {
      backgroundColor: theme.colors.primary,
      color: "#fff",
      border: "none",
    },
    secondary: {
      backgroundColor: theme.colors.surface,
      color: theme.colors.text,
      border: `1px solid ${theme.colors.muted}`,
    },
    ghost: {
      backgroundColor: "transparent",
      color: theme.colors.primary,
      border: `1px solid transparent`,
    },
  };

  const baseStyles: React.CSSProperties = {
    padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
    borderRadius: theme.borderRadius,
    fontWeight: theme.font.weight.medium,
    cursor: "pointer",
    transition: "transform 0.15s ease, box-shadow 0.15s ease",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing.xs,
  };

  return (
    <button
      ref={ref}
      style={{
        ...baseStyles,
        ...variantStyles[variant],
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = "Button";
