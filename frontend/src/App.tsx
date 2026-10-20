import React, { useState, useEffect } from 'react';
import { checkBackendHealth, fetchDemoScenario, runAnalysis } from './api';
import { AnalysisInput, AnalysisResult, ExperimentScore } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; engine_mode: string; version: string } | null>(null);
  const [scenario, setScenario] = useState<AnalysisInput | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'hypotheses' | 'experiments' | 'audit'>('overview');
  const [selectedExpId, setSelectedExpId] = useState<string | null>(null);

  // Load initial backend health and demo scenario
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        setError(null);
        const healthData = await checkBackendHealth();
        setHealth(healthData);
        
        const demoData = await fetchDemoScenario();
        setScenario(demoData);
        
        // Execute initial baseline analysis
        const result = await runAnalysis(demoData);
        setAnalysisResult(result);
        if (result.ranked_experiments.length > 0) {
          setSelectedExpId(result.ranked_experiments[0].experiment_id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to connect to JANUS backend.');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const handleRunAnalysis = async () => {
    if (!scenario) return;
    try {
      setRunning(true);
      setError(null);
      const result = await runAnalysis(scenario);
      setAnalysisResult(result);
    } catch (err: any) {
      setError(err.message || 'Execution failed.');
    } finally {
      setRunning(false);
    }
  };

  const handlePriorChange = (hypothesisId: string, newPrior: number) => {
    if (!scenario) return;
    const updatedHypotheses = scenario.hypotheses.map(h => 
      h.id === hypothesisId ? { ...h, prior: Math.max(0.01, Math.min(1.0, newPrior)) } : h
    );
    setScenario({ ...scenario, hypotheses: updatedHypotheses });
  };

  const handleResetDemo = async () => {
    try {
      setLoading(true);
      setError(null);
      const demoData = await fetchDemoScenario();
      setScenario(demoData);
      const result = await runAnalysis(demoData);
      setAnalysisResult(result);
      if (result.ranked_experiments.length > 0) {
        setSelectedExpId(result.ranked_experiments[0].experiment_id);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="app-container" style={{ textAlign: 'center', paddingTop: '100px' }}>
        <div className="brand-badge" style={{ display: 'inline-block', marginBottom: '16px' }}>JANUS</div>
        <h2>Initializing Scientific Intelligence Workspace...</h2>
        <p style={{ color: 'var(--text-subtle)', marginTop: '8px' }}>Verifying Python 3.12 engine & deterministic state machine</p>
      </div>
    );
  }

  const selectedScore: ExperimentScore | undefined = analysisResult?.ranked_experiments.find(
    s => s.experiment_id === selectedExpId
  );

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-badge">JANUS</div>
          <div className="brand-title">
            <h1>Scientific Intelligence Core</h1>
            <p>Discriminative Experiment Selection for Competing Scientific Hypotheses</p>
          </div>
        </div>

        <div className="header-status">
          {health ? (
            <span className="badge badge-emerald">
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#059669' }}></span>
              API: ONLINE ({health.engine_mode})
            </span>
          ) : (
            <span className="badge badge-rose">API: OFFLINE</span>
          )}
          <span className="badge badge-amber">SYNTHETIC BENCHMARK</span>
          <span className="badge badge-indigo">V0.1.0 VERTICAL SLICE</span>
        </div>
      </header>

      {/* Global Alerts / Warnings */}
      {error && (
        <div className="alert-box alert-amber">
          <strong>System Alert:</strong> {error}
        </div>
      )}

      {/* Mission Banner */}
      <div className="mission-banner">
        <h2>Discriminative Selection Engine</h2>
        <p>
          JANUS calculates expected information gain (Shannon entropy reduction) over competing scientific hypotheses. 
          Rather than predicting generic outcomes, JANUS identifies the exact assays that maximally disambiguate rival scientific theories under budget and feasibility constraints.
        </p>
      </div>

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        <button 
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          1. Overview & Baseline
        </button>
        <button 
          className={`tab-btn ${activeTab === 'hypotheses' ? 'active' : ''}`}
          onClick={() => setActiveTab('hypotheses')}
        >
          2. Competing Hypotheses ({scenario?.hypotheses.length || 0})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'experiments' ? 'active' : ''}`}
          onClick={() => setActiveTab('experiments')}
        >
          3. Experiment Explorer & Ranking ({analysisResult?.ranked_experiments.length || 0})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          4. Evidence & Audit Trail
        </button>
      </nav>

      {/* Control Action Bar */}
      <div className="control-bar">
        <div className="scenario-indicator">
          <strong>Active Scenario:</strong>
          <span>{scenario?.scenario_name}</span>
          <span className="badge badge-amber" style={{ fontSize: '0.65rem' }}>ILLUSTRATIVE VALUES</span>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={handleResetDemo} disabled={running}>
            Reset Demo Scenario
          </button>
          <button className="btn-primary" onClick={handleRunAnalysis} disabled={running}>
            {running ? 'Computing Information Gain...' : '▶ Run Deterministic Analysis'}
          </button>
        </div>
      </div>

      {/* TAB 1: OVERVIEW & BASELINE */}
      {activeTab === 'overview' && (
        <div>
          {/* Baseline Summary Card */}
          {analysisResult?.baseline_comparison && (
            <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid #059669' }}>
              <div className="card-header">
                <div>
                  <h3 className="card-title">Evaluation Benchmark: JANUS vs Random Experiment Selection</h3>
                  <p className="card-subtitle">Rigorous baseline evaluation metric</p>
                </div>
                <span className="badge badge-emerald">
                  {analysisResult.baseline_comparison.eig_improvement_ratio}x EIG GAIN
                </span>
              </div>
              <div className="card-body">
                <p style={{ marginBottom: '12px', fontSize: '0.95rem' }}>
                  {analysisResult.baseline_comparison.summary}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', background: 'var(--bg-surface-alt)', padding: '14px', borderRadius: '6px' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Uniform Random Policy EIG</span>
                    <p className="metric-highlight" style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>
                      {analysisResult.baseline_comparison.baseline_expected_eig.toFixed(3)} bits
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Top JANUS Candidate EIG</span>
                    <p className="metric-highlight" style={{ fontSize: '1.2rem', color: 'var(--brand-primary)' }}>
                      {analysisResult.baseline_comparison.best_experiment_eig.toFixed(3)} bits
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Prior Hypothesis Entropy</span>
                    <p className="metric-highlight" style={{ fontSize: '1.2rem', color: 'var(--accent-emerald)' }}>
                      {analysisResult.ranked_experiments[0]?.prior_entropy.toFixed(3)} bits
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Core Architecture Overview */}
          <div className="cards-grid">
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: '8px' }}>Scientific Disambiguation Problem</h3>
              <p className="card-body">
                In complex biology and chemistry, multiple hypotheses often explain identical baseline phenotypes. 
                Running experiments indiscriminately wastes time and budget. 
                JANUS applies information theory to target only high-yield discriminatory experiments.
              </p>
              <div style={{ marginTop: '14px', padding: '10px 12px', background: 'var(--accent-blue-bg)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--accent-blue)' }}>
                <strong>Mathematical Foundation:</strong> Mutual Information: I(H; Y) = H(H) - E_y[H(H | y)]
              </div>
            </div>

            <div className="card">
              <h3 className="card-title" style={{ marginBottom: '8px' }}>Validation & Integrity Principles</h3>
              <p className="card-body">
                • <strong>Zero Hallucinated Science:</strong> All current values are explicitly tagged as synthetic fixtures.<br/>
                • <strong>Deterministic Ranking:</strong> Exact mathematical computation; no LLM decides the top experiment.<br/>
                • <strong>Constraint Aware:</strong> Hard rejection of infeasible assays and cost penalization.
              </p>
              <div style={{ marginTop: '14px', padding: '10px 12px', background: 'var(--accent-emerald-bg)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--accent-emerald)' }}>
                <strong>Status:</strong> {analysisResult?.validation_status}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: COMPETING HYPOTHESES */}
      {activeTab === 'hypotheses' && (
        <div>
          <div className="alert-box alert-blue">
            <span>
              <strong>Hypothesis Sensitivity:</strong> You can adjust prior probabilities below and re-run the analysis 
              to verify how the deterministic engine shifts experiment priorities when scientific beliefs change.
            </span>
          </div>

          <div className="cards-grid">
            {scenario?.hypotheses.map(h => {
              const normalizedP = analysisResult?.normalized_priors[h.id] ?? h.prior;
              return (
                <div key={h.id} className="card">
                  <div className="card-header">
                    <div>
                      <span className="badge badge-indigo" style={{ marginBottom: '6px' }}>{h.id}</span>
                      <h3 className="card-title">{h.name}</h3>
                    </div>
                    <span className="badge badge-emerald">
                      P(H) = {(normalizedP * 100).toFixed(1)}%
                    </span>
                  </div>

                  <p className="card-body" style={{ marginBottom: '14px' }}>
                    {h.description}
                  </p>

                  <div style={{ marginBottom: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-subtle)' }}>Prior Probability Input:</span>
                      <span className="mono">{h.prior.toFixed(2)}</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.05" 
                      max="0.95" 
                      step="0.05" 
                      value={h.prior}
                      onChange={(e) => handlePriorChange(h.id, parseFloat(e.target.value))}
                      style={{ width: '100%', cursor: 'pointer' }}
                    />
                  </div>

                  <div>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                      Core Assumptions:
                    </span>
                    <ul className="assumptions-list">
                      {h.assumptions.map((asm, i) => (
                        <li key={i}>{asm}</li>
                      ))}
                    </ul>
                  </div>

                  <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                    <strong>Evidence citations:</strong> {h.evidence_ids.join(', ') || 'None attached'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 3: EXPERIMENT EXPLORER & RANKING */}
      {activeTab === 'experiments' && (
        <div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '60px' }}>Rank</th>
                  <th>Candidate Experiment</th>
                  <th>EIG (Bits)</th>
                  <th>Disambiguation</th>
                  <th>Feasibility</th>
                  <th>Cost</th>
                  <th>Utility Score</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {analysisResult?.ranked_experiments.map(score => {
                  const isSelected = score.experiment_id === selectedExpId;
                  return (
                    <tr 
                      key={score.experiment_id}
                      style={{ backgroundColor: isSelected ? '#f8fafc' : undefined }}
                    >
                      <td>
                        <span className={`rank-pill rank-${score.rank}`}>
                          {score.rank}
                        </span>
                      </td>
                      <td>
                        <strong style={{ display: 'block', color: 'var(--text-main)' }}>{score.experiment_name}</strong>
                        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>{score.experiment_id}</span>
                      </td>
                      <td>
                        <span className="metric-highlight">
                          {score.expected_information_gain.toFixed(4)}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: 60, height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
                            <div 
                              style={{ 
                                width: `${score.normalized_information_gain * 100}%`, 
                                height: '100%', 
                                background: score.is_informative ? '#4338ca' : '#94a3b8' 
                              }}
                            />
                          </div>
                          <span style={{ fontSize: '0.75rem' }} className="mono">
                            {(score.normalized_information_gain * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="badge badge-blue">
                          {(score.feasibility * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td>
                        <span className="mono" style={{ fontSize: '0.85rem' }}>{score.cost.toFixed(1)}</span>
                      </td>
                      <td>
                        <span className="metric-highlight" style={{ color: score.composite_utility_score > 0 ? '#059669' : '#e11d48' }}>
                          {score.composite_utility_score.toFixed(4)}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn-secondary" 
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => setSelectedExpId(score.experiment_id)}
                        >
                          {isSelected ? 'Viewing' : 'Inspect'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Detailed Inspector for Selected Experiment */}
          {selectedScore && (
            <div className="card" style={{ borderLeft: '4px solid var(--brand-primary)' }}>
              <div className="card-header">
                <div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                    <span className="badge badge-indigo">RANK #{selectedScore.rank}</span>
                    <span className="mono" style={{ color: 'var(--text-subtle)', fontSize: '0.8rem' }}>{selectedScore.experiment_id}</span>
                  </div>
                  <h3 className="card-title" style={{ fontSize: '1.15rem' }}>{selectedScore.experiment_name}</h3>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', display: 'block' }}>Expected Info Gain</span>
                  <span className="metric-highlight" style={{ fontSize: '1.25rem' }}>{selectedScore.expected_information_gain.toFixed(4)} bits</span>
                </div>
              </div>

              <div className="card-body">
                <p style={{ marginBottom: '14px', background: 'var(--bg-surface-alt)', padding: '12px', borderRadius: '6px' }}>
                  <strong>Deterministic Rationale:</strong> {selectedScore.explanation}
                </p>

                {/* Bayesian Posterior Update Matrix */}
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Bayesian Posterior Distribution Matrix: P(Hypothesis | Observed Outcome)
                </h4>
                <div className="table-container" style={{ marginBottom: '12px' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Observable Outcome (y)</th>
                        <th>Marginal P(y)</th>
                        {scenario?.hypotheses.map(h => (
                          <th key={h.id}>P({h.id} | y)</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(selectedScore.posterior_matrix).map(([outcome, posteriors]) => (
                        <tr key={outcome}>
                          <td><strong>{outcome}</strong></td>
                          <td>
                            <span className="mono">{selectedScore.outcome_marginal_probabilities[outcome]?.toFixed(3) ?? '0.000'}</span>
                          </td>
                          {scenario?.hypotheses.map(h => {
                            const p = posteriors[h.id] ?? 0.0;
                            const isHigh = p > 0.8;
                            return (
                              <td key={h.id}>
                                <span className={`mono ${isHigh ? 'metric-highlight' : ''}`} style={{ fontWeight: isHigh ? 700 : 400 }}>
                                  {(p * 100).toFixed(1)}%
                                </span>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: EVIDENCE & AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div>
          {/* Data Provenance Table */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <h3 className="card-title" style={{ marginBottom: '10px' }}>Scientific Data Provenance & Trust Matrix</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Entity</th>
                    <th>Source Identifier</th>
                    <th>Classification</th>
                    <th>Confidence</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {scenario?.evidence.map(ev => (
                    <tr key={ev.id}>
                      <td><strong>{ev.title}</strong></td>
                      <td className="mono" style={{ fontSize: '0.75rem' }}>{ev.source}</td>
                      <td>
                        <span className="badge badge-amber">{ev.provenance}</span>
                      </td>
                      <td className="mono">{(ev.confidence * 100).toFixed(0)}%</td>
                      <td>
                        <span className="badge badge-emerald">Active Benchmark</span>
                      </td>
                    </tr>
                  ))}
                  <tr>
                    <td><strong>Hypothesis Priors</strong></td>
                    <td>User Interactive / Scenario Config</td>
                    <td><span className="badge badge-blue">User-Supplied</span></td>
                    <td className="mono">100%</td>
                    <td><span className="badge badge-emerald">Normalized</span></td>
                  </tr>
                  <tr>
                    <td><strong>Experiment Ranking Engine</strong></td>
                    <td>Deterministic Shannon Entropy Engine</td>
                    <td><span className="badge badge-indigo">Algorithmic Math</span></td>
                    <td className="mono">Deterministic</td>
                    <td><span className="badge badge-emerald">Verified</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Engine Execution Audit Trail */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Reproducible Engine Execution Audit Log</h3>
                <p className="card-subtitle">Real-time trace generated by Python ScientificEngine</p>
              </div>
              <span className="badge badge-indigo mono">
                RUN: {analysisResult?.analysis_id}
              </span>
            </div>
            <div className="log-stream">
              {analysisResult?.audit_trail.map((line, idx) => (
                <div key={idx} className="log-item">
                  <span className="log-prefix">[{idx + 1}]</span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
