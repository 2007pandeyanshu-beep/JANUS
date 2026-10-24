"""Pydantic schemas for the JANUS Independent Experiment Designer uAgent (Phase 7).

Defines the message payload contracts for the Fetch.ai `janus_experiment_design` protocol (v1.0.0).
Provides strongly-typed schemas for requesting Bayesian Experimental Design (BED) evaluation,
information-theoretic ranking, composite utility scoring, and sequential candidate re-ranking.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExperimentScoreItem(BaseModel):
    """Structured representation of an evaluated and scored candidate experiment."""
    experiment_id: str = Field(..., description="Unique experiment assay identifier (e.g. EXP-WGS-02)")
    experiment_name: str = Field(..., description="Descriptive title of experimental assay")
    rank: Optional[int] = Field(default=None, description="Overall primary rank (ordered by composite utility)")
    utility_rank: Optional[int] = Field(default=None, description="Rank ordered strictly by composite utility score")
    eig_rank: Optional[int] = Field(default=None, description="Rank ordered strictly by pure expected information gain (bits)")
    quantification_status: str = Field(default="QUANTIFIED", description="QUANTIFIED or UNQUANTIFIED_NEEDS_MEASUREMENT")
    prior_entropy: float = Field(default=0.0, description="Prior Shannon entropy H(P) in bits")
    expected_posterior_entropy: float = Field(default=0.0, description="Expected posterior Shannon entropy in bits")
    expected_information_gain: float = Field(default=0.0, description="Expected Information Gain (EIG) in bits")
    normalized_information_gain: float = Field(default=0.0, description="EIG normalized by prior entropy [0.0, 1.0]")
    feasibility: float = Field(default=1.0, ge=0.0, le=1.0, description="Technical/resource feasibility score [0.0, 1.0]")
    cost: float = Field(default=1.0, ge=0.0, description="Normalized economic/operational cost score")
    composite_utility_score: float = Field(default=0.0, description="Composite utility: Feasibility * EIG / (1 + alpha * Cost)")
    outcome_marginal_probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Marginal probability distribution P(y|e) across possible outcomes",
    )
    posterior_matrix: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Posterior probability matrix P(H_k | y, e) for each outcome y",
    )
    explanation: str = Field(default="", description="Detailed scientific and mathematical ranking rationale")
    missing_inputs_explanation: Optional[str] = Field(default=None, description="Explanation for unquantified assays")
    is_informative: bool = Field(default=True, description="True if assay provides non-zero diagnostic information (EIG > 1e-4)")


class ExperimentDesignRequest(BaseModel):
    """Inbound request model for the `janus_experiment_design` protocol."""
    correlation_id: str = Field(..., description="Unique correlation ID tracing this design request across uAgents")
    investigation_id: Optional[str] = Field(default=None, description="JANUS investigation identifier")
    scenario_name: str = Field(..., description="Descriptive scenario or inquiry title")
    scenario_type: str = Field(default="published_case_study", description="Scenario type: published_case_study or synthetic_benchmark")
    case_study_id: Optional[str] = Field(default="CS-CAT-001", description="Associated scenario identifier (e.g. CS-CAT-001, CS-OER-002)")
    hypotheses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Competing hypothesis definitions with prior probabilities P(H_k)",
    )
    candidate_experiments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Candidate experiment definitions with likelihood distributions P(y | H_k)",
    )
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Optional evidence records for context and provenance tracking",
    )
    cost_weight: float = Field(default=0.1, ge=0.0, description="Cost weight factor alpha in composite utility ranking")
    max_cost_budget: Optional[float] = Field(default=None, ge=0.0, description="Optional hard budget constraint ceiling")
    is_synthetic: bool = Field(default=False, description="Flag indicating if scenario uses synthetic benchmark fixtures")


class ExperimentDesignResponse(BaseModel):
    """Outbound response model for the `janus_experiment_design` protocol."""
    correlation_id: str = Field(..., description="Echoes correlation ID from request")
    investigation_id: Optional[str] = Field(default=None, description="JANUS investigation identifier")
    status: str = Field(
        ...,
        description="DESIGN_COMPLETED, DESIGN_PARTIAL, INSUFFICIENT_CANDIDATES, or DESIGN_UNAVAILABLE",
    )
    agent_address: str = Field(..., description="Fetch.ai cryptographic address of the Experiment Designer Agent")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of design completion")
    scenario_name: str = Field(default="", description="Evaluated scenario name")
    scenario_type: str = Field(default="published_case_study", description="Evaluated scenario type")
    case_study_id: Optional[str] = Field(default=None, description="Evaluated scenario identifier")
    is_synthetic: bool = Field(default=False, description="Synthetic benchmark flag")
    normalized_priors: Dict[str, float] = Field(
        default_factory=dict,
        description="Validated and normalized prior probability simplex",
    )
    prior_entropy_bits: float = Field(default=0.0, description="Prior Shannon entropy H(P) in bits")
    cost_weight_alpha: float = Field(default=0.1, description="Cost weight factor alpha applied in ranking")
    ranked_experiments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Ranked candidate assays ordered by composite utility",
    )
    unquantified_experiments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Preserved unquantified candidate assays requiring empirical calibration",
    )
    top_recommendation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optimal candidate assay under JANUS utility policy",
    )
    baseline_comparison: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Random selection baseline comparison metrics",
    )
    audit_trail: List[str] = Field(
        default_factory=list,
        description="Deterministic audit trail of engine operations",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Diagnostic warnings, caveats, or boundary disclaimers",
    )
    execution_time_ms: float = Field(default=0.0, description="Execution runtime in milliseconds")
