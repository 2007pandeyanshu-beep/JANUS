// TypeScript definitions mirroring backend Pydantic schemas

export interface Evidence {
  id: string;
  title: string;
  source: string;
  provenance: string;
  summary: string;
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
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  possible_outcomes: string[];
  predictions: PredictedOutcome[];
  cost: number;
  feasibility: number;
  assumptions: string[];
  is_feasible: boolean;
}

export interface ExperimentScore {
  experiment_id: string;
  experiment_name: string;
  rank: number;
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
  is_synthetic: boolean;
  hypotheses: Hypothesis[];
  normalized_priors: Record<string, number>;
  ranked_experiments: ExperimentScore[];
  baseline_comparison: BaselineComparison;
  audit_trail: string[];
  warnings: string[];
  validation_status: string;
}
