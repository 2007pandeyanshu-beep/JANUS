"""Tests for JANUS Information-Theoretic Scientific Engine"""

import pytest
import math
from app.schemas.scientific import Hypothesis, Experiment, PredictedOutcome, AnalysisInput
from scientific.scoring import compute_shannon_entropy, evaluate_experiment_information_gain
from scientific.validation import validate_and_normalize_priors, validate_experiment_predictions, ScientificValidationError
from scientific.engine import ScientificEngine
from scientific.scenarios import get_demo_scenario
from evaluation.baselines import evaluate_random_selection_baseline


def test_shannon_entropy_binary():
    # Maximum entropy for fair binary coin: -2 * (0.5 * log2(0.5)) = 1.0 bit
    h_max = compute_shannon_entropy([0.5, 0.5])
    assert pytest.approx(h_max, 1e-6) == 1.0

    # Deterministic certainty has 0 entropy: -1 * log2(1) = 0.0
    h_zero = compute_shannon_entropy([1.0, 0.0])
    assert pytest.approx(h_zero, 1e-6) == 0.0


def test_prior_normalization():
    h1 = Hypothesis(id="H1", name="H1", description="desc", prior=0.3)
    h2 = Hypothesis(id="H2", name="H2", description="desc", prior=0.3)
    
    # 0.3 + 0.3 = 0.6 -> should normalize to 0.5 each with warning
    priors, warnings = validate_and_normalize_priors([h1, h2])
    assert pytest.approx(priors["H1"], 1e-6) == 0.5
    assert pytest.approx(priors["H2"], 1e-6) == 0.5
    assert len(warnings) == 1
    assert "automatically normalized" in warnings[0]


def test_known_toy_example_perfect_disambiguation():
    """
    Known analytical toy example:
    P(H1) = 0.5, P(H2) = 0.5. Prior entropy = 1.0 bit.
    Experiment A has outcomes [Y1, Y2].
    Under H1: P(Y1)=1.0, P(Y2)=0.0.
    Under H2: P(Y1)=0.0, P(Y2)=1.0.
    Outcome Y1 guarantees H1; Y2 guarantees H2.
    Expected posterior entropy = 0.0 bit.
    Expected Information Gain = 1.0 - 0.0 = 1.0 bit.
    """
    priors = {"H1": 0.5, "H2": 0.5}
    exp = Experiment(
        id="EXP-TOY",
        name="Perfect Separator",
        description="Assay that perfectly separates H1 and H2",
        possible_outcomes=["Y1", "Y2"],
        predictions=[
            PredictedOutcome(outcome_label="Y1", hypothesis_id="H1", probability=1.0),
            PredictedOutcome(outcome_label="Y2", hypothesis_id="H1", probability=0.0),
            PredictedOutcome(outcome_label="Y1", hypothesis_id="H2", probability=0.0),
            PredictedOutcome(outcome_label="Y2", hypothesis_id="H2", probability=1.0),
        ],
        cost=1.0,
        feasibility=1.0
    )
    
    matrix = {
        "H1": {"Y1": 1.0, "Y2": 0.0},
        "H2": {"Y1": 0.0, "Y2": 1.0}
    }
    
    score = evaluate_experiment_information_gain(exp, priors, matrix)
    assert pytest.approx(score.prior_entropy, 1e-5) == 1.0
    assert pytest.approx(score.expected_posterior_entropy, 1e-5) == 0.0
    assert pytest.approx(score.expected_information_gain, 1e-5) == 1.0
    assert pytest.approx(score.normalized_information_gain, 1e-5) == 1.0
    assert score.is_informative is True


def test_identical_predictions_yields_zero_information():
    """
    If all hypotheses predict the exact same outcome probabilities,
    the experiment provides 0.0 bits of information gain.
    """
    priors = {"H1": 0.6, "H2": 0.4}
    exp = Experiment(
        id="EXP-ZERO",
        name="Uninformative Assay",
        description="Assay with identical predictions under all hypotheses",
        possible_outcomes=["Pass", "Fail"],
        predictions=[
            PredictedOutcome(outcome_label="Pass", hypothesis_id="H1", probability=0.8),
            PredictedOutcome(outcome_label="Fail", hypothesis_id="H1", probability=0.2),
            PredictedOutcome(outcome_label="Pass", hypothesis_id="H2", probability=0.8),
            PredictedOutcome(outcome_label="Fail", hypothesis_id="H2", probability=0.2),
        ],
        cost=1.0,
        feasibility=1.0
    )
    
    matrix = {
        "H1": {"Pass": 0.8, "Fail": 0.2},
        "H2": {"Pass": 0.8, "Fail": 0.2}
    }
    
    score = evaluate_experiment_information_gain(exp, priors, matrix)
    assert pytest.approx(score.expected_information_gain, 1e-6) == 0.0
    assert score.is_informative is False
    assert "0.0 bits" in score.explanation


def test_infeasible_experiment_handling():
    """Infeasible experiments must receive 0 utility score."""
    priors = {"H1": 0.5, "H2": 0.5}
    exp = Experiment(
        id="EXP-INFEASIBLE",
        name="Impossible Assay",
        description="Assay with feasibility = 0",
        possible_outcomes=["A", "B"],
        predictions=[],
        cost=10.0,
        feasibility=0.0,
        is_feasible=False
    )
    
    score = evaluate_experiment_information_gain(exp, priors, {})
    assert score.composite_utility_score == 0.0
    assert score.expected_information_gain == 0.0
    assert "infeasible" in score.explanation


def test_missing_outcome_prediction_raises_error():
    """Missing predictions for any outcome under any hypothesis must raise ScientificValidationError."""
    exp = Experiment(
        id="EXP-INCOMPLETE",
        name="Incomplete Assay",
        description="Missing H2 prediction",
        possible_outcomes=["O1", "O2"],
        predictions=[
            PredictedOutcome(outcome_label="O1", hypothesis_id="H1", probability=0.5),
            PredictedOutcome(outcome_label="O2", hypothesis_id="H1", probability=0.5),
            # Missing H2
        ]
    )
    
    with pytest.raises(ScientificValidationError):
        validate_experiment_predictions(exp, ["H1", "H2"])


def test_demo_scenario_end_to_end_reproducibility():
    """Verifies that the demo scenario executes deterministically and yields consistent ranking."""
    payload = get_demo_scenario()
    
    result1 = ScientificEngine.execute_analysis(payload)
    result2 = ScientificEngine.execute_analysis(payload)
    
    assert len(result1.ranked_experiments) == len(payload.experiments)
    assert result1.validation_status == "VALIDATED_DETERMINISTIC"
    
    # Check that rank order is identical across consecutive runs
    ranks1 = [r.experiment_id for r in result1.ranked_experiments]
    ranks2 = [r.experiment_id for r in result2.ranked_experiments]
    assert ranks1 == ranks2
    
    # Check that scores match exactly
    for s1, s2 in zip(result1.ranked_experiments, result2.ranked_experiments):
        assert s1.composite_utility_score == s2.composite_utility_score
        assert s1.expected_information_gain == s2.expected_information_gain
        assert s1.rank == s2.rank
    
    # Check that uninformative experiment EXP-04 has 0.0 EIG
    exp04_score = next(s for s in result1.ranked_experiments if s.experiment_id == "EXP-04")
    assert pytest.approx(exp04_score.expected_information_gain, 1e-6) == 0.0
    
    # Check that infeasible experiment EXP-05 has 0.0 utility
    exp05_score = next(s for s in result1.ranked_experiments if s.experiment_id == "EXP-05")
    assert exp05_score.composite_utility_score == 0.0
    
    # Check baseline comparison
    assert result1.baseline_comparison.baseline_expected_eig > 0.0
    assert result1.baseline_comparison.eig_improvement_ratio >= 1.0
