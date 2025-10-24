import { Link } from "react-router-dom";

import { Card } from "../components/ui/Card";
import { useTheme } from "../components/ThemeProvider";

export const NotFoundPage = () => {
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
      <Card title="Page not found" style={{ maxWidth: "520px" }}>
        <p style={{ margin: 0, color: theme.colors.muted }}>
          The page you are looking for does not exist or has been moved. Use the button below to return
          to the dashboard.
        </p>
        <Link to="/" style={{ color: theme.colors.primary }}>
          Return to dashboard
        </Link>
      </Card>
    </div>
  );
};
