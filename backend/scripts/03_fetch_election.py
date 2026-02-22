"""
Script 03 — Load 2024 election results from RDH precinct CSV.

Reads: data/raw/rdh/ca_2024_gen_prec_csv.csv
Writes: election_results table + updates precincts table with vote totals

The RDH UNIQUE_ID field encodes state+county+precinct and maps to
the TIGER VTD GEOID20 used as precinct_id in our precincts table.

Usage:
    DATABASE_URL=<url> python 03_fetch_election.py
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


def load_rdh_csv() -> pd.DataFrame:
    """Load and process RDH 2024 precinct election results."""
    log.info("Loading RDH 2024 precinct CSV...")
    df = pd.read_csv(cfg.RDH_PRECINCT_CSV, dtype=str, low_memory=False)
    log.info("Loaded %d precinct rows", len(df))

    # Coerce vote columns
    for col in [cfg.RDH_DEM_COL, cfg.RDH_REP_COL, cfg.RDH_TOTAL_COL]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Compute election stats
    df["dem_votes"]   = df[cfg.RDH_DEM_COL].astype(int)
    df["rep_votes"]   = df[cfg.RDH_REP_COL].astype(int)
    df["total_votes"] = df[cfg.RDH_TOTAL_COL].astype(int)

    df["dem_pct"] = (
        df["dem_votes"] / df["total_votes"].replace(0, float("nan"))
    ).round(4)
    df["rep_pct"] = (
        df["rep_votes"] / df["total_votes"].replace(0, float("nan"))
    ).round(4)
    df["dem_margin"] = (df["dem_pct"] - df["rep_pct"]).round(4)

    # Normalize precinct ID to match TIGER VTD GEOID20 (11 chars: state+county+vtdi)
    # RDH UNIQUE_ID is state(2)+county(3)+precinct — strip to 11 chars if longer
    df["precinct_id"] = df[cfg.RDH_PRECINCT_ID].str.strip()

    # Also try building an 11-char key from COUNTYFP + PRECINCT
    df["COUNTYFP_3"] = df[cfg.RDH_COUNTYFP_COL].str.strip().str[-3:].str.zfill(3)
    df["PRECINCT_6"] = df["PRECINCT"].str.strip().str.zfill(6).str[-6:]
    df["vtd_key_11"] = "06" + df["COUNTYFP_3"] + df["PRECINCT_6"]

    df["county_name"] = df[cfg.RDH_COUNTY_COL].str.strip()
    df["election_date"] = cfg.ELECTION_DATE
    df["contest_name"]  = cfg.ELECTION_CONTEST

    return df[[
        "precinct_id", "vtd_key_11", "county_name",
        "dem_votes", "rep_votes", "total_votes",
        "dem_pct", "dem_margin", "election_date", "contest_name"
    ]]


def upsert_election_results(df: pd.DataFrame, engine) -> None:
    """Insert election results into election_results table."""
    log.info("Inserting %d rows into election_results...", len(df))
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO election_results
                    (election_date, county_name, precinct_id, contest_name,
                     dem_votes, rep_votes, total_votes, dem_pct, dem_margin)
                VALUES
                    (:election_date, :county_name, :precinct_id, :contest_name,
                     :dem_votes, :rep_votes, :total_votes, :dem_pct, :dem_margin)
                ON CONFLICT DO NOTHING
            """), {
                "election_date": row["election_date"],
                "county_name":   row["county_name"],
                "precinct_id":   row["precinct_id"],
                "contest_name":  row["contest_name"],
                "dem_votes":     int(row["dem_votes"]),
                "rep_votes":     int(row["rep_votes"]),
                "total_votes":   int(row["total_votes"]),
                "dem_pct":       float(row["dem_pct"]) if pd.notna(row.get("dem_pct")) else None,
                "dem_margin":    float(row["dem_margin"]) if pd.notna(row.get("dem_margin")) else None,
            })
    log.info("Election results inserted.")


def update_precinct_election_data(df: pd.DataFrame, engine) -> int:
    """
    Update precincts table with election results.
    Tries matching on precinct_id directly, then falls back to vtd_key_11.
    """
    matched = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            # Try direct match first (RDH UNIQUE_ID = TIGER GEOID20)
            result = conn.execute(text("""
                UPDATE precincts SET
                    county_name = :county_name,
                    dem_votes   = :dem_votes,
                    rep_votes   = :rep_votes,
                    total_votes = :total_votes,
                    dem_pct     = :dem_pct,
                    dem_margin  = :dem_margin
                WHERE precinct_id = :precinct_id
            """), {
                "precinct_id": row["precinct_id"],
                "county_name": row["county_name"],
                "dem_votes":   int(row["dem_votes"]),
                "rep_votes":   int(row["rep_votes"]),
                "total_votes": int(row["total_votes"]),
                "dem_pct":     float(row["dem_pct"]) if pd.notna(row.get("dem_pct")) else None,
                "dem_margin":  float(row["dem_margin"]) if pd.notna(row.get("dem_margin")) else None,
            })

            if result.rowcount == 0:
                # Fallback: try 11-char VTD key
                result2 = conn.execute(text("""
                    UPDATE precincts SET
                        county_name = :county_name,
                        dem_votes   = :dem_votes,
                        rep_votes   = :rep_votes,
                        total_votes = :total_votes,
                        dem_pct     = :dem_pct,
                        dem_margin  = :dem_margin
                    WHERE precinct_id = :precinct_id
                """), {
                    "precinct_id": row["vtd_key_11"],
                    "county_name": row["county_name"],
                    "dem_votes":   int(row["dem_votes"]),
                    "rep_votes":   int(row["rep_votes"]),
                    "total_votes": int(row["total_votes"]),
                    "dem_pct":     float(row["dem_pct"]) if pd.notna(row.get("dem_pct")) else None,
                    "dem_margin":  float(row["dem_margin"]) if pd.notna(row.get("dem_margin")) else None,
                })
                if result2.rowcount > 0:
                    matched += 1
            else:
                matched += 1

    total = len(df)
    log.info("Matched %d / %d precincts (%.1f%%)", matched, total, 100 * matched / total if total else 0)
    return matched


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    df = load_rdh_csv()
    upsert_election_results(df, engine)
    update_precinct_election_data(df, engine)
    log.info("Script 03 complete.")


if __name__ == "__main__":
    main()
