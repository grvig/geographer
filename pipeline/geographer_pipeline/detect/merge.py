"""Combining Mapillary's detections with OWLv2's into one list per image."""

from geographer_pipeline.detect.geometry import Detection, iou

# Boxes overlapping more than this are taken to be the same object.
SAME_OBJECT_IOU = 0.5


def merge_detections(
    mapillary: list[Detection], owl: list[Detection]
) -> list[Detection]:
    # Mapillary outlines the object's real shape, so it wins over an OWLv2 box,
    # even when the two disagree on the category.
    merged = list(mapillary)
    for detection in owl:
        same = any(
            iou(detection.box, other.box) > SAME_OBJECT_IOU for other in mapillary
        )
        if not same:
            merged.append(detection)
    # Left to right, so detection ids stay stable between runs.
    return sorted(merged, key=lambda d: (d.box[0], d.box[1]))
