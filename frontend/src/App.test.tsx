import { render, screen } from "@testing-library/react";

import App from "./App";
import { ThemeProvider } from "./components/ThemeProvider";
import { AuthProvider, AUTH_STORAGE_KEY } from "./contexts/AuthContext";

const renderApp = (initialPath = "/") => {
  window.history.pushState({}, "Test", initialPath);

  return render(
    <ThemeProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  );
};

describe("App routing", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("redirects unauthenticated users to the login page", async () => {
    renderApp("/");

    expect(await screen.findByText(/sign in to your account/i)).toBeInTheDocument();
  });

  it("allows authenticated users to view the overview dashboard", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        tokens: {
          accessToken: "token",
          refreshToken: "refresh",
          expiresAt: Date.now() + 60_000,
        },
        user: {
          id: "1",
          email: "user@example.com",
          roles: ["member"],
        },
      })
    );

    renderApp("/");

    expect(await screen.findByRole("heading", { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByText(/active projects/i)).toBeInTheDocument();
  });

  it("prevents navigation to admin route without required role", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        tokens: {
          accessToken: "token",
          refreshToken: "refresh",
          expiresAt: Date.now() + 60_000,
        },
        user: {
          id: "1",
          email: "user@example.com",
          roles: ["member"],
        },
      })
    );

    renderApp("/admin");

    expect(await screen.findByText(/access restricted/i)).toBeInTheDocument();
  });

  it("grants access to admin route when user has the admin role", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        tokens: {
          accessToken: "token",
          refreshToken: "refresh",
          expiresAt: Date.now() + 60_000,
        },
        user: {
          id: "1",
          email: "admin@example.com",
          roles: ["admin"],
        },
      })
    );

    renderApp("/admin");

    expect(await screen.findByRole("heading", { name: "Admin" })).toBeInTheDocument();
  });
});
