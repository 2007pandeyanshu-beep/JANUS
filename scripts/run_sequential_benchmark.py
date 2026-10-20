"""JANUS Sequential BED Benchmark Evaluation CLI Runner

Executes matched-seed comparative campaigns comparing:
1. JANUS Composite Utility Optimization
2. Raw EIG Maximization (Ablation)
3. Naive Cost-Minimizer (Cheapest First)
4. Naive Feasibility-Maximizer (Easiest First)
5. Uniform Random Selection Baseline
6. Privileged Greedy Policy (H*-Informed)
7. True Offline Combinatorial Upper Bound (Reference)

Evaluated on Case Study CS-CAT-001 under Nature's simulated physical ground-truth.
Includes matched single-seed analysis and multi-seed / multi-hypothesis statistical audit.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scientific.evidence_ingestion import get_wgs_case_study_scenario
from evaluation.sequential_evaluation import (
    run_sequential_policy_comparison,
    run_multiseed_sequential_evaluation,
    run_synthetic_benchmark_suite,
    run_objective_sensitivity_audit,
)


def main():
    print("=" * 104)
    print(" JANUS SEQUENTIAL BAYESIAN EXPERIMENTAL DESIGN (BED) BENCHMARK & AUDIT (PHASE 5.1)")
    print(" Case Study: CS-CAT-001 (Pt/CeO2 WGS Catalysis) | Simulated Ground Truth H* = H1 (Redox)")
    print("=" * 104)
    
    scenario = get_wgs_case_study_scenario()
    seed = 42
    budget = 10.0
    threshold = 0.95
    max_steps = 6
    
    report = run_sequential_policy_comparison(
        scenario=scenario,
        hidden_hypothesis_id="H1",
        seed=seed,
        budget=budget,
        max_steps=max_steps,
        confidence_threshold=threshold
    )
    
    print(f"\n[1] CAMPAIGN CONFIGURATION (SEED 42):")
    print(f"  • Hidden Nature Truth:    {report.hidden_hypothesis_id} ({report.hidden_hypothesis_name})")
    print(f"  • Random Seed:            {report.seed} (pre-sampled counterfactual realization)")
    print(f"  • Budget Limit:           {report.budget:.1f}")
    print(f"  • Target Confidence:      {report.confidence_threshold*100:.0f}%")
    print(f"  • Offline Upper Bound:    {report.offline_optimal_ig_bits:.4f} bits via {report.offline_optimal_subset} (cost={report.offline_optimal_cost:.1f})")
    
    print(f"\n[2] COMPARATIVE POLICY RESULTS (SEED 42):")
    header = (
        f"  {'Policy':<42} {'P(H*)':<10} {'Steps':<6} {'Cost':<7} "
        f"{'Real. IG':<11} {'Failures':<9} {'0-EIG':<7} {'Target?':<8} {'Regret (Off)':<12}"
    )
    print(header)
    print("  " + "-" * 114)
    
    for s in report.policy_summaries:
        target_str = "YES" if s.target_confidence_achieved else "NO"
        line = (
            f"  {s.policy_name:<42} {s.final_confidence_h_star*100:>5.1f}%    "
            f"{s.total_steps:<6} {s.total_cost:<7.1f} {s.total_realized_ig_bits:<11.4f} "
            f"{s.execution_failures:<9} {s.zero_eig_selections:<7} {target_str:<8} "
            f"{s.regret_vs_offline_optimal:<12.4f}"
        )
        print(line)
        
    print("  " + "-" * 114)
    
    print(f"\n[3] SCIENTIFIC SUMMARY & OBSERVATIONS (SEED 42):")
    print(f"  {report.summary_verdict}")
    
    print(f"\n[4] MULTI-SEED & MULTI-HYPOTHESIS STATISTICAL AUDIT (50 Seeds x 3 Hypotheses = 150 Matched Campaigns):")
    print("  Executing 150 matched campaigns across all candidate policies on CS-CAT-001...")
    audit = run_multiseed_sequential_evaluation(
        scenario=scenario,
        hidden_hypotheses=["H1", "H2", "H3"],
        seeds=list(range(1, 51)),
        budget=budget,
        max_steps=max_steps,
        confidence_threshold=threshold
    )
    
    # Overall summary across all 150 runs
    overall = audit["overall"]
    ov_off_mean = overall["offline_upper_bound"]["mean_ig"]
    ov_off_std = overall["offline_upper_bound"]["std_ig"]
    print(f"\n  --- Overall Performance Across All 3 Hypotheses (150 Campaigns per Policy) ---")
    print(f"  Offline Upper Bound Across All Runs: {ov_off_mean:.4f} +/- {ov_off_std:.4f} bits")
    print(f"    {'Policy':<36} {'Mean IG (bits)':<18} {'Mean Regret':<14} {'Mean P(H*)':<12} {'Mean Cost':<11} {'Mean 0-EIG':<10}")
    print("    " + "-" * 98)
    for p_key, p_stats in overall["policies"].items():
        disp_name = next(p[1] for p in [
            ("janus_utility", "JANUS Composite Utility"),
            ("raw_eig", "Raw EIG Maximization"),
            ("cheapest", "Naive Cheapest"),
            ("feasibility", "Naive Feasibility"),
            ("uniform_random", "Uniform Random"),
            ("privileged_greedy", "Privileged Greedy (H*)"),
        ] if p[0] == p_key)
        line = (
            f"    {disp_name:<36} {p_stats['mean_ig']:.4f} +/- {p_stats['std_ig']:.3f}   "
            f"{p_stats['mean_regret']:.4f}        "
            f"{p_stats['mean_conf']*100:>5.1f}%      "
            f"{p_stats['mean_cost']:<11.1f} "
            f"{p_stats['mean_zero_eig']:<10.2f}"
        )
        print(line)
        
    print(f"\n[5] PAIRED STATISTICAL COMPARISONS VS. JANUS COMPOSITE UTILITY (N = 150 Paired Differences):")
    print(f"    {'Baseline':<28} {'Delta IG (95% CI)':<26} {'Cohen d':<10} {'p (raw)':<10} {'p (Holm)':<10} {'Delta Cost':<12}")
    print("    " + "-" * 98)
    for b_key, comp in overall["paired_comparisons_vs_janus"].items():
        ig = comp["ig_difference"]
        cost = comp["cost_difference"]
        ci_str = f"[{ig['ci_95'][0]:+.3f}, {ig['ci_95'][1]:+.3f}]"
        disp_name = next(p[1] for p in [
            ("raw_eig", "Raw EIG Maximization"),
            ("cheapest", "Naive Cheapest"),
            ("feasibility", "Naive Feasibility"),
            ("uniform_random", "Uniform Random"),
            ("privileged_greedy", "Privileged Greedy (H*)"),
        ] if p[0] == b_key)
        line = (
            f"    {disp_name:<28} {ig['mean_difference']:+.4f} {ci_str:<18} "
            f"{ig['cohen_d']:>+7.3f}   "
            f"{ig['raw_p_value']:<10.4f} "
            f"{ig['adjusted_p_value']:<10.4f} "
            f"{cost['mean_difference']:>+6.2f}"
        )
        print(line)
        print(f"      -> Verdict: {comp['statistical_verdict']}")
        
    print(f"\n[6] SYNTHETIC BENCHMARK SUITE EVALUATION (SYNTH-A THROUGH SYNTH-F):")
    print("  Evaluating all 6 benchmark archetypes across 10 independent seeds per archetype...")
    suite = run_synthetic_benchmark_suite(n_seeds=10, budget=budget)
    
    for s_key, s_data in suite["scenarios"].items():
        off = s_data["offline_upper_bound"]
        print(f"\n  === {s_key}: {s_data['scenario_name']} ===")
        print(f"  Hypotheses: {s_data['hypothesis_count']}, Candidate Experiments: {s_data['experiment_count']}")
        print(f"  Offline Upper Bound: {off['mean_ig']:.4f} +/- {off['std_ig']:.4f} bits")
        print(f"    {'Policy':<36} {'Mean IG (bits)':<18} {'Mean Regret':<14} {'Mean Cost':<11} {'Mean 0-EIG':<10}")
        print("    " + "-" * 88)
        for p_key, p_stats in s_data["policies"].items():
            disp_name = next(p[1] for p in [
                ("janus_utility", "JANUS Composite Utility"),
                ("raw_eig", "Raw EIG Maximization"),
                ("cheapest", "Naive Cheapest"),
                ("feasibility", "Naive Feasibility"),
                ("uniform_random", "Uniform Random"),
                ("privileged_greedy", "Privileged Greedy (H*)"),
            ] if p[0] == p_key)
            line = (
                f"    {disp_name:<36} {p_stats['mean_ig']:.4f} +/- {p_stats['std_ig']:.3f}   "
                f"{p_stats['mean_regret']:.4f}        "
                f"{p_stats['mean_cost']:<11.1f} "
                f"{p_stats['mean_zero_eig']:<10.2f}"
            )
            print(line)
            
    print(f"\n[7] COST-PENALTY SENSITIVITY AUDIT (Alpha in [0.0, 1.0] on CS-CAT-001):")
    sensitivity = run_objective_sensitivity_audit(scenario=scenario, seeds=list(range(1, 21)))
    print(f"    {'Alpha Weight':<18} {'Mean IG':<12} {'Mean Cost':<12} {'IG / Cost Efficiency':<22} {'Mean Conf(H*)':<15}")
    print("    " + "-" * 78)
    for a_key, a_data in sensitivity["alpha_evaluations"].items():
        line = (
            f"    alpha = {a_data['alpha']:<10.2f} "
            f"{a_data['mean_ig']:<12.4f} "
            f"{a_data['mean_cost']:<12.2f} "
            f"{a_data['ig_per_cost']:<22.4f} "
            f"{a_data['mean_confidence']*100:>5.1f}%"
        )
        print(line)
        
    print("\n" + "=" * 104)


if __name__ == "__main__":
    main()
