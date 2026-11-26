"""Local cache in data/cache.sqlite, so every stage can resume where it stopped."""

import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CACHE_FILE = DATA_DIR / "cache.sqlite"

# Each entry moves the cache up one version. Never edit an entry once a cache
# has been built with it; add a new one instead.
MIGRATIONS = [
    """
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
""",
    """
-- One vector per detection crop and model.
CREATE TABLE embeddings (
    image_id TEXT NOT NULL,
    detection_id TEXT NOT NULL,
    model TEXT NOT NULL,
    vector BLOB NOT NULL,
    PRIMARY KEY (image_id, detection_id, model),
    FOREIGN KEY (image_id, detection_id)
        REFERENCES detections (image_id, id) ON DELETE CASCADE
);

-- clue is NULL when the matcher abstained. alternatives is JSON
-- [{"clue", "confidence"}]. consistent is NULL when there is no clue.
CREATE TABLE matches (
    image_id TEXT NOT NULL,
    detection_id TEXT NOT NULL,
    clue TEXT,
    confidence REAL NOT NULL,
    alternatives TEXT NOT NULL,
    consistent INTEGER,
    PRIMARY KEY (image_id, detection_id),
    FOREIGN KEY (image_id, detection_id)
        REFERENCES detections (image_id, id) ON DELETE CASCADE
);
""",
]
SCHEMA_VERSION = len(MIGRATIONS)


class CacheError(Exception):
    pass


def connect(path: Path = CACHE_FILE) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        db.close()
        raise CacheError(
            f"{path} uses cache schema {version}, newer than this code's "
            f"{SCHEMA_VERSION}. Update the code or delete the file to rebuild it."
        )
    for number, script in enumerate(MIGRATIONS[version:], version + 1):
        db.executescript(script)
        db.execute(f"PRAGMA user_version = {number}")
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


def save_detections(db: sqlite3.Connection, image_id: str, detections: list) -> None:
    # detections: (id, Detection) pairs. Replaces whatever the image had before.
    rows = [
        (image_id, detection_id, d.category, d.source, json.dumps(d.shape()), d.score)
        for detection_id, d in detections
    ]
    with db:
        db.execute("DELETE FROM detections WHERE image_id = ?", (image_id,))
        db.executemany("INSERT INTO detections VALUES (?, ?, ?, ?, ?, ?)", rows)
        db.execute("UPDATE images SET detected = 1 WHERE id = ?", (image_id,))


def image_detections(db: sqlite3.Connection, image_id: str) -> list[sqlite3.Row]:
    # Insertion order keeps d2 before d10.
    return db.execute(
        "SELECT * FROM detections WHERE image_id = ? ORDER BY rowid", (image_id,)
    ).fetchall()


def images_with_detections(db: sqlite3.Connection, area: str) -> list[str]:
    rows = db.execute(
        "SELECT DISTINCT image_id FROM detections"
        " JOIN images ON images.id = detections.image_id WHERE images.area = ?",
        (area,),
    )
    return [row["image_id"] for row in rows]
