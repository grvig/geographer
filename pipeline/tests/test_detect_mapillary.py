import base64

import mapbox_vector_tile
import pytest

from geographer_pipeline.detect.mapillary import (
    class_map,
    decode_outline,
    fetch_mapillary_detections,
)


def encode(wkt: str) -> str:
    layer = {"name": "mpy-or", "features": [{"geometry": wkt, "properties": {}}]}
    data = mapbox_vector_tile.encode(
        [layer], default_options={"y_coord_down": True, "extents": 4096}
    )
    return base64.b64encode(data).decode()


def test_normalises_a_polygon_with_y_pointing_down():
    outline = decode_outline(encode("POLYGON ((0 0, 2048 0, 2048 1024, 0 1024, 0 0))"))
    assert outline[:4] == [(0.0, 0.0), (0.5, 0.0), (0.5, 0.25), (0.0, 0.25)]


def test_keeps_the_largest_piece_of_a_multipolygon():
    small = "((3000 3000, 3100 3000, 3100 3100, 3000 3100, 3000 3000))"
    large = "((100 100, 500 100, 500 900, 100 900, 100 100))"
    outline = decode_outline(encode(f"MULTIPOLYGON ({small}, {large})"))
    xs = [x for x, _ in outline]
    assert min(xs) == pytest.approx(100 / 4096)
    assert max(xs) == pytest.approx(500 / 4096)


def test_non_polygon_geometry_gives_no_outline():
    assert decode_outline(encode("LINESTRING (0 0, 100 100)")) == []


CATEGORIES = [
    {
        "id": "utility-pole",
        "detector": {"mapillary": ["object--support--utility-pole"]},
    },
    {
        "id": "bollard",
        "detector": {"owl": {"prompts": ["a bollard"], "threshold": 0.3}},
    },
]
SQUARE = "POLYGON ((0 0, 2048 0, 2048 1024, 0 1024, 0 0))"


class FakeClient:
    def graph(self, path, fields):
        assert path == "123/detections"
        items = [
            {"value": "object--support--utility-pole", "geometry": encode(SQUARE)},
            {"value": "nature--sky", "geometry": encode(SQUARE)},
            {
                "value": "object--support--utility-pole",
                "geometry": encode("POINT (1 1)"),
            },
        ]
        return {"data": items}


def test_keeps_only_mapped_classes_with_an_outline():
    classes = class_map(CATEGORIES)
    assert classes == {"object--support--utility-pole": "utility-pole"}
    detections = fetch_mapillary_detections(FakeClient(), "123", classes)
    assert len(detections) == 1
    assert detections[0].category == "utility-pole"
    assert detections[0].source == "mapillary"
    assert detections[0].box == (0.0, 0.0, 0.5, 0.25)
