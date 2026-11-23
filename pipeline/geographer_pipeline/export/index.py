"""Start-point indexes for the site: index/<CC>.json plus index/countries.json."""

import random

from geographer_pipeline.areas import Country
from geographer_pipeline.mapillary.tiles import (
    ZOOM,
    decode_image_points,
    tiles_for_bbox,
)


def sample_image_ids(
    client, country: Country, tiles_per_area: int, limit: int, rng: random.Random
) -> list[str]:
    # Each area gets an equal share, so one dense city can't fill the whole index.
    share = max(1, limit // len(country.areas))
    chosen = []
    for area in country.areas:
        west, south, east, north = area.bbox
        tiles = tiles_for_bbox(area.bbox)
        ids = set()
        for x, y in rng.sample(tiles, min(tiles_per_area, len(tiles))):
            for point in decode_image_points(client.tile(ZOOM, x, y), ZOOM, x, y):
                if west <= point.lon <= east and south <= point.lat <= north:
                    ids.add(point.id)
        candidates = sorted(ids, key=int)
        chosen.extend(rng.sample(candidates, min(share, len(candidates))))
    return sorted(chosen, key=int)
