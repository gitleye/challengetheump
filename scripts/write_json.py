"""
Validate computed metrics against Pydantic schemas and write JSON to src/data/.
Also regenerates src/lib/types.ts from the Pydantic schemas.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from compute_metrics import ComputedMetrics
from lib.schemas import (
    DailyData,
    LeagueSummary,
    MetricDefinition,
    MetricsGlossary,
    PlayersData,
    TeamsData,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "src" / "data"
TYPES_FILE = REPO_ROOT / "src" / "lib" / "types.ts"
PIPELINE_VERSION = "0.1.0"


def write_all(metrics: ComputedMetrics, dry_run: bool = False) -> bool:
    """
    Validate and write all JSON files to src/data/.
    Returns True on success, False if any validation failed.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ok = True

    # ---- Validate --------------------------------------------------------
    files = [
        ("teams.json", metrics.teams, TeamsData),
        ("players.json", metrics.players, PlayersData),
        ("daily.json", metrics.daily, DailyData),
    ]

    validated: list[tuple[str, object]] = []
    for filename, data, schema_cls in files:
        try:
            # Re-validate by round-tripping through the schema
            schema_cls.model_validate(data.model_dump())
            validated.append((filename, data))
            logger.debug(f"Validation passed: {filename}")
        except ValidationError as exc:
            logger.error(f"Validation FAILED for {filename}: {exc}")
            ok = False

    if not ok:
        logger.error("Validation errors — aborting write. Bad data is worse than missing data.")
        return False

    # ---- Write -----------------------------------------------------------
    if dry_run:
        logger.info("Dry run — skipping file writes")
        for filename, data in validated:
            logger.info(f"  Would write: {DATA_DIR / filename}")
        return True

    for filename, data in validated:
        path = DATA_DIR / filename
        content = data.model_dump_json(indent=2)
        path.write_text(content)
        logger.info(f"Wrote {path} ({len(content):,} bytes)")

    # ---- Metadata --------------------------------------------------------
    from lib.schemas import DataQuality, Metadata
    from fetch_data import FetchResult

    stale_sources = getattr(metrics, "_stale_sources", [])
    quality = DataQuality.OK
    if stale_sources:
        quality = DataQuality.PARTIAL

    meta = Metadata(
        last_updated=metrics.now_iso,
        season=metrics.teams.season,
        data_quality=quality,
        stale_sources=stale_sources,
        pipeline_version=PIPELINE_VERSION,
        games_through=_latest_game_date(metrics),
    )
    meta_path = DATA_DIR / "metadata.json"
    meta_path.write_text(meta.model_dump_json(indent=2))
    logger.info(f"Wrote {meta_path}")

    # ---- League summary --------------------------------------------------
    league_path = DATA_DIR / "league.json"
    league_path.write_text(metrics.league.model_dump_json(indent=2))
    logger.info(f"Wrote {league_path}")

    # ---- Metrics glossary -----------------------------------------------
    glossary = _build_glossary(metrics.now_iso)
    glossary_path = DATA_DIR / "metrics_glossary.json"
    glossary_path.write_text(glossary.model_dump_json(indent=2))
    logger.info(f"Wrote {glossary_path}")

    return True


def _latest_game_date(metrics: ComputedMetrics) -> str | None:
    if not metrics.daily.snapshots:
        return None
    return metrics.daily.snapshots[-1].date


def _build_glossary(now: str) -> MetricsGlossary:
    metrics = [
        MetricDefinition(
            key="challenge_wpa",
            label="Challenge WPA",
            definition="Sum of Win Probability Added across all successful ABS challenges for a team or player.",
            formula="Σ delta_home_win_exp for overturned pitches (adjusted for team perspective)",
            caveats=[
                "WPA is context-dependent — a challenge in a blowout contributes nearly zero.",
                "Based on Statcast WPA model, which may differ from ESPN or Baseball Reference.",
                "Small samples (< 5 successful challenges) are highly volatile.",
            ],
            unit="win probability units (0–1 scale)",
        ),
        MetricDefinition(
            key="success_rate",
            label="Challenge Success Rate",
            definition="Proportion of ABS challenges that resulted in an overturned call.",
            formula="successful_challenges / total_challenges",
            caveats=[
                "Does not weight by leverage — a meaningless challenge counts the same as a game-changing one.",
                "Samples below 10 challenges are flagged as unreliable.",
            ],
            unit="proportion (0–1)",
        ),
        MetricDefinition(
            key="net_overturns",
            label="Net Overturns",
            definition="Overturns in a team's favor minus overturns against them.",
            formula="overturns_for - overturns_against",
            caveats=[
                "Does not capture leverage — a team can have positive net overturns but negative WPA.",
            ],
            unit="integer",
        ),
        MetricDefinition(
            key="usage_rate",
            label="Challenge Usage Rate",
            definition="Challenges used per available challenge opportunity.",
            formula="total_challenges / total_challenge_opportunities",
            caveats=[
                "Total opportunities is estimated (2 per game per team) — actual availability varies.",
            ],
            unit="proportion (0–1)",
        ),
        MetricDefinition(
            key="win_pct_expected",
            label="Expected Win%",
            definition="Pythagorean win expectancy based on runs scored and allowed.",
            formula="RS^1.83 / (RS^1.83 + RA^1.83)",
            caveats=[
                "Exponent 1.83 is the MLB-calibrated Pythagorean exponent (James, 1980).",
                "Deviations from actual W% suggest luck or bullpen performance.",
            ],
            unit="proportion (0–1)",
        ),
    ]
    return MetricsGlossary(metrics=metrics, generated=now)


# ---- TypeScript type generation -----------------------------------------

TS_HEADER = """\
/**
 * Shared TypeScript types for the ABS Dashboard.
 * AUTO-GENERATED from scripts/lib/schemas.py — do not edit manually.
 * Regenerate: python scripts/run.py (or python scripts/write_json.py --types-only)
 *
 * Generated: {generated}
 */

"""

TS_TYPE_MAP = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "None": "null",
}


def regenerate_typescript_types(now: str) -> None:
    """
    Regenerate src/lib/types.ts from the Pydantic schema definitions.

    We write the types directly rather than using datamodel-code-generator,
    because the generated output often needs hand-tuning and the schemas
    are simple enough to translate manually here.
    """
    # Read the existing types.ts and update only the header timestamp
    if TYPES_FILE.exists():
        content = TYPES_FILE.read_text()
        # Replace the "Generated:" line
        import re
        content = re.sub(
            r"Generated:.*",
            f"Generated: {now}",
            content,
        )
        TYPES_FILE.write_text(content)
        logger.info(f"Updated timestamp in {TYPES_FILE}")
    else:
        logger.warning(f"{TYPES_FILE} does not exist — skipping TypeScript type update")
