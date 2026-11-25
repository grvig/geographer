import io
import json

import mapbox_vector_tile
from PIL import Image
from test_export_index import TILE_BBOX
from test_mapillary_images import image_data

from geographer_pipeline.areas import AnalysisArea
from geographer_pipeline.cache import area_images, connect
from geographer_pipeline.detect.geometry import Detection
from geographer_pipeline.detect.run import detect_area, pick_images
from geographer_pipeline.mapillary.tiles import ImagePoint

AREA = AnalysisArea("test", "FR", TILE_BBOX, limit=3)


def point(image_id, sequence, captured_at, lon=None, is_pano=False):
    if lon is None:
        lon = (TILE_BBOX[0] + TILE_BBOX[2]) / 2
    lat = (TILE_BBOX[1] + TILE_BBOX[3]) / 2
    return ImagePoint(image_id, lon, lat, is_pano, captured_at, sequence)


def test_picks_consecutive_runs_inside_the_area():
    points = [
        point("1", "a", 3),
        point("2", "a", 1),
        point("3", "a", 2),
        point("4", "b", 1, is_pano=True),
        point("5", "b", 2, lon=TILE_BBOX[2] + 1),
    ]
    assert pick_images(points, AREA) == ["2", "3", "1"]


class FakeClient:
    def tile(self, z, x, y):
        features = [
            {
                "geometry": "POINT(2000 2000)",
                "properties": {"id": 11, "sequence_id": "s", "captured_at": 1},
            }
        ]
        layers = [{"name": "image", "features": features}]
        return mapbox_vector_tile.encode(layers, default_options={"y_coord_down": True})

    def graph(self, path, fields, **params):
        if path == "images":
            return {"data": [image_data(i) for i in params["image_ids"].split(",")]}
        return {"data": []}

    def download(self, url):
        buffer = io.BytesIO()
        Image.new("RGB", (400, 300), "grey").save(buffer, "JPEG")
        return buffer.getvalue()


class FakeOwl:
    def __init__(self):
        self.calls = 0

    def detect(self, image):
        self.calls += 1
        return [Detection("bollard", "owl", (0.5, 0.5, 0.6, 0.7), 0.45)]


def test_detects_crops_and_resumes(tmp_path):
    db = connect(tmp_path / "cache.sqlite")
    owl = FakeOwl()
    run = (FakeClient(), db, AREA, owl, {})
    assert detect_area(*run, tmp_path / "raw", tmp_path / "crops") == 1
    row = db.execute("SELECT * FROM detections").fetchone()
    assert (row["image_id"], row["id"], row["category"]) == ("11", "d1", "bollard")
    assert json.loads(row["shape"])["type"] == "rect"
    assert (tmp_path / "crops" / "11" / "d1.jpg").exists()
    assert area_images(db, "test")[0]["country"] == "FR"
    # A second run finds nothing left to do.
    assert detect_area(*run, tmp_path / "raw", tmp_path / "crops") == 0
    assert owl.calls == 1
