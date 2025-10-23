import { clientEnv } from "./lib/env";
import { useTheme } from "./components/ThemeProvider";
import type { Theme } from "./theme";

const cardStyles = (token: Theme) => ({
  backgroundColor: token.colors.surface,
  color: token.colors.text,
  padding: token.spacing.xl,
  borderRadius: token.borderRadius,
  boxShadow: token.shadow,
  maxWidth: "720px",
  margin: "0 auto",
  display: "flex",
  flexDirection: "column" as const,
  gap: token.spacing.lg,
});

const badgeStyles = (token: Theme) => ({
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: `${token.spacing.xs} ${token.spacing.sm}`,
  borderRadius: "9999px",
  backgroundColor: token.colors.primary,
  color: "#fff",
  fontSize: token.font.size.sm,
  fontWeight: token.font.weight.medium,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
});

const linkStyles = (token: Theme) => ({
  color: token.colors.primary,
  fontWeight: token.font.weight.medium,
});

function App() {
  const theme = useTheme();

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: theme.spacing.xl,
        background: theme.colors.background,
      }}
    >
      <section style={cardStyles(theme)}>
        <span style={badgeStyles(theme)}>Monorepo Ready</span>
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "clamp(2rem, 3vw, 3rem)",
              fontFamily: theme.font.family,
              fontWeight: theme.font.weight.bold,
            }}
          >
            {clientEnv.appName}
          </h1>
          <p
            style={{
              marginTop: theme.spacing.sm,
              fontSize: theme.font.size.base,
              color: theme.colors.muted,
              maxWidth: "48ch",
            }}
          >
            Frontend tooling (Vite, React, TypeScript) and FastAPI backend scaffolding are set up
            and ready for collaborative development inside a single monorepo.
          </p>
        </div>

        <div>
          <h2
            style={{
              marginBottom: theme.spacing.sm,
              fontSize: theme.font.size.lg,
              fontWeight: theme.font.weight.medium,
            }}
          >
            Environment summary
          </h2>
          <ul
            style={{
              listStyle: "none",
              display: "grid",
              gap: theme.spacing.sm,
              margin: 0,
              padding: 0,
              fontSize: theme.font.size.base,
            }}
          >
            <li>
              <strong>API base URL:</strong> {clientEnv.apiBaseUrl}
            </li>
            <li>
              <strong>Mode:</strong> {clientEnv.mode}
            </li>
            <li>
              <strong>Development:</strong> {clientEnv.isDev ? "Enabled" : "Disabled"}
            </li>
            <li>
              <strong>Production build:</strong> {clientEnv.isProd ? "Yes" : "No"}
            </li>
          </ul>
        </div>

        <footer
          style={{
            display: "flex",
            flexWrap: "wrap" as const,
            gap: theme.spacing.md,
            alignItems: "center",
            fontSize: theme.font.size.sm,
          }}
        >
          <span>Start the development servers:</span>
          <code
            style={{
              backgroundColor: theme.colors.background,
              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
              borderRadius: theme.spacing.sm,
            }}
          >
            make dev-backend &amp;&amp; make dev-frontend
          </code>
          <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noreferrer" style={linkStyles(theme)}>
            FastAPI Docs
          </a>
          <a href="https://vitejs.dev" target="_blank" rel="noreferrer" style={linkStyles(theme)}>
            Vite Docs
          </a>
        </footer>
      </section>
    </main>
  );
}

export default App;
