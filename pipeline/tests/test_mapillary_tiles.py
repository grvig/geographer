import mapbox_vector_tile
import pytest

from geographer_pipeline.mapillary.tiles import (
    decode_image_points,
    tile_to_lonlat,
    tile_xy,
    tiles_for_bbox,
)

BENGALURU = (77.5946, 12.9716)


def encode_points(*points):
    features = [
        {"geometry": f"POINT({px} {py})", "properties": properties}
        for px, py, properties in points
    ]
    layers = [{"name": "image", "features": features}]
    return mapbox_vector_tile.encode(layers, default_options={"y_coord_down": True})


def test_tile_xy_and_corner_round_trip():
    x, y = tile_xy(*BENGALURU)
    west, north = tile_to_lonlat(14, x, y, 0, 0, 4096)
    east, south = tile_to_lonlat(14, x, y, 4096, 4096, 4096)
    assert west <= BENGALURU[0] < east
    assert south < BENGALURU[1] <= north


def test_tiles_for_bbox_covers_every_tile_once():
    tiles = tiles_for_bbox([77.55, 12.93, 77.62, 13.0])
    assert len(tiles) == len(set(tiles))
    assert tile_xy(*BENGALURU) in tiles
    assert len(tiles) == 16


def test_decodes_points_with_top_left_origin():
    x, y = tile_xy(*BENGALURU)
    data = encode_points(
        (0, 0, {"id": 845419122985554, "captured_at": 5, "sequence_id": "s1"}),
        (4096, 4096, {"id": 7, "is_pano": True}),
    )
    top_left, bottom_right = decode_image_points(data, 14, x, y)
    assert top_left.id == "845419122985554"
    assert top_left.captured_at == 5
    assert top_left.sequence == "s1"
    assert not top_left.is_pano
    assert bottom_right.is_pano
    # A flipped y axis would swap the north and south edges.
    assert top_left.lat > bottom_right.lat
    west, north = tile_to_lonlat(14, x, y, 0, 0, 4096)
    assert top_left.lon == pytest.approx(west)
    assert top_left.lat == pytest.approx(north)


def test_tile_without_image_layer_has_no_points():
    data = mapbox_vector_tile.encode([{"name": "sequence", "features": []}])
    assert decode_image_points(data, 14, 0, 0) == []
