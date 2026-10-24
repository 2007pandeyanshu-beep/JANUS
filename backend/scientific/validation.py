"""Scientific Validation Module for JANUS

Validates probabilistic assumptions:
- Prior probability normalization
- Likelihood distributions summing to 1.0 per hypothesis
- Missing outcome predictions
- Feasibility constraints
"""

from typing import List, Dict, Tuple, Optional, Any
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


# ==============================================================================
# Independent Mathematical Verifier (Phase 2 Audit)
# ==============================================================================

import math
from app.schemas.scientific import AnalysisInput, AnalysisResult, ExperimentScore


class IndependentEngineVerifier:
    """
    Independently recalculates and audits deterministic scientific engine outputs.
    
    Verifies:
    1. Prior simplex normalization and non-negativity (sum = 1.0 +/- tolerance).
    2. Likelihood distribution row-stochasticity and non-negativity per hypothesis.
    3. Fresh recalculation of marginal outcome probabilities and posterior matrices.
    4. Information-theoretic bounds: Shannon entropy, expected posterior entropy,
       and Expected Information Gain (0.0 <= EIG <= H(Theta)).
    5. Finiteness and consistency of cost, feasibility, and composite utility U(e).
    6. Authoritative ranking sort order, tie-breaking rules, and dual-ranking fidelity.
    7. Unquantified proposal boundary conditions (withheld from ranking).
    8. Bayesian observation conditioning correctness.
    """

    @classmethod
    def verify_prior_simplex(
        cls,
        priors: Dict[str, float],
        tolerance: float = 1e-4
    ) -> Dict[str, Any]:
        """Independently verifies hypothesis priors."""
        total = sum(priors.values())
        has_negative = any(v < 0.0 for v in priors.values())
        is_normalized = abs(total - 1.0) < tolerance
        count = len(priors)
        
        # Fresh entropy calculation
        entropy = 0.0
        for p in priors.values():
            if p > 1e-12:
                entropy -= p * math.log2(p)
                
        is_valid = (not has_negative) and is_normalized and (count >= 2)
        status = "PASS" if is_valid else "FAIL"
        
        reasons = []
        if has_negative:
            reasons.append("Priors contain negative values.")
        if not is_normalized:
            reasons.append(f"Priors sum to {total:.6f} != 1.0.")
        if count < 2:
            reasons.append(f"Fewer than 2 hypotheses ({count}).")
            
        return {
            "check": "prior_simplex",
            "status": status,
            "is_valid": is_valid,
            "sum": round(total, 6),
            "recalculated_entropy_bits": round(entropy, 6),
            "message": "Priors satisfy probability simplex" if is_valid else "; ".join(reasons),
        }

    @classmethod
    def verify_likelihood_distribution(
        cls,
        experiment: Experiment,
        hypothesis_ids: List[str],
        tolerance: float = 1e-4
    ) -> Dict[str, Any]:
        """Independently checks likelihood distribution for a candidate assay."""
        outcomes = experiment.possible_outcomes
        if len(outcomes) < 2:
            return {
                "check": f"likelihood_{experiment.id}",
                "status": "FAIL",
                "message": f"Experiment '{experiment.id}' has < 2 possible outcomes ({len(outcomes)}).",
            }

        matrix: Dict[str, Dict[str, float]] = {h: {} for h in hypothesis_ids}
        for p in experiment.predictions:
            if p.hypothesis_id in matrix:
                matrix[p.hypothesis_id][p.outcome_label] = float(p.probability)

        failures = []
        for h in hypothesis_ids:
            h_preds = matrix[h]
            missing = [o for o in outcomes if o not in h_preds]
            if missing:
                failures.append(f"H '{h}' missing outcomes {missing}")
                continue
            vals = [h_preds[o] for o in outcomes]
            if any(v < 0.0 or not math.isfinite(v) for v in vals):
                failures.append(f"H '{h}' has non-finite or negative likelihoods")
            row_sum = sum(vals)
            if abs(row_sum - 1.0) >= tolerance:
                failures.append(f"H '{h}' likelihood row sum equals {row_sum:.6f} != 1.0")

        is_valid = len(failures) == 0
        return {
            "check": f"likelihood_{experiment.id}",
            "status": "PASS" if is_valid else "FAIL",
            "is_valid": is_valid,
            "message": f"Experiment '{experiment.id}' likelihoods row-stochastic across all hypotheses" if is_valid else "; ".join(failures),
        }

    @classmethod
    def verify_experiment_scoring(
        cls,
        experiment: Experiment,
        score: ExperimentScore,
        priors: Dict[str, float],
        cost_weight: float = 0.1,
        tolerance: float = 1e-3
    ) -> Dict[str, Any]:
        """
        Independently recalculates marginals, posteriors, EIG, and utility from raw inputs.
        Compares recalculations against the primary engine's output score.
        """
        hypothesis_ids = list(priors.keys())
        outcomes = experiment.possible_outcomes

        # 1. Recalculate prior entropy
        h_prior = 0.0
        for p in priors.values():
            if p > 1e-12:
                h_prior -= p * math.log2(p)

        # Build likelihood matrix
        matrix: Dict[str, Dict[str, float]] = {h: {} for h in hypothesis_ids}
        for p in experiment.predictions:
            if p.hypothesis_id in matrix:
                matrix[p.hypothesis_id][p.outcome_label] = float(p.probability)

        # 2. Recalculate marginal outcome probabilities P(y)
        calc_marginals: Dict[str, float] = {}
        for y in outcomes:
            p_y = sum(priors[h] * matrix[h].get(y, 0.0) for h in hypothesis_ids)
            calc_marginals[y] = p_y

        total_m = sum(calc_marginals.values())
        if total_m > 1e-12:
            calc_marginals = {y: p / total_m for y, p in calc_marginals.items()}

        # 3. Recalculate posterior matrix and conditional entropies
        calc_posterior_entropies: Dict[str, float] = {}
        for y in outcomes:
            p_y = calc_marginals[y]
            if p_y > 1e-12:
                y_post = []
                for h in hypothesis_ids:
                    p_h_y = (priors[h] * matrix[h].get(y, 0.0)) / p_y
                    y_post.append(p_h_y)
                # Compute outcome entropy
                e_y = 0.0
                for p in y_post:
                    if p > 1e-12:
                        e_y -= p * math.log2(p)
                calc_posterior_entropies[y] = e_y
            else:
                calc_posterior_entropies[y] = h_prior

        # 4. Expected posterior entropy and EIG
        calc_exp_posterior_entropy = sum(
            calc_marginals[y] * calc_posterior_entropies[y] for y in outcomes
        )
        calc_eig = max(0.0, h_prior - calc_exp_posterior_entropy)

        # Bounds check: 0 <= EIG <= H(prior) for both recalculated EIG and reported score EIG
        eig_bounds_valid = (
            (-1e-9 <= calc_eig <= h_prior + 1e-5)
            and (-1e-9 <= score.expected_information_gain <= h_prior + 1e-5)
        )

        # 5. Feasibility and Cost Utility
        feas = float(experiment.feasibility)
        cost = float(experiment.cost)
        if feas < 0.0 or feas > 1.0 or not math.isfinite(feas):
            return {
                "check": f"scoring_{experiment.id}",
                "status": "FAIL",
                "message": f"Invalid feasibility {feas} for '{experiment.id}'.",
            }
        if cost <= 0.0 or not math.isfinite(cost):
            return {
                "check": f"scoring_{experiment.id}",
                "status": "FAIL",
                "message": f"Invalid cost {cost} for '{experiment.id}'.",
            }

        cost_factor = 1.0 + (cost_weight * cost)
        calc_utility = (feas * calc_eig) / cost_factor

        # 6. Compare with primary engine output
        discrepancies = []
        if not eig_bounds_valid:
            discrepancies.append(f"EIG {calc_eig:.4f} violates bounds [0, {h_prior:.4f}]")
        if abs(calc_eig - score.expected_information_gain) > tolerance:
            discrepancies.append(
                f"EIG mismatch: recalculated {calc_eig:.4f} vs score {score.expected_information_gain:.4f}"
            )
        if abs(calc_utility - score.composite_utility_score) > tolerance:
            discrepancies.append(
                f"Utility mismatch: recalculated {calc_utility:.4f} vs score {score.composite_utility_score:.4f}"
            )

        is_valid = len(discrepancies) == 0
        return {
            "check": f"scoring_{experiment.id}",
            "status": "PASS" if is_valid else "FAIL",
            "is_valid": is_valid,
            "eig_within_bounds": eig_bounds_valid,
            "recalculated_eig_bits": round(calc_eig, 6),
            "recalculated_utility": round(calc_utility, 6),
            "recalculated_prior_entropy_bits": round(h_prior, 6),
            "recalculated_expected_posterior_entropy_bits": round(calc_exp_posterior_entropy, 6),
            "message": f"Scoring independently verified for {experiment.id}" if is_valid else "; ".join(discrepancies),
        }

    @classmethod
    def verify_ranking_order(
        cls,
        ranked_experiments: List[ExperimentScore]
    ) -> Dict[str, Any]:
        """
        Verifies sorting order against the authoritative JANUS ranking policy:
        Primary: Composite Utility Rank:
          (-s.composite_utility_score, -s.expected_information_gain, -s.feasibility, s.cost, s.experiment_id)
        Secondary: Pure EIG Rank:
          (-s.expected_information_gain, -s.feasibility, s.cost, s.experiment_id)
        """
        if not ranked_experiments:
            return {"check": "ranking_order", "status": "PASS", "message": "No experiments to rank"}

        failures = []

        # 1. Verify primary utility sorting and rank indices
        for i in range(len(ranked_experiments)):
            s = ranked_experiments[i]
            expected_rank = i + 1
            if s.utility_rank != expected_rank or s.rank != expected_rank:
                failures.append(
                    f"Experiment {s.experiment_id} at position {expected_rank} has rank={s.rank}, utility_rank={s.utility_rank}"
                )
            if i > 0:
                prev = ranked_experiments[i - 1]
                # prev should be >= curr by primary key tuple
                key_prev = (
                    -prev.composite_utility_score,
                    -prev.expected_information_gain,
                    -prev.feasibility,
                    prev.cost,
                    prev.experiment_id,
                )
                key_curr = (
                    -s.composite_utility_score,
                    -s.expected_information_gain,
                    -s.feasibility,
                    s.cost,
                    s.experiment_id,
                )
                if key_prev > key_curr:
                    failures.append(
                        f"Ranking monotonic inversion between {prev.experiment_id} ({prev.composite_utility_score}) and {s.experiment_id} ({s.composite_utility_score})"
                    )

        # 2. Verify secondary pure EIG rank values
        eig_sorted = sorted(
            ranked_experiments,
            key=lambda s: (
                -s.expected_information_gain,
                -s.feasibility,
                s.cost,
                s.experiment_id,
            ),
        )
        expected_eig_ranks = {s.experiment_id: idx for idx, s in enumerate(eig_sorted, start=1)}
        for s in ranked_experiments:
            exp_rank = expected_eig_ranks.get(s.experiment_id)
            if s.eig_rank != exp_rank:
                failures.append(
                    f"Experiment {s.experiment_id} has eig_rank={s.eig_rank}, expected {exp_rank}"
                )

        is_valid = len(failures) == 0
        return {
            "check": "ranking_order",
            "status": "PASS" if is_valid else "FAIL",
            "is_valid": is_valid,
            "message": "Ranking sort order and dual-rank tie breaking verified" if is_valid else "; ".join(failures),
        }

    @classmethod
    def verify_bayesian_observation_update(
        cls,
        initial_priors: Dict[str, float],
        likelihood_vector: Dict[str, float],
        observed_posteriors: Dict[str, float],
        experiment_id: Optional[str] = None,
        observed_outcome: Optional[str] = None,
        tolerance: float = 1e-4
    ) -> Dict[str, Any]:
        """
        Independently computes Bayes' theorem for an observed outcome:
        P(H_k | y) = P(H_k) * P(y | H_k) / sum_j [ P(H_j) * P(y | H_j) ]
        """
        hypothesis_ids = list(initial_priors.keys())
        numerators = {h: initial_priors[h] * likelihood_vector.get(h, 0.0) for h in hypothesis_ids}
        marginal = sum(numerators.values())

        if marginal <= 1e-12:
            return {
                "check": "bayesian_observation_update",
                "status": "FAIL",
                "is_valid": False,
                "verification_status": "UPDATE_VIOLATION",
                "message": f"Observation has 0 marginal probability (marginal={marginal}). Inconsistent likelihood model.",
                "max_divergence": 1.0,
                "failures": ["Observation has 0 marginal probability"],
            }

        calc_posteriors = {h: numerators[h] / marginal for h in hypothesis_ids}
        
        failures = []
        for h in hypothesis_ids:
            calc_val = calc_posteriors[h]
            obs_val = observed_posteriors.get(h)
            if obs_val is None:
                failures.append(f"Hypothesis {h} missing in observed posteriors")
            elif abs(calc_val - obs_val) > tolerance:
                failures.append(
                    f"Posterior mismatch for {h}: calculated {calc_val:.4f} vs observed {obs_val:.4f}"
                )

        # Check posterior simplex
        post_sum = sum(observed_posteriors.values())
        if abs(post_sum - 1.0) > tolerance:
            failures.append(f"Observed posteriors sum to {post_sum:.6f} != 1.0")

        is_valid = len(failures) == 0
        max_div = max((abs(calc_posteriors[h] - observed_posteriors.get(h, 0.0)) for h in hypothesis_ids), default=0.0)
        return {
            "check": "bayesian_observation_update",
            "status": "PASS" if is_valid else "FAIL",
            "is_valid": is_valid,
            "verification_status": "VERIFIED" if is_valid else "UPDATE_VIOLATION",
            "experiment_id": experiment_id,
            "observed_outcome": observed_outcome,
            "marginal_probability": round(marginal, 6),
            "max_divergence": round(max_div, 6),
            "recalculated_posteriors": {h: round(v, 6) for h, v in calc_posteriors.items()},
            "failures": failures,
            "message": "Bayesian observation update independently verified" if is_valid else "; ".join(failures),
        }

    @classmethod
    def verify_analysis_result(
        cls,
        analysis_result: AnalysisResult,
        scenario_input: AnalysisInput
    ) -> Dict[str, Any]:
        """
        Executes a comprehensive, independent mathematical audit over an entire AnalysisResult.
        """
        checks: List[Dict[str, Any]] = []

        # 1. Prior simplex check
        priors = analysis_result.normalized_priors
        checks.append(cls.verify_prior_simplex(priors))

        # Build map of candidate experiments
        exp_map = {e.id: e for e in scenario_input.experiments}

        # 2. Check likelihood distributions for each quantified experiment
        for s in analysis_result.ranked_experiments:
            exp = exp_map.get(s.experiment_id)
            if exp:
                checks.append(cls.verify_likelihood_distribution(exp, list(priors.keys())))
                checks.append(
                    cls.verify_experiment_scoring(
                        experiment=exp,
                        score=s,
                        priors=priors,
                        cost_weight=scenario_input.cost_weight
                    )
                )

        # 3. Ranking order verification
        checks.append(cls.verify_ranking_order(analysis_result.ranked_experiments))

        # 4. Unquantified proposals verification
        unquant_failures = []
        for s in analysis_result.unquantified_experiments:
            if s.expected_information_gain != 0.0 or s.composite_utility_score != 0.0:
                unquant_failures.append(f"Unquantified assay {s.experiment_id} has non-zero EIG/utility")
            if s.rank is not None:
                unquant_failures.append(f"Unquantified assay {s.experiment_id} has rank={s.rank} (must be None)")
            if not s.missing_inputs_explanation:
                unquant_failures.append(f"Unquantified assay {s.experiment_id} lacks missing inputs explanation")

        unquant_valid = len(unquant_failures) == 0
        checks.append({
            "check": "unquantified_proposals_boundary",
            "status": "PASS" if unquant_valid else "FAIL",
            "is_valid": unquant_valid,
            "message": "Unquantified proposal boundary respected (0 fabricated scores)" if unquant_valid else "; ".join(unquant_failures),
        })

        passed_count = sum(1 for c in checks if c["status"] == "PASS")
        total_count = len(checks)
        all_passed = (passed_count == total_count)

        summary = (
            f"Independent Mathematical Audit: {passed_count}/{total_count} checks passed. "
            f"Simplex, likelihood distributions, bounds, and utility ranking verified."
            if all_passed else
            f"Independent Mathematical Audit FAILED: {total_count - passed_count}/{total_count} checks failed."
        )

        return {
            "is_verified": all_passed,
            "verification_status": "VERIFIED" if all_passed else "INVARIANT_VIOLATION",
            "all_invariants_hold": all_passed,
            "total_checks": total_count,
            "passed_checks": passed_count,
            "failed_checks": total_count - passed_count,
            "check_items": checks,
            "summary": summary,
            "verification_type": "INDEPENDENT_MATHEMATICAL_VERIFICATION",
        }

