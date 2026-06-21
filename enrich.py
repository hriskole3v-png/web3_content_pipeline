"""Enrichment stage.

Takes raw collected content and normalises it into a consistent shape with a
few derived features (engagement total, hashtags, recency). This is the step
that turns messy upstream payloads into something the scoring stage can reason
about cleanly.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from models import EnrichedItem, RawItem

_HASHTAG = re.compile(r"#(\w+)")


def extract_hashtags(caption: str) -> list[str]:
    """Pull hashtags out of a caption, lowercased and de-duplicated."""
    seen: list[str] = []
    for tag in _HASHTAG.findall(caption or ""):
        tag = tag.lower()
        if tag not in seen:
            seen.append(tag)
    return seen


def age_in_hours(posted_at: datetime, now: datetime | None = None) -> float:
    """Hours elapsed since a post was published. Never negative."""
    now = now or datetime.now(timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    delta = (now - posted_at).total_seconds() / 3600.0
    return max(0.0, round(delta, 2))


def enrich(item: RawItem, now: datetime | None = None) -> EnrichedItem:
    """Normalise a single raw item and attach derived features."""
    caption = (item.caption or "").strip()
    return EnrichedItem(
        short_code=item.short_code,
        source=item.source,
        caption=caption,
        media_url=item.media_url,
        posted_at=item.posted_at,
        engagement=item.like_count + item.comment_count,
        hashtags=extract_hashtags(caption),
        word_count=len(caption.split()),
        age_hours=age_in_hours(item.posted_at, now),
    )


def enrich_batch(items: list[RawItem], now: datetime | None = None) -> list[EnrichedItem]:
    """Enrich a batch, dropping anything missing a usable media URL."""
    out: list[EnrichedItem] = []
    for raw in items:
        if not raw.media_url:
            continue
        out.append(enrich(raw, now))
    return out
