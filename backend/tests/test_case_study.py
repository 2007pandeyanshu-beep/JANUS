"""Tests for Published Case Study and Evidence Ingestion in JANUS"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from scientific.evidence_ingestion import (
    load_evidence_ledger,
    load_candidate_experiments,
    get_wgs_case_study_scenario,
)
from scientific.engine import ScientificEngine

client = TestClient(app)


def test_evidence_ledger_validation():
    claims = load_evidence_ledger()
    assert len(claims) >= 5
    
    valid_provenances = {
        "empirical_observation",
        "author_interpretation",
        "computational_dft",
        "synthetic_fixture",
        "unquantified_assumption"
    }
    
    for c in claims:
        assert c.id.startswith("CLM-WGS-")
        assert c.provenance in valid_provenances
        assert c.source is not None
        assert len(c.source) > 5
        assert c.confidence >= 0.0 and c.confidence <= 1.0


def test_candidate_experiments_separation():
    experiments = load_candidate_experiments()
    assert len(experiments) >= 5
    
    unquantified = [e for e in experiments if e.quantification_status == "UNQUANTIFIED_NEEDS_MEASUREMENT"]
    quantified = [e for e in experiments if e.quantification_status == "QUANTIFIED_BAYESIAN"]
    
    assert len(unquantified) >= 1
    assert "EXP-WGS-05" in [e.id for e in unquantified]
    
    # Unquantified experiments should have empty predictions to avoid fabricated data
    for u in unquantified:
        assert len(u.predictions) == 0


def test_case_study_deterministic_analysis():
    scenario = get_wgs_case_study_scenario()
    assert scenario.is_synthetic is False
    assert scenario.scenario_type == "published_case_study"
    assert scenario.case_study_id == "CS-CAT-001"
    
    result = ScientificEngine.execute_analysis(scenario)
    assert result.validation_status == "VALIDATED_DETERMINISTIC"
    assert result.is_synthetic is False
    
    # Verify unquantified experiment is routed cleanly without fake scores
    assert len(result.unquantified_experiments) == 1
    unquant = result.unquantified_experiments[0]
    assert unquant.experiment_id == "EXP-WGS-05"
    assert unquant.rank is None
    assert unquant.expected_information_gain == 0.0
    assert unquant.missing_inputs_explanation is not None
    assert "refuses to fabricate" in unquant.missing_inputs_explanation
    
    # Verify quantified experiments
    assert len(result.ranked_experiments) >= 4
    top_exp = result.ranked_experiments[0]
    assert top_exp.rank == 1
    assert top_exp.expected_information_gain > 0.4  # SSITKA / 18O pulses are highly informative
    
    # Verify negative control blank has 0.0 bits EIG
    blank_exp = next(e for e in result.ranked_experiments if e.experiment_id == "EXP-WGS-06")
    assert pytest.approx(blank_exp.expected_information_gain, 1e-4) == 0.0


def test_case_study_api_endpoints():
    res_cs = client.get("/api/scenarios/case-study")
    assert res_cs.status_code == 200
    data_cs = res_cs.json()
    assert data_cs["is_synthetic"] is False
    assert data_cs["scenario_type"] == "published_case_study"
    assert len(data_cs["hypotheses"]) == 3
    assert len(data_cs["evidence"]) >= 5
    
    res_ledger = client.get("/api/evidence/ledger")
    assert res_ledger.status_code == 200
    ledger = res_ledger.json()
    assert len(ledger) >= 5
    assert all("provenance" in item for item in ledger)
    
    res_run = client.post("/api/analysis/run", json=data_cs)
    assert res_run.status_code == 200
    res_data = res_run.json()
    assert res_data["is_synthetic"] is False
    assert len(res_data["unquantified_experiments"]) >= 1
    assert len(res_data["ranked_experiments"]) >= 4
