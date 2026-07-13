import { describe, expect, it } from "vitest";
import { TokenStorage } from "@/lib/token-storage";
import { AUTH_CONFIG } from "@/lib/config";

// sessionStorage is reset after each test by vitest.setup.ts.

describe("TokenStorage", () => {
  it("round-trips the access token", () => {
    expect(TokenStorage.getAccessToken()).toBeNull();
    TokenStorage.setAccessToken("tok-123");
    expect(TokenStorage.getAccessToken()).toBe("tok-123");
    expect(sessionStorage.getItem(AUTH_CONFIG.accessTokenKey)).toBe("tok-123");
  });

  it("round-trips the session id", () => {
    expect(TokenStorage.getSessionId()).toBeNull();
    TokenStorage.setSessionId("sess-abc");
    expect(TokenStorage.getSessionId()).toBe("sess-abc");
  });

  it("reports authentication state from token presence", () => {
    expect(TokenStorage.isAuthenticated()).toBe(false);
    TokenStorage.setAccessToken("tok");
    expect(TokenStorage.isAuthenticated()).toBe(true);
  });

  it("clear() removes both token and session id", () => {
    TokenStorage.setAccessToken("tok");
    TokenStorage.setSessionId("sess");
    TokenStorage.clear();
    expect(TokenStorage.getAccessToken()).toBeNull();
    expect(TokenStorage.getSessionId()).toBeNull();
    expect(TokenStorage.isAuthenticated()).toBe(false);
  });
});
