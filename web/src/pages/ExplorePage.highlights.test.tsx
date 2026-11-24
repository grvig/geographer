import { act, fireEvent, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clearClueCache } from "../data/loadClues";
import { clearShardCache } from "../data/loadShard";
import type { Detection } from "../data/shardSchema";
import { renderRoute } from "../test/renderRoute";
import type { Hover, ViewerImage } from "../viewer/MapillaryViewer";

type ViewerProps = {
  imageId: string;
  detections: Detection[];
  onImageChange: (image: ViewerImage) => void;
  onHover: (hit: Hover | null) => void;
  onSelect: (hit: Hover | null) => void;
};

// The fake viewer exposes its props so tests can play the user's pointer.
const viewer = vi.hoisted(() => ({ props: null as ViewerProps | null }));

vi.mock("../viewer/MapillaryViewer", () => ({
  default: (props: ViewerProps) => {
    viewer.props = props;
    return <p>{props.detections.length} outlines</p>;
  },
}));
vi.mock("../components/Minimap", () => ({ default: () => null }));

const detection = (id: string, clue: string | null): Detection => ({
  id,
  category: "bollard",
  source: "manual",
  shape: { type: "rect", coords: [0.1, 0.1, 0.2, 0.3] },
  clue,
  confidence: 0.82,
  alternatives: [],
  consistent: true,
  verified: false,
});

const shard = {
  schema_version: 1,
  sequence: "seq",
  images: [
    {
      id: "500",
      lat: 47.3,
      lon: 4.2,
      country: "FR",
      admin1: "Bourgogne",
      is_pano: false,
      detections: [detection("d1", "fr-bollard"), detection("d2", null)],
    },
  ],
};

const clues = {
  schema_version: 1,
  categories: [
    {
      id: "bollard",
      label: "Bollard",
      overlay_colour: "#f59e0b",
      scene: false,
    },
  ],
  clues: [
    {
      id: "fr-bollard",
      category: "bollard",
      title: "French bollard",
      visual: { description: "A white post", features: ["white post"] },
      signifies: "France",
      regions: [{ country: "FR", strength: "typical" }],
      status: "draft",
    },
  ],
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.endsWith("clues.json")) {
        return Promise.resolve(Response.json(clues));
      }
      return Promise.resolve(Response.json(shard));
    }),
  );
});

afterEach(() => {
  clearShardCache();
  clearClueCache();
  vi.unstubAllGlobals();
});

async function openImage() {
  renderRoute("/explore/fr?image=500");
  const image = {
    id: "500",
    sequenceId: "seq",
    lat: 47.3,
    lon: 4.2,
    creator: "a",
  };
  act(() => viewer.props?.onImageChange(image));
  expect(await screen.findByText("2 outlines")).toBeInTheDocument();
}

describe("ExplorePage highlights", () => {
  it("shows a card on hover and hides it when the pointer leaves", async () => {
    await openImage();
    act(() => viewer.props?.onHover({ detectionId: "d1", x: 10, y: 10 }));
    expect(screen.getByRole("article")).toHaveTextContent("French bollard");
    act(() => viewer.props?.onHover(null));
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("keeps a clicked card until it is closed or Escape is pressed", async () => {
    await openImage();
    act(() => viewer.props?.onSelect({ detectionId: "d2", x: 10, y: 10 }));
    act(() => viewer.props?.onHover(null));
    expect(screen.getByRole("article")).toHaveTextContent("Unknown bollard");
    fireEvent.click(screen.getByRole("button", { name: "Close card" }));
    expect(screen.queryByRole("article")).not.toBeInTheDocument();

    act(() => viewer.props?.onSelect({ detectionId: "d1", x: 10, y: 10 }));
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("hides outlines with H and narrows them with the filters", async () => {
    await openImage();
    fireEvent.keyDown(window, { key: "h" });
    expect(screen.getByText("0 outlines")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "h" });
    expect(screen.getByText("2 outlines")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Checked by hand only"));
    expect(screen.getByText("0 outlines")).toBeInTheDocument();
    expect(screen.getByText(/hidden by the filters/)).toBeInTheDocument();
  });

  it("pins a card when an object is picked from the In view list", async () => {
    await openImage();
    fireEvent.click(screen.getByRole("button", { name: /French bollard/ }));
    expect(screen.getByRole("article")).toHaveTextContent("French bollard");
    expect(
      screen.getByRole("button", { name: "Close card" }),
    ).toBeInTheDocument();
  });
});
