"""
Script 04 — Area-weighted spatial join: interpolate ACS block group
demographics into voting precincts using PostGIS.

The area-weighted interpolation formula:
    precinct_pop_18_29 = SUM(
        cbg.pop_18_29 * ST_Area(ST_Intersection(p.geom, cbg.geom)) / ST_Area(cbg.geom)
    )

This runs entirely in PostGIS for performance.

Usage:
    DATABASE_URL=<url> python 04_crosswalk.py
"""

import os
import sys
import logging
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

CROSSWALK_SQL = text("""
    UPDATE precincts p
    SET
        total_pop = sub.total_pop,
        pop_18_29 = sub.pop_18_29,
        youth_share = CASE
            WHEN sub.total_pop > 0 THEN sub.pop_18_29::double precision / sub.total_pop
            ELSE NULL
        END
    FROM (
        SELECT
            p.precinct_id,
            SUM(
                cbg.total_pop
                * ST_Area(ST_Intersection(p.geom, cbg.geom))
                / NULLIF(ST_Area(cbg.geom), 0)
            )::integer AS total_pop,
            SUM(
                cbg.pop_18_29
                * ST_Area(ST_Intersection(p.geom, cbg.geom))
                / NULLIF(ST_Area(cbg.geom), 0)
            )::integer AS pop_18_29
        FROM precincts p
        JOIN census_block_groups cbg
            ON ST_Intersects(p.geom, cbg.geom)
        WHERE p.geom IS NOT NULL
          AND cbg.geom IS NOT NULL
        GROUP BY p.precinct_id
    ) sub
    WHERE p.precinct_id = sub.precinct_id
""")


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    log.info("Running area-weighted spatial join (this may take several minutes)...")
    with engine.begin() as conn:
        result = conn.execute(CROSSWALK_SQL)
        log.info("Updated %d precinct rows with census demographics.", result.rowcount)

    log.info("Script 04 complete.")


if __name__ == "__main__":
    main()
