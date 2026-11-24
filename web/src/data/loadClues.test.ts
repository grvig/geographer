import { afterEach, describe, expect, it, vi } from "vitest";
import { clearClueCache, loadClues } from "./loadClues";

const file = {
  schema_version: 1,
  categories: [
    {
      id: "bollard",
      label: "Bollard",
      overlay_colour: "#f59e0b",
      scene: false,
    },
  ],
  clues: [
    {
      id: "fr-bollard-white-black-band",
      category: "bollard",
      title: "French bollard",
      visual: { description: "A white post", features: ["white"] },
      signifies: "France",
      regions: [{ country: "FR", strength: "typical" }],
      status: "draft",
    },
  ],
};

afterEach(() => {
  clearClueCache();
  vi.unstubAllGlobals();
});

describe("loadClues", () => {
  it("fetches once and indexes clues and categories by id", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() => Promise.resolve(Response.json(file)));
    vi.stubGlobal("fetch", fetchMock);
    const library = await loadClues();
    await loadClues();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith("/data/clues.json");
    expect(library.clues.get("fr-bollard-white-black-band")?.title).toBe(
      "French bollard",
    );
    expect(library.categories.get("bollard")?.label).toBe("Bollard");
  });

  it("tries again after a failed load", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("offline"))
      .mockResolvedValue(Response.json(file));
    vi.stubGlobal("fetch", fetchMock);
    await expect(loadClues()).rejects.toThrow("offline");
    const library = await loadClues();
    expect(library.clues.size).toBe(1);
  });
});
