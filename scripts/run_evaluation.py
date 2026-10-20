"""Reproducible Benchmark Evaluation CLI Runner for JANUS

Runs the statistical benchmark comparing JANUS vs Random Selection and Heuristics
on the Pt/CeO2 WGS Catalysis Case Study (CS-CAT-001).
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from evaluation.benchmark_evaluation import run_reproducible_benchmark


def main():
    print("=" * 80)
    print(" JANUS BENCHMARK EVALUATION: JANUS VS. BASELINE SELECTION POLICIES")
    print(" Benchmark ID: BENCH-WGS-001 | Case Study: CS-CAT-001 (Pt/CeO2 WGS)")
    print("=" * 80)
    
    seed = 42
    samples = 10000
    report = run_reproducible_benchmark(seed=seed, monte_carlo_samples=samples)
    
    print(f"\n[1] BENCHMARK SETUP & PARAMETERS:")
    print(f"  • Candidate Pool Size (Quantified): {report.candidate_pool_size}")
    print(f"  • Monte Carlo Samples:             {report.monte_carlo_sample_size}")
    print(f"  • Random Seed:                     {report.seed}")
    print(f"  • Decision Protocol:               Single-Step Selection (k=1 intervention)")
    
    print(f"\n[2] CANDIDATE EXPERIMENTS IN BENCHMARK POOL:")
    print(f"  {'ID':<12} {'Rank':<6} {'EIG (bits)':<12} {'Feas.':<8} {'Cost':<6} {'Utility':<10} {'Name'}")
    print("  " + "-" * 76)
    for c in report.candidate_experiments:
        print(f"  {c['id']:<12} #{c['rank']:<5} {c['eig_bits']:<12.4f} {c['feasibility']*100:>5.0f}%  {c['cost']:<6.1f} {c['utility_score']:<10.4f} {c['name'][:30]}")
    
    print(f"\n[3] COMPARATIVE POLICY PERFORMANCE:")
    j = report.janus_policy
    r = report.random_policy
    c = report.cheapest_heuristic_policy
    f = report.feasibility_heuristic_policy
    
    print(f"  {'Policy':<36} {'EIG (bits)':<16} {'Cost':<8} {'Utility':<10} {'Waste Rate':<10}")
    print("  " + "-" * 80)
    print(f"  {'JANUS Utility Optimization (Top-1)':<36} {j.expected_information_gain:<16.4f} {j.cost:<8.1f} {j.composite_utility:<10.4f} {j.waste_rate*100:<9.1f}%")
    print(f"  {'Uniform Random Policy (Monte Carlo)':<36} {r.mean_eig:<6.4f} (±{r.std_eig:.3f})  {r.mean_cost:<8.1f} {r.mean_utility:<10.4f} {r.waste_rate*100:<9.1f}%")
    print(f"  {'Naive Cost-Minimizer (Cheapest)':<36} {c.expected_information_gain:<16.4f} {c.cost:<8.1f} {c.composite_utility:<10.4f} {c.waste_rate*100:<9.1f}%")
    print(f"  {'Naive Feasibility-Maximizer':<36} {f.expected_information_gain:<16.4f} {f.cost:<8.1f} {f.composite_utility:<10.4f} {f.waste_rate*100:<9.1f}%")
    
    print(f"\n[4] STATISTICAL COMPARISON & EFFECT SIZE:")
    s = report.comparison_summary
    print(f"  • EIG Improvement Ratio:           {s['eig_improvement_ratio']}x over random selection")
    print(f"  • Composite Utility Improvement:   {s['utility_improvement_ratio']}x over random selection")
    print(f"  • Cohen's d Effect Size:           {s['cohens_d_effect_size']} (Large effect)")
    print(f"  • Empirical p-value:               p = {s['empirical_p_value']:.4f} (Fraction of random trials >= JANUS)")
    print(f"  • 95% Confidence Interval (Random): [{r.ci_95_eig[0]:.4f}, {r.ci_95_eig[1]:.4f}] bits")
    print(f"  • Waste Rate Elimination:          {s['waste_rate_reduction']}")
    
    print(f"\n[5] SCIENTIFIC VERDICT:")
    print(f"  {report.scientific_verdict}")
    
    print(f"\n[6] ASSUMPTIONS & BOUNDARY CONDITIONS:")
    for a in report.assumptions:
        print(f"  • {a}")
        
    print(f"\n[7] LIMITATIONS:")
    for l in report.limitations:
        print(f"  • {l}")
    print("=" * 80)


if __name__ == "__main__":
    main()
