"""Analytical Verification and Edge Case Tests for JANUS Information Engine

Rigorously verifies:
1. Closed-form analytical Shannon entropy bounds
2. Zero-division and boundary likelihood robustness
3. Information-theoretic non-negativity and upper bounds (I(H; Y) <= H(H))
4. Extreme prior behavior (near certainty vs maximum ignorance)
5. Strict monotonicity of cost and feasibility constraints
6. Deterministic reproducibility across seeds
"""

import pytest
import math
import numpy as np
from scientific.scoring import (
    compute_shannon_entropy,
    evaluate_experiment_information_gain,
    rank_experiments,
)
from app.schemas.scientific import Hypothesis, Experiment, PredictedOutcome
from evaluation.benchmark_evaluation import run_reproducible_benchmark


def test_analytical_entropy_closed_forms():
    """Verifies that computed entropy matches exact analytical values."""
    # H = log2(K) for uniform distribution
    for K in [2, 3, 4, 8, 16]:
        probs = [1.0 / K] * K
        expected = math.log2(K)
        computed = compute_shannon_entropy(probs)
        assert pytest.approx(computed, 1e-9) == expected

    # Skewed binary distribution: [0.9, 0.1]
    expected_skewed = -(0.9 * math.log2(0.9) + 0.1 * math.log2(0.1))
    computed_skewed = compute_shannon_entropy([0.9, 0.1])
    assert pytest.approx(computed_skewed, 1e-9) == expected_skewed

    # Certainty (Dirac delta): H = 0
    assert compute_shannon_entropy([1.0, 0.0, 0.0]) == 0.0


def test_eig_upper_bound_and_non_negativity():
    """Axiom: 0 <= EIG(e) <= H(H) for any valid experiment."""
    priors = {"H1": 0.4, "H2": 0.35, "H3": 0.25}
    prior_entropy = compute_shannon_entropy(list(priors.values()))

    # Case A: Arbitrary noisy experiment
    exp = Experiment(
        id="EXP-TEST-A",
        name="Noisy Experiment",
        description="Assay with arbitrary likelihoods",
        possible_outcomes=["O1", "O2", "O3"],
        predictions=[
            PredictedOutcome(outcome_label="O1", hypothesis_id="H1", probability=0.7),
            PredictedOutcome(outcome_label="O2", hypothesis_id="H1", probability=0.2),
            PredictedOutcome(outcome_label="O3", hypothesis_id="H1", probability=0.1),
            PredictedOutcome(outcome_label="O1", hypothesis_id="H2", probability=0.1),
            PredictedOutcome(outcome_label="O2", hypothesis_id="H2", probability=0.8),
            PredictedOutcome(outcome_label="O3", hypothesis_id="H2", probability=0.1),
            PredictedOutcome(outcome_label="O1", hypothesis_id="H3", probability=0.2),
            PredictedOutcome(outcome_label="O2", hypothesis_id="H3", probability=0.3),
            PredictedOutcome(outcome_label="O3", hypothesis_id="H3", probability=0.5),
        ],
        cost=1.0,
        feasibility=1.0
    )

    matrix = {
        "H1": {"O1": 0.7, "O2": 0.2, "O3": 0.1},
        "H2": {"O1": 0.1, "O2": 0.8, "O3": 0.1},
        "H3": {"O1": 0.2, "O2": 0.3, "O3": 0.5},
    }

    score = evaluate_experiment_information_gain(exp, priors, matrix)
    assert score.expected_information_gain >= 0.0
    assert score.expected_information_gain <= prior_entropy + 1e-9
    assert 0.0 <= score.normalized_information_gain <= 1.0


def test_zero_likelihood_outcomes_handled_safely():
    """Outcomes with 0 likelihood under a hypothesis must update posterior to 0 without error."""
    priors = {"H1": 0.5, "H2": 0.5}
    exp = Experiment(
        id="EXP-ZERO-TEST",
        name="Zero Likelihood Test",
        description="Tests P(y|H)=0",
        possible_outcomes=["Pass", "Fail"],
        predictions=[]
    )
    # H1 always passes; H2 always fails
    matrix = {
        "H1": {"Pass": 1.0, "Fail": 0.0},
        "H2": {"Pass": 0.0, "Fail": 1.0}
    }
    score = evaluate_experiment_information_gain(exp, priors, matrix)

    # If outcome is Pass: P(H1|Pass) = 1.0, P(H2|Pass) = 0.0
    assert pytest.approx(score.posterior_matrix["Pass"]["H1"], 1e-6) == 1.0
    assert pytest.approx(score.posterior_matrix["Pass"]["H2"], 1e-6) == 0.0

    # If outcome is Fail: P(H1|Fail) = 0.0, P(H2|Fail) = 1.0
    assert pytest.approx(score.posterior_matrix["Fail"]["H1"], 1e-6) == 0.0
    assert pytest.approx(score.posterior_matrix["Fail"]["H2"], 1e-6) == 1.0

    # Perfect disambiguation yields EIG = prior entropy = 1.0 bit
    assert pytest.approx(score.expected_information_gain, 1e-6) == 1.0
    assert pytest.approx(score.expected_posterior_entropy, 1e-6) == 0.0


def test_extreme_priors_sensitivity():
    """Under near-certainty prior, prior entropy and EIG approach 0."""
    priors_certain = {"H1": 0.99998, "H2": 0.00001, "H3": 0.00001}
    exp = Experiment(
        id="EXP-EXTREME",
        name="Assay under near certainty",
        description="Assay",
        possible_outcomes=["A", "B"],
        predictions=[]
    )
    matrix = {
        "H1": {"A": 0.9, "B": 0.1},
        "H2": {"A": 0.1, "B": 0.9},
        "H3": {"A": 0.5, "B": 0.5},
    }
    score = evaluate_experiment_information_gain(exp, priors_certain, matrix)
    assert score.prior_entropy < 0.001
    assert score.expected_information_gain < 0.001


def test_cost_and_feasibility_monotonicity():
    """Utility must strictly increase with feasibility and strictly decrease with cost."""
    priors = {"H1": 0.5, "H2": 0.5}
    matrix = {
        "H1": {"A": 0.8, "B": 0.2},
        "H2": {"A": 0.2, "B": 0.8},
    }

    exp_base = Experiment(
        id="EXP-BASE",
        name="Base Assay",
        description="Base",
        possible_outcomes=["A", "B"],
        predictions=[],
        cost=2.0,
        feasibility=0.8
    )

    exp_cheaper = Experiment(
        id="EXP-CHEAP",
        name="Cheaper Assay",
        description="Cheaper",
        possible_outcomes=["A", "B"],
        predictions=[],
        cost=1.0,  # Lower cost
        feasibility=0.8
    )

    exp_more_feasible = Experiment(
        id="EXP-FEASIBLE",
        name="More Feasible Assay",
        description="More feasible",
        possible_outcomes=["A", "B"],
        predictions=[],
        cost=2.0,
        feasibility=0.95  # Higher feasibility
    )

    score_base = evaluate_experiment_information_gain(exp_base, priors, matrix, cost_weight=0.1)
    score_cheaper = evaluate_experiment_information_gain(exp_cheaper, priors, matrix, cost_weight=0.1)
    score_feasible = evaluate_experiment_information_gain(exp_more_feasible, priors, matrix, cost_weight=0.1)

    # Cheaper must have higher utility
    assert score_cheaper.composite_utility_score > score_base.composite_utility_score
    # More feasible must have higher utility
    assert score_feasible.composite_utility_score > score_base.composite_utility_score


def test_reproducible_benchmark_evaluation_properties():
    """Verifies that benchmark evaluation matches exact expectations and has no regressions."""
    report1 = run_reproducible_benchmark(seed=42, monte_carlo_samples=5000)
    report2 = run_reproducible_benchmark(seed=42, monte_carlo_samples=5000)

    # Strict reproducibility across identical seeds
    assert report1.janus_policy.expected_information_gain == report2.janus_policy.expected_information_gain
    assert report1.monte_carlo_verification.empirical_mean_eig == report2.monte_carlo_verification.empirical_mean_eig

    # Verify exact analytical population properties
    assert pytest.approx(report1.exact_random_baseline.exact_mean_eig, 1e-4) == 0.3506
    assert pytest.approx(report1.exact_random_baseline.exact_population_std_eig, 1e-4) == 0.1940
    assert pytest.approx(report1.exact_random_baseline.exact_mean_utility, 1e-4) == 0.2503
    assert report1.exact_random_baseline.exact_waste_rate == 0.20
    assert report1.exact_random_baseline.probability_of_selecting_optimal == 0.20

    # Verify JANUS exact calculations
    assert pytest.approx(report1.janus_policy.expected_information_gain, 1e-4) == 0.5593
    assert pytest.approx(report1.janus_policy.composite_utility, 1e-4) == 0.4171
    assert pytest.approx(report1.comparison_summary["exact_eig_multiplier"], 1e-3) == 1.5950
    assert pytest.approx(report1.comparison_summary["exact_utility_multiplier"], 1e-3) == 1.6665

    # Verify cheapest heuristic selects the 0-EIG quartz blank (EXP-WGS-06)
    assert report1.cheapest_heuristic_policy.selected_experiment_ids == ["EXP-WGS-06"]
    assert report1.cheapest_heuristic_policy.expected_information_gain == 0.0
    assert report1.cheapest_heuristic_policy.waste_rate == 1.0

    # Verify JANUS waste rate is strictly zero
    assert report1.janus_policy.waste_rate == 0.0
