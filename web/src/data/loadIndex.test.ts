import { afterEach, describe, expect, it, vi } from "vitest";
import { DataError, loadCountryIndex, pickRandomImage } from "./loadIndex";
import type { CountryIndex } from "./indexSchema";

const india: CountryIndex = {
  schema_version: 1,
  country: "IN",
  name: "India",
  bbox: [68.1, 6.7, 97.4, 35.5],
  images: ["101", "202", "303"],
  analysed: [],
};

function stubFetch(status: number, body: unknown) {
  const response = new Response(JSON.stringify(body), { status });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("loadCountryIndex", () => {
  it("returns a valid index", async () => {
    stubFetch(200, india);
    await expect(loadCountryIndex("IN")).resolves.toEqual(india);
    expect(fetch).toHaveBeenCalledWith("/data/index/IN.json");
  });

  it("rejects an HTTP error", async () => {
    stubFetch(404, {});
    await expect(loadCountryIndex("XX")).rejects.toThrow(DataError);
  });

  it("rejects data in the wrong shape", async () => {
    stubFetch(200, { ...india, images: [] });
    await expect(loadCountryIndex("IN")).rejects.toThrow(/expected format/);
  });
});

describe("pickRandomImage", () => {
  it("maps the random number onto the image list", () => {
    expect(pickRandomImage(india, () => 0)).toBe("101");
    expect(pickRandomImage(india, () => 0.99)).toBe("303");
  });

  it("prefers analysed images when there are any", () => {
    const analysed = { ...india, analysed: ["404", "505"] };
    expect(pickRandomImage(analysed, () => 0)).toBe("404");
    expect(pickRandomImage(analysed, () => 0.99)).toBe("505");
  });
});
