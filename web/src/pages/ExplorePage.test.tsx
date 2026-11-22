import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderRoute } from "../test/renderRoute";

vi.mock("../viewer/MapillaryViewer", () => ({
  default: (props: { imageId: string }) => <p>viewer at {props.imageId}</p>,
}));

function stubFetch(status: number, body: unknown) {
  const response = new Response(JSON.stringify(body), { status });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ExplorePage", () => {
  it("starts at a random image from the country index", async () => {
    stubFetch(200, {
      schema_version: 1,
      country: "IN",
      name: "India",
      bbox: [68, 6, 97, 35],
      images: ["777"],
    });
    renderRoute("/explore/in");
    expect(await screen.findByText("viewer at 777")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/data/index/IN.json");
  });

  it("opens the image named in the URL without loading the index", () => {
    stubFetch(500, {});
    renderRoute("/explore/in?image=555");
    expect(screen.getByText("viewer at 555")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("explains when a country has no data", async () => {
    stubFetch(404, {});
    renderRoute("/explore/zz");
    expect(await screen.findByRole("alert")).toHaveTextContent("ZZ");
  });
});
