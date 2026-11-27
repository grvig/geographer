"""People's verdicts on detections, kept in content/labels/<area>.jsonl.

The file is append-only: each review adds a line, and the latest line for a
detection wins. That keeps history and makes merges in git painless.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from geographer_pipeline.content.validate import CONTENT_DIR, schema_errors

LABELS_DIR = CONTENT_DIR / "labels"


def label_errors(label: dict, where: str, content_dir: Path = CONTENT_DIR) -> list:
    return schema_errors(content_dir, "label", label, where)


def append_label(area: str, label: dict, labels_dir: Path = LABELS_DIR) -> dict:
    label = {**label, "at": datetime.now(UTC).isoformat(timespec="seconds")}
    errors = label_errors(label, "label", labels_dir.parent)
    if errors:
        raise ValueError("; ".join(errors))
    labels_dir.mkdir(parents=True, exist_ok=True)
    with (labels_dir / f"{area}.jsonl").open(
        "a", encoding="utf-8", newline="\n"
    ) as file:
        file.write(json.dumps(label, ensure_ascii=False) + "\n")
    return label


def load_labels(area: str, labels_dir: Path = LABELS_DIR) -> dict[tuple, dict]:
    path = labels_dir / f"{area}.jsonl"
    labels = {}
    if not path.exists():
        return labels
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        label = json.loads(line)
        errors = label_errors(label, f"{path.name}:{number}", labels_dir.parent)
        if errors:
            raise ValueError("; ".join(errors))
        labels[(label["image_id"], label["detection_id"])] = label
    return labels
