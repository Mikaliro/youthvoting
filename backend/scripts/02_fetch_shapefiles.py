"""
Script 02 — Load precinct geometries from TIGER/Line VTD shapefiles.

Downloads the statewide CA VTD shapefile from Census and loads precinct
boundaries into the precincts table. This provides the geometry column
that the map uses — election results are joined in script 03.

Usage:
    DATABASE_URL=<url> python 02_fetch_shapefiles.py
"""

import os
import sys
import logging
import zipfile
import tempfile
from pathlib import Path

import requests
import geopandas as gpd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

# CA statewide VTD shapefile (single zip, all counties)
TIGER_VTD_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/"
    "06_CALIFORNIA/06/tl_2020_06_vtd20.zip"
)


def download_vtd_shapefile(dest_dir: Path) -> Path:
    """Download CA statewide VTD shapefile zip."""
    zip_path = dest_dir / "tl_2020_06_vtd20.zip"
    log.info("Downloading CA VTD shapefile (~75 MB)...")
    resp = requests.get(TIGER_VTD_URL, timeout=300, stream=True)
    resp.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=131072):
            f.write(chunk)

    extract_dir = dest_dir / "vtd"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    shp_files = list(extract_dir.glob("*.shp"))
    if not shp_files:
        raise FileNotFoundError("No .shp file found in VTD zip")
    return shp_files[0]


def load_vtd_shapefile(shp_path: Path) -> gpd.GeoDataFrame:
    """Load VTD shapefile and normalize fields."""
    log.info("Loading VTD shapefile...")
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs(epsg=4326)

    # TIGER VTD fields: GEOID20 = state+county+vtdi (11 chars)
    # NAMELSAD20 = human-readable name
    # COUNTYFP20 = 3-digit county FIPS
    gdf["precinct_id"]  = gdf["GEOID20"].str.strip()
    gdf["county_fips"]  = "06" + gdf["COUNTYFP20"].str.strip()
    gdf["vtdi"]         = gdf["VTDI20"].str.strip() if "VTDI20" in gdf.columns else gdf["GEOID20"].str[5:]

    # Ensure MultiPolygon
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: g if g is None or g.geom_type == "MultiPolygon"
        else g.__class__([g]) if g.geom_type == "Polygon"
        else g
    )

    log.info("Loaded %d precincts from VTD shapefile", len(gdf))
    return gdf[["precinct_id", "county_fips", "vtdi", "geometry"]]


def upsert_precinct_geometries(gdf: gpd.GeoDataFrame, engine) -> int:
    """Upsert precinct rows with geometry."""
    log.info("Upserting %d precinct geometries...", len(gdf))
    count = 0
    with engine.begin() as conn:
        for _, row in gdf.iterrows():
            if row["geometry"] is None:
                continue
            conn.execute(text("""
                INSERT INTO precincts (precinct_id, county_name, geom)
                VALUES (
                    :precinct_id,
                    :county_name,
                    ST_Multi(ST_GeomFromText(:wkt, 4326))
                )
                ON CONFLICT (precinct_id) DO UPDATE SET
                    geom = EXCLUDED.geom
            """), {
                "precinct_id": row["precinct_id"],
                "county_name": row["county_fips"],
                "wkt":         row["geometry"].wkt,
            })
            count += 1
            if count % 1000 == 0:
                log.info("  %d precincts upserted...", count)

    log.info("Upsert complete — %d precincts.", count)
    return count


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = download_vtd_shapefile(Path(tmpdir))
        gdf = load_vtd_shapefile(shp_path)
        n = upsert_precinct_geometries(gdf, engine)

    log.info("Script 02 complete — %d precincts loaded.", n)


if __name__ == "__main__":
    main()
