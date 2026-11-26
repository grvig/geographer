import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Clue } from "../data/clueSchema";
import ClueImages from "./ClueImages";

const clue: Clue = {
  id: "fr-bollard",
  category: "bollard",
  title: "White bollard",
  visual: { description: "x", features: ["white"] },
  signifies: "France.",
  regions: [{ country: "FR", strength: "typical" }],
  lookalikes: [],
  references: [
    {
      file: "fr-bollard/01.jpg",
      mapillary_image_id: "42",
      creator: "Pierre",
      captured_at: "2020-10-23",
    },
  ],
  sources: [],
  status: "draft",
};

const photo = { src: "https://cdn/photo.jpg", width: 2048, height: 1536 };

describe("ClueImages", () => {
  it("shows the first reference photo with its credit", () => {
    render(
      <ClueImages
        clue={clue}
        shape={{ type: "rect", coords: [0.4, 0.4, 0.6, 0.8] }}
        photo={null}
      />,
    );
    const picture = screen.getByRole("img", {
      name: "Reference photo: White bollard",
    });
    expect(picture.getAttribute("src")).toMatch(
      /\/data\/refs\/fr-bollard\/01\.jpg$/,
    );
    expect(screen.getByText(/Pierre/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "View on Mapillary" }),
    ).toHaveAttribute("href", "https://www.mapillary.com/app/?pKey=42");
  });

  it("says so when the clue has no photo yet", () => {
    render(
      <ClueImages
        clue={{ ...clue, references: [] }}
        shape={{ type: "rect", coords: [0.4, 0.4, 0.6, 0.8] }}
        photo={null}
      />,
    );
    expect(screen.getByText("No reference photo yet.")).toBeInTheDocument();
  });

  it("cuts the object out of the current photo when it has loaded", () => {
    render(
      <ClueImages
        clue={clue}
        shape={{ type: "rect", coords: [0.4, 0.4, 0.6, 0.8] }}
        photo={photo}
      />,
    );
    const crop = screen.getByRole("img", {
      name: /cut from the current image/,
    });
    expect(crop.style.backgroundImage).toContain("https://cdn/photo.jpg");
    expect(screen.getByText("Here")).toBeInTheDocument();
  });
});
