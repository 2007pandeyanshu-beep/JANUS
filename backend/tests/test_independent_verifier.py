"""Unit tests for Independent Mathematical Verifier (Workstream B).

Verifies:
- Independent recalculation of prior simplex (sum to 1.0, non-negativity)
- Independent row-sum verification of likelihood distributions (sum to 1.0 per hypothesis)
- Independent marginal outcome probability and Shannon entropy recalculation
- Information-theoretic bounds verification: 0 <= EIG <= H(P)
- Authoritative composite utility ranking verification with tie-breaking
- Bayesian sequential posterior update recalculation
- Integration with Critic role via IndependentVerificationTool
"""

import pytest
import math
from app.schemas.scientific import PredictedOutcome, Experiment, ExperimentScore
from scientific.engine import ScientificEngine
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.validation import IndependentEngineVerifier
from agents.tools import IndependentVerificationTool


def test_independent_verifier_valid_prior_simplex():
    """Tests that valid prior distributions sum to 1.0 and pass simplex invariants."""
    priors = {"H1": 0.4, "H2": 0.35, "H3": 0.25}
    res = IndependentEngineVerifier.verify_prior_simplex(priors)
    assert res["is_valid"] is True
    assert res["status"] == "PASS"
    assert res["sum"] == pytest.approx(1.0, abs=1e-5)


def test_independent_verifier_invalid_prior_simplex():
    """Tests that perturbed prior distributions violate simplex invariants."""
    # Sum != 1.0
    bad_priors_sum = {"H1": 0.5, "H2": 0.3, "H3": 0.1}
    res1 = IndependentEngineVerifier.verify_prior_simplex(bad_priors_sum)
    assert res1["is_valid"] is False
    assert res1["status"] == "FAIL"

    # Negative prior
    bad_priors_neg = {"H1": 1.2, "H2": -0.2}
    res2 = IndependentEngineVerifier.verify_prior_simplex(bad_priors_neg)
    assert res2["is_valid"] is False
    assert res2["status"] == "FAIL"


def test_independent_verifier_likelihood_distribution():
    """Tests verification of likelihood rows per hypothesis summing to 1.0."""
    valid_predictions = [
        PredictedOutcome(outcome_label="Out_A", hypothesis_id="H1", probability=0.8),
        PredictedOutcome(outcome_label="Out_B", hypothesis_id="H1", probability=0.2),
        PredictedOutcome(outcome_label="Out_A", hypothesis_id="H2", probability=0.1),
        PredictedOutcome(outcome_label="Out_B", hypothesis_id="H2", probability=0.9),
    ]
    exp_valid = Experiment(
        id="EXP-TEST-01",
        name="Valid Exp",
        description="Testing valid likelihood",
        cost=1.0,
        feasibility=0.9,
        possible_outcomes=["Out_A", "Out_B"],
        predictions=valid_predictions,
    )
    res_valid = IndependentEngineVerifier.verify_likelihood_distribution(
        experiment=exp_valid,
        hypothesis_ids=["H1", "H2"],
    )
    assert res_valid["is_valid"] is True
    assert res_valid["status"] == "PASS"

    # Defective likelihood summing to 0.7 for H1
    bad_predictions = [
        PredictedOutcome(outcome_label="Out_A", hypothesis_id="H1", probability=0.5),
        PredictedOutcome(outcome_label="Out_B", hypothesis_id="H1", probability=0.2),
        PredictedOutcome(outcome_label="Out_A", hypothesis_id="H2", probability=0.1),
        PredictedOutcome(outcome_label="Out_B", hypothesis_id="H2", probability=0.9),
    ]
    exp_bad = Experiment(
        id="EXP-TEST-02",
        name="Bad Exp",
        description="Testing defective likelihood",
        cost=1.0,
        feasibility=0.9,
        possible_outcomes=["Out_A", "Out_B"],
        predictions=bad_predictions,
    )
    res_bad = IndependentEngineVerifier.verify_likelihood_distribution(
        experiment=exp_bad,
        hypothesis_ids=["H1", "H2"],
    )
    assert res_bad["is_valid"] is False
    assert res_bad["status"] == "FAIL"


def test_independent_verifier_eig_bounds():
    """Tests that EIG is strictly bounded by 0 <= EIG <= Shannon Entropy H(P)."""
    priors = {"H1": 0.5, "H2": 0.5}
    # Maximum entropy for binary uniform is log2(2) = 1.0 bit
    H_max = - (0.5 * math.log2(0.5) + 0.5 * math.log2(0.5))
    assert pytest.approx(H_max) == 1.0

    exp = Experiment(
        id="EXP-BOUNDS-01",
        name="Perfect Disambiguator",
        description="Distinguishes H1 from H2 completely",
        cost=2.0,
        feasibility=0.9,
        possible_outcomes=["Y1", "Y2"],
        predictions=[
            PredictedOutcome(outcome_label="Y1", hypothesis_id="H1", probability=1.0),
            PredictedOutcome(outcome_label="Y2", hypothesis_id="H1", probability=0.0),
            PredictedOutcome(outcome_label="Y1", hypothesis_id="H2", probability=0.0),
            PredictedOutcome(outcome_label="Y2", hypothesis_id="H2", probability=1.0),
        ],
    )

    score = ExperimentScore(
        experiment_id=exp.id,
        experiment_name=exp.name,
        expected_information_gain=1.0,  # Valid: EIG == H(P)
        composite_utility_score=0.75,
        cost=exp.cost,
        feasibility=exp.feasibility,
        prior_entropy=1.0,
        expected_posterior_entropy=0.0,
        normalized_information_gain=1.0,
        explanation="Test scoring verification",
        marginal_probabilities={"Y1": 0.5, "Y2": 0.5},
        posterior_matrix={"Y1": {"H1": 1.0, "H2": 0.0}, "Y2": {"H1": 0.0, "H2": 1.0}},
    )

    verif = IndependentEngineVerifier.verify_experiment_scoring(exp, score, priors)
    assert verif["is_valid"] is True
    assert verif["status"] == "PASS"
    assert verif["eig_within_bounds"] is True

    # Artificial violation: EIG exceeding entropy bound
    score_invalid = score.model_copy(update={"expected_information_gain": 1.5})
    verif_invalid = IndependentEngineVerifier.verify_experiment_scoring(exp, score_invalid, priors)
    assert verif_invalid["is_valid"] is False
    assert verif_invalid["eig_within_bounds"] is False


def test_independent_verifier_authoritative_ranking_order():
    """Tests that ranking is verified against authoritative composite utility formula with tie breaking."""
    s1 = ExperimentScore(
        experiment_id="EXP-01",
        experiment_name="Exp 1",
        expected_information_gain=0.6,
        composite_utility_score=0.90,
        cost=2.0,
        feasibility=0.9,
        prior_entropy=1.5,
        expected_posterior_entropy=0.9,
        normalized_information_gain=0.4,
        explanation="Score 1",
        utility_rank=1,
        rank=1,
        eig_rank=2,
    )
    s2 = ExperimentScore(
        experiment_id="EXP-02",
        experiment_name="Exp 2",
        expected_information_gain=0.8,  # Higher EIG, but lower composite utility
        composite_utility_score=0.75,
        cost=5.0,
        feasibility=0.6,
        prior_entropy=1.5,
        expected_posterior_entropy=0.7,
        normalized_information_gain=0.53,
        explanation="Score 2",
        utility_rank=2,
        rank=2,
        eig_rank=1,
    )

    # Correct authoritative ordering by utility: s1 before s2
    res_correct = IndependentEngineVerifier.verify_ranking_order([s1, s2])
    assert res_correct["is_valid"] is True
    assert res_correct["status"] == "PASS"

    # Incorrect ordering (sorted by EIG instead of utility)
    s2_swapped = s2.model_copy(update={"utility_rank": 1, "rank": 1})
    s1_swapped = s1.model_copy(update={"utility_rank": 2, "rank": 2})
    res_incorrect = IndependentEngineVerifier.verify_ranking_order([s2_swapped, s1_swapped])
    assert res_incorrect["is_valid"] is False
    assert res_incorrect["status"] == "FAIL"


def test_independent_verifier_bayesian_observation_update():
    """Tests independent recalculation of Bayes' theorem update."""
    initial_priors = {"H_RED": 0.40, "H_FOR": 0.35, "H_CRB": 0.25}
    # Observation y: P(y|H_RED)=0.95, P(y|H_FOR)=0.05, P(y|H_CRB)=0.20
    likelihood_vector = {"H_RED": 0.95, "H_FOR": 0.05, "H_CRB": 0.20}

    # Expected marginal: P(y) = 0.40*0.95 + 0.35*0.05 + 0.25*0.20 = 0.380 + 0.0175 + 0.050 = 0.4475
    # Expected posteriors:
    # H_RED: 0.380 / 0.4475 = 0.84916
    # H_FOR: 0.0175 / 0.4475 = 0.03910
    # H_CRB: 0.050 / 0.4475 = 0.11173
    correct_posteriors = {
        "H_RED": 0.380 / 0.4475,
        "H_FOR": 0.0175 / 0.4475,
        "H_CRB": 0.050 / 0.4475,
    }

    res_valid = IndependentEngineVerifier.verify_bayesian_observation_update(
        initial_priors=initial_priors,
        likelihood_vector=likelihood_vector,
        observed_posteriors=correct_posteriors,
        experiment_id="EXP-WGS-02",
        observed_outcome="Initial_CO2_Mainly_Lattice_16O",
    )
    assert res_valid["is_valid"] is True
    assert res_valid["verification_status"] == "VERIFIED"
    assert res_valid["max_divergence"] < 1e-4

    # Fabricated / corrupted posteriors
    corrupted_posteriors = {"H_RED": 0.50, "H_FOR": 0.30, "H_CRB": 0.20}
    res_corrupted = IndependentEngineVerifier.verify_bayesian_observation_update(
        initial_priors=initial_priors,
        likelihood_vector=likelihood_vector,
        observed_posteriors=corrupted_posteriors,
        experiment_id="EXP-WGS-02",
        observed_outcome="Initial_CO2_Mainly_Lattice_16O",
    )
    assert res_corrupted["is_valid"] is False
    assert res_corrupted["verification_status"] == "UPDATE_VIOLATION"


def test_independent_verifier_full_analysis_result():
    """Tests end-to-end mathematical audit on the authoritative Pt/CeO2 WGS scenario."""
    scenario = get_wgs_case_study_scenario()
    analysis = ScientificEngine.execute_analysis(scenario)

    verif_dict, record = IndependentVerificationTool.verify(analysis, scenario)

    assert verif_dict["verification_status"] == "VERIFIED"
    assert verif_dict["is_verified"] is True
    assert verif_dict["all_invariants_hold"] is True
    assert verif_dict["failed_checks"] == 0
    assert record.status == "SUCCESS"
    assert record.tool_name == "independent_mathematical_verification"
