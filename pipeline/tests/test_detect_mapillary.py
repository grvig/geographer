import base64

import mapbox_vector_tile
import pytest

from geographer_pipeline.detect.mapillary import decode_outline


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
