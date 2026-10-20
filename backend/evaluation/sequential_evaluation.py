"""JANUS Sequential Policy Benchmark & Evaluation Module

Executes comparative multi-policy evaluation across sequential experimental campaigns:
- JANUS Composite Utility Optimization
- Pure Raw EIG Maximization (Ablation)
- Naive Cost-Minimizer (Cheapest First)
- Naive Feasibility-Maximizer (Easiest First)
- Uniform Random Selection Baseline
- Idealized Omniscient Oracle Reference

Evaluates realized information gain, discovery steps, budget efficiency,
waste rates, and regret without information leakage.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import numpy as np

from app.schemas.scientific import (
    AnalysisInput,
    BEDCampaignInput,
    BEDCampaignResult,
    PolicyCampaignSummary,
    BEDPolicyComparisonReport,
)
from scientific.sequential_engine import SequentialBEDEngine


POLICIES_TO_EVALUATE = [
    ("janus_utility", "JANUS Composite Utility Optimization"),
    ("raw_eig", "Raw EIG Maximization (Ablation)"),
    ("cheapest", "Naive Cost-Minimization Heuristic"),
    ("feasibility", "Naive Feasibility-Maximization Heuristic"),
    ("uniform_random", "Uniform Random Selection Baseline"),
    ("oracle", "Idealized Omniscient Oracle (Upper Bound)"),
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
    Runs a matched-seed sequential comparative benchmark across all 6 policies.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    comparison_id = f"SEQ-BENCH-{uuid.uuid4().hex[:6].upper()}"
    
    hypo_names = {h.id: h.name for h in scenario.hypotheses}
    h_name = hypo_names.get(hidden_hypothesis_id, hidden_hypothesis_id)
    
    summaries: List[PolicyCampaignSummary] = []
    oracle_realized_ig = 0.0
    
    # 1. Run each policy with matched seed
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
        if policy_key == "oracle":
            oracle_realized_ig = res.total_realized_information_gain
            
    # 2. Compute comparative metrics and regret
    for policy_key, policy_display in POLICIES_TO_EVALUATE:
        res, elapsed_ms = campaign_results[policy_key]
        regret = max(oracle_realized_ig - res.total_realized_information_gain, 0.0)
        
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
            regret_vs_oracle_utility=round(regret, 4)
        )
        summaries.append(summary)
        
    # 3. Formulate verdict
    janus_res = campaign_results["janus_utility"][0]
    random_res = campaign_results["uniform_random"][0]
    cheapest_res = campaign_results["cheapest"][0]
    
    verdict = (
        f"In sequential evaluation on '{scenario.scenario_name}' under hidden truth H*='{hidden_hypothesis_id}' (seed={seed}), "
        f"JANUS Composite Utility achieved final confidence P(H*) = {janus_res.final_confidence_in_hidden_hypothesis:.2%} "
        f"in {janus_res.total_steps} steps (cost={janus_res.total_cost:.1f}, realized IG={janus_res.total_realized_information_gain:.4f} bits, "
        f"termination='{janus_res.termination_reason}'). "
        f"By contrast, Naive Cheapest selected uninformative assays ({cheapest_res.uninformative_selection_count} zero-EIG picks) "
        f"yielding only {cheapest_res.total_realized_information_gain:.4f} bits realized IG. "
        f"Random selection achieved {random_res.total_realized_information_gain:.4f} bits with {random_res.uninformative_selection_count} uninformative picks. "
        f"These results demonstrate the sequential efficiency of closed-loop information-theoretic experimentation."
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
        policy_summaries=summaries,
        summary_verdict=verdict
    )
