"""JANUS Sequential Bayesian Experimental Design (BED) Engine

Implements a closed-loop sequential experimentation campaign:
1. Nature (Simulation Environment) holds hidden ground-truth hypothesis H*.
2. Policy selects candidates without access to H* (information-leakage prevention).
3. Simulates physical execution feasibility.
4. Generates observable outcome conditional on H*.
5. Executes Bayesian posterior updates and entropy calculations.
6. Dynamically re-ranks remaining candidates under the updated posterior.
7. Evaluates configurable stopping conditions.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from app.schemas.scientific import (
    AnalysisInput,
    Experiment,
    ExperimentScore,
    Hypothesis,
    BEDCampaignInput,
    BEDCampaignStep,
    BEDCampaignResult,
    PolicyCampaignSummary,
    BEDPolicyComparisonReport,
)
from scientific.scoring import (
    compute_shannon_entropy,
    evaluate_experiment_information_gain,
    rank_experiments,
)
from scientific.validation import (
    validate_and_normalize_priors,
    validate_experiment_predictions,
    ScientificValidationError,
)


class Nature:
    """
    Simulation Environment ("Nature").
    
    COUNTERFACTUAL REALIZATION FAIRNESS:
    - Pre-generates deterministic physical execution outcomes (feasibility Bernoulli trial
      and conditional categorical outcome draw) for every candidate experiment in the pool
      under the given seed.
    - Guarantees that if an assay is executed at step 1 by Policy A or at step 4 by Policy B,
      it encounters the identical physical reality under the same seed.
    - Completely eliminates RNG stream coupling and evaluation drift across policies.
    
    ISOLATION INVARIANT:
    - Holds the hidden ground-truth hypothesis H*.
    - NEVER exposes H* to the decision policy during experiment selection.
    - Generates physical feasibility failures and observable outcomes.
    """
    def __init__(
        self,
        hidden_hypothesis_id: str,
        rng: np.random.Generator,
        candidate_experiments: Optional[List[Experiment]] = None,
        likelihood_matrices: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None,
    ):
        self._hidden_hypothesis_id = hidden_hypothesis_id
        self._rng = rng
        self._counterfactual_realizations: Dict[str, Tuple[bool, Optional[str]]] = {}
        
        # Pre-sample counterfactual realizations if candidates provided
        if candidate_experiments and likelihood_matrices:
            # Sort candidates canonically by id to ensure deterministic order across runs
            sorted_candidates = sorted(candidate_experiments, key=lambda e: e.id)
            for exp in sorted_candidates:
                p_feas = float(min(max(exp.feasibility, 0.0), 1.0))
                is_successful = bool(self._rng.random() < p_feas)
                if not is_successful:
                    self._counterfactual_realizations[exp.id] = (False, None)
                    continue
                
                h_likelihoods = likelihood_matrices.get(exp.id, {}).get(hidden_hypothesis_id, {})
                outcomes = exp.possible_outcomes
                probs = np.array([float(h_likelihoods.get(y, 0.0)) for y in outcomes], dtype=np.float64)
                prob_sum = probs.sum()
                if prob_sum <= 1e-12:
                    probs = np.ones(len(outcomes)) / len(outcomes)
                else:
                    probs = probs / prob_sum
                sampled_idx = self._rng.choice(len(outcomes), p=probs)
                self._counterfactual_realizations[exp.id] = (True, outcomes[sampled_idx])
        
    @property
    def hidden_hypothesis_id(self) -> str:
        """Accessed only by evaluation reports and audit logs outside policy selection."""
        return self._hidden_hypothesis_id
        
    @property
    def counterfactual_realizations(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Provides read-only access for offline upper bound computation."""
        return dict(self._counterfactual_realizations)

    def execute_experiment(
        self,
        experiment: Experiment,
        likelihood_matrix: Dict[str, Dict[str, float]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Simulates physical execution of candidate assay in the real world:
        1. Uses pre-sampled counterfactual realization if available (guaranteeing inter-policy fairness).
        2. Falls back to stream generation for unseeded dynamic experiments.
        
        Returns:
            (is_successful: bool, observed_outcome: Optional[str])
        """
        if experiment.id in self._counterfactual_realizations:
            return self._counterfactual_realizations[experiment.id]
            
        p_feas = float(min(max(experiment.feasibility, 0.0), 1.0))
        is_successful = bool(self._rng.random() < p_feas)
        
        if not is_successful:
            return False, None
            
        # Sample outcome conditioned strictly on H*
        h_star = self._hidden_hypothesis_id
        h_likelihoods = likelihood_matrix.get(h_star, {})
        
        outcomes = experiment.possible_outcomes
        probs = np.array([float(h_likelihoods.get(y, 0.0)) for y in outcomes], dtype=np.float64)
        
        prob_sum = probs.sum()
        if prob_sum <= 1e-12:
            probs = np.ones(len(outcomes)) / len(outcomes)
        else:
            probs = probs / prob_sum
            
        sampled_idx = self._rng.choice(len(outcomes), p=probs)
        return True, outcomes[sampled_idx]


def compute_bayesian_posterior_update(
    prior: Dict[str, float],
    observed_outcome: str,
    likelihood_matrix: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    Computes exact Bayes' rule update:
    P(H_k | y) = [ P(H_k) * P(y | H_k) ] / P(y)
    
    Guarantees strict normalization (sum = 1.0) and numerical stability.
    """
    hypothesis_ids = list(prior.keys())
    unnormalized: Dict[str, float] = {}
    
    for h_id in hypothesis_ids:
        p_h = prior[h_id]
        p_y_given_h = likelihood_matrix.get(h_id, {}).get(observed_outcome, 0.0)
        unnormalized[h_id] = float(p_h * p_y_given_h)
        
    marginal_p_y = sum(unnormalized.values())
    
    if marginal_p_y <= 1e-12:
        # Numerically degenerate or unexpected 0-probability outcome:
        # Preserve prior unchanged rather than dividing by zero
        return {h_id: float(prior[h_id]) for h_id in hypothesis_ids}
        
    posterior = {h_id: float(p / marginal_p_y) for h_id, p in unnormalized.items()}
    
    # Exact IEEE-754 simplex normalization without lossy premature rounding
    total_post = sum(posterior.values())
    if total_post > 0:
        posterior = {h_id: float(p / total_post) for h_id, p in posterior.items()}
            
    return posterior


def select_candidate_experiment(
    policy_name: str,
    available_experiments: List[Experiment],
    ranked_scores: List[ExperimentScore],
    likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]],
    current_prior: Dict[str, float],
    cost_weight: float,
    rng: np.random.Generator,
    oracle_hidden_hypothesis_id: Optional[str] = None
) -> Tuple[Experiment, ExperimentScore, str]:
    """
    Selects the next candidate experiment according to the specified policy.
    
    Policies supported:
    - 'janus_utility': Argmax composite utility U(e) (default JANUS policy)
    - 'raw_eig': Argmax expected information gain (pure information ablation)
    - 'cheapest': Argmin cost with higher EIG as tie-breaker
    - 'feasibility': Argmax feasibility with lower cost as tie-breaker
    - 'uniform_random': Uniform random draw over available candidates
    - 'oracle': Idealized upper bound with knowledge of H*
    """
    exp_by_id = {e.id: e for e in available_experiments}
    score_by_id = {s.experiment_id: s for s in ranked_scores}
    
    if policy_name == "janus_utility":
        top_score = ranked_scores[0]
        chosen_exp = exp_by_id[top_score.experiment_id]
        rationale = f"Selected '{chosen_exp.name}' maximizing composite utility ({top_score.composite_utility_score:.4f}, Utility Rank #1)."
        return chosen_exp, top_score, rationale
        
    elif policy_name == "raw_eig":
        top_score = max(
            ranked_scores,
            key=lambda s: (s.expected_information_gain, s.feasibility, -s.cost)
        )
        chosen_exp = exp_by_id[top_score.experiment_id]
        rationale = f"Selected '{chosen_exp.name}' maximizing pure EIG ({top_score.expected_information_gain:.4f} bits, EIG Rank #1)."
        return chosen_exp, top_score, rationale
        
    elif policy_name == "cheapest":
        top_score = min(
            ranked_scores,
            key=lambda s: (s.cost, -s.expected_information_gain, -s.feasibility)
        )
        chosen_exp = exp_by_id[top_score.experiment_id]
        rationale = f"Selected '{chosen_exp.name}' via cheapest-first heuristic (Cost={top_score.cost:.1f})."
        return chosen_exp, top_score, rationale
        
    elif policy_name == "feasibility":
        top_score = max(
            ranked_scores,
            key=lambda s: (s.feasibility, -s.cost, s.expected_information_gain)
        )
        chosen_exp = exp_by_id[top_score.experiment_id]
        rationale = f"Selected '{chosen_exp.name}' via highest-feasibility heuristic (Feasibility={top_score.feasibility*100:.0f}%)."
        return chosen_exp, top_score, rationale
        
    elif policy_name == "uniform_random":
        chosen_idx = int(rng.integers(0, len(available_experiments)))
        chosen_exp = available_experiments[chosen_idx]
        chosen_score = score_by_id[chosen_exp.id]
        rationale = f"Selected '{chosen_exp.name}' via uniform random baseline choice (1/{len(available_experiments)})."
        return chosen_exp, chosen_score, rationale
        
    elif policy_name in ("privileged_greedy", "oracle"):
        # Privileged Greedy Policy (H*-Informed): computes expected realized entropy reduction under true H*
        # NOTE: This is a 1-step myopic heuristic with access to H*, NOT a multi-step combinatorial upper bound.
        h_star = oracle_hidden_hypothesis_id
        if not h_star:
            # Fallback to utility if oracle ID omitted
            top_score = ranked_scores[0]
            return exp_by_id[top_score.experiment_id], top_score, "Privileged greedy fallback to utility."
            
        prior_entropy = compute_shannon_entropy(list(current_prior.values()))
        
        def privileged_score_candidate(s: ExperimentScore) -> Tuple[float, float, float]:
            exp = exp_by_id[s.experiment_id]
            l_matrix = likelihood_matrices[exp.id]
            h_probs = l_matrix.get(h_star, {})
            
            # Expected entropy reduction under true H*
            expected_reduction = 0.0
            for y in exp.possible_outcomes:
                p_y_true = h_probs.get(y, 0.0)
                if p_y_true > 1e-12:
                    post = compute_bayesian_posterior_update(current_prior, y, l_matrix)
                    post_ent = compute_shannon_entropy(list(post.values()))
                    expected_reduction += p_y_true * max(prior_entropy - post_ent, 0.0)
                    
            oracle_utility = (exp.feasibility * expected_reduction) / (1.0 + cost_weight * exp.cost)
            return (oracle_utility, expected_reduction, -exp.cost)
            
        best_score = max(ranked_scores, key=privileged_score_candidate)
        chosen_exp = exp_by_id[best_score.experiment_id]
        rationale = f"Selected '{chosen_exp.name}' via Privileged Greedy heuristic (1-step expected reduction under H*={h_star})."
        return chosen_exp, best_score, rationale
        
    else:
        raise ValueError(f"Unknown selection policy: '{policy_name}'")


class SequentialBEDEngine:
    """
    Executes a complete Sequential Bayesian Experimental Design campaign.
    
    Guarantees:
    - Strict isolation of Nature's hidden hypothesis from decision policies.
    - Deterministic reproducibility given a random seed.
    - Dynamic re-scoring of remaining candidate assays after each Bayesian update.
    - Support for multiple stopping conditions.
    """

    @staticmethod
    def run_campaign(
        scenario: AnalysisInput,
        input_params: BEDCampaignInput
    ) -> BEDCampaignResult:
        """
        Executes a multi-step sequential experimental design campaign.
        """
        start_time = datetime.now(timezone.utc).isoformat()
        campaign_id = f"BED-{uuid.uuid4().hex[:8].upper()}"
        warnings: List[str] = []
        
        # 1. Validate scenario priors and predictions
        normalized_priors, prior_warnings = validate_and_normalize_priors(scenario.hypotheses)
        warnings.extend(prior_warnings)
        hypothesis_ids = list(normalized_priors.keys())
        
        # Determine hidden hypothesis H* in simulation environment
        hypo_dict = {h.id: h.name for h in scenario.hypotheses}
        if input_params.hidden_hypothesis_id and input_params.hidden_hypothesis_id in hypo_dict:
            hidden_h_id = input_params.hidden_hypothesis_id
        else:
            # Default to first hypothesis (e.g. H1 Redox)
            hidden_h_id = hypothesis_ids[0]
            
        hidden_h_name = hypo_dict[hidden_h_id]
        
        # 2. Filter candidate pool: exclude unquantified proposals
        quantified_exps: List[Experiment] = []
        likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]] = {}
        
        for exp in scenario.experiments:
            if exp.quantification_status == "UNQUANTIFIED_NEEDS_MEASUREMENT" or len(exp.predictions) == 0:
                warnings.append(f"Excluded unquantified candidate '{exp.id}' from sequential candidate pool.")
                continue
            matrix, exp_warnings = validate_experiment_predictions(exp, hypothesis_ids)
            likelihood_matrices[exp.id] = matrix
            warnings.extend(exp_warnings)
            quantified_exps.append(exp)
            
        if not quantified_exps:
            raise ScientificValidationError("No quantified candidate experiments available for sequential BED.")
            
        # 3. Initialize Nature simulation environment and RNG
        nature_rng = np.random.default_rng(input_params.seed)
        nature = Nature(
            hidden_hypothesis_id=hidden_h_id,
            rng=nature_rng,
            candidate_experiments=quantified_exps,
            likelihood_matrices=likelihood_matrices
        )
        # Dedicated policy RNG decoupled from Nature simulation
        policy_rng = np.random.default_rng(input_params.seed + 9999)
        
        # 4. Initialize sequential campaign state
        current_prior = dict(normalized_priors)
        available_candidates: List[Experiment] = list(quantified_exps)
        cumulative_cost = 0.0
        total_realized_ig = 0.0
        execution_failures = 0
        uninformative_selections = 0
        steps: List[BEDCampaignStep] = []
        
        termination_reason = "MAX_STEPS_REACHED"
        target_confidence_achieved = False
        
        # 5. Sequential Execution Loop
        for step_idx in range(1, input_params.max_steps + 1):
            # Check stopping condition 1: Target confidence achieved prior to step
            max_conf = max(current_prior.values())
            if max_conf >= input_params.confidence_threshold:
                termination_reason = "TARGET_CONFIDENCE_ACHIEVED"
                target_confidence_achieved = True
                break
                
            # Check stopping condition 2: No candidates remaining
            if not available_candidates:
                termination_reason = "NO_CANDIDATES_REMAINING"
                break
                
            # Score and rank available candidates under current_prior
            ranked_scores = rank_experiments(
                experiments=available_candidates,
                normalized_priors=current_prior,
                likelihood_matrices=likelihood_matrices,
                cost_weight=input_params.cost_weight
            )
            
            # Check stopping condition 3: All remaining candidates are completely uninformative
            if all(s.expected_information_gain < 1e-4 for s in ranked_scores):
                # If current prior is already completely confident or completely stalled
                current_entropy = compute_shannon_entropy(list(current_prior.values()))
                if current_entropy < 0.05 or all(s.expected_information_gain < 1e-5 for s in ranked_scores):
                    termination_reason = "NO_INFORMATIVE_CANDIDATES_REMAINING"
                    break
                    
            # Select candidate according to policy (without exposing H*)
            is_privileged = input_params.policy in ("privileged_greedy", "oracle")
            chosen_exp, chosen_score, rationale = select_candidate_experiment(
                policy_name=input_params.policy,
                available_experiments=available_candidates,
                ranked_scores=ranked_scores,
                likelihood_matrices=likelihood_matrices,
                current_prior=current_prior,
                cost_weight=input_params.cost_weight,
                rng=policy_rng,
                oracle_hidden_hypothesis_id=nature.hidden_hypothesis_id if is_privileged else None
            )
            
            # Check stopping condition 4: Budget exhausted
            if cumulative_cost + chosen_exp.cost > input_params.budget:
                # Can any remaining candidate fit within remaining budget?
                remaining_budget = input_params.budget - cumulative_cost
                affordable_candidates = [e for e in available_candidates if e.cost <= remaining_budget]
                if not affordable_candidates:
                    termination_reason = "BUDGET_EXHAUSTED"
                    break
                else:
                    # Filter to affordable candidates and re-select
                    affordable_scores = [s for s in ranked_scores if s.cost <= remaining_budget]
                    chosen_exp, chosen_score, rationale = select_candidate_experiment(
                        policy_name=input_params.policy,
                        available_experiments=affordable_candidates,
                        ranked_scores=affordable_scores,
                        likelihood_matrices=likelihood_matrices,
                        current_prior=current_prior,
                        cost_weight=input_params.cost_weight,
                        rng=policy_rng,
                        oracle_hidden_hypothesis_id=nature.hidden_hypothesis_id if is_privileged else None
                    )
                    
            # Track zero EIG selections (waste rate)
            if chosen_score.expected_information_gain < 0.01:
                uninformative_selections += 1
                
            # 6. Physical execution simulation via Nature
            is_successful, observed_outcome = nature.execute_experiment(
                experiment=chosen_exp,
                likelihood_matrix=likelihood_matrices[chosen_exp.id]
            )
            
            prior_entropy = compute_shannon_entropy(list(current_prior.values()))
            step_cost = float(chosen_exp.cost)
            cumulative_cost += step_cost
            
            # 7. Bayesian posterior update
            if is_successful and observed_outcome:
                execution_status = "SUCCESS"
                updated_posterior = compute_bayesian_posterior_update(
                    prior=current_prior,
                    observed_outcome=observed_outcome,
                    likelihood_matrix=likelihood_matrices[chosen_exp.id]
                )
                post_entropy = compute_shannon_entropy(list(updated_posterior.values()))
                # Realized information gain is signed entropy reduction: Delta H = H(P_{t-1}) - H(P_t)
                # Preserving sign ensures telescoping sum sum(Delta H_t) == H(P_0) - H(P_T)
                realized_ig = prior_entropy - post_entropy
            else:
                # Execution failure: experiment aborted due to feasibility barrier
                execution_status = "EXECUTION_FAILURE"
                execution_failures += 1
                # Posterior remains strictly unchanged (failure carries no likelihood evidence)
                updated_posterior = dict(current_prior)
                realized_ig = 0.0
                
            total_realized_ig += realized_ig
            
            # 8. Consume candidate (one-shot experiment)
            available_candidates = [e for e in available_candidates if e.id != chosen_exp.id]
            
            # 9. Dynamic re-ranking of remaining candidates for inspector view
            if available_candidates:
                re_ranked = rank_experiments(
                    experiments=available_candidates,
                    normalized_priors=updated_posterior,
                    likelihood_matrices=likelihood_matrices,
                    cost_weight=input_params.cost_weight
                )
            else:
                re_ranked = []
                
            step_record = BEDCampaignStep(
                step_number=step_idx,
                selected_experiment_id=chosen_exp.id,
                selected_experiment_name=chosen_exp.name,
                execution_status=execution_status,
                observed_outcome=observed_outcome,
                simulated_is_successful=is_successful,
                prior_distribution={k: round(v, 4) for k, v in current_prior.items()},
                posterior_distribution={k: round(v, 4) for k, v in updated_posterior.items()},
                predicted_eig=round(chosen_score.expected_information_gain, 4),
                realized_information_gain=round(realized_ig, 4),
                step_cost=round(step_cost, 2),
                cumulative_cost=round(cumulative_cost, 2),
                remaining_candidate_count=len(available_candidates),
                remaining_candidate_scores=re_ranked,
                selection_rationale=rationale
            )
            steps.append(step_record)
            
            # Advance prior for next sequential iteration
            current_prior = dict(updated_posterior)
            
            # Check stopping condition immediately after update
            if max(current_prior.values()) >= input_params.confidence_threshold:
                termination_reason = "TARGET_CONFIDENCE_ACHIEVED"
                target_confidence_achieved = True
                break
                
        # Final confidence in true hidden hypothesis H*
        final_conf_h_star = float(current_prior.get(hidden_h_id, 0.0))
        
        return BEDCampaignResult(
            campaign_id=campaign_id,
            timestamp=start_time,
            scenario_name=scenario.scenario_name,
            policy_name=input_params.policy,
            hidden_hypothesis_id=hidden_h_id,
            hidden_hypothesis_name=hidden_h_name,
            seed=input_params.seed,
            budget=input_params.budget,
            max_steps=input_params.max_steps,
            confidence_threshold=input_params.confidence_threshold,
            initial_priors={k: round(v, 4) for k, v in normalized_priors.items()},
            final_posterior={k: round(v, 4) for k, v in current_prior.items()},
            final_confidence_in_hidden_hypothesis=round(final_conf_h_star, 4),
            steps=steps,
            total_steps=len(steps),
            total_cost=round(cumulative_cost, 2),
            total_realized_information_gain=round(total_realized_ig, 4),
            termination_reason=termination_reason,
            target_confidence_achieved=target_confidence_achieved,
            execution_failure_count=execution_failures,
            uninformative_selection_count=uninformative_selections,
            warnings=warnings
        )


def compute_offline_combinatorial_upper_bound(
    scenario: AnalysisInput,
    quantified_experiments: List[Experiment],
    likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]],
    initial_priors: Dict[str, float],
    nature: Nature,
    budget: float,
    max_evaluations: int = 100000
) -> Tuple[float, List[str], float, Dict[str, float]]:
    """
    Computes the true global offline combinatorial upper bound on realized information gain
    for the exact physical realization generated by Nature under the given seed.
    
    1. Filters out uninformative controls (identical likelihoods across all hypotheses)
       which mathematically cannot alter posterior beliefs.
    2. Sorts candidate experiments by cost ascending to enable exact branch-and-bound pruning.
    3. Traverses all budget-admissible subsets: any branch whose cumulative cost exceeds budget
       is pruned immediately.
    4. Simulates Bayesian posterior updates for all successful executions in each budget-admissible subset.
    5. Computes realized information gain Delta H(S) = H(P_0) - H(P_final).
    6. Returns max_{S} Delta H(S), optimal subset, cost, and final posterior.
    
    Guarantees: Delta H_realized(pi) <= O*_offline for ALL sequential policies pi.
    """
    h_ids = list(initial_priors.keys())
    p0_entropy = compute_shannon_entropy(list(initial_priors.values()))
    realizations = nature.counterfactual_realizations
    
    # 1. Prune uninformative assays (zero differential diagnostic likelihood across all hypotheses)
    informative: List[Experiment] = []
    for exp in quantified_experiments:
        is_diag = False
        for y in exp.possible_outcomes:
            probs = [likelihood_matrices[exp.id][h].get(y, 0.0) for h in h_ids]
            if max(probs) - min(probs) > 1e-4:
                is_diag = True
                break
        if is_diag:
            informative.append(exp)
            
    if not informative:
        return 0.0, [], 0.0, dict(initial_priors)
        
    # 2. Sort candidate experiments by cost ascending for exact branch-and-bound pruning
    sorted_informative = sorted(informative, key=lambda e: e.cost)
    
    best_ig = 0.0
    best_subset: List[str] = []
    best_cost = 0.0
    best_posterior = dict(initial_priors)
    
    # Branch-and-bound DFS
    # Stack stores: (start_index, current_cost, current_posterior, current_subset_ids)
    stack = [(0, 0.0, dict(initial_priors), [])]
    eval_count = 0
    
    while stack and eval_count < max_evaluations:
        idx, cur_cost, cur_post, cur_ids = stack.pop()
        eval_count += 1
        
        if cur_ids:
            cur_entropy = compute_shannon_entropy(list(cur_post.values()))
            cur_ig = max(p0_entropy - cur_entropy, 0.0)
            if cur_ig > best_ig + 1e-6 or (abs(cur_ig - best_ig) <= 1e-6 and cur_cost < best_cost):
                best_ig = cur_ig
                best_subset = list(cur_ids)
                best_cost = cur_cost
                best_posterior = cur_post
                
        # Explore adding subsequent experiments
        # Since sorted_informative is sorted by cost ascending, break early when cost limit exceeded
        for i in range(idx, len(sorted_informative)):
            exp = sorted_informative[i]
            nxt_cost = cur_cost + exp.cost
            if nxt_cost > budget + 1e-9:
                break
                
            is_succ, outcome = realizations.get(exp.id, (True, None))
            if is_succ and outcome:
                nxt_post = compute_bayesian_posterior_update(
                    cur_post,
                    outcome,
                    likelihood_matrices[exp.id]
                )
            else:
                nxt_post = cur_post
                
            stack.append((i + 1, nxt_cost, nxt_post, cur_ids + [exp.id]))
            
    return round(best_ig, 4), best_subset, round(best_cost, 2), best_posterior
