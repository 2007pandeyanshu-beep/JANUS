"""API Integration Tests for JANUS Backend"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from scientific.scenarios import get_demo_scenario

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["llm_required"] is False
    assert data["engine_mode"] == "DETERMINISTIC_INFORMATION_THEORETIC"


def test_get_demo_scenario():
    response = client.get("/api/scenarios/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["is_synthetic"] is True
    assert len(data["hypotheses"]) >= 2
    assert len(data["experiments"]) >= 3


def test_run_analysis_with_demo_scenario():
    demo = get_demo_scenario()
    payload = demo.model_dump()
    
    response = client.post("/api/analysis/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["validation_status"] == "VALIDATED_DETERMINISTIC"
    assert len(data["ranked_experiments"]) == len(demo.experiments)
    
    # Check top ranked experiment has valid positive EIG
    top_exp = data["ranked_experiments"][0]
    assert top_exp["rank"] == 1
    assert top_exp["expected_information_gain"] > 0.0
    assert "outcome_marginal_probabilities" in top_exp
    assert "posterior_matrix" in top_exp
    assert len(data["audit_trail"]) > 0


def test_run_analysis_validation_failure():
    # Pass invalid payload with only 1 hypothesis
    payload = {
        "scenario_name": "Invalid Single Hypothesis Test",
        "hypotheses": [
            {
                "id": "H1",
                "name": "Single Hypothesis",
                "description": "No competitor",
                "prior": 1.0,
                "assumptions": [],
                "evidence_ids": [],
                "status": "active"
            }
        ],
        "experiments": [],
        "is_synthetic": True,
        "cost_weight": 0.1
    }
    
    response = client.post("/api/analysis/run", json=payload)
    # Pydantic schema validation should reject min_length < 2
    assert response.status_code in (422, 400)


def test_sequential_run_endpoint():
    payload = {
        "scenario_id": "CS-CAT-001",
        "policy": "janus_utility",
        "hidden_hypothesis_id": "H1",
        "seed": 42,
        "budget": 10.0,
        "max_steps": 3,
        "confidence_threshold": 0.95
    }
    response = client.post("/api/sequential/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["policy_name"] == "janus_utility"
    assert data["hidden_hypothesis_id"] == "H1"
    assert data["total_steps"] >= 1
    assert len(data["steps"]) == data["total_steps"]
    assert "final_confidence_in_hidden_hypothesis" in data
    assert "termination_reason" in data


def test_sequential_compare_endpoint():
    response = client.post("/api/sequential/compare?scenario_id=CS-CAT-001&hidden_hypothesis_id=H1&seed=42&budget=8.0&max_steps=3")
    assert response.status_code == 200
    data = response.json()
    assert data["comparison_id"].startswith("SEQ-BENCH-")
    assert len(data["policy_summaries"]) == 6
    assert "summary_verdict" in data
