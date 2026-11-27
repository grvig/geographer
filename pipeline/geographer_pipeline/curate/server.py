"""The local curation server: a small JSON API behind the site's dev-only
/curate page. It is never deployed; the curate command binds it to 127.0.0.1.
"""

import json
import re
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from geographer_pipeline.areas import AREAS_FILE, load_analysis_areas
from geographer_pipeline.cache import CACHE_FILE, connect
from geographer_pipeline.content.refs import add_reference
from geographer_pipeline.content.validate import CONTENT_DIR, load_clues
from geographer_pipeline.curate.labels import append_label, load_labels
from geographer_pipeline.curate.queue import review_queue
from geographer_pipeline.detect.crop import CROPS_DIR, crop_path
from geographer_pipeline.export.shards import shape_box


@dataclass(frozen=True)
class Paths:
    cache: Path = CACHE_FILE
    content: Path = CONTENT_DIR
    crops: Path = CROPS_DIR
    areas: Path = AREAS_FILE


class ReferenceRequest(BaseModel):
    area: str
    image_id: str
    detection_id: str
    clue: str


class LabelRequest(BaseModel):
    area: str
    image_id: str
    detection_id: str
    action: Literal["accept", "relabel", "reject", "unknown"]
    clue: str | None = None


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

    @app.get("/api/crops/{image_id}/{detection_id}.jpg")
    def crop(image_id: str, detection_id: str) -> FileResponse:
        # Plain ids only, so no request can reach outside the crops folder.
        plain = re.fullmatch(r"\d+", image_id) and re.fullmatch(r"d\d+", detection_id)
        path = crop_path(image_id, detection_id, paths.crops)
        if not plain or not path.is_file():
            raise HTTPException(404, "No such crop")
        return FileResponse(path, media_type="image/jpeg")

    def find_detection(area: str, image_id: str, detection_id: str):
        with closing(connect(paths.cache)) as db:
            row = db.execute(
                "SELECT d.category, d.shape, m.clue FROM detections d"
                " JOIN images i ON i.id = d.image_id"
                " LEFT JOIN matches m"
                " ON m.image_id = d.image_id AND m.detection_id = d.id"
                " WHERE i.area = ? AND d.image_id = ? AND d.id = ?",
                (area, image_id, detection_id),
            ).fetchone()
        if row is None:
            raise HTTPException(404, "No such detection in this area")
        return row

    def check_clue(clue_id: str | None, category: str) -> None:
        same = [clue for clue in clue_library() if clue["category"] == category]
        if clue_id not in {clue["id"] for clue in same}:
            raise HTTPException(400, f"{clue_id} is not a {category} clue")

    @app.post("/api/labels")
    def add_label(request: LabelRequest) -> dict:
        row = find_detection(request.area, request.image_id, request.detection_id)
        if request.action == "accept" and row["clue"] is None:
            raise HTTPException(400, "There is no match to accept; relabel it instead")
        if request.action == "relabel":
            check_clue(request.clue, row["category"])
        entry = {
            "image_id": request.image_id,
            "detection_id": request.detection_id,
            # Stored so the label can tell if detection is rerun and renumbered.
            "box": [round(value, 4) for value in shape_box(json.loads(row["shape"]))],
            "action": request.action,
        }
        if request.action == "relabel":
            entry["clue"] = request.clue
        return append_label(request.area, entry, paths.content / "labels")

    @app.post("/api/references")
    def use_as_reference(request: ReferenceRequest) -> dict:
        row = find_detection(request.area, request.image_id, request.detection_id)
        check_clue(request.clue, row["category"])
        with closing(connect(paths.cache)) as db:
            try:
                file = add_reference(
                    db,
                    request.clue,
                    request.image_id,
                    request.detection_id,
                    paths.content,
                    paths.crops,
                )
            except ValueError as error:
                raise HTTPException(409, str(error)) from error
        # A reference photo of a clue is, by definition, that clue.
        action = "relabel"
        if row["clue"] == request.clue:
            action = "accept"
        fields = request.model_dump()
        if action == "accept":
            fields.pop("clue")
        add_label(LabelRequest(**fields, action=action))
        return {"file": file}

    @app.get("/api/clues")
    def clues() -> list[dict]:
        # Just enough for the relabel picker.
        return [
            {"id": clue["id"], "category": clue["category"], "title": clue["title"]}
            for clue in sorted(clue_library(), key=lambda clue: clue["id"])
        ]

    return app
