import shutil

import pytest

from geographer_pipeline.content.__main__ import main as content_main
from geographer_pipeline.content.validate import CONTENT_DIR, load_categories


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


def test_duplicate_category_ids_are_reported(content):
    entry = "- {id: pole, label: Pole, detector: {mapillary: [object--support--pole]},"
    entry += " overlay_colour: '#38bdf8', scene: false}\n"
    _, errors = load_categories(content(entry + entry))
    assert errors == ["categories.yaml: duplicate id pole"]
