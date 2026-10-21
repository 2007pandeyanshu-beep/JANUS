"""Tests for CS-OER-002 Scenario Constructor and Execution Integrity

Verifies:
1. Probabilistic simplex normalization (priors sum to 1.0, likelihoods sum to 1.0 per hypothesis).
2. Initial Shannon entropy matches the frozen theoretical value (1.5087 bits).
3. Negative control assay (EXP-OER-05) has mathematically zero EIG (EIG == 0.0000 bits).
4. Offline combinatorial upper bound strictly bounds all sequential policies on CS-OER-002.
5. Single-seed diagnostic execution completes without error.
"""

import pytest
import math
import numpy as np

from scientific.oer_scenario import get_oer_case_study_scenario
from scientific.scoring import compute_shannon_entropy, evaluate_experiment_information_gain
from scientific.validation import validate_and_normalize_priors, validate_experiment_predictions
from evaluation.sequential_evaluation import run_sequential_policy_comparison


def test_oer_scenario_schema_and_priors():
    """Verifies schema conformance and exact prior normalization."""
    scenario = get_oer_case_study_scenario()
    assert scenario.case_study_id == "CS-OER-002"
    assert len(scenario.hypotheses) == 3
    assert len(scenario.experiments) == 5

    # Verify priors sum to 1.0
    priors, warnings = validate_and_normalize_priors(scenario.hypotheses)
    assert len(warnings) == 0
    assert pytest.approx(sum(priors.values()), abs=1e-9) == 1.0
    assert priors["H1"] == 0.35
    assert priors["H2"] == 0.45
    assert priors["H3"] == 0.20

    # Verify initial entropy: - [0.35*log2(0.35) + 0.45*log2(0.45) + 0.20*log2(0.20)]
    expected_entropy = - (0.35 * math.log2(0.35) + 0.45 * math.log2(0.45) + 0.20 * math.log2(0.20))
    calc_entropy = compute_shannon_entropy(list(priors.values()))
    assert pytest.approx(calc_entropy, abs=1e-6) == expected_entropy
    assert pytest.approx(calc_entropy, abs=1e-4) == 1.5129


def test_oer_experiment_likelihood_normalization():
    """Verifies that every experiment's outcome likelihood distribution sums to 1.0 per hypothesis."""
    scenario = get_oer_case_study_scenario()
    h_ids = [h.id for h in scenario.hypotheses]

    for exp in scenario.experiments:
        matrix, warnings = validate_experiment_predictions(exp, h_ids)
        assert len(warnings) == 0
        for h_id in h_ids:
            total_p = sum(matrix[h_id].values())
            assert pytest.approx(total_p, abs=1e-6) == 1.0, f"Likelihood sum != 1.0 for {exp.id} under {h_id}"


def test_oer_blank_control_zero_eig():
    """Verifies that EXP-OER-05 (HR-TEM) is an exact zero-EIG negative control."""
    scenario = get_oer_case_study_scenario()
    priors, _ = validate_and_normalize_priors(scenario.hypotheses)
    h_ids = list(priors.keys())
    tem_exp = next(e for e in scenario.experiments if e.id == "EXP-OER-05")
    matrix, _ = validate_experiment_predictions(tem_exp, h_ids)
    score = evaluate_experiment_information_gain(tem_exp, priors, matrix, cost_weight=0.1)

    assert pytest.approx(score.expected_information_gain, abs=1e-6) == 0.0000
    assert score.is_informative is False
    assert score.composite_utility_score == 0.0


def test_oer_diagnostic_assays_ranking():
    """Verifies that diagnostic assays have positive EIG and reasonable utilities."""
    scenario = get_oer_case_study_scenario()
    priors, _ = validate_and_normalize_priors(scenario.hypotheses)
    h_ids = list(priors.keys())

    for exp in scenario.experiments:
        if exp.id != "EXP-OER-05":
            matrix, _ = validate_experiment_predictions(exp, h_ids)
            score = evaluate_experiment_information_gain(exp, priors, matrix, cost_weight=0.1)
            assert score.expected_information_gain > 0.05, f"Assay {exp.id} has unexpectedly low EIG"
            assert score.composite_utility_score > 0.0


def test_oer_offline_bound_invariant_seed42():
    """Verifies that offline combinatorial upper bound strictly holds across all policies on CS-OER-002."""
    scenario = get_oer_case_study_scenario()
    for h_id in ["H1", "H2", "H3"]:
        report = run_sequential_policy_comparison(
            scenario=scenario,
            hidden_hypothesis_id=h_id,
            seed=42,
            budget=10.0,
            max_steps=5,
            confidence_threshold=0.95
        )
        bound = report.offline_optimal_ig_bits
        for s in report.policy_summaries:
            assert s.total_realized_ig_bits <= bound + 1e-6, (
                f"Bound violation under {h_id}: policy {s.policy_key} achieved "
                f"{s.total_realized_ig_bits} > bound {bound}"
            )
            assert s.regret_vs_offline_optimal >= -1e-6
