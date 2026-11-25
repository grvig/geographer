import pytest

from geographer_pipeline.detect.geometry import (
    Detection,
    iou,
    polygon_area,
    polygon_box,
    short_side_px,
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


def test_short_side_uses_image_pixels():
    # 10% of 2048 wide is 204.8 px; 2% of 1536 high is 30.72 px.
    assert short_side_px((0.0, 0.0, 0.1, 0.02), 2048, 1536) == pytest.approx(30.72)


def test_shape_prefers_polygon_and_rounds():
    rect = Detection("bollard", "owl", (0.123456, 0.2, 0.3, 0.4), 0.5)
    assert rect.shape() == {"type": "rect", "coords": [0.1235, 0.2, 0.3, 0.4]}
    outlined = Detection("utility-pole", "mapillary", (0.1, 0.1, 0.3, 0.3), 1.0, SQUARE)
    assert outlined.shape()["type"] == "polygon"
    assert outlined.shape()["coords"][0] == [0.1, 0.1]
