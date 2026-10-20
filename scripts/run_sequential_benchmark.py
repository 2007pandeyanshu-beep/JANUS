"""JANUS Sequential BED Benchmark Evaluation CLI Runner

Executes matched-seed comparative campaigns comparing:
1. JANUS Composite Utility Optimization
2. Raw EIG Maximization (Ablation)
3. Naive Cost-Minimizer (Cheapest First)
4. Naive Feasibility-Maximizer (Easiest First)
5. Uniform Random Selection Baseline
6. Idealized Omniscient Oracle Reference

Evaluated on Case Study CS-CAT-001 under Nature's simulated physical ground-truth.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scientific.evidence_ingestion import get_wgs_case_study_scenario
from evaluation.sequential_evaluation import run_sequential_policy_comparison


def main():
    print("=" * 96)
    print(" JANUS SEQUENTIAL BAYESIAN EXPERIMENTAL DESIGN (BED) BENCHMARK")
    print(" Case Study: CS-CAT-001 (Pt/CeO2 WGS Catalysis) | Simulated Ground Truth H* = H1 (Redox)")
    print("=" * 96)
    
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
    
    print(f"\n[1] CAMPAIGN CONFIGURATION:")
    print(f"  • Hidden Nature Truth: {report.hidden_hypothesis_id} ({report.hidden_hypothesis_name})")
    print(f"  • Random Seed:         {report.seed}")
    print(f"  • Budget Limit:        {report.budget:.1f}")
    print(f"  • Target Confidence:   {report.confidence_threshold*100:.0f}%")
    print(f"  • Max Steps:           {max_steps}")
    
    print(f"\n[2] COMPARATIVE POLICY RESULTS:")
    header = (
        f"  {'Policy':<42} {'P(H*)':<10} {'Steps':<6} {'Cost':<7} "
        f"{'Real. IG':<11} {'Failures':<9} {'0-EIG':<7} {'Target?':<8} {'Regret':<8}"
    )
    print(header)
    print("  " + "-" * 106)
    
    for s in report.policy_summaries:
        target_str = "YES" if s.target_confidence_achieved else "NO"
        line = (
            f"  {s.policy_name:<42} {s.final_confidence_h_star*100:>5.1f}%    "
            f"{s.total_steps:<6} {s.total_cost:<7.1f} {s.total_realized_ig_bits:<11.4f} "
            f"{s.execution_failures:<9} {s.zero_eig_selections:<7} {target_str:<8} "
            f"{s.regret_vs_oracle_utility:<8.4f}"
        )
        print(line)
        
    print("  " + "-" * 106)
    
    print(f"\n[3] SCIENTIFIC SUMMARY & OBSERVATIONS:")
    print(f"  {report.summary_verdict}")
    print("\n" + "=" * 96)


if __name__ == "__main__":
    main()
