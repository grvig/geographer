import { fireEvent, render, screen, within } from "@testing-library/react";
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
  vi.mocked(api.sendLabel).mockResolvedValue({});
  vi.mocked(api.addReference).mockResolvedValue({ file: "fr-bollard/05.jpg" });
});

const target = (detection_id: string) => ({
  area: "saulieu",
  image_id: "5",
  detection_id,
});

async function itemFor(detectionId: string) {
  const crop = await screen.findByRole("img", {
    name: `bollard ${detectionId} in image 5`,
  });
  return within(crop.closest("li")!);
}

describe("CuratePage", () => {
  it("lists the first area's queue with each crop and answer", async () => {
    render(<CuratePage />);
    expect(await screen.findByText("2 left to review")).toBeInTheDocument();
    expect(api.loadQueue).toHaveBeenCalledWith("saulieu");
    expect(screen.getByText("Unknown bollard")).toBeInTheDocument();
    expect(
      screen.getByText("White bollard", { selector: "p" }),
    ).toBeInTheDocument();
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

  it("saves a verdict and takes the item off the queue", async () => {
    render(<CuratePage />);
    const item = await itemFor("d2");
    fireEvent.click(item.getByRole("button", { name: /Right/ }));
    expect(await screen.findByText("1 left to review")).toBeInTheDocument();
    expect(api.sendLabel).toHaveBeenCalledWith(
      target("d2"),
      "accept",
      undefined,
    );
    expect(screen.queryByRole("img", { name: /d2/ })).not.toBeInTheDocument();
  });

  it("can't accept an object the matcher didn't name", async () => {
    render(<CuratePage />);
    const item = await itemFor("d1");
    expect(item.getByRole("button", { name: /Right/ })).toBeDisabled();
  });

  it("relabels or takes a reference with the chosen clue", async () => {
    render(<CuratePage />);
    const first = await itemFor("d1");
    fireEvent.click(first.getByRole("button", { name: "It's this clue" }));
    expect(await screen.findByText("1 left to review")).toBeInTheDocument();
    expect(api.sendLabel).toHaveBeenCalledWith(
      target("d1"),
      "relabel",
      "fr-bollard",
    );
    const second = await itemFor("d2");
    fireEvent.click(second.getByRole("button", { name: /reference photo/ }));
    expect(await screen.findByText("0 left to review")).toBeInTheDocument();
    expect(api.addReference).toHaveBeenCalledWith(target("d2"), "fr-bollard");
  });

  it("answers keyboard shortcuts for the first item", async () => {
    render(<CuratePage />);
    await itemFor("d1");
    fireEvent.keyDown(window, { key: "a" });
    fireEvent.keyDown(window, { key: "x" });
    expect(await screen.findByText("1 left to review")).toBeInTheDocument();
    // The first item has no match, so A did nothing and X rejected it.
    expect(api.sendLabel).toHaveBeenCalledTimes(1);
    expect(api.sendLabel).toHaveBeenCalledWith(target("d1"), "reject");
  });

  it("shows the server's reason when a verdict is refused", async () => {
    vi.mocked(api.sendLabel).mockRejectedValue(new Error("No such detection"));
    render(<CuratePage />);
    const item = await itemFor("d1");
    fireEvent.click(item.getByRole("button", { name: /Unknown variant/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No such detection",
    );
    expect(screen.getByText("2 left to review")).toBeInTheDocument();
  });
});
