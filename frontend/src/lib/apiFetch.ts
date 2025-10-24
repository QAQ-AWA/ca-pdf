import { clientEnv } from "./env";
import { getTokenProviderSnapshot } from "./httpClient";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data: unknown) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

const buildUrl = (input: string): string => {
  if (input.startsWith("http://") || input.startsWith("https://")) {
    return input;
  }

  const base = clientEnv.apiBaseUrl.replace(/\/$/, "");
  const path = input.startsWith("/") ? input : `/${input}`;

  return `${base}${path}`;
};

const parseResponse = async (response: Response): Promise<unknown> => {
  const contentType = response.headers.get("content-type");

  if (!contentType) {
    return null;
  }

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
};

let refreshInFlight: Promise<string | null> | null = null;

export const apiFetch = async <T = unknown>(input: string, init: RequestInit = {}): Promise<T> => {
  const url = buildUrl(input);
  const headers = new Headers(init.headers ?? undefined);

  const tokenProvider = getTokenProviderSnapshot();
  const token = tokenProvider.getAccessToken?.();

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const makeRequest = async (): Promise<Response> => {
    return fetch(url, {
      ...init,
      headers,
      credentials: init.credentials ?? "include",
    });
  };

  let response = await makeRequest();

  if (response.status === 401 && tokenProvider.refreshTokens) {
    if (!refreshInFlight) {
      refreshInFlight = tokenProvider.refreshTokens().finally(() => {
        refreshInFlight = null;
      });
    }

    const newToken = await refreshInFlight;

    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await makeRequest();
    } else {
      tokenProvider.onUnauthorized?.();
    }
  }

  if (!response.ok) {
    const data = await parseResponse(response);
    throw new ApiError(response.status, response.statusText || "Request failed", data);
  }

  return (await parseResponse(response)) as T;
};
