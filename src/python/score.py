"""Scoring stage.

Decides which enriched items are worth turning into assets.

NOTE: the production relevance model is proprietary and is intentionally
omitted from this repository. What ships here is the interface plus a simple,
transparent baseline so the pipeline runs end to end. The real implementation
weights signals differently and incorporates logic that is specific to the
business; it is not published.

The contract is stable: score_item() returns a float in [0, 1] and select()
applies a threshold. Swapping in the production scorer is a drop-in.
"""

from __future__ import annotations

from models import EnrichedItem, ScoredItem

# Default keep threshold. The production pipeline tunes this per source.
DEFAULT_THRESHOLD = 0.5


def score_item(item: EnrichedItem) -> float:
    """Return a relevance score in [0, 1] for a single item.

    ---------------------------------------------------------------------
    Production scoring logic omitted.

    The shipped model combines engagement, recency, topical relevance and
    several business-specific signals. The baseline below is a stand-in that
    keeps the pipeline runnable and the interface honest.
    ---------------------------------------------------------------------
    """
    # Transparent baseline: blend normalised engagement with a recency decay.
    engagement_signal = min(item.engagement / 1000.0, 1.0)
    recency_signal = 1.0 / (1.0 + item.age_hours / 24.0)
    score = 0.6 * engagement_signal + 0.4 * recency_signal
    return round(min(max(score, 0.0), 1.0), 4)


def select(
    items: list[EnrichedItem], threshold: float = DEFAULT_THRESHOLD
) -> list[ScoredItem]:
    """Score a batch and tag each item with a keep/skip decision."""
    scored: list[ScoredItem] = []
    for item in items:
        s = score_item(item)
        scored.append(ScoredItem(item=item, score=s, keep=s >= threshold))
    # Highest scoring first, so downstream consumers can cap volume easily.
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored
