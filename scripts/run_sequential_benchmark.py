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
    
    print(f"\n[4] MULTI-SEED & MULTI-HYPOTHESIS STATISTICAL AUDIT (20 Seeds x 3 Hypotheses):")
    print("  Executing 60 matched campaigns across all candidate policies...")
    audit = run_multiseed_sequential_evaluation(
        scenario=scenario,
        hidden_hypotheses=["H1", "H2", "H3"],
        seeds=list(range(1, 21)),
        budget=budget,
        max_steps=max_steps,
        confidence_threshold=threshold
    )
    
    for h_id in ["H1", "H2", "H3"]:
        h_data = audit["per_hypothesis"][h_id]
        off_mean = h_data["offline_upper_bound"]["mean_ig"]
        off_std = h_data["offline_upper_bound"]["std_ig"]
        print(f"\n  --- Ground Truth H* = {h_id} (Offline Upper Bound Mean IG: {off_mean:.4f} +/- {off_std:.4f} bits) ---")
        sub_header = f"    {'Policy':<36} {'Mean IG (bits)':<18} {'Mean Regret':<14} {'Mean P(H*)':<12} {'Mean Cost':<11} {'Mean 0-EIG':<10}"
        print(sub_header)
        print("    " + "-" * 98)
        for p_key, p_stats in h_data["policies"].items():
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
            
    # Overall summary across all 60 runs
    overall = audit["overall"]
    print(f"\n  --- Overall Across All 3 Hypotheses (60 Campaigns per Policy) ---")
    ov_off_mean = overall["offline_upper_bound"]["mean_ig"]
    ov_off_std = overall["offline_upper_bound"]["std_ig"]
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
        
    print("\n" + "=" * 104)


if __name__ == "__main__":
    main()
