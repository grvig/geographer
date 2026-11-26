import json
import shutil

import yaml

from geographer_pipeline.content.attribution import attribution_markdown
from geographer_pipeline.content.build import build
from geographer_pipeline.content.validate import CONTENT_DIR


def make_content(tmp_path, clue_ids):
    shutil.copytree(CONTENT_DIR / "schema", tmp_path / "schema")
    shutil.copy(CONTENT_DIR / "categories.yaml", tmp_path)
    (tmp_path / "clues" / "bollard").mkdir(parents=True)
    for clue_id in clue_ids:
        clue = {
            "id": clue_id,
            "category": "bollard",
            "title": "Test bollard",
            "visual": {"description": "A plain white bollard", "features": ["white"]},
            "signifies": "Test",
            "regions": [{"country": "FR", "strength": "typical"}],
            "status": "draft",
        }
        path = tmp_path / "clues" / "bollard" / f"{clue_id}.yaml"
        path.write_text(yaml.safe_dump(clue), encoding="utf-8")
    return tmp_path


def test_build_writes_sorted_clues_and_site_categories(tmp_path):
    content = make_content(tmp_path / "content", ["in-b", "fr-a"])
    out = tmp_path / "out" / "clues.json"
    assert build(content, out) == 0
    assert b"\r\n" not in out.read_bytes()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert [clue["id"] for clue in data["clues"]] == ["fr-a", "in-b"]
    bollard = data["categories"][0]
    assert set(bollard) == {"id", "label", "overlay_colour", "scene"}
    credits = (tmp_path / "ATTRIBUTION.md").read_text(encoding="utf-8")
    assert "no reference photos yet" in credits


def test_build_refuses_invalid_content(tmp_path, capsys):
    content = make_content(tmp_path / "content", ["in-a"])
    clue_file = content / "clues" / "bollard" / "in-a.yaml"
    clue_file.rename(clue_file.with_name("in-z.yaml"))
    out = tmp_path / "clues.json"
    assert build(content, out) == 1
    assert not out.exists()
    assert "Not built" in capsys.readouterr().err


def test_attribution_lists_every_reference():
    clues = [
        {
            "id": "fr-a",
            "references": [
                {
                    "file": "fr-a/01.jpg",
                    "mapillary_image_id": "42",
                    "creator": "pipe|name",
                    "captured_at": "2020-10-23",
                }
            ],
        },
        {"id": "in-b"},
    ]
    text = attribution_markdown(clues)
    assert "CC-BY-SA 4.0" in text
    assert (
        "| `fr-a/01.jpg` | pipe\\|name | 2020-10-23 "
        "| [Mapillary image](https://www.mapillary.com/app/?pKey=42) |"
    ) in text
