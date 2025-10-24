import { Link } from "react-router-dom";

import { Card } from "../components/ui/Card";
import { useTheme } from "../components/ThemeProvider";

export const UnauthorizedPage = () => {
  const theme = useTheme();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: theme.colors.background,
        padding: theme.spacing.xl,
      }}
    >
      <Card title="Access restricted" style={{ maxWidth: "520px" }}>
        <p style={{ margin: 0, color: theme.colors.muted }}>
          You do not have permission to view this area. Please contact an administrator if you
          believe this is a mistake.
        </p>
        <Link to="/" style={{ color: theme.colors.primary }}>
          Go back to dashboard
        </Link>
      </Card>
    </div>
  );
};
