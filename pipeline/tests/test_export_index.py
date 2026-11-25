import json
import random

import mapbox_vector_tile

from geographer_pipeline.areas import Area, Country
from geographer_pipeline.export.index import (
    add_analysed,
    build_indexes,
    sample_image_ids,
    write_index,
)
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


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_writes_index_and_updates_country_list_in_place(tmp_path):
    areas = [Area("A", TILE_BBOX)]
    assert build_indexes(FakeClient(), [country("IN", areas)], tmp_path, 1, 3, 0) == 0
    build_indexes(FakeClient(), [country("FR", areas)], tmp_path, 1, 3, 0)
    build_indexes(FakeClient(), [country("IN", areas)], tmp_path, 1, 4, 0)
    index = read(tmp_path / "IN.json")
    assert index["schema_version"] == 1
    assert index["bbox"] == [-180, -90, 180, 90]
    assert len(index["images"]) == 4
    assert read(tmp_path / "countries.json")["countries"] == [
        {"code": "IN", "name": "Country IN", "image_count": 4},
        {"code": "FR", "name": "Country FR", "image_count": 3},
    ]


def test_country_without_images_is_reported_not_written(tmp_path):
    empty = Area("Nowhere", [0, 0, 0.01, 0.01])
    assert build_indexes(FakeClient(), [country("XX", [empty])], tmp_path, 1, 5, 0) == 1
    assert not (tmp_path / "XX.json").exists()


def test_analysed_images_survive_resampling(tmp_path):
    france = country("FR", [Area("A", TILE_BBOX)])
    write_index(france, ["1", "2"], tmp_path)
    assert add_analysed("FR", ["30", "4"], tmp_path) == 2
    assert add_analysed("FR", ["4", "5"], tmp_path) == 3
    write_index(france, ["7"], tmp_path)
    index = json.loads((tmp_path / "FR.json").read_text(encoding="utf-8"))
    assert index["images"] == ["7"]
    assert index["analysed"] == ["4", "5", "30"]
