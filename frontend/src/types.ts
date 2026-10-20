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
