"""
Script 03 — Fetch CA SoS precinct-level election results and load into
election_results table.

CA SoS publishes county-level CSV files after each election.
This script downloads the statewide precinct results CSV from the
official CA SoS website for the configured election date.

Usage:
    DATABASE_URL=<url> python 03_fetch_election.py
"""

import os
import sys
import logging
import io
from pathlib import Path

import requests
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

# CA SoS 2024 General Election statewide precinct results
# Adjust URL for different elections as needed
SOS_RESULTS_URL = (
    "https://elections.cdn.sos.ca.gov/results/2024-general/"
    "precinct-results.csv"
)


def fetch_election_results() -> pd.DataFrame:
    """Download CA SoS precinct results CSV and return filtered DataFrame."""
    log.info("Downloading election results from CA SoS...")
    resp = requests.get(SOS_RESULTS_URL, timeout=300, stream=True)
    resp.raise_for_status()

    df = pd.read_csv(io.BytesIO(resp.content), dtype=str, low_memory=False)
    log.info("Downloaded %d rows", len(df))

    # Normalize column names (CA SoS format varies by year)
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]

    # Filter to presidential contest
    contest_col = next((c for c in df.columns if "CONTEST" in c), None)
    if contest_col:
        df = df[df[contest_col].str.contains(cfg.ELECTION_CONTEST, case=False, na=False)]

    log.info("Filtered to %d rows for contest: %s", len(df), cfg.ELECTION_CONTEST)
    return df


def aggregate_to_precincts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate candidate rows to precinct-level dem/rep vote totals.
    Assumes columns: PRECINCT_ID (or similar), COUNTY_NAME, CANDIDATE_PARTY,
    VOTES, CONTEST_NAME.
    """
    # Flexible column mapping
    col_map = {}
    for col in df.columns:
        if "PRECINCT" in col and "ID" in col:
            col_map["precinct_id"] = col
        elif "COUNTY" in col:
            col_map["county_name"] = col
        elif "PARTY" in col:
            col_map["party"] = col
        elif "VOTES" in col and "TOTAL" not in col:
            col_map["votes"] = col
        elif "CONTEST" in col:
            col_map["contest"] = col

    df = df.rename(columns={v: k for k, v in col_map.items()})
    df["votes"] = pd.to_numeric(df.get("votes", 0), errors="coerce").fillna(0).astype(int)

    dem_mask = df.get("party", pd.Series(dtype=str)).str.upper().str.contains("DEM", na=False)
    rep_mask = df.get("party", pd.Series(dtype=str)).str.upper().str.contains("REP", na=False)

    groupby_cols = ["precinct_id", "county_name"]
    groupby_cols = [c for c in groupby_cols if c in df.columns]

    agg = df.groupby(groupby_cols).apply(lambda g: pd.Series({
        "dem_votes": g.loc[g.index.isin(g[dem_mask].index), "votes"].sum() if "votes" in g.columns else 0,
        "rep_votes": g.loc[g.index.isin(g[rep_mask].index), "votes"].sum() if "votes" in g.columns else 0,
        "total_votes": g["votes"].sum() if "votes" in g.columns else 0,
    })).reset_index()

    agg["dem_pct"] = (agg["dem_votes"] / agg["total_votes"].replace(0, float("nan"))).round(4)
    agg["rep_pct"] = (agg["rep_votes"] / agg["total_votes"].replace(0, float("nan"))).round(4)
    agg["dem_margin"] = (agg["dem_pct"] - agg["rep_pct"]).round(4)
    agg["election_date"] = cfg.ELECTION_DATE
    agg["contest_name"] = cfg.ELECTION_CONTEST

    return agg


def upsert_election_results(df: pd.DataFrame, engine) -> None:
    log.info("Upserting %d election result rows...", len(df))
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
                "election_date": row.get("election_date", cfg.ELECTION_DATE),
                "county_name": row.get("county_name", ""),
                "precinct_id": row.get("precinct_id", ""),
                "contest_name": cfg.ELECTION_CONTEST,
                "dem_votes": int(row.get("dem_votes", 0)),
                "rep_votes": int(row.get("rep_votes", 0)),
                "total_votes": int(row.get("total_votes", 0)),
                "dem_pct": float(row["dem_pct"]) if pd.notna(row.get("dem_pct")) else None,
                "dem_margin": float(row["dem_margin"]) if pd.notna(row.get("dem_margin")) else None,
            })
    log.info("Upsert complete.")


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    raw_df = fetch_election_results()
    agg_df = aggregate_to_precincts(raw_df)
    upsert_election_results(agg_df, engine)
    log.info("Script 03 complete — %d precincts with election data.", len(agg_df))


if __name__ == "__main__":
    main()
