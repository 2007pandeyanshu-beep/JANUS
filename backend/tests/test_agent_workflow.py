"""Comprehensive Tests for JANUS Multi-Agent Scientific Investigation (Phase 8)"""

import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_investigation_wgs_deterministic_demo():
    """Verify that full 5-agent investigation loop executes cleanly on CS-CAT-001 in offline demo mode."""
    payload = {
        "question": "Which reaction pathway governs low-temperature water-gas shift on Pt/CeO2?",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001"
    }
    response = client.post("/api/agents/investigate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["investigation_id"].startswith("INV-")
    assert data["case_study_id"] == "CS-CAT-001"

    # 1. Research Agent verified citations
    assert len(data["retrieved_evidence"]) >= 3
    for ev in data["retrieved_evidence"]:
        assert ev["source"]
        assert ev["provenance"]

    # 2. Hypothesis Agent competing mechanisms
    assert len(data["hypotheses"]) == 3
    hyp_ids = [h["id"] for h in data["hypotheses"]]
    assert "H1" in hyp_ids
    assert "H2" in hyp_ids
    assert "H3" in hyp_ids

    # 3. Scientific Tool Agent executed real calculations
    assert len(data["tool_executions"]) >= 4
    tool_names = [t["tool_name"] for t in data["tool_executions"]]
    assert "literature_retrieval" in tool_names
    assert "chemical_kinetics_kie" in tool_names
    assert "janus_information_theoretic_ranking" in tool_names
    assert "simplex_validation" in tool_names

    for t in data["tool_executions"]:
        assert t["execution_time_ms"] >= 0.0
        assert t["status"] in ("SUCCESS", "WARNING")
        assert t["provenance"]

    # 4. Strategy Agent JANUS ranking
    analysis = data["analysis_result"]
    assert analysis is not None
    assert len(analysis["ranked_experiments"]) >= 4
    # EXP-WGS-02 ranks #1 on Pt/CeO2 WGS
    assert analysis["ranked_experiments"][0]["experiment_id"] == "EXP-WGS-02"

    # 5. Critic Agent review items
    assert len(data["critic_review"]) >= 2
    critic_severities = [c["severity"] for c in data["critic_review"]]
    assert "VERIFIED" in critic_severities

    # 6. Agent inspectable activity log
    assert len(data["agent_logs"]) >= 5
    roles_logged = [log["role"] for log in data["agent_logs"]]
    assert "RESEARCH_AGENT" in roles_logged
    assert "HYPOTHESIS_AGENT" in roles_logged
    assert "SCIENTIFIC_TOOL_AGENT" in roles_logged
    assert "EXPERIMENT_STRATEGY_AGENT" in roles_logged
    assert "CRITIC_AGENT" in roles_logged


def test_agent_investigation_oer_deterministic_demo():
    """Verify that multi-agent investigation executes on CS-OER-002."""
    payload = {
        "question": "Which reaction mechanism dominates oxygen evolution on La_{1-x}Sr_xCoO_{3-delta}?",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-OER-002"
    }
    response = client.post("/api/agents/investigate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["case_study_id"] == "CS-OER-002"
    assert len(data["hypotheses"]) == 3
    # EXP-OER-03 ranks #1 on CS-OER-002
    assert data["analysis_result"]["ranked_experiments"][0]["experiment_id"] == "EXP-OER-03"

    # Critic should flag EXP-OER-05 blank control
    control_critic = next((c for c in data["critic_review"] if "EXP-OER-05" in c["target_claim_or_object"]), None)
    assert control_critic is not None
    assert control_critic["severity"] == "NOTE"


def test_agent_missing_key_actionable_error():
    """Verify that live mode without API key returns an actionable error without silent fallback."""
    payload = {
        "question": "Any question",
        "mode": "live_agent_loop",
        "case_study_id": "CS-CAT-001"
    }
    response = client.post("/api/agents/investigate", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "no valid llm api key" in detail.lower()
    assert "deterministic_offline_demo" in detail


def test_agent_evidence_feedback_and_posterior_update():
    """Verify that supplying an observation updates Bayesian posteriors and triggers re-ranking."""
    # 1. Start initial investigation
    payload = {
        "question": "OER mechanism disambiguation",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-OER-002"
    }
    init_res = client.post("/api/agents/investigate", json=payload)
    assert init_res.status_code == 200
    inv_id = init_res.json()["investigation_id"]

    # 2. Supply observation for EXP-OER-03: 'Continuous_Electrode_Mass_Loss'
    obs_payload = {
        "experiment_id": "EXP-OER-03",
        "observed_outcome": "Continuous_Electrode_Mass_Loss"
    }
    update_res = client.post(f"/api/agents/investigation/{inv_id}/evidence", json=obs_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()

    # Priors should have updated
    priors = {h["id"]: h["prior"] for h in updated_data["hypotheses"]}
    assert priors["H2"] > 0.85  # LOM strongly favored by mass loss
    assert priors["H1"] < 0.10

    # EXP-OER-03 should have been executed and removed from candidate pool
    remaining_ids = [e["id"] for e in updated_data["candidate_experiments"]]
    assert "EXP-OER-03" not in remaining_ids

    # New top experiment recommendation
    assert updated_data["analysis_result"]["ranked_experiments"][0]["experiment_id"] == "EXP-OER-02"


def test_get_investigation_by_id():
    """Verify retrieving investigation report by ID."""
    payload = {
        "question": "Pt/CeO2 test retrieval",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001"
    }
    create_res = client.post("/api/agents/investigate", json=payload)
    inv_id = create_res.json()["investigation_id"]

    get_res = client.get(f"/api/agents/investigation/{inv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["investigation_id"] == inv_id

    # 404 on nonexistent ID
    bad_res = client.get("/api/agents/investigation/INV-NONEXISTENT")
    assert bad_res.status_code == 404


def test_phase10_interactive_investigation_lifecycle_with_budget_and_history():
    """Verify Phase 10 demo lifecycle: initial_priors persistence, sequential budget tracking, and observation history."""
    payload = {
        "question": "Which pathway governs low-temperature water-gas shift on Pt/CeO2?",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001",
    }
    init_res = client.post("/api/agents/investigate", json=payload)
    assert init_res.status_code == 200
    data = init_res.json()
    inv_id = data["investigation_id"]

    # Initial state assertions
    assert data["initial_priors"] == {"H1": 0.50, "H2": 0.20, "H3": 0.30}
    assert data["remaining_budget"] == 10.0
    assert data["executed_observations"] == []
    assert data["retired_experiments"] == []

    top_exp = data["analysis_result"]["ranked_experiments"][0]
    assert top_exp["experiment_id"] == "EXP-WGS-02"
    exp_cost = top_exp["cost"]

    # Step 1: Submit simulated observation
    obs_payload = {
        "experiment_id": "EXP-WGS-02",
        "observed_outcome": "Initial_CO2_Mainly_Lattice_16O",
    }
    step1_res = client.post(f"/api/agents/investigation/{inv_id}/evidence", json=obs_payload)
    assert step1_res.status_code == 200
    step1_data = step1_res.json()

    # Budget and history assertions
    assert step1_data["initial_priors"] == {"H1": 0.50, "H2": 0.20, "H3": 0.30}
    assert round(step1_data["remaining_budget"], 2) == round(10.0 - exp_cost, 2)
    assert step1_data["retired_experiments"] == ["EXP-WGS-02"]
    assert len(step1_data["executed_observations"]) == 1
    assert step1_data["executed_observations"][0]["experiment_id"] == "EXP-WGS-02"
    assert step1_data["executed_observations"][0]["observed_outcome"] == "Initial_CO2_Mainly_Lattice_16O"
    assert step1_data["executed_observations"][0]["status"] == "SIMULATED_OBSERVATION"

    # Posterior update: H1 (Redox) should surge given 16O lattice extraction
    h1_prior = next(h["prior"] for h in step1_data["hypotheses"] if h["id"] == "H1")
    assert h1_prior > 0.60

    # Step 2: Next top experiment is EXP-WGS-01
    next_exp = step1_data["analysis_result"]["ranked_experiments"][0]
    assert next_exp["experiment_id"] == "EXP-WGS-01"
    next_cost = next_exp["cost"]

    obs2_payload = {
        "experiment_id": "EXP-WGS-01",
        "observed_outcome": "Formate_Decay_Much_Slower_Than_TOF",
    }
    step2_res = client.post(f"/api/agents/investigation/{inv_id}/evidence", json=obs2_payload)
    assert step2_res.status_code == 200
    step2_data = step2_res.json()

    assert step2_data["initial_priors"] == {"H1": 0.50, "H2": 0.20, "H3": 0.30}
    assert round(step2_data["remaining_budget"], 2) == round(10.0 - exp_cost - next_cost, 2)
    assert "EXP-WGS-02" in step2_data["retired_experiments"]
    assert "EXP-WGS-01" in step2_data["retired_experiments"]
    assert len(step2_data["executed_observations"]) == 2


def test_phase10_synthetic_kinase_scenario_investigation():
    """Verify that SYN-001 preset runs cleanly through multi-agent orchestration."""
    payload = {
        "question": "Disambiguating allosteric vs catalytic kinase inhibition",
        "mode": "deterministic_offline_demo",
        "case_study_id": "SYN-001",
    }
    res = client.post("/api/agents/investigate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "COMPLETED"
    assert data["case_study_id"] == "SYN-001"
    assert len(data["hypotheses"]) == 3
    assert len(data["candidate_experiments"]) >= 3
    assert data["initial_priors"] == {"H1": 0.35, "H2": 0.45, "H3": 0.20}
    assert data["remaining_budget"] == 10.0

    # Verify synthetic audit notice from Critic Agent
    critic_notes = [c for c in data["critic_review"] if "Synthetic" in c["target_claim_or_object"]]
    assert len(critic_notes) >= 1


def test_phase11_invalid_observation_handling_and_state_integrity():
    """Verify that invalid or unsupported observations cannot corrupt investigation state (Phase 11 demo freeze)."""
    payload = {
        "question": "Pt/CeO2 low-temperature WGS",
        "mode": "deterministic_offline_demo",
        "case_study_id": "CS-CAT-001",
    }
    init_res = client.post("/api/agents/investigate", json=payload)
    assert init_res.status_code == 200
    inv_id = init_res.json()["investigation_id"]

    # 1. Invalid experiment ID returns 400 Bad Request
    bad_exp_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-NONEXISTENT", "observed_outcome": "Any_Outcome"}
    )
    assert bad_exp_res.status_code == 400
    assert "not found in ranked experiments" in bad_exp_res.json()["detail"]

    # 2. Invalid outcome for valid experiment returns 400 Bad Request
    bad_outcome_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Fabricated_Fake_Outcome"}
    )
    assert bad_outcome_res.status_code == 400
    assert "not found in predictions" in bad_outcome_res.json()["detail"]

    # 3. Verify state integrity after failed submissions
    check_res = client.get(f"/api/agents/investigation/{inv_id}")
    assert check_res.status_code == 200
    state = check_res.json()
    assert state["remaining_budget"] == 10.0
    assert len(state["executed_observations"]) == 0
    assert len(state["retired_experiments"]) == 0
    assert state["initial_priors"] == {"H1": 0.50, "H2": 0.20, "H3": 0.30}

    # 4. Valid submission succeeds
    good_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Initial_CO2_Mainly_Lattice_16O"}
    )
    assert good_res.status_code == 200
    good_data = good_res.json()
    assert len(good_data["executed_observations"]) == 1
    assert "EXP-WGS-02" in good_data["retired_experiments"]

    # 5. Attempting to re-submit already-retired experiment returns 400
    repeat_res = client.post(
        f"/api/agents/investigation/{inv_id}/evidence",
        json={"experiment_id": "EXP-WGS-02", "observed_outcome": "Initial_CO2_Mainly_Lattice_16O"}
    )
    assert repeat_res.status_code == 400
    assert "not found in ranked experiments" in repeat_res.json()["detail"]


