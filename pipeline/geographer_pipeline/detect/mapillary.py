"""Mapillary's own detections: decoding their outlines into 0-1 polygons."""

import base64

import mapbox_vector_tile

from geographer_pipeline.detect.geometry import Point, polygon_area


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
