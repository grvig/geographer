import { describe, expect, it } from "vitest";
import { cluesFileSchema } from "./clueSchema";

const minimalClue = {
  id: "in-milestone-yellow-top",
  category: "kilometre-marker",
  title: "Yellow-top milestone",
  visual: { description: "A white stone with a yellow top", features: ["x"] },
  signifies: "National Highway",
  regions: [{ country: "IN", strength: "typical" }],
  status: "draft",
};

function parse(clues: unknown[]) {
  return cluesFileSchema.safeParse({
    schema_version: 1,
    categories: [
      {
        id: "kilometre-marker",
        label: "Kilometre marker",
        overlay_colour: "#f472b6",
        scene: false,
      },
    ],
    clues,
  });
}

describe("cluesFileSchema", () => {
  it("fills optional lists with empty defaults", () => {
    const result = parse([minimalClue]);
    expect(result.success).toBe(true);
    const parsed = result.data?.clues[0];
    expect(parsed?.lookalikes).toEqual([]);
    expect(parsed?.references).toEqual([]);
    expect(parsed?.sources).toEqual([]);
  });

  it("rejects bad ids, strengths and source urls", () => {
    expect(parse([{ ...minimalClue, id: "India-1" }]).success).toBe(false);
    const always = [{ country: "IN", strength: "always" }];
    expect(parse([{ ...minimalClue, regions: always }]).success).toBe(false);
    const sources = [{ title: "Guide", url: "not a url" }];
    expect(parse([{ ...minimalClue, sources }]).success).toBe(false);
  });

  it("rejects a file from a different schema version", () => {
    const result = cluesFileSchema.safeParse({
      schema_version: 2,
      categories: [],
      clues: [],
    });
    expect(result.success).toBe(false);
  });
});
