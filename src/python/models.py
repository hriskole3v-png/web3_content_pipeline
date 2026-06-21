"""Shared data models for the content pipeline.

These dataclasses define the shape of data as it moves through each stage:
raw collected content -> enriched -> scored -> asset ready for publishing.
Keeping them in one place means every stage agrees on the contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class RawItem:
    """A single piece of content as collected, before any processing."""

    short_code: str
    source: str
    caption: str
    media_url: str
    posted_at: datetime
    like_count: int = 0
    comment_count: int = 0

    @staticmethod
    def from_dict(data: dict) -> "RawItem":
        """Build a RawItem from an upstream JSON payload.

        Tolerant of missing engagement fields, which are common when a
        source rate-limits or hides counts.
        """
        return RawItem(
            short_code=str(data["shortCode"]),
            source=str(data.get("source", "unknown")),
            caption=str(data.get("caption", "")),
            media_url=str(data["mediaUrl"]),
            posted_at=_parse_ts(data.get("postedAt")),
            like_count=int(data.get("likeCount", 0) or 0),
            comment_count=int(data.get("commentCount", 0) or 0),
        )


@dataclass
class EnrichedItem:
    """A RawItem after normalisation and feature extraction."""

    short_code: str
    source: str
    caption: str
    media_url: str
    posted_at: datetime
    engagement: int
    hashtags: list[str] = field(default_factory=list)
    word_count: int = 0
    age_hours: float = 0.0


@dataclass
class ScoredItem:
    """An EnrichedItem with a relevance score and a keep/skip decision."""

    item: EnrichedItem
    score: float
    keep: bool


@dataclass
class Asset:
    """A publish-ready asset with a collision-safe hosted filename."""

    short_code: str
    filename: str
    hosted_url: str
    run_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _parse_ts(value: Optional[str]) -> datetime:
    """Parse an ISO timestamp, defaulting to now() if absent or malformed."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)
