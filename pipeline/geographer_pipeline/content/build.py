"""Builds web/public/data/clues.json from the validated clue database."""

import sys
from pathlib import Path

from geographer_pipeline.content.validate import (
    CONTENT_DIR,
    load_categories,
    load_clues,
)
from geographer_pipeline.export.index import write_json

# Bump when the shape changes, together with the site's schema for this file.
SCHEMA_VERSION = 1
CLUES_JSON = CONTENT_DIR.parent / "web" / "public" / "data" / "clues.json"
# Detector settings only matter to the pipeline, so the site doesn't get them.
SITE_CATEGORY_FIELDS = ["id", "label", "overlay_colour", "scene"]


def build(content_dir: Path = CONTENT_DIR, out_path: Path = CLUES_JSON) -> int:
    clues, errors = load_clues(content_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("Not built: fix the problems above first.", file=sys.stderr)
        return 1
    categories, _ = load_categories(content_dir)
    site_categories = []
    for category in categories:
        site_categories.append({key: category[key] for key in SITE_CATEGORY_FIELDS})
    data = {
        "schema_version": SCHEMA_VERSION,
        "categories": site_categories,
        "clues": sorted(clues, key=lambda clue: clue["id"]),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, data)
    print(f"Wrote {len(clues)} clues to {out_path}")
    return 0
