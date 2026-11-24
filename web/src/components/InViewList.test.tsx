import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ClueLibrary } from "../data/loadClues";
import type { Detection, ShardImage } from "../data/shardSchema";
import type { Analysis } from "../viewer/useAnalysis";
import InViewList from "./InViewList";

const library: ClueLibrary = {
  clues: new Map([
    [
      "fr-bollard",
      {
        id: "fr-bollard",
        category: "bollard",
        title: "French bollard",
        visual: { description: "x", features: ["x"] },
        signifies: "France",
        regions: [{ country: "FR", strength: "typical" }],
        lookalikes: [],
        references: [],
        sources: [],
        status: "draft",
      },
    ],
  ]),
  categories: new Map([
    [
      "bollard",
      {
        id: "bollard",
        label: "Bollard",
        overlay_colour: "#f59e0b",
        scene: false,
      },
    ],
  ]),
};

function detection(id: string, clue: string | null): Detection {
  return {
    id,
    category: "bollard",
    source: "manual",
    shape: { type: "rect", coords: [0, 0, 1, 1] },
    clue,
    confidence: 0.82,
    alternatives: [],
    consistent: true,
    verified: false,
  };
}

const detections = [detection("d1", "fr-bollard"), detection("d2", null)];
const image: ShardImage = {
  id: "1",
  lat: 0,
  lon: 0,
  country: "FR",
  admin1: null,
  is_pano: false,
  detections,
  scene: [],
};

function analysis(extra: Partial<Analysis>): Analysis {
  return { imageId: "1", image, library, failed: false, ...extra };
}

function show(state: Analysis | null, shown = detections) {
  const onSelect = vi.fn();
  render(
    <InViewList
      analysis={state}
      detections={shown}
      selectedId="d1"
      onSelect={onSelect}
    />,
  );
  return onSelect;
}

describe("InViewList", () => {
  it("lists named and unknown objects and selects one on click", () => {
    const onSelect = show(analysis({}));
    expect(
      screen.getByRole("button", { name: /French bollard/ }),
    ).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: /Unknown bollard/ }));
    expect(onSelect).toHaveBeenCalledWith("d2");
  });

  it.each([
    [null, detections, "Checking this image"],
    [analysis({ failed: true, image: null }), [], "didn't load"],
    [
      analysis({ image: null, library: null }),
      [],
      "No analysis for this image yet",
    ],
    [
      analysis({ image: { ...image, detections: [] } }),
      [],
      "Nothing recognised",
    ],
    [analysis({}), [], "hidden by the filters"],
  ])("explains why nothing is listed (%#)", (state, shown, text) => {
    show(state, shown);
    expect(screen.getByText(new RegExp(text))).toBeInTheDocument();
  });
});
