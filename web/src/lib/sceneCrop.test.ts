import { describe, expect, it } from "vitest";
import { cropStyle, paddedBox } from "./sceneCrop";

describe("paddedBox", () => {
  it("pads a rectangle by 15% of its size on each side", () => {
    const box = paddedBox({ type: "rect", coords: [0.2, 0.2, 0.4, 0.6] });
    expect(box.map((value) => value.toFixed(2))).toEqual([
      "0.17",
      "0.14",
      "0.43",
      "0.66",
    ]);
  });

  it("boxes a polygon and stops at the image edge", () => {
    const box = paddedBox({
      type: "polygon",
      coords: [
        [0, 0.5],
        [0.1, 0.5],
        [0.1, 1],
      ],
    });
    expect(box[0]).toBe(0);
    expect(box[3]).toBe(1);
  });
});

describe("cropStyle", () => {
  it("scales and slides the photo so the box fills the frame", () => {
    const photo = { src: "https://cdn/x.jpg", width: 2000, height: 1000 };
    const style = cropStyle(photo, {
      type: "rect",
      coords: [0.25, 0.25, 0.75, 0.75],
    });
    // Padded to [0.175, 0.175, 0.825, 0.825]: 0.65 of the photo each way.
    expect(style.backgroundImage).toBe('url("https://cdn/x.jpg")');
    expect(style.backgroundSize).toBe("153.85% 153.85%");
    expect(style.backgroundPosition).toBe("50.00% 50.00%");
    expect(style.aspectRatio).toBe("1300 / 650");
  });
});
