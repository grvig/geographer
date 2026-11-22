import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderRoute } from "../test/renderRoute";

describe("NotFoundPage", () => {
  it("renders for unknown addresses inside the layout", () => {
    renderRoute("/no/such/page");
    expect(
      screen.getByRole("heading", { name: "Page not found" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Geographer" })).toHaveAttribute(
      "href",
      "/",
    );
  });
});
