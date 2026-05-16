#!/usr/bin/env python3
"""
Entry point for the ABS Dashboard data pipeline.

Usage:
    python scripts/run.py                  # full run
    python scripts/run.py --dry-run        # fetch and compute but don't write JSON
    python scripts/run.py --skip-fetch     # use cached data, recompute only
"""

from __future__ import annotations

import argparse
import sys
import logging
import os
from pathlib import Path

# Configure logging before any imports that use it
log_level = os.environ.get("PIPELINE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    stream=sys.stdout,
)
logger = logging.getLogger("run")

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="ABS Dashboard data pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Compute but don't write JSON")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached data only")
    args = parser.parse_args()

    logger.info("ABS Dashboard pipeline starting")

    # Stub — full implementation in 02-data-pipeline.md
    logger.warning(
        "Pipeline stubs only. Run after completing 02-data-pipeline.md prompt. "
        "Writing placeholder JSON files."
    )

    if not args.dry_run:
        # Write minimal placeholder JSON to keep the build happy
        import json
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data_dir = REPO_ROOT / "src" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        placeholders = {
            "metadata.json": {
                "last_updated": now,
                "season": 2026,
                "data_quality": "missing",
                "stale_sources": ["all — pipeline not yet implemented"],
                "pipeline_version": "0.0.0",
                "games_through": None,
            },
            "teams.json": {"teams": [], "last_updated": now, "season": 2026},
            "players.json": {"players": [], "last_updated": now, "season": 2026},
            "daily.json": {"snapshots": [], "team_snapshots": [], "last_updated": now, "season": 2026},
        }

        for filename, payload in placeholders.items():
            path = data_dir / filename
            with open(path, "w") as f:
                json.dump(payload, f, indent=2)
            logger.info(f"Wrote placeholder {path}")

    logger.info("Pipeline complete (stub run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
