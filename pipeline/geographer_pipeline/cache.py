"""Local cache in data/cache.sqlite, so every stage can resume where it stopped."""

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CACHE_FILE = DATA_DIR / "cache.sqlite"
SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE images (
    id TEXT PRIMARY KEY,
    area TEXT NOT NULL,
    sequence TEXT NOT NULL,
    lon REAL NOT NULL,
    lat REAL NOT NULL,
    is_pano INTEGER NOT NULL,
    captured_at INTEGER NOT NULL,
    creator TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    thumb_url TEXT NOT NULL,
    country TEXT,
    admin1 TEXT,
    detected INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX images_by_area ON images (area);

-- shape is JSON {"type": "rect" | "polygon", "coords": ...} in 0-1 image coordinates.
CREATE TABLE detections (
    image_id TEXT NOT NULL REFERENCES images (id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT NOT NULL,
    shape TEXT NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY (image_id, id)
);
"""


class CacheError(Exception):
    pass


def connect(path: Path = CACHE_FILE) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        db.executescript(SCHEMA)
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    elif version != SCHEMA_VERSION:
        db.close()
        raise CacheError(
            f"{path} uses cache schema {version}, this code expects "
            f"{SCHEMA_VERSION}. Delete the file to rebuild it."
        )
    return db


def missing_image_ids(db: sqlite3.Connection, ids: list[str]) -> list[str]:
    known = {row["id"] for row in db.execute("SELECT id FROM images")}
    return [image_id for image_id in ids if image_id not in known]


def save_images(db: sqlite3.Connection, images: list, area: str) -> None:
    rows = [
        (
            image.id,
            area,
            image.sequence,
            image.lon,
            image.lat,
            image.is_pano,
            image.captured_at,
            image.creator,
            image.width,
            image.height,
            image.thumb_url,
        )
        for image in images
    ]
    with db:
        db.executemany(
            "INSERT OR IGNORE INTO images (id, area, sequence, lon, lat, is_pano,"
            " captured_at, creator, width, height, thumb_url)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )


def area_images(db: sqlite3.Connection, area: str) -> list[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM images WHERE area = ? ORDER BY sequence, captured_at", (area,)
    ).fetchall()
