"""Image metadata from the Graph API, fetched in batches."""

from dataclasses import dataclass

from geographer_pipeline.cache import missing_image_ids, save_images

FIELDS = [
    "id",
    "sequence",
    "computed_geometry",
    "geometry",
    "is_pano",
    "captured_at",
    "creator",
    "width",
    "height",
    "thumb_2048_url",
]
# Ids per /images request; the URL stays well under length limits.
BATCH_SIZE = 50


@dataclass(frozen=True)
class ImageMeta:
    id: str
    sequence: str
    lon: float
    lat: float
    is_pano: bool
    captured_at: int
    creator: str
    width: int
    height: int
    thumb_url: str


def parse_image(data: dict) -> ImageMeta:
    # The computed position is corrected by Mapillary's reconstruction; the raw
    # GPS position is the fallback for images that were never reconstructed.
    geometry = data.get("computed_geometry") or data["geometry"]
    lon, lat = geometry["coordinates"]
    creator = data.get("creator") or {}
    return ImageMeta(
        id=str(data["id"]),
        sequence=data["sequence"],
        lon=lon,
        lat=lat,
        is_pano=bool(data.get("is_pano")),
        captured_at=int(data.get("captured_at", 0)),
        creator=creator.get("username", ""),
        width=int(data["width"]),
        height=int(data["height"]),
        thumb_url=data["thumb_2048_url"],
    )


def fetch_images(client, ids: list[str]) -> list[ImageMeta]:
    images = []
    for start in range(0, len(ids), BATCH_SIZE):
        batch = ids[start : start + BATCH_SIZE]
        response = client.graph("images", FIELDS, image_ids=",".join(batch))
        for data in response["data"]:
            images.append(parse_image(data))
    return images


def cache_images(client, db, ids: list[str], area: str) -> int:
    # Only ids the cache hasn't seen are fetched, so a rerun costs nothing.
    missing = missing_image_ids(db, ids)
    if missing:
        save_images(db, fetch_images(client, missing), area)
    return len(missing)
