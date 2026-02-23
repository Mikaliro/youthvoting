from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["precincts"])


@router.get("/precincts")
def get_precincts(
    district: Optional[int] = None,
    youth_min: float = 0.15,
    margin_floor: float = 0.0,
    tier: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Returns a GeoJSON FeatureCollection of precincts built entirely in PostgreSQL
    via json_build_object + json_agg + ST_AsGeoJSON for maximum performance.
    """
    conditions = [
        "score IS NOT NULL",
        "youth_share >= :youth_min",
        "dem_margin >= :margin_floor",
    ]
    params: dict = {"youth_min": youth_min, "margin_floor": margin_floor}

    if district is not None:
        conditions.append("cd_number = :district")
        params["district"] = district

    if tier is not None:
        conditions.append("tier = :tier")
        params["tier"] = tier

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(f.feature), '[]'::json)
        ) AS geojson
        FROM (
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(COALESCE(geom_simplified, geom))::json,
                'properties', json_build_object(
                    'precinct_id', precinct_id,
                    'county_name', county_name,
                    'cd_number', cd_number,
                    'total_pop', total_pop,
                    'pop_18_29', pop_18_29,
                    'youth_share', youth_share,
                    'dem_votes', dem_votes,
                    'rep_votes', rep_votes,
                    'total_votes', total_votes,
                    'dem_pct', dem_pct,
                    'dem_margin', dem_margin,
                    'score', score,
                    'tier', tier
                )
            ) AS feature
            FROM precincts
            WHERE {where_clause}
            ORDER BY score DESC
            LIMIT 5000
        ) f
    """)

    row = db.execute(sql, params).fetchone()
    return row[0] if row and row[0] else {"type": "FeatureCollection", "features": []}
