"""Comprehensive Tests for JANUS Phase 9: Agentic Value Evaluation"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from evaluation.agentic_value_evaluation import AgenticValueEvaluator

client = TestClient(app)


def test_stochastic_baseline_regret_is_positive():
    """Verify that uniform random selection has strictly positive regret and is never reported as zero."""
    for case_id in ["CS-CAT-001", "CS-OER-002", "SYN-001"]:
        summary = AgenticValueEvaluator.evaluate_case(case_id)
        rand_pipeline = next(p for p in summary.pipelines if p.workflow_name == "uniform_random")
        assert rand_pipeline.eig_regret_bits > 0.10, f"Random regret must be > 0.10 bits on {case_id}"
        expected_diff = summary.ground_truth_optimal_eig - rand_pipeline.eig_bits
        assert abs(rand_pipeline.eig_regret_bits - expected_diff) < 1e-3


def test_citation_validity_metric():
    """Verify that curated citations are distinguished from LLM citations and have verified DOIs."""
    summary_wgs = AgenticValueEvaluator.evaluate_case("CS-CAT-001")
    c_wgs = summary_wgs.citation_metric
    assert c_wgs.curated_citations_count >= 3
    assert c_wgs.curated_validity_rate == 1.0
    assert c_wgs.curated_verified_dois_count == c_wgs.curated_citations_count
    assert c_wgs.llm_fabricated_citations_count == 0

    summary_oer = AgenticValueEvaluator.evaluate_case("CS-OER-002")
    c_oer = summary_oer.citation_metric
    assert c_oer.curated_citations_count >= 3
    assert c_oer.curated_validity_rate == 1.0
    assert c_oer.curated_verified_dois_count == c_oer.curated_citations_count
    assert c_oer.llm_fabricated_citations_count == 0


def test_hypothesis_simplex_consistency():
    """Verify that prior distributions satisfy the mathematical probability simplex constraint sum=1.0."""
    for case_id in ["CS-CAT-001", "CS-OER-002", "SYN-001"]:
        summary = AgenticValueEvaluator.evaluate_case(case_id)
        h_metric = summary.hypothesis_metric
        assert h_metric.is_simplex_valid is True
        assert h_metric.simplex_error < 1e-4
        assert abs(h_metric.simplex_sum - 1.0) < 1e-4
        assert h_metric.prior_entropy_bits > 0.0


def test_recommendation_equivalence():
    """Verify that the multi-agent workflow selects the exact same optimal experiment as the authoritative non-agentic engine."""
    for case_id in ["CS-CAT-001", "CS-OER-002", "SYN-001"]:
        summary = AgenticValueEvaluator.evaluate_case(case_id)
        rec = summary.recommendation_metric
        assert rec.matches_optimal_pick is True
        assert rec.recommended_experiment_id == summary.ground_truth_optimal_id
        assert rec.eig_regret_bits == 0.0
        assert abs(rec.recommended_eig_bits - summary.ground_truth_optimal_eig) < 1e-3


def test_critic_waste_filtering():
    """Verify that the Critic Agent successfully flags uninformative blank controls and unquantified proposals."""
    # CS-CAT-001 should flag unquantified EXP-WGS-05
    summary_wgs = AgenticValueEvaluator.evaluate_case("CS-CAT-001")
    assert summary_wgs.filtering_metric.unquantified_proposals_flagged == 1
    assert any("EXP-WGS-05" in ent for ent in summary_wgs.filtering_metric.flagged_entities)

    # CS-OER-002 should flag blank control EXP-OER-05
    summary_oer = AgenticValueEvaluator.evaluate_case("CS-OER-002")
    assert summary_oer.filtering_metric.uninformative_controls_detected == 1
    assert any("EXP-OER-05" in ent for ent in summary_oer.filtering_metric.flagged_entities)


def test_bayesian_posterior_exactness():
    """Verify that dynamic agent belief updates match the closed-form analytical Bayes theorem with zero error."""
    for case_id in ["CS-CAT-001", "CS-OER-002", "SYN-001"]:
        summary = AgenticValueEvaluator.evaluate_case(case_id)
        b_metric = summary.bayesian_update_metric
        assert b_metric is not None
        assert b_metric.is_exact_match is True
        assert b_metric.max_absolute_posterior_error < 1e-6


def test_live_llm_blocking_uncredentialed():
    """Verify that without API credentials, live LLM mode is cleanly recorded as BLOCKED_MISSING_CREDENTIALS."""
    summary = AgenticValueEvaluator.evaluate_case("CS-CAT-001", api_key=None)
    live_pipeline = next((p for p in summary.pipelines if p.workflow_name == "live_llm_agent"), None)
    assert live_pipeline is not None
    assert live_pipeline.execution_status == "BLOCKED_MISSING_CREDENTIALS"
    assert live_pipeline.live_llm_called is False


def test_decision_consistency_synthesis_statement():
    """Verify that the report synthesis explicitly frames equivalence as decision consistency, not superiority."""
    report = AgenticValueEvaluator.evaluate_all()
    synthesis = report.value_synthesis.lower()
    assert "decision consistency" in synthesis
    assert "not superior agentic performance" in synthesis


def test_agentic_value_api_endpoint():
    """Verify that GET /api/evaluation/agentic-value returns 200 and valid evaluation report schema."""
    response = client.get("/api/evaluation/agentic-value")
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"].startswith("AGENT-VAL-")
    assert len(data["evaluated_cases"]) == 3
    case_ids = [c["case_id"] for c in data["evaluated_cases"]]
    assert "CS-CAT-001" in case_ids
    assert "CS-OER-002" in case_ids
    assert "SYN-001" in case_ids
    assert data["value_synthesis"]
