"""Shards for the site: images/<CC>/<sequence id>.json, one file per sequence."""

import json
from collections import defaultdict
from pathlib import Path

from geographer_pipeline.cache import area_images, image_detections, image_matches
from geographer_pipeline.detect.geometry import iou, polygon_box, simplify
from geographer_pipeline.export.index import write_json
from geographer_pipeline.match.location import is_consistent

# Must match SHARD_SCHEMA_VERSION in web/src/data/shardSchema.ts.
SCHEMA_VERSION = 1
# About 4 px on a 2048 px image: invisible in the viewer, and it shrinks
# Mapillary's outlines several times over.
OUTLINE_TOLERANCE = 0.002
SHARD_DIR = Path(__file__).resolve().parents[3] / "web" / "public" / "data" / "images"


def shard_shape(shape: dict) -> dict:
    if shape["type"] != "polygon":
        return shape
    points = simplify(shape["coords"], OUTLINE_TOLERANCE)
    # The site needs at least a triangle.
    if len(points) < 3:
        return shape
    return {"type": "polygon", "coords": points}


def shape_box(shape: dict) -> tuple:
    if shape["type"] == "rect":
        return tuple(shape["coords"])
    return polygon_box(shape["coords"])


def apply_label(entry: dict, label: dict, row, clues: dict) -> dict | None:
    # A person's verdict overrides the matcher. None means drop the detection.
    if label["action"] == "reject":
        return None
    entry["verified"] = True
    if label["action"] == "unknown":
        entry["clue"] = None
        entry["consistent"] = None
    if label["action"] == "relabel":
        clue = clues.get(label["clue"])
        entry["clue"] = label["clue"]
        entry["confidence"] = 1.0
        entry["alternatives"] = []
        entry["consistent"] = None
        if clue:
            entry["consistent"] = is_consistent(clue, row["country"], row["admin1"])
    return entry


def shard_image(row, detections, matches: dict, labels: dict, clues: dict) -> dict:
    entries = []
    for detection in detections:
        entry = {
            "id": detection["id"],
            "category": detection["category"],
            "source": detection["source"],
            "shape": shard_shape(json.loads(detection["shape"])),
            "clue": None,
            # Until the match stage has run, the detector's own score stands in.
            "confidence": round(detection["score"], 2),
            "alternatives": [],
            "consistent": None,
            "verified": False,
        }
        match = matches.get(detection["id"])
        if match:
            entry["clue"] = match["clue"]
            entry["confidence"] = match["confidence"]
            entry["alternatives"] = json.loads(match["alternatives"])
            if match["consistent"] is not None:
                entry["consistent"] = bool(match["consistent"])
        label = labels.get((row["id"], detection["id"]))
        # A rerun of detection can renumber objects; a label only counts if it
        # still sits on the same object.
        box = shape_box(json.loads(detection["shape"]))
        if label and iou(tuple(label["box"]), box) > 0.5:
            entry = apply_label(entry, label, row, clues)
        if entry:
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


def manual_images(path: Path) -> dict[str, dict]:
    # Images in an existing shard whose detections were drawn by hand. They have
    # no detector output behind them, so they are kept as they are. Everything
    # else is rebuilt from the cache and the labels on every export.
    if not path.exists():
        return {}
    shard = json.loads(path.read_text(encoding="utf-8"))
    kept = {}
    for image in shard["images"]:
        for detection in image["detections"]:
            if detection["source"] == "manual":
                kept[image["id"]] = image
    return kept


def export_area(
    db, area, shard_dir: Path = SHARD_DIR, labels=None, clues=None
) -> list[Path]:
    labels = labels or {}
    clues = clues or {}
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
        kept = manual_images(path)
        images = []
        for row in rows:
            image = kept.pop(row["id"], None)
            if image is None:
                detections = image_detections(db, row["id"])
                matches = image_matches(db, row["id"])
                image = shard_image(row, detections, matches, labels, clues)
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
