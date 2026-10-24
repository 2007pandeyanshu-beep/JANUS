// TypeScript definitions mirroring backend Pydantic schemas

export interface Evidence {
  id: string;
  title: string;
  source: string;
  source_doi?: string;
  source_location?: string;
  exact_source_quote?: string;
  claim_status?: string;
  ambiguity_notes?: string;
  provenance: string;
  summary: string;
  quantitative_value?: {
    metric: string;
    value: number | string;
    range?: [number, number];
    unit: string;
  } | null;
  supports_hypotheses?: string[];
  refutes_hypotheses?: string[];
  confidence: number;
}

export interface Hypothesis {
  id: string;
  name: string;
  description: string;
  prior: number;
  assumptions: string[];
  evidence_ids: string[];
  status: string;
}

export interface PredictedOutcome {
  outcome_label: string;
  hypothesis_id: string;
  probability: number;
  uncertainty?: number;
  basis?: string;
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  quantification_status?: 'QUANTIFIED_BAYESIAN' | 'UNQUANTIFIED_NEEDS_MEASUREMENT';
  possible_outcomes: string[];
  predictions: PredictedOutcome[];
  cost: number;
  feasibility: number;
  assumptions: string[];
  is_feasible: boolean;
  source_evidence_ids?: string[];
}

export interface ExperimentScore {
  experiment_id: string;
  experiment_name: string;
  rank?: number | null;
  utility_rank?: number | null;
  eig_rank?: number | null;
  quantification_status?: 'QUANTIFIED_BAYESIAN' | 'UNQUANTIFIED_NEEDS_MEASUREMENT';
  prior_entropy: number;
  expected_posterior_entropy: number;
  expected_information_gain: number;
  normalized_information_gain: number;
  feasibility: number;
  cost: number;
  composite_utility_score: number;
  outcome_marginal_probabilities: Record<string, number>;
  posterior_matrix: Record<string, Record<string, number>>;
  explanation: string;
  missing_inputs_explanation?: string | null;
  is_informative: boolean;
}

export interface BaselineComparison {
  baseline_type: string;
  baseline_expected_eig: number;
  best_experiment_eig: number;
  eig_improvement_ratio: number;
  summary: string;
}

export interface AnalysisInput {
  scenario_name: string;
  scenario_type?: 'synthetic_benchmark' | 'published_case_study';
  case_study_id?: string | null;
  hypotheses: Hypothesis[];
  experiments: Experiment[];
  evidence: Evidence[];
  is_synthetic: boolean;
  cost_weight: number;
}

export interface AnalysisResult {
  analysis_id: string;
  timestamp: string;
  scenario_name: string;
  scenario_type?: 'synthetic_benchmark' | 'published_case_study';
  case_study_id?: string | null;
  is_synthetic: boolean;
  hypotheses: Hypothesis[];
  normalized_priors: Record<string, number>;
  ranked_experiments: ExperimentScore[];
  unquantified_experiments: ExperimentScore[];
  baseline_comparison: BaselineComparison;
  audit_trail: string[];
  warnings: string[];
  validation_status: string;
}

export interface BEDCampaignStep {
  step_number: number;
  selected_experiment_id: string;
  selected_experiment_name: string;
  execution_status: 'SUCCESS' | 'EXECUTION_FAILURE';
  observed_outcome?: string | null;
  simulated_is_successful: boolean;
  prior_distribution: Record<string, number>;
  posterior_distribution: Record<string, number>;
  predicted_eig: number;
  realized_information_gain: number;
  step_cost: number;
  cumulative_cost: number;
  remaining_candidate_count: number;
  remaining_candidate_scores: ExperimentScore[];
  selection_rationale: string;
}

export interface BEDCampaignResult {
  campaign_id: string;
  timestamp: string;
  scenario_name: string;
  policy_name: string;
  hidden_hypothesis_id: string;
  hidden_hypothesis_name: string;
  seed: number;
  budget: number;
  max_steps: number;
  confidence_threshold: number;
  initial_priors: Record<string, number>;
  final_posterior: Record<string, number>;
  final_confidence_in_hidden_hypothesis: number;
  steps: BEDCampaignStep[];
  total_steps: number;
  total_cost: number;
  total_realized_information_gain: number;
  termination_reason: string;
  target_confidence_achieved: boolean;
  execution_failure_count: number;
  uninformative_selection_count: number;
  warnings: string[];
}

export interface BEDCampaignInput {
  scenario_id?: string;
  policy: string;
  hidden_hypothesis_id?: string | null;
  seed: number;
  budget: number;
  max_steps: number;
  confidence_threshold: number;
  cost_weight?: number;
}

export interface PolicyCampaignSummary {
  policy_key: string;
  policy_name: string;
  final_confidence_h_star: number;
  total_steps: number;
  total_cost: number;
  total_realized_ig_bits: number;
  execution_failures: number;
  zero_eig_selections: number;
  target_confidence_achieved: boolean;
  termination_reason: string;
  runtime_ms: number;
  regret_vs_oracle_utility: number;
  regret_vs_offline_optimal?: number;
  signed_delta_vs_privileged?: number;
}

export interface BEDPolicyComparisonReport {
  comparison_id: string;
  timestamp: string;
  scenario_name: string;
  hidden_hypothesis_id: string;
  hidden_hypothesis_name: string;
  seed: number;
  budget: number;
  confidence_threshold: number;
  offline_optimal_ig_bits?: number;
  offline_optimal_subset?: string[];
  offline_optimal_cost?: number;
  policy_summaries: PolicyCampaignSummary[];
  summary_verdict: string;
}

// ==============================================================================
// Multi-Agent Scientific Investigation Schemas (Phase 8)
// ==============================================================================

export type AgentRole = 'RESEARCH_AGENT' | 'HYPOTHESIS_AGENT' | 'SCIENTIFIC_TOOL_AGENT' | 'EXPERIMENT_STRATEGY_AGENT' | 'CRITIC_AGENT';

export type CriticSeverity = 'VERIFIED' | 'NOTE' | 'WARNING' | 'HIGH_SEVERITY_CHALLENGE' | 'UNRESOLVED_DISAGREEMENT';

export interface CriticItem {
  id: string;
  agent_targeted: AgentRole;
  target_claim_or_object: string;
  severity: CriticSeverity;
  critique: string;
  evidence_basis: string;
  recommendation: string;
  is_resolved: boolean;
}

export interface ToolExecutionRecord {
  tool_name: string;
  invoked_by: AgentRole;
  input_arguments: Record<string, any>;
  output_data: Record<string, any>;
  execution_time_ms: number;
  status: string;
  provenance: string;
}

export interface AgentLogEntry {
  timestamp: string;
  role: AgentRole;
  stage: string;
  thought: string;
  action_taken: string;
  tool_name?: string | null;
  output_summary?: string | null;
}

export interface InvestigationInput {
  question: string;
  mode: 'deterministic_offline_demo' | 'live_agent_loop';
  case_study_id?: string | null;
  api_key?: string | null;
}

export interface AgentInvestigationReport {
  investigation_id: string;
  question: string;
  mode: string;
  status: string;
  case_study_id?: string | null;
  retrieved_evidence: Evidence[];
  hypotheses: Hypothesis[];
  candidate_experiments: Experiment[];
  analysis_result?: AnalysisResult | null;
  tool_executions: ToolExecutionRecord[];
  critic_review: CriticItem[];
  agent_logs: AgentLogEntry[];
  synthesis_summary: string;
  human_approval_required?: string | null;
  initial_priors?: Record<string, number>;
  executed_observations?: Array<{
    experiment_id: string;
    experiment_name?: string;
    observed_outcome: string;
    cost?: string;
    timestamp?: string;
    status: string;
  }>;
  retired_experiments?: string[];
  remaining_budget?: number;
}
