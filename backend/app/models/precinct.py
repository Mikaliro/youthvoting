from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database import Base


class Precinct(Base):
    __tablename__ = "precincts"

    id = Column(Integer, primary_key=True, index=True)
    precinct_id = Column(String, nullable=False, unique=True)
    county_name = Column(String, nullable=False)
    cd_number = Column(Integer, nullable=True)  # Congressional district 1–52

    # Geometry: full resolution + simplified for API responses
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    geom_simplified = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)

    # Demographics
    total_pop = Column(Integer, nullable=True)
    pop_18_29 = Column(Integer, nullable=True)
    youth_share = Column(Float, nullable=True)

    # Election results
    dem_votes = Column(Integer, nullable=True)
    rep_votes = Column(Integer, nullable=True)
    total_votes = Column(Integer, nullable=True)
    dem_pct = Column(Float, nullable=True)
    dem_margin = Column(Float, nullable=True)

    # Scoring
    score = Column(Float, nullable=True)
    tier = Column(String, nullable=True)  # "priority", "target", "watchlist", "low"

    # Audit
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=True)
    pipeline_run = relationship("PipelineRun", back_populates="precincts")

    __table_args__ = (
        Index("idx_precincts_geom", "geom", postgresql_using="gist"),
        Index("idx_precincts_geom_simplified", "geom_simplified", postgresql_using="gist"),
        Index("idx_precincts_cd_number", "cd_number"),
        Index("idx_precincts_tier", "tier"),
        Index("idx_precincts_score", "score"),
        Index("idx_precincts_youth_share", "youth_share"),
        Index("idx_precincts_dem_margin", "dem_margin"),
    )
