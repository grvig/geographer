"""Downloads 2048 px thumbnails to data/raw/, skipping files already there."""

from pathlib import Path

from geographer_pipeline.cache import DATA_DIR
from geographer_pipeline.mapillary.client import MapillaryError
from geographer_pipeline.mapillary.images import fetch_images

RAW_DIR = DATA_DIR / "raw"
JPEG_START = b"\xff\xd8"


def raw_path(image_id: str, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"{image_id}.jpg"


def download_images(client, ids: list[str], raw_dir: Path = RAW_DIR) -> int:
    pending = [image_id for image_id in ids if not raw_path(image_id, raw_dir).exists()]
    if not pending:
        return 0
    raw_dir.mkdir(parents=True, exist_ok=True)
    # Thumbnail links are signed and expire, so fetch fresh ones right before use.
    for image in fetch_images(client, pending):
        data = client.download(image.thumb_url)
        if not data.startswith(JPEG_START):
            raise MapillaryError(f"Image {image.id} did not download as a JPEG")
        # Write then rename, so an interrupted run never leaves half a file behind.
        path = raw_path(image.id, raw_dir)
        partial = path.with_suffix(".part")
        partial.write_bytes(data)
        partial.replace(path)
    return len(pending)
