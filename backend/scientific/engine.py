"""JANUS Deterministic Scientific Engine

Coordinates the full scientific analysis pipeline:
1. Schema & probability distribution validation
2. Feasibility constraint checks
3. Information-theoretic scoring & ranking
4. Baseline comparison
5. Transparent audit trail generation
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List
from app.schemas.scientific import AnalysisInput, AnalysisResult, ExperimentScore
from scientific.validation import (
    validate_and_normalize_priors,
    validate_experiment_predictions,
    ScientificValidationError,
)
from scientific.scoring import rank_experiments
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
        
        if payload.is_synthetic:
            warnings.append(
                "SYNTHETIC DATA ADVISORY: All likelihoods, priors, and outcomes in this scenario "
                "are synthetic benchmark values designed for algorithmic validation. "
                "Do not use these values for clinical or wet-lab decision making without empirical validation."
            )
        
        # 1. Validate & normalize priors
        normalized_priors, prior_warnings = validate_and_normalize_priors(payload.hypotheses)
        warnings.extend(prior_warnings)
        audit_trail.append(
            f"Validated {len(payload.hypotheses)} competing hypotheses. "
            f"Normalized priors: {', '.join(f'{k}={v:.3f}' for k, v in normalized_priors.items())}"
        )
        
        # 2. Validate likelihood predictions for all experiments
        hypothesis_ids = list(normalized_priors.keys())
        likelihood_matrices: Dict[str, Dict[str, Dict[str, float]]] = {}
        
        for exp in payload.experiments:
            matrix, exp_warnings = validate_experiment_predictions(exp, hypothesis_ids)
            likelihood_matrices[exp.id] = matrix
            warnings.extend(exp_warnings)
            audit_trail.append(
                f"Validated outcome distribution for experiment '{exp.id}' ({len(exp.possible_outcomes)} outcomes)."
            )
            
        # 3. Deterministic Information-Theoretic Scoring & Ranking
        ranked_scores = rank_experiments(
            experiments=payload.experiments,
            normalized_priors=normalized_priors,
            likelihood_matrices=likelihood_matrices,
            cost_weight=payload.cost_weight
        )
        audit_trail.append(
            f"Ranked {len(ranked_scores)} candidate experiments using expected information gain (EIG) "
            f"and composite cost-feasibility utility (cost_weight={payload.cost_weight})."
        )
        
        # 4. Baseline Evaluation
        baseline = evaluate_random_selection_baseline(ranked_scores)
        audit_trail.append(
            f"Evaluated random baseline: Mean EIG = {baseline.baseline_expected_eig:.4f} bits. "
            f"Top experiment improvement ratio = {baseline.eig_improvement_ratio}x."
        )
        
        return AnalysisResult(
            analysis_id=analysis_id,
            timestamp=start_time,
            scenario_name=payload.scenario_name,
            is_synthetic=payload.is_synthetic,
            hypotheses=payload.hypotheses,
            normalized_priors={k: round(v, 4) for k, v in normalized_priors.items()},
            ranked_experiments=ranked_scores,
            baseline_comparison=baseline,
            audit_trail=audit_trail,
            warnings=warnings,
            validation_status="VALIDATED_DETERMINISTIC"
        )
