import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Clue } from "../data/clueSchema";
import type { ClueLibrary } from "../data/loadClues";
import type { Detection } from "../data/shardSchema";
import ClueCard from "./ClueCard";

function clue(id: string, title: string, extra: Partial<Clue> = {}): Clue {
  return {
    id,
    category: "kilometre-marker",
    title,
    visual: { description: "x", features: ["white stone", "yellow top"] },
    signifies: "Marks a National Highway.",
    regions: [{ country: "IN", strength: "typical" }],
    lookalikes: [],
    references: [],
    sources: [],
    status: "draft",
    ...extra,
  };
}

const library: ClueLibrary = {
  clues: new Map([
    [
      "in-yellow",
      clue("in-yellow", "Yellow-top milestone", {
        lookalikes: ["in-green"],
        tell_apart: "Check the colour of the top.",
        sources: [{ title: "Plonk It: India", url: "https://example.org/in" }],
      }),
    ],
    ["in-green", clue("in-green", "Green-top milestone")],
  ]),
  categories: new Map([
    [
      "kilometre-marker",
      {
        id: "kilometre-marker",
        label: "Kilometre marker",
        overlay_colour: "#f472b6",
        scene: false,
      },
    ],
  ]),
};

function detection(extra: Partial<Detection>): Detection {
  return {
    id: "d1",
    category: "kilometre-marker",
    source: "manual",
    shape: { type: "rect", coords: [0, 0, 1, 1] },
    clue: "in-yellow",
    confidence: 0.82,
    alternatives: [{ clue: "in-green", confidence: 0.11 }],
    consistent: true,
    verified: true,
    ...extra,
  };
}

const inIndia = { country: "IN", admin1: "Karnataka" };

describe("ClueCard", () => {
  it("shows what the clue is, where it points and how sure the match is", () => {
    render(
      <ClueCard
        detection={detection({})}
        library={library}
        imagePlace={inIndia}
      />,
    );
    expect(screen.getByRole("heading")).toHaveTextContent(
      "Yellow-top milestone",
    );
    expect(screen.getByText(/82% match · checked by hand/)).toBeInTheDocument();
    expect(screen.getByText("Typical of India")).toBeInTheDocument();
    expect(
      screen.getByText("Could also be: Green-top milestone (11%)"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Look-alikes: Green-top milestone"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Check the colour of the top."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Learn more/ })).toHaveAttribute(
      "href",
      "https://example.org/in",
    );
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("warns when the clue doesn't fit where the image was taken", () => {
    render(
      <ClueCard
        detection={detection({ consistent: false })}
        library={library}
        imagePlace={{ country: "FR", admin1: "Bourgogne" }}
      />,
    );
    expect(screen.getByRole("note")).toHaveTextContent(
      "Looks like yellow-top milestone (from India), but you're in Bourgogne, France: a look-alike!",
    );
  });

  it("names the category when the matcher abstained", () => {
    render(
      <ClueCard
        detection={detection({ clue: null, consistent: null })}
        library={library}
        imagePlace={inIndia}
      />,
    );
    expect(screen.getByRole("heading")).toHaveTextContent(
      "Unknown kilometre marker",
    );
  });
});
