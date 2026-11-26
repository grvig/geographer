import numpy as np
from PIL import Image

from geographer_pipeline.match.references import build_candidates


class FakeEmbedder:
    def embed_images(self, images):
        return np.ones((len(images), 2), dtype=np.float32)

    def embed_texts(self, texts):
        return np.full((len(texts), 2), len(texts), dtype=np.float32)


CATEGORIES = [
    {"id": "bollard", "negatives": ["a fence post", "a tree trunk"]},
    {"id": "kilometre-marker", "negatives": ["a rock"]},
]


def clue(clue_id, category, files=()):
    return {
        "id": clue_id,
        "category": category,
        "visual": {"description": f"looks like {clue_id}"},
        "references": [{"file": file} for file in files],
    }


def test_every_category_offers_none_of_these_and_its_clues(tmp_path):
    (tmp_path / "refs" / "fr-bollard").mkdir(parents=True)
    for name in ["01.jpg", "02.jpg"]:
        Image.new("RGB", (8, 8)).save(tmp_path / "refs" / "fr-bollard" / name)
    clues = [
        clue("in-bollard", "bollard"),
        clue("fr-bollard", "bollard", ["fr-bollard/01.jpg", "fr-bollard/02.jpg"]),
    ]
    candidates = build_candidates(CATEGORIES, clues, FakeEmbedder(), tmp_path)
    bollard = candidates["bollard"]
    assert [c.clue for c in bollard] == [None, "fr-bollard", "in-bollard"]
    assert bollard[0].texts.shape == (2, 2)
    assert bollard[1].references.shape == (2, 2)
    assert bollard[2].references.size == 0
    assert [c.clue for c in candidates["kilometre-marker"]] == [None]
