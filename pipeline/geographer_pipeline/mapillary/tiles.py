"""Mapillary coverage tiles: which tiles cover an area, and the images in one."""

import math
from dataclasses import dataclass

import mapbox_vector_tile

# The per-image layer only exists at this zoom level.
ZOOM = 14


@dataclass(frozen=True)
class ImagePoint:
    id: str
    lon: float
    lat: float
    is_pano: bool
    captured_at: int


def tile_xy(lon: float, lat: float, zoom: int = ZOOM) -> tuple[int, int]:
    n = 2**zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def tiles_for_bbox(bbox: list[float], zoom: int = ZOOM) -> list[tuple[int, int]]:
    west, south, east, north = bbox
    x0, y0 = tile_xy(west, north, zoom)
    x1, y1 = tile_xy(east, south, zoom)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def tile_to_lonlat(
    z: int, x: int, y: int, px: float, py: float, extent: int
) -> tuple[float, float]:
    n = 2**z
    lon = (x + px / extent) / n * 360 - 180
    mercator_y = math.pi * (1 - 2 * (y + py / extent) / n)
    lat = math.degrees(math.atan(math.sinh(mercator_y)))
    return lon, lat


def decode_image_points(data: bytes, z: int, x: int, y: int) -> list[ImagePoint]:
    # The library flips y by default; Mapillary tiles have their origin top-left.
    layers = mapbox_vector_tile.decode(data, default_options={"y_coord_down": True})
    layer = layers.get("image")
    if layer is None:
        return []
    points = []
    for feature in layer["features"]:
        px, py = feature["geometry"]["coordinates"]
        lon, lat = tile_to_lonlat(z, x, y, px, py, layer["extent"])
        properties = feature["properties"]
        point = ImagePoint(
            id=str(properties["id"]),
            lon=lon,
            lat=lat,
            is_pano=bool(properties.get("is_pano")),
            captured_at=int(properties.get("captured_at", 0)),
        )
        points.append(point)
    return points
