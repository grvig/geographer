import type { CSSProperties } from "react";
import type { Shape } from "../data/shardSchema";

// Same padding as the pipeline's crops, so the two pictures in the card match.
const PADDING = 0.15;

export type Photo = { src: string; width: number; height: number };

export function paddedBox(shape: Shape): [number, number, number, number] {
  let points: [number, number][] = shape.coords as [number, number][];
  if (shape.type === "rect") {
    const [x0, y0, x1, y1] = shape.coords;
    points = [
      [x0, y0],
      [x1, y1],
    ];
  }
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const padX = (Math.max(...xs) - Math.min(...xs)) * PADDING;
  const padY = (Math.max(...ys) - Math.min(...ys)) * PADDING;
  return [
    Math.max(0, Math.min(...xs) - padX),
    Math.max(0, Math.min(...ys) - padY),
    Math.min(1, Math.max(...xs) + padX),
    Math.min(1, Math.max(...ys) + padY),
  ];
}

// Shows one box of the photo by scaling it as a background and sliding it into
// place. A CSS percentage position p puts the image's p% point on the box's p%
// point, hence offset / (1 - size).
export function cropStyle(photo: Photo, shape: Shape): CSSProperties {
  const [x0, y0, x1, y1] = paddedBox(shape);
  const width = x1 - x0;
  const height = y1 - y0;
  let left = 0;
  if (width < 1) {
    left = (x0 / (1 - width)) * 100;
  }
  let top = 0;
  if (height < 1) {
    top = (y0 / (1 - height)) * 100;
  }
  return {
    backgroundImage: `url("${photo.src}")`,
    backgroundSize: `${(100 / width).toFixed(2)}% ${(100 / height).toFixed(2)}%`,
    backgroundPosition: `${left.toFixed(2)}% ${top.toFixed(2)}%`,
    aspectRatio: `${Math.round(width * photo.width)} / ${Math.round(height * photo.height)}`,
  };
}
