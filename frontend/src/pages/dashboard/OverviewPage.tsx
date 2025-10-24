import { Card } from "../../components/ui/Card";
import { useTheme } from "../../components/ThemeProvider";

export const OverviewPage = () => {
  const theme = useTheme();

  const stats = [
    { label: "Active projects", value: "12" },
    { label: "Pending reviews", value: "3" },
    { label: "Team members", value: "28" },
  ];

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <h2 style={{ margin: 0 }}>Overview</h2>
      <div
        style={{
          display: "grid",
          gap: theme.spacing.lg,
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        }}
      >
        {stats.map((stat) => (
          <Card key={stat.label}>
            <span style={{ color: theme.colors.muted, fontSize: theme.font.size.sm }}>{stat.label}</span>
            <strong style={{ fontSize: "2.5rem", lineHeight: 1 }}>{stat.value}</strong>
          </Card>
        ))}
      </div>
    </div>
  );
};
