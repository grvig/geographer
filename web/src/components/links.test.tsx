import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import GoogleMapsLink from "./GoogleMapsLink";
import MapillaryCredit from "./MapillaryCredit";

describe("GoogleMapsLink", () => {
  it("links to the coordinates in a new tab", () => {
    render(<GoogleMapsLink lat={12.9716} lon={77.5946} />);
    const link = screen.getByRole("link", { name: "Open in Google Maps" });
    expect(link).toHaveAttribute(
      "href",
      "https://www.google.com/maps/search/?api=1&query=12.971600,77.594600",
    );
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });
});

describe("MapillaryCredit", () => {
  it("credits the creator and links to the image", () => {
    render(<MapillaryCredit imageId="123" creator="alice" />);
    expect(screen.getByText(/© alice/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "View on Mapillary" }),
    ).toHaveAttribute("href", "https://www.mapillary.com/app/?pKey=123");
  });

  it("falls back to a generic credit without a creator", () => {
    render(<MapillaryCredit imageId="123" />);
    expect(screen.getByText(/© Mapillary contributor/)).toBeInTheDocument();
  });
});
