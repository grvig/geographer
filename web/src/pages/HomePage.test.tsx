import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderRoute } from "../test/renderRoute";

function stubFetch(status: number, body: unknown) {
  const response = new Response(JSON.stringify(body), { status });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("HomePage", () => {
  it("lists the processed countries as links to explore", async () => {
    stubFetch(200, {
      schema_version: 1,
      countries: [
        { code: "IN", name: "India", image_count: 500 },
        { code: "FR", name: "France", image_count: 500 },
      ],
    });
    renderRoute("/");
    expect(
      screen.getByRole("heading", { level: 1, name: "Geographer" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading countries");
    const india = await screen.findByRole("link", { name: "India" });
    expect(india).toHaveAttribute("href", "/explore/in");
    expect(screen.getByRole("link", { name: "France" })).toBeInTheDocument();
  });

  it("says so when the country list fails to load", async () => {
    stubFetch(500, {});
    renderRoute("/");
    expect(await screen.findByRole("alert")).toHaveTextContent("didn't load");
  });
});
