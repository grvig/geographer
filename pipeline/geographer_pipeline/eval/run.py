"""Leave-one-out evaluation over the clues' reference photos.

Each reference photo in turn is taken out of its clue and matched as if it were
a new detection. Until curation gives us labelled detections, this is the one
honest measure of the matcher: it never sees the photo it is tested on.
"""

from collections import Counter
from dataclasses import dataclass, replace

import numpy as np

from geographer_pipeline.match.score import candidate_scores, decide


@dataclass
class Result:
    category: str
    truth: str
    # None when the matcher abstained.
    predicted: str | None
    confidence: float


def leave_one_out(candidates: dict, settings) -> list[Result]:
    results = []
    for category, options in sorted(candidates.items()):
        for index, candidate in enumerate(options):
            for row in range(len(candidate.references)):
                vector = candidate.references[row]
                kept = np.delete(candidate.references, row, axis=0)
                held_out = list(options)
                held_out[index] = replace(candidate, references=kept)
                scores = candidate_scores(vector, held_out, settings)
                match = decide(held_out, scores, settings)
                results.append(
                    Result(category, candidate.clue, match.clue, match.confidence)
                )
    return results


def report(results: list[Result]) -> str:
    if not results:
        return "No reference photos to evaluate yet."
    lines = ["category          tested  right  wrong  abstained"]
    for category in sorted({result.category for result in results}):
        mine = [result for result in results if result.category == category]
        right = sum(1 for result in mine if result.predicted == result.truth)
        abstained = sum(1 for result in mine if result.predicted is None)
        wrong = len(mine) - right - abstained
        lines.append(
            f"{category:<17} {len(mine):>6} {right:>6} {wrong:>6} {abstained:>10}"
        )
    confused = Counter(
        (result.truth, result.predicted)
        for result in results
        if result.predicted not in (None, result.truth)
    )
    if confused:
        lines.append("")
        lines.append("Most confused (truth -> predicted):")
        for (truth, predicted), count in confused.most_common(5):
            lines.append(f"  {truth} -> {predicted}: {count}")
    return "\n".join(lines)
