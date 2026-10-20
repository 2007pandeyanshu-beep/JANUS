"""Scientific Validation Module for JANUS

Validates probabilistic assumptions:
- Prior probability normalization
- Likelihood distributions summing to 1.0 per hypothesis
- Missing outcome predictions
- Feasibility constraints
"""

from typing import List, Dict, Tuple
import numpy as np
from app.schemas.scientific import Hypothesis, Experiment, PredictedOutcome


class ScientificValidationError(Exception):
    """Raised when scientific inputs violate probabilistic or mathematical axioms."""
    pass


def validate_and_normalize_priors(hypotheses: List[Hypothesis]) -> Tuple[Dict[str, float], List[str]]:
    """
    Validates hypothesis prior probabilities and normalizes them if necessary.
    
    Returns:
        Tuple of (normalized_priors_dict, audit_warnings)
    """
    if len(hypotheses) < 2:
        raise ScientificValidationError(
            f"At least two competing hypotheses are required for disambiguation. Received {len(hypotheses)}."
        )
    
    warnings: List[str] = []
    ids = [h.id for h in hypotheses]
    if len(ids) != len(set(ids)):
        raise ScientificValidationError("Duplicate hypothesis IDs found.")
    
    raw_priors = {h.id: float(h.prior) for h in hypotheses}
    total_prior = sum(raw_priors.values())
    
    if total_prior <= 0.0:
        raise ScientificValidationError(f"Sum of prior probabilities must be strictly positive. Got {total_prior}.")
    
    # Check if normalization is needed
    if abs(total_prior - 1.0) > 1e-4:
        warnings.append(
            f"Hypothesis priors summed to {total_prior:.4f} instead of 1.0; priors were automatically normalized."
        )
    
    normalized_priors = {h_id: p / total_prior for h_id, p in raw_priors.items()}
    return normalized_priors, warnings


def validate_experiment_predictions(
    experiment: Experiment,
    hypothesis_ids: List[str]
) -> Tuple[Dict[str, Dict[str, float]], List[str]]:
    """
    Validates that each hypothesis has an exhaustive, valid probability distribution
    over the experiment's possible outcomes.
    
    Returns:
        likelihood_matrix[hypothesis_id][outcome_label] = probability
        audit_warnings
    """
    warnings: List[str] = []
    outcomes = experiment.possible_outcomes
    if len(outcomes) < 2:
        raise ScientificValidationError(
            f"Experiment '{experiment.id}' must specify at least two possible outcomes. Got {outcomes}."
        )
    
    # Build likelihood matrix: hypothesis_id -> outcome_label -> probability
    matrix: Dict[str, Dict[str, float]] = {h_id: {} for h_id in hypothesis_ids}
    
    for pred in experiment.predictions:
        if pred.hypothesis_id not in matrix:
            warnings.append(
                f"Experiment '{experiment.id}' contains prediction for unknown hypothesis '{pred.hypothesis_id}' (ignored)."
            )
            continue
        if pred.outcome_label not in outcomes:
            raise ScientificValidationError(
                f"Experiment '{experiment.id}' prediction specifies outcome '{pred.outcome_label}' which is not in possible_outcomes {outcomes}."
            )
        matrix[pred.hypothesis_id][pred.outcome_label] = float(pred.probability)
    
    # Check completeness and normalization for each hypothesis
    for h_id in hypothesis_ids:
        h_preds = matrix[h_id]
        missing_outcomes = [o for o in outcomes if o not in h_preds]
        if missing_outcomes:
            raise ScientificValidationError(
                f"Experiment '{experiment.id}' is missing prediction under hypothesis '{h_id}' for outcomes: {missing_outcomes}."
            )
        
        total_p = sum(h_preds.values())
        if total_p <= 0.0:
            raise ScientificValidationError(
                f"Likelihoods for experiment '{experiment.id}' under hypothesis '{h_id}' sum to {total_p} <= 0."
            )
        
        if abs(total_p - 1.0) > 1e-4:
            warnings.append(
                f"Likelihoods for '{experiment.id}' under '{h_id}' summed to {total_p:.4f}; automatically normalized to 1.0."
            )
            for o in outcomes:
                h_preds[o] = h_preds[o] / total_p
    
    return matrix, warnings
