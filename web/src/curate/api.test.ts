import { afterEach, describe, expect, it, vi } from "vitest";
import { loadQueue, sendLabel } from "./api";

function stubFetch(status: number, body: unknown) {
  const fetchMock = vi.fn<typeof fetch>(async () =>
    Response.json(body, { status }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

const item = {
  image_id: "5",
  detection_id: "d1",
  category: "bollard",
  source: "owl",
  box: [0.1, 0.2, 0.15, 0.4],
  clue: null,
  confidence: 0.45,
  alternatives: [],
  crop: "/api/crops/5/d1.jpg",
};

describe("curation api", () => {
  it("loads and checks the queue for an area", async () => {
    const fetchMock = stubFetch(200, { total: 1, items: [item] });
    const queue = await loadQueue("saulieu & co");
    expect(queue.items[0]!.detection_id).toBe("d1");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/queue?area=saulieu%20%26%20co",
      undefined,
    );
  });

  it("posts labels as JSON", async () => {
    const fetchMock = stubFetch(200, {});
    const target = { area: "a", image_id: "5", detection_id: "d1" };
    await sendLabel(target, "relabel", "fr-bollard");
    const init = fetchMock.mock.calls[0]![1]!;
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      ...target,
      action: "relabel",
      clue: "fr-bollard",
    });
  });

  it("passes on the server's reason for a refusal", async () => {
    stubFetch(400, { detail: "There is no match to accept" });
    const target = { area: "a", image_id: "5", detection_id: "d1" };
    await expect(sendLabel(target, "accept")).rejects.toThrow(
      "There is no match to accept",
    );
  });
});
