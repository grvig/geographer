"""Mapillary's own detections, decoded into 0-1 outlines and mapped to categories."""

import base64

import mapbox_vector_tile

from geographer_pipeline.detect.geometry import (
    Detection,
    Point,
    polygon_area,
    polygon_box,
)


def decode_outline(geometry: str) -> list[Point]:
    # Each detection is a base64 vector tile whose extent spans the whole image.
    # Verified visually: with y pointing down the outlines sit exactly on the objects.
    tile = mapbox_vector_tile.decode(
        base64.b64decode(geometry), default_options={"y_coord_down": True}
    )
    rings = []
    for layer in tile.values():
        extent = layer["extent"]
        for feature in layer["features"]:
            shape = feature["geometry"]
            polygons = []
            if shape["type"] == "Polygon":
                polygons = [shape["coordinates"]]
            elif shape["type"] == "MultiPolygon":
                polygons = shape["coordinates"]
            for polygon in polygons:
                # The first ring is the outside; the rest are holes.
                ring = [(x / extent, y / extent) for x, y in polygon[0]]
                rings.append(ring)
    if not rings:
        return []
    # An object split by something in front of it comes as several pieces;
    # the largest piece is the one worth outlining.
    return max(rings, key=polygon_area)


def class_map(categories: list[dict]) -> dict[str, str]:
    # Mapillary class value, e.g. "object--street-light", to our category id.
    mapping = {}
    for category in categories:
        for value in category["detector"].get("mapillary", []):
            mapping[value] = category["id"]
    return mapping


def fetch_mapillary_detections(
    client, image_id: str, classes: dict[str, str]
) -> list[Detection]:
    response = client.graph(f"{image_id}/detections", ["value", "geometry"])
    detections = []
    for item in response["data"]:
        # Most values (sky, road, cars, ...) aren't clues and are skipped here.
        category = classes.get(item["value"])
        if category is None:
            continue
        outline = decode_outline(item["geometry"])
        if len(outline) < 3:
            continue
        # Mapillary gives no score; its detections count as certain.
        box = polygon_box(outline)
        detections.append(Detection(category, "mapillary", box, 1.0, outline))
    return detections
