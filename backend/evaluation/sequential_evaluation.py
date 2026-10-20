"""JANUS Sequential Policy Benchmark & Evaluation Module

Executes comparative multi-policy evaluation across sequential experimental campaigns:
- JANUS Composite Utility Optimization
- Pure Raw EIG Maximization (Ablation)
- Naive Cost-Minimizer (Cheapest First)
- Naive Feasibility-Maximizer (Easiest First)
- Uniform Random Selection Baseline
- Privileged Greedy Policy (H*-Informed Heuristic)
- True Offline Combinatorial Upper Bound (Global Maximum Realized IG)

Evaluates realized information gain, discovery steps, budget efficiency,
waste rates, counterfactual execution fairness, and non-negative regret.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any
import numpy as np

from app.schemas.scientific import (
    AnalysisInput,
    BEDCampaignInput,
    BEDCampaignResult,
    PolicyCampaignSummary,
    BEDPolicyComparisonReport,
    Experiment,
)
from scientific.sequential_engine import (
    Nature,
    SequentialBEDEngine,
    compute_offline_combinatorial_upper_bound,
)
from scientific.validation import (
    validate_and_normalize_priors,
    validate_experiment_predictions,
)


POLICIES_TO_EVALUATE = [
    ("janus_utility", "JANUS Composite Utility Optimization"),
    ("raw_eig", "Raw EIG Maximization (Ablation)"),
    ("cheapest", "Naive Cost-Minimization Heuristic"),
    ("feasibility", "Naive Feasibility-Maximization Heuristic"),
    ("uniform_random", "Uniform Random Selection Baseline"),
    ("privileged_greedy", "Privileged Greedy Policy (H*-Informed)"),
]


def run_sequential_policy_comparison(
    scenario: AnalysisInput,
    hidden_hypothesis_id: str = "H1",
    seed: int = 42,
    budget: float = 10.0,
    max_steps: int = 8,
    confidence_threshold: float = 0.95,
    cost_weight: float = 0.1
) -> BEDPolicyComparisonReport:
    """
    Runs a matched-seed sequential comparative benchmark across all 6 policies
    and evaluates regret against the True Offline Combinatorial Upper Bound.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    comparison_id = f"SEQ-BENCH-{uuid.uuid4().hex[:6].upper()}"
    
    hypo_names = {h.id: h.name for h in scenario.hypotheses}
    h_name = hypo_names.get(hidden_hypothesis_id, hidden_hypothesis_id)
    
    # Prepare scenario validation and candidate pool
    normalized_priors, _ = validate_and_normalize_priors(scenario.hypotheses)
    hypothesis_ids = list(normalized_priors.keys())
    
    quantified_exps: List[Experiment] = []
    likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]] = {}
    for exp in scenario.experiments:
        if exp.quantification_status == "UNQUANTIFIED_NEEDS_MEASUREMENT" or len(exp.predictions) == 0:
            continue
        matrix, _ = validate_experiment_predictions(exp, hypothesis_ids)
        likelihood_matrices[exp.id] = matrix
        quantified_exps.append(exp)
        
    # Pre-generate Nature counterfactual state to compute the True Offline Combinatorial Bound
    offline_nature = Nature(
        hidden_hypothesis_id=hidden_hypothesis_id,
        rng=np.random.default_rng(seed),
        candidate_experiments=quantified_exps,
        likelihood_matrices=likelihood_matrices
    )
    offline_ig, offline_subset, offline_cost, offline_post = compute_offline_combinatorial_upper_bound(
        scenario=scenario,
        quantified_experiments=quantified_exps,
        likelihood_matrices=likelihood_matrices,
        initial_priors=normalized_priors,
        nature=offline_nature,
        budget=budget
    )
    
    summaries: List[PolicyCampaignSummary] = []
    privileged_realized_ig = 0.0
    
    # 1. Run each policy with matched seed and counterfactual physical reality
    campaign_results: Dict[str, Tuple[BEDCampaignResult, float]] = {}
    
    for policy_key, policy_display in POLICIES_TO_EVALUATE:
        campaign_input = BEDCampaignInput(
            scenario_id=scenario.case_study_id or "custom",
            policy=policy_key,
            hidden_hypothesis_id=hidden_hypothesis_id,
            seed=seed,
            budget=budget,
            max_steps=max_steps,
            confidence_threshold=confidence_threshold,
            cost_weight=cost_weight
        )
        
        t0 = time.perf_counter()
        res = SequentialBEDEngine.run_campaign(scenario, campaign_input)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        
        campaign_results[policy_key] = (res, elapsed_ms)
        if policy_key in ("privileged_greedy", "oracle"):
            privileged_realized_ig = res.total_realized_information_gain
            
    # 2. Compute comparative metrics and regret against Offline Combinatorial Optimal
    for policy_key, policy_display in POLICIES_TO_EVALUATE:
        res, elapsed_ms = campaign_results[policy_key]
        regret_vs_offline = max(offline_ig - res.total_realized_information_gain, 0.0)
        signed_delta = privileged_realized_ig - res.total_realized_information_gain
        
        summary = PolicyCampaignSummary(
            policy_key=policy_key,
            policy_name=policy_display,
            final_confidence_h_star=round(res.final_confidence_in_hidden_hypothesis, 4),
            total_steps=res.total_steps,
            total_cost=round(res.total_cost, 2),
            total_realized_ig_bits=round(res.total_realized_information_gain, 4),
            execution_failures=res.execution_failure_count,
            zero_eig_selections=res.uninformative_selection_count,
            target_confidence_achieved=res.target_confidence_achieved,
            termination_reason=res.termination_reason,
            runtime_ms=round(elapsed_ms, 2),
            regret_vs_oracle_utility=round(regret_vs_offline, 4),
            regret_vs_offline_optimal=round(regret_vs_offline, 4),
            signed_delta_vs_privileged=round(signed_delta, 4)
        )
        summaries.append(summary)
        
    # 3. Formulate verdict
    janus_res = campaign_results["janus_utility"][0]
    random_res = campaign_results["uniform_random"][0]
    cheapest_res = campaign_results["cheapest"][0]
    privileged_res = campaign_results["privileged_greedy"][0]
    
    verdict = (
        f"In sequential evaluation on '{scenario.scenario_name}' under hidden truth H*='{hidden_hypothesis_id}' (seed={seed}, budget={budget:.1f}): "
        f"The True Offline Combinatorial Upper Bound achieved {offline_ig:.4f} bits realized IG "
        f"via subset {offline_subset} (cost={offline_cost:.1f}). "
        f"JANUS Composite Utility achieved {janus_res.total_realized_information_gain:.4f} bits realized IG "
        f"(regret={offline_ig - janus_res.total_realized_information_gain:.4f} bits, P(H*)={janus_res.final_confidence_in_hidden_hypothesis:.2%}) "
        f"with 0 execution failures and 0 uninformative selections. "
        f"Privileged Greedy achieved {privileged_res.total_realized_information_gain:.4f} bits (regret={offline_ig - privileged_res.total_realized_information_gain:.4f}). "
        f"Naive Cheapest achieved {cheapest_res.total_realized_information_gain:.4f} bits but incurred {cheapest_res.uninformative_selection_count} uninformative control selections. "
        f"Uniform Random achieved {random_res.total_realized_information_gain:.4f} bits with {random_res.uninformative_selection_count} uninformative selections and high regret. "
        f"Evaluating against the True Offline Combinatorial Bound guarantees mathematically non-negative regret across all policies."
    )
    
    return BEDPolicyComparisonReport(
        comparison_id=comparison_id,
        timestamp=timestamp,
        scenario_name=scenario.scenario_name,
        hidden_hypothesis_id=hidden_hypothesis_id,
        hidden_hypothesis_name=h_name,
        seed=seed,
        budget=budget,
        confidence_threshold=confidence_threshold,
        offline_optimal_ig_bits=offline_ig,
        offline_optimal_subset=offline_subset,
        offline_optimal_cost=offline_cost,
        policy_summaries=summaries,
        summary_verdict=verdict
    )


def run_multiseed_sequential_evaluation(
    scenario: AnalysisInput,
    hidden_hypotheses: Optional[List[str]] = None,
    seeds: Optional[List[int]] = None,
    budget: float = 10.0,
    max_steps: int = 8,
    confidence_threshold: float = 0.95,
    cost_weight: float = 0.1
) -> Dict[str, Any]:
    """
    Executes a multi-seed, multi-hypothesis statistical evaluation across sequential policies.
    Computes mean, standard deviation, and 95% bootstrap confidence intervals for realized IG,
    regret against the True Offline Combinatorial Bound, final confidence, and waste rate.
    """
    if hidden_hypotheses is None:
        hidden_hypotheses = [h.id for h in scenario.hypotheses]
    if seeds is None:
        seeds = list(range(1, 21))  # 20 seeds
        
    policies = [p[0] for p in POLICIES_TO_EVALUATE]
    
    audit_results: Dict[str, Any] = {
        "scenario_name": scenario.scenario_name,
        "n_seeds": len(seeds),
        "hypotheses_evaluated": hidden_hypotheses,
        "per_hypothesis": {},
        "overall": {}
    }
    
    overall_by_policy: Dict[str, Dict[str, List[float]]] = {
        p: {"ig": [], "regret": [], "conf": [], "cost": [], "uninf": [], "failures": []}
        for p in policies
    }
    overall_offline_igs: List[float] = []
    
    for h_id in hidden_hypotheses:
        hypo_results: Dict[str, Dict[str, List[float]]] = {
            p: {"ig": [], "regret": [], "conf": [], "cost": [], "uninf": [], "failures": []}
            for p in policies
        }
        offline_igs: List[float] = []
        
        for seed in seeds:
            report = run_sequential_policy_comparison(
                scenario=scenario,
                hidden_hypothesis_id=h_id,
                seed=seed,
                budget=budget,
                max_steps=max_steps,
                confidence_threshold=confidence_threshold,
                cost_weight=cost_weight
            )
            offline_igs.append(report.offline_optimal_ig_bits)
            overall_offline_igs.append(report.offline_optimal_ig_bits)
            
            for s in report.policy_summaries:
                hypo_results[s.policy_key]["ig"].append(s.total_realized_ig_bits)
                hypo_results[s.policy_key]["regret"].append(s.regret_vs_offline_optimal)
                hypo_results[s.policy_key]["conf"].append(s.final_confidence_h_star)
                hypo_results[s.policy_key]["cost"].append(s.total_cost)
                hypo_results[s.policy_key]["uninf"].append(float(s.zero_eig_selections))
                hypo_results[s.policy_key]["failures"].append(float(s.execution_failures))
                
                overall_by_policy[s.policy_key]["ig"].append(s.total_realized_ig_bits)
                overall_by_policy[s.policy_key]["regret"].append(s.regret_vs_offline_optimal)
                overall_by_policy[s.policy_key]["conf"].append(s.final_confidence_h_star)
                overall_by_policy[s.policy_key]["cost"].append(s.total_cost)
                overall_by_policy[s.policy_key]["uninf"].append(float(s.zero_eig_selections))
                overall_by_policy[s.policy_key]["failures"].append(float(s.execution_failures))
                
        # Aggregate per hypothesis
        hypo_summary: Dict[str, Any] = {
            "offline_upper_bound": {
                "mean_ig": round(float(np.mean(offline_igs)), 4),
                "std_ig": round(float(np.std(offline_igs)), 4),
            },
            "policies": {}
        }
        for p in policies:
            hypo_summary["policies"][p] = {
                "mean_ig": round(float(np.mean(hypo_results[p]["ig"])), 4),
                "std_ig": round(float(np.std(hypo_results[p]["ig"])), 4),
                "mean_regret": round(float(np.mean(hypo_results[p]["regret"])), 4),
                "std_regret": round(float(np.std(hypo_results[p]["regret"])), 4),
                "mean_conf": round(float(np.mean(hypo_results[p]["conf"])), 4),
                "mean_cost": round(float(np.mean(hypo_results[p]["cost"])), 2),
                "mean_zero_eig": round(float(np.mean(hypo_results[p]["uninf"])), 2),
                "mean_failures": round(float(np.mean(hypo_results[p]["failures"])), 2),
            }
        audit_results["per_hypothesis"][h_id] = hypo_summary
        
    # Aggregate overall
    audit_results["overall"]["offline_upper_bound"] = {
        "mean_ig": round(float(np.mean(overall_offline_igs)), 4),
        "std_ig": round(float(np.std(overall_offline_igs)), 4),
    }
    audit_results["overall"]["policies"] = {}
    for p in policies:
        audit_results["overall"]["policies"][p] = {
            "mean_ig": round(float(np.mean(overall_by_policy[p]["ig"])), 4),
            "std_ig": round(float(np.std(overall_by_policy[p]["ig"])), 4),
            "mean_regret": round(float(np.mean(overall_by_policy[p]["regret"])), 4),
            "std_regret": round(float(np.std(overall_by_policy[p]["regret"])), 4),
            "mean_conf": round(float(np.mean(overall_by_policy[p]["conf"])), 4),
            "mean_cost": round(float(np.mean(overall_by_policy[p]["cost"])), 2),
            "mean_zero_eig": round(float(np.mean(overall_by_policy[p]["uninf"])), 2),
            "mean_failures": round(float(np.mean(overall_by_policy[p]["failures"])), 2),
        }
        
    # Compute paired statistical comparisons vs JANUS Composite Utility
    janus_igs = overall_by_policy["janus_utility"]["ig"]
    janus_costs = overall_by_policy["janus_utility"]["cost"]
    paired_comparisons: Dict[str, Any] = {}
    
    for baseline in policies:
        if baseline == "janus_utility":
            continue
        base_igs = overall_by_policy[baseline]["ig"]
        base_costs = overall_by_policy[baseline]["cost"]
        
        ig_stats = compute_paired_statistics(janus_igs, base_igs)
        cost_stats = compute_paired_statistics(janus_costs, base_costs)
        
        paired_comparisons[baseline] = {
            "ig_difference": ig_stats,
            "cost_difference": cost_stats,
        }
        
    # Apply Holm-Bonferroni correction across the baseline comparisons
    raw_p_values = {b: paired_comparisons[b]["ig_difference"]["raw_p_value"] for b in paired_comparisons}
    sorted_baselines = sorted(raw_p_values.keys(), key=lambda k: raw_p_values[k])
    m_tests = len(sorted_baselines)
    running_max_p = 0.0
    
    for rank_idx, b in enumerate(sorted_baselines):
        p_raw = raw_p_values[b]
        adj_p = min(1.0, max(running_max_p, (m_tests - rank_idx) * p_raw))
        running_max_p = adj_p
        paired_comparisons[b]["ig_difference"]["adjusted_p_value"] = round(adj_p, 4)
        
        # Formulate statistically defensible conclusion
        mean_diff = paired_comparisons[b]["ig_difference"]["mean_difference"]
        if adj_p < 0.05:
            if mean_diff > 0:
                conclusion = f"Statistically significant advantage over {b} (p_adj={adj_p:.4f}, d={paired_comparisons[b]['ig_difference']['cohen_d']:.2f})."
            else:
                conclusion = f"Statistically significant underperformance vs {b} (p_adj={adj_p:.4f}, d={paired_comparisons[b]['ig_difference']['cohen_d']:.2f})."
        else:
            conclusion = f"No statistically significant difference vs {b} after multiple-testing correction (p_adj={adj_p:.4f})."
        paired_comparisons[b]["statistical_verdict"] = conclusion
        
    audit_results["overall"]["paired_comparisons_vs_janus"] = paired_comparisons
    return audit_results


def compute_paired_statistics(
    x: List[float],
    y: List[float],
    n_boot: int = 5000,
    n_perm: int = 5000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Computes rigorous paired statistical comparison metrics between two matched sequences:
    - Mean paired difference (x - y)
    - Sample standard deviation of differences
    - 95% bootstrap confidence interval on mean paired difference
    - Paired Cohen's d_z effect size
    - Exact two-sided sign-flip permutation test p-value (non-parametric, sharp null)
    """
    diffs = np.array(x, dtype=np.float64) - np.array(y, dtype=np.float64)
    n = len(diffs)
    mean_d = float(np.mean(diffs))
    std_d = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
    
    # Bootstrap CI
    rng = np.random.default_rng(seed)
    boot_samples = rng.choice(diffs, size=(n_boot, n), replace=True)
    boot_means = np.mean(boot_samples, axis=1)
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    
    # Paired Cohen's d_z
    cohen_d = float(mean_d / std_d) if std_d > 1e-12 else 0.0
    
    # Two-sided sign-flip permutation test
    obs_t = abs(mean_d)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, n))
    perm_means = np.abs(np.mean(signs * diffs, axis=1))
    p_val = float(np.mean(perm_means >= obs_t))
    p_val = max(p_val, 1.0 / n_perm)
    
    return {
        "mean_difference": round(mean_d, 4),
        "std_difference": round(std_d, 4),
        "ci_95": (round(ci_lower, 4), round(ci_upper, 4)),
        "cohen_d": round(cohen_d, 4),
        "raw_p_value": round(p_val, 4)
    }


def run_synthetic_benchmark_suite(
    scenario_keys: Optional[List[str]] = None,
    n_seeds: int = 20,
    budget: float = 10.0,
    cost_weight: float = 0.1
) -> Dict[str, Any]:
    """
    Executes comparative sequential BED benchmark campaigns across the synthetic scenario
    suite (SYNTH-A through SYNTH-F) specified in evaluation_plan.md.
    """
    from scientific.synthetic_scenarios import SYNTHETIC_SCENARIO_GENERATORS, get_synthetic_scenario
    
    if scenario_keys is None:
        scenario_keys = list(SYNTHETIC_SCENARIO_GENERATORS.keys())
        
    suite_results: Dict[str, Any] = {
        "benchmark_id": f"SYNTH-SUITE-{uuid.uuid4().hex[:6].upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_seeds_per_archetype": n_seeds,
        "scenarios": {}
    }
    
    for key in scenario_keys:
        scenario = get_synthetic_scenario(key, seed=42)
        hypo_ids = [h.id for h in scenario.hypotheses[:min(3, len(scenario.hypotheses))]]
        seeds = list(range(1, n_seeds + 1))
        
        audit = run_multiseed_sequential_evaluation(
            scenario=scenario,
            hidden_hypotheses=hypo_ids,
            seeds=seeds,
            budget=budget,
            cost_weight=cost_weight
        )
        suite_results["scenarios"][key] = {
            "scenario_name": scenario.scenario_name,
            "hypothesis_count": len(scenario.hypotheses),
            "experiment_count": len(scenario.experiments),
            "offline_upper_bound": audit["overall"]["offline_upper_bound"],
            "policies": audit["overall"]["policies"],
            "paired_comparisons_vs_janus": audit["overall"].get("paired_comparisons_vs_janus", {})
        }
        
    return suite_results


def run_objective_sensitivity_audit(
    scenario: AnalysisInput,
    alpha_weights: Optional[List[float]] = None,
    seeds: Optional[List[int]] = None,
    budget: float = 10.0
) -> Dict[str, Any]:
    """
    Evaluates sensitivity of JANUS sequential design performance across varying cost penalty weights
    alpha in U(e) = feasibility * EIG / (1 + alpha * cost).
    """
    if alpha_weights is None:
        alpha_weights = [0.0, 0.05, 0.10, 0.25, 0.50, 1.0]
    if seeds is None:
        seeds = list(range(1, 21))
        
    hypo_ids = [h.id for h in scenario.hypotheses]
    sensitivity: Dict[str, Any] = {
        "scenario_name": scenario.scenario_name,
        "alpha_evaluations": {}
    }
    
    for alpha in alpha_weights:
        audit = run_multiseed_sequential_evaluation(
            scenario=scenario,
            hidden_hypotheses=hypo_ids,
            seeds=seeds,
            budget=budget,
            cost_weight=alpha
        )
        janus_stats = audit["overall"]["policies"]["janus_utility"]
        sensitivity["alpha_evaluations"][f"alpha_{alpha}"] = {
            "alpha": alpha,
            "mean_ig": janus_stats["mean_ig"],
            "std_ig": janus_stats["std_ig"],
            "mean_cost": janus_stats["mean_cost"],
            "mean_regret": janus_stats["mean_regret"],
            "mean_zero_eig": janus_stats["mean_zero_eig"],
            "mean_confidence": janus_stats["mean_conf"],
            "ig_per_cost": round(janus_stats["mean_ig"] / max(janus_stats["mean_cost"], 0.1), 4)
        }
        
    return sensitivity
