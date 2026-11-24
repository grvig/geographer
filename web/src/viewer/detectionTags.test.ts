import { describe, expect, it, vi } from "vitest";
import type { Detection } from "../data/shardSchema";
import { hexToNumber, toTags } from "./detectionTags";

// The real classes need WebGL; these record what they were built with.
vi.mock("mapillary-js", () => ({
  RectGeometry: class {
    constructor(public rect: number[]) {}
  },
  PolygonGeometry: class {
    constructor(public polygon: number[][]) {}
  },
  OutlineTag: class {
    constructor(
      public id: string,
      public geometry: unknown,
      public options: { lineColor: number },
    ) {}
  },
}));

function detection(id: string, category: string, shape: Detection["shape"]) {
  return {
    id,
    category,
    shape,
    source: "manual",
    clue: null,
    confidence: 0.5,
    alternatives: [],
    consistent: null,
    verified: false,
  } satisfies Detection;
}

describe("toTags", () => {
  it("colours outlines by category and closes polygons", () => {
    const colours = new Map([["bollard", "#f59e0b"]]);
    const tags = toTags(
      [
        detection("d1", "bollard", {
          type: "rect",
          coords: [0.1, 0.2, 0.3, 0.4],
        }),
        detection("d2", "unknown", {
          type: "polygon",
          coords: [
            [0, 0],
            [1, 0],
            [1, 1],
          ],
        }),
      ],
      colours,
    ) as unknown as {
      id: string;
      geometry: { rect?: number[]; polygon?: number[][] };
      options: { lineColor: number };
    }[];
    expect(tags[0]?.options.lineColor).toBe(0xf59e0b);
    expect(tags[0]?.geometry.rect).toEqual([0.1, 0.2, 0.3, 0.4]);
    expect(tags[1]?.options.lineColor).toBe(0xffffff);
    expect(tags[1]?.geometry.polygon).toEqual([
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 0],
    ]);
  });

  it("converts hex colours to numbers", () => {
    expect(hexToNumber("#4ade80")).toBe(0x4ade80);
  });
});
