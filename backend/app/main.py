"""JANUS Backend Application

FastAPI entry point for JANUS: Discriminative Experiment Selection for Competing Hypotheses.
"""

import sys
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
    version="0.1.0"
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local Vite dev server on any port
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
