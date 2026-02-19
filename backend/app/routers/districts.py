from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.precinct import DistrictStats

router = APIRouter(tags=["districts"])


@router.get("/districts", response_model=list[DistrictStats])
def get_districts(db: Session = Depends(get_db)):
    """Aggregate stats per congressional district."""
    sql = text("""
        SELECT
            cd_number,
            COUNT(*) AS precinct_count,
            AVG(youth_share) AS avg_youth_share,
            AVG(dem_margin) AS avg_dem_margin,
            COUNT(*) FILTER (WHERE tier = 'priority') AS priority_count,
            COUNT(*) FILTER (WHERE tier = 'target') AS target_count
        FROM precincts
        WHERE cd_number IS NOT NULL
        GROUP BY cd_number
        ORDER BY cd_number
    """)
    rows = db.execute(sql).mappings().all()
    return [dict(r) for r in rows]
