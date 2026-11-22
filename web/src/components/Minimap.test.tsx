import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Minimap from "./Minimap";

// MapLibre needs WebGL, which jsdom lacks, so the map and marker are fakes.
const fake = vi.hoisted(() => ({
  jumpTo: vi.fn(),
  remove: vi.fn(),
  setLngLat: vi.fn(),
  setRotation: vi.fn(),
  addTo: vi.fn(),
  // A plain field, because the worker URL is set once at import and mock call
  // history is cleared before each test.
  workerUrl: "",
}));

vi.mock("maplibre-gl", () => ({
  setWorkerUrl: (url: string) => {
    fake.workerUrl = url;
  },
  Map: vi.fn(function () {
    return { jumpTo: fake.jumpTo, remove: fake.remove };
  }),
  Marker: vi.fn(function () {
    return {
      setLngLat: fake.setLngLat,
      setRotation: fake.setRotation,
      addTo: fake.addTo,
    };
  }),
}));

describe("Minimap", () => {
  it("points MapLibre at the bundled worker file", () => {
    expect(fake.workerUrl).toContain("maplibre-gl-worker");
  });

  it("centres on the position and rotates the heading marker", () => {
    const { rerender, unmount } = render(
      <Minimap lat={12.97} lon={77.59} bearing={0} />,
    );
    expect(fake.jumpTo).toHaveBeenLastCalledWith({ center: [77.59, 12.97] });

    rerender(<Minimap lat={13} lon={77.6} bearing={90} />);
    expect(fake.setLngLat).toHaveBeenLastCalledWith([77.6, 13]);
    expect(fake.setRotation).toHaveBeenLastCalledWith(90);

    unmount();
    expect(fake.remove).toHaveBeenCalled();
  });
});
