"""Evaluation Metrics for Experiment Ranking Systems

Contains scoring and metric calculation utilities:
- Information-theoretic bounds
- Ranking consistency
- Disambiguation efficiency
"""

from typing import List
from app.schemas.scientific import ExperimentScore


def compute_cumulative_information_gain(ranked_scores: List[ExperimentScore]) -> List[float]:
    """Computes running cumulative EIG down the ranked list."""
    cumulative = []
    total = 0.0
    for s in ranked_scores:
        total += s.expected_information_gain
        cumulative.append(round(total, 4))
    return cumulative
