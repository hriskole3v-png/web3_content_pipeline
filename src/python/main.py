"""Pipeline entry point.

Wires the stages together: load raw content -> enrich -> score/select ->
emit asset specs for the JS carousel generator. In production this is invoked
from an n8n Execute Command node; locally it runs against a fixtures file so
the whole flow is demonstrable without any live credentials.

Usage:
    python main.py --input fixtures/sample_input.json
    python main.py            # falls back to the bundled fixture
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from enrich import enrich_batch
from models import Asset, RawItem
from naming import asset_filename, new_run_id
from score import select

DEFAULT_INPUT = Path(__file__).parent / "fixtures" / "sample_input.json"
MAX_ASSETS = int(os.getenv("MAX_ASSETS", "10"))


def load_raw(path: Path) -> list[RawItem]:
    """Read an input payload and parse it into RawItems."""
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("items", data) if isinstance(data, dict) else data
    return [RawItem.from_dict(r) for r in records]


def build_asset_specs(path: Path, run_id: str) -> list[dict]:
    """Run the pipeline and produce asset specs for the generator stage."""
    raw = load_raw(path)
    enriched = enrich_batch(raw)
    scored = select(enriched)
    kept = [s for s in scored if s.keep][:MAX_ASSETS]

    specs: list[dict] = []
    for s in kept:
        asset = Asset(
            short_code=s.item.short_code,
            filename=asset_filename(s.item.short_code, run_id),
            hosted_url="",  # populated by the generator/host stage
            run_id=run_id,
        )
        specs.append(
            {
                "shortCode": asset.short_code,
                "filename": asset.filename,
                "runId": asset.run_id,
                "score": s.score,
                "caption": s.item.caption,
                "mediaUrl": s.item.media_url,
            }
        )
    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the content pipeline.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args(argv)

    run_id = new_run_id()
    specs = build_asset_specs(args.input, run_id)

    # Emit as JSON on stdout so an n8n node can pick it straight up.
    json.dump({"runId": run_id, "assets": specs}, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
