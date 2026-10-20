"""JANUS Information-Theoretic Experiment Scoring Engine

Calculates deterministic metrics for discriminative experiment selection:
- Prior Shannon Entropy H(H)
- Marginal Outcome Probabilities P(y)
- Posterior Probability Distribution P(H|y) via Bayes' Theorem
- Expected Posterior Entropy E_y[H(H|y)]
- Expected Information Gain (EIG) / Mutual Information I(H; Y)
- Normalized Information Gain and Cost-Feasibility Weighted Utility
"""

import math
from typing import Dict, List, Tuple
from app.schemas.scientific import Experiment, ExperimentScore


def compute_shannon_entropy(probabilities: List[float]) -> float:
    """
    Computes Shannon entropy in bits (base 2):
    H = - sum(p * log2(p)) for p > 0
    """
    entropy = 0.0
    for p in probabilities:
        if p > 1e-12:
            entropy -= p * math.log2(p)
    return float(entropy)


def evaluate_experiment_information_gain(
    experiment: Experiment,
    normalized_priors: Dict[str, float],
    likelihood_matrix: Dict[str, Dict[str, float]],
    cost_weight: float = 0.1
) -> ExperimentScore:
    """
    Deterministically computes the Expected Information Gain (EIG) and
    composite utility score for a candidate experiment.
    
    Args:
        experiment: The Experiment definition
        normalized_priors: Dict mapping hypothesis_id -> prior probability P(H_k)
        likelihood_matrix: Dict mapping hypothesis_id -> outcome_label -> P(y | H_k, e)
        cost_weight: Weight applied to cost penalization in composite utility
        
    Returns:
        ExperimentScore populated with information metrics and diagnostic breakdowns
    """
    hypothesis_ids = list(normalized_priors.keys())
    outcomes = experiment.possible_outcomes
    
    # 1. Prior Shannon Entropy H(H)
    prior_probs = [normalized_priors[h_id] for h_id in hypothesis_ids]
    prior_entropy = compute_shannon_entropy(prior_probs)
    
    # Check feasibility constraint
    if not experiment.is_feasible or experiment.feasibility <= 0.0:
        return ExperimentScore(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            rank=999,
            prior_entropy=round(prior_entropy, 6),
            expected_posterior_entropy=round(prior_entropy, 6),
            expected_information_gain=0.0,
            normalized_information_gain=0.0,
            feasibility=float(experiment.feasibility),
            cost=float(experiment.cost),
            composite_utility_score=0.0,
            outcome_marginal_probabilities={o: 0.0 for o in outcomes},
            posterior_matrix={o: {h: normalized_priors[h] for h in hypothesis_ids} for o in outcomes},
            explanation=f"Experiment '{experiment.name}' is marked as infeasible (feasibility={experiment.feasibility}, is_feasible={experiment.is_feasible}). Excluded from utility ranking.",
            is_informative=False
        )
    
    # 2. Compute marginal outcome probabilities P(y | e)
    # P(y | e) = sum_k P(H_k) * P(y | H_k, e)
    marginal_outcomes: Dict[str, float] = {}
    for y in outcomes:
        p_y = sum(normalized_priors[h_id] * likelihood_matrix[h_id].get(y, 0.0) for h_id in hypothesis_ids)
        marginal_outcomes[y] = float(p_y)
    
    # Normalize marginals in case of small numerical drift
    total_marginal = sum(marginal_outcomes.values())
    if total_marginal > 1e-12:
        marginal_outcomes = {y: p / total_marginal for y, p in marginal_outcomes.items()}
    
    # 3. Compute posterior probabilities P(H_k | y, e) and posterior entropies H(H | y, e)
    # P(H_k | y) = (P(H_k) * P(y | H_k)) / P(y)
    posterior_matrix: Dict[str, Dict[str, float]] = {}
    posterior_entropies: Dict[str, float] = {}
    
    for y in outcomes:
        p_y = marginal_outcomes[y]
        posterior_matrix[y] = {}
        if p_y > 1e-12:
            y_posteriors = []
            for h_id in hypothesis_ids:
                p_h_given_y = (normalized_priors[h_id] * likelihood_matrix[h_id].get(y, 0.0)) / p_y
                posterior_matrix[y][h_id] = float(p_h_given_y)
                y_posteriors.append(p_h_given_y)
            posterior_entropies[y] = compute_shannon_entropy(y_posteriors)
        else:
            # Outcome has 0 probability under current model
            for h_id in hypothesis_ids:
                posterior_matrix[y][h_id] = float(normalized_priors[h_id])
            posterior_entropies[y] = prior_entropy
    
    # 4. Expected Posterior Entropy E_y[H(H | y)]
    # E_y[H(H|y)] = sum_y P(y) * H(H | y)
    expected_posterior_entropy = sum(
        marginal_outcomes[y] * posterior_entropies[y] for y in outcomes
    )
    
    # 5. Expected Information Gain (EIG) = H(H) - E_y[H(H | y)]
    eig = prior_entropy - expected_posterior_entropy
    if abs(eig) < 1e-9:
        eig = 0.0
    elif eig < 0.0:
        eig = 0.0  # Guard against numerical precision epsilon
    
    # 6. Normalized Information Gain
    norm_eig = (eig / prior_entropy) if prior_entropy > 1e-9 else 0.0
    norm_eig = min(max(norm_eig, 0.0), 1.0)
    
    # 7. Composite Utility Score
    # Utility = Feasibility * (EIG / (1.0 + alpha * Cost))
    cost_factor = 1.0 + (cost_weight * experiment.cost)
    composite_utility = (experiment.feasibility * eig) / cost_factor
    
    # 8. Deterministic Explanation Synthesis
    is_informative = eig > 1e-4
    if not is_informative:
        explanation = (
            f"Experiment '{experiment.name}' provides 0.0 bits of information gain. "
            f"All competing hypotheses predict indistinguishable outcome likelihoods, "
            f"yielding zero diagnostic disambiguation power."
        )
    elif norm_eig > 0.85:
        # High disambiguation
        max_outcome = max(marginal_outcomes, key=marginal_outcomes.get)
        explanation = (
            f"Highly decisive experiment with {eig:.3f} bits EIG ({norm_eig*100:.1f}% entropy reduction). "
            f"Distinct hypotheses produce starkly divergent likelihoods across outcomes. "
            f"Feasibility: {experiment.feasibility*100:.0f}%, Cost: {experiment.cost:.1f}."
        )
    else:
        explanation = (
            f"Moderately informative experiment yielding {eig:.3f} bits EIG ({norm_eig*100:.1f}% entropy reduction). "
            f"Partially distinguishes hypotheses. Feasibility: {experiment.feasibility*100:.0f}%, Cost: {experiment.cost:.1f}."
        )
        
    return ExperimentScore(
        experiment_id=experiment.id,
        experiment_name=experiment.name,
        rank=1,  # Assigned after sorting
        prior_entropy=round(prior_entropy, 6),
        expected_posterior_entropy=round(expected_posterior_entropy, 6),
        expected_information_gain=round(eig, 6),
        normalized_information_gain=round(norm_eig, 6),
        feasibility=float(experiment.feasibility),
        cost=float(experiment.cost),
        composite_utility_score=round(composite_utility, 6),
        outcome_marginal_probabilities={k: round(v, 4) for k, v in marginal_outcomes.items()},
        posterior_matrix={
            y: {h: round(p, 4) for h, p in h_dict.items()}
            for y, h_dict in posterior_matrix.items()
        },
        explanation=explanation,
        is_informative=is_informative
    )


def rank_experiments(
    experiments: List[Experiment],
    normalized_priors: Dict[str, float],
    likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]],
    cost_weight: float = 0.1
) -> List[ExperimentScore]:
    """
    Scores and deterministically ranks all candidate experiments.
    Sorting precedence:
    1. composite_utility_score (descending)
    2. expected_information_gain (descending)
    3. feasibility (descending)
    4. cost (ascending)
    5. experiment_id (lexicographic tie-break for strict determinism)
    """
    scores: List[ExperimentScore] = []
    
    for exp in experiments:
        score = evaluate_experiment_information_gain(
            experiment=exp,
            normalized_priors=normalized_priors,
            likelihood_matrix=likelihood_matrices[exp.id],
            cost_weight=cost_weight
        )
        scores.append(score)
    
    # Deterministic multi-key sort
    scores.sort(
        key=lambda s: (
            -s.composite_utility_score,
            -s.expected_information_gain,
            -s.feasibility,
            s.cost,
            s.experiment_id
        )
    )
    
    # Assign sequential ranks
    for idx, s in enumerate(scores, start=1):
        s.rank = idx
        
    return scores
