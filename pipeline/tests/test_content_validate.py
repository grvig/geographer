import shutil

import pytest
import yaml

from geographer_pipeline.content.__main__ import main as content_main
from geographer_pipeline.content.validate import (
    CONTENT_DIR,
    load_categories,
    load_clues,
)


@pytest.fixture
def content(tmp_path):
    """A content folder with the real schemas and the given categories file."""
    shutil.copytree(CONTENT_DIR / "schema", tmp_path / "schema")

    def write(categories_yaml):
        (tmp_path / "categories.yaml").write_text(categories_yaml, encoding="utf-8")
        return tmp_path

    return write


def test_shipped_categories_are_valid():
    categories, errors = load_categories()
    assert errors == []
    assert "bollard" in [category["id"] for category in categories]


def test_validate_command_passes_on_shipped_content(capsys):
    assert content_main(["validate"]) == 0
    assert "clues are valid" in capsys.readouterr().out


def test_category_schema_errors_name_the_field(content):
    path = content("- {id: Bollard, label: B, detector: {}, overlay_colour: red}\n")
    _, errors = load_categories(path)
    assert any("0/id" in error for error in errors)
    assert any("0/overlay_colour" in error for error in errors)
    assert any("'scene' is a required property" in error for error in errors)


TYPICAL = {"strength": "typical"}


@pytest.fixture
def clues_dir(tmp_path):
    """Real schemas and categories, plus a helper that writes one clue file."""
    shutil.copytree(CONTENT_DIR / "schema", tmp_path / "schema")
    shutil.copy(CONTENT_DIR / "categories.yaml", tmp_path)

    def write(file_name, folder="bollard", **fields):
        clue = {
            "id": file_name.removesuffix(".yaml"),
            "category": "bollard",
            "title": "Test bollard",
            "visual": {"description": "A plain white bollard", "features": ["white"]},
            "signifies": "Test",
            "regions": [{"country": "IN", "strength": "typical"}],
            "status": "draft",
        }
        clue.update(fields)
        path = tmp_path / "clues" / folder / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(clue), encoding="utf-8")

    return tmp_path, write


def test_valid_clues_with_lookalikes_and_references_pass(clues_dir):
    root, write = clues_dir
    reference = {"file": "in-a/01.jpg", "mapillary_image_id": "1", "creator": "x"}
    reference["captured_at"] = "2024-01-02"
    write("in-a.yaml", lookalikes=["fr-b"], references=[reference])
    write("fr-b.yaml", lookalikes=["in-a"])
    (root / "refs" / "in-a").mkdir(parents=True)
    (root / "refs" / "in-a" / "01.jpg").write_bytes(b"")
    clues, errors = load_clues(root)
    assert errors == []
    assert [clue["id"] for clue in clues] == ["fr-b", "in-a"]


def test_cross_file_rules_are_reported(clues_dir):
    root, write = clues_dir
    reference = {"file": "in-a/01.jpg", "mapillary_image_id": "1", "creator": "x"}
    reference["captured_at"] = "2024-01-02"
    write("in-a.yaml", lookalikes=["in-a", "zz-missing"], references=[reference])
    write("in-b.yaml", id="in-a")
    write("in-c.yaml", folder="poles", category="poles")
    _, errors = load_clues(root)
    assert errors == [
        "clues/bollard/in-a.yaml: missing refs/in-a/01.jpg",
        "clues/bollard/in-b.yaml: file name must match the id in-a",
        "clues/bollard/in-b.yaml: id in-a is used by clues/bollard/in-a.yaml",
        "clues/poles/in-c.yaml: unknown category poles",
        "clues/bollard/in-a.yaml: a clue can't be its own look-alike",
        "clues/bollard/in-a.yaml: unknown look-alike zz-missing",
    ]


def test_admin1_must_match_the_geocoder_spelling(clues_dir):
    root, write = clues_dir
    write("in-a.yaml", regions=[{"country": "IN", "admin1": "Karnataka"} | TYPICAL])
    write("fr-b.yaml", regions=[{"country": "FR", "admin1": "Bretagne"} | TYPICAL])
    write("in-c.yaml", regions=[{"country": "IN", "admin1": "Karnatka"} | TYPICAL])
    _, errors = load_clues(root)
    assert errors == [
        "clues/bollard/fr-b.yaml: FR has no region called 'Bretagne'"
        " (did you mean 'Brittany'?)",
        "clues/bollard/in-c.yaml: IN has no region called 'Karnatka'"
        " (did you mean 'Karnataka'?)",
    ]


def test_bad_yaml_and_schema_errors_are_reported(clues_dir):
    root, write = clues_dir
    write("in-a.yaml", status="final")
    write("in-b.yaml", folder="utility-pole")
    (root / "clues" / "bollard" / "in-c.yaml").write_text("id: [unclosed\n")
    _, errors = load_clues(root)
    assert errors[0] == "clues/bollard/in-a.yaml: status: 'final' is not one of " + (
        "['draft', 'reviewed']"
    )
    assert errors[1].startswith("clues/bollard/in-c.yaml: not valid YAML")
    assert errors[2] == "clues/utility-pole/in-b.yaml: belongs in clues/bollard/"


def test_duplicate_category_ids_are_reported(content):
    entry = "- {id: pole, label: Pole, detector: {mapillary: [object--support--pole]},"
    entry += " negatives: [a tree], overlay_colour: '#38bdf8', scene: false}\n"
    _, errors = load_categories(content(entry + entry))
    assert errors == ["categories.yaml: duplicate id pole"]
