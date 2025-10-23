import { createContext, PropsWithChildren, useContext } from "react";

import { theme, type Theme } from "../theme";

const ThemeContext = createContext<Theme | null>(null);

export const ThemeProvider = ({ children }: PropsWithChildren) => (
  <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>
);

export const useTheme = (): Theme => {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }

  return context;
};
