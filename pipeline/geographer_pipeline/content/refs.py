"""Turns a detection crop into a reference photo for a clue.

The crop is copied to content/refs/<clue id>/NN.jpg and listed in the clue's
YAML file, with what attribution needs: the Mapillary image, creator and date.
The YAML is edited as text so its comments and layout survive.
"""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from geographer_pipeline.content.validate import CONTENT_DIR
from geographer_pipeline.detect.crop import CROPS_DIR, crop_path


def reference_lines(file: str, image) -> list[str]:
    taken = datetime.fromtimestamp(image["captured_at"] / 1000, UTC)
    return [
        f"  - file: {file}",
        f'    mapillary_image_id: "{image["id"]}"',
        # JSON strings are valid YAML, and escape any odd characters in names.
        f"    creator: {json.dumps(image['creator'])}",
        f'    captured_at: "{taken.date().isoformat()}"',
    ]


def insert_reference(text: str, lines: list[str]) -> str:
    rows = text.splitlines()
    if "references:" in rows:
        # After the last line of the existing list.
        end = rows.index("references:") + 1
        while end < len(rows) and rows[end].startswith(" "):
            end += 1
        rows[end:end] = lines
    else:
        before = len(rows)
        for key in ["sources:", "status:"]:
            if key in rows:
                before = min(before, rows.index(key))
        rows[before:before] = ["references:", *lines]
    return "\n".join(rows) + "\n"


def add_reference(
    db,
    clue_id: str,
    image_id: str,
    detection_id: str,
    content_dir: Path = CONTENT_DIR,
    crops_dir: Path = CROPS_DIR,
) -> str:
    matches = list((content_dir / "clues").glob(f"*/{clue_id}.yaml"))
    if not matches:
        raise ValueError(f"No clue called {clue_id}")
    crop = crop_path(image_id, detection_id, crops_dir)
    image = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if image is None or not crop.exists():
        raise ValueError(f"No crop for {image_id} {detection_id}; run detect first")
    text = matches[0].read_text(encoding="utf-8")
    if f'mapillary_image_id: "{image_id}"' in text:
        raise ValueError(f"{clue_id} already has a reference from image {image_id}")
    folder = content_dir / "refs" / clue_id
    folder.mkdir(parents=True, exist_ok=True)
    number = len(list(folder.glob("*.jpg"))) + 1
    file = f"{clue_id}/{number:02d}.jpg"
    shutil.copyfile(crop, content_dir / "refs" / file)
    new_text = insert_reference(text, reference_lines(file, image))
    matches[0].write_text(new_text, encoding="utf-8", newline="\n")
    return file
