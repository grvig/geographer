import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "./api";
import CuratePage from "./CuratePage";

vi.mock("./api");

const matched: api.QueueItem = {
  image_id: "5",
  detection_id: "d2",
  category: "bollard",
  source: "owl",
  box: [0.5, 0.2, 0.55, 0.4],
  clue: "fr-bollard",
  confidence: 0.93,
  alternatives: [],
  crop: "/api/crops/5/d2.jpg",
};
const unknown: api.QueueItem = {
  ...matched,
  detection_id: "d1",
  clue: null,
  confidence: 0.45,
  crop: "/api/crops/5/d1.jpg",
};

beforeEach(() => {
  vi.mocked(api.loadAreas).mockResolvedValue([
    { name: "saulieu", country: "FR" },
  ]);
  vi.mocked(api.loadClueOptions).mockResolvedValue([
    { id: "fr-bollard", category: "bollard", title: "White bollard" },
  ]);
  vi.mocked(api.loadQueue).mockResolvedValue({
    total: 2,
    items: [unknown, matched],
  });
});

describe("CuratePage", () => {
  it("lists the first area's queue with each crop and answer", async () => {
    render(<CuratePage />);
    expect(await screen.findByText("2 left to review")).toBeInTheDocument();
    expect(api.loadQueue).toHaveBeenCalledWith("saulieu");
    expect(screen.getByText("Unknown bollard")).toBeInTheDocument();
    expect(screen.getByText("White bollard")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "bollard d2 in image 5" }),
    ).toHaveAttribute("src", "/api/crops/5/d2.jpg");
  });

  it("explains how to start the server when it isn't running", async () => {
    vi.mocked(api.loadAreas).mockRejectedValue(new Error("offline"));
    render(<CuratePage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "geographer_pipeline curate",
    );
  });
});
