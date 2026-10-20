import React, { useState, useEffect } from 'react';
import {
  checkBackendHealth,
  fetchDemoScenario,
  fetchCaseStudyScenario,
  runAnalysis,
} from './api';
import { AnalysisInput, AnalysisResult, ExperimentScore } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<{
    status: string;
    engine_mode: string;
    version: string;
    active_case_study?: string;
  } | null>(null);
  
  const [currentScenario, setCurrentScenario] = useState<AnalysisInput | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'hypotheses' | 'experiments' | 'evidence' | 'audit'>('overview');
  const [selectedExpId, setSelectedExpId] = useState<string | null>(null);
  const [selectedMode, setSelectedMode] = useState<'case_study' | 'synthetic'>('case_study');

  // Load published case study as default primary scientific scenario
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        setError(null);
        const healthData = await checkBackendHealth();
        setHealth(healthData);
        
        // Default to real published case study on Pt/CeO2
        const caseStudyData = await fetchCaseStudyScenario();
        setCurrentScenario(caseStudyData);
        setSelectedMode('case_study');
        
        const result = await runAnalysis(caseStudyData);
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

  const handleSwitchMode = async (mode: 'case_study' | 'synthetic') => {
    try {
      setRunning(true);
      setError(null);
      setSelectedMode(mode);
      
      const scenarioData = mode === 'case_study' 
        ? await fetchCaseStudyScenario()
        : await fetchDemoScenario();
        
      setCurrentScenario(scenarioData);
      const result = await runAnalysis(scenarioData);
      setAnalysisResult(result);
      if (result.ranked_experiments.length > 0) {
        setSelectedExpId(result.ranked_experiments[0].experiment_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to switch scenario mode.');
    } finally {
      setRunning(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!currentScenario) return;
    try {
      setRunning(true);
      setError(null);
      const result = await runAnalysis(currentScenario);
      setAnalysisResult(result);
    } catch (err: any) {
      setError(err.message || 'Execution failed.');
    } finally {
      setRunning(false);
    }
  };

  const handlePriorChange = (hypothesisId: string, newPrior: number) => {
    if (!currentScenario) return;
    const updatedHypotheses = currentScenario.hypotheses.map(h => 
      h.id === hypothesisId ? { ...h, prior: Math.max(0.01, Math.min(1.0, newPrior)) } : h
    );
    setCurrentScenario({ ...currentScenario, hypotheses: updatedHypotheses });
  };

  if (loading) {
    return (
      <div className="app-container" style={{ textAlign: 'center', paddingTop: '100px' }}>
        <div className="brand-badge" style={{ display: 'inline-block', marginBottom: '16px' }}>JANUS</div>
        <h2>Loading Scientific Intelligence Core...</h2>
        <p style={{ color: 'var(--text-subtle)', marginTop: '8px' }}>
          Ingesting published heterogeneous catalysis case study & verifying evidence ledger
        </p>
      </div>
    );
  }

  const selectedScore: ExperimentScore | undefined = 
    analysisResult?.ranked_experiments.find(s => s.experiment_id === selectedExpId) ||
    analysisResult?.unquantified_experiments.find(s => s.experiment_id === selectedExpId);

  const isRealCaseStudy = currentScenario?.is_synthetic === false;

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

          {isRealCaseStudy ? (
            <span className="badge badge-emerald">PUBLISHED PRIMARY EVIDENCE (CS-CAT-001)</span>
          ) : (
            <span className="badge badge-amber">SYNTHETIC BENCHMARK</span>
          )}

          <span className="badge badge-indigo">PHASE 2 CASE STUDY</span>
        </div>
      </header>

      {/* Global Alerts / Warnings */}
      {error && (
        <div className="alert-box alert-amber">
          <strong>System Alert:</strong> {error}
        </div>
      )}

      {/* Scenario Mode Switcher Bar */}
      <div className="scenario-switcher-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <strong style={{ fontSize: '0.875rem' }}>Select Scenario Mode:</strong>
          <div className="switcher-pills">
            <button
              className={`switcher-btn ${selectedMode === 'case_study' ? 'active real' : ''}`}
              onClick={() => handleSwitchMode('case_study')}
              disabled={running}
            >
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#059669' }}></span>
              Published Case Study: Pt/CeO2 WGS Catalysis
            </button>
            <button
              className={`switcher-btn ${selectedMode === 'synthetic' ? 'active demo' : ''}`}
              onClick={() => handleSwitchMode('synthetic')}
              disabled={running}
            >
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#d97706' }}></span>
              Synthetic Benchmark: Kinase Signaling Pathway
            </button>
          </div>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
          {isRealCaseStudy ? (
            <span>Peer-reviewed empirical data from <em>J. Catal.</em> & <em>Science</em></span>
          ) : (
            <span>Illustrative benchmark fixture for algorithmic testing</span>
          )}
        </div>
      </div>

      {/* Mission / Context Banner */}
      <div className={`mission-banner ${isRealCaseStudy ? 'case-study-mode' : ''}`}>
        <h2>
          {isRealCaseStudy
            ? 'Heterogeneous Catalysis Case Study: Pt/CeO2 Water-Gas Shift Mechanism'
            : 'Discriminative Selection Engine (Synthetic Demonstration)'}
        </h2>
        <p>
          {isRealCaseStudy
            ? 'Disambiguating whether low-temperature WGS on Pt/CeO2 proceeds via a Redox (Mars-van Krevelen) mechanism, an Associative Formate pathway, or an Associative Carboxyl pathway with formates as spectators. JANUS computes Expected Information Gain (EIG in bits) using published isotopic kinetic data and operando spectroscopy detection limits.'
            : 'JANUS calculates Shannon entropy reduction to identify the exact assays that maximally distinguish competing scientific hypotheses under budget and feasibility constraints.'}
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
          2. Competing Hypotheses ({currentScenario?.hypotheses.length || 0})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'experiments' ? 'active' : ''}`}
          onClick={() => setActiveTab('experiments')}
        >
          3. Experiment Explorer & Ranking ({analysisResult?.ranked_experiments.length || 0})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'evidence' ? 'active' : ''}`}
          onClick={() => setActiveTab('evidence')}
        >
          4. Evidence Ledger & Claims ({currentScenario?.evidence.length || 0})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          5. Mathematical Audit Trail
        </button>
      </nav>

      {/* Control Action Bar */}
      <div className="control-bar">
        <div className="scenario-indicator">
          <strong>Active Scenario:</strong>
          <span>{currentScenario?.scenario_name}</span>
          {isRealCaseStudy ? (
            <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>EVIDENCE-GROUNDED</span>
          ) : (
            <span className="badge badge-amber" style={{ fontSize: '0.65rem' }}>ILLUSTRATIVE VALUES</span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            className={`btn-primary ${isRealCaseStudy ? 'emerald' : ''}`} 
            onClick={handleRunAnalysis} 
            disabled={running}
          >
            {running ? 'Computing Information Gain...' : '▶ Recompute Deterministic Ranking'}
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
                  <p className="card-subtitle">Quantified on the candidate experiment set</p>
                </div>
                <span className="badge badge-emerald">
                  {analysisResult.baseline_comparison.eig_improvement_ratio}x EIG MULTIPLIER
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
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Top Candidate EIG</span>
                    <p className="metric-highlight" style={{ fontSize: '1.2rem', color: 'var(--brand-primary)' }}>
                      {analysisResult.baseline_comparison.best_experiment_eig.toFixed(3)} bits
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Prior Hypothesis Entropy</span>
                    <p className="metric-highlight green" style={{ fontSize: '1.2rem' }}>
                      {analysisResult.ranked_experiments[0]?.prior_entropy.toFixed(3)} bits
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Core Architecture Cards */}
          <div className="cards-grid">
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: '8px' }}>Scientific Disambiguation Problem</h3>
              <p className="card-body">
                {isRealCaseStudy ? (
                  <span>
                    In the low-temperature water-gas shift reaction, multiple plausible reaction pathways explain steady-state CO2 generation. 
                    Running standard kinetic rate measurements cannot differentiate whether formates are active intermediates or inert spectators. 
                    JANUS selects transient isotopic and operando spectroscopic experiments that target the exact points of theoretical divergence.
                  </span>
                ) : (
                  <span>
                    In complex biology and chemistry, multiple hypotheses often explain identical baseline phenotypes. 
                    Running experiments indiscriminately wastes time and budget. 
                    JANUS applies information theory to target only high-yield discriminatory experiments.
                  </span>
                )}
              </p>
              <div style={{ marginTop: '14px', padding: '10px 12px', background: 'var(--accent-blue-bg)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--accent-blue)' }}>
                <strong>Mathematical Foundation:</strong> Mutual Information: I(H; Y) = H(H) - E_y[H(H | y)]
              </div>
            </div>

            <div className="card">
              <h3 className="card-title" style={{ marginBottom: '8px' }}>Evidence & Provenance Integrity</h3>
              <p className="card-body">
                • <strong>No Fabricated Probabilities:</strong> Experiments lacking published quantitative data (e.g., sub-second stopped-flow carboxyl detection) are isolated as unquantified proposals.<br/>
                • <strong>Full Provenance Ledger:</strong> Every claim links directly to its DOI and specific page/figure in primary literature.<br/>
                • <strong>Negative Control Verification:</strong> Homogeneous gas-phase blank control confirms 0.0 bits EIG when predictions are identical.
              </p>
              <div style={{ marginTop: '14px', padding: '10px 12px', background: 'var(--accent-emerald-bg)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--accent-emerald)' }}>
                <strong>Validation Status:</strong> {analysisResult?.validation_status}
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
              <strong>Hypothesis Sensitivity:</strong> Adjust prior probabilities below and recompute the analysis 
              to verify how the deterministic engine shifts experiment priorities when scientific beliefs change.
            </span>
          </div>

          <div className="cards-grid">
            {currentScenario?.hypotheses.map(h => {
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
                    <strong>Supporting Claims:</strong> {h.evidence_ids.join(', ') || 'None attached'}
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
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '12px' }}>
            Deterministically Quantified Experiments (Ranked by Utility)
          </h3>
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

          {/* Unquantified Proposals Section */}
          {analysisResult?.unquantified_experiments && analysisResult.unquantified_experiments.length > 0 && (
            <div style={{ marginTop: '28px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  Unquantified Experimental Proposals (No Fabricated Likelihoods)
                </h3>
                <span className="badge badge-slate">EXCLUDED FROM EIG RANKING</span>
              </div>
              <div className="alert-box alert-amber">
                <div>
                  <strong>Integrity Boundary:</strong> The following experiments are scientifically formulated in literature, 
                  but published quantitative likelihood distributions are missing. JANUS refuses to invent synthetic probabilities 
                  to make the ranking appear complete. Empirical signal-to-noise and kinetic lifetime measurements are required.
                </div>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Proposal ID</th>
                      <th>Experimental Proposal</th>
                      <th>Status</th>
                      <th>Feasibility</th>
                      <th>Missing Information Required</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResult.unquantified_experiments.map(unq => (
                      <tr key={unq.experiment_id}>
                        <td className="mono"><strong>{unq.experiment_id}</strong></td>
                        <td>
                          <strong>{unq.experiment_name}</strong>
                        </td>
                        <td>
                          <span className="badge badge-slate">UNQUANTIFIED</span>
                        </td>
                        <td>
                          <span className="badge badge-blue">{(unq.feasibility * 100).toFixed(0)}%</span>
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {unq.missing_inputs_explanation}
                        </td>
                        <td>
                          <button 
                            className="btn-secondary" 
                            style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                            onClick={() => setSelectedExpId(unq.experiment_id)}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Detailed Inspector for Selected Experiment */}
          {selectedScore && (
            <div className="card" style={{ borderLeft: '4px solid var(--brand-primary)', marginTop: '20px' }}>
              <div className="card-header">
                <div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                    {selectedScore.rank ? (
                      <span className="badge badge-indigo">RANK #{selectedScore.rank}</span>
                    ) : (
                      <span className="badge badge-slate">UNQUANTIFIED PROPOSAL</span>
                    )}
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
                  <strong>Scientific Rationale:</strong> {selectedScore.explanation}
                </p>

                {/* Bayesian Posterior Update Matrix (only if quantified) */}
                {Object.keys(selectedScore.posterior_matrix).length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase', marginBottom: '8px' }}>
                      Bayesian Posterior Distribution Matrix: P(Hypothesis | Observed Outcome)
                    </h4>
                    <div className="table-container" style={{ marginBottom: '12px' }}>
                      <table>
                        <thead>
                          <tr>
                            <th>Observable Outcome (y)</th>
                            <th>Marginal P(y)</th>
                            {currentScenario?.hypotheses.map(h => (
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
                              {currentScenario?.hypotheses.map(h => {
                                const p = posteriors[h.id] ?? 0.0;
                                const isHigh = p > 0.8;
                                return (
                                  <td key={h.id}>
                                    <span className={`mono ${isHigh ? 'metric-highlight green' : ''}`} style={{ fontWeight: isHigh ? 700 : 400 }}>
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
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: EVIDENCE LEDGER & CLAIMS */}
      {activeTab === 'evidence' && (
        <div>
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <div>
                <h3 className="card-title">Peer-Reviewed Evidence Ledger & Claim Verification</h3>
                <p className="card-subtitle">Every claim is traced to an authoritative peer-reviewed primary source</p>
              </div>
              <span className="badge badge-emerald">PRIMARY SOURCES VERIFIED</span>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Claim ID</th>
                    <th>Verified Statement</th>
                    <th>Provenance</th>
                    <th>Primary Source & DOI</th>
                    <th>Location in Source</th>
                    <th>Extracted Quantitative Value</th>
                  </tr>
                </thead>
                <tbody>
                  {currentScenario?.evidence.map(ev => {
                    let provBadgeClass = 'badge-slate';
                    if (ev.provenance === 'empirical_observation') provBadgeClass = 'badge-emerald';
                    else if (ev.provenance === 'computational_dft') provBadgeClass = 'badge-blue';
                    else if (ev.provenance === 'author_interpretation') provBadgeClass = 'badge-purple';
                    else if (ev.provenance === 'synthetic_fixture') provBadgeClass = 'badge-amber';

                    return (
                      <tr key={ev.id}>
                        <td className="mono" style={{ whiteSpace: 'nowrap' }}>
                          <strong>{ev.id}</strong>
                        </td>
                        <td style={{ minWidth: '280px' }}>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '6px' }}>{ev.summary}</p>
                          <div style={{ display: 'flex', gap: '6px', fontSize: '0.75rem' }}>
                            {ev.supports_hypotheses && ev.supports_hypotheses.length > 0 && (
                              <span style={{ color: '#059669' }}>Supports: {ev.supports_hypotheses.join(', ')}</span>
                            )}
                            {ev.refutes_hypotheses && ev.refutes_hypotheses.length > 0 && (
                              <span style={{ color: '#e11d48' }}>Refutes: {ev.refutes_hypotheses.join(', ')}</span>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${provBadgeClass}`} style={{ whiteSpace: 'nowrap' }}>
                            {ev.provenance.replace('_', ' ')}
                          </span>
                        </td>
                        <td style={{ minWidth: '220px', fontSize: '0.8rem' }}>
                          <div>{ev.source}</div>
                          {ev.source_doi && (
                            <a 
                              href={`https://doi.org/${ev.source_doi}`} 
                              target="_blank" 
                              rel="noreferrer" 
                              className="doi-link"
                            >
                              doi:{ev.source_doi} ↗
                            </a>
                          )}
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', whiteSpace: 'nowrap' }}>
                          {ev.source_location || 'N/A'}
                        </td>
                        <td className="mono" style={{ fontSize: '0.8rem' }}>
                          {ev.quantitative_value ? (
                            <div>
                              <strong>{ev.quantitative_value.metric}</strong>: {ev.quantitative_value.value} {ev.quantitative_value.unit}
                            </div>
                          ) : (
                            <span style={{ color: 'var(--text-subtle)' }}>Qualitative</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: MATHEMATICAL AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div>
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
