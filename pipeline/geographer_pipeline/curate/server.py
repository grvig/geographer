"""The local curation server: a small JSON API behind the site's dev-only
/curate page. It is never deployed; the curate command binds it to 127.0.0.1.
"""

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from geographer_pipeline.areas import AREAS_FILE, load_analysis_areas
from geographer_pipeline.cache import CACHE_FILE
from geographer_pipeline.content.validate import CONTENT_DIR
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

    return app
