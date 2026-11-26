import numpy as np
import pytest

from geographer_pipeline.match.references import Candidate
from geographer_pipeline.match.score import candidate_scores
from geographer_pipeline.match.settings import Settings

SETTINGS = Settings("m", "p", 0.75, 0.02, 0.7, 0.5, 0.1)
NONE = np.zeros((0, 0), dtype=np.float32)


def unit(*values):
    vector = np.array(values, dtype=np.float32)
    return vector / np.linalg.norm(vector)


def test_combines_best_reference_and_description():
    crop = unit(1, 0)
    candidates = [
        Candidate(None, NONE, np.stack([unit(0, 1), unit(1, 1)])),
        Candidate(
            "fr-bollard", np.stack([unit(0, 1), unit(1, 0)]), np.stack([unit(0, 1)])
        ),
        Candidate("in-bollard", NONE, np.stack([unit(1, 0)])),
    ]
    scores = candidate_scores(crop, candidates, SETTINGS)
    # none: 0.75 * 0.7 + 0.25 * cos45; fr: best reference matches exactly, text 0;
    # in: no references, so the floor, with a perfect description.
    assert scores == pytest.approx(
        [0.75 * 0.7 + 0.25 * 2**-0.5, 0.75, 0.75 * 0.7 + 0.25]
    )
