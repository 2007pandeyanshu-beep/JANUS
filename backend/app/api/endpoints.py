"""JANUS API Endpoints

Provides REST endpoints for:
- Health check & system diagnostics
- Retrieving the demonstration scenario (Synthetic Benchmark)
- Retrieving the published scientific case study (Pt/CeO2 WGS Catalysis)
- Retrieving the structured evidence ledger & claims
- Executing deterministic scientific analyses
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.scientific import (
    AnalysisInput,
    AnalysisResult,
    Evidence,
    Experiment,
    BEDCampaignInput,
    BEDCampaignResult,
    BEDPolicyComparisonReport,
)
from scientific.engine import ScientificEngine
from scientific.sequential_engine import SequentialBEDEngine
from scientific.scenarios import get_demo_scenario
from scientific.evidence_ingestion import (
    get_wgs_case_study_scenario,
    load_evidence_ledger,
    load_candidate_experiments,
)
from scientific.validation import ScientificValidationError
from evaluation.benchmark_evaluation import run_reproducible_benchmark, BenchmarkEvaluationReport
from evaluation.sequential_evaluation import run_sequential_policy_comparison

router = APIRouter(prefix="/api", tags=["Scientific Intelligence"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint confirming engine operational readiness."""
    return {
        "status": "online",
        "service": "JANUS Scientific Intelligence Core",
        "version": "0.2.0",
        "engine_mode": "DETERMINISTIC_INFORMATION_THEORETIC",
        "supported_scenarios": [
            "synthetic_benchmark",
            "published_case_study"
        ],
        "active_case_study": "CS-CAT-001 (Pt/CeO2 Low-Temperature WGS)",
        "llm_required": False
    }


@router.get("/scenarios/demo", response_model=AnalysisInput)
def get_demo():
    """
    Returns the synthetic kinase pathway benchmark scenario.
    All data is explicitly flagged with is_synthetic=True.
    """
    return get_demo_scenario()


@router.get("/scenarios/case-study", response_model=AnalysisInput)
def get_case_study():
    """
    Returns the peer-reviewed published case study on Pt/CeO2 Water-Gas Shift catalysis.
    All claims are verified against primary literature (Kalamaras 2011, Meunier 2007, Rodriguez 2007, Burch 2006).
    is_synthetic is False.
    """
    try:
        return get_wgs_case_study_scenario()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load case study package: {str(e)}"
        )


@router.get("/evidence/ledger", response_model=List[Evidence])
def get_evidence():
    """Retrieves the full evidence ledger containing claim-level primary source citations and DOIs."""
    try:
        return load_evidence_ledger()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load evidence ledger: {str(e)}"
        )


@router.get("/experiments/candidates", response_model=List[Experiment])
def get_candidates():
    """Retrieves candidate experiments including quantified and unquantified proposals."""
    try:
        return load_candidate_experiments()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load candidate experiments: {str(e)}"
        )


@router.get("/evaluation/benchmark", response_model=BenchmarkEvaluationReport)
def get_benchmark_evaluation(seed: int = 42, samples: int = 10000):
    """
    Returns reproducible benchmark evaluation comparing JANUS against
    Random Selection and Heuristic policies on CS-CAT-001.
    """
    try:
        return run_reproducible_benchmark(seed=seed, monte_carlo_samples=samples)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark evaluation failed: {str(e)}"
        )


@router.post("/analysis/run", response_model=AnalysisResult)
def run_analysis(payload: AnalysisInput):
    """
    Executes deterministic experiment selection on user-supplied or case-study hypotheses.
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


@router.post("/sequential/run", response_model=BEDCampaignResult)
def run_sequential_campaign(payload: BEDCampaignInput):
    """
    Executes a multi-step closed-loop Sequential Bayesian Experimental Design (BED) campaign.
    Simulates Nature's hidden hypothesis and physical feasibility while isolating the policy.
    """
    try:
        if payload.custom_scenario:
            scenario = payload.custom_scenario
        elif payload.scenario_id == "demo":
            scenario = get_demo_scenario()
        else:
            scenario = get_wgs_case_study_scenario()
            
        return SequentialBEDEngine.run_campaign(scenario, payload)
    except ScientificValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Scientific Validation Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sequential BED Campaign Failed: {str(e)}"
        )


@router.post("/sequential/compare", response_model=BEDPolicyComparisonReport)
def compare_sequential_policies(
    scenario_id: str = "CS-CAT-001",
    hidden_hypothesis_id: str = "H1",
    seed: int = 42,
    budget: float = 10.0,
    max_steps: int = 8,
    confidence_threshold: float = 0.95
):
    """
    Runs a matched-seed comparative evaluation of all 6 sequential experiment selection policies.
    """
    try:
        if scenario_id == "demo":
            scenario = get_demo_scenario()
        else:
            scenario = get_wgs_case_study_scenario()
            
        return run_sequential_policy_comparison(
            scenario=scenario,
            hidden_hypothesis_id=hidden_hypothesis_id,
            seed=seed,
            budget=budget,
            max_steps=max_steps,
            confidence_threshold=confidence_threshold
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy Comparison Failed: {str(e)}"
        )
