import numpy as np
import pytest
from PIL import Image
from test_mapillary_images import FakeClient

from geographer_pipeline.cache import area_embeddings, connect, save_detections
from geographer_pipeline.detect.crop import crop_path
from geographer_pipeline.detect.geometry import Detection
from geographer_pipeline.mapillary.images import cache_images
from geographer_pipeline.match.embed import embed_area


class FakeEmbedder:
    name = "fake/1"

    def __init__(self):
        self.calls = 0

    def embed_images(self, images):
        self.calls += 1
        # The crop's red level, as a unit vector.
        vectors = [[image.getpixel((0, 0))[0], 255.0] for image in images]
        return np.array(vectors) / np.linalg.norm(vectors, axis=1, keepdims=True)


def test_embeds_each_crop_once(tmp_path):
    db = connect(tmp_path / "cache.sqlite")
    cache_images(FakeClient(), db, ["1"], "area")
    bollard = Detection("bollard", "owl", (0.1, 0.1, 0.2, 0.2), 0.5)
    save_detections(db, "1", [("d1", bollard), ("d2", bollard)])
    for detection_id, red in [("d1", 255), ("d2", 0)]:
        path = crop_path("1", detection_id, tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (4, 4), (red, 0, 0)).save(path)
    embedder = FakeEmbedder()
    assert embed_area(db, "area", embedder, tmp_path) == 2
    assert embed_area(db, "area", embedder, tmp_path) == 0
    assert embedder.calls == 1
    vectors = area_embeddings(db, "area", "fake/1")
    assert vectors[("1", "d1")] == pytest.approx([2**-0.5, 2**-0.5], abs=0.01)
    assert vectors[("1", "d2")] == pytest.approx([0, 1])
    assert area_embeddings(db, "area", "other/model") == {}
    # Detecting again drops the old vectors with the old detections.
    save_detections(db, "1", [])
    assert area_embeddings(db, "area", "fake/1") == {}
