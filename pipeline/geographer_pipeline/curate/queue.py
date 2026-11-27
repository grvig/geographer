"""The review queue: detections nobody has labelled yet, least sure first."""

import json

from geographer_pipeline.export.shards import shape_box


def review_queue(
    db, area: str, labels: dict, categories: set[str], limit: int
) -> tuple[int, list[dict]]:
    rows = db.execute(
        "SELECT d.image_id, d.id, d.category, d.source, d.shape, d.score,"
        " m.clue, m.confidence, m.alternatives"
        " FROM detections d JOIN images i ON i.id = d.image_id"
        " LEFT JOIN matches m ON m.image_id = d.image_id AND m.detection_id = d.id"
        " WHERE i.area = ?",
        (area,),
    ).fetchall()
    items = []
    for row in rows:
        if (row["image_id"], row["id"]) in labels or row["category"] not in categories:
            continue
        confidence = row["score"]
        alternatives = []
        if row["confidence"] is not None:
            confidence = row["confidence"]
            alternatives = json.loads(row["alternatives"])
        box = shape_box(json.loads(row["shape"]))
        items.append(
            {
                "image_id": row["image_id"],
                "detection_id": row["id"],
                "category": row["category"],
                "source": row["source"],
                "box": [round(value, 4) for value in box],
                "clue": row["clue"],
                "confidence": confidence,
                "alternatives": alternatives,
                "crop": f"/api/crops/{row['image_id']}/{row['id']}.jpg",
            }
        )
    # The answers most likely to be wrong are the most useful to check.
    items.sort(
        key=lambda item: (item["confidence"], item["image_id"], item["detection_id"])
    )
    return len(items), items[:limit]
