"""Tests for collision-safe asset naming.

These cover the exact bug the naming module exists to fix: two runs of the
same post must not collide, slides within a run must stay distinct, and the
same inputs must always produce the same name.
"""

import re

import pytest
from naming import asset_filename, new_run_id, safe_slug


def test_same_inputs_are_deterministic():
    name_a = asset_filename("Cx7aB2qLk0", "20260621093000-abc123", index=0)
    name_b = asset_filename("Cx7aB2qLk0", "20260621093000-abc123", index=0)
    assert name_a == name_b


def test_different_runs_do_not_collide():
    name_a = asset_filename("Cx7aB2qLk0", new_run_id())
    name_b = asset_filename("Cx7aB2qLk0", new_run_id())
    assert name_a != name_b


def test_slides_within_a_run_are_distinct():
    run = "20260621093000-abc123"
    names = {asset_filename("Cx7aB2qLk0", run, index=i) for i in range(5)}
    assert len(names) == 5


def test_run_id_is_sortable_and_unique():
    a = new_run_id()
    b = new_run_id()
    assert a != b
    # 14-digit timestamp, a hyphen, then a 6-char suffix
    assert re.match(r"^\d{14}-[0-9a-f]{6}$", a)


def test_safe_slug_strips_unsafe_characters():
    assert safe_slug("Hello World!/../x") == "hello-world-x"


def test_missing_short_code_raises():
    with pytest.raises(ValueError):
        asset_filename("", "20260621093000-abc123")


def test_missing_run_id_raises():
    with pytest.raises(ValueError):
        asset_filename("Cx7aB2qLk0", "")
