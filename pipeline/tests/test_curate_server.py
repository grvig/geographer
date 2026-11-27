import shutil

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from test_mapillary_images import FakeClient

from geographer_pipeline.cache import connect, save_detections, save_matches
from geographer_pipeline.content.validate import CONTENT_DIR
from geographer_pipeline.curate.server import Paths, create_app
from geographer_pipeline.detect.crop import crop_path
from geographer_pipeline.detect.geometry import Detection
from geographer_pipeline.mapillary.images import cache_images

BOLLARD = "fr-bollard-white-black-band"


@pytest.fixture
def world(tmp_path):
    """A cache with one image: two bollards (one matched) and a street light."""
    shutil.copytree(CONTENT_DIR, tmp_path / "content")
    paths = Paths(
        cache=tmp_path / "cache.sqlite",
        content=tmp_path / "content",
        crops=tmp_path / "crops",
    )
    db = connect(paths.cache)
    cache_images(FakeClient(), db, ["5"], "test")
    found = [
        ("d1", Detection("bollard", "owl", (0.1, 0.2, 0.15, 0.4), 0.45)),
        ("d2", Detection("bollard", "owl", (0.5, 0.2, 0.55, 0.4), 0.5)),
        ("d3", Detection("street-light", "mapillary", (0.7, 0.1, 0.8, 0.3), 1.0)),
    ]
    save_detections(db, "5", found)
    save_matches(db, "test", [("5", "d2", BOLLARD, 0.93, "[]", 1)])
    db.close()
    for detection_id, _ in found:
        path = crop_path("5", detection_id, paths.crops)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 16), "white").save(path)
    return paths


def client(paths=None):
    return TestClient(create_app(paths or Paths()))


def test_health_and_areas():
    api = client()
    assert api.get("/api/health").json() == {"ok": True}
    areas = api.get("/api/areas").json()
    assert {"name": "saulieu", "country": "FR"} in areas


def test_no_interactive_docs_are_served():
    assert client().get("/docs").status_code == 404


def test_queue_lists_least_sure_first_in_categories_with_clues(world):
    body = client(world).get("/api/queue", params={"area": "test"}).json()
    assert body["total"] == 2
    first, second = body["items"]
    # d1 has no match yet, so its detector score (0.45) stands in.
    assert (first["detection_id"], first["clue"], first["confidence"]) == (
        "d1",
        None,
        0.45,
    )
    assert (second["detection_id"], second["clue"]) == ("d2", BOLLARD)
    assert first["box"] == [0.1, 0.2, 0.15, 0.4]
    assert first["crop"] == "/api/crops/5/d1.jpg"


def test_queue_can_show_one_category(world):
    params = {"area": "test", "category": "street-light"}
    body = client(world).get("/api/queue", params=params).json()
    assert [item["detection_id"] for item in body["items"]] == ["d3"]


def test_clues_for_the_relabel_picker(world):
    clues = client(world).get("/api/clues").json()
    assert {
        "id": BOLLARD,
        "category": "bollard",
        "title": "White bollard with a dark band",
    } in clues


def test_serves_crops_and_nothing_else(world):
    api = client(world)
    response = api.get("/api/crops/5/d1.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert api.get("/api/crops/5/d9.jpg").status_code == 404
    assert api.get("/api/crops/5/..%2F..%2Fcache.jpg").status_code == 404
    assert api.get("/api/crops/x5/d1.jpg").status_code == 404


def post_label(api, detection_id, action, **extra):
    body = {"area": "test", "image_id": "5", "detection_id": detection_id}
    return api.post("/api/labels", json={**body, "action": action, **extra})


def test_labelled_objects_leave_the_queue(world):
    api = client(world)
    response = post_label(api, "d2", "accept")
    assert response.status_code == 200
    assert response.json()["box"] == [0.5, 0.2, 0.55, 0.4]
    assert post_label(api, "d1", "relabel", clue=BOLLARD).status_code == 200
    body = api.get("/api/queue", params={"area": "test"}).json()
    assert body["total"] == 0
    lines = (world.content / "labels" / "test.jsonl").read_text(encoding="utf-8")
    assert len(lines.splitlines()) == 2


@pytest.mark.parametrize(
    ("detection_id", "action", "extra", "status"),
    [
        ("d1", "accept", {}, 400),
        ("d1", "relabel", {"clue": "fr-kilometre-marker-yellow-top"}, 400),
        ("d1", "relabel", {}, 400),
        ("d9", "reject", {}, 404),
        ("d1", "maybe", {}, 422),
    ],
)
def test_bad_labels_are_refused(world, detection_id, action, extra, status):
    response = post_label(client(world), detection_id, action, **extra)
    assert response.status_code == status
    assert not (world.content / "labels" / "test.jsonl").exists()
