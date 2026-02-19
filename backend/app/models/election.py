from sqlalchemy import Column, Integer, String, Float, Date, Index

from app.database import Base


class ElectionResult(Base):
    __tablename__ = "election_results"

    id = Column(Integer, primary_key=True, index=True)
    election_date = Column(Date, nullable=False)
    county_name = Column(String, nullable=False)
    precinct_id = Column(String, nullable=False)
    contest_name = Column(String, nullable=False)
    dem_votes = Column(Integer, nullable=False, default=0)
    rep_votes = Column(Integer, nullable=False, default=0)
    total_votes = Column(Integer, nullable=False, default=0)
    dem_pct = Column(Float, nullable=True)
    dem_margin = Column(Float, nullable=True)

    __table_args__ = (
        Index("idx_election_results_precinct_id", "precinct_id"),
        Index("idx_election_results_county_contest", "county_name", "contest_name"),
    )
