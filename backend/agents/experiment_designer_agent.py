"""JANUS Independent Experiment Designer uAgent (Phase 7).

Provides an autonomous, independently running Fetch.ai uAgent dedicated to
Bayesian Experimental Design (BED), information-theoretic candidate scoring,
Expected Information Gain (EIG) evaluation, composite utility ranking, and
sequential experiment re-ranking.

Architecture:
- Native Fetch.ai uAgents Protocol (`janus_experiment_design`, version 1.0.0)
- Independent agent identity and distinct cryptographic address (Port 8013)
- Reuses the authoritative deterministic ScientificEngine and scoring invariants
- Explicit input schemas, parameter validation, and budget constraints
- Preserves the unquantified assay boundary: refuses to fabricate likelihoods
- Distinguishes remote execution from local fallback without fabricating success
"""

import sys
import os
import math
import time
from pathlib import Path

# Prevent local backend/agents directory from shadowing standard library 'types' during direct script execution
_script_dir = os.path.dirname(os.path.abspath(__file__))
if sys.path and sys.path[0] == _script_dir:
    sys.path.pop(0)

_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from uagents import Agent, Context, Protocol
from app.schemas.experiment_design import (
    ExperimentScoreItem,
    ExperimentDesignRequest,
    ExperimentDesignResponse,
)
from app.schemas.scientific import (
    Hypothesis,
    Experiment,
    PredictedOutcome,
    Evidence,
    ExperimentScore,
    AnalysisInput,
    AnalysisResult,
)
from scientific.engine import ScientificEngine
from scientific.constraints import filter_feasible_experiments


experiment_design_proto = Protocol(
    name="janus_experiment_design",
    version="1.0.0"
)


# ==============================================================================
# Pure Deterministic Experiment Design & Ranking Engine Entry Point
# ==============================================================================

def perform_experiment_design(
    request: ExperimentDesignRequest,
    agent_address: str = ""
) -> ExperimentDesignResponse:
    """
    Executes deterministic Bayesian Experimental Design and ranking.
    
    Reuses the authoritative JANUS ScientificEngine, preserving all mathematical
    and information-theoretic axioms (Shannon entropy, EIG bounds, composite utility,
    unquantified assay boundaries, and dual-rank tie breaking).
    """
    t0 = time.perf_counter()
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_trail: List[str] = [
        f"Experiment Designer uAgent ({agent_address or 'in-process'}) received design request.",
        f"Scenario: '{request.scenario_name}' (Case study: {request.case_study_id or 'synthetic'}).",
    ]
    warnings: List[str] = []

    # 1. Validate hypotheses input
    if not request.hypotheses:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ExperimentDesignResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="INSUFFICIENT_CANDIDATES",
            agent_address=agent_address,
            timestamp=now_iso,
            scenario_name=request.scenario_name,
            scenario_type=request.scenario_type,
            case_study_id=request.case_study_id,
            is_synthetic=request.is_synthetic,
            normalized_priors={},
            prior_entropy_bits=0.0,
            cost_weight_alpha=request.cost_weight,
            ranked_experiments=[],
            unquantified_experiments=[],
            top_recommendation=None,
            baseline_comparison=None,
            audit_trail=audit_trail,
            warnings=["No competing hypotheses provided for experimental design."],
            execution_time_ms=elapsed,
        )

    # 2. Validate candidate experiments input
    if not request.candidate_experiments:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ExperimentDesignResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="INSUFFICIENT_CANDIDATES",
            agent_address=agent_address,
            timestamp=now_iso,
            scenario_name=request.scenario_name,
            scenario_type=request.scenario_type,
            case_study_id=request.case_study_id,
            is_synthetic=request.is_synthetic,
            normalized_priors={},
            prior_entropy_bits=0.0,
            cost_weight_alpha=request.cost_weight,
            ranked_experiments=[],
            unquantified_experiments=[],
            top_recommendation=None,
            baseline_comparison=None,
            audit_trail=audit_trail,
            warnings=["No candidate experiments provided to rank."],
            execution_time_ms=elapsed,
        )

    # 3. Convert input dicts/models into strong domain models
    hypotheses_list: List[Hypothesis] = []
    for h in request.hypotheses:
        if isinstance(h, Hypothesis):
            hypotheses_list.append(h)
        elif isinstance(h, dict):
            h_copy = dict(h)
            if "description" not in h_copy or not h_copy["description"]:
                h_copy["description"] = h_copy.get("name", "Hypothesis description")
            hypotheses_list.append(Hypothesis(**h_copy))

    experiments_list: List[Experiment] = []
    for e in request.candidate_experiments:
        if isinstance(e, Experiment):
            experiments_list.append(e)
        elif isinstance(e, dict):
            e_copy = dict(e)
            # Ensure possible_outcomes is a list of strings
            if "possible_outcomes" in e_copy and isinstance(e_copy["possible_outcomes"], list):
                e_copy["possible_outcomes"] = [
                    str(out.outcome_label if hasattr(out, "outcome_label") else (out["outcome_label"] if isinstance(out, dict) and "outcome_label" in out else out))
                    for out in e_copy["possible_outcomes"]
                ]
            # Ensure predictions is a list of PredictedOutcome objects
            if "predictions" in e_copy and isinstance(e_copy["predictions"], list):
                converted_preds = []
                for p in e_copy["predictions"]:
                    if isinstance(p, PredictedOutcome):
                        converted_preds.append(p)
                    elif isinstance(p, dict):
                        p_dict = dict(p)
                        if "outcome" in p_dict and "outcome_label" not in p_dict:
                            p_dict["outcome_label"] = p_dict.pop("outcome")
                        converted_preds.append(PredictedOutcome(**p_dict))
                e_copy["predictions"] = converted_preds
            if "description" not in e_copy or not e_copy["description"]:
                e_copy["description"] = e_copy.get("name", "Experiment description")
            experiments_list.append(Experiment(**e_copy))

    evidence_list: List[Evidence] = []
    for ev in request.evidence:
        if isinstance(ev, Evidence):
            evidence_list.append(ev)
        elif isinstance(ev, dict):
            evidence_list.append(Evidence(**ev))

    # 4. Apply hard feasibility and budget constraints
    feasible_experiments, filter_log = filter_feasible_experiments(
        experiments_list,
        max_cost_budget=request.max_cost_budget
    )
    audit_trail.extend(filter_log)
    if len(feasible_experiments) < len(experiments_list):
        rejected_count = len(experiments_list) - len(feasible_experiments)
        warnings.append(f"Hard feasibility/budget constraint filtered out {rejected_count} candidate assays.")

    if not feasible_experiments:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ExperimentDesignResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="INSUFFICIENT_CANDIDATES",
            agent_address=agent_address,
            timestamp=now_iso,
            scenario_name=request.scenario_name,
            scenario_type=request.scenario_type,
            case_study_id=request.case_study_id,
            is_synthetic=request.is_synthetic,
            normalized_priors={},
            prior_entropy_bits=0.0,
            cost_weight_alpha=request.cost_weight,
            ranked_experiments=[],
            unquantified_experiments=[],
            top_recommendation=None,
            baseline_comparison=None,
            audit_trail=audit_trail,
            warnings=["All candidate experiments were rejected by hard feasibility or budget constraints."],
            execution_time_ms=elapsed,
        )

    # 5. Assemble AnalysisInput and execute authoritative ScientificEngine analysis
    analysis_input = AnalysisInput(
        scenario_name=request.scenario_name,
        scenario_type=request.scenario_type,
        case_study_id=request.case_study_id,
        hypotheses=hypotheses_list,
        experiments=feasible_experiments,
        evidence=evidence_list,
        is_synthetic=request.is_synthetic,
        cost_weight=request.cost_weight,
    )

    try:
        engine_result: AnalysisResult = ScientificEngine.execute_analysis(analysis_input)
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ExperimentDesignResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="INVALID_PARAMETERS",
            agent_address=agent_address,
            timestamp=now_iso,
            scenario_name=request.scenario_name,
            scenario_type=request.scenario_type,
            case_study_id=request.case_study_id,
            is_synthetic=request.is_synthetic,
            normalized_priors={},
            prior_entropy_bits=0.0,
            cost_weight_alpha=request.cost_weight,
            ranked_experiments=[],
            unquantified_experiments=[],
            top_recommendation=None,
            baseline_comparison=None,
            audit_trail=audit_trail,
            warnings=[f"Deterministic engine execution failed: {str(exc)}"],
            execution_time_ms=elapsed,
        )

    # 6. Serialize ranked and unquantified experiment scores
    ranked_dicts = [score.model_dump() for score in engine_result.ranked_experiments]
    unquantified_dicts = [score.model_dump() for score in engine_result.unquantified_experiments]
    top_rec = ranked_dicts[0] if ranked_dicts else None

    baseline_dict = engine_result.baseline_comparison.model_dump() if engine_result.baseline_comparison else None
    audit_trail.extend(engine_result.audit_trail)
    warnings.extend(engine_result.warnings)

    prior_entropy = ranked_dicts[0]["prior_entropy"] if ranked_dicts else (
        unquantified_dicts[0]["prior_entropy"] if unquantified_dicts else 0.0
    )

    # Determine status
    if ranked_dicts:
        status = "DESIGN_COMPLETED"
    elif unquantified_dicts:
        status = "DESIGN_PARTIAL"
    else:
        status = "INSUFFICIENT_CANDIDATES"

    elapsed = (time.perf_counter() - t0) * 1000.0
    return ExperimentDesignResponse(
        correlation_id=request.correlation_id,
        investigation_id=request.investigation_id,
        status=status,
        agent_address=agent_address,
        timestamp=now_iso,
        scenario_name=request.scenario_name,
        scenario_type=request.scenario_type,
        case_study_id=request.case_study_id,
        is_synthetic=request.is_synthetic,
        normalized_priors=engine_result.normalized_priors,
        prior_entropy_bits=prior_entropy,
        cost_weight_alpha=request.cost_weight,
        ranked_experiments=ranked_dicts,
        unquantified_experiments=unquantified_dicts,
        top_recommendation=top_rec,
        baseline_comparison=baseline_dict,
        audit_trail=audit_trail,
        warnings=warnings,
        execution_time_ms=elapsed,
    )


# ==============================================================================
# Protocol Message Handler
# ==============================================================================

@experiment_design_proto.on_message(
    model=ExperimentDesignRequest,
    replies={ExperimentDesignResponse}
)
async def handle_design_request(ctx: Context, sender: str, msg: ExperimentDesignRequest):
    """Handles inbound ExperimentDesignRequest and returns ExperimentDesignResponse."""
    ctx.logger.info(
        f"Received experiment design request for '{msg.scenario_name}' "
        f"from {sender} (Correlation: {msg.correlation_id})"
    )
    response = perform_experiment_design(msg, agent_address=str(ctx.agent.address))
    await ctx.send(sender, response)


# ==============================================================================
# Agent Daemon Construction
# ==============================================================================

def create_experiment_designer_uagent(
    name: str = "janus_experiment_designer",
    seed: Optional[str] = None,
    port: int = 8013,
    endpoint: Optional[List[str]] = None,
    use_mailbox: Optional[bool] = None,
    agentverse_url: Optional[str] = None,
) -> Agent:
    """
    Constructs and returns the configured JANUS Experiment Designer uAgent.
    """
    effective_seed = seed or os.getenv("JANUS_EXPERIMENT_DESIGNER_SEED")
    raw_env_mailbox = os.getenv("JANUS_EXPERIMENT_DESIGNER_USE_MAILBOX")

    if use_mailbox is not None:
        is_mailbox = bool(use_mailbox)
    elif raw_env_mailbox is not None and raw_env_mailbox.strip():
        is_mailbox = raw_env_mailbox.strip().lower() in ("true", "1", "yes")
    else:
        is_mailbox = False

    if is_mailbox:
        if not effective_seed:
            raise ValueError(
                "Agentverse mailbox mode requires a securely configured, persistent identity seed. "
                "Please set the 'JANUS_EXPERIMENT_DESIGNER_SEED' environment variable."
            )
    elif not effective_seed:
        # Isolated evaluation test seed fallback for local and headless test execution
        effective_seed = "janus_designer_isolated_evaluation_seed_phase7"

    agent_kwargs: Dict[str, Any] = {
        "name": name,
        "seed": effective_seed,
        "port": port,
    }

    try:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except Exception:
        pass

    if is_mailbox:
        agent_kwargs["mailbox"] = True
        effective_agentverse = agentverse_url or os.getenv("AGENTVERSE_URL")
        if effective_agentverse:
            agent_kwargs["agentverse"] = effective_agentverse
    else:
        agent_kwargs["mailbox"] = False
        agent_kwargs["endpoint"] = endpoint or [f"http://127.0.0.1:{port}/submit"]

    agent = Agent(**agent_kwargs)
    agent.include(experiment_design_proto)
    return agent


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).resolve().parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()
    except ImportError:
        pass

    designer_port = int(os.getenv("JANUS_EXPERIMENT_DESIGNER_PORT", "8013"))
    agent_instance = create_experiment_designer_uagent(port=designer_port)

    print("=" * 80)
    print("JANUS Independent Experiment Designer uAgent (Phase 7)")
    print("=" * 80)
    print(f"Agent Name:    {agent_instance.name}")
    print(f"Agent Address: {agent_instance.address}")
    print(f"Agent Port:    {designer_port}")
    print(f"Protocol:      janus_experiment_design (v1.0.0)")
    print(f"Endpoint:      http://127.0.0.1:{designer_port}/submit")
    print("Starting daemon server...")
    agent_instance.run()
