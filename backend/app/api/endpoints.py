"""JANUS API Endpoints

Provides REST endpoints for:
- Health check & system diagnostics
- Retrieving the demonstration scenario
- Executing deterministic scientific analyses
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.scientific import AnalysisInput, AnalysisResult
from scientific.engine import ScientificEngine
from scientific.scenarios import get_demo_scenario
from scientific.validation import ScientificValidationError

router = APIRouter(prefix="/api", tags=["Scientific Intelligence"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint confirming engine operational readiness."""
    return {
        "status": "online",
        "service": "JANUS Scientific Intelligence Core",
        "version": "0.1.0",
        "engine_mode": "DETERMINISTIC_INFORMATION_THEORETIC",
        "llm_required": False
    }


@router.get("/scenarios/demo", response_model=AnalysisInput)
def get_demo():
    """
    Returns the synthetic kinase pathway benchmark scenario.
    All data is clearly flagged with is_synthetic=True.
    """
    return get_demo_scenario()


@router.post("/analysis/run", response_model=AnalysisResult)
def run_analysis(payload: AnalysisInput):
    """
    Executes deterministic experiment selection on user-supplied or demo hypotheses.
    Computes Shannon entropy, Bayes posterior matrices, EIG, and composite rankings.
    """
    try:
        result = ScientificEngine.execute_analysis(payload)
        return result
    except ScientificValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Scientific Validation Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis Execution Failed: {str(e)}"
        )
