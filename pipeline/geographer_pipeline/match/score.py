"""Scores a detection's embedding against its category's candidates, and decides
which clue it is, if any."""

from dataclasses import dataclass

import numpy as np

# Clues less likely than this aren't worth listing as alternatives.
MIN_ALTERNATIVE = 0.05


@dataclass
class Match:
    # None when the matcher abstains: the object is shown as unknown.
    clue: str | None
    # How likely the best clue is, whether or not it was accepted.
    confidence: float
    # Other clues worth mentioning, most likely first.
    alternatives: list[tuple[str, float]]


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


def softmax(scores: np.ndarray, temperature: float) -> np.ndarray:
    weights = np.exp((scores - scores.max()) / temperature)
    return weights / weights.sum()


def decide(candidates: list, scores: np.ndarray, settings) -> Match:
    probabilities = softmax(scores, settings.temperature)
    order = list(np.argsort(-probabilities))
    ranked = [(candidates[i].clue, float(probabilities[i])) for i in order]
    clues = [(clue, p) for clue, p in ranked if clue is not None]
    if not clues:
        return Match(None, 0.0, [])
    best, best_p = clues[0]
    runner_up = ranked[1][1]
    if ranked[0][0] != best:
        runner_up = ranked[0][1]
    # Abstain when "none of these" wins, when the best clue is unsure, or when
    # something else comes too close: a confident wrong answer is worse.
    accepted = best_p >= settings.threshold and best_p - runner_up >= settings.margin
    others = clues[1:]
    clue = best
    if not accepted:
        clue = None
        others = clues
    alternatives = [(c, round(p, 2)) for c, p in others[:3] if p >= MIN_ALTERNATIVE]
    return Match(clue, round(best_p, 2), alternatives)
