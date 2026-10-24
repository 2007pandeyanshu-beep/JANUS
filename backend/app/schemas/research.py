"""Pydantic schemas for the JANUS Independent Research uAgent (Phase 4).

Defines the message payload contracts for the Fetch.ai `janus_scientific_research` protocol.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ResearchEvidenceItem(BaseModel):
    """Structured scientific evidence item with full bibliographic provenance."""
    id: str = Field(..., description="Unique claim or evidence identifier (e.g., CLM-WGS-001, EVD-OER-01)")
    title: str = Field(..., description="Full scholarly title of the cited publication")
    authors: Optional[List[str]] = Field(default=None, description="Author names extracted from bibliographic record")
    source: str = Field(..., description="Human-readable citation string (e.g., Meunier et al., J. Catal. 252 (2007) 18–22)")
    source_doi: Optional[str] = Field(default=None, description="Canonical DOI identifier (e.g., 10.1016/j.jcat.2007.10.004)")
    source_url: Optional[str] = Field(default=None, description="Direct URL to official publication record")
    provenance: str = Field(default="literature_derived", description="Evidence derivation category")
    summary: str = Field(..., description="Mechanistic finding or experimental conclusion")
    relevance_explanation: str = Field(default="", description="Detailed rationale of relevance to research query")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence weighting assigned to this evidence")
    doi_verification_status: str = Field(
        default="BIBLIOGRAPHIC_VERIFIED_ONLINE",
        description="Verification state: BIBLIOGRAPHIC_VERIFIED_ONLINE, BIBLIOGRAPHIC_CACHED_OFFLINE, METADATA_MISMATCH, DOI_NOT_FOUND, or UNAVAILABLE",
    )
    doi_verification_message: Optional[str] = Field(default=None, description="Diagnostic notice from Crossref or catalog validation")
    bibliographic_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Raw publisher metadata extracted from Crossref")


class ScientificResearchRequest(BaseModel):
    """Inbound request model for the `janus_scientific_research` protocol."""
    correlation_id: str = Field(..., description="Unique correlation ID tracing this investigation across uAgents")
    investigation_id: str = Field(..., description="JANUS investigation identifier (e.g., INV-E8D1415F)")
    research_question: str = Field(..., description="Scientific inquiry or problem statement to research")
    case_study_id: Optional[str] = Field(default="CS-CAT-001", description="Associated scenario identifier (e.g. CS-CAT-001, CS-OER-002)")
    topic_context: Optional[str] = Field(default=None, description="Optional domain context, reaction conditions, or catalysts")
    max_results: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of evidence claims to retrieve")


class ScientificResearchResponse(BaseModel):
    """Outbound response model for the `janus_scientific_research` protocol."""
    correlation_id: str = Field(..., description="Echoes correlation ID from request")
    investigation_id: str = Field(..., description="JANUS investigation identifier")
    status: str = Field(
        ...,
        description="RESEARCH_COMPLETED, RESEARCH_PARTIAL, RESEARCH_EMPTY, or RESEARCH_UNAVAILABLE",
    )
    agent_address: str = Field(..., description="Fetch.ai cryptographic address of the Research Agent")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of research completion")
    evidence_items: List[ResearchEvidenceItem] = Field(default_factory=list, description="Retrieved and validated evidence records")
    total_evidence_count: int = Field(default=0, description="Total number of evidence items returned")
    verified_online_count: int = Field(default=0, description="Count of items verified live via Crossref REST API")
    cached_offline_count: int = Field(default=0, description="Count of items verified via offline curated catalog")
    metadata_mismatch_count: int = Field(default=0, description="Count of items where publisher metadata differs from citation")
    not_found_count: int = Field(default=0, description="Count of items whose DOI could not be resolved")
    warnings: List[str] = Field(default_factory=list, description="Diagnostic warnings or discrepancies identified during retrieval")
    scientific_boundary_notice: str = Field(
        default=(
            "Crossref metadata validation confirms publication metadata record consistency, "
            "but does not prove or empirically confirm any mechanistic claim made within the article."
        ),
        description="Authoritative scientific and epistemic boundary notice",
    )
    execution_summary: str = Field(..., description="Human-readable summary of research findings and verification metrics")
