"""Data models and schemas for JANUS Phase 9: Agentic Value Evaluation

Defines structured schemas for:
- 7 practical scientific quality metrics
- Per-pipeline comparison records
- Auditable execution trace items
- Evaluation reports
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class CitationMetric(BaseModel):
    """Measures citation validity and claim-to-source support, separating curated vs LLM citations."""
    # Curated Literature Records
    curated_citations_count: int = 0
    curated_verified_dois_count: int = 0
    curated_validity_rate: float = 1.0  # curated_verified / curated_total
    
    # LLM-Generated Literature Records (Audited)
    llm_generated_citations_count: int = 0
    llm_verified_citations_count: int = 0
    llm_fabricated_citations_count: int = 0
    llm_citation_audit_notes: str = "No external unverified literature citations were introduced by the LLM."

    # Backwards-compatible aggregate fields
    total_citations: int = 0
    verified_doi_count: int = 0
    citation_validity_rate: float = 1.0
    fabricated_citation_count: int = 0
    sources_summary: List[str] = Field(default_factory=list)


class HypothesisDistinctionMetric(BaseModel):
    """Measures hypothesis mathematical consistency and mechanistic distinction."""
    hypothesis_count: int
    prior_entropy_bits: float
    simplex_sum: float
    simplex_error: float  # abs(sum - 1.0)
    is_simplex_valid: bool
    pairwise_discriminability: float  # Mean total variation distance between likelihood distributions


class ToolExecutionMetric(BaseModel):
    """Measures computational tool-call validity and execution reliability."""
    total_tools_invoked: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    execution_success_rate: float = 1.0
    total_latency_ms: float = 0.0
    tools_used: List[str] = Field(default_factory=list)


class RecommendationQualityMetric(BaseModel):
    """Measures experiment recommendation quality against ground-truth optimal."""
    recommended_experiment_id: str
    ground_truth_optimal_id: str
    matches_optimal_pick: bool
    recommended_eig_bits: float
    optimal_eig_bits: float
    eig_regret_bits: float  # optimal - recommended (>= 0.0)
    composite_utility: float
    utility_rank: int
    eig_rank: int


class FilteringWasteMetric(BaseModel):
    """Measures filtering of uninformative controls and unquantified proposals."""
    uninformative_controls_detected: int = 0
    unquantified_proposals_flagged: int = 0
    critic_issue_count: int = 0
    waste_avoidance_success: bool = True
    flagged_entities: List[str] = Field(default_factory=list)


class BayesianUpdateAccuracyMetric(BaseModel):
    """Measures numerical correctness of dynamic belief updates against Bayes rule."""
    tested_experiment_id: str
    tested_outcome: str
    max_absolute_posterior_error: float = 0.0
    is_exact_match: bool = True


class LiveExecutionTrace(BaseModel):
    """Auditable trace of live model invocation, tool results, and component attribution."""
    model_name: str = "models/gemini-3-flash-preview"
    raw_model_response: str = ""
    executed_tools: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    critic_output: List[Dict[str, Any]] = Field(default_factory=list)
    final_recommended_experiment: str = ""
    decision_component_attribution: Dict[str, str] = Field(default_factory=dict)


class PipelineComparisonRecord(BaseModel):
    """Row comparing one execution pipeline on a benchmark scenario."""
    workflow_name: str  # 'non_agentic_janus', 'deterministic_multi_agent', 'live_llm_agent', 'uniform_random', 'cheapest_heuristic'
    case_id: str  # 'CS-CAT-001', 'CS-OER-002', 'SYN-001'
    execution_latency_ms: float
    recommended_experiment: Optional[str] = None
    eig_bits: float = 0.0
    composite_utility: float = 0.0
    cost: float = 0.0
    feasibility: float = 1.0
    eig_regret_bits: float = 0.0  # max(0.0, optimal_eig - eig_bits)
    citation_validity_pct: float = 100.0
    simplex_error: float = 0.0
    critic_challenges_count: int = 0
    execution_status: str = "SUCCESS"  # 'SUCCESS', 'BLOCKED_MISSING_CREDENTIALS', 'FAILED'
    live_llm_called: bool = False
    decision_attribution: str = ""
    notes: str = ""


class CaseEvaluationSummary(BaseModel):
    """Complete evaluation report for a single case study."""
    case_id: str
    case_name: str
    ground_truth_optimal_id: str
    ground_truth_optimal_eig: float
    ground_truth_optimal_utility: float
    pipelines: List[PipelineComparisonRecord]
    citation_metric: CitationMetric
    hypothesis_metric: HypothesisDistinctionMetric
    tool_metric: ToolExecutionMetric
    recommendation_metric: RecommendationQualityMetric
    filtering_metric: FilteringWasteMetric
    bayesian_update_metric: Optional[BayesianUpdateAccuracyMetric] = None
    live_execution_trace: Optional[LiveExecutionTrace] = None


class AgenticValueEvaluationReport(BaseModel):
    """Consolidated multi-case report assessing agentic value."""
    report_id: str
    timestamp: str
    evaluated_cases: List[CaseEvaluationSummary]
    live_llm_provider_tested: str
    live_llm_status: str
    value_synthesis: str
