"""Pydantic schemas for the JANUS Independent Hypothesis Analyst uAgent (Phase 5).

Defines the message payload contracts for the Fetch.ai `janus_scientific_hypothesis` protocol.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HypothesisEvidenceLink(BaseModel):
    """Structured link connecting a specific empirical evidence item to a mechanistic hypothesis."""
    evidence_id: str = Field(..., description="Unique evidence identifier (e.g., CLM-WGS-001, EVD-OER-01)")
    relation_type: str = Field(
        ...,
        description="Epistemic relation: SUPPORTING, CONTRADICTING, INDIRECT, or NEUTRAL",
    )
    rationale: str = Field(..., description="Mechanistic explanation of how the evidence relates to the hypothesis")
    confidence_weight: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence weighting assigned to this link (0.0 to 1.0)",
    )


class HypothesisEvaluationItem(BaseModel):
    """Detailed evaluation and evidence-grounded formulation of a scientific hypothesis."""
    id: str = Field(..., description="Hypothesis identifier (e.g. H1, H2, H3)")
    name: str = Field(..., description="Descriptive title of the mechanistic hypothesis")
    description: str = Field(..., description="Detailed reaction mechanism or explanatory model")
    prior: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Prior probability P(H_k) in [0.0, 1.0]. Sum across hypotheses must equal 1.0",
    )
    evidence_links: List[HypothesisEvidenceLink] = Field(
        default_factory=list,
        description="Traceable links to specific retrieved evidence items with epistemic relations",
    )
    supporting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Identifiers of all retrieved evidence items supporting this hypothesis",
    )
    contradicting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Identifiers of all retrieved evidence items challenging or refuting this hypothesis",
    )
    epistemic_status: str = Field(
        default="VIABLE_CANDIDATE",
        description="Status: VIABLE_CANDIDATE, STRONGLY_CONTRADICTED, or INSUFFICIENT_EVIDENCE",
    )
    uncertainty_explanation: str = Field(
        default="",
        description="Explicit disclosure of model, kinetic, or measurement uncertainty",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Explicit physical or chemical assumptions underlying this hypothesis",
    )
    mathematical_formulation: Optional[str] = Field(
        default=None,
        description="Optional rate law, kinetic equation, or mathematical expression",
    )


class HypothesisAnalysisRequest(BaseModel):
    """Inbound request model for the `janus_scientific_hypothesis` protocol."""
    correlation_id: str = Field(..., description="Correlation ID tracing this investigation across uAgents")
    investigation_id: str = Field(..., description="JANUS investigation identifier")
    research_question: str = Field(..., description="Scientific inquiry or problem statement to formulate hypotheses for")
    case_study_id: Optional[str] = Field(default="CS-CAT-001", description="Associated scenario identifier (e.g. CS-CAT-001, CS-OER-002)")
    retrieved_evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of structured evidence records retrieved by the Research Agent",
    )
    existing_priors: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional calibrated prior probability vector to evaluate or preserve",
    )
    domain_assumptions: Optional[List[str]] = Field(
        default=None,
        description="Optional boundary conditions or known domain constraints",
    )


class HypothesisAnalysisResponse(BaseModel):
    """Outbound response model for the `janus_scientific_hypothesis` protocol."""
    correlation_id: str = Field(..., description="Echoes correlation ID from request")
    investigation_id: str = Field(..., description="JANUS investigation identifier")
    status: str = Field(
        ...,
        description="ANALYSIS_COMPLETED, ANALYSIS_PARTIAL, INSUFFICIENT_EVIDENCE, or ANALYSIS_UNAVAILABLE",
    )
    agent_address: str = Field(..., description="Fetch.ai cryptographic address of the Hypothesis Analyst Agent")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of hypothesis analysis completion")
    hypotheses: List[HypothesisEvaluationItem] = Field(
        default_factory=list,
        description="Formulated hypotheses with explicit evidence links, priors, and epistemic statuses",
    )
    simplex_sum: float = Field(
        default=1.0,
        description="Sum of prior probabilities across all hypotheses (must equal 1.0 within 1e-4)",
    )
    is_simplex_valid: bool = Field(
        default=True,
        description="Whether the probability simplex condition is rigorously satisfied",
    )
    unresolved_questions: List[str] = Field(
        default_factory=list,
        description="Key mechanistic questions that cannot be discriminated without further experimental data",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Diagnostic warnings or discrepancies identified during hypothesis formulation",
    )
    summary: str = Field(
        ...,
        description="Synthesis and mechanistic comparison of the candidate hypotheses",
    )
