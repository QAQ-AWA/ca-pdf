import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { useTheme } from "../ThemeProvider";

const navigationLinks = [
  { to: "/", label: "Overview" },
  { to: "/settings", label: "Settings" },
  { to: "/admin", label: "Admin", roles: ["admin"] as string[] },
];

export const DashboardShell = () => {
  const { user, logout, hasRole } = useAuth();
  const theme = useTheme();

  const links = navigationLinks.filter((link) => !link.roles || hasRole(...link.roles));

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "260px 1fr",
        background: theme.colors.background,
      }}
    >
      <aside
        style={{
          background: theme.colors.surface,
          borderRight: `1px solid ${theme.colors.muted}`,
          display: "grid",
          gridTemplateRows: "auto 1fr auto",
          padding: theme.spacing.xl,
          gap: theme.spacing.xl,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: theme.font.size.lg }}>Control Center</h1>
          <p style={{ margin: 0, color: theme.colors.muted, fontSize: theme.font.size.sm }}>
            Manage your workspace
          </p>
        </div>
        <nav style={{ display: "grid", gap: theme.spacing.sm }}>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              style={({ isActive }) => ({
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                borderRadius: theme.borderRadius,
                background: isActive ? theme.colors.primary : "transparent",
                color: isActive ? "#fff" : theme.colors.text,
                fontWeight: isActive ? theme.font.weight.medium : theme.font.weight.regular,
                transition: "background 0.2s ease",
              })}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <Card style={{ padding: theme.spacing.lg }}>
          <div style={{ display: "grid", gap: theme.spacing.xs }}>
            <span style={{ fontSize: theme.font.size.sm, color: theme.colors.muted }}>Signed in as</span>
            <strong>{user?.fullName ?? user?.email}</strong>
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
              Roles: {user?.roles.join(", ") || "none"}
            </span>
          </div>
          <Button variant="secondary" onClick={() => logout().catch(() => undefined)}>
            Sign out
          </Button>
        </Card>
      </aside>
      <main
        style={{
          padding: `${theme.spacing.xl} ${theme.spacing.xxl}`,
          display: "grid",
          gap: theme.spacing.xl,
          alignContent: "start",
        }}
      >
        <Outlet />
      </main>
    </div>
  );
};
