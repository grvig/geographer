import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderRoute } from "../test/renderRoute";

describe("HomePage", () => {
  it("renders the title at the root route", () => {
    renderRoute("/");
    expect(
      screen.getByRole("heading", { level: 1, name: "Geographer" }),
    ).toBeInTheDocument();
  });
});
