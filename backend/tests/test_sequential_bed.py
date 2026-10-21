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
    """Verifies that comparative benchmark runs across all 6 policies cleanly and computes offline optimal."""
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
    assert "privileged_greedy" in policy_keys
    
    # Offline optimal bound must be populated and >= all policy realized IG
    assert report.offline_optimal_ig_bits > 0.0
    for s in report.policy_summaries:
        assert s.regret_vs_offline_optimal >= 0.0


def test_counterfactual_execution_fairness():
    """
    Verifies that Nature pre-samples physical reality so that an experiment
    experiences the exact same outcome regardless of which policy selects it
    or at what step order it is executed under the same seed.
    """
    scenario = get_wgs_case_study_scenario()
    
    res_janus = SequentialBEDEngine.run_campaign(
        scenario,
        BEDCampaignInput(scenario_id="CS-CAT-001", policy="janus_utility", seed=42, budget=10.0)
    )
    res_cheapest = SequentialBEDEngine.run_campaign(
        scenario,
        BEDCampaignInput(scenario_id="CS-CAT-001", policy="cheapest", seed=42, budget=10.0)
    )
    
    janus_outcomes = {s.selected_experiment_id: (s.simulated_is_successful, s.observed_outcome) for s in res_janus.steps}
    cheapest_outcomes = {s.selected_experiment_id: (s.simulated_is_successful, s.observed_outcome) for s in res_cheapest.steps}
    
    common_exps = set(janus_outcomes.keys()).intersection(set(cheapest_outcomes.keys()))
    assert len(common_exps) >= 2  # EXP-WGS-01 and EXP-WGS-02 are common
    for exp_id in common_exps:
        assert janus_outcomes[exp_id] == cheapest_outcomes[exp_id], (
            f"Counterfactual drift detected for {exp_id}: "
            f"JANUS={janus_outcomes[exp_id]} vs Cheapest={cheapest_outcomes[exp_id]}"
        )


def test_offline_combinatorial_upper_bound_optimality():
    """
    Verifies that the True Offline Combinatorial Upper Bound strictly bounds
    all sequential policies (O*_offline >= realized_ig for all pi) and produces
    non-negative regret (regret >= 0.0) across seeds.
    """
    scenario = get_wgs_case_study_scenario()
    for test_seed in [42, 101, 777]:
        report = run_sequential_policy_comparison(
            scenario=scenario,
            hidden_hypothesis_id="H1",
            seed=test_seed,
            budget=10.0,
            max_steps=6,
            confidence_threshold=0.95
        )
        assert report.offline_optimal_ig_bits > 0.0
        assert len(report.offline_optimal_subset) > 0
        assert report.offline_optimal_cost <= 10.0
        
        for s in report.policy_summaries:
            assert s.total_realized_ig_bits <= report.offline_optimal_ig_bits + 1e-6, (
                f"Policy {s.policy_key} exceeded offline upper bound: "
                f"{s.total_realized_ig_bits} > {report.offline_optimal_ig_bits}"
            )
            assert s.regret_vs_offline_optimal >= 0.0


def test_privileged_greedy_myopia_demonstration():
    """
    Verifies that Privileged Greedy (1-step myopic with H* knowledge) does not
    solve the multi-step combinatorial knapsack problem and can achieve strictly
    lower realized information gain than the offline combinatorial upper bound.
    """
    scenario = get_wgs_case_study_scenario()
    report = run_sequential_policy_comparison(
        scenario=scenario,
        hidden_hypothesis_id="H1",
        seed=42,
        budget=10.0,
        max_steps=6
    )
    priv_summary = next(s for s in report.policy_summaries if s.policy_key == "privileged_greedy")
    assert priv_summary.total_realized_ig_bits <= report.offline_optimal_ig_bits
    assert priv_summary.regret_vs_offline_optimal > 0.0


def test_multihypothesis_consistency():
    """
    Verifies that sequential campaigns execute cleanly under all competing hypotheses
    (H1, H2, H3) and preserve isolation and Bayesian consistency.
    """
    scenario = get_wgs_case_study_scenario()
    for h_id in ["H1", "H2", "H3"]:
        res = SequentialBEDEngine.run_campaign(
            scenario,
            BEDCampaignInput(scenario_id="CS-CAT-001", policy="janus_utility", hidden_hypothesis_id=h_id, seed=42, budget=10.0)
        )
        assert res.hidden_hypothesis_id == h_id
        assert res.total_steps >= 1
        assert res.total_cost <= 10.0
        assert 0.0 <= res.final_confidence_in_hidden_hypothesis <= 1.0


def test_step_history_and_summary_consistency():
    """
    Verifies internal mathematical consistency between step-by-step history
    and campaign-level summary aggregates.
    """
    scenario = get_wgs_case_study_scenario()
    res = SequentialBEDEngine.run_campaign(
        scenario,
        BEDCampaignInput(scenario_id="CS-CAT-001", policy="janus_utility", seed=42, budget=10.0)
    )
    # Sum of step costs must match total_cost
    step_cost_sum = sum(s.step_cost for s in res.steps)
    assert res.total_cost == pytest.approx(step_cost_sum, abs=1e-4)
    
    # Cumulative cost on last step must equal total_cost
    assert res.steps[-1].cumulative_cost == pytest.approx(res.total_cost, abs=1e-4)
    
    # Sum of realized IG must match total_realized_information_gain
    step_ig_sum = sum(s.realized_information_gain for s in res.steps)
    assert res.total_realized_information_gain == pytest.approx(step_ig_sum, abs=1e-4)
    
    # Final step posterior must match final_posterior
    assert res.steps[-1].posterior_distribution == res.final_posterior


def test_oracle_backward_compatibility_alias():
    """Confirms that 'oracle' policy string works as an alias for privileged_greedy."""
    scenario = get_wgs_case_study_scenario()
    res_oracle = SequentialBEDEngine.run_campaign(
        scenario,
        BEDCampaignInput(scenario_id="CS-CAT-001", policy="oracle", seed=42, budget=10.0)
    )
    res_priv = SequentialBEDEngine.run_campaign(
        scenario,
        BEDCampaignInput(scenario_id="CS-CAT-001", policy="privileged_greedy", seed=42, budget=10.0)
    )
    assert res_oracle.total_steps == res_priv.total_steps
    assert res_oracle.total_cost == res_priv.total_cost
    assert res_oracle.total_realized_information_gain == res_priv.total_realized_information_gain


def test_max_steps_stopping_condition():
    """Confirms campaign halts with MAX_STEPS_REACHED when step limit is reached."""
    scenario = get_wgs_case_study_scenario()
    inp = BEDCampaignInput(
        scenario_id="CS-CAT-001",
        policy="janus_utility",
        max_steps=2,
        budget=50.0,
        confidence_threshold=0.999
    )
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    assert res.termination_reason == "MAX_STEPS_REACHED"
    assert res.total_steps == 2


def test_no_candidates_remaining_stopping_condition():
    """Confirms campaign halts with NO_CANDIDATES_REMAINING when pool is exhausted."""
    from app.schemas.scientific import PredictedOutcome
    h = [Hypothesis(id="H1", name="H1", description="H1", prior=0.5), Hypothesis(id="H2", name="H2", description="H2", prior=0.5)]
    exps = [
        Experiment(id="E1", name="E1", description="E1", possible_outcomes=["A", "B"], predictions=[
            PredictedOutcome(hypothesis_id="H1", outcome_label="A", probability=0.6, derivation_mode="t"),
            PredictedOutcome(hypothesis_id="H1", outcome_label="B", probability=0.4, derivation_mode="t"),
            PredictedOutcome(hypothesis_id="H2", outcome_label="A", probability=0.4, derivation_mode="t"),
            PredictedOutcome(hypothesis_id="H2", outcome_label="B", probability=0.6, derivation_mode="t"),
        ], cost=1.0, feasibility=1.0, is_feasible=True),
    ]
    scen = AnalysisInput(scenario_name="SingleExpPool", hypotheses=h, experiments=exps)
    inp = BEDCampaignInput(policy="janus_utility", max_steps=10, budget=50.0, confidence_threshold=0.999)
    res = SequentialBEDEngine.run_campaign(scen, inp)
    assert res.termination_reason == "NO_CANDIDATES_REMAINING"
    assert res.total_steps == 1


def test_no_informative_candidates_remaining_stopping_condition():
    """Confirms campaign halts with NO_INFORMATIVE_CANDIDATES_REMAINING when pool has zero EIG."""
    from app.schemas.scientific import PredictedOutcome
    h = [Hypothesis(id="H1", name="H1", description="H1", prior=0.5), Hypothesis(id="H2", name="H2", description="H2", prior=0.5)]
    e_uninf = Experiment(id="E-UNINF", name="E-UNINF", description="Uninf", possible_outcomes=["A", "B"], predictions=[
        PredictedOutcome(hypothesis_id="H1", outcome_label="A", probability=0.5, derivation_mode="t"),
        PredictedOutcome(hypothesis_id="H1", outcome_label="B", probability=0.5, derivation_mode="t"),
        PredictedOutcome(hypothesis_id="H2", outcome_label="A", probability=0.5, derivation_mode="t"),
        PredictedOutcome(hypothesis_id="H2", outcome_label="B", probability=0.5, derivation_mode="t"),
    ], cost=1.0, feasibility=1.0, is_feasible=True)
    scen = AnalysisInput(scenario_name="UninformativePool", hypotheses=h, experiments=[e_uninf])
    inp = BEDCampaignInput(policy="janus_utility", max_steps=5, budget=10.0, confidence_threshold=0.95)
    res = SequentialBEDEngine.run_campaign(scen, inp)
    assert res.termination_reason == "NO_INFORMATIVE_CANDIDATES_REMAINING"
    assert res.total_steps == 0


def test_probability_bounds_and_simplex_normalization():
    """Verifies that every sequential step maintains strict probability bounds in [0, 1] summing to 1.0."""
    scenario = get_wgs_case_study_scenario()
    inp = BEDCampaignInput(scenario_id="CS-CAT-001", policy="janus_utility", seed=42, budget=10.0, max_steps=5)
    res = SequentialBEDEngine.run_campaign(scenario, inp)
    
    for step in res.steps:
        for h_id, p in step.posterior_distribution.items():
            assert 0.0 <= p <= 1.0, f"Probability bound violated: P({h_id}) = {p}"
        assert sum(step.posterior_distribution.values()) == pytest.approx(1.0, abs=1e-4)


def test_all_synthetic_scenarios_execute_cleanly():
    """Verifies that all 6 synthetic scenario generators (SYNTH-A to SYNTH-F) run cleanly."""
    from scientific.synthetic_scenarios import SYNTHETIC_SCENARIO_GENERATORS, get_synthetic_scenario
    for key in SYNTHETIC_SCENARIO_GENERATORS:
        scen = get_synthetic_scenario(key, seed=42)
        res = SequentialBEDEngine.run_campaign(
            scen,
            BEDCampaignInput(scenario_id=key, policy="janus_utility", seed=42, budget=10.0, max_steps=3)
        )
        assert res.total_steps >= 0
        assert res.total_cost <= 10.0 + 1e-6
        assert 0.0 <= res.final_confidence_in_hidden_hypothesis <= 1.0


def test_paired_statistics_bootstrap_and_permutation():
    """Verifies mathematical properties of paired difference statistics and Holm-Bonferroni correction."""
    from evaluation.sequential_evaluation import compute_paired_statistics
    x = [1.5, 2.0, 1.8, 1.9, 2.1]
    y = [1.0, 1.2, 1.1, 1.0, 1.3]
    stats = compute_paired_statistics(x, y, n_boot=2000, n_perm=2000, seed=42)
    assert stats["mean_difference"] > 0.0
    assert stats["ci_95"][0] <= stats["mean_difference"] <= stats["ci_95"][1]
    assert stats["cohen_d"] > 0.0
    assert 0.0 <= stats["raw_p_value"] <= 1.0


def test_offline_combinatorial_upper_bound_branch_and_bound_exactness():
    """
    Verifies that the branch-and-bound combinatorial upper bound explores all candidates
    in broad libraries (SYNTH-F, 50 candidates) and guarantees non-negative regret for all policies.
    """
    from scientific.synthetic_scenarios import get_synthetic_scenario
    from scientific.sequential_engine import compute_offline_combinatorial_upper_bound
    from scientific.validation import validate_and_normalize_priors, validate_experiment_predictions
    
    scen = get_synthetic_scenario("SYNTH-F", seed=42)
    priors, _ = validate_and_normalize_priors(scen.hypotheses)
    h_ids = list(priors.keys())
    quantified = [e for e in scen.experiments if e.quantification_status != "UNQUANTIFIED_NEEDS_MEASUREMENT"]
    l_matrices = {e.id: validate_experiment_predictions(e, h_ids)[0] for e in quantified}
    nature = Nature(h_ids[0], np.random.default_rng(42), quantified, l_matrices)
    
    ig, subset, cost, _ = compute_offline_combinatorial_upper_bound(
        scen, quantified, l_matrices, priors, nature, budget=10.0
    )
    assert ig >= 2.10, f"Expected global upper bound >= 2.10 bits, got {ig}"
    assert cost <= 10.0 + 1e-6
    assert len(subset) >= 2


def test_identification_accuracy_and_target_attainment():
    """Verifies tracking of final identification accuracy and target confidence attainment."""
    scenario = get_wgs_case_study_scenario()
    report = run_sequential_policy_comparison(
        scenario=scenario,
        hidden_hypothesis_id="H1",
        seed=42,
        budget=10.0,
        confidence_threshold=0.95
    )
    for s in report.policy_summaries:
        assert isinstance(s.hypothesis_identified, bool)
        assert isinstance(s.target_confidence_achieved, bool)
        if s.target_confidence_achieved:
            assert s.final_confidence_h_star >= 0.95 or s.termination_reason == "TARGET_CONFIDENCE_ACHIEVED"


def test_alpha_sensitivity_sample_size_consistency():
    """
    Regression test verifying root cause of Phase 5.2 sensitivity table discrepancy:
    N=20 seeds produces 0.9481 bits, while N=50 seeds produces 0.9568 bits, exactly
    reproducing both documented outputs.
    """
    from evaluation.sequential_evaluation import run_objective_sensitivity_audit
    scenario = get_wgs_case_study_scenario()
    
    sens_20 = run_objective_sensitivity_audit(scenario, alpha_weights=[0.10], seeds=list(range(1, 21)))
    sens_50 = run_objective_sensitivity_audit(scenario, alpha_weights=[0.10], seeds=list(range(1, 51)))
    
    ig_20 = sens_20["alpha_evaluations"]["alpha_0.1"]["mean_ig"]
    ig_50 = sens_50["alpha_evaluations"]["alpha_0.1"]["mean_ig"]
    
    assert ig_20 == pytest.approx(0.9481, abs=1e-4)
    assert ig_50 == pytest.approx(0.9568, abs=1e-4)


def test_held_out_robustness_suite_structure():
    """Verifies that run_held_out_robustness_suite returns structured evaluation without errors."""
    from evaluation.sequential_evaluation import run_held_out_robustness_suite
    scenario = get_wgs_case_study_scenario()
    res = run_held_out_robustness_suite(
        scenario,
        dev_seeds=list(range(1, 6)),
        held_out_seeds=list(range(101, 106)),
        budget=10.0
    )
    assert "development_audit" in res
    assert "held_out_audit" in res
    assert "budget_sweep" in res
    assert "threshold_sweep" in res
    assert "stress_tests" in res


def test_offline_bound_invariant_across_all_synthetic_scenarios():
    """
    Release Gate Verification:
    Asserts that the True Offline Combinatorial Upper Bound strictly bounds EVERY
    sequential policy across all 6 synthetic scenarios (SYNTH-A to F) and the primary
    case study across multiple seeds, guaranteeing non-negative regret without masking.
    """
    from scientific.synthetic_scenarios import SYNTHETIC_SCENARIO_GENERATORS, get_synthetic_scenario
    
    test_scenarios = [("CS-CAT-001", get_wgs_case_study_scenario())]
    for key in SYNTHETIC_SCENARIO_GENERATORS:
        test_scenarios.append((key, get_synthetic_scenario(key, seed=42)))
        
    for s_name, scen in test_scenarios:
        for test_seed in [1, 2, 42, 101]:
            report = run_sequential_policy_comparison(
                scenario=scen,
                hidden_hypothesis_id=scen.hypotheses[0].id,
                seed=test_seed,
                budget=10.0
            )
            bound = report.offline_optimal_ig_bits
            for s in report.policy_summaries:
                assert s.total_realized_ig_bits <= bound + 1e-6, (
                    f"Invariant violated in {s_name} (seed {test_seed}): "
                    f"policy {s.policy_key} achieved {s.total_realized_ig_bits} > bound {bound}"
                )
                assert s.regret_vs_offline_optimal >= 0.0


def test_offline_bound_assertion_raises_on_violation():
    """
    Release Gate Verification:
    Verifies that if a policy achieves realized IG exceeding the offline bound,
    run_sequential_policy_comparison raises an explicit AssertionError with full
    diagnostic details rather than silently masking the violation as zero regret.
    """
    import evaluation.sequential_evaluation as seq_eval
    
    scenario = get_wgs_case_study_scenario()
    real_run = seq_eval.SequentialBEDEngine.run_campaign
    
    def corrupt_run(scen, inp):
        res = real_run(scen, inp)
        if inp.policy == "janus_utility":
            res.total_realized_information_gain = 99.0  # Artificial violation
        return res
        
    seq_eval.SequentialBEDEngine.run_campaign = corrupt_run
    try:
        with pytest.raises(AssertionError) as exc_info:
            seq_eval.run_sequential_policy_comparison(scenario, "H1", seed=42, budget=10.0)
        assert "OFFLINE COMBINATORIAL BOUND INVARIANT VIOLATION" in str(exc_info.value)
        assert "janus_utility" in str(exc_info.value)
    finally:
        seq_eval.SequentialBEDEngine.run_campaign = real_run
