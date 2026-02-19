"""
Script 01 — Fetch ACS 5-year data for all California block groups.

Pulls B01001 (Sex by Age) variables, computes youth_share (18–29),
and upserts rows into the census_block_groups table.

Usage:
    CENSUS_API_KEY=<key> DATABASE_URL=<url> python 01_fetch_census.py
"""

import os
import sys
import logging
from pathlib import Path

import requests
import pandas as pd
from sqlalchemy import create_engine, text

# Allow running from scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")


def fetch_acs_block_groups() -> pd.DataFrame:
    """Fetch ACS variables for all CA block groups via Census API."""
    base_url = f"https://api.census.gov/data/{cfg.ACS_VINTAGE}/{cfg.ACS_DATASET}"
    variables = ",".join(["GEO_ID"] + cfg.ACS_VARIABLES)

    log.info("Fetching ACS block groups from Census API (vintage=%s)...", cfg.ACS_VINTAGE)
    resp = requests.get(
        base_url,
        params={
            "get": variables,
            "for": "block group:*",
            "in": f"state:{cfg.CA_STATE_FIPS} county:* tract:*",
            "key": CENSUS_API_KEY,
        },
        timeout=120,
    )
    resp.raise_for_status()

    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])

    # Coerce numeric columns
    for col in cfg.ACS_VARIABLES:
        df[col] = pd.to_numeric(df[col], errors="coerce").clip(lower=0)

    # Compute derived fields
    df["pop_18_29"] = df[cfg.MALE_18_29_VARS + cfg.FEMALE_18_29_VARS].sum(axis=1)
    df["total_pop"] = df[cfg.TOTAL_POP_VAR]
    df["youth_share"] = (df["pop_18_29"] / df["total_pop"].replace(0, float("nan"))).round(4)

    # Build GEOID: state(2) + county(3) + tract(6) + block group(1)
    df["geoid"] = df["state"] + df["county"] + df["tract"] + df["block group"]
    df["county_fips"] = df["state"] + df["county"]

    log.info("Fetched %d block groups", len(df))
    return df[["geoid", "county_fips", "total_pop", "pop_18_29", "youth_share"]]


def upsert_census_data(df: pd.DataFrame, engine) -> None:
    """Upsert block group rows into census_block_groups (no geometry yet)."""
    log.info("Upserting %d block groups into database...", len(df))

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS census_block_groups (
                id          SERIAL PRIMARY KEY,
                geoid       VARCHAR(12) NOT NULL UNIQUE,
                county_fips VARCHAR(5)  NOT NULL,
                total_pop   INTEGER,
                pop_18_29   INTEGER,
                youth_share DOUBLE PRECISION,
                geom        GEOMETRY(MultiPolygon, 4326),
                acs_vintage INTEGER NOT NULL
            )
        """))

        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO census_block_groups (geoid, county_fips, total_pop, pop_18_29, youth_share, acs_vintage)
                VALUES (:geoid, :county_fips, :total_pop, :pop_18_29, :youth_share, :acs_vintage)
                ON CONFLICT (geoid) DO UPDATE SET
                    total_pop   = EXCLUDED.total_pop,
                    pop_18_29   = EXCLUDED.pop_18_29,
                    youth_share = EXCLUDED.youth_share,
                    acs_vintage = EXCLUDED.acs_vintage
            """), {
                "geoid": row["geoid"],
                "county_fips": row["county_fips"],
                "total_pop": int(row["total_pop"]) if pd.notna(row["total_pop"]) else None,
                "pop_18_29": int(row["pop_18_29"]) if pd.notna(row["pop_18_29"]) else None,
                "youth_share": float(row["youth_share"]) if pd.notna(row["youth_share"]) else None,
                "acs_vintage": cfg.ACS_VINTAGE,
            })

    log.info("Upsert complete.")


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    df = fetch_acs_block_groups()
    upsert_census_data(df, engine)
    log.info("Script 01 complete — %d block groups loaded.", len(df))


if __name__ == "__main__":
    main()
