"""Reproducible Benchmark Evaluation CLI Runner for JANUS

Statistical Audit & Benchmark Verification for CS-CAT-001 (Pt/CeO2 WGS Catalysis).
Strictly separates exact analytical population moments from Monte Carlo convergence checks.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from evaluation.benchmark_evaluation import run_reproducible_benchmark


def main():
    print("=" * 84)
    print(" JANUS STATISTICAL BENCHMARK EVALUATION (PHASE 3.2 AUDIT)")
    print(" Benchmark ID: BENCH-WGS-001 | Case Study: CS-CAT-001 (Pt/CeO2 WGS Catalysis)")
    print("=" * 84)
    
    seed = 42
    samples = 10000
    report = run_reproducible_benchmark(seed=seed, monte_carlo_samples=samples)
    
    print(f"\n[1] BENCHMARK METHODOLOGICAL SPECIFICATION:")
    for k, v in report.methodology_specification.items():
        print(f"  • {k.replace('_', ' ').title()}:")
        print(f"    {v}")
    
    print(f"\n[2] CANDIDATE EXPERIMENTS IN BENCHMARK POOL (N={report.candidate_pool_size}):")
    print(f"  {'ID':<12} {'Util. Rank':<12} {'EIG Rank':<10} {'EIG (bits)':<12} {'Feas.':<8} {'Cost':<6} {'Utility':<10} {'Name'}")
    print("  " + "-" * 90)
    for c in report.candidate_experiments:
        u_rank = f"#{c.get('utility_rank', c['rank'])}"
        e_rank = f"#{c.get('eig_rank', c['rank'])}"
        print(f"  {c['id']:<12} {u_rank:<12} {e_rank:<10} {c['eig_bits']:<12.4f} {c['feasibility']*100:>5.0f}%  {c['cost']:<6.1f} {c['utility_score']:<10.4f} {c['name'][:26]}")
    print("  " + "-" * 90)
    print("  * Ranking Divergence Note: EXP-WGS-03 has higher raw EIG (EIG Rank #3, 0.3775 bits) than EXP-WGS-04 (EIG Rank #4, 0.3233 bits),")
    print("    but EXP-WGS-04 ranks higher in Composite Utility (Util Rank #3, 0.2797 vs Util Rank #4, 0.1601) due to synchrotron beamline")
    print("    cost penalty (6.5 vs 1.1) and lower feasibility (70% vs 96%). Both metrics are reported separately.")
    
    print(f"\n[3] COMPARATIVE POLICY PERFORMANCE:")
    j = report.janus_policy
    e = report.exact_random_baseline
    mc = report.monte_carlo_verification
    c = report.cheapest_heuristic_policy
    f = report.feasibility_heuristic_policy
    
    print(f"  {'Policy':<40} {'EIG (bits)':<16} {'Cost':<8} {'Utility':<10} {'Waste Rate':<10}")
    print("  " + "-" * 84)
    print(f"  {'JANUS Utility Optimization (Top-1)':<40} {j.expected_information_gain:<16.4f} {j.cost:<8.1f} {j.composite_utility:<10.4f} {j.waste_rate*100:<9.1f}%")
    print(f"  {'EXACT Analytical Random Baseline (N=5)':<40} {e.exact_mean_eig:<6.4f} (std={e.exact_population_std_eig:.3f}) {e.exact_mean_cost:<8.1f} {e.exact_mean_utility:<10.4f} {e.exact_waste_rate*100:<9.1f}%")
    print(f"  {'Monte Carlo Verification (M=10,000, s=42)':<40} {mc.empirical_mean_eig:<6.4f} (+/-{mc.mc_standard_error_of_mean:.4f}) {e.exact_mean_cost:<8.1f} {mc.empirical_mean_utility:<10.4f} {mc.empirical_waste_rate*100:<9.1f}%")
    print(f"  {'Naive Cost-Minimizer (Cheapest First)':<40} {c.expected_information_gain:<16.4f} {c.cost:<8.1f} {c.composite_utility:<10.4f} {c.waste_rate*100:<9.1f}%")
    print(f"  {'Naive Feasibility-Maximizer (Easiest)':<40} {f.expected_information_gain:<16.4f} {f.cost:<8.1f} {f.composite_utility:<10.4f} {f.waste_rate*100:<9.1f}%")
    
    print(f"\n[4] EXACT MATHEMATICAL COMPARISON:")
    s = report.comparison_summary
    print(f"  • Exact EIG Multiplier:             {s['exact_eig_multiplier']:.4f}x ({j.expected_information_gain:.4f} vs {e.exact_mean_eig:.4f} bits)")
    print(f"  • Exact Absolute EIG Gain:          +{s['exact_absolute_eig_gain_bits']:.4f} bits (+{s['exact_absolute_eig_gain_bits']/e.exact_mean_eig*100:.1f}%)")
    print(f"  • Exact Composite Utility Multiplier:{s['exact_utility_multiplier']:.4f}x ({j.composite_utility:.4f} vs {e.exact_mean_utility:.4f})")
    print(f"  • Exact Absolute Utility Gain:      +{s['exact_absolute_utility_gain']:.4f} (+{s['exact_absolute_utility_gain']/e.exact_mean_utility*100:.1f}%)")
    print(f"  • Optimal Selection Probability:    {s['optimal_selection_probability_comparison']}")
    print(f"  • Waste Rate Elimination:           {s['exact_waste_rate_reduction']}")
    print(f"  • Heuristic Failure Warning:        {s['cheapest_heuristic_failure']}")
    
    print(f"\n[5] SCIENTIFIC VERDICT:")
    print(f"  {report.scientific_verdict}")
    
    print(f"\n[6] SCIENTIFIC LIMITATIONS & BOUNDARY CONDITIONS:")
    for l in report.limitations:
        print(f"  • {l}")
    print("=" * 84)


if __name__ == "__main__":
    main()
