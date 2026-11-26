"""The match stage for one area: embed new crops, then match every detection."""

import json
from pathlib import Path

from geographer_pipeline.cache import area_embeddings, save_matches
from geographer_pipeline.detect.crop import CROPS_DIR
from geographer_pipeline.match.embed import embed_area
from geographer_pipeline.match.location import is_consistent
from geographer_pipeline.match.score import candidate_scores, decide


def match_area(
    db,
    area: str,
    embedder,
    candidates: dict,
    clues: dict,
    settings,
    crops_dir: Path = CROPS_DIR,
) -> tuple[int, int]:
    embed_area(db, area, embedder, crops_dir)
    vectors = area_embeddings(db, area, embedder.name)
    detections = db.execute(
        "SELECT d.image_id, d.id, d.category, i.country, i.admin1 FROM detections d"
        " JOIN images i ON i.id = d.image_id WHERE i.area = ?",
        (area,),
    ).fetchall()
    rows = []
    for row in detections:
        options = candidates.get(row["category"])
        if options is None:
            # The category was removed from the content since detection ran.
            continue
        vector = vectors[(row["image_id"], row["id"])]
        match = decide(options, candidate_scores(vector, options, settings), settings)
        # The location only labels the match; it never changes it.
        consistent = None
        if match.clue:
            clue = clues[match.clue]
            consistent = is_consistent(clue, row["country"], row["admin1"])
        alternatives = [{"clue": c, "confidence": p} for c, p in match.alternatives]
        rows.append(
            (
                row["image_id"],
                row["id"],
                match.clue,
                match.confidence,
                json.dumps(alternatives),
                consistent,
            )
        )
    save_matches(db, area, rows)
    matched = sum(1 for row in rows if row[2])
    return len(rows), matched
