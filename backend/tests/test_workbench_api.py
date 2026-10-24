"""Focused API Tests for Scientific Decision Workbench (Phase 7)"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.schemas.scientific import AnalysisInput, Hypothesis, Experiment, PredictedOutcome

client = TestClient(app)


def test_get_oer_scenario_endpoint():
    """Verify that CS-OER-002 scenario can be fetched via API for the workbench."""
    response = client.get("/api/scenarios/oer")
    assert response.status_code == 200
    data = response.json()
    assert "Perovskite" in data["scenario_name"]
    assert data["case_study_id"] == "CS-OER-002"
    assert len(data["hypotheses"]) == 3
    assert len(data["experiments"]) == 5
    
    # Check frozen priors (0.35, 0.45, 0.20)
    priors = {h["id"]: h["prior"] for h in data["hypotheses"]}
    assert abs(priors["H1"] - 0.35) < 1e-6
    assert abs(priors["H2"] - 0.45) < 1e-6
    assert abs(priors["H3"] - 0.20) < 1e-6
    assert abs(sum(priors.values()) - 1.0) < 1e-6


def test_custom_workbench_scenario_analysis():
    """
    Verify that a researcher can construct a custom scientific question with
    hypotheses and candidate experiments in the workbench, and obtain exact EIG rankings.
    """
    custom_scenario = {
        "scenario_name": "Custom Enzymatic Catalysis Mechanism",
        "scenario_type": "synthetic_benchmark",
        "is_synthetic": True,
        "cost_weight": 0.1,
        "hypotheses": [
            {
                "id": "H_PINGPONG",
                "name": "Ping-Pong Bi-Bi Mechanism",
                "description": "Substrate A binds, product P releases before substrate B binds",
                "prior": 0.60,
                "assumptions": ["Substrate saturation at 37C"],
                "evidence_ids": [],
                "status": "active"
            },
            {
                "id": "H_ORDERED",
                "name": "Ordered Sequential Bi-Bi Mechanism",
                "description": "Both substrates bind in obligate sequence before products release",
                "prior": 0.40,
                "assumptions": ["Substrate saturation at 37C"],
                "evidence_ids": [],
                "status": "active"
            }
        ],
        "experiments": [
            {
                "id": "EXP_PARALLEL_LINE",
                "name": "Double Reciprocal Lineweaver-Burk Assay",
                "description": "Vary substrate A at multiple fixed concentrations of B",
                "quantification_status": "QUANTIFIED_BAYESIAN",
                "possible_outcomes": ["parallel_lines", "intersecting_lines"],
                "predictions": [
                    {"outcome_label": "parallel_lines", "hypothesis_id": "H_PINGPONG", "probability": 0.95},
                    {"outcome_label": "intersecting_lines", "hypothesis_id": "H_PINGPONG", "probability": 0.05},
                    {"outcome_label": "parallel_lines", "hypothesis_id": "H_ORDERED", "probability": 0.08},
                    {"outcome_label": "intersecting_lines", "hypothesis_id": "H_ORDERED", "probability": 0.92}
                ],
                "cost": 1.5,
                "feasibility": 0.95,
                "assumptions": ["Initial rate steady state holds"],
                "is_feasible": True
            },
            {
                "id": "EXP_DEAD_END",
                "name": "Dead-End Competitive Inhibition Assay",
                "description": "Inhibit with non-reactive substrate analogue",
                "quantification_status": "QUANTIFIED_BAYESIAN",
                "possible_outcomes": ["competitive_pattern", "mixed_pattern"],
                "predictions": [
                    {"outcome_label": "competitive_pattern", "hypothesis_id": "H_PINGPONG", "probability": 0.50},
                    {"outcome_label": "mixed_pattern", "hypothesis_id": "H_PINGPONG", "probability": 0.50},
                    {"outcome_label": "competitive_pattern", "hypothesis_id": "H_ORDERED", "probability": 0.50},
                    {"outcome_label": "mixed_pattern", "hypothesis_id": "H_ORDERED", "probability": 0.50}
                ],
                "cost": 0.8,
                "feasibility": 0.99,
                "assumptions": ["Analogue does not denature enzyme"],
                "is_feasible": True
            }
        ],
        "evidence": []
    }
    
    response = client.post("/api/analysis/run", json=custom_scenario)
    assert response.status_code == 200
    data = response.json()
    assert data["validation_status"] == "VALIDATED_DETERMINISTIC"
    assert len(data["ranked_experiments"]) == 2
    
    # Lineweaver-Burk should rank #1 with high EIG
    top = data["ranked_experiments"][0]
    assert top["experiment_id"] == "EXP_PARALLEL_LINE"
    assert top["rank"] == 1
    assert top["expected_information_gain"] > 0.5  # Strong disambiguation
    assert top["is_informative"] is True
    
    # Dead-end assay has identical predictions (0.5/0.5), so EIG must be 0.0
    second = data["ranked_experiments"][1]
    assert second["experiment_id"] == "EXP_DEAD_END"
    assert abs(second["expected_information_gain"]) < 1e-6
    assert second["is_informative"] is False
    
    # Check posterior matrix for top experiment
    posteriors = top["posterior_matrix"]
    assert "parallel_lines" in posteriors
    assert "intersecting_lines" in posteriors
    # If parallel lines observed, H_PINGPONG posterior should be very high
    assert posteriors["parallel_lines"]["H_PINGPONG"] > 0.90
    # If intersecting lines observed, H_ORDERED posterior should be very high
    assert posteriors["intersecting_lines"]["H_ORDERED"] > 0.90


def test_workbench_unnormalized_prior_normalization():
    """Verify that unnormalized valid priors entered by researcher (sum != 1.0) are safely normalized with audit warning."""
    custom_scenario = {
        "scenario_name": "Unnormalized Priors Test",
        "hypotheses": [
            {"id": "H1", "name": "Hypothesis 1", "description": "Desc 1", "prior": 0.30, "assumptions": [], "evidence_ids": [], "status": "active"},
            {"id": "H2", "name": "Hypothesis 2", "description": "Desc 2", "prior": 0.60, "assumptions": [], "evidence_ids": [], "status": "active"}
        ],
        "experiments": [
            {
                "id": "EXP1",
                "name": "Test Assay",
                "description": "Desc",
                "possible_outcomes": ["pos", "neg"],
                "predictions": [
                    {"outcome_label": "pos", "hypothesis_id": "H1", "probability": 0.8},
                    {"outcome_label": "neg", "hypothesis_id": "H1", "probability": 0.2},
                    {"outcome_label": "pos", "hypothesis_id": "H2", "probability": 0.1},
                    {"outcome_label": "neg", "hypothesis_id": "H2", "probability": 0.9}
                ],
                "cost": 1.0,
                "feasibility": 1.0
            }
        ]
    }
    response = client.post("/api/analysis/run", json=custom_scenario)
    assert response.status_code == 200
    data = response.json()
    assert abs(data["normalized_priors"]["H1"] - (0.3 / 0.9)) < 1e-4
    assert abs(data["normalized_priors"]["H2"] - (0.6 / 0.9)) < 1e-4
    assert any("normalized" in w.lower() for w in data["warnings"])


def test_sequential_run_with_oer_scenario():
    """Verify sequential campaign execution endpoint accepts CS-OER-002."""
    payload = {
        "scenario_id": "CS-OER-002",
        "policy": "janus_utility",
        "hidden_hypothesis_id": "H1",
        "seed": 42,
        "budget": 10.0,
        "max_steps": 4,
        "confidence_threshold": 0.95
    }
    response = client.post("/api/sequential/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["policy_name"] == "janus_utility"
    assert data["hidden_hypothesis_id"] == "H1"
    assert data["total_steps"] >= 1
