import { afterEach, describe, expect, it, vi } from "vitest";

async function loadEnv() {
  vi.resetModules();
  return import("./env");
}

describe("env", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("defaults the API URL to localhost:8000", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", undefined);
    vi.stubEnv("API_INTERNAL_URL", undefined);
    const { publicEnv, serverApiUrl } = await loadEnv();
    expect(publicEnv.apiUrl).toBe("http://localhost:8000");
    expect(serverApiUrl()).toBe("http://localhost:8000");
  });

  it("strips trailing slashes", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://cawasma.example/");
    const { publicEnv } = await loadEnv();
    expect(publicEnv.apiUrl).toBe("https://cawasma.example");
  });

  it("prefers API_INTERNAL_URL on the server", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    vi.stubEnv("API_INTERNAL_URL", "http://api:8000");
    const { serverApiUrl } = await loadEnv();
    expect(serverApiUrl()).toBe("http://api:8000");
  });
});
