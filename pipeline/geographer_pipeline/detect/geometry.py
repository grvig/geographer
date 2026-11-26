"""Detections and the box maths for comparing them. Coordinates are 0-1."""

import math
from dataclasses import dataclass

# x0, y0, x1, y1 with the origin at the image's top-left corner.
Box = tuple[float, float, float, float]
Point = tuple[float, float]


@dataclass
class Detection:
    category: str
    source: str
    box: Box
    score: float
    # The object's outline, when the source gives one (Mapillary does, OWLv2 doesn't).
    polygon: list[Point] | None = None

    def shape(self) -> dict:
        if self.polygon:
            coords = [[round(x, 4), round(y, 4)] for x, y in self.polygon]
            return {"type": "polygon", "coords": coords}
        return {"type": "rect", "coords": [round(value, 4) for value in self.box]}


def polygon_box(points: list[Point]) -> Box:
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return (min(xs), min(ys), max(xs), max(ys))


def polygon_area(points: list[Point]) -> float:
    # Shoelace formula; the sign depends on winding, so take the absolute value.
    total = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1], strict=True):
        total += x0 * y1 - x1 * y0
    return abs(total) / 2


def box_area(box: Box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def iou(a: Box, b: Box) -> float:
    overlap = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
    shared = box_area(overlap)
    union = box_area(a) + box_area(b) - shared
    if union <= 0:
        return 0.0
    return shared / union


def non_max_suppression(detections: list[Detection], limit: float) -> list[Detection]:
    # Keep the best-scoring box of each cluster of boxes that overlap by more
    # than the limit: they are one object, found several times or under several
    # categories, and one object gets one category.
    kept = []
    for detection in sorted(detections, key=lambda d: d.score, reverse=True):
        duplicate = any(iou(other.box, detection.box) > limit for other in kept)
        if not duplicate:
            kept.append(detection)
    return kept


def simplify(points: list, tolerance: float) -> list:
    # Douglas-Peucker: keep the point farthest from the line between the ends if
    # it strays more than the tolerance, and repeat on both halves.
    if len(points) < 3:
        return list(points)
    (x0, y0), (x1, y1) = points[0], points[-1]
    length = math.hypot(x1 - x0, y1 - y0)
    farthest = 0.0
    index = 0
    for i, (x, y) in enumerate(points[1:-1], 1):
        if length == 0:
            # A closed ring starts and ends on the same point.
            distance = math.hypot(x - x0, y - y0)
        else:
            distance = abs((y1 - y0) * x - (x1 - x0) * y + x1 * y0 - y1 * x0) / length
        if distance > farthest:
            farthest = distance
            index = i
    if farthest <= tolerance:
        return [points[0], points[-1]]
    head = simplify(points[: index + 1], tolerance)
    return head[:-1] + simplify(points[index:], tolerance)
