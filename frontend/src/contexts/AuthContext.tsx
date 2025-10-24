import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { httpClient, registerTokenProvider } from "../lib/httpClient";

export type User = {
  id: string;
  email: string;
  fullName?: string;
  roles: string[];
};

export type AuthTokens = {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
};

export type LoginCredentials = {
  email: string;
  password: string;
};

export const AUTH_STORAGE_KEY = "frontend.auth";

export type AuthContextValue = {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthenticating: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<string | null>;
  hasRole: (...roles: string[]) => boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const serializeAuthState = (tokens: AuthTokens | null, user: User | null) => {
  if (typeof window === "undefined") {
    return;
  }

  if (!tokens || !user) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }

  const payload = JSON.stringify({ tokens, user });
  window.localStorage.setItem(AUTH_STORAGE_KEY, payload);
};

const readStoredAuthState = (): { tokens: AuthTokens; user: User } | null => {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const stored = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) {
      return null;
    }

    const parsed = JSON.parse(stored) as { tokens: AuthTokens; user: User };
    if (!parsed?.tokens?.accessToken || !parsed?.tokens?.refreshToken) {
      return null;
    }

    return parsed;
  } catch (error) {
    console.warn("Failed to parse stored auth state", error);
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
};

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const tokensRef = useRef<AuthTokens | null>(null);
  const userRef = useRef<User | null>(null);

  const persistState = useCallback((nextTokens: AuthTokens | null, nextUser: User | null) => {
    tokensRef.current = nextTokens;
    userRef.current = nextUser;
    serializeAuthState(nextTokens, nextUser);
  }, []);

  const clearState = useCallback(async () => {
    setTokens(null);
    setUser(null);
    persistState(null, null);
  }, [persistState]);

  const logout = useCallback(async () => {
    const snapshot = tokensRef.current;
    await clearState();

    if (!snapshot?.refreshToken) {
      return;
    }

    try {
      await httpClient.post(
        "/auth/logout",
        { refreshToken: snapshot.refreshToken },
        { skipAuthRefresh: true }
      );
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn("Failed to notify backend about logout", error);
      }
    }
  }, [clearState]);

  const refreshTokens = useCallback(async (): Promise<string | null> => {
    const activeTokens = tokensRef.current;
    if (!activeTokens?.refreshToken) {
      await clearState();
      return null;
    }

    try {
      const response = await httpClient.post(
        "/auth/refresh",
        { refreshToken: activeTokens.refreshToken },
        { skipAuthRefresh: true }
      );

      const data = response.data as {
        accessToken: string;
        refreshToken?: string;
        expiresIn: number;
        user?: User;
      };

      const updatedTokens: AuthTokens = {
        accessToken: data.accessToken,
        refreshToken: data.refreshToken ?? activeTokens.refreshToken,
        expiresAt: Date.now() + data.expiresIn * 1000,
      };

      const nextUser = data.user ?? userRef.current;

      setTokens(updatedTokens);
      setUser(nextUser ?? null);
      persistState(updatedTokens, nextUser ?? null);

      return updatedTokens.accessToken;
    } catch (error) {
      await clearState();
      return null;
    }
  }, [clearState, persistState]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsAuthenticating(true);
      try {
        const response = await httpClient.post("/auth/login", credentials, { skipAuthRefresh: true });

        const data = response.data as {
          accessToken: string;
          refreshToken: string;
          expiresIn: number;
          user: User;
        };

        const nextTokens: AuthTokens = {
          accessToken: data.accessToken,
          refreshToken: data.refreshToken,
          expiresAt: Date.now() + data.expiresIn * 1000,
        };

        setTokens(nextTokens);
        setUser(data.user);
        persistState(nextTokens, data.user);
      } finally {
        setIsAuthenticating(false);
      }
    },
    [persistState]
  );

  useEffect(() => {
    const stored = readStoredAuthState();
    if (!stored) {
      setIsLoading(false);
      return;
    }

    setTokens(stored.tokens);
    setUser(stored.user);
    persistState(stored.tokens, stored.user);

    if (stored.tokens.expiresAt <= Date.now()) {
      refreshTokens().finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [persistState, refreshTokens]);

  useEffect(() => {
    registerTokenProvider({
      getAccessToken: () => {
        const activeTokens = tokensRef.current;
        if (!activeTokens) {
          return null;
        }

        if (activeTokens.expiresAt <= Date.now()) {
          return null;
        }

        return activeTokens.accessToken;
      },
      refreshTokens,
      onUnauthorized: () => {
        void logout();
      },
    });

    return () => {
      registerTokenProvider({
        getAccessToken: () => null,
      });
    };
  }, [logout, refreshTokens]);

  const hasRole = useCallback(
    (...roles: string[]) => {
      if (!roles.length) {
        return true;
      }
      const currentUser = userRef.current;
      if (!currentUser?.roles?.length) {
        return false;
      }

      return roles.every((role) => currentUser.roles.includes(role));
    },
    []
  );

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user,
      tokens,
      isAuthenticated: Boolean(user),
      isLoading,
      isAuthenticating,
      login,
      logout,
      refreshTokens,
      hasRole,
    }),
    [user, tokens, isLoading, isAuthenticating, login, logout, refreshTokens, hasRole]
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }

  return context;
};
