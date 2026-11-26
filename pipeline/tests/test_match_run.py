import json

import numpy as np
from PIL import Image
from test_mapillary_images import FakeClient
from test_match_embed import FakeEmbedder

from geographer_pipeline.cache import connect, save_detections
from geographer_pipeline.detect.crop import crop_path
from geographer_pipeline.detect.geometry import Detection
from geographer_pipeline.geocode import geocode_images
from geographer_pipeline.mapillary.images import cache_images
from geographer_pipeline.match.references import Candidate
from geographer_pipeline.match.run import match_area
from geographer_pipeline.match.settings import Settings

SETTINGS = Settings("m", "p", 1.0, 0.02, 0.9, 0.5, 0.1)
NONE = np.zeros((0, 0), dtype=np.float32)
RED = np.array([[2**-0.5, 2**-0.5]], dtype=np.float32)
# Weight 1.0 makes descriptions irrelevant, so they can all be the same.
TEXT = np.zeros((1, 2), dtype=np.float32)
CLUES = {
    "fr-bollard": {"regions": [{"country": "FR", "strength": "typical"}]},
    "in-bollard": {"regions": [{"country": "IN", "strength": "typical"}]},
}


def test_matches_red_crops_and_checks_their_location(tmp_path):
    db = connect(tmp_path / "cache.sqlite")
    cache_images(FakeClient(), db, ["1"], "area")
    geocode_images(db, "area")
    bollard = Detection("bollard", "owl", (0.1, 0.1, 0.2, 0.2), 0.5)
    pole = Detection("utility-pole", "owl", (0.5, 0.1, 0.6, 0.9), 0.5)
    save_detections(db, "1", [("d1", bollard), ("d2", bollard), ("d3", pole)])
    for detection_id, red in [("d1", 255), ("d2", 0), ("d3", 255)]:
        path = crop_path("1", detection_id, tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (4, 4), (red, 0, 0)).save(path)
    candidates = {
        "bollard": [
            Candidate(None, NONE, TEXT),
            Candidate("fr-bollard", RED, TEXT),
            Candidate("in-bollard", NONE, TEXT),
        ]
    }
    args = (db, "area", FakeEmbedder(), candidates, CLUES, SETTINGS, tmp_path)
    assert match_area(*args) == (2, 1)
    rows = {row["detection_id"]: row for row in db.execute("SELECT * FROM matches")}
    # The red crop is the French bollard, and the image is in France.
    assert rows["d1"]["clue"] == "fr-bollard"
    assert rows["d1"]["consistent"] == 1
    # The black crop is nothing in particular: unknown, with no location verdict.
    assert rows["d2"]["clue"] is None
    assert rows["d2"]["consistent"] is None
    assert json.loads(rows["d2"]["alternatives"])[0]["clue"] in CLUES
    # Poles have no candidates here, so they get no match row.
    assert "d3" not in rows
    # Running again replaces rather than duplicates.
    assert match_area(*args) == (2, 1)
    assert db.execute("SELECT count(*) FROM matches").fetchone()[0] == 2
