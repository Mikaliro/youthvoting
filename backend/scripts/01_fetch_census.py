"""
Script 01 — Load NHGIS block-level P12 age data and aggregate to VTD level.

Reads: data/raw/nhgis/nhgis0002_ds258_2020_block.csv
Writes: census_block_groups table (repurposed as VTD demographics)

Each row in the output represents one VTD (precinct boundary), with
total_pop and pop_18_29 aggregated from all census blocks inside it.
The NHGIS block CSV already contains VTD assignment (VTDI column),
so no spatial join is needed.

Usage:
    DATABASE_URL=<url> python 01_fetch_census.py
"""

import os
import sys
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]


def load_nhgis_blocks() -> pd.DataFrame:
    """Load NHGIS block CSV and compute youth population per block."""
    log.info("Loading NHGIS block CSV (~288 MB, may take a minute)...")
    df = pd.read_csv(cfg.NHGIS_BLOCK_CSV, dtype=str, low_memory=False)
    log.info("Loaded %d blocks", len(df))

    # Coerce age columns to numeric
    age_cols = cfg.MALE_18_29_VARS + cfg.FEMALE_18_29_VARS + [cfg.TOTAL_POP_VAR]
    for col in age_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["pop_18_29"] = df[cfg.MALE_18_29_VARS + cfg.FEMALE_18_29_VARS].sum(axis=1)
    df["total_pop"] = df[cfg.TOTAL_POP_VAR]

    # Build VTD composite key: state(2) + county(3) + vtdi
    df["STATEA"]  = df["STATEA"].str.strip().str.zfill(2)
    df["COUNTYA"] = df["COUNTYA"].str.strip().str.zfill(3)
    df["VTDI"]    = df["VTDI"].str.strip().fillna("")

    df["vtd_key"] = df["STATEA"] + df["COUNTYA"] + df["VTDI"]

    # Drop blocks with no VTD assignment
    df = df[df["VTDI"] != ""]
    log.info("%d blocks have VTD assignment", len(df))

    return df[["vtd_key", "STATEA", "COUNTYA", "VTDI", "COUNTY", "total_pop", "pop_18_29"]]


def load_baf_cd() -> pd.DataFrame:
    """Load block-to-CD crosswalk from BAF file."""
    log.info("Loading BAF congressional district crosswalk...")
    baf = pd.read_csv(cfg.BAF_CD_TXT, sep="|", dtype=str)
    baf.columns = ["block_geoid", "cd_number"]
    baf["block_geoid"] = baf["block_geoid"].str.strip()
    baf["cd_number"]   = pd.to_numeric(baf["cd_number"], errors="coerce")

    # Build VTD key from block GEOID: state(2)+county(3)+tract(6)+block(4)
    # VTD key = state(2) + county(3) + vtdi — we'll join on block→vtd from NHGIS later
    # For now return block→CD mapping
    baf["state_county"] = baf["block_geoid"].str[:5]
    return baf[["block_geoid", "cd_number"]]


def aggregate_to_vtd(blocks: pd.DataFrame) -> pd.DataFrame:
    """Aggregate block-level data to VTD level."""
    log.info("Aggregating blocks to VTD level...")
    vtd = blocks.groupby(["vtd_key", "STATEA", "COUNTYA", "VTDI", "COUNTY"]).agg(
        total_pop=("total_pop", "sum"),
        pop_18_29=("pop_18_29", "sum"),
    ).reset_index()

    vtd["youth_share"] = (
        vtd["pop_18_29"] / vtd["total_pop"].replace(0, float("nan"))
    ).round(4)

    log.info("Aggregated to %d VTDs", len(vtd))
    return vtd


def upsert_vtd_demographics(vtd: pd.DataFrame, engine) -> None:
    """Upsert VTD demographics into census_block_groups table."""
    log.info("Upserting %d VTD rows into database...", len(vtd))

    with engine.begin() as conn:
        for _, row in vtd.iterrows():
            conn.execute(text("""
                INSERT INTO census_block_groups
                    (geoid, county_fips, total_pop, pop_18_29, youth_share, acs_vintage)
                VALUES
                    (:geoid, :county_fips, :total_pop, :pop_18_29, :youth_share, :vintage)
                ON CONFLICT (geoid) DO UPDATE SET
                    total_pop   = EXCLUDED.total_pop,
                    pop_18_29   = EXCLUDED.pop_18_29,
                    youth_share = EXCLUDED.youth_share
            """), {
                "geoid":       row["vtd_key"],
                "county_fips": row["STATEA"] + row["COUNTYA"],
                "total_pop":   int(row["total_pop"]),
                "pop_18_29":   int(row["pop_18_29"]),
                "youth_share": float(row["youth_share"]) if pd.notna(row["youth_share"]) else None,
                "vintage":     2020,
            })

    log.info("Upsert complete.")


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    blocks = load_nhgis_blocks()
    vtd    = aggregate_to_vtd(blocks)
    upsert_vtd_demographics(vtd, engine)
    log.info("Script 01 complete — %d VTDs loaded.", len(vtd))


if __name__ == "__main__":
    main()
