"""
Script 05 — Join election results to precincts, compute normalized composite
score, assign tiers, and simplify geometries.

Scoring formula:
    youth_norm = (youth_share - youth_share_min) / (1 - youth_share_min)
    margin_norm = (dem_margin - dem_margin_floor) / (1 - dem_margin_floor)
    score = w_youth * youth_norm + w_margin * margin_norm  (clamped 0–1)

Tier assignment:
    score >= 0.70 → priority
    score >= 0.50 → target
    score >= 0.30 → watchlist
    else          → low

Usage:
    DATABASE_URL=<url> python 05_merge_score.py [pipeline_run_id]
"""

import os
import sys
import logging
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]


def merge_election_results(engine) -> int:
    """Copy election results into precincts table by precinct_id."""
    sql = text("""
        UPDATE precincts p
        SET
            dem_votes   = er.dem_votes,
            rep_votes   = er.rep_votes,
            total_votes = er.total_votes,
            dem_pct     = er.dem_pct,
            dem_margin  = er.dem_margin
        FROM election_results er
        WHERE p.precinct_id = er.precinct_id
          AND er.contest_name = :contest
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {"contest": cfg.ELECTION_CONTEST})
        log.info("Merged election results into %d precincts.", result.rowcount)
        return result.rowcount


def compute_scores(engine) -> int:
    """Compute normalized composite score and assign tier labels."""
    w_youth = cfg.SCORE_WEIGHTS["youth_share"]
    w_margin = cfg.SCORE_WEIGHTS["dem_margin"]
    y_min = cfg.YOUTH_SHARE_MIN
    m_floor = cfg.DEM_MARGIN_FLOOR

    # Determine tier thresholds sorted descending
    tier_cases = " ".join([
        f"WHEN score >= {v['score_min']} THEN '{k}'"
        for k, v in sorted(cfg.TIERS.items(), key=lambda x: -x[1]["score_min"])
    ])

    sql = text(f"""
        WITH scored AS (
            SELECT
                precinct_id,
                GREATEST(0, LEAST(1,
                    {w_youth} * GREATEST(0, (youth_share - {y_min}) / NULLIF(1 - {y_min}, 0))
                  + {w_margin} * GREATEST(0, (dem_margin - {m_floor}) / NULLIF(1 - {m_floor}, 0))
                )) AS score
            FROM precincts
            WHERE youth_share IS NOT NULL
              AND dem_margin IS NOT NULL
              AND youth_share >= {y_min}
              AND dem_margin >= {m_floor}
        )
        UPDATE precincts p
        SET
            score = s.score,
            tier  = CASE {tier_cases} ELSE 'low' END
        FROM scored s
        WHERE p.precinct_id = s.precinct_id
    """)

    with engine.begin() as conn:
        result = conn.execute(sql)
        log.info("Scored %d precincts.", result.rowcount)
        return result.rowcount


def simplify_geometries(engine) -> None:
    """Populate geom_simplified using ST_SimplifyPreserveTopology."""
    sql = text("""
        UPDATE precincts
        SET geom_simplified = ST_Multi(
            ST_SimplifyPreserveTopology(geom, :tolerance)
        )
        WHERE geom IS NOT NULL
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {"tolerance": cfg.SIMPLIFICATION_TOLERANCE})
        log.info("Simplified geometry for %d precincts.", result.rowcount)


def main():
    pipeline_run_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    merge_election_results(engine)
    scored_count = compute_scores(engine)
    simplify_geometries(engine)

    # Tag precincts with this pipeline run
    if pipeline_run_id:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE precincts SET pipeline_run_id = :rid WHERE pipeline_run_id IS NULL"),
                {"rid": pipeline_run_id},
            )

    log.info("Script 05 complete — %d precincts scored.", scored_count)


if __name__ == "__main__":
    main()
