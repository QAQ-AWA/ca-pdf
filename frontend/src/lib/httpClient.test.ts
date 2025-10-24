import { vi } from "vitest";
import MockAdapter from "axios-mock-adapter";

import { httpClient, registerTokenProvider } from "./httpClient";

describe("httpClient", () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(httpClient);
    registerTokenProvider({
      getAccessToken: () => null,
    });
  });

  afterEach(() => {
    mock.restore();
    registerTokenProvider({
      getAccessToken: () => null,
    });
  });

  it("attaches the bearer token to outgoing requests", async () => {
    registerTokenProvider({
      getAccessToken: () => "sample-token",
    });

    mock.onGet("/protected").reply((config) => {
      expect(config.headers?.Authorization).toBe("Bearer sample-token");
      return [200, { ok: true }];
    });

    const response = await httpClient.get("/protected");

    expect(response.data).toEqual({ ok: true });
  });

  it("attempts to refresh the token after a 401 response", async () => {
    let token = "old-token";
    const refresh = vi.fn(async () => {
      token = "new-token";
      return token;
    });

    registerTokenProvider({
      getAccessToken: () => token,
      refreshTokens: refresh,
    });

    mock
      .onGet("/secure")
      .replyOnce((config) => {
        expect(config.headers?.Authorization).toBe("Bearer old-token");
        return [401];
      })
      .onGet("/secure")
      .replyOnce((config) => {
        expect(config.headers?.Authorization).toBe("Bearer new-token");
        return [200, { success: true }];
      });

    const response = await httpClient.get("/secure");

    expect(response.data).toEqual({ success: true });
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("notifies the auth layer when refresh fails", async () => {
    const onUnauthorized = vi.fn();
    registerTokenProvider({
      getAccessToken: () => "old-token",
      refreshTokens: async () => null,
      onUnauthorized,
    });

    mock.onGet("/secure").reply(401);

    await expect(httpClient.get("/secure")).rejects.toMatchObject({
      response: { status: 401 },
    });

    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });
});
