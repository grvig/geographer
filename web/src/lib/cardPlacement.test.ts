import { describe, expect, it } from "vitest";
import { placeCard } from "./cardPlacement";

describe("placeCard", () => {
  it("opens towards the larger free area around the pointer", () => {
    expect(placeCard(100, 50, 800, 600)).toEqual({ left: 116, top: 66 });
    expect(placeCard(700, 500, 800, 600)).toEqual({ right: 116, bottom: 116 });
  });
});
