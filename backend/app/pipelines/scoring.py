"""Pure scoring functions — no I/O, no external calls. Kept separate from
the orchestration pipeline specifically so they're trivially unit-testable
(brief: "write tests for the core logic, especially parsing/scoring
functions")."""

import math

# A keyword at or above this monthly volume gets full marks on the volume
# component. Log-scaled so 100 vs 1,000 matters more than 10,000 vs 11,000.
_VOLUME_CEILING = 10_000

_WEIGHT_VOLUME = 0.40
_WEIGHT_DIFFICULTY = 0.35
_WEIGHT_RELEVANCE = 0.25


def normalize_volume(volume: int | None) -> float:
    """0-1 score. None/0 volume scores 0 rather than raising — a keyword
    DataForSEO has no data for isn't necessarily worthless, just unscored
    on this axis."""
    if not volume or volume <= 0:
        return 0.0
    return min(1.0, math.log10(volume + 1) / math.log10(_VOLUME_CEILING + 1))


def normalize_difficulty(difficulty: float | None) -> float:
    """0-1 score, inverted: low difficulty -> high score. None difficulty
    is treated as neutral (0.5) rather than 0 or 1, since we genuinely don't
    know — assuming the worst or best case would both bias the ranking."""
    if difficulty is None:
        return 0.5
    clamped = max(0.0, min(100.0, difficulty))
    return 1.0 - (clamped / 100.0)


def opportunity_score(
    *,
    volume: int | None,
    difficulty: float | None,
    relevance_score: float,
) -> float:
    """0-100 composite. relevance_score is expected to already be 0-100
    (Claude's judgment call on topical fit from Module 1 step 3)."""
    relevance_component = max(0.0, min(100.0, relevance_score)) / 100.0

    score = (
        _WEIGHT_VOLUME * normalize_volume(volume)
        + _WEIGHT_DIFFICULTY * normalize_difficulty(difficulty)
        + _WEIGHT_RELEVANCE * relevance_component
    )
    return round(score * 100, 2)
