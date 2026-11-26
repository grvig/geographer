"""Start-point indexes for the site: index/<CC>.json plus index/countries.json."""

import json
import random
import time
from pathlib import Path

from geographer_pipeline.areas import Country
from geographer_pipeline.mapillary.tiles import (
    ZOOM,
    decode_image_points,
    tiles_for_bbox,
)

# Must match INDEX_SCHEMA_VERSION in web/src/data/indexSchema.ts.
SCHEMA_VERSION = 1
INDEX_DIR = Path(__file__).resolve().parents[3] / "web" / "public" / "data" / "index"


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


def write_json(path: Path, data: dict, attempts: int = 4, sleep=time.sleep) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    # A synced folder (OneDrive) can hold a file for a moment while it uploads,
    # and Windows then refuses the write. Waiting briefly is enough.
    for attempt in range(attempts):
        try:
            # Plain \n on every OS, so regenerated files don't differ by platform.
            path.write_text(text + "\n", encoding="utf-8", newline="\n")
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            sleep(0.5 * (attempt + 1))


def write_index(country: Country, ids: list[str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{country.code}.json"
    # Resampling start points must not forget which images were analysed.
    analysed = []
    if path.exists():
        analysed = json.loads(path.read_text(encoding="utf-8")).get("analysed", [])
    index = {
        "schema_version": SCHEMA_VERSION,
        "country": country.code,
        "name": country.name,
        "bbox": country.bbox,
        "images": ids,
        "analysed": analysed,
    }
    write_json(path, index)
    # Replace this country's entry in place and keep the others.
    list_path = out_dir / "countries.json"
    entries = {}
    if list_path.exists():
        for entry in json.loads(list_path.read_text(encoding="utf-8"))["countries"]:
            entries[entry["code"]] = entry
    entries[country.code] = {
        "code": country.code,
        "name": country.name,
        "image_count": len(ids),
    }
    countries = list(entries.values())
    write_json(list_path, {"schema_version": SCHEMA_VERSION, "countries": countries})


def build_indexes(client, countries, out_dir, tiles_per_area, limit, seed) -> int:
    rng = random.Random(seed)
    failed = 0
    for country in countries:
        ids = sample_image_ids(client, country, tiles_per_area, limit, rng)
        if not ids:
            print(f"{country.code}: no images found, index not written")
            failed += 1
            continue
        write_index(country, ids, out_dir)
        print(f"{country.code}: {len(ids)} start points")
    return failed


def add_analysed(code: str, ids: list[str], out_dir: Path = INDEX_DIR) -> int:
    path = out_dir / f"{code}.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    analysed = sorted(set(index.get("analysed", [])) | set(ids), key=int)
    index["analysed"] = analysed
    write_json(path, index)
    return len(analysed)
