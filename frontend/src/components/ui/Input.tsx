import { forwardRef } from "react";

import { useTheme } from "../ThemeProvider";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  helperText?: string;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(({ label, helperText, style, ...props }, ref) => {
  const theme = useTheme();

  const inputField = (
    <input
      ref={ref}
      style={{
        width: "100%",
        padding: `${theme.spacing.sm} ${theme.spacing.md}`,
        borderRadius: theme.borderRadius,
        border: `1px solid ${theme.colors.muted}`,
        fontSize: theme.font.size.base,
        backgroundColor: "#fff",
        color: theme.colors.text,
      }}
      {...props}
    />
  );

  if (!label) {
    return inputField;
  }

  return (
    <label style={{ display: "grid", gap: theme.spacing.xs, width: "100%", ...style }}>
      <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>{label}</span>
      {inputField}
      {helperText ? (
        <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>{helperText}</span>
      ) : null}
    </label>
  );
});

Input.displayName = "Input";
