"""JANUS Scientific Schemas

Rigid Pydantic schemas for scientific entities:
- Hypotheses
- Experiments
- Predicted Outcomes (Likelihoods)
- Evidence & Provenance
- Experiment Scores (Information-Theoretic)
- Analysis Results & Audit Trails
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class Evidence(BaseModel):
    """Scientific evidence supporting a hypothesis or prior assumption."""
    id: str = Field(..., description="Unique evidence identifier")
    title: str = Field(..., description="Short title of the evidence source")
    source: str = Field(..., description="Citation, DOI, or repository URL")
    provenance: str = Field(
        ...,
        description="Provenance level: 'synthetic_fixture', 'user_supplied', 'literature', or 'experimental_observation'"
    )
    summary: str = Field(..., description="Detailed description of the observation or finding")
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this evidence item (0.0 to 1.0)"
    )


class Hypothesis(BaseModel):
    """Scientific hypothesis competing to explain a phenomenon."""
    id: str = Field(..., description="Unique hypothesis identifier (e.g., 'H1')")
    name: str = Field(..., description="Short descriptive name")
    description: str = Field(..., description="Detailed mechanism or explanation")
    prior: float = Field(
        ...,
        gt=0.0,
        le=1.0,
        description="Prior probability P(H_k). Must be strictly positive"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Core assumptions underlying this hypothesis"
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="IDs of supporting evidence"
    )
    status: str = Field(
        default="active",
        description="Status: 'active', 'supported', 'marginalized', or 'rejected'"
    )


class PredictedOutcome(BaseModel):
    """The predicted outcome probability distribution for an experiment under a specific hypothesis."""
    outcome_label: str = Field(..., description="Label of the experimental outcome (e.g. 'Positive', 'Inhibited')")
    hypothesis_id: str = Field(..., description="Hypothesis ID under which this prediction applies")
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Likelihood P(y | H_k, e). Must be in [0, 1]"
    )
    uncertainty: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        description="Standard deviation or estimated variance in prediction"
    )


class Experiment(BaseModel):
    """Candidate experiment or intervention capable of generating observable outcomes."""
    id: str = Field(..., description="Unique experiment identifier (e.g., 'EXP-01')")
    name: str = Field(..., description="Descriptive title of the assay or experiment")
    description: str = Field(..., description="Protocol or procedure summary")
    possible_outcomes: List[str] = Field(
        ...,
        min_length=2,
        description="Exhaustive set of mutually exclusive outcome labels"
    )
    predictions: List[PredictedOutcome] = Field(
        ...,
        description="Outcome probability distributions for each competing hypothesis"
    )
    cost: float = Field(
        default=1.0,
        ge=0.01,
        description="Relative or monetary cost of executing this experiment (must be > 0)"
    )
    feasibility: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Technical/ethical feasibility score between 0.0 (impossible) and 1.0 (readily executable)"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Experimental assumptions (e.g., reagent specificity, linearity range)"
    )
    is_feasible: bool = Field(
        default=True,
        description="Hard constraint flag. If False, experiment is rejected during ranking"
    )


class ExperimentScore(BaseModel):
    """Information-theoretic evaluation and ranking score for an experiment."""
    experiment_id: str
    experiment_name: str
    rank: int = Field(..., ge=1, description="Deterministic rank (1 is most informative)")
    
    # Information-Theoretic Metrics (measured in bits for base-2 logarithms)
    prior_entropy: float = Field(..., description="Prior Shannon entropy H(H) in bits")
    expected_posterior_entropy: float = Field(..., description="Expected posterior Shannon entropy E_y[H(H|y)] in bits")
    expected_information_gain: float = Field(..., description="EIG = H(H) - E_y[H(H|y)] in bits (Mutual Information I(H; Y))")
    normalized_information_gain: float = Field(..., description="EIG normalized by prior entropy (0.0 to 1.0)")
    
    # Practical Constraints
    feasibility: float
    cost: float
    composite_utility_score: float = Field(
        ...,
        description="Deterministic utility incorporating EIG, feasibility, and cost: Feasibility * (EIG / (1 + 0.1 * Cost))"
    )
    
    # Diagnostic Breakdown
    outcome_marginal_probabilities: Dict[str, float] = Field(
        ...,
        description="Marginal outcome probabilities P(y | e) across all hypotheses"
    )
    posterior_matrix: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Posterior probability P(H_k | y, e) for each outcome y and hypothesis H_k"
    )
    explanation: str = Field(..., description="Deterministic scientific explanation for the score")
    is_informative: bool = Field(..., description="True if expected information gain > 1e-4 bits")


class AnalysisInput(BaseModel):
    """Input payload for a complete hypothesis disambiguation analysis."""
    scenario_name: str = Field(default="Scientific Disambiguation Scenario")
    hypotheses: List[Hypothesis] = Field(..., min_length=2, description="At least two competing hypotheses required")
    experiments: List[Experiment] = Field(..., min_length=1, description="At least one candidate experiment")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence items")
    is_synthetic: bool = Field(
        default=True,
        description="Explicit flag indicating whether inputs are synthetic / illustrative"
    )
    cost_weight: float = Field(
        default=0.1,
        ge=0.0,
        description="Weight alpha applied to cost penalization in composite score"
    )


class BaselineComparison(BaseModel):
    """Evaluation comparison against naive / baseline selection policies."""
    baseline_type: str = "random_selection"
    baseline_expected_eig: float
    best_experiment_eig: float
    eig_improvement_ratio: float
    summary: str


class AnalysisResult(BaseModel):
    """Complete reproducible output of a JANUS scientific analysis."""
    analysis_id: str
    timestamp: str
    scenario_name: str
    is_synthetic: bool
    hypotheses: List[Hypothesis]
    normalized_priors: Dict[str, float]
    ranked_experiments: List[ExperimentScore]
    baseline_comparison: BaselineComparison
    audit_trail: List[str]
    warnings: List[str]
    validation_status: str = Field(
        default="VALIDATED_DETERMINISTIC",
        description="Status flag indicating mathematical and schema verification"
    )
