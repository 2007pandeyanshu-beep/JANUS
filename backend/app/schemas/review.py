"""Pydantic schemas for the JANUS Coordinator Scientific Critic and Review Stage (Phase 8).

Defines strongly-typed schemas for evaluating multi-agent scientific outputs across 7 core dimensions:
1. Evidence sufficiency & provenance
2. Hypothesis consistency & simplex normalization
3. Scientific computation validity & numerical limits
4. Experiment ranking integrity & unquantified assay handling
5. Uncertainty & limitations disclosure
6. Cross-agent consistency & contradiction detection
7. Conclusion discipline & three-state conclusion gating
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    """Execution status of the Critic/Review evaluation."""
    REVIEW_COMPLETED = "REVIEW_COMPLETED"
    REVIEW_PARTIAL = "REVIEW_PARTIAL"
    REVIEW_FAILED = "REVIEW_FAILED"
    REVIEW_UNAVAILABLE = "REVIEW_UNAVAILABLE"


class ConclusionGateStatus(str, Enum):
    """Three-state scientific conclusion gate regulating downstream presentation and action."""
    SUFFICIENTLY_SUPPORTED = "SUFFICIENTLY_SUPPORTED"
    REQUIRES_QUALIFICATION = "REQUIRES_QUALIFICATION"
    WITHHOLD_CONCLUSIONS = "WITHHOLD_CONCLUSIONS"


class ReviewCategory(str, Enum):
    """The 7 scientific evaluation dimensions plus independent audit alignment."""
    EVIDENCE_SUFFICIENCY = "EVIDENCE_SUFFICIENCY"
    HYPOTHESIS_CONSISTENCY = "HYPOTHESIS_CONSISTENCY"
    SCIENTIFIC_COMPUTATION = "SCIENTIFIC_COMPUTATION"
    EXPERIMENT_RANKING = "EXPERIMENT_RANKING"
    UNCERTAINTY_DISCLOSURE = "UNCERTAINTY_DISCLOSURE"
    CROSS_AGENT_CONSISTENCY = "CROSS_AGENT_CONSISTENCY"
    CONCLUSION_DISCIPLINE = "CONCLUSION_DISCIPLINE"
    INDEPENDENT_AUDIT = "INDEPENDENT_AUDIT"


class ReviewFindingItem(BaseModel):
    """Detailed scientific review finding registered by the Critic."""
    finding_id: str = Field(..., description="Unique finding identifier (e.g. REV-EVD-001, REV-HYP-001)")
    category: ReviewCategory = Field(..., description="Evaluation dimension category")
    severity: str = Field(
        ...,
        description="Severity level: VERIFIED, NOTE, WARNING, HIGH_SEVERITY_CHALLENGE, UNRESOLVED_DISAGREEMENT",
    )
    target_agent: str = Field(..., description="Specialist agent or role evaluated")
    target_object: str = Field(..., description="Specific claim, parameter, assay, or hypothesis evaluated")
    claim: str = Field(..., description="Original claim or assertion under review")
    critique: str = Field(..., description="Critical scientific assessment and boundary analysis")
    evidence_basis: str = Field(..., description="Empirical, mathematical, or literature evidence basis")
    recommendation: str = Field(..., description="Actionable recommendation or constraint for synthesis")
    is_blocking: bool = Field(
        default=False,
        description="True if finding prevents proceeding to SUFFICIENTLY_SUPPORTED (forces WITHHOLD_CONCLUSIONS)",
    )


class ScientificReviewRequest(BaseModel):
    """Input payload to the Scientific Critic Engine."""
    correlation_id: str = Field(..., description="Unique correlation tracking ID")
    investigation_id: Optional[str] = Field(default=None, description="JANUS investigation identifier")
    question: str = Field(..., description="Scientific inquiry or mechanistic question")
    case_study_id: Optional[str] = Field(default="CS-CAT-001", description="Case study identifier if applicable")
    is_synthetic: bool = Field(default=False, description="Whether scenario is a synthetic benchmark")
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list, description="Formulated competing hypotheses")
    candidate_experiments: List[Dict[str, Any]] = Field(default_factory=list, description="Candidate assays")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved evidence records")
    ranked_experiments: List[Dict[str, Any]] = Field(default_factory=list, description="Ranked experiments from BED")
    tool_executions: List[Dict[str, Any]] = Field(default_factory=list, description="Tool execution records")
    independent_verification: Optional[Dict[str, Any]] = Field(default=None, description="Internal math verifier result")
    auditor_address: Optional[str] = Field(default="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg", description="Fetch.ai address of auditor agent")
    auditor_status: Optional[str] = Field(default=None, description="External Auditor uAgent status (AUDIT_PASSED, etc.)")
    auditor_verdict: Optional[str] = Field(default=None, description="External Auditor uAgent verdict statement")
    unquantified_experiments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Unquantified assays excluded from ranking",
    )


class ScientificReviewReport(BaseModel):
    """Structured review evaluation report produced by the Coordinator's Critic/Review Stage."""
    correlation_id: str = Field(..., description="Correlation ID matching request")
    investigation_id: Optional[str] = Field(default=None, description="JANUS investigation identifier")
    status: ReviewStatus = Field(..., description="Review execution status")
    conclusion_gate: ConclusionGateStatus = Field(
        ...,
        description="Conclusion gate state: SUFFICIENTLY_SUPPORTED, REQUIRES_QUALIFICATION, or WITHHOLD_CONCLUSIONS",
    )
    gate_rationale: str = Field(..., description="Scientific and mathematical rationale for the conclusion gate verdict")
    total_findings_count: int = Field(default=0, description="Total number of registered findings")
    blocking_findings_count: int = Field(default=0, description="Number of blocking findings that withhold conclusions")
    findings: List[ReviewFindingItem] = Field(default_factory=list, description="All registered critique findings")
    evaluated_dimensions: List[str] = Field(default_factory=list, description="List of evaluated dimension names")
    disclosed_limitations: List[str] = Field(default_factory=list, description="Explicitly disclosed boundaries and limitations")
    summary: str = Field(default="", description="Executive consensus review summary")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of review completion")
