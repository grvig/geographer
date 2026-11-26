import numpy as np

from geographer_pipeline.eval.run import Result, leave_one_out, report
from geographer_pipeline.match.references import Candidate
from geographer_pipeline.match.settings import Settings

# Visual only, so the test doesn't depend on descriptions.
SETTINGS = Settings("m", "p", 1.0, 0.02, 0.5, 0.5, 0.1)
NONE = np.zeros((0, 0), dtype=np.float32)
TEXT = np.zeros((1, 2), dtype=np.float32)


def unit(angle):
    return np.array([np.cos(angle), np.sin(angle)], dtype=np.float32)


def test_each_reference_is_matched_without_itself():
    # Two clues whose photos point in clearly different directions. A clue with
    # a single photo has nothing left once that photo is held out.
    candidates = {
        "bollard": [
            Candidate(None, NONE, TEXT),
            Candidate("fr-bollard", np.stack([unit(0), unit(0.05)]), TEXT),
            Candidate("in-bollard", np.stack([unit(1.5)]), TEXT),
        ]
    }
    results = leave_one_out(candidates, SETTINGS)
    assert [(r.truth, r.predicted) for r in results] == [
        ("fr-bollard", "fr-bollard"),
        ("fr-bollard", "fr-bollard"),
        ("in-bollard", None),
    ]


def test_report_counts_right_wrong_and_abstained():
    results = [
        Result("bollard", "fr-a", "fr-a", 0.9),
        Result("bollard", "fr-a", "in-b", 0.7),
        Result("bollard", "in-b", None, 0.3),
    ]
    text = report(results)
    assert "bollard                3      1      1          1" in text
    assert "fr-a -> in-b: 1" in text
    assert report([]) == "No reference photos to evaluate yet."
