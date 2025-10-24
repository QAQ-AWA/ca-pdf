import { useTheme } from "../ThemeProvider";

type SpinnerProps = {
  size?: number;
};

export const Spinner = ({ size = 32 }: SpinnerProps) => {
  const theme = useTheme();

  const borderSize = Math.max(2, Math.round(size * 0.12));

  return (
    <span
      role="status"
      aria-live="polite"
      style={{
        width: size,
        height: size,
        display: "inline-block",
        borderRadius: "50%",
        border: `${borderSize}px solid ${theme.colors.muted}`,
        borderTopColor: theme.colors.primary,
        animation: "spin 0.85s linear infinite",
      }}
    />
  );
};
