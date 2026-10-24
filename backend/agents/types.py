"""Type definitions and schemas for JANUS Multi-Agent Scientific Investigation (Phase 8)"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.scientific import Hypothesis, Experiment, Evidence, AnalysisResult
from app.schemas.review import ScientificReviewReport


class AgentRole(str, Enum):
    RESEARCH = "RESEARCH_AGENT"
    HYPOTHESIS = "HYPOTHESIS_AGENT"
    SCIENTIFIC_TOOL = "SCIENTIFIC_TOOL_AGENT"
    EXPERIMENT_STRATEGY = "EXPERIMENT_STRATEGY_AGENT"
    CRITIC = "CRITIC_AGENT"


class ProvenanceClassification(str, Enum):
    EMPIRICAL_LITERATURE = "EMPIRICAL_LITERATURE"
    THEORETICAL_COMPUTATION = "THEORETICAL_COMPUTATION"
    USER_SPECIFIED_ASSUMPTION = "USER_SPECIFIED_ASSUMPTION"
    CALCULATED_BAYESIAN = "CALCULATED_BAYESIAN"
    SIMULATED_PREVIEW = "SIMULATED_PREVIEW"
    EXTERNAL_RETRIEVAL = "EXTERNAL_RETRIEVAL"


class CriticSeverity(str, Enum):
    VERIFIED = "VERIFIED"
    NOTE = "NOTE"
    WARNING = "WARNING"
    HIGH_SEVERITY_CHALLENGE = "HIGH_SEVERITY_CHALLENGE"
    UNRESOLVED_DISAGREEMENT = "UNRESOLVED_DISAGREEMENT"


class CriticItem(BaseModel):
    id: str
    agent_targeted: AgentRole
    target_claim_or_object: str
    severity: CriticSeverity
    critique: str
    evidence_basis: str
    recommendation: str
    is_resolved: bool = False


class ToolExecutionRecord(BaseModel):
    tool_name: str
    invoked_by: AgentRole
    input_arguments: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time_ms: float
    status: str = "SUCCESS"  # "SUCCESS", "ERROR", "BLOCKED_AWAITING_APPROVAL"
    provenance: ProvenanceClassification


class AgentLogEntry(BaseModel):
    timestamp: str
    role: AgentRole
    stage: str
    thought: str
    action_taken: str
    tool_name: Optional[str] = None
    output_summary: Optional[str] = None




class ObservationProvenance(str, Enum):
    USER_SUPPLIED = "user_supplied"
    SIMULATED_DEMONSTRATION = "simulated_demonstration"
    EMPIRICAL_MEASUREMENT = "empirical_measurement"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class ObservationRecord(BaseModel):
    observation_id: str
    experiment_id: str
    experiment_name: str
    observed_outcome: str
    provenance: str = "user_supplied"
    cost: float = 0.0
    timestamp: str
    status: str = "APPLIED"
    idempotency_key: Optional[str] = None
    prior_snapshot: Dict[str, float] = Field(default_factory=dict)
    posterior_snapshot: Dict[str, float] = Field(default_factory=dict)
    marginal_probability: float = 1.0


class InvestigationEvent(BaseModel):
    event_id: str
    investigation_id: str
    event_type: str
    version_after: int
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str

class InvestigationInput(BaseModel):
    question: str = Field(..., description="The scientific question or mechanistic ambiguity to investigate")
    mode: str = Field(default="deterministic_offline_demo", description="'deterministic_offline_demo' or 'live_agent_loop'")
    case_study_id: Optional[str] = Field(default="CS-CAT-001", description="'CS-CAT-001', 'CS-OER-002', or None")
    api_key: Optional[str] = Field(default=None, description="Optional LLM API key if running in live mode")


class AgentInvestigationReport(BaseModel):
    investigation_id: str
    question: str
    mode: str
    status: str
    case_study_id: Optional[str] = None
    retrieved_evidence: List[Evidence] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    candidate_experiments: List[Experiment] = Field(default_factory=list)
    analysis_result: Optional[AnalysisResult] = None
    tool_executions: List[ToolExecutionRecord] = Field(default_factory=list)
    critic_review: List[CriticItem] = Field(default_factory=list)
    review_report: Optional[ScientificReviewReport] = None
    agent_logs: List[AgentLogEntry] = Field(default_factory=list)
    synthesis_summary: str = ""
    human_approval_required: Optional[str] = None
    initial_priors: Dict[str, float] = Field(default_factory=dict)
    executed_observations: List[Dict[str, str]] = Field(default_factory=list)
    retired_experiments: List[str] = Field(default_factory=list)
    remaining_budget: float = 10.0
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    observation_records: List[ObservationRecord] = Field(default_factory=list)
    events: List[InvestigationEvent] = Field(default_factory=list)
    idempotency_keys: List[str] = Field(default_factory=list)
