"""
Pipeline configuration — single source of truth for all thresholds and file paths.
"""
import os

# --- File paths (relative to backend/ working directory) ---
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

NHGIS_BLOCK_CSV   = os.path.join(RAW_DIR, "nhgis", "nhgis0002_ds258_2020_block.csv")
RDH_PRECINCT_CSV  = os.path.join(RAW_DIR, "rdh",   "ca_2024_gen_prec_csv.csv")
BAF_CD_TXT        = os.path.join(RAW_DIR, "baf",   "BlockAssign_ST06_CA_CD.txt")
CD_SHAPEFILE      = os.path.join(RAW_DIR, "cd",    "tl_2023_06_cd118.shp")

# --- NHGIS variable codes (2020 Decennial DHC, Table P12 / U7S) ---
# Male 18–29
MALE_18_29_VARS   = ["U7S007", "U7S008", "U7S009", "U7S010", "U7S011"]
# Female 18–29
FEMALE_18_29_VARS = ["U7S031", "U7S032", "U7S033", "U7S034", "U7S035"]
TOTAL_POP_VAR     = "U7S001"

# --- RDH election column names ---
RDH_DEM_COL       = "G24PREDHAR"   # Harris (Democrat)
RDH_REP_COL       = "G24PRERTRU"   # Trump (Republican)
RDH_TOTAL_COL     = "TOTVOTE"
RDH_PRECINCT_ID   = "UNIQUE_ID"
RDH_COUNTY_COL    = "COUNTY"
RDH_COUNTYFP_COL  = "COUNTYFP"

# --- Election metadata ---
ELECTION_DATE    = "2024-11-05"
ELECTION_CONTEST = "PRESIDENT OF THE UNITED STATES"

# --- Scoring thresholds ---
YOUTH_SHARE_MIN  = 0.15    # Minimum 18–29 share to include precinct
DEM_MARGIN_FLOOR = -0.10   # Minimum dem_margin (exclude deep-red precincts)

SCORE_WEIGHTS = {
    "youth_share": 0.60,
    "dem_margin":  0.40,
}

TIERS = {
    "priority":  {"score_min": 0.70, "color": "#1a237e"},
    "target":    {"score_min": 0.50, "color": "#3949ab"},
    "watchlist": {"score_min": 0.30, "color": "#7986cb"},
    "low":       {"score_min": 0.00, "color": "#c5cae9"},
}

# Geometry simplification tolerance (~50m at CA latitude)
SIMPLIFICATION_TOLERANCE = 0.0005

# Output
OUTPUT_DIR      = os.path.join(os.path.dirname(__file__), "..", "data", "output")
EXPORT_FILENAME = f"precincts_{ELECTION_DATE.replace('-', '')}.csv"
