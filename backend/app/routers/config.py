from fastapi import APIRouter
from app.schemas.precinct import PipelineConfig

router = APIRouter(tags=["config"])

# Mirror of scripts/config.py — kept in sync manually or via shared import
PIPELINE_CONFIG = {
    "youth_share_min": 0.15,
    "dem_margin_floor": -0.10,
    "score_weights": {
        "youth_share": 0.6,
        "dem_margin": 0.4,
    },
    "tiers": {
        "priority": {"score_min": 0.70, "color": "#1a237e"},
        "target": {"score_min": 0.50, "color": "#3949ab"},
        "watchlist": {"score_min": 0.30, "color": "#7986cb"},
        "low": {"score_min": 0.0, "color": "#c5cae9"},
    },
    "acs_vintage": 2022,
    "election_contest": "PRESIDENT OF THE UNITED STATES",
}


@router.get("/config", response_model=PipelineConfig)
def get_config():
    """Returns pipeline threshold constants used for scoring precincts."""
    return PIPELINE_CONFIG
