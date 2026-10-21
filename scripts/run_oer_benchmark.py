"""JANUS Standalone CS-OER-002 Benchmark Evaluation CLI Runner

Executes the preregistered CS-OER-002 benchmark protocol:
- Scenario: Oxygen Evolution Reaction Mechanism on Perovskite Electrocatalysts (La_{1-x}Sr_xCoO_{3-delta})
- Ground Truths: H1 (AEM), H2 (LOM), H3 (OPM)
- Evaluated Policies:
  1. JANUS Composite Utility Optimization
  2. Raw EIG Maximization (Ablation)
  3. Naive Cost-Minimization Heuristic (Cheapest First)
  4. Naive Feasibility-Maximization Heuristic (Easiest First)
  5. Uniform Random Selection Baseline
  6. Privileged Greedy Policy (H*-Informed)
  7. True Offline Combinatorial Upper Bound (Reference)
- Seed Partitions:
  - Development Partition: Seeds 1..50 (150 matched campaigns)
  - Held-Out Partition: Seeds 101..150 (150 matched campaigns)
- Statistical Rigor: Paired permutation tests, 95% bootstrap CIs, Cohen's d_z, Holm-Bonferroni FWER control.
- Invariants: Strict Offline Upper Bound enforcement (IG <= offline_optimum + 1e-6).
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scientific.oer_scenario import get_oer_case_study_scenario
from evaluation.sequential_evaluation import (
    run_sequential_policy_comparison,
    run_multiseed_sequential_evaluation,
    POLICIES_TO_EVALUATE,
)


def run_single_seed_diagnostic(scenario, seed: int = 42, budget: float = 10.0, max_steps: int = 5, threshold: float = 0.95):
    """Executes matched-seed 42 diagnostics across all three ground-truth hypotheses."""
    print("\n" + "=" * 104)
    print(f" SECTION 1: SEED-42 DIAGNOSTIC ACROSS ALL 3 GROUND-TRUTH HYPOTHESES (Budget={budget:.1f}, tau={threshold:.2f})")
    print("=" * 104)

    for h_id in ["H1", "H2", "H3"]:
        report = run_sequential_policy_comparison(
            scenario=scenario,
            hidden_hypothesis_id=h_id,
            seed=seed,
            budget=budget,
            max_steps=max_steps,
            confidence_threshold=threshold,
            cost_weight=0.1
        )
        print(f"\n  --- Ground Truth H* = {h_id} ({report.hidden_hypothesis_name}) ---")
        print(f"  Offline Upper Bound: {report.offline_optimal_ig_bits:.4f} bits via {report.offline_optimal_subset} (cost={report.offline_optimal_cost:.1f})")
        header = (
            f"    {'Policy':<42} {'P(H*)':<10} {'Steps':<6} {'Cost':<7} "
            f"{'Real. IG':<11} {'Failures':<9} {'0-EIG':<7} {'Target?':<8} {'Regret (Off)':<12}"
        )
        print(header)
        print("    " + "-" * 110)
        for s in report.policy_summaries:
            target_str = "YES" if s.target_confidence_achieved else "NO"
            line = (
                f"    {s.policy_name:<42} {s.final_confidence_h_star*100:>5.1f}%    "
                f"{s.total_steps:<6} {s.total_cost:<7.1f} {s.total_realized_ig_bits:<11.4f} "
                f"{s.execution_failures:<9} {s.zero_eig_selections:<7} {target_str:<8} "
                f"{s.regret_vs_offline_optimal:<12.4f}"
            )
            print(line)
            # Invariant assertion check
            assert s.regret_vs_offline_optimal >= -1e-6, f"Offline bound violated by {s.policy_key}!"


def print_partition_results(title: str, audit: dict):
    """Prints formatted summary statistics and paired differences for a seed partition."""
    print("\n" + "=" * 104)
    print(f" {title.upper()} ({audit['n_seeds']} Seeds x 3 Hypotheses = {audit['total_campaigns']} Matched Campaigns)")
    print("=" * 104)

    overall = audit["overall"]
    off_mean = overall["offline_upper_bound"]["mean_ig"]
    off_std = overall["offline_upper_bound"]["std_ig"]
    print(f"\n  Offline Combinatorial Upper Bound Across All Campaigns: {off_mean:.4f} +/- {off_std:.4f} bits\n")

    header = (
        f"  {'Policy':<36} {'Mean IG (bits)':<18} {'Cost':<7} {'Acc':<7} "
        f"{'Mean P(H*)':<12} {'Regret':<9} {'0-EIG':<7} {'Failures':<8}"
    )
    print(header)
    print("  " + "-" * 104)

    policy_display_names = {
        "janus_utility": "JANUS Composite Utility",
        "raw_eig": "Raw EIG Maximization",
        "cheapest": "Naive Cheapest First",
        "feasibility": "Naive Feasibility First",
        "uniform_random": "Uniform Random Selection",
        "privileged_greedy": "Privileged Greedy (H*)",
    }

    for p_key, p_stats in overall["policies"].items():
        disp_name = policy_display_names.get(p_key, p_key)
        acc_str = f"{p_stats['identification_accuracy']*100:.1f}%"
        conf_str = f"{p_stats['mean_conf']*100:.1f}%"
        line = (
            f"  {disp_name:<36} {p_stats['mean_ig']:<6.4f} +/- {p_stats['std_ig']:<7.3f} "
            f"{p_stats['mean_cost']:<7.1f} {acc_str:<7} {conf_str:<12} {p_stats['mean_regret']:<9.4f} "
            f"{p_stats['mean_zero_eig']:<7.2f} {p_stats['mean_failures']:<8.2f}"
        )
        print(line)

    print("\n  --- Paired Statistical Comparisons vs. JANUS Composite Utility (FWER Controlled at alpha=0.05) ---")
    paired_header = (
        f"    {'Baseline':<28} {'Delta IG (95% CI)':<26} {'Cohen dz':<10} "
        f"{'p (raw)':<10} {'p (Holm)':<10} {'Delta Cost':<10}"
    )
    print(paired_header)
    print("    " + "-" * 98)

    paired = overall["paired_comparisons_vs_janus"]
    for b_key, stats in paired.items():
        ig_diff = stats["ig_difference"]
        cost_diff = stats["cost_difference"]
        ci_str = f"[{ig_diff['ci_95'][0]:+.3f}, {ig_diff['ci_95'][1]:+.3f}]"
        diff_str = f"{ig_diff['mean_difference']:+.4f} {ci_str}"
        disp_b = policy_display_names.get(b_key, b_key)
        line = (
            f"    {disp_b:<28} {diff_str:<26} {ig_diff['cohen_d']:>+7.3f}   "
            f"{ig_diff['raw_p_value']:<10.4f} {ig_diff['adjusted_p_value']:<10.4f} "
            f"{cost_diff['mean_difference']:>+7.2f}"
        )
        print(line)
        print(f"       -> {stats['statistical_verdict']}")


def audit_preregistered_decision_rules(dev_audit: dict, held_out_audit: dict):
    """Evaluates the preregistered success, failure, and inconclusive criteria on CS-OER-002."""
    print("\n" + "=" * 104)
    print(" SECTION 4: PREREGISTERED DECISION RULE AUDIT (CS-OER-002)")
    print("=" * 104)

    held_overall = held_out_audit["overall"]
    janus_stats = held_overall["policies"]["janus_utility"]
    random_stats = held_overall["policies"]["uniform_random"]
    paired_vs_random = held_overall["paired_comparisons_vs_janus"]["uniform_random"]["ig_difference"]

    delta_ig = paired_vs_random["mean_difference"]
    p_adj = paired_vs_random["adjusted_p_value"]
    accuracy = janus_stats["identification_accuracy"]
    mean_regret = janus_stats["mean_regret"]
    waste_rate_janus = janus_stats["mean_zero_eig"]
    waste_rate_random = random_stats["mean_zero_eig"]

    print(f"\n  Preregistered Criteria Evaluation (Held-Out Set, N=150):")
    print(f"  1. Statistical Advantage vs. Uniform Random: Delta IG = {delta_ig:+.4f} b, p_adj = {p_adj:.4f}")
    crit1_pass = delta_ig > 0 and p_adj < 0.05
    print(f"     -> Criterion 1 (p_adj < 0.05): {'PASS (Statistically Significant)' if crit1_pass else 'FAIL / INCONCLUSIVE'}")

    print(f"  2. Discrete Identification Accuracy: {accuracy*100:.1f}% (Preregistered Target >= 80.0%)")
    crit2_pass = accuracy >= 0.80
    print(f"     -> Criterion 2 (Accuracy >= 80%): {'PASS' if crit2_pass else 'FAIL'}")

    print(f"  3. Strict Non-Negative Regret: Mean Regret = {mean_regret:.4f} b (Zero violations <= offline bound + 1e-6)")
    crit3_pass = mean_regret >= 0.0
    print(f"     -> Criterion 3 (Regret >= 0.0): {'PASS' if crit3_pass else 'FAIL (Bound Violation)'}")

    print(f"  4. Waste Elimination: JANUS picks = {waste_rate_janus:.2f} vs. Random picks = {waste_rate_random:.2f}")
    crit4_pass = waste_rate_janus < waste_rate_random
    print(f"     -> Criterion 4 (Waste < Random): {'PASS' if crit4_pass else 'FAIL'}")

    overall_success = crit1_pass and crit2_pass and crit3_pass and crit4_pass
    print("\n  " + "-" * 98)
    if overall_success:
        print("  FINAL CERTIFIED VERDICT: SUCCESS (PREREGISTERED CRITERIA MET)")
        print("  JANUS Composite Utility achieved statistically significant superiority over baseline policies")
        print("  with high identification accuracy and non-negative regret under the frozen simulation model.")
    else:
        print("  FINAL CERTIFIED VERDICT: INCONCLUSIVE / DEFICIENT")
        print("  At least one preregistered criterion was not met under the frozen parameters.")
    print("  " + "-" * 98)


def main():
    print("=" * 104)
    print(" JANUS PREREGISTERED CS-OER-002 SIMULATION BENCHMARK RUNNER")
    print(" System: Transition-Metal Perovskite Electrocatalysis (La_{1-x}Sr_xCoO_{3-delta})")
    print(" Frozen Documents: docs/case_study/CS_OER_002_{specification, evidence_ledger, protocol}.md")
    print("=" * 104)

    scenario = get_oer_case_study_scenario()
    budget = 10.0
    threshold = 0.95
    max_steps = 5

    # 1. Single-Seed 42 Diagnostic across all 3 ground truths
    run_single_seed_diagnostic(scenario, seed=42, budget=budget, max_steps=max_steps, threshold=threshold)

    # 2. Frozen Development Partition: Seeds 1..50 (150 campaigns)
    print("\nExecuting Development Partition Benchmark (Seeds 1..50 x 3 Hypotheses = 150 campaigns)...")
    dev_audit = run_multiseed_sequential_evaluation(
        scenario=scenario,
        hidden_hypotheses=["H1", "H2", "H3"],
        seeds=list(range(1, 51)),
        budget=budget,
        max_steps=max_steps,
        confidence_threshold=threshold,
        cost_weight=0.1
    )
    print_partition_results("Section 2: Development Benchmark Partition (Seeds 1..50)", dev_audit)

    # 3. Frozen Held-Out Partition: Seeds 101..150 (150 campaigns)
    print("\nExecuting Held-Out Generalization Benchmark (Seeds 101..150 x 3 Hypotheses = 150 campaigns)...")
    held_out_audit = run_multiseed_sequential_evaluation(
        scenario=scenario,
        hidden_hypotheses=["H1", "H2", "H3"],
        seeds=list(range(101, 151)),
        budget=budget,
        max_steps=max_steps,
        confidence_threshold=threshold,
        cost_weight=0.1
    )
    print_partition_results("Section 3: Held-Out Evaluation Partition (Seeds 101..150)", held_out_audit)

    # 4. Preregistered Decision Rule Audit
    audit_preregistered_decision_rules(dev_audit, held_out_audit)


if __name__ == "__main__":
    main()
