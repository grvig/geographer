"""Scores a detection's embedding against its category's candidates."""

import numpy as np


def candidate_scores(vector: np.ndarray, candidates: list, settings) -> np.ndarray:
    # score = weight * visual + (1 - weight) * text, all cosine similarities of
    # unit vectors. Without reference photos, visual falls back to what an
    # unrelated object scores, so such a clue has only its description to go on.
    scores = []
    for candidate in candidates:
        visual = settings.none_visual
        if candidate.references.size:
            visual = float((candidate.references @ vector).max())
        text = float((candidate.texts @ vector).max())
        scores.append(settings.weight * visual + (1 - settings.weight) * text)
    return np.array(scores)
