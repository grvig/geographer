import shutil

import pytest
import yaml
from PIL import Image
from test_mapillary_images import FakeClient

from geographer_pipeline.cache import connect
from geographer_pipeline.content.refs import add_reference, insert_reference
from geographer_pipeline.content.validate import CONTENT_DIR, load_clues
from geographer_pipeline.detect.crop import crop_path
from geographer_pipeline.mapillary.images import cache_images

CLUE = "fr-bollard-white-black-band"


@pytest.fixture
def setup(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, content, ignore=shutil.ignore_patterns("refs"))
    db = connect(tmp_path / "cache.sqlite")
    cache_images(FakeClient(), db, ["7", "8"], "area")
    for image_id in ["7", "8"]:
        path = crop_path(image_id, "d1", tmp_path / "crops")
        path.parent.mkdir(parents=True)
        Image.new("RGB", (10, 20), "white").save(path)
    return db, content, tmp_path / "crops"


def test_copies_the_crop_and_lists_it_in_the_clue(setup):
    db, content, crops = setup
    assert add_reference(db, CLUE, "7", "d1", content, crops) == f"{CLUE}/01.jpg"
    assert add_reference(db, CLUE, "8", "d1", content, crops) == f"{CLUE}/02.jpg"
    clue_file = content / "clues" / "bollard" / f"{CLUE}.yaml"
    references = yaml.safe_load(clue_file.read_text(encoding="utf-8"))["references"]
    assert references[0] == {
        "file": f"{CLUE}/01.jpg",
        "mapillary_image_id": "7",
        "creator": "walker",
        "captured_at": "2023-11-14",
    }
    assert references[1]["mapillary_image_id"] == "8"
    _, errors = load_clues(content)
    assert errors == []


def test_refuses_duplicates_and_unknown_things(setup):
    db, content, crops = setup
    add_reference(db, CLUE, "7", "d1", content, crops)
    with pytest.raises(ValueError, match="already has a reference"):
        add_reference(db, CLUE, "7", "d1", content, crops)
    with pytest.raises(ValueError, match="No clue"):
        add_reference(db, "xx-nothing", "7", "d1", content, crops)
    with pytest.raises(ValueError, match="No crop"):
        add_reference(db, CLUE, "7", "d9", content, crops)


def test_new_list_goes_before_sources():
    text = "id: x\nsources:\n  - title: t\nstatus: draft\n"
    assert insert_reference(text, ["  - file: a"]) == (
        "id: x\nreferences:\n  - file: a\nsources:\n  - title: t\nstatus: draft\n"
    )
