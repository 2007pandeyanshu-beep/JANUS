"""JANUS Deterministic Scientific Engine

Coordinates the full scientific analysis pipeline:
1. Schema & probability distribution validation
2. Feasibility constraint checks
3. Strict separation of Quantified Bayesian vs Unquantified Proposal experiments
4. Information-theoretic scoring & ranking
5. Baseline comparison
6. Transparent audit trail generation
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List
from app.schemas.scientific import (
    AnalysisInput,
    AnalysisResult,
    ExperimentScore,
    Experiment,
)
from scientific.validation import (
    validate_and_normalize_priors,
    validate_experiment_predictions,
    ScientificValidationError,
)
from scientific.scoring import (
    rank_experiments,
    compute_shannon_entropy,
)
from evaluation.baselines import evaluate_random_selection_baseline


class ScientificEngine:
    """Core deterministic execution engine for JANUS."""
    
    @staticmethod
    def execute_analysis(payload: AnalysisInput) -> AnalysisResult:
        """
        Executes a deterministic experiment ranking analysis.
        Strictly reproducible: identical inputs yield identical outputs.
        """
        audit_trail: List[str] = []
        warnings: List[str] = []
        
        start_time = datetime.now(timezone.utc).isoformat()
        analysis_id = f"ANL-{uuid.uuid4().hex[:8].upper()}"
        
        audit_trail.append(f"Initialized analysis '{analysis_id}' for scenario: {payload.scenario_name}")
        audit_trail.append(f"Scenario Type: {payload.scenario_type.upper()} (is_synthetic={payload.is_synthetic})")
        
        if payload.is_synthetic:
            warnings.append(
                "SYNTHETIC DATA ADVISORY: All likelihoods, priors, and outcomes in this scenario "
                "are synthetic benchmark values designed for algorithmic validation. "
                "Do not use these values for clinical or wet-lab decision making without empirical validation."
            )
        else:
            audit_trail.append(
                f"Ground-truth mode active: Ingested {len(payload.evidence)} primary literature evidence claims."
            )
        
        # 1. Validate & normalize priors
        normalized_priors, prior_warnings = validate_and_normalize_priors(payload.hypotheses)
        warnings.extend(prior_warnings)
        audit_trail.append(
            f"Validated {len(payload.hypotheses)} competing hypotheses. "
            f"Normalized priors: {', '.join(f'{k}={v:.3f}' for k, v in normalized_priors.items())}"
        )
        
        prior_entropy = compute_shannon_entropy(list(normalized_priors.values()))
        
        # 2. Separate Quantified vs Unquantified Candidate Experiments
        quantified_exps: List[Experiment] = []
        unquantified_scores: List[ExperimentScore] = []
        
        for exp in payload.experiments:
            if exp.quantification_status == "UNQUANTIFIED_NEEDS_MEASUREMENT":
                missing_info = (
                    f"Candidate experiment '{exp.name}' is grounded in published literature, but "
                    f"reliable quantitative likelihood distributions are not yet available. "
                    f"JANUS refuses to fabricate arbitrary probabilities. Experimental signal-to-noise "
                    f"measurements or calibrated microkinetic models are required to compute EIG."
                )
                unquantified_scores.append(
                    ExperimentScore(
                        experiment_id=exp.id,
                        experiment_name=exp.name,
                        rank=None,
                        utility_rank=None,
                        eig_rank=None,
                        quantification_status="UNQUANTIFIED_NEEDS_MEASUREMENT",
                        prior_entropy=round(prior_entropy, 6),
                        expected_posterior_entropy=round(prior_entropy, 6),
                        expected_information_gain=0.0,
                        normalized_information_gain=0.0,
                        feasibility=float(exp.feasibility),
                        cost=float(exp.cost),
                        composite_utility_score=0.0,
                        outcome_marginal_probabilities={},
                        posterior_matrix={},
                        explanation=missing_info,
                        missing_inputs_explanation=missing_info,
                        is_informative=False
                    )
                )
                warnings.append(f"UNQUANTIFIED INPUT: '{exp.id}' ({exp.name}) requires quantitative measurement.")
                audit_trail.append(
                    f"Flagged '{exp.id}' as UNQUANTIFIED. Preserved in evidence view without fabricated scores."
                )
            else:
                quantified_exps.append(exp)
        
        # 3. Validate likelihood predictions for all quantified experiments
        hypothesis_ids = list(normalized_priors.keys())
        likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]] = {}
        
        for exp in quantified_exps:
            matrix, exp_warnings = validate_experiment_predictions(exp, hypothesis_ids)
            likelihood_matrices[exp.id] = matrix
            warnings.extend(exp_warnings)
            audit_trail.append(
                f"Validated outcome distribution for experiment '{exp.id}' ({len(exp.possible_outcomes)} outcomes)."
            )
            
        # 4. Deterministic Information-Theoretic Scoring & Ranking
        ranked_scores = rank_experiments(
            experiments=quantified_exps,
            normalized_priors=normalized_priors,
            likelihood_matrices=likelihood_matrices,
            cost_weight=payload.cost_weight
        )
        audit_trail.append(
            f"Ranked {len(ranked_scores)} quantified experiments using expected information gain (EIG) "
            f"and composite cost-feasibility utility (cost_weight={payload.cost_weight})."
        )
        
        # 5. Baseline Evaluation on the Quantified Experiment Set
        baseline = evaluate_random_selection_baseline(ranked_scores)
        audit_trail.append(
            f"Evaluated random baseline: Mean EIG = {baseline.baseline_expected_eig:.4f} bits. "
            f"Top experiment improvement ratio = {baseline.eig_improvement_ratio}x."
        )
        
        return AnalysisResult(
            analysis_id=analysis_id,
            timestamp=start_time,
            scenario_name=payload.scenario_name,
            scenario_type=payload.scenario_type,
            case_study_id=payload.case_study_id,
            is_synthetic=payload.is_synthetic,
            hypotheses=payload.hypotheses,
            normalized_priors={k: round(v, 4) for k, v in normalized_priors.items()},
            ranked_experiments=ranked_scores,
            unquantified_experiments=unquantified_scores,
            baseline_comparison=baseline,
            audit_trail=audit_trail,
            warnings=warnings,
            validation_status="VALIDATED_DETERMINISTIC"
        )
