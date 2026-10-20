"""Baseline Policies for Scientific Experiment Selection Evaluation

Provides meaningful benchmarks to assess JANUS ranking advantage:
- Random Selection Policy
- Naive Cost-Minimization Policy
- Feasibility-Only Policy
"""

from typing import List, Dict, Any
import numpy as np
from app.schemas.scientific import ExperimentScore, BaselineComparison


def evaluate_random_selection_baseline(
    ranked_scores: List[ExperimentScore]
) -> BaselineComparison:
    """
    Evaluates expected performance if experiments were chosen uniformly at random.
    """
    if not ranked_scores:
        return BaselineComparison(
            baseline_type="random_selection",
            baseline_expected_eig=0.0,
            best_experiment_eig=0.0,
            eig_improvement_ratio=1.0,
            summary="No candidate experiments available for baseline evaluation."
        )
    
    # Calculate average EIG across all candidate experiments
    all_eigs = [s.expected_information_gain for s in ranked_scores]
    mean_eig = float(np.mean(all_eigs))
    
    top_score = ranked_scores[0]
    best_eig = top_score.expected_information_gain
    
    # Improvement ratio over random selection
    if mean_eig > 1e-6:
        improvement = best_eig / mean_eig
    else:
        improvement = 1.0 if best_eig <= 1e-6 else float("inf")
        
    summary = (
        f"Top experiment '{top_score.experiment_name}' delivers {best_eig:.3f} bits EIG, "
        f"which is {improvement:.2f}x the expected value ({mean_eig:.3f} bits) of uniform random selection."
    )
    
    return BaselineComparison(
        baseline_type="random_selection",
        baseline_expected_eig=round(mean_eig, 4),
        best_experiment_eig=round(best_eig, 4),
        eig_improvement_ratio=round(improvement, 2),
        summary=summary
    )
