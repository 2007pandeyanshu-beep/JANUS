"""JANUS Scientific Schemas

Rigid Pydantic schemas for scientific entities:
- Hypotheses
- Experiments (Quantified Bayesian and Unquantified Experimental Proposals)
- Predicted Outcomes (Likelihoods with Provenance)
- Evidence Ledger & Claims
- Experiment Scores (Information-Theoretic)
- Analysis Results & Audit Trails
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class Evidence(BaseModel):
    """Scientific evidence supporting a hypothesis or prior assumption."""
    id: str = Field(..., description="Unique evidence identifier (e.g. 'CLM-WGS-001')")
    title: str = Field(..., description="Short title of the claim or evidence source")
    source: str = Field(..., description="Citation, DOI, or repository URL")
    source_doi: Optional[str] = Field(default=None, description="Direct DOI string if available")
    source_location: Optional[str] = Field(default=None, description="Page, section, or figure in the cited source")
    exact_source_quote: Optional[str] = Field(default=None, description="Direct excerpt or table quote from primary literature")
    claim_status: Optional[str] = Field(default="VERIFIED_PRIMARY_SOURCE", description="Verification status")
    claim_type: Optional[str] = Field(default="source_reported_value", description="Classification of claim")
    ambiguity_notes: Optional[str] = Field(default=None, description="Scientific boundary conditions or ambiguities")
    provenance: str = Field(
        ...,
        description="Provenance level: 'empirical_observation', 'author_interpretation', 'computational_dft', 'synthetic_fixture', or 'unquantified_assumption'"
    )
    summary: str = Field(..., description="Detailed description of the observation or finding")
    quantitative_value: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted quantitative value, metric, range, and unit"
    )
    supports_hypotheses: List[str] = Field(default_factory=list, description="Hypothesis IDs supported")
    refutes_hypotheses: List[str] = Field(default_factory=list, description="Hypothesis IDs challenged/refuted")
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
    outcome_label: str = Field(..., description="Label of the experimental outcome (e.g. 'Formate_Decay_Matches_TOF')")
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
    derivation_mode: Optional[str] = Field(
        default="derived_from_reported_value_with_noise_model",
        description="Derivation: 'source_reported_frequency', 'derived_from_reported_value_with_noise_model', 'theoretical_null_control', or 'illustrative_synthetic'"
    )
    basis: Optional[str] = Field(
        default=None,
        description="Primary literature citation or physical principle establishing this likelihood"
    )


class Experiment(BaseModel):
    """Candidate experiment or intervention capable of generating observable outcomes."""
    id: str = Field(..., description="Unique experiment identifier (e.g., 'EXP-WGS-01')")
    name: str = Field(..., description="Descriptive title of the assay or experiment")
    description: str = Field(..., description="Protocol or procedure summary")
    quantification_status: str = Field(
        default="QUANTIFIED_BAYESIAN",
        description="'QUANTIFIED_BAYESIAN' if likelihoods are documented; 'UNQUANTIFIED_NEEDS_MEASUREMENT' if qualitative only"
    )
    possible_outcomes: List[str] = Field(
        ...,
        min_length=2,
        description="Exhaustive set of mutually exclusive outcome labels"
    )
    predictions: List[PredictedOutcome] = Field(
        default_factory=list,
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
    source_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence ledger IDs supporting this experimental design"
    )


class ExperimentScore(BaseModel):
    """Information-theoretic evaluation and ranking score for an experiment."""
    experiment_id: str
    experiment_name: str
    rank: Optional[int] = Field(default=None, description="Primary composite utility rank (1 is most optimal); None if unquantified")
    utility_rank: Optional[int] = Field(default=None, description="Deterministic rank ordered by composite utility (incorporating EIG, feasibility, and cost)")
    eig_rank: Optional[int] = Field(default=None, description="Deterministic rank ordered strictly by raw Expected Information Gain in bits (ignoring cost and feasibility)")
    quantification_status: str = Field(
        default="QUANTIFIED_BAYESIAN",
        description="'QUANTIFIED_BAYESIAN' or 'UNQUANTIFIED_NEEDS_MEASUREMENT'"
    )
    
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
        default_factory=dict,
        description="Marginal outcome probabilities P(y | e) across all hypotheses"
    )
    posterior_matrix: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Posterior probability P(H_k | y, e) for each outcome y and hypothesis H_k"
    )
    explanation: str = Field(..., description="Deterministic scientific explanation for the score")
    missing_inputs_explanation: Optional[str] = Field(
        default=None,
        description="For unquantified experiments, exact data or measurements needed to enable Bayesian ranking"
    )
    is_informative: bool = Field(default=False, description="True if expected information gain > 1e-4 bits")


class AnalysisInput(BaseModel):
    """Input payload for a complete hypothesis disambiguation analysis."""
    scenario_name: str = Field(default="Scientific Disambiguation Scenario")
    scenario_type: str = Field(
        default="synthetic_benchmark",
        description="'synthetic_benchmark' or 'published_case_study'"
    )
    case_study_id: Optional[str] = Field(default=None, description="Optional ID of published case study")
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
    scenario_type: str = Field(default="synthetic_benchmark", description="'synthetic_benchmark' or 'published_case_study'")
    case_study_id: Optional[str] = None
    is_synthetic: bool
    hypotheses: List[Hypothesis]
    normalized_priors: Dict[str, float]
    ranked_experiments: List[ExperimentScore]
    unquantified_experiments: List[ExperimentScore] = Field(
        default_factory=list,
        description="Experiments that cannot be ranked because published quantitative likelihoods are unavailable"
    )
    baseline_comparison: BaselineComparison
    audit_trail: List[str]
    warnings: List[str]
    validation_status: str = Field(
        default="VALIDATED_DETERMINISTIC",
        description="Status flag indicating mathematical and schema verification"
    )
