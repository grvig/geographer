"""The local curation server: a small JSON API behind the site's dev-only
/curate page. It is never deployed; the curate command binds it to 127.0.0.1.
"""

from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException

from geographer_pipeline.areas import AREAS_FILE, load_analysis_areas
from geographer_pipeline.cache import CACHE_FILE, connect
from geographer_pipeline.content.validate import CONTENT_DIR, load_clues
from geographer_pipeline.curate.labels import load_labels
from geographer_pipeline.curate.queue import review_queue
from geographer_pipeline.detect.crop import CROPS_DIR


@dataclass(frozen=True)
class Paths:
    cache: Path = CACHE_FILE
    content: Path = CONTENT_DIR
    crops: Path = CROPS_DIR
    areas: Path = AREAS_FILE


def create_app(paths: Paths = Paths()) -> FastAPI:
    app = FastAPI(title="Geographer curation", docs_url=None, redoc_url=None)

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/areas")
    def areas() -> list[dict]:
        found = load_analysis_areas(paths.areas).values()
        return [{"name": area.name, "country": area.country} for area in found]

    def clue_library() -> list[dict]:
        clues, errors = load_clues(paths.content)
        if errors:
            raise HTTPException(
                500, "The clue files have problems: run content validate"
            )
        return clues

    @app.get("/api/queue")
    def queue(area: str, limit: int = 50, category: str | None = None) -> dict:
        clues = clue_library()
        # By default only categories with clues: there is nothing to confirm in
        # the others yet, only false detections to reject.
        categories = {clue["category"] for clue in clues}
        if category:
            categories = {category}
        labels = load_labels(area, paths.content / "labels")
        with closing(connect(paths.cache)) as db:
            total, items = review_queue(db, area, labels, categories, limit)
        return {"total": total, "items": items}

    @app.get("/api/clues")
    def clues() -> list[dict]:
        # Just enough for the relabel picker.
        return [
            {"id": clue["id"], "category": clue["category"], "title": clue["title"]}
            for clue in sorted(clue_library(), key=lambda clue: clue["id"])
        ]

    return app
