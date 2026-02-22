"""
Script 04 — Join VTD demographics to precincts and assign congressional districts.

Two joins:
1. VTD demographics (from census_block_groups table) → precincts
   Matches on VTD GEOID: state(2)+county(3)+vtdi
2. Block→CD assignment (from BAF file) → precincts via majority CD

Usage:
    DATABASE_URL=<url> python 04_crosswalk.py
"""

import os
import sys
import logging
from pathlib import Path
from collections import Counter

import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]


def join_demographics(engine) -> int:
    """
    Match census_block_groups (VTD-level demographics) to precincts.
    The geoid in census_block_groups = state+county+vtdi (same as TIGER GEOID20).
    """
    log.info("Joining VTD demographics to precincts...")
    sql = text("""
        UPDATE precincts p
        SET
            total_pop   = cbg.total_pop,
            pop_18_29   = cbg.pop_18_29,
            youth_share = cbg.youth_share
        FROM census_block_groups cbg
        WHERE p.precinct_id = cbg.geoid
    """)
    with engine.begin() as conn:
        result = conn.execute(sql)
        log.info("Matched %d precincts with demographics.", result.rowcount)
        return result.rowcount


def assign_congressional_districts(engine) -> int:
    """
    Assign congressional district to each precinct using BAF CD file.
    For each precinct, find the most common CD among its blocks.
    """
    log.info("Loading BAF CD crosswalk...")
    baf = pd.read_csv(cfg.BAF_CD_TXT, sep="|", dtype=str)
    baf.columns = ["block_geoid", "cd_number"]
    baf["block_geoid"] = baf["block_geoid"].str.strip()
    baf["cd_number"]   = pd.to_numeric(baf["cd_number"], errors="coerce")

    # Construct VTD key from block GEOID: state(2)+county(3)+remaining is tract+block
    # VTD key = state(2)+county(3)+vtdi — but block GEOID = state(2)+county(3)+tract(6)+block(4)
    # We need to group blocks by VTD. Use state+county as grouping + get majority CD per VTD.
    # Since we don't have the VTD→block direct mapping here without the VTD BAF file,
    # we use the spatial join via PostGIS as fallback.

    log.info("Loading precincts with geometry for CD spatial join...")
    with engine.connect() as conn:
        precincts = pd.read_sql(
            "SELECT precinct_id, ST_AsText(ST_Centroid(geom)) as centroid_wkt FROM precincts WHERE geom IS NOT NULL",
            conn
        )

    if precincts.empty:
        log.warning("No precincts with geometry found — skipping CD assignment.")
        return 0

    # Load CD shapefile
    log.info("Loading congressional district shapefile...")
    cds = gpd.read_file(cfg.CD_SHAPEFILE).to_crs(epsg=4326)
    cds["cd_number"] = pd.to_numeric(cds["CD118FP"], errors="coerce")

    # Build precinct centroids GeoDataFrame
    from shapely import wkt
    precincts["geometry"] = precincts["centroid_wkt"].apply(wkt.loads)
    prec_gdf = gpd.GeoDataFrame(precincts, geometry="geometry", crs="EPSG:4326")

    # Spatial join centroids → CD
    joined = gpd.sjoin(prec_gdf, cds[["cd_number", "geometry"]], how="left", predicate="within")
    joined = joined.drop_duplicates("precinct_id")

    log.info("Updating CD numbers in precincts table...")
    matched = 0
    with engine.begin() as conn:
        for _, row in joined.iterrows():
            if pd.isna(row.get("cd_number_right")):
                continue
            conn.execute(text("""
                UPDATE precincts SET cd_number = :cd WHERE precinct_id = :pid
            """), {"cd": int(row["cd_number_right"]), "pid": row["precinct_id"]})
            matched += 1

    log.info("Assigned CD to %d precincts.", matched)
    return matched


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    join_demographics(engine)
    assign_congressional_districts(engine)
    log.info("Script 04 complete.")


if __name__ == "__main__":
    main()
