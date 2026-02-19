from typing import Any, Optional
from pydantic import BaseModel


class PrecinctProperties(BaseModel):
    precinct_id: str
    county_name: str
    cd_number: Optional[int]
    total_pop: Optional[int]
    pop_18_29: Optional[int]
    youth_share: Optional[float]
    dem_votes: Optional[int]
    rep_votes: Optional[int]
    total_votes: Optional[int]
    dem_pct: Optional[float]
    dem_margin: Optional[float]
    score: Optional[float]
    tier: Optional[str]


class PrecinctFeature(BaseModel):
    type: str = "Feature"
    geometry: Any
    properties: PrecinctProperties


class PrecinctFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[PrecinctFeature]


class DistrictStats(BaseModel):
    cd_number: int
    precinct_count: int
    avg_youth_share: Optional[float]
    avg_dem_margin: Optional[float]
    priority_count: int
    target_count: int


class PipelineConfig(BaseModel):
    youth_share_min: float
    dem_margin_floor: float
    score_weights: dict[str, float]
    tiers: dict[str, dict[str, Any]]
    acs_vintage: int
    election_contest: str
