import axios, { AxiosError } from "axios";

import { clientEnv } from "./env";

import type { InternalAxiosRequestConfig } from "axios";

type TokenProvider = {
  getAccessToken: () => string | null;
  refreshTokens?: () => Promise<string | null>;
  onUnauthorized?: () => void;
};

type AuthenticatedRequestConfig = InternalAxiosRequestConfig & {
  skipAuthRefresh?: boolean;
};

const defaultTokenProvider: TokenProvider = {
  getAccessToken: () => null,
};

let tokenProvider: TokenProvider = defaultTokenProvider;

export const registerTokenProvider = (provider: TokenProvider) => {
  tokenProvider = { ...defaultTokenProvider, ...provider };
};

export const getTokenProviderSnapshot = () => ({ ...tokenProvider });

export const httpClient = axios.create({
  baseURL: clientEnv.apiBaseUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = tokenProvider.getAccessToken?.();
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }

  return config;
});

let refreshPromise: Promise<string | null> | null = null;

httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalConfig = error.config as AuthenticatedRequestConfig | undefined;

    if (!originalConfig) {
      return Promise.reject(error);
    }

    if (originalConfig.skipAuthRefresh) {
      return Promise.reject(error);
    }

    const status = error.response?.status;

    if (status === 401 && tokenProvider.refreshTokens) {
      if (!refreshPromise) {
        refreshPromise = tokenProvider
          .refreshTokens()
          .catch(() => null)
          .finally(() => {
            refreshPromise = null;
          });
      }

      const newAccessToken = await refreshPromise;

      if (newAccessToken) {
        originalConfig.headers = {
          ...originalConfig.headers,
          Authorization: `Bearer ${newAccessToken}`,
        };
        originalConfig.skipAuthRefresh = true;
        return httpClient(originalConfig);
      }
    }

    if (status === 401) {
      tokenProvider.onUnauthorized?.();
    }

    return Promise.reject(error);
  }
);
