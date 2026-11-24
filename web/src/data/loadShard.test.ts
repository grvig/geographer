import { afterEach, describe, expect, it, vi } from "vitest";
import { clearShardCache, findImage, loadShard } from "./loadShard";

const shard = {
  schema_version: 1,
  sequence: "seq_1",
  images: [
    {
      id: "123",
      lat: 12.97,
      lon: 77.59,
      country: "IN",
      admin1: "Karnataka",
      is_pano: false,
      detections: [
        {
          id: "d1",
          category: "bollard",
          source: "manual",
          shape: { type: "rect", coords: [0.4, 0.5, 0.45, 0.65] },
          clue: null,
          confidence: 0.3,
          consistent: null,
          verified: false,
        },
      ],
    },
  ],
};

function stubFetch(...responses: (Response | Error)[]) {
  const fetchMock = vi.fn();
  for (const response of responses) {
    if (response instanceof Error) {
      fetchMock.mockRejectedValueOnce(response);
    } else {
      fetchMock.mockResolvedValueOnce(response);
    }
  }
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  clearShardCache();
  vi.unstubAllGlobals();
});

describe("loadShard", () => {
  it("loads a sequence once and finds images in it", async () => {
    const fetchMock = stubFetch(Response.json(shard));
    const loaded = await loadShard("IN", "seq_1");
    await loadShard("IN", "seq_1");
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith("/data/images/IN/seq_1.json");
    expect(findImage(loaded, "123")?.detections[0]?.clue).toBeNull();
    expect(findImage(loaded, "999")).toBeNull();
  });

  it("treats a missing shard or an HTML fallback page as no analysis", async () => {
    stubFetch(
      new Response("", { status: 404 }),
      new Response("<!doctype html>", { status: 200 }),
    );
    expect(await loadShard("IN", "a")).toBeNull();
    expect(await loadShard("IN", "b")).toBeNull();
  });

  it("never builds a URL from unsafe ids", async () => {
    const fetchMock = stubFetch();
    expect(await loadShard("IN", "../secrets")).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects malformed shards and retries after network errors", async () => {
    const bad = { ...shard, images: [{ ...shard.images[0], lat: "north" }] };
    stubFetch(Response.json(bad), new TypeError("offline"));
    await expect(loadShard("IN", "x")).rejects.toThrow("expected format");
    await expect(loadShard("IN", "y")).rejects.toThrow("offline");
  });
});
