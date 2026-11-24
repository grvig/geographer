import { OutlineTag, PolygonGeometry, RectGeometry } from "mapillary-js";
import type { Detection, Shape } from "../data/shardSchema";

const FALLBACK_COLOUR = "#ffffff";

export function hexToNumber(hex: string) {
  return Number.parseInt(hex.slice(1), 16);
}

function geometryFor(shape: Shape) {
  if (shape.type === "rect") {
    return new RectGeometry([...shape.coords]);
  }
  const ring = shape.coords.map(([x, y]) => [x, y]);
  const first = ring[0]!;
  const last = ring[ring.length - 1]!;
  // MapillaryJS only accepts closed polygons.
  if (first[0] !== last[0] || first[1] !== last[1]) {
    ring.push([first[0]!, first[1]!]);
  }
  return new PolygonGeometry(ring);
}

export function toTags(
  detections: Detection[],
  categoryColours: Map<string, string>,
) {
  return detections.map((detection) => {
    const colour = hexToNumber(
      categoryColours.get(detection.category) ?? FALLBACK_COLOUR,
    );
    return new OutlineTag(detection.id, geometryFor(detection.shape), {
      lineColor: colour,
      lineWidth: 2,
      fillColor: colour,
      fillOpacity: 0.12,
    });
  });
}
