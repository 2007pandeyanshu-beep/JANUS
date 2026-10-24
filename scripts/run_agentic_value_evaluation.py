"""JANUS Phase 9: Agentic Value Evaluation CLI Runner

Empirically benchmarks:
1. Non-Agentic JANUS Bayesian Engine
2. Uniform Random Selection Baseline (Stochastic Expected Regret)
3. Naive Cost-Minimization Heuristic (Cheapest First)
4. Deterministic 5-Agent Coordinated Workflow
5. Live Gemini 3 Flash Agent Workflow (Auditable Trace)

Evaluates 7 practical scientific quality metrics across:
- CS-CAT-001 (Pt/CeO2 WGS Catalysis)
- CS-OER-002 (Perovskite OER Electrocatalysis)
- SYN-001 (Kinase Mechanism Disambiguation)
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from evaluation.agentic_value_evaluation import AgenticValueEvaluator


def mask_key(k: str) -> str:
    if not k or len(k) < 8:
        return "***"
    return f"{k[:6]}...{k[-4:]}"


def main():
    parser = argparse.ArgumentParser(description="JANUS Agentic Value Evaluation Runner")
    parser.add_argument("--api-key", type=str, default=None, help="Optional LLM API key for live demonstration")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    print("=" * 104)
    print(" JANUS PHASE 9: EMPIRICAL AGENTIC VALUE DEMONSTRATION & BENCHMARK")
    print(f" Live LLM Provider: {'models/gemini-3-flash-preview (Key: ' + mask_key(api_key) + ')' if api_key else 'None (Explicitly Blocked)'}")
    print("=" * 104)

    print("\nExecuting evaluation harness across CS-CAT-001, CS-OER-002, and SYN-001...")
    report = AgenticValueEvaluator.evaluate_all(api_key=api_key)

    for case in report.evaluated_cases:
        print(f"\n" + "-" * 104)
        print(f" CASE STUDY: {case.case_name} (ID: {case.case_id})")
        print(f" Ground-Truth Optimal Experiment: {case.ground_truth_optimal_id} (EIG={case.ground_truth_optimal_eig:.4f} b, Utility={case.ground_truth_optimal_utility:.4f})")
        print("-" * 104)

        # Pipeline Comparison Table
        print(f"  {'Pipeline / Workflow':<28} {'Latency':<10} {'Top Rec.':<12} {'EIG (b)':<10} {'Utility':<10} {'Regret':<10} {'Status':<12}")
        print("  " + "-" * 100)
        for p in case.pipelines:
            rec = p.recommended_experiment or "N/A"
            lat = f"{p.execution_latency_ms:.1f} ms"
            print(f"  {p.workflow_name:<28} {lat:<10} {rec:<12} {p.eig_bits:<10.4f} {p.composite_utility:<10.4f} {p.eig_regret_bits:<10.4f} {p.execution_status:<12}")

        # Scientific Quality Metrics
        print(f"\n  [7 Scientific Quality Metrics for {case.case_id}]:")
        c_m = case.citation_metric
        h_m = case.hypothesis_metric
        t_m = case.tool_metric
        r_m = case.recommendation_metric
        f_m = case.filtering_metric
        b_m = case.bayesian_update_metric

        print(f"  1. Citation Lineage:        Curated: {c_m.curated_citations_count} items ({c_m.curated_verified_dois_count} verified DOIs), LLM Generated: {c_m.llm_generated_citations_count} (Fabricated: {c_m.llm_fabricated_citations_count})")
        print(f"  2. Hypothesis Distinction:  {h_m.hypothesis_count} mechanisms, Prior Entropy={h_m.prior_entropy_bits:.4f} b, Simplex Sum={h_m.simplex_sum:.6f} (Error={h_m.simplex_error:.2e})")
        print(f"  3. Tool Reliability:        {t_m.successful_executions}/{t_m.total_tools_invoked} tools succeeded ({t_m.execution_success_rate*100:.1f}%), Latency={t_m.total_latency_ms:.1f} ms")
        print(f"  4. Recommendation Quality:  Recommended '{r_m.recommended_experiment_id}', Matches Optimal={r_m.matches_optimal_pick}, EIG Regret={r_m.eig_regret_bits:.4f} b")
        print(f"  5. Bayesian Update Match:   Tested {b_m.tested_experiment_id} -> '{b_m.tested_outcome}', Max Posterior Error={b_m.max_absolute_posterior_error:.2e} (Exact Match: {b_m.is_exact_match})")
        print(f"  6. Waste / Control Filter:  Flagged Entities={len(f_m.flagged_entities)} ({', '.join(f_m.flagged_entities) if f_m.flagged_entities else 'None'}), Waste Avoidance={f_m.waste_avoidance_success}")
        
        # Latency Comparison
        direct_lat = next(p.execution_latency_ms for p in case.pipelines if p.workflow_name == "non_agentic_janus")
        agent_lat = next(p.execution_latency_ms for p in case.pipelines if p.workflow_name == "deterministic_multi_agent")
        overhead = agent_lat / max(0.001, direct_lat)
        print(f"  7. Computational Overhead:  Direct Python={direct_lat:.2f} ms vs. 5-Agent Loop={agent_lat:.2f} ms ({overhead:.1f}x overhead)")

        # Auditable Live Execution Trace (if live LLM executed)
        if case.live_execution_trace:
            tr = case.live_execution_trace
            print(f"\n  [Auditable Live Gemini Execution Trace]:")
            print(f"    • Model:                {tr.model_name}")
            print(f"    • Tools Executed:       {len(tr.executed_tools)} ({', '.join(t['tool_name'] for t in tr.executed_tools)})")
            print(f"    • Final Recommendation: {tr.final_recommended_experiment}")
            print(f"    • Decision Attribution:")
            for comp, attr in tr.decision_component_attribution.items():
                print(f"        - {comp:<28}: {attr}")
            print(f"    • Model Consensus Synthesis Excerpt:")
            first_line = tr.raw_model_response.strip().split('\n')[0]
            print(f"        \"{first_line[:100]}...\"")

    print("\n" + "=" * 104)
    print(" BALANCED SCIENTIFIC VERDICT & SYNTHESIS")
    print("=" * 104)
    print(report.value_synthesis)
    print("=" * 104)


if __name__ == "__main__":
    main()
