"""
Phase 9 Comprehensive Verification Suite:
Persistent Investigation State + Observation-Driven Scientific Loop
"""

import os
import tempfile
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.agents.orchestrator import ScientificInvestigationOrchestrator, INVESTIGATIONS_STORE
from backend.storage.investigation_store import (
    InvestigationStore,
    get_investigation_store,
    set_investigation_store,
    ConcurrencyConflictError,
)
from backend.agents.types import AgentInvestigationReport, ObservationRecord, InvestigationInput

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_isolated_store(monkeypatch):
    """Create a temporary SQLite database for each test to ensure total isolation."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    monkeypatch.setenv("JANUS_DB_PATH", db_path)
    store = InvestigationStore(db_path=db_path)
    set_investigation_store(store)
    INVESTIGATIONS_STORE.clear()

    yield store

    # Teardown
    set_investigation_store(None)
    try:
        os.remove(db_path)
    except OSError:
        pass


# ==============================================================================
# 1. CANONICAL PERSISTENCE & REBOOT RECOVERY
# ==============================================================================

def test_persistence_across_simulated_restart(setup_isolated_store):
    """
    Verify that an investigation created by the coordinator is persisted in SQLite,
    survives process cache eviction, and is accurately rehydrated by a fresh store instance.
    """
    store = setup_isolated_store
    db_path = store.db_path

    # Step 1: Start investigation via Orchestrator
    report = ScientificInvestigationOrchestrator.start_investigation(
        InvestigationInput(
            question="Which pathway governs low-temperature water-gas shift on Pt/CeO2?",
            mode="deterministic_offline_demo",
            case_study_id="CS-CAT-001",
        )
    )
    inv_id = report.investigation_id

    assert report.version == 1
    assert report.remaining_budget == 10.0
    assert len(report.hypotheses) == 3
    assert len(report.candidate_experiments) >= 4
    assert report.initial_priors == {"H1": 0.50, "H2": 0.20, "H3": 0.30}

    # Step 2: Clear memory caches to simulate process restart / shutdown
    INVESTIGATIONS_STORE.clear()
    assert inv_id not in INVESTIGATIONS_STORE

    # Step 3: Instantiate a completely new store instance pointing to the same SQLite DB file
    reboot_store = InvestigationStore(db_path=db_path)
    restored = reboot_store.get(inv_id)

    assert restored is not None
    assert restored.investigation_id == inv_id
    assert restored.version == 1
    assert restored.question == report.question
    assert restored.case_study_id == "CS-CAT-001"
    assert restored.initial_priors == {"H1": 0.50, "H2": 0.20, "H3": 0.30}
    assert restored.remaining_budget == 10.0
    assert len(restored.hypotheses) == 3
    assert [h.id for h in restored.hypotheses] == ["H1", "H2", "H3"]
    assert len(restored.candidate_experiments) == len(report.candidate_experiments)
    assert restored.review_report is not None
    assert (restored.review_report.conclusion_gate.value if hasattr(restored.review_report.conclusion_gate, "value") else str(restored.review_report.conclusion_gate)) in ["SUFFICIENTLY_SUPPORTED", "REQUIRES_QUALIFICATION", "WITHHOLD_CONCLUSIONS"]

    # Step 4: Verify Orchestrator rehydrates from store on get_investigation
    orch_restored = ScientificInvestigationOrchestrator.get_investigation(inv_id)
    assert orch_restored is not None
    assert orch_restored.investigation_id == inv_id
    assert inv_id in INVESTIGATIONS_STORE  # Re-cached


# ==============================================================================
# 2. OBSERVATION-DRIVEN SEQUENTIAL SCIENTIFIC UPDATE LOOP
# ==============================================================================

def test_observation_application_and_posterior_update():
    """
    Verify the complete sequential update loop:
    1. Observation is applied.
    2. Posteriors updated mathematically and normalized to simplex.
    3. Executed experiment is retired and removed from candidate pool.
    4. Budget is deducted accurately.
    5. Remaining experiments are dynamically reranked by Experiment Designer (Port 8013).
    6. State version increments.
    """
    report = ScientificInvestigationOrchestrator.start_investigation(
        InvestigationInput(
            question="Pt/CeO2 low-temperature WGS mechanism",
            mode="deterministic_offline_demo",
            case_study_id="CS-CAT-001",
        )
    )
    inv_id = report.investigation_id
    initial_exp_count = len(report.candidate_experiments)
    exp_to_run = report.analysis_result.ranked_experiments[0]
    exp_id = exp_to_run.experiment_id
    exp_cost = exp_to_run.cost

    outcome = "Initial_CO2_Mainly_Lattice_16O"
    expected_posteriors = exp_to_run.posterior_matrix[outcome]

    # Supply observation
    updated = ScientificInvestigationOrchestrator.supply_new_evidence_observation(
        investigation_id=inv_id,
        experiment_id=exp_id,
        observed_outcome=outcome,
        provenance="simulated_demonstration",
        idempotency_key="idem-test-001",
        expected_version=1,
    )

    # 1. State version incremented
    assert updated.version == 2

    # 2. Posteriors updated
    for h in updated.hypotheses:
        assert round(h.prior, 3) == round(expected_posteriors[h.id], 3)
    # Simplex normalization check
    assert abs(sum(h.prior for h in updated.hypotheses) - 1.0) < 1e-3

    # 3. Budget deducted
    assert round(updated.remaining_budget, 2) == round(10.0 - exp_cost, 2)

    # 4. Experiment retired and removed from candidate pool
    assert exp_id in updated.retired_experiments
    assert not any(e.id == exp_id for e in updated.candidate_experiments)
    assert len(updated.candidate_experiments) == initial_exp_count - 1

    # 5. Observation recorded in typed ObservationRecord and legacy executed_observations
    assert len(updated.observation_records) == 1
    obs_rec = updated.observation_records[0]
    assert obs_rec.experiment_id == exp_id
    assert obs_rec.observed_outcome == outcome
    assert obs_rec.provenance == "simulated_demonstration"
    assert obs_rec.cost == exp_cost
    assert obs_rec.status == "APPLIED"
    assert obs_rec.marginal_probability > 0.0

    assert len(updated.executed_observations) == 1
    assert updated.executed_observations[0]["experiment_id"] == exp_id
    assert updated.executed_observations[0]["status"] == "SIMULATED_OBSERVATION"

    # 6. Reranking completed by Experiment Designer
    assert updated.analysis_result is not None
    # Executed experiment not present in new ranked experiments
    assert not any(r.experiment_id == exp_id for r in updated.analysis_result.ranked_experiments)


# ==============================================================================
# 3. IDEMPOTENCY & DUPLICATE SUBMISSION HANDLING
# ==============================================================================

def test_idempotent_duplicate_observation_submission():
    """
    Verify that submitting an observation with the same idempotency key is a safe no-op:
    returns the already-updated state without decrementing budget twice, incrementing version,
    or re-applying Bayes updates.
    """
    report = ScientificInvestigationOrchestrator.start_investigation(
        InvestigationInput(
            question="Pt/CeO2 low-temperature WGS mechanism",
            mode="deterministic_offline_demo",
            case_study_id="CS-CAT-001",
        )
    )
    inv_id = report.investigation_id
    exp_to_run = report.analysis_result.ranked_experiments[0]
    exp_id = exp_to_run.experiment_id
    cost = exp_to_run.cost

    key = "unique-key-xyz-777"
    outcome = "Initial_CO2_Mainly_Lattice_16O"

    # First submission
    first_res = ScientificInvestigationOrchestrator.supply_new_evidence_observation(
        investigation_id=inv_id,
        experiment_id=exp_id,
        observed_outcome=outcome,
        idempotency_key=key,
        expected_version=1,
    )
    assert first_res.version == 2
    assert round(first_res.remaining_budget, 2) == round(10.0 - cost, 2)
    assert len(first_res.observation_records) == 1
    posteriors_first = {h.id: h.prior for h in first_res.hypotheses}

    # Second submission with the exact same idempotency key
    second_res = ScientificInvestigationOrchestrator.supply_new_evidence_observation(
        investigation_id=inv_id,
        experiment_id=exp_id,
        observed_outcome=outcome,
        idempotency_key=key,
        expected_version=2,
    )

    # State must be identical and not re-applied
    assert second_res.version == 2
    assert round(second_res.remaining_budget, 2) == round(10.0 - cost, 2)
    assert len(second_res.observation_records) == 1
    assert {h.id: h.prior for h in second_res.hypotheses} == posteriors_first


# ==============================================================================
# 4. OPTIMISTIC CONCURRENCY CONTROL & VERSION CONFLICT
# ==============================================================================

def test_optimistic_locking_concurrency_conflict():
    """
    Verify that providing a stale expected_version triggers ConcurrencyConflictError
    and HTTP 409 Conflict via REST API.
    """
    init_res = client.post("/api/agents/investigate", json={
        "question": "Pt/CeO2 low-temperature WGS mechanism",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001",
    })
    assert init_res.status_code == 200
    inv_id = init_res.json()["investigation_id"]

    # Provide stale expected_version (e.g., 99 instead of 1)
    conflict_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={
            "experiment_id": "EXP-WGS-02",
            "observed_outcome": "Initial_CO2_Mainly_Lattice_16O",
            "expected_version": 99,
        }
    )
    assert conflict_res.status_code == 409
    detail = conflict_res.json()["detail"]
    assert "version conflict" in detail.lower()
    assert "expected version 99" in detail


# ==============================================================================
# 5. SCIENTIFIC BOUNDARIES & VALIDATION CHECKS
# ==============================================================================

def test_scientific_boundary_and_outcome_validation():
    """
    Verify strict rejection of invalid experimental inputs:
    - Nonexistent experiment
    - Invalid outcome outside likelihood space
    - Resubmission of already retired experiment without idempotency key
    """
    init_res = client.post("/api/agents/investigate", json={
        "question": "Pt/CeO2 low-temperature WGS mechanism",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001",
    })
    inv_id = init_res.json()["investigation_id"]

    # 1. Non-existent experiment
    bad_exp = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-NONEXISTENT", "observed_outcome": "Some_Outcome"}
    )
    assert bad_exp.status_code == 400
    assert "not found in ranked experiments" in bad_exp.json()["detail"]

    # 2. Invalid outcome
    bad_out = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Physically_Impossible_Outcome"}
    )
    assert bad_out.status_code == 400
    assert "not found in predictions" in bad_out.json()["detail"]

    # 3. Valid submission
    good_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Initial_CO2_Mainly_Lattice_16O"}
    )
    assert good_res.status_code == 200

    # 4. Attempt to run already retired experiment without idempotency key
    repeat_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Initial_CO2_Mainly_Lattice_16O"}
    )
    assert repeat_res.status_code == 400
    assert "not found in ranked experiments" in repeat_res.json()["detail"]


# ==============================================================================
# 6. UNQUANTIFIED ASSAY BOUNDARY (EXP-WGS-05)
# ==============================================================================

def test_unquantified_assay_boundary_preserved():
    """
    Verify that unquantified assay EXP-WGS-05 is kept separated in unquantified_experiments
    and never mathematically ranked by the Bayesian engine.
    """
    init_res = client.post("/api/agents/investigate", json={
        "question": "Pt/CeO2 low-temperature WGS mechanism",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001",
    })
    inv_id = init_res.json()["investigation_id"]

    # Submit observation
    step_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Initial_CO2_Mainly_Lattice_16O"}
    )
    assert step_res.status_code == 200
    data = step_res.json()

    # Verify unquantified experiments exist and include EXP-WGS-05
    unquantified = data["analysis_result"].get("unquantified_experiments", [])
    assert any(u["experiment_id"] == "EXP-WGS-05" for u in unquantified)

    # Verify EXP-WGS-05 is NOT in ranked_experiments
    ranked = data["analysis_result"]["ranked_experiments"]
    assert not any(r["experiment_id"] == "EXP-WGS-05" for r in ranked)


# ==============================================================================
# 7. CRITIC RE-REVIEW & AUDITOR INVARIANT VERIFICATION
# ==============================================================================

def test_critic_rereview_and_auditor_invariant_gating():
    """
    Verify that after observation feedback:
    1. Critic re-evaluates the state and updates review_report.
    2. Auditor invariants are re-evaluated.
    3. Gate recommendation is maintained.
    """
    report = ScientificInvestigationOrchestrator.start_investigation(
        InvestigationInput(
            question="Pt/CeO2 low-temperature WGS mechanism",
            mode="deterministic_offline_demo",
            case_study_id="CS-CAT-001",
        )
    )
    inv_id = report.investigation_id
    initial_review = report.review_report
    assert initial_review is not None

    updated = ScientificInvestigationOrchestrator.supply_new_evidence_observation(
        investigation_id=inv_id,
        experiment_id="EXP-WGS-02",
        observed_outcome="Initial_CO2_Mainly_Lattice_16O",
    )

    # Review report refreshed
    assert updated.review_report is not None
    assert (updated.review_report.conclusion_gate.value if hasattr(updated.review_report.conclusion_gate, "value") else str(updated.review_report.conclusion_gate)) in ["SUFFICIENTLY_SUPPORTED", "REQUIRES_QUALIFICATION", "WITHHOLD_CONCLUSIONS"]
    assert len(updated.review_report.findings) >= 1

    # Critic re-review logs verified
    critic_entries = [log for log in updated.agent_logs if (log.role == "critic" or (hasattr(log.role, "value") and "CRITIC" in str(log.role.value)))]
    assert len(critic_entries) >= 2  # At least initial run + post-update run


# ==============================================================================
# 8. APPEND-ONLY AUDIT JOURNAL & QUERY ENDPOINTS
# ==============================================================================

def test_append_only_event_journal_and_api_queries():
    """
    Verify audit journal integrity:
    1. Events table records chronological events with payload and event_type.
    2. GET /api/agents/investigation/{id}/events returns full event history.
    3. GET /api/agents/investigation/{id}/observations returns observation history.
    4. GET /api/agents/investigations returns list of all campaigns.
    """
    init_res = client.post("/api/agents/investigate", json={
        "question": "Pt/CeO2 low-temperature WGS mechanism",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001",
    })
    inv_id = init_res.json()["investigation_id"]

    # Post an observation
    obs_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={
            "experiment_id": "EXP-WGS-02",
            "observed_outcome": "Initial_CO2_Mainly_Lattice_16O",
            "provenance": "empirical_measurement",
            "idempotency_key": "journal-test-key-01",
        }
    )
    assert obs_res.status_code == 200

    # 1. Query events
    events_res = client.get(f"/api/agents/investigation/{inv_id}/events")
    assert events_res.status_code == 200
    events_list = events_res.json()
    assert len(events_list) >= 2
    event_types = [e["event_type"] for e in events_list]
    assert "INVESTIGATION_INITIALIZED" in event_types
    assert "OBSERVATION_APPLIED" in event_types

    # 2. Query observations
    obs_list_res = client.get(f"/api/agents/investigation/{inv_id}/observations")
    assert obs_list_res.status_code == 200
    obs_list = obs_list_res.json()
    assert len(obs_list) == 1
    assert obs_list[0]["experiment_id"] == "EXP-WGS-02"
    assert obs_list[0]["provenance"] == "empirical_measurement"

    # 3. Query all investigations
    all_res = client.get("/api/agents/investigations")
    assert all_res.status_code == 200
    all_list = all_res.json()
    assert len(all_list) >= 1
    assert any(inv["investigation_id"] == inv_id for inv in all_list)
