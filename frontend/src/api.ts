import {
  AnalysisInput,
  AnalysisResult,
  Evidence,
  Experiment,
  BEDCampaignInput,
  BEDCampaignResult,
  BEDPolicyComparisonReport,
} from './types';

const API_BASE = '/api';

export async function checkBackendHealth(): Promise<{
  status: string;
  engine_mode: string;
  version: string;
  active_case_study?: string;
}> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Backend health check failed (${res.status} ${res.statusText})`);
  }
  return res.json();
}

export async function fetchDemoScenario(): Promise<AnalysisInput> {
  const res = await fetch(`${API_BASE}/scenarios/demo`);
  if (!res.ok) {
    throw new Error(`Failed to load demo scenario (${res.status} ${res.statusText})`);
  }
  return res.json();
}

export async function fetchCaseStudyScenario(): Promise<AnalysisInput> {
  const res = await fetch(`${API_BASE}/scenarios/case-study`);
  if (!res.ok) {
    throw new Error(`Failed to load published case study (${res.status} ${res.statusText})`);
  }
  return res.json();
}

export async function fetchEvidenceLedger(): Promise<Evidence[]> {
  const res = await fetch(`${API_BASE}/evidence/ledger`);
  if (!res.ok) {
    throw new Error(`Failed to load evidence ledger (${res.status} ${res.statusText})`);
  }
  return res.json();
}

export async function fetchCandidateExperiments(): Promise<Experiment[]> {
  const res = await fetch(`${API_BASE}/experiments/candidates`);
  if (!res.ok) {
    throw new Error(`Failed to load candidate experiments (${res.status} ${res.statusText})`);
  }
  return res.json();
}

export async function runAnalysis(payload: AnalysisInput): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analysis/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Analysis execution failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function runSequentialCampaign(input: BEDCampaignInput): Promise<BEDCampaignResult> {
  const res = await fetch(`${API_BASE}/sequential/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Sequential campaign failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function compareSequentialPolicies(
  scenarioId: string = 'CS-CAT-001',
  hiddenHypothesisId: string = 'H1',
  seed: number = 42,
  budget: number = 10.0,
  maxSteps: number = 8,
  confidenceThreshold: number = 0.95
): Promise<BEDPolicyComparisonReport> {
  const url = `${API_BASE}/sequential/compare?scenario_id=${encodeURIComponent(scenarioId)}&hidden_hypothesis_id=${encodeURIComponent(hiddenHypothesisId)}&seed=${seed}&budget=${budget}&max_steps=${maxSteps}&confidence_threshold=${confidenceThreshold}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Policy comparison failed with HTTP ${res.status}`);
  }
  return res.json();
}
