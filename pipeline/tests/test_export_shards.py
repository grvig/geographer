import json

from test_mapillary_images import FakeClient

from geographer_pipeline.areas import AnalysisArea
from geographer_pipeline.cache import connect, images_with_detections, save_detections
from geographer_pipeline.detect.geometry import Detection
from geographer_pipeline.export.shards import export_area
from geographer_pipeline.geocode import geocode_images
from geographer_pipeline.mapillary.images import cache_images

AREA = AnalysisArea("test", "FR", [4.0, 47.0, 4.5, 47.5], limit=10)


def analysed_cache(tmp_path):
    db = connect(tmp_path / "cache.sqlite")
    cache_images(FakeClient(), db, ["1", "2", "3"], AREA.name)
    geocode_images(db, AREA.name)
    found = [
        Detection("bollard", "owl", (0.1, 0.2, 0.15, 0.4), 0.456),
        Detection("utility-pole", "mapillary", (0.5, 0.0, 0.6, 0.5), 1.0),
    ]
    save_detections(db, "1", list(zip(["d1", "d2"], found, strict=True)))
    save_detections(db, "2", [])
    return db


def test_writes_one_shard_per_sequence_with_unknown_objects(tmp_path):
    db = analysed_cache(tmp_path)
    [path] = export_area(db, AREA, tmp_path / "images")
    assert path == tmp_path / "images" / "FR" / "seq1.json"
    shard = json.loads(path.read_text(encoding="utf-8"))
    assert shard["schema_version"] == 1
    assert shard["sequence"] == "seq1"
    # Image 3 hasn't been through detection yet, so it isn't exported.
    assert [image["id"] for image in shard["images"]] == ["1", "2"]
    first = shard["images"][0]
    assert (first["country"], first["admin1"]) == ("FR", "Bourgogne")
    assert first["detections"][0] == {
        "id": "d1",
        "category": "bollard",
        "source": "owl",
        "shape": {"type": "rect", "coords": [0.1, 0.2, 0.15, 0.4]},
        "clue": None,
        "confidence": 0.46,
        "alternatives": [],
        "consistent": None,
        "verified": False,
    }
    assert shard["images"][1]["detections"] == []
    assert images_with_detections(db, AREA.name) == ["1"]


def test_keeps_hand_checked_images(tmp_path):
    db = analysed_cache(tmp_path)
    [path] = export_area(db, AREA, tmp_path / "images")
    shard = json.loads(path.read_text(encoding="utf-8"))
    shard["images"][0]["detections"][0]["verified"] = True
    shard["images"][0]["detections"][0]["clue"] = "fr-bollard"
    manual = {"id": "9", "detections": [{"verified": False, "source": "manual"}]}
    shard["images"].append(manual)
    path.write_text(json.dumps(shard), encoding="utf-8")
    export_area(db, AREA, tmp_path / "images")
    images = json.loads(path.read_text(encoding="utf-8"))["images"]
    assert [image["id"] for image in images] == ["1", "2", "9"]
    assert images[0]["detections"][0]["clue"] == "fr-bollard"
