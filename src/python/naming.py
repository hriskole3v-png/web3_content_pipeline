"""Collision-safe asset naming.

Early pipeline runs hit filename collisions on the asset host: two different
posts, or the same post across re-runs, could resolve to the same target
filename and silently overwrite each other.

The fix keys every filename on the post's shortCode plus a per-run identifier.
That makes names deterministic within a run, unique across runs, and traceable
back to both the source post and the run that produced them.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

_SAFE = re.compile(r"[^a-zA-Z0-9_-]")


def new_run_id(now: datetime | None = None) -> str:
    """Generate a sortable, unique run identifier.

    Format: YYYYMMDDhhmmss-xxxxxx
    The timestamp prefix makes runs sort chronologically; the short random
    suffix guarantees uniqueness even for runs started in the same second.
    """
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"{stamp}-{suffix}"


def safe_slug(value: str) -> str:
    """Reduce an arbitrary string to a filesystem- and URL-safe slug."""
    cleaned = _SAFE.sub("-", value.strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned.lower() or "item"


def asset_filename(short_code: str, run_id: str, index: int = 0, ext: str = "png") -> str:
    """Build a collision-safe filename for a single asset.

    short_code identifies the source post, run_id isolates the run, and index
    distinguishes slides within a single carousel. The result is stable for a
    given (short_code, run_id, index) and unique otherwise.
    """
    if not short_code:
        raise ValueError("short_code is required")
    if not run_id:
        raise ValueError("run_id is required")
    code = safe_slug(short_code)
    return f"{code}__{run_id}__{index:02d}.{ext}"
