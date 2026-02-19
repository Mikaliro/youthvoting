# CA Youth Voter Outreach

Data pipeline and dashboard to identify California voting precincts with high
18–29 population that lean Democratic — prioritizing outreach effort by a
composite score of youth share and partisan lean.

## Stack

| Layer     | Technology                                  |
|-----------|---------------------------------------------|
| Frontend  | Next.js 15, Mapbox GL JS 3, Zustand, Tailwind CSS |
| Backend   | FastAPI, SQLAlchemy, GeoAlchemy2            |
| Database  | PostgreSQL 15 + PostGIS                     |
| Hosting   | Render (Blueprint deploy via render.yaml)   |

---

## Project Structure

```
youthvoting/
├── backend/
│   ├── app/           # FastAPI application
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── routers/
│   │   └── schemas/
│   ├── db/
│   │   └── schema.sql  # Run once to initialize PostGIS schema
│   └── scripts/        # ETL pipeline (run in order 01→06)
│       ├── config.py   # Single source of truth for all thresholds
│       ├── 01_fetch_census.py
│       ├── 02_fetch_shapefiles.py
│       ├── 03_fetch_election.py
│       ├── 04_crosswalk.py
│       ├── 05_merge_score.py
│       └── 06_export.py
└── frontend/
    ├── app/
    │   ├── map/page.tsx
    │   └── _components/
    └── hooks/
        └── useFilters.ts
```

---

## Local Setup

### Prerequisites

- Python 3.12
- Node.js 20+
- PostgreSQL 15 with PostGIS extension

### 1. Clone and configure environment

```bash
git clone https://github.com/arlogreer/youthvoting.git
cd youthvoting
cp .env.example .env
# Edit .env with your credentials
```

### 2. Initialize the database

```bash
psql $DATABASE_URL -f backend/db/schema.sql
```

### 3. Start the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Running the Pipeline

Run scripts in order from the `backend/` directory with environment variables set:

```bash
export DATABASE_URL=postgresql://localhost:5432/youthvoting
export CENSUS_API_KEY=your_key_here

cd backend

# 1. Fetch ACS demographics (~5 min)
python scripts/01_fetch_census.py

# 2. Download TIGER/Line VTD shapefiles for all 58 CA counties (~20 min)
python scripts/02_fetch_shapefiles.py

# 3. Fetch CA SoS election results
python scripts/03_fetch_election.py

# 4. Area-weighted spatial join: block groups → precincts (~10 min in PostGIS)
python scripts/04_crosswalk.py

# 5. Compute scores, assign tiers, simplify geometries
python scripts/05_merge_score.py

# 6. Export CSV snapshot (requires pipeline_run_id from pipeline_runs table)
python scripts/06_export.py 1
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check |
| GET | `/api/precincts` | GeoJSON FeatureCollection (filtered) |
| GET | `/api/districts` | Aggregate stats per congressional district |
| GET | `/api/config` | Pipeline threshold constants |
| GET | `/api/export/csv` | Streaming CSV export |

### `/api/precincts` query parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `district` | int | — | Filter to CA-XX congressional district |
| `youth_min` | float | 0.0 | Minimum youth share (0–1) |
| `margin_floor` | float | −1.0 | Minimum Dem margin (−1 to +1) |
| `tier` | string | — | Filter by tier: priority, target, watchlist, low |

---

## Scoring Methodology

```
youth_norm  = (youth_share − 0.15) / (1 − 0.15)
margin_norm = (dem_margin − (−0.10)) / (1 − (−0.10))
score       = 0.60 × youth_norm + 0.40 × margin_norm   (clamped 0–1)
```

Tiers:

| Tier | Score |
|------|-------|
| Priority | ≥ 0.70 |
| Target | ≥ 0.50 |
| Watchlist | ≥ 0.30 |
| Low | < 0.30 |

Thresholds are configurable in `backend/scripts/config.py`.

---

## Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `CENSUS_API_KEY` | Backend (pipeline) | Census Bureau API key |
| `ALLOWED_ORIGINS` | Backend | Comma-separated CORS origins |
| `SECRET_KEY` | Backend | Random secret (32+ hex chars) |
| `NEXT_PUBLIC_API_URL` | Frontend | FastAPI backend URL |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Frontend | Mapbox GL JS public token |

---

## Render Deployment

1. Fork or push this repo to GitHub
2. In the Render dashboard, create a new **Blueprint** from `render.yaml`
3. After initial deploy, set manual env vars in each service dashboard:
   - `youthvoting-api`: `CENSUS_API_KEY`, `ALLOWED_ORIGINS`
   - `youthvoting-frontend`: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_MAPBOX_TOKEN`
4. Run the schema migration against the Render DB:
   ```bash
   psql $RENDER_DATABASE_URL -f backend/db/schema.sql
   ```
5. Run pipeline scripts with Render DB credentials

---

## Verification Checklist

- [ ] `GET /healthz` → `{"status":"ok"}`
- [ ] `GET /api/config` → JSON with threshold values
- [ ] `GET /api/precincts?youth_min=0.15&margin_floor=-0.10` → valid GeoJSON
- [ ] `npm run dev` → map centered on California, sidebar renders
- [ ] Filter sliders update map layers reactively
- [ ] Export CSV button triggers browser download
