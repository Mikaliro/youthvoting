"""
Script 02 — Download TIGER/Line VTD (Voting Tabulation District) shapefiles
for all California counties and load into the precincts table (geometry only).

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

# TIGER/Line VTD shapefile URL template (2020 vintage matches census geographies)
TIGER_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/VTD/"
    "tl_2020_{county_fips}_vtd20.zip"
)

# All 58 California county FIPS codes (zero-padded)
CA_COUNTY_FIPS = [
    "06001", "06003", "06005", "06007", "06009", "06011", "06013", "06015",
    "06017", "06019", "06021", "06023", "06025", "06027", "06029", "06031",
    "06033", "06035", "06037", "06039", "06041", "06043", "06045", "06047",
    "06049", "06051", "06053", "06055", "06057", "06059", "06061", "06063",
    "06065", "06067", "06069", "06071", "06073", "06075", "06077", "06079",
    "06081", "06083", "06085", "06087", "06089", "06091", "06093", "06095",
    "06097", "06099", "06101", "06103", "06105", "06107", "06109", "06111",
    "06113", "06115",
]


def download_vtd_shapefile(county_fips: str, dest_dir: Path) -> Path | None:
    """Download and extract VTD shapefile zip for a county."""
    url = TIGER_URL.format(county_fips=county_fips)
    zip_path = dest_dir / f"{county_fips}.zip"

    try:
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        extract_dir = dest_dir / county_fips
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        shp_files = list(extract_dir.glob("*.shp"))
        return shp_files[0] if shp_files else None
    except Exception as exc:
        log.warning("Failed to download %s: %s", county_fips, exc)
        return None


def load_county_vtds(shp_path: Path, county_fips: str) -> gpd.GeoDataFrame:
    """Load a county VTD shapefile and normalize columns."""
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs(epsg=4326)

    # TIGER VTD fields: GEOID20, NAME20, COUNTYFP20
    gdf["precinct_id"] = gdf.get("GEOID20", gdf.get("GEOID", county_fips + "_unknown"))
    gdf["county_fips"] = county_fips

    # Ensure MultiPolygon
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: g if g is None or g.geom_type == "MultiPolygon"
        else g.__class__([g]) if g.geom_type == "Polygon" else g
    )

    return gdf[["precinct_id", "county_fips", "geometry"]]


def upsert_precincts_geometry(gdf: gpd.GeoDataFrame, engine) -> int:
    """Upsert precinct rows with geometry into precincts table."""
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
                    ST_Multi(ST_GeomFromText(:geom_wkt, 4326))
                )
                ON CONFLICT (precinct_id) DO UPDATE SET
                    geom = EXCLUDED.geom
            """), {
                "precinct_id": row["precinct_id"],
                "county_name": row["county_fips"],
                "geom_wkt": row["geometry"].wkt,
            })
            count += 1
    return count


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        total = 0

        for county_fips in CA_COUNTY_FIPS:
            log.info("Processing county %s...", county_fips)
            shp_path = download_vtd_shapefile(county_fips, tmp_path)
            if shp_path is None:
                continue

            gdf = load_county_vtds(shp_path, county_fips)
            n = upsert_precincts_geometry(gdf, engine)
            total += n
            log.info("  Loaded %d precincts for %s", n, county_fips)

    log.info("Script 02 complete — %d precincts loaded.", total)


if __name__ == "__main__":
    main()
