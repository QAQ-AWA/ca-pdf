import { vi } from "vitest";

import { apiFetch, ApiError } from "./apiFetch";
import { registerTokenProvider } from "./httpClient";

describe("apiFetch", () => {
  beforeEach(() => {
    registerTokenProvider({
      getAccessToken: () => null,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    registerTokenProvider({
      getAccessToken: () => null,
    });
  });

  it("prefixes the API base URL and includes credentials", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    await apiFetch("/status");

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe("http://localhost:8000/status");
    expect(init).toMatchObject({ credentials: "include" });
  });

  it("attaches the bearer token when available", async () => {
    registerTokenProvider({
      getAccessToken: () => "token-123",
    });

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    await apiFetch("/me");

    const [, init] = fetchSpy.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Bearer token-123");
  });

  it("attempts token refresh and retries once after a 401 response", async () => {
    const refresh = vi.fn().mockResolvedValue("fresh-token");
    registerTokenProvider({
      getAccessToken: () => "stale-token",
      refreshTokens: refresh,
    });

    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response("Unauthorized", {
          status: 401,
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    const result = await apiFetch("/secure");

    expect(result).toEqual({ ok: true });
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetchSpy).toHaveBeenCalledTimes(2);
    const [, retryInit] = fetchSpy.mock.calls[1];
    const headers = new Headers(retryInit?.headers);
    expect(headers.get("Authorization")).toBe("Bearer fresh-token");
  });

  it("throws an ApiError when the response is not ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("Not found", { status: 404, statusText: "Not Found" })
    );

    const request = apiFetch("/missing");

    await expect(request).rejects.toBeInstanceOf(ApiError);
    await expect(request).rejects.toMatchObject({ status: 404 });
  });
});
