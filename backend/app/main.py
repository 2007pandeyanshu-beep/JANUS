"""JANUS Backend Application

FastAPI entry point for JANUS: Discriminative Experiment Selection for Competing Hypotheses.
"""

import sys
import os
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router

app = FastAPI(
    title="JANUS Scientific Intelligence API",
    description="Deterministic experiment selection engine to distinguish competing scientific hypotheses.",
    version="0.2.0"
)

# Configure allowed CORS origins (explicit origins prevent credentials/wildcard policy violations)
raw_origins = os.getenv("CORS_ORIGINS", "")
if raw_origins:
    allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "project": "JANUS",
        "description": "Discriminative scientific experiment selection engine",
        "docs": "/docs",
        "health": "/api/health",
        "demo_scenario": "/api/scenarios/demo"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
