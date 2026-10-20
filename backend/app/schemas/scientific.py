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


# ==============================================================================
# Sequential Bayesian Experimental Design (BED) Schemas (Phase 5)
# ==============================================================================

class BEDCampaignStep(BaseModel):
    """A single sequential decision, execution, and Bayesian update step in a BED campaign."""
    step_number: int = Field(..., description="1-indexed sequential step number")
    selected_experiment_id: str
    selected_experiment_name: str
    execution_status: str = Field(..., description="'SUCCESS' or 'EXECUTION_FAILURE'")
    observed_outcome: Optional[str] = Field(default=None, description="Observed categorical outcome label if successful")
    simulated_is_successful: bool = Field(..., description="True if feasibility check succeeded")
    
    # Bayesian distribution states
    prior_distribution: Dict[str, float] = Field(..., description="P(H_k) immediately before this step")
    posterior_distribution: Dict[str, float] = Field(..., description="P(H_k | y) immediately after this step")
    
    # Information & Cost metrics
    predicted_eig: float = Field(..., description="Expected Information Gain in bits calculated prior to execution")
    realized_information_gain: float = Field(..., description="Actual Shannon entropy reduction H(prior) - H(posterior) in bits")
    step_cost: float
    cumulative_cost: float
    
    # State of remaining pool
    remaining_candidate_count: int
    remaining_candidate_scores: List[ExperimentScore] = Field(
        default_factory=list,
        description="Top re-ranked candidate scores under updated posterior"
    )
    selection_rationale: str


class BEDCampaignResult(BaseModel):
    """Complete reproducible record of a Sequential Bayesian Experimental Design campaign."""
    campaign_id: str
    timestamp: str
    scenario_name: str
    policy_name: str
    hidden_hypothesis_id: str = Field(..., description="Designated true hypothesis in simulation environment")
    hidden_hypothesis_name: str
    seed: int
    budget: float
    max_steps: int
    confidence_threshold: float
    
    # Outcome states
    initial_priors: Dict[str, float]
    final_posterior: Dict[str, float]
    final_confidence_in_hidden_hypothesis: float = Field(..., description="P(H* | observed evidence)")
    
    # Campaign progression
    steps: List[BEDCampaignStep]
    total_steps: int
    total_cost: float
    total_realized_information_gain: float = Field(..., description="Cumulative entropy reduction in bits")
    
    # Termination
    termination_reason: str = Field(
        ...,
        description="'TARGET_CONFIDENCE_ACHIEVED', 'BUDGET_EXHAUSTED', 'MAX_STEPS_REACHED', 'NO_CANDIDATES_REMAINING', or 'NO_INFORMATIVE_CANDIDATES_REMAINING'"
    )
    target_confidence_achieved: bool
    execution_failure_count: int
    uninformative_selection_count: int
    warnings: List[str] = Field(default_factory=list)


class BEDCampaignInput(BaseModel):
    """Input payload to start a sequential BED campaign."""
    scenario_id: Optional[str] = Field(default="CS-CAT-001", description="'CS-CAT-001' or 'demo'")
    custom_scenario: Optional[AnalysisInput] = Field(default=None, description="Optional custom AnalysisInput payload")
    policy: str = Field(
        default="janus_utility",
        description="'janus_utility', 'raw_eig', 'cheapest', 'feasibility', 'uniform_random', or 'oracle'"
    )
    hidden_hypothesis_id: Optional[str] = Field(
        default=None,
        description="Specific hidden hypothesis H*; if None, defaulted to H1"
    )
    seed: int = Field(default=42, ge=0, description="Random seed for simulation reproducibility")
    budget: float = Field(default=10.0, gt=0.0, description="Maximum total campaign cost budget")
    max_steps: int = Field(default=8, ge=1, le=50, description="Maximum sequential intervention steps")
    confidence_threshold: float = Field(default=0.95, gt=0.5, le=0.999, description="Target posterior confidence P(H_k) >= threshold")
    cost_weight: float = Field(default=0.1, ge=0.0, description="Cost penalization weight alpha for composite utility")


class PolicyCampaignSummary(BaseModel):
    policy_key: str
    policy_name: str
    final_confidence_h_star: float
    total_steps: int
    total_cost: float
    total_realized_ig_bits: float
    execution_failures: int
    zero_eig_selections: int
    target_confidence_achieved: bool
    termination_reason: str
    runtime_ms: float
    regret_vs_oracle_utility: float = Field(..., description="Legacy regret field; now reports regret against offline combinatorial optimal")
    regret_vs_offline_optimal: float = Field(default=0.0, description="True non-negative regret vs offline combinatorial upper bound")
    signed_delta_vs_privileged: float = Field(default=0.0, description="Signed difference: privileged_greedy_ig - policy_ig")
    hypothesis_identified: bool = Field(default=False, description="True if top final posterior hypothesis matches true hidden hypothesis H*")


class BEDPolicyComparisonReport(BaseModel):
    comparison_id: str
    timestamp: str
    scenario_name: str
    hidden_hypothesis_id: str
    hidden_hypothesis_name: str
    seed: int
    budget: float
    confidence_threshold: float
    offline_optimal_ig_bits: float = Field(default=0.0, description="Global maximum realized IG achievable by any budget-admissible subset")
    offline_optimal_subset: List[str] = Field(default_factory=list, description="IDs of experiments in optimal subset")
    offline_optimal_cost: float = Field(default=0.0, description="Cost of optimal subset")
    policy_summaries: List[PolicyCampaignSummary]
    summary_verdict: str
