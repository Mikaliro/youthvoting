-- Youth Voter Outreach — PostgreSQL + PostGIS schema
-- Run once against a fresh database: psql $DATABASE_URL -f schema.sql

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ---------------------------------------------------------------------------
-- census_block_groups
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS census_block_groups (
    id           SERIAL PRIMARY KEY,
    geoid        VARCHAR(12) NOT NULL UNIQUE,
    county_fips  VARCHAR(5)  NOT NULL,
    total_pop    INTEGER,
    pop_18_29    INTEGER,
    youth_share  DOUBLE PRECISION,
    geom         GEOMETRY(MultiPolygon, 4326),
    acs_vintage  INTEGER NOT NULL  -- e.g. 2022
);

CREATE INDEX IF NOT EXISTS idx_cbg_geom        ON census_block_groups USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cbg_county_fips ON census_block_groups (county_fips);

-- ---------------------------------------------------------------------------
-- election_results
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS election_results (
    id            SERIAL PRIMARY KEY,
    election_date DATE        NOT NULL,
    county_name   VARCHAR(50) NOT NULL,
    precinct_id   VARCHAR(50) NOT NULL,
    contest_name  VARCHAR(100) NOT NULL,
    dem_votes     INTEGER NOT NULL DEFAULT 0,
    rep_votes     INTEGER NOT NULL DEFAULT 0,
    total_votes   INTEGER NOT NULL DEFAULT 0,
    dem_pct       DOUBLE PRECISION,
    dem_margin    DOUBLE PRECISION  -- dem_pct - rep_pct (−1 to +1)
);

CREATE INDEX IF NOT EXISTS idx_er_precinct_id    ON election_results (precinct_id);
CREATE INDEX IF NOT EXISTS idx_er_county_contest ON election_results (county_name, contest_name);

-- ---------------------------------------------------------------------------
-- pipeline_runs  (audit log)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id               SERIAL PRIMARY KEY,
    status           VARCHAR(20)  NOT NULL DEFAULT 'running',  -- running | success | failed
    config_snapshot  JSONB,
    precincts_scored INTEGER,
    error_message    TEXT,
    started_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    finished_at      TIMESTAMPTZ
);

-- ---------------------------------------------------------------------------
-- precincts  (scored output — rebuilt each pipeline run)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS precincts (
    id               SERIAL PRIMARY KEY,
    precinct_id      VARCHAR(50)  NOT NULL UNIQUE,
    county_name      VARCHAR(50)  NOT NULL,
    cd_number        INTEGER,                     -- Congressional district 1–52

    -- Two geometry columns: full res + simplified for fast API responses
    geom             GEOMETRY(MultiPolygon, 4326),
    geom_simplified  GEOMETRY(MultiPolygon, 4326),

    -- Demographics (interpolated from ACS block groups)
    total_pop        INTEGER,
    pop_18_29        INTEGER,
    youth_share      DOUBLE PRECISION,

    -- Election results
    dem_votes        INTEGER,
    rep_votes        INTEGER,
    total_votes      INTEGER,
    dem_pct          DOUBLE PRECISION,
    dem_margin       DOUBLE PRECISION,

    -- Composite score (0–1) and tier label
    score            DOUBLE PRECISION,
    tier             VARCHAR(20),  -- priority | target | watchlist | low

    -- Audit linkage
    pipeline_run_id  INTEGER REFERENCES pipeline_runs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_precincts_geom             ON precincts USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_precincts_geom_simplified  ON precincts USING GIST (geom_simplified);
CREATE INDEX IF NOT EXISTS idx_precincts_cd_number        ON precincts (cd_number);
CREATE INDEX IF NOT EXISTS idx_precincts_tier             ON precincts (tier);
CREATE INDEX IF NOT EXISTS idx_precincts_score            ON precincts (score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_precincts_youth_share      ON precincts (youth_share);
CREATE INDEX IF NOT EXISTS idx_precincts_dem_margin       ON precincts (dem_margin);
