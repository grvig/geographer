import { describe, expect, it } from "vitest";
import type { Detection } from "../data/shardSchema";
import { DEFAULT_FILTERS, filterDetections } from "./filterDetections";

function detection(id: string, extra: Partial<Detection>): Detection {
  return {
    id,
    category: "bollard",
    source: "manual",
    shape: { type: "rect", coords: [0, 0, 1, 1] },
    clue: null,
    confidence: 0.5,
    alternatives: [],
    consistent: null,
    verified: false,
    ...extra,
  };
}

const all = [
  detection("pole", { category: "utility-pole" }),
  detection("weak", { confidence: 0.2 }),
  detection("checked", { verified: true, confidence: 0.9 }),
];

function ids(detections: Detection[]) {
  return detections.map((detection) => detection.id);
}

describe("filterDetections", () => {
  it("keeps everything by default", () => {
    expect(ids(filterDetections(all, DEFAULT_FILTERS))).toEqual([
      "pole",
      "weak",
      "checked",
    ]);
  });

  it("applies each filter", () => {
    const hidden = { ...DEFAULT_FILTERS, hiddenCategories: ["utility-pole"] };
    expect(ids(filterDetections(all, hidden))).toEqual(["weak", "checked"]);
    const confident = { ...DEFAULT_FILTERS, minConfidence: 0.4 };
    expect(ids(filterDetections(all, confident))).toEqual(["pole", "checked"]);
    const verified = { ...DEFAULT_FILTERS, verifiedOnly: true };
    expect(ids(filterDetections(all, verified))).toEqual(["checked"]);
  });
});
