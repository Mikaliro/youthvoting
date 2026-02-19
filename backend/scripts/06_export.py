"""
Script 06 — Export CSV snapshot of scored precincts and record pipeline_run audit.

Creates data/output/precincts_YYYYMMDD.csv and updates the pipeline_runs row
for this run (status=success, precincts_scored=N, finished_at=NOW()).

Usage:
    DATABASE_URL=<url> python 06_export.py <pipeline_run_id>
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

EXPORT_COLUMNS = [
    "precinct_id", "county_name", "cd_number",
    "total_pop", "pop_18_29", "youth_share",
    "dem_votes", "rep_votes", "total_votes", "dem_pct", "dem_margin",
    "score", "tier",
]


def export_csv(engine, output_path: Path) -> int:
    """Export scored precincts to CSV, return row count."""
    cols = ", ".join(EXPORT_COLUMNS)
    sql = text(f"""
        SELECT {cols} FROM precincts
        WHERE score IS NOT NULL
        ORDER BY score DESC NULLS LAST
    """)

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Exported %d rows to %s", len(df), output_path)
    return len(df)


def mark_pipeline_success(engine, run_id: int, precincts_scored: int) -> None:
    config_snapshot = {
        "youth_share_min": cfg.YOUTH_SHARE_MIN,
        "dem_margin_floor": cfg.DEM_MARGIN_FLOOR,
        "score_weights": cfg.SCORE_WEIGHTS,
        "acs_vintage": cfg.ACS_VINTAGE,
        "election_contest": cfg.ELECTION_CONTEST,
        "election_date": cfg.ELECTION_DATE,
    }
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE pipeline_runs
            SET status           = 'success',
                precincts_scored = :precincts_scored,
                config_snapshot  = :config_snapshot,
                finished_at      = :finished_at
            WHERE id = :run_id
        """), {
            "run_id": run_id,
            "precincts_scored": precincts_scored,
            "config_snapshot": json.dumps(config_snapshot),
            "finished_at": datetime.now(timezone.utc),
        })
    log.info("Pipeline run %d marked as success.", run_id)


def main():
    if len(sys.argv) < 2:
        log.error("Usage: python 06_export.py <pipeline_run_id>")
        sys.exit(1)

    pipeline_run_id = int(sys.argv[1])
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    output_path = Path(cfg.OUTPUT_DIR) / cfg.EXPORT_FILENAME
    n = export_csv(engine, output_path)
    mark_pipeline_success(engine, pipeline_run_id, n)

    log.info("Script 06 complete — pipeline run %d finished.", pipeline_run_id)


if __name__ == "__main__":
    main()
