import pytest

from geographer_pipeline.detect.geometry import (
    Detection,
    iou,
    non_max_suppression,
    polygon_area,
    polygon_box,
)

SQUARE = [(0.1, 0.1), (0.3, 0.1), (0.3, 0.3), (0.1, 0.3)]


def test_polygon_box_and_area():
    assert polygon_box(SQUARE) == (0.1, 0.1, 0.3, 0.3)
    assert polygon_area(SQUARE) == pytest.approx(0.04)
    assert polygon_area(list(reversed(SQUARE))) == pytest.approx(0.04)


def test_iou():
    a = (0.0, 0.0, 0.2, 0.2)
    assert iou(a, a) == pytest.approx(1.0)
    assert iou(a, (0.1, 0.0, 0.3, 0.2)) == pytest.approx(1 / 3)
    assert iou(a, (0.5, 0.5, 0.6, 0.6)) == 0.0
    assert iou((0.1, 0.1, 0.1, 0.1), (0.1, 0.1, 0.1, 0.1)) == 0.0


def test_shape_prefers_polygon_and_rounds():
    rect = Detection("bollard", "owl", (0.123456, 0.2, 0.3, 0.4), 0.5)
    assert rect.shape() == {"type": "rect", "coords": [0.1235, 0.2, 0.3, 0.4]}
    outlined = Detection("utility-pole", "mapillary", (0.1, 0.1, 0.3, 0.3), 1.0, SQUARE)
    assert outlined.shape()["type"] == "polygon"
    assert outlined.shape()["coords"][0] == [0.1, 0.1]


def test_suppression_keeps_one_box_per_object_whatever_its_category():
    box = (0.1, 0.1, 0.2, 0.3)
    shifted = (0.11, 0.1, 0.21, 0.3)
    detections = [
        Detection("bollard", "owl", box, 0.4),
        Detection("bollard", "owl", shifted, 0.7),
        Detection("kilometre-marker", "owl", box, 0.5),
        Detection("bollard", "owl", (0.5, 0.5, 0.6, 0.6), 0.3),
    ]
    kept = non_max_suppression(detections, 0.5)
    assert [(d.category, d.score) for d in kept] == [("bollard", 0.7), ("bollard", 0.3)]
