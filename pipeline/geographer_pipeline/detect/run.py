"""The detect stage for one analysis area: pick images, fetch them, detect, crop.

Every step skips work already in the cache, so an interrupted run picks up
where it stopped.
"""

import random
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image

from geographer_pipeline.cache import area_images, save_detections
from geographer_pipeline.detect.crop import CROPS_DIR, crop_path, save_crop
from geographer_pipeline.detect.mapillary import fetch_mapillary_detections
from geographer_pipeline.detect.merge import merge_detections
from geographer_pipeline.geocode import geocode_images
from geographer_pipeline.mapillary.download import RAW_DIR, download_images, raw_path
from geographer_pipeline.mapillary.images import cache_images
from geographer_pipeline.mapillary.tiles import (
    ZOOM,
    decode_image_points,
    tiles_for_bbox,
)

# Consecutive images taken from each sequence.
RUN_LENGTH = 40


def pick_images(points, area, seed: int = 0) -> list[str]:
    # Runs of consecutive images rather than a scatter, so walking along a road
    # in the viewer keeps finding analysed images. Panoramas are left out for
    # now: crops from them are distorted.
    west, south, east, north = area.bbox
    by_sequence = defaultdict(list)
    for point in points:
        inside = west <= point.lon <= east and south <= point.lat <= north
        if inside and not point.is_pano:
            by_sequence[point.sequence].append(point)
    sequences = sorted(by_sequence)
    random.Random(seed).shuffle(sequences)
    chosen = []
    for sequence in sequences:
        run = sorted(by_sequence[sequence], key=lambda point: point.captured_at)
        room = area.limit - len(chosen)
        chosen.extend(point.id for point in run[: min(RUN_LENGTH, room)])
        if len(chosen) >= area.limit:
            break
    return chosen


def detect_area(
    client,
    db,
    area,
    owl,
    classes: dict[str, str],
    raw_dir: Path = RAW_DIR,
    crops_dir: Path = CROPS_DIR,
    redo: bool = False,
) -> int:
    points = []
    for x, y in tiles_for_bbox(area.bbox):
        points.extend(decode_image_points(client.tile(ZOOM, x, y), ZOOM, x, y))
    ids = pick_images(points, area)
    print(f"{area.name}: {len(points)} images in the area, {len(ids)} picked")
    cache_images(client, db, ids, area.name)
    download_images(client, ids, raw_dir)
    geocode_images(db, area.name)
    # redo reruns the detectors on everything, e.g. after changing prompts.
    pending = [row for row in area_images(db, area.name) if redo or not row["detected"]]
    for number, row in enumerate(pending, 1):
        image = Image.open(raw_path(row["id"], raw_dir)).convert("RGB")
        mapillary = fetch_mapillary_detections(client, row["id"], classes)
        found = merge_detections(mapillary, owl.detect(image))
        named = [(f"d{index}", detection) for index, detection in enumerate(found, 1)]
        shutil.rmtree(crops_dir / row["id"], ignore_errors=True)
        for detection_id, detection in named:
            save_crop(
                image, detection.box, crop_path(row["id"], detection_id, crops_dir)
            )
        save_detections(db, row["id"], named)
        print(f"  {number}/{len(pending)} {row['id']}: {len(found)} objects")
    return len(pending)
