"""Shards for the site: images/<CC>/<sequence id>.json, one file per sequence."""

import json
from collections import defaultdict
from pathlib import Path

from geographer_pipeline.cache import area_images, image_detections
from geographer_pipeline.export.index import write_json

# Must match SHARD_SCHEMA_VERSION in web/src/data/shardSchema.ts.
SCHEMA_VERSION = 1
SHARD_DIR = Path(__file__).resolve().parents[3] / "web" / "public" / "data" / "images"


def shard_image(row, detections) -> dict:
    # Matching to clues comes later, so for now every object is unknown and its
    # confidence is the detector's own score.
    entries = []
    for detection in detections:
        entry = {
            "id": detection["id"],
            "category": detection["category"],
            "source": detection["source"],
            "shape": json.loads(detection["shape"]),
            "clue": None,
            "confidence": round(detection["score"], 2),
            "alternatives": [],
            "consistent": None,
            "verified": False,
        }
        entries.append(entry)
    return {
        "id": row["id"],
        "lat": round(row["lat"], 6),
        "lon": round(row["lon"], 6),
        "country": row["country"],
        "admin1": row["admin1"],
        "is_pano": bool(row["is_pano"]),
        "detections": entries,
        "scene": [],
    }


def hand_checked_images(path: Path) -> dict[str, dict]:
    # Images in an existing shard that someone labelled or checked by hand.
    # Those entries are kept as they are rather than replaced by detector output.
    if not path.exists():
        return {}
    shard = json.loads(path.read_text(encoding="utf-8"))
    kept = {}
    for image in shard["images"]:
        for detection in image["detections"]:
            if detection["verified"] or detection["source"] == "manual":
                kept[image["id"]] = image
    return kept


def export_area(db, area, shard_dir: Path = SHARD_DIR) -> list[Path]:
    by_sequence = defaultdict(list)
    for row in area_images(db, area.name):
        if row["detected"]:
            by_sequence[row["sequence"]].append(row)
    # The site looks shards up under the country being explored, so they go in
    # the area's country even if an image near a border geocodes to a neighbour.
    folder = shard_dir / area.country
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for sequence, rows in sorted(by_sequence.items()):
        path = folder / f"{sequence}.json"
        kept = hand_checked_images(path)
        images = []
        for row in rows:
            image = kept.pop(row["id"], None)
            if image is None:
                image = shard_image(row, image_detections(db, row["id"]))
            images.append(image)
        images.extend(kept.values())
        shard = {
            "schema_version": SCHEMA_VERSION,
            "sequence": sequence,
            "images": images,
        }
        write_json(path, shard)
        written.append(path)
    return written
