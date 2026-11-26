"""The candidates a detection is matched against: every clue of its category,
from every country, plus "none of these"."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from geographer_pipeline.content.validate import CONTENT_DIR


@dataclass
class Candidate:
    # None stands for "none of these".
    clue: str | None
    # Reference photo vectors, one row each; empty when the clue has none yet.
    references: np.ndarray
    # Description vectors: one for a clue, one per negative for "none of these".
    texts: np.ndarray


def build_candidates(
    categories: list[dict],
    clues: list[dict],
    embedder,
    content_dir: Path = CONTENT_DIR,
) -> dict[str, list[Candidate]]:
    nothing = np.zeros((0, 0), dtype=np.float32)
    candidates = {}
    for category in categories:
        negatives = embedder.embed_texts(category["negatives"])
        candidates[category["id"]] = [Candidate(None, nothing, negatives)]
    for clue in sorted(clues, key=lambda clue: clue["id"]):
        files = [
            content_dir / "refs" / ref["file"] for ref in clue.get("references", [])
        ]
        references = nothing
        if files:
            references = embedder.embed_images([Image.open(file) for file in files])
        texts = embedder.embed_texts([clue["visual"]["description"]])
        candidates[clue["category"]].append(Candidate(clue["id"], references, texts))
    return candidates
