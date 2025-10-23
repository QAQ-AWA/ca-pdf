import { render, screen } from "@testing-library/react";

import App from "./App";
import { ThemeProvider } from "./components/ThemeProvider";

const renderWithProviders = () =>
  render(
    <ThemeProvider>
      <App />
    </ThemeProvider>
  );

describe("App", () => {
  it("renders the application title", () => {
    renderWithProviders();

    expect(screen.getByRole("heading", { name: /monorepo ui/i })).toBeInTheDocument();
  });
});
