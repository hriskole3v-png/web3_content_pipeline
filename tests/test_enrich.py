"""Tests for the enrichment and scoring stages."""

from datetime import datetime, timedelta, timezone

from enrich import age_in_hours, enrich, enrich_batch, extract_hashtags
from models import RawItem
from score import score_item, select


def _raw(**kwargs) -> RawItem:
    base = dict(
        short_code="Cx7aB2qLk0",
        source="example",
        caption="hello world #growth #Growth #startup",
        media_url="https://example.com/x.jpg",
        posted_at=datetime.now(timezone.utc),
        like_count=100,
        comment_count=20,
    )
    base.update(kwargs)
    return RawItem(**base)


def test_extract_hashtags_dedupes_and_lowercases():
    tags = extract_hashtags("hello #Growth #growth #Startup")
    assert tags == ["growth", "startup"]


def test_age_in_hours_never_negative():
    future = datetime.now(timezone.utc) + timedelta(hours=5)
    assert age_in_hours(future) == 0.0


def test_enrich_sums_engagement():
    item = enrich(_raw(like_count=100, comment_count=20))
    assert item.engagement == 120


def test_enrich_extracts_features():
    item = enrich(_raw(caption="a b c #one #two"))
    assert item.word_count == 5
    assert item.hashtags == ["one", "two"]


def test_enrich_batch_drops_items_without_media():
    items = [_raw(), _raw(media_url="")]
    out = enrich_batch(items)
    assert len(out) == 1


def test_score_is_bounded():
    item = enrich(_raw(like_count=10_000, comment_count=10_000))
    s = score_item(item)
    assert 0.0 <= s <= 1.0


def test_select_sorts_by_score_desc():
    high = enrich(_raw(short_code="HIGH", like_count=5000, comment_count=500))
    low = enrich(_raw(short_code="LOW", like_count=1, comment_count=0,
                      posted_at=datetime.now(timezone.utc) - timedelta(days=30)))
    scored = select([low, high])
    assert scored[0].item.short_code == "HIGH"
    assert scored[0].score >= scored[1].score


def test_select_applies_threshold():
    item = enrich(_raw(like_count=1, comment_count=0,
                       posted_at=datetime.now(timezone.utc) - timedelta(days=60)))
    scored = select([item], threshold=0.99)
    assert scored[0].keep is False
