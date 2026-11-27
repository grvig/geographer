import shutil

import pytest

from geographer_pipeline.content.validate import CONTENT_DIR
from geographer_pipeline.curate.labels import append_label, load_labels


@pytest.fixture
def labels_dir(tmp_path):
    shutil.copytree(CONTENT_DIR / "schema", tmp_path / "schema")
    return tmp_path / "labels"


def label(action, **extra):
    return {
        "image_id": "123",
        "detection_id": "d1",
        "box": [0.1, 0.2, 0.3, 0.4],
        "action": action,
        **extra,
    }


def test_latest_label_for_a_detection_wins(labels_dir):
    append_label("saulieu", label("accept"), labels_dir)
    append_label("saulieu", label("relabel", clue="fr-bollard"), labels_dir)
    append_label("saulieu", {**label("reject"), "detection_id": "d2"}, labels_dir)
    labels = load_labels("saulieu", labels_dir)
    assert labels[("123", "d1")]["action"] == "relabel"
    assert labels[("123", "d1")]["clue"] == "fr-bollard"
    assert labels[("123", "d2")]["action"] == "reject"
    lines = (labels_dir / "saulieu.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert load_labels("other", labels_dir) == {}


@pytest.mark.parametrize(
    "bad",
    [
        label("relabel"),
        label("accept", clue="fr-bollard"),
        label("maybe"),
        {**label("accept"), "box": [0.1, 0.2]},
    ],
)
def test_invalid_labels_are_refused(labels_dir, bad):
    with pytest.raises(ValueError):
        append_label("saulieu", bad, labels_dir)
    assert not (labels_dir / "saulieu.jsonl").exists()


def test_a_broken_line_in_the_file_is_reported(labels_dir):
    labels_dir.mkdir()
    (labels_dir / "saulieu.jsonl").write_text('{"image_id": "1"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="saulieu.jsonl:1"):
        load_labels("saulieu", labels_dir)
