import { Card } from "../../components/ui/Card";
import { useTheme } from "../../components/ThemeProvider";

export const AdminPage = () => {
  const theme = useTheme();

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <h2 style={{ margin: 0 }}>Admin</h2>
      <Card title="Audit log">
        <p style={{ margin: 0, color: theme.colors.muted }}>
          Administrative tools and audit insights will appear here. Only users with the admin role can
          view this section.
        </p>
      </Card>
    </div>
  );
};
