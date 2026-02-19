import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["export"])

EXPORT_COLUMNS = [
    "precinct_id", "county_name", "cd_number",
    "total_pop", "pop_18_29", "youth_share",
    "dem_votes", "rep_votes", "total_votes", "dem_pct", "dem_margin",
    "score", "tier",
]


@router.get("/export/csv")
def export_csv(
    district: Optional[int] = None,
    youth_min: float = 0.0,
    margin_floor: float = -1.0,
    tier: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Stream a CSV export of filtered precincts."""
    conditions = [
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
    cols = ", ".join(EXPORT_COLUMNS)
    sql = text(f"SELECT {cols} FROM precincts WHERE {where_clause} ORDER BY score DESC NULLS LAST")

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(EXPORT_COLUMNS)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        rows = db.execute(sql, params)
        for row in rows:
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=precincts.csv"},
    )
