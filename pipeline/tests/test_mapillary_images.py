from geographer_pipeline.cache import area_images, connect
from geographer_pipeline.mapillary import images
from geographer_pipeline.mapillary.images import (
    cache_images,
    fetch_images,
    parse_image,
)


def image_data(image_id, **extra):
    data = {
        "id": image_id,
        "sequence": "seq1",
        "geometry": {"type": "Point", "coordinates": [4.2, 47.3]},
        "is_pano": False,
        "captured_at": 1700000000000,
        "creator": {"username": "walker", "id": "9"},
        "width": 4000,
        "height": 3000,
        "thumb_2048_url": f"https://cdn.example/{image_id}.jpg?sig=x",
    }
    data.update(extra)
    return data


def test_prefers_computed_position_over_raw_gps():
    computed = {"type": "Point", "coordinates": [4.25, 47.31]}
    image = parse_image(image_data("1", computed_geometry=computed))
    assert (image.lon, image.lat) == (4.25, 47.31)
    assert image.creator == "walker"
    assert parse_image(image_data("2")).lon == 4.2


def test_missing_creator_becomes_empty_name():
    assert parse_image(image_data("1", creator=None)).creator == ""


class FakeClient:
    def __init__(self):
        self.calls = []

    def graph(self, path, fields, **params):
        self.calls.append((path, params))
        ids = params["image_ids"].split(",")
        return {"data": [image_data(image_id) for image_id in ids]}


def test_fetches_in_batches(monkeypatch):
    monkeypatch.setattr(images, "BATCH_SIZE", 2)
    client = FakeClient()
    fetched = fetch_images(client, ["1", "2", "3"])
    assert [image.id for image in fetched] == ["1", "2", "3"]
    assert [params["image_ids"] for _, params in client.calls] == ["1,2", "3"]
    assert client.calls[0][0] == "images"


def test_caches_only_images_it_has_not_seen(tmp_path):
    db = connect(tmp_path / "cache.sqlite")
    client = FakeClient()
    assert cache_images(client, db, ["1", "2"], "FR/test") == 2
    assert cache_images(client, db, ["2", "3"], "FR/test") == 1
    assert client.calls[1][1]["image_ids"] == "3"
    rows = area_images(db, "FR/test")
    assert [row["id"] for row in rows] == ["1", "2", "3"]
    assert rows[0]["creator"] == "walker"
    assert rows[0]["is_pano"] == 0
    assert area_images(db, "IN/other") == []
