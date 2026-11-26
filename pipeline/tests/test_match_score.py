import numpy as np
import pytest

from geographer_pipeline.match.references import Candidate
from geographer_pipeline.match.score import candidate_scores, decide, softmax
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


def three(*clues):
    return [Candidate(clue, NONE, NONE) for clue in clues]


def test_softmax_sharpens_with_a_low_temperature():
    probabilities = softmax(np.array([0.70, 0.75]), 0.02)
    assert probabilities.sum() == pytest.approx(1)
    assert probabilities[1] > 0.9


def test_accepts_a_clear_winner_and_lists_alternatives():
    match = decide(three(None, "a", "b"), np.array([0.60, 0.75, 0.70]), SETTINGS)
    assert match.clue == "a"
    assert match.confidence == pytest.approx(0.92, abs=0.01)
    assert [c for c, _ in match.alternatives] == ["b"]


def test_abstains_when_none_of_these_wins():
    match = decide(three(None, "a", "b"), np.array([0.75, 0.70, 0.60]), SETTINGS)
    assert match.clue is None
    # The closest clue is still reported, for a "closest guess".
    assert match.alternatives[0][0] == "a"
    assert match.confidence < 0.1


def test_abstains_when_two_clues_are_too_close():
    match = decide(three(None, "a", "b"), np.array([0.5, 0.75, 0.749]), SETTINGS)
    assert match.clue is None
    assert [c for c, _ in match.alternatives] == ["a", "b"]


def test_a_category_without_clues_is_always_unknown():
    assert decide(three(None), np.array([0.7]), SETTINGS).clue is None
