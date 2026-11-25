"""Crops of detected objects, saved to data/crops/<image id>/<detection id>.jpg."""

from pathlib import Path

from geographer_pipeline.cache import DATA_DIR
from geographer_pipeline.detect.geometry import Box

CROPS_DIR = DATA_DIR / "crops"
# A little context around the object helps matching (the top of a bollard,
# the ground under a marker), so crops grow by this share of the box on each side.
PADDING = 0.15


def crop_box(box: Box, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    pad_x = (x1 - x0) * PADDING
    pad_y = (y1 - y0) * PADDING
    return (
        max(0, round((x0 - pad_x) * width)),
        max(0, round((y0 - pad_y) * height)),
        min(width, round((x1 + pad_x) * width)),
        min(height, round((y1 + pad_y) * height)),
    )


def crop_path(image_id: str, detection_id: str, crops_dir: Path = CROPS_DIR) -> Path:
    return crops_dir / image_id / f"{detection_id}.jpg"


def save_crop(image, box: Box, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.crop(crop_box(box, image.width, image.height)).save(path, quality=92)
