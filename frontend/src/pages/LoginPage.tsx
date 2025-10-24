import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate, type Location } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { useTheme } from "../components/ThemeProvider";

type LocationState = {
  from?: Location;
};

export const LoginPage = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticating, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    try {
      await login({ email, password });
      const redirectTarget = (location.state as LocationState | undefined)?.from?.pathname ?? "/";
      navigate(redirectTarget, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in. Please try again.");
    }
  };

  if (isAuthenticated) {
    const redirectTarget = (location.state as LocationState | undefined)?.from?.pathname ?? "/";
    return <Navigate to={redirectTarget} replace />;
  }

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
      <Card title="Sign in to your account" style={{ width: "min(420px, 100%)" }}>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.lg }}>
          <Input
            type="email"
            name="email"
            label="Email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <Input
            type="password"
            name="password"
            label="Password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {error ? (
            <p style={{ color: theme.colors.danger ?? "#dc2626", margin: 0, fontSize: theme.font.size.sm }}>{error}</p>
          ) : null}
          <Button type="submit" disabled={isAuthenticating}>
            {isAuthenticating ? (
              <>
                <Spinner size={18} /> Signing in...
              </>
            ) : (
              "Sign in"
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
};
