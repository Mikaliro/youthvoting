"""
Pipeline configuration — single source of truth for all thresholds.
Imported by all pipeline scripts (01–06) and mirrored in app/routers/config.py.
"""

# --- ACS / Census settings ---
ACS_VINTAGE = 2022  # 5-year ACS dataset year
ACS_DATASET = "acs/acs5"
CA_STATE_FIPS = "06"

# ACS variable codes for age/sex by population
# B01001: Sex by Age — sum male + female age groups 18–29
ACS_VARIABLES = [
    "B01001_001E",  # Total population
    # Male 18–29
    "B01001_007E",  # Male 18–19
    "B01001_008E",  # Male 20
    "B01001_009E",  # Male 21
    "B01001_010E",  # Male 22–24
    "B01001_011E",  # Male 25–29
    # Female 18–29
    "B01001_031E",  # Female 18–19
    "B01001_032E",  # Female 20
    "B01001_033E",  # Female 21
    "B01001_034E",  # Female 22–24
    "B01001_035E",  # Female 25–29
]

MALE_18_29_VARS = [
    "B01001_007E", "B01001_008E", "B01001_009E", "B01001_010E", "B01001_011E"
]
FEMALE_18_29_VARS = [
    "B01001_031E", "B01001_032E", "B01001_033E", "B01001_034E", "B01001_035E"
]
TOTAL_POP_VAR = "B01001_001E"

# --- Election settings ---
ELECTION_DATE = "2024-11-05"
ELECTION_CONTEST = "PRESIDENT OF THE UNITED STATES"

# --- Scoring thresholds ---
YOUTH_SHARE_MIN = 0.15   # Minimum 18–29 share to include precinct
DEM_MARGIN_FLOOR = -0.10  # Minimum dem_margin (exclude deep-red precincts)

# Composite score weights (must sum to 1.0)
SCORE_WEIGHTS = {
    "youth_share": 0.60,
    "dem_margin": 0.40,
}

# Tier definitions (score thresholds, inclusive lower bound)
TIERS = {
    "priority":  {"score_min": 0.70, "color": "#1a237e"},
    "target":    {"score_min": 0.50, "color": "#3949ab"},
    "watchlist": {"score_min": 0.30, "color": "#7986cb"},
    "low":       {"score_min": 0.00, "color": "#c5cae9"},
}

# Geometry simplification tolerance (degrees, ~50m at CA latitude)
SIMPLIFICATION_TOLERANCE = 0.0005

# Output paths
OUTPUT_DIR = "data/output"
EXPORT_FILENAME = f"precincts_{ELECTION_DATE.replace('-', '')}.csv"
