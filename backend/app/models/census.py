from sqlalchemy import Column, Integer, String, Float, Index
from geoalchemy2 import Geometry

from app.database import Base


class CensusBlockGroup(Base):
    __tablename__ = "census_block_groups"

    id = Column(Integer, primary_key=True, index=True)
    geoid = Column(String(12), nullable=False, unique=True)
    county_fips = Column(String(5), nullable=False)
    total_pop = Column(Integer, nullable=True)
    pop_18_29 = Column(Integer, nullable=True)
    youth_share = Column(Float, nullable=True)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    acs_vintage = Column(Integer, nullable=False)  # e.g. 2022

    __table_args__ = (
        Index("idx_cbg_geom", "geom", postgresql_using="gist"),
        Index("idx_cbg_county_fips", "county_fips"),
    )
