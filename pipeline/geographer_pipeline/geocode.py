"""Offline country and region (admin1) lookup for image positions."""

import contextlib
import io


def locate(points: list[tuple[float, float]]) -> list[tuple[str, str | None]]:
    # (lat, lon) in, (country code, admin1) out. The answer is the nearest town's
    # region, so it can be wrong right next to a border.
    if not points:
        return []
    import reverse_geocoder

    # Mode 1 is single-process; the default multiprocess mode is unreliable on
    # Windows. The package also prints a loading message, which is dropped.
    with contextlib.redirect_stdout(io.StringIO()):
        results = reverse_geocoder.search(points, mode=1)
    places = []
    for result in results:
        admin1 = result["admin1"] or None
        places.append((result["cc"], admin1))
    return places


def geocode_images(db, area: str) -> int:
    rows = db.execute(
        "SELECT id, lat, lon FROM images WHERE area = ? AND country IS NULL", (area,)
    ).fetchall()
    places = locate([(row["lat"], row["lon"]) for row in rows])
    with db:
        for row, (country, admin1) in zip(rows, places, strict=True):
            db.execute(
                "UPDATE images SET country = ?, admin1 = ? WHERE id = ?",
                (country, admin1, row["id"]),
            )
    return len(rows)
