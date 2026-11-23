import random

import mapbox_vector_tile

from geographer_pipeline.areas import Area, Country
from geographer_pipeline.export.index import sample_image_ids
from geographer_pipeline.mapillary.tiles import tile_to_lonlat, tile_xy

# An area just inside one tile, so no neighbouring tile is sampled.
X, Y = tile_xy(77.5946, 12.9716)
WEST, NORTH = tile_to_lonlat(14, X, Y, 50, 50, 4096)
EAST, SOUTH = tile_to_lonlat(14, X, Y, 4000, 4000, 4096)
TILE_BBOX = [WEST, SOUTH, EAST, NORTH]


class FakeClient:
    def tile(self, z, x, y):
        # Twenty images on the tile's diagonal, plus one outside the area.
        features = [
            {"geometry": f"POINT({100 * i} {100 * i})", "properties": {"id": i}}
            for i in range(1, 21)
        ]
        features.append({"geometry": "POINT(4090 10)", "properties": {"id": 99}})
        layers = [{"name": "image", "features": features}]
        return mapbox_vector_tile.encode(layers, default_options={"y_coord_down": True})


def country(code, areas):
    return Country(code, f"Country {code}", [-180, -90, 180, 90], areas)


def test_each_area_gets_an_equal_share_of_sorted_ids():
    areas = [Area("A", TILE_BBOX), Area("B", TILE_BBOX)]
    ids = sample_image_ids(FakeClient(), country("IN", areas), 1, 10, random.Random(0))
    # Two shares of 5, drawn from the same 20 images, so overlaps are possible.
    assert 5 <= len(ids) <= 10
    assert ids == sorted(ids, key=int)
    assert "99" not in ids


def test_area_without_images_gives_no_ids():
    empty = Area("Nowhere", [0, 0, 0.01, 0.01])
    rng = random.Random(0)
    assert sample_image_ids(FakeClient(), country("XX", [empty]), 1, 5, rng) == []
