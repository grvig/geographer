import type { CSSProperties } from "react";

const GAP = 16;

// Opens the card towards the larger free area around the pointer, so it stays
// inside the viewer whichever corner the object is in.
export function placeCard(
  x: number,
  y: number,
  width: number,
  height: number,
): CSSProperties {
  const style: CSSProperties = {};
  if (x < width / 2) {
    style.left = x + GAP;
  } else {
    style.right = width - x + GAP;
  }
  if (y < height / 2) {
    style.top = y + GAP;
  } else {
    style.bottom = height - y + GAP;
  }
  return style;
}
