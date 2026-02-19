from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import precincts, districts, config, export

app = FastAPI(
    title="Youth Voter Outreach API",
    version="1.0.0",
    description="California youth voter outreach data pipeline and dashboard API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(precincts.router, prefix="/api")
app.include_router(districts.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.get("/healthz")
def health_check():
    return {"status": "ok"}
