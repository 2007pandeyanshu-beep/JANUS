"""Tests for JANUS Independent Experiment Designer uAgent (Phase 7).

Verifies:
1. Protocol schema serialization, deserialization, and parameter boundary validation.
2. Distinct cryptographic identity (address, port 8013, protocol) from coordinator,
   auditor, research, hypothesis analyst, and scientific tool agents.
3. Deterministic Bayesian Experimental Design (BED) and composite utility ranking on
   the low-temperature water-gas shift (Pt/CeO2) benchmark scenario.
4. Feasibility and budget constraint filtering (feasibility score, max budget cutoffs).
5. Dual ranking and tie-breaking order (composite utility desc, experiment ID asc).
6. Preservation of unquantified assay boundaries with zero likelihood fabrication.
7. Roundtrip preservation of correlation_id and investigation_id.
8. Honest offline reporting (DESIGN_UNAVAILABLE, never faking success).
9. Graceful local fallback when daemon is offline with transparent audit trail and fallback flags.
10. Full integration with ScientificInvestigationOrchestrator Stage 4 (experiment ranking).
11. Dynamic re-ranking integration with ScientificInvestigationOrchestrator.record_observation.
12. Live inter-agent request/response message exchange over native Fetch.ai uAgents protocol.
"""

import os
import sys
import math
import time
import asyncio
import threading
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any
from pydantic import ValidationError

# Ensure backend directory is in sys.path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_test_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

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
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.engine import ScientificEngine
from agents.tools import (
    ExperimentDesignerAgentTool,
    ScientificToolAgentTool,
    HypothesisAnalystTool,
    ResearchAgentTool,
    AuditorAgentTool,
)
from agents.experiment_designer_agent import (
    create_experiment_designer_uagent,
    perform_experiment_design,
    experiment_design_proto,
)
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import InvestigationInput, AgentRole


def test_experiment_designer_schemas_and_validation():
    """Verifies that experiment design schemas serialize, deserialize, and enforce validation rules."""
    score_item = ExperimentScoreItem(
        experiment_id="EXP-WGS-02",
        experiment_name="Transient H2(18O) / C(16O) Isotopic Pulse Mass Spectrometry",
        expected_information_gain=0.811,
        cost=1.8,
        feasibility=0.88,
        composite_utility_score=0.321,
        rank=1,
        quantification_status="FULLY_QUANTIFIED",
        explanation="Strong discriminator between Redox and Associative pathways",
    )
    assert score_item.experiment_id == "EXP-WGS-02"
    assert score_item.rank == 1
    assert score_item.composite_utility_score == 0.321

    # Invalid cost weight must raise ValidationError
    with pytest.raises(ValidationError):
        ExperimentDesignRequest(
            correlation_id="corr-err-01",
            investigation_id="INV-ERR-01",
            scenario_name="Test Scenario",
            cost_weight=-0.5,  # Must be >= 0.0
            hypotheses=[
                {"id": "H1", "name": "Hypothesis 1", "description": "Desc 1", "prior": 0.5},
                {"id": "H2", "name": "Hypothesis 2", "description": "Desc 2", "prior": 0.5},
            ],
            candidate_experiments=[],
        )

    # Valid request serialization and round-trip
    req = ExperimentDesignRequest(
        correlation_id="corr-design-01",
        investigation_id="INV-DES-01",
        scenario_name="Water-Gas Shift Pt/CeO2",
        case_study_id="CS-CAT-001",
        cost_weight=0.1,
        hypotheses=[
            {"id": "H1", "name": "Associative Formate", "description": "Formate intermediate pathway", "prior": 0.5},
            {"id": "H2", "name": "Redox Mechanism", "description": "Regenerative Mars-van Krevelen pathway", "prior": 0.5},
        ],
        candidate_experiments=[
            {
                "id": "EXP-01",
                "name": "Test Experiment",
                "cost": 1.0,
                "feasibility": 1.0,
                "possible_outcomes": ["O1", "O2"],
                "predictions": [
                    {"hypothesis_id": "H1", "outcome": "O1", "probability": 0.9},
                    {"hypothesis_id": "H1", "outcome": "O2", "probability": 0.1},
                    {"hypothesis_id": "H2", "outcome": "O1", "probability": 0.1},
                    {"hypothesis_id": "H2", "outcome": "O2", "probability": 0.9},
                ],
            }
        ],
    )
    dumped = req.model_dump()
    assert dumped["correlation_id"] == "corr-design-01"
    assert dumped["scenario_name"] == "Water-Gas Shift Pt/CeO2"

    restored = ExperimentDesignRequest.model_validate(dumped)
    assert restored.investigation_id == "INV-DES-01"
    assert len(restored.hypotheses) == 2
    assert len(restored.candidate_experiments) == 1


def test_experiment_designer_agent_identity_distinct():
    """Verifies that the Experiment Designer uAgent has distinct cryptographic identity, address, and port."""
    agent = create_experiment_designer_uagent(port=8013)

    assert agent.name == "janus_experiment_designer"
    # Port 8013 default test evaluation address
    assert agent.address == "agent1q0qpwtcrpp5cmehgwg2reypzk47qxt9mzhxulj9962qrdj9a8a40keavldj"
    assert experiment_design_proto.name == "janus_experiment_design"
    assert experiment_design_proto.version == "1.0.0"

    # Must be distinct from all other agents in JANUS
    coordinator_addr = "agent1q0hmkpdw4v28hmkkfqa56u2zwx3pzly44z7r8048pjtgw4lq8r5my29pn3t"
    auditor_addr = "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
    research_addr = "agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py"
    analyst_addr = "agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d"
    scientific_tool_addr = "agent1q2lmglm5n5nl8wxrcly6j4w0xts9fa9zh2u8qq8mxf30ya3mfxcpjq6md8t"

    all_addresses = [
        coordinator_addr,
        auditor_addr,
        research_addr,
        analyst_addr,
        scientific_tool_addr,
        agent.address,
    ]
    assert len(set(all_addresses)) == 6, "All 6 JANUS agents must have distinct cryptographic addresses"


def test_deterministic_ranking_wgs_benchmark():
    """Verifies that Bayesian Experimental Design ranking on WGS benchmark matches ground truth exactly."""
    scenario = get_wgs_case_study_scenario()
    req = ExperimentDesignRequest(
        correlation_id="corr-bench-wgs",
        investigation_id="INV-BENCH-01",
        scenario_name=scenario.scenario_name,
        case_study_id=scenario.case_study_id or "CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        candidate_experiments=[e.model_dump() for e in scenario.experiments],
        cost_weight=0.1,
    )

    resp = perform_experiment_design(req, agent_address="agent1q0qpwtcrpp5cmehgwg2reypzk47qxt9mzhxulj9962qrdj9a8a40keavldj")

    assert resp.status == "DESIGN_COMPLETED"
    assert resp.correlation_id == "corr-bench-wgs"
    assert resp.investigation_id == "INV-BENCH-01"
    assert len(resp.ranked_experiments) >= 4

    # Top recommendation must be EXP-WGS-02
    top_rec = resp.top_recommendation
    assert top_rec is not None
    assert top_rec["experiment_id"] == "EXP-WGS-02"
    assert top_rec["rank"] == 1
    assert "Transient" in top_rec["experiment_name"] or "Isotopic" in top_rec["experiment_name"]

    # Invariant: 0 <= EIG <= H(prior)
    h_prior = resp.prior_entropy_bits
    assert h_prior > 1.0  # ~1.585 bits for 3 uniform hypotheses
    for exp_item in resp.ranked_experiments:
        assert 0.0 <= exp_item["expected_information_gain"] <= h_prior + 1e-6
        assert exp_item["composite_utility_score"] >= 0.0


def test_feasibility_and_budget_filtering():
    """Verifies that budget cutoffs and feasibility filtering operate deterministically."""
    scenario = get_wgs_case_study_scenario()

    # Apply strict budget of 1.2
    # EXP-WGS-04 cost=1.1, EXP-WGS-06 cost=0.3 are <= 1.2
    # EXP-WGS-01 cost=1.5, EXP-WGS-02 cost=1.8, EXP-WGS-03 cost=6.5 exceed 1.2
    req_budget = ExperimentDesignRequest(
        correlation_id="corr-budget-01",
        investigation_id="INV-BUDGET-01",
        scenario_name=scenario.scenario_name,
        case_study_id=scenario.case_study_id or "CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        candidate_experiments=[e.model_dump() for e in scenario.experiments],
        cost_weight=0.1,
        max_cost_budget=1.2,
    )
    resp_budget = perform_experiment_design(req_budget, agent_address="agent1test")

    assert resp_budget.status == "DESIGN_COMPLETED"
    feasible_ids = [e["experiment_id"] for e in resp_budget.ranked_experiments]
    assert "EXP-WGS-04" in feasible_ids
    assert "EXP-WGS-02" not in feasible_ids  # cost 1.8 exceeds 1.2
    assert "EXP-WGS-03" not in feasible_ids  # cost 6.5 exceeds 1.2

    # Low feasibility experiment utility test
    zero_feas_exp = {
        "id": "EXP-ZERO-FEAS",
        "name": "Zero Feasibility Experiment",
        "cost": 5.0,
        "feasibility": 0.0,
        "possible_outcomes": ["O1", "O2"],
        "predictions": [
            {"hypothesis_id": "H1", "outcome": "O1", "probability": 0.9},
            {"hypothesis_id": "H1", "outcome": "O2", "probability": 0.1},
            {"hypothesis_id": "H2", "outcome": "O1", "probability": 0.1},
            {"hypothesis_id": "H2", "outcome": "O2", "probability": 0.9},
            {"hypothesis_id": "H3", "outcome": "O1", "probability": 0.5},
            {"hypothesis_id": "H3", "outcome": "O2", "probability": 0.5},
        ],
    }
    req_feas = ExperimentDesignRequest(
        correlation_id="corr-feas-01",
        investigation_id="INV-FEAS-01",
        scenario_name=scenario.scenario_name,
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        candidate_experiments=[zero_feas_exp],
        cost_weight=0.1,
    )
    resp_feas = perform_experiment_design(req_feas, agent_address="agent1test")
    # Feasibility 0.0 is filtered out as infeasible by filter_feasible_experiments
    assert "EXP-ZERO-FEAS" not in [e["experiment_id"] for e in resp_feas.ranked_experiments]


def test_dual_ranking_and_tie_breaking_order():
    """Verifies that experiments are sorted by composite utility descending, with secondary tie-break by ID."""
    hypotheses = [
        {"id": "H1", "name": "H1", "description": "Mechanism 1", "prior": 0.5},
        {"id": "H2", "name": "H2", "description": "Mechanism 2", "prior": 0.5},
    ]
    # Two identical experiments with different IDs
    exp_b = {
        "id": "EXP-B",
        "name": "Experiment B",
        "cost": 1.0,
        "feasibility": 1.0,
        "possible_outcomes": ["O1", "O2"],
        "predictions": [
            {"hypothesis_id": "H1", "outcome": "O1", "probability": 0.9},
            {"hypothesis_id": "H1", "outcome": "O2", "probability": 0.1},
            {"hypothesis_id": "H2", "outcome": "O1", "probability": 0.1},
            {"hypothesis_id": "H2", "outcome": "O2", "probability": 0.9},
        ],
    }
    exp_a = {
        "id": "EXP-A",
        "name": "Experiment A",
        "cost": 1.0,
        "feasibility": 1.0,
        "possible_outcomes": ["O1", "O2"],
        "predictions": [
            {"hypothesis_id": "H1", "outcome": "O1", "probability": 0.9},
            {"hypothesis_id": "H1", "outcome": "O2", "probability": 0.1},
            {"hypothesis_id": "H2", "outcome": "O1", "probability": 0.1},
            {"hypothesis_id": "H2", "outcome": "O2", "probability": 0.9},
        ],
    }
    req = ExperimentDesignRequest(
        correlation_id="corr-tie-01",
        investigation_id="INV-TIE-01",
        scenario_name="Tie Breaking Test",
        hypotheses=hypotheses,
        candidate_experiments=[exp_b, exp_a],  # Input in reverse alphabetical order
        cost_weight=0.1,
    )
    resp = perform_experiment_design(req, agent_address="agent1test")

    assert resp.status == "DESIGN_COMPLETED"
    assert len(resp.ranked_experiments) == 2
    # EXP-A should tie-break before EXP-B
    assert resp.ranked_experiments[0]["experiment_id"] == "EXP-A"
    assert resp.ranked_experiments[0]["rank"] == 1
    assert resp.ranked_experiments[1]["experiment_id"] == "EXP-B"
    assert resp.ranked_experiments[1]["rank"] == 2


def test_unquantified_candidate_boundary_no_fabrication():
    """Verifies that unquantified assay candidates are isolated with EIG=0.0 and never assigned fabricated likelihoods."""
    hypotheses = [
        {"id": "H1", "name": "H1", "description": "Mechanism 1", "prior": 0.5},
        {"id": "H2", "name": "H2", "description": "Mechanism 2", "prior": 0.5},
    ]
    quantified_exp = {
        "id": "EXP-QUANT",
        "name": "Quantified Assay",
        "cost": 1.0,
        "feasibility": 1.0,
        "possible_outcomes": ["O1", "O2"],
        "predictions": [
            {"hypothesis_id": "H1", "outcome": "O1", "probability": 0.8},
            {"hypothesis_id": "H1", "outcome": "O2", "probability": 0.2},
            {"hypothesis_id": "H2", "outcome": "O1", "probability": 0.2},
            {"hypothesis_id": "H2", "outcome": "O2", "probability": 0.8},
        ],
    }
    unquantified_exp = {
        "id": "EXP-UNQUANT",
        "name": "Speculative Assay Without Measurements",
        "description": "Rapid-scan operando assay with uncalibrated transient signals",
        "cost": 2.0,
        "feasibility": 0.5,
        "possible_outcomes": ["Transient_Band_Detected", "No_Band_Detected"],
        "predictions": [],
        "quantification_status": "UNQUANTIFIED_NEEDS_MEASUREMENT",
    }
    req = ExperimentDesignRequest(
        correlation_id="corr-unquant-01",
        investigation_id="INV-UNQUANT-01",
        scenario_name="Unquantified Boundary Test",
        hypotheses=hypotheses,
        candidate_experiments=[quantified_exp, unquantified_exp],
        cost_weight=0.1,
    )
    resp = perform_experiment_design(req, agent_address="agent1test")

    assert resp.status in ("DESIGN_COMPLETED", "DESIGN_PARTIAL")
    assert len(resp.ranked_experiments) == 1
    assert resp.ranked_experiments[0]["experiment_id"] == "EXP-QUANT"

    assert len(resp.unquantified_experiments) == 1
    unq = resp.unquantified_experiments[0]
    assert unq["experiment_id"] == "EXP-UNQUANT"
    assert unq["expected_information_gain"] == 0.0
    assert unq.get("rank") is None
    assert unq["quantification_status"] == "UNQUANTIFIED_NEEDS_MEASUREMENT"
    assert any("unquantified" in w.lower() for w in resp.warnings)


def test_correlation_and_investigation_id_preservation():
    """Verifies that correlation_id and investigation_id are preserved throughout processing."""
    req = ExperimentDesignRequest(
        correlation_id="corr-corr-unique-9999",
        investigation_id="INV-ID-UNIQUE-8888",
        scenario_name="ID Preservation Test",
        hypotheses=[
            {"id": "H1", "name": "H1", "description": "Mechanism 1", "prior": 0.5},
            {"id": "H2", "name": "H2", "description": "Mechanism 2", "prior": 0.5},
        ],
        candidate_experiments=[],
    )
    resp = perform_experiment_design(req, agent_address="agent1test")
    assert resp.correlation_id == "corr-corr-unique-9999"
    assert resp.investigation_id == "INV-ID-UNIQUE-8888"


def test_offline_daemon_handling_and_honest_reporting():
    """Verifies honest DESIGN_UNAVAILABLE reporting when daemon is offline and fallback is disabled."""
    os.environ["JANUS_EXPERIMENT_DESIGNER_ENDPOINT"] = "http://127.0.0.1:59997/submit"
    os.environ["JANUS_EXPERIMENT_DESIGNER_TIMEOUT_SECONDS"] = "1.0"
    try:
        req = ExperimentDesignRequest(
            correlation_id="corr-off-01",
            investigation_id="INV-OFF-01",
            scenario_name="Offline Test",
            hypotheses=[
                {"id": "H1", "name": "H1", "description": "Mechanism 1", "prior": 0.5},
                {"id": "H2", "name": "H2", "description": "Mechanism 2", "prior": 0.5},
            ],
            candidate_experiments=[],
        )
        resp, record = ExperimentDesignerAgentTool.execute_design(
            req,
            timeout=1.0,
            allow_local_fallback=False,
        )

        assert resp.status == "DESIGN_UNAVAILABLE"
        assert record.status == "WARNING"
        assert len(resp.ranked_experiments) == 0
        assert any("non-design" in w.lower() or "offline" in w.lower() or "communication error" in w.lower() or "connection" in w.lower() for w in resp.warnings)
    finally:
        os.environ.pop("JANUS_EXPERIMENT_DESIGNER_ENDPOINT", None)
        os.environ.pop("JANUS_EXPERIMENT_DESIGNER_TIMEOUT_SECONDS", None)


def test_offline_daemon_with_fallback_engaged():
    """Verifies that when daemon is offline and fallback is enabled, local ranking engages honestly."""
    os.environ["JANUS_EXPERIMENT_DESIGNER_ENDPOINT"] = "http://127.0.0.1:59997/submit"
    os.environ["JANUS_EXPERIMENT_DESIGNER_TIMEOUT_SECONDS"] = "1.0"
    try:
        scenario = get_wgs_case_study_scenario()
        req = ExperimentDesignRequest(
            correlation_id="corr-fb-01",
            investigation_id="INV-FB-01",
            scenario_name=scenario.scenario_name,
            case_study_id=scenario.case_study_id or "CS-CAT-001",
            hypotheses=[h.model_dump() for h in scenario.hypotheses],
            candidate_experiments=[e.model_dump() for e in scenario.experiments],
            cost_weight=0.1,
        )
        resp, record = ExperimentDesignerAgentTool.execute_design(
            req,
            timeout=1.0,
            allow_local_fallback=True,
        )

        assert resp.status == "DESIGN_UNAVAILABLE"  # Truthful daemon offline status preserved
        assert record.status == "WARNING"
        assert record.input_arguments.get("fallback_engaged") is True
        assert len(resp.ranked_experiments) >= 4
        assert resp.top_recommendation["experiment_id"] == "EXP-WGS-02"
        assert any("fallback ranking engaged" in w.lower() for w in resp.warnings)
    finally:
        os.environ.pop("JANUS_EXPERIMENT_DESIGNER_ENDPOINT", None)
        os.environ.pop("JANUS_EXPERIMENT_DESIGNER_TIMEOUT_SECONDS", None)


def test_orchestrator_stage4_designer_integration():
    """Verifies that ScientificInvestigationOrchestrator Stage 4 invokes the Experiment Designer uAgent."""
    inp = InvestigationInput(
        question="Which mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inp)

    # Verify tool execution record is present
    designer_rec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_experiment_designer_uagent"), None)
    assert designer_rec is not None, "Stage 4 must invoke janus_independent_experiment_designer_uagent tool"
    assert designer_rec.invoked_by == AgentRole.EXPERIMENT_STRATEGY
    assert "investigation_id" in designer_rec.input_arguments

    # Verify Stage 4 log entries
    designer_logs = [l for l in report.agent_logs if l.role == AgentRole.EXPERIMENT_STRATEGY]
    assert len(designer_logs) >= 1
    assert any("Experiment Designer uAgent" in l.thought for l in designer_logs)

    # Verify ranked experiments and top recommendation
    assert report.analysis_result is not None
    assert len(report.analysis_result.ranked_experiments) >= 4
    assert report.analysis_result.ranked_experiments[0].experiment_id == "EXP-WGS-02"


def test_orchestrator_observation_reranking_designer_integration():
    """Verifies that ScientificInvestigationOrchestrator.supply_new_evidence_observation invokes Experiment Designer for re-ranking."""
    inp = InvestigationInput(
        question="Which mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    initial_report = ScientificInvestigationOrchestrator.start_investigation(inp)
    inv_id = initial_report.investigation_id

    # Record an observation from top experiment EXP-WGS-02
    updated_report = ScientificInvestigationOrchestrator.supply_new_evidence_observation(
        investigation_id=inv_id,
        experiment_id="EXP-WGS-02",
        observed_outcome="Initial_CO2_Mainly_Lattice_16O",
    )

    # Verify updated investigation state
    assert updated_report.investigation_id == inv_id
    assert len(updated_report.executed_observations) == 1
    assert updated_report.executed_observations[0]["experiment_id"] == "EXP-WGS-02"

    # Verify Experiment Designer re-ranking tool execution record
    designer_recs = [t for t in updated_report.tool_executions if t.tool_name == "janus_independent_experiment_designer_uagent"]
    assert len(designer_recs) >= 2, "Must contain initial design and re-ranking design tool executions"
    assert updated_report.analysis_result is not None
    assert len(updated_report.analysis_result.ranked_experiments) >= 3


def test_live_experiment_designer_inter_agent_communication_cycle():
    """
    Spins up the Independent Experiment Designer uAgent on an ephemeral port (8093),
    sends a real synchronous ExperimentDesignRequest over the native Fetch.ai protocol,
    and asserts structured DESIGN_COMPLETED response.
    """
    test_port = 8093
    test_endpoint = f"http://127.0.0.1:{test_port}/submit"

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ag = create_experiment_designer_uagent(
            name="test_live_experiment_designer",
            port=test_port,
            endpoint=[test_endpoint],
        )
        ag.run()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    time.sleep(2.0)  # Wait for uAgent socket binding

    os.environ["JANUS_EXPERIMENT_DESIGNER_ADDRESS"] = "agent1q0qpwtcrpp5cmehgwg2reypzk47qxt9mzhxulj9962qrdj9a8a40keavldj"
    os.environ["JANUS_EXPERIMENT_DESIGNER_ENDPOINT"] = test_endpoint
    try:
        scenario = get_wgs_case_study_scenario()
        req = ExperimentDesignRequest(
            correlation_id="corr-live-designer-01",
            investigation_id="INV-LIVE-DES-CYCLE",
            scenario_name=scenario.scenario_name,
            case_study_id=scenario.case_study_id or "CS-CAT-001",
            hypotheses=[h.model_dump() for h in scenario.hypotheses],
            candidate_experiments=[e.model_dump() for e in scenario.experiments],
            cost_weight=0.1,
        )
        resp, record = ExperimentDesignerAgentTool.execute_design(
            req,
            timeout=6.0,
            allow_local_fallback=False,
        )

        assert resp.status == "DESIGN_COMPLETED"
        assert resp.agent_address == "agent1q0qpwtcrpp5cmehgwg2reypzk47qxt9mzhxulj9962qrdj9a8a40keavldj"
        assert len(resp.ranked_experiments) >= 4
        assert resp.top_recommendation is not None
        assert resp.top_recommendation["experiment_id"] == "EXP-WGS-02"
        assert record.status == "SUCCESS"
        assert record.tool_name == "janus_independent_experiment_designer_uagent"
        assert any("Experiment Designer uAgent" in trail for trail in resp.audit_trail)
    finally:
        os.environ.pop("JANUS_EXPERIMENT_DESIGNER_ADDRESS", None)
        os.environ.pop("JANUS_EXPERIMENT_DESIGNER_ENDPOINT", None)
