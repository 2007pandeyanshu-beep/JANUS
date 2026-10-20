import { AnalysisInput, AnalysisResult } from './types';

const API_BASE = '/api';

export async function checkBackendHealth(): Promise<{ status: string; engine_mode: string; version: string }> {
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
