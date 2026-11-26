"""Embeds every detection crop of an area that doesn't have a vector yet."""

from pathlib import Path

from PIL import Image

from geographer_pipeline.cache import save_embeddings, unembedded_detections
from geographer_pipeline.detect.crop import CROPS_DIR, crop_path

# Crops opened at once; keeps memory flat on large areas.
CHUNK = 128


def embed_area(db, area: str, embedder, crops_dir: Path = CROPS_DIR) -> int:
    rows = unembedded_detections(db, area, embedder.name)
    for start in range(0, len(rows), CHUNK):
        keys = [(row["image_id"], row["id"]) for row in rows[start : start + CHUNK]]
        images = [Image.open(crop_path(*key, crops_dir)) for key in keys]
        save_embeddings(db, keys, embedder.name, embedder.embed_images(images))
    return len(rows)
