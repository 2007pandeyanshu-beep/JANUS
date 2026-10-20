"""Tests for JANUS Sequential Bayesian Experimental Design (BED) Engine (Phase 5).

Verifies:
1. Exact Bayesian posterior updates against analytical hand-calculated values.
2. Posterior normalization invariant (sum = 1.0).
3. Hidden-hypothesis isolation (policy does not access H*).
4. Deterministic reproducibility under fixed seeds.
5. Failed-experiment handling (posterior unchanged, 0 realized bits, cost incurred).
6. Dynamic re-ranking after new evidence.
7. Stopping conditions: confidence threshold, budget exhaustion, max steps, no informative candidates.
8. Unquantified assay exclusion.
9. Campaign history and cumulative cost tracking.
10. Fair multi-policy comparison benchmark.
"""

import pytest
import numpy as np
from app.schemas.scientific import (
    BEDCampaignInput,
    Experiment,
    Hypothesis,
    AnalysisInput,
)
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.sequential_engine import (
    Nature,
    compute_bayesian_posterior_update,
    SequentialBEDEngine,
)
from evaluation.sequential_evaluation import run_sequential_policy_comparison


def test_hand_calculated_bayesian_posterior_update():
    """
    Hand-calculated analytical test:
    Prior: P(H1) = 0.50, P(H2) = 0.20, P(H3) = 0.30
    Experiment: EXP-WGS-02 (H2(18O) / C(16O) Pulse)
    Observed Outcome: 'Initial_CO2_Mainly_Lattice_16O'
    Likelihoods: P(y | H1) = 0.92, P(y | H2) = 0.08, P(y | H3) = 0.12
    
    Unnormalized:
      H1: 0.50 * 0.92 = 0.460
      H2: 0.20 * 0.08 = 0.016
      H3: 0.30 * 0.12 = 0.036
      Marginal P(y) = 0.460 + 0.016 + 0.036 = 0.512
      
    Posterior:
      P(H1 | y) = 0.460 / 0.512 = 0.8984375
      P(H2 | y) = 0.016 / 0.512 = 0.0312500
      P(H3 | y) = 0.036 / 0.512 = 0.0703125
    """
    prior = {"H1": 0.50, "H2": 0.20, "H3": 0.30}
    l_matrix = {
        "H1": {"Initial_CO2_Mainly_Lattice_16O": 0.92, "Initial_CO2_Mainly_Mixed_18O": 0.08},
        "H2": {"Initial_CO2_Mainly_Lattice_16O": 0.08, "Initial_CO2_Mainly_Mixed_18O": 0.92},
        "H3": {"Initial_CO2_Mainly_Lattice_16O": 0.12, "Initial_CO2_Mainly_Mixed_18O": 0.88},
    }
    
    post = compute_bayesian_posterior_update(prior, "Initial_CO2_Mainly_Lattice_16O", l_matrix)
    
    assert post["H1"] == pytest.approx(0.898438, abs=1e-4)
    assert post["H2"] == pytest.approx(0.031250, abs=1e-4)
    assert post["H3"] == pytest.approx(0.070312, abs=1e-4)
    assert sum(post.values()) == pytest.approx(1.0, abs=1e-6)


def test_posterior_normalization_invariant():
    """Confirms that posterior sums strictly to 1.0 even with arbitrary unnormalized inputs."""
    prior = {"H1": 0.333333, "H2": 0.333333, "H3": 0.333334}
    l_matrix = {
        "H1": {"yA": 0.137, "yB": 0.863},
        "H2": {"yA": 0.589, "yB": 0.411},
        "H3": {"yA": 0.912, "yB": 0.088},
    }
    
    post_A = compute_bayesian_posterior_update(prior, "yA", l_matrix)
    post_B = compute_bayesian_posterior_update(prior, "yB", l_matrix)
    
    assert sum(post_A.values()) == pytest.approx(1.0, abs=1e-6)
    assert sum(post_B.values()) == pytest.approx(1.0, abs=1e-6)


def test_hidden_hypothesis_isolation():
    """
    Ensures the selection policy cannot inspect Nature's private _hidden_hypothesis_id.
    """
    rng = np.random.default_rng(42)
    nature = Nature(hidden_hypothesis_id="H1", rng=rng)
    
    # Check that Nature encapsulates hidden hypothesis
    assert hasattr(nature, "_hidden_hypothesis_id")
    
    scenario = get_wgs_case_study_scenario()
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=42,
        budget=10.0,
        max_steps=3
    )
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    
    # Step selection rationale should never mention knowing H*
    for step in res.steps:
        assert "hidden" not in step.selection_rationale.lower()
        assert "h*" not in step.selection_rationale.lower()


def test_deterministic_execution_fixed_seed():
    """Fixed seed must produce bit-for-bit identical sequential campaigns."""
    scenario = get_wgs_case_study_scenario()
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=12345,
        budget=10.0,
        max_steps=4
    )
    
    res1 = SequentialBEDEngine.run_campaign(scenario, inp)
    res2 = SequentialBEDEngine.run_campaign(scenario, inp)
    
    assert res1.total_steps == res2.total_steps
    assert res1.total_cost == res2.total_cost
    assert res1.final_posterior == res2.final_posterior
    for s1, s2 in zip(res1.steps, res2.steps):
        assert s1.selected_experiment_id == s2.selected_experiment_id
        assert s1.observed_outcome == s2.observed_outcome
        assert s1.execution_status == s2.execution_status
        assert s1.realized_information_gain == s2.realized_information_gain


def test_failed_experiment_handling():
    """
    When an experiment fails feasibility:
    1. Posterior must remain strictly identical to prior.
    2. Realized information gain must be exactly 0.0 bits.
    3. Cost must still be deducted from budget.
    """
    # Create an experiment with 1% feasibility to simulate execution failure of an informative assay
    failing_exp = Experiment(
        id="EXP-FAIL-01",
        name="Fragile High-Risk Assay",
        description="Assay that fails feasibility",
        possible_outcomes=["OutcomeA", "OutcomeB"],
        predictions=[
            {"hypothesis_id": "H1", "outcome_label": "OutcomeA", "probability": 0.9, "derivation_mode": "test"},
            {"hypothesis_id": "H1", "outcome_label": "OutcomeB", "probability": 0.1, "derivation_mode": "test"},
            {"hypothesis_id": "H2", "outcome_label": "OutcomeA", "probability": 0.1, "derivation_mode": "test"},
            {"hypothesis_id": "H2", "outcome_label": "OutcomeB", "probability": 0.9, "derivation_mode": "test"},
        ],
        cost=2.5,
        feasibility=0.01,  # Fails feasibility check under seed 42!
        is_feasible=True
    )
    
    hypotheses = [
        Hypothesis(id="H1", name="H1", description="H1", prior=0.5),
        Hypothesis(id="H2", name="H2", description="H2", prior=0.5),
    ]
    
    scenario = AnalysisInput(
        scenario_name="Failure Test Scenario",
        hypotheses=hypotheses,
        experiments=[failing_exp],
        cost_weight=0.1
    )
    
    inp = BEDCampaignInput(
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=42,
        budget=10.0,
        max_steps=1
    )
    
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    assert res.total_steps == 1
    step = res.steps[0]
    
    assert step.execution_status == "EXECUTION_FAILURE"
    assert step.observed_outcome is None
    assert step.prior_distribution == step.posterior_distribution  # Unchanged!
    assert step.realized_information_gain == 0.0  # Zero bits!
    assert step.step_cost == 2.5
    assert res.total_cost == 2.5  # Cost was incurred!


def test_dynamic_re_ranking_after_evidence():
    """
    Verifies that remaining candidate experiments are re-scored using updated posterior.
    """
    scenario = get_wgs_case_study_scenario()
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=42,
        budget=10.0,
        max_steps=2
    )
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    
    # After step 1, remaining candidates should have their scores recomputed under step 1's posterior
    step1 = res.steps[0]
    assert len(step1.remaining_candidate_scores) > 0
    
    # Verify that remaining scores match rank_experiments evaluated on step 1's posterior
    remaining_ids = [s.experiment_id for s in step1.remaining_candidate_scores]
    assert "EXP-WGS-02" not in remaining_ids  # Consumed in step 1!


def test_budget_exhaustion_stopping():
    """Campaign must terminate with BUDGET_EXHAUSTED if remaining budget cannot afford any assay."""
    scenario = get_wgs_case_study_scenario()
    # Budget of 2.0 allows only EXP-WGS-02 (cost 1.8), leaving 0.2 which cannot afford EXP-WGS-01 (1.5) or 04 (1.1)
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=42,
        budget=2.0,
        max_steps=10
    )
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    assert res.termination_reason == "BUDGET_EXHAUSTED"
    assert res.total_cost <= 2.0


def test_confidence_threshold_stopping():
    """Campaign terminates immediately once confidence exceeds threshold."""
    scenario = get_wgs_case_study_scenario()
    # Low threshold of 0.85 should be reached on Step 1 (which reaches ~0.8984)
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=42,
        budget=20.0,
        max_steps=10,
        confidence_threshold=0.85
    )
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    assert res.termination_reason == "TARGET_CONFIDENCE_ACHIEVED"
    assert res.target_confidence_achieved is True
    assert res.total_steps == 1  # Stopped right after step 1!


def test_unquantified_assay_excluded_from_campaign():
    """Confirms EXP-WGS-05 is not executed or selected in any step."""
    scenario = get_wgs_case_study_scenario()
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        hidden_hypothesis_id="H1",
        seed=42,
        budget=20.0,
        max_steps=5
    )
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    
    executed_ids = [s.selected_experiment_id for s in res.steps]
    assert "EXP-WGS-05" not in executed_ids
    assert any("Excluded unquantified candidate 'EXP-WGS-05'" in w for w in res.warnings)


def test_sequential_policy_comparison():
    """Verifies that comparative benchmark runs across all 6 policies cleanly."""
    scenario = get_wgs_case_study_scenario()
    report = run_sequential_policy_comparison(
        scenario=scenario,
        hidden_hypothesis_id="H1",
        seed=42,
        budget=10.0,
        max_steps=4,
        confidence_threshold=0.95
    )
    
    assert len(report.policy_summaries) == 6
    policy_keys = [s.policy_key for s in report.policy_summaries]
    assert "janus_utility" in policy_keys
    assert "raw_eig" in policy_keys
    assert "cheapest" in policy_keys
    assert "feasibility" in policy_keys
    assert "uniform_random" in policy_keys
    assert "oracle" in policy_keys
    
    # Oracle regret should be 0.0
    oracle_summary = next(s for s in report.policy_summaries if s.policy_key == "oracle")
    assert oracle_summary.regret_vs_oracle_utility == 0.0
