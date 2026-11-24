import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import MapillaryViewer from "./MapillaryViewer";

// MapillaryJS needs WebGL, which jsdom lacks, so the viewer is a fake.
const fake = vi.hoisted(() => ({
  handlers: new Map<string, (event: unknown) => void>(),
  moveTo: vi.fn(),
  tags: { add: vi.fn(), removeAll: vi.fn(), getTagIdsAt: vi.fn() },
}));

vi.mock("mapillary-js", () => ({
  CancelMapillaryError: class extends Error {},
  RectGeometry: class {},
  PolygonGeometry: class {},
  OutlineTag: class {
    constructor(public id: string) {}
  },
  Viewer: vi.fn(function () {
    return {
      on: (type: string, handler: (event: unknown) => void) => {
        fake.handlers.set(type, handler);
      },
      moveTo: fake.moveTo,
      getComponent: () => fake.tags,
      remove: vi.fn(),
    };
  }),
}));

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("MapillaryViewer", () => {
  it("explains what to do when the token is missing", () => {
    vi.stubEnv("VITE_MAPILLARY_TOKEN", "");
    render(
      <MapillaryViewer
        imageId="1"
        onImageChange={vi.fn()}
        onBearingChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("VITE_MAPILLARY_TOKEN");
  });

  it("moves to the image and reports where it is", async () => {
    vi.stubEnv("VITE_MAPILLARY_TOKEN", "token");
    fake.moveTo.mockRejectedValue(new Error("network"));
    const onImageChange = vi.fn();
    render(
      <MapillaryViewer
        imageId="42"
        onImageChange={onImageChange}
        onBearingChange={vi.fn()}
      />,
    );
    expect(fake.moveTo).toHaveBeenCalledWith("42");
    expect(await screen.findByRole("alert")).toHaveTextContent("Image 42");

    const image = {
      id: "42",
      sequenceId: "seq_9",
      lngLat: { lat: 1, lng: 2 },
      creatorUsername: "a",
    };
    act(() => fake.handlers.get("image")?.({ image }));
    expect(onImageChange).toHaveBeenCalledWith({
      id: "42",
      sequenceId: "seq_9",
      lat: 1,
      lon: 2,
      creator: "a",
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("reports hover changes and clicks on outlines", async () => {
    vi.stubEnv("VITE_MAPILLARY_TOKEN", "token");
    fake.moveTo.mockResolvedValue(undefined);
    const onHover = vi.fn();
    const onSelect = vi.fn();
    render(
      <MapillaryViewer
        imageId="1"
        onImageChange={vi.fn()}
        onBearingChange={vi.fn()}
        onHover={onHover}
        onSelect={onSelect}
      />,
    );
    const move = (x: number, y: number) =>
      act(async () => fake.handlers.get("mousemove")?.({ pixelPoint: [x, y] }));

    fake.tags.getTagIdsAt.mockResolvedValue(["d1"]);
    await move(10, 20);
    await move(11, 21);
    expect(onHover).toHaveBeenCalledTimes(1);
    expect(onHover).toHaveBeenLastCalledWith({
      detectionId: "d1",
      x: 10,
      y: 20,
    });

    fake.tags.getTagIdsAt.mockResolvedValue([]);
    await move(300, 300);
    expect(onHover).toHaveBeenLastCalledWith(null);

    fake.tags.getTagIdsAt.mockResolvedValue(["d2"]);
    await act(async () => fake.handlers.get("click")?.({ pixelPoint: [5, 5] }));
    expect(onSelect).toHaveBeenCalledWith("d2");
  });

  it("replaces the outlines when the detections change", () => {
    vi.stubEnv("VITE_MAPILLARY_TOKEN", "token");
    fake.moveTo.mockResolvedValue(undefined);
    const shape = { type: "rect" as const, coords: [0, 0, 1, 1] as const };
    const detection = {
      id: "d1",
      category: "bollard",
      source: "manual" as const,
      shape: {
        ...shape,
        coords: [...shape.coords] as [number, number, number, number],
      },
      clue: null,
      confidence: 0.5,
      alternatives: [],
      consistent: null,
      verified: false,
    };
    const props = {
      imageId: "1",
      onImageChange: vi.fn(),
      onBearingChange: vi.fn(),
    };
    const { rerender } = render(<MapillaryViewer {...props} />);
    expect(fake.tags.add).toHaveBeenLastCalledWith([]);
    rerender(<MapillaryViewer {...props} detections={[detection]} />);
    expect(fake.tags.removeAll).toHaveBeenCalled();
    expect(fake.tags.add).toHaveBeenLastCalledWith([
      expect.objectContaining({ id: "d1" }),
    ]);
  });
});
