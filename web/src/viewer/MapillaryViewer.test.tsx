import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import MapillaryViewer from "./MapillaryViewer";

// MapillaryJS needs WebGL, which jsdom lacks, so the viewer is a fake.
const fake = vi.hoisted(() => ({
  handlers: new Map<string, (event: unknown) => void>(),
  moveTo: vi.fn(),
}));

vi.mock("mapillary-js", () => ({
  CancelMapillaryError: class extends Error {},
  Viewer: vi.fn(function () {
    return {
      on: (type: string, handler: (event: unknown) => void) => {
        fake.handlers.set(type, handler);
      },
      moveTo: fake.moveTo,
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
      lngLat: { lat: 1, lng: 2 },
      creatorUsername: "a",
    };
    act(() => fake.handlers.get("image")?.({ image }));
    expect(onImageChange).toHaveBeenCalledWith({
      id: "42",
      lat: 1,
      lon: 2,
      creator: "a",
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
