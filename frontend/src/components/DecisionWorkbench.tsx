import React, { useState, useEffect } from 'react';
import type {
  AnalysisInput,
  AnalysisResult,
  Hypothesis,
  Experiment,
  PredictedOutcome,
} from '../types';
import {
  fetchCaseStudyScenario,
  fetchOerScenario,
  fetchDemoScenario,
  runAnalysis,
} from '../api';

interface SequentialHistoryStep {
  stepNumber: number;
  experimentId: string;
  experimentName: string;
  observedOutcome: string;
  priorEntropy: number;
  posteriorEntropy: number;
  informationGain: number;
  stepCost: number;
  cumulativeCost: number;
  resultingPosterior: Record<string, number>;
}

export const DecisionWorkbench: React.FC = () => {
  // Current active step in the researcher flow
  const [currentStage, setCurrentStage] = useState<'question' | 'hypotheses' | 'experiments' | 'rankings' | 'preview'>('question');

  // Core Scenario Data
  const [scenario, setScenario] = useState<AnalysisInput>({
    scenario_name: 'Pt/CeO2 Low-Temperature Water-Gas Shift Mechanism',
    scenario_type: 'published_case_study',
    case_study_id: 'CS-CAT-001',
    is_synthetic: false,
    cost_weight: 0.1,
    hypotheses: [],
    experiments: [],
    evidence: [],
  });

  // Analysis result from backend
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Selected experiment in rankings/explanation
  const [selectedExpId, setSelectedExpId] = useState<string | null>(null);

  // Outcome preview state
  const [previewExpId, setPreviewExpId] = useState<string | null>(null);
  const [previewOutcome, setPreviewOutcome] = useState<string | null>(null);

  // Initial pristine copy for reset
  const [initialScenarioCopy, setInitialScenarioCopy] = useState<AnalysisInput | null>(null);

  // Multi-step sequential execution log
  const [executionHistory, setExecutionHistory] = useState<SequentialHistoryStep[]>([]);
  const [executedExperimentIds, setExecutedExperimentIds] = useState<string[]>([]);

  // Load default scenario (CS-CAT-001) on mount
  useEffect(() => {
    loadScenarioPreset('CS-CAT-001');
  }, []);

  const loadScenarioPreset = async (presetId: 'CS-CAT-001' | 'CS-OER-002' | 'demo' | 'blank') => {
    setLoading(true);
    setError(null);
    try {
      if (presetId === 'blank') {
        const blankScenario: AnalysisInput = {
          scenario_name: 'Custom Hypothesis Disambiguation Question',
          scenario_type: 'synthetic_benchmark',
          is_synthetic: true,
          cost_weight: 0.1,
          hypotheses: [
            {
              id: 'H1',
              name: 'Hypothesis A (Primary Mechanism)',
              description: 'Primary mechanistic pathway proposed for this phenomenon.',
              prior: 0.50,
              assumptions: ['Standard laboratory conditions hold'],
              evidence_ids: [],
              status: 'active',
            },
            {
              id: 'H2',
              name: 'Hypothesis B (Alternative Mechanism)',
              description: 'Competing alternative pathway proposed in domain literature.',
              prior: 0.50,
              assumptions: ['Standard laboratory conditions hold'],
              evidence_ids: [],
              status: 'active',
            },
          ],
          experiments: [
            {
              id: 'EXP-01',
              name: 'Diagnostic Assay 1',
              description: 'Quantitative assay designed to measure differential marker response.',
              quantification_status: 'QUANTIFIED_BAYESIAN',
              possible_outcomes: ['Signal_Elevated', 'Signal_Baseline'],
              predictions: [
                { outcome_label: 'Signal_Elevated', hypothesis_id: 'H1', probability: 0.85 },
                { outcome_label: 'Signal_Baseline', hypothesis_id: 'H1', probability: 0.15 },
                { outcome_label: 'Signal_Elevated', hypothesis_id: 'H2', probability: 0.10 },
                { outcome_label: 'Signal_Baseline', hypothesis_id: 'H2', probability: 0.90 },
              ],
              cost: 1.0,
              feasibility: 0.95,
              assumptions: ['Detector response is linear in dynamic range'],
              is_feasible: true,
              source_evidence_ids: [],
            },
          ],
          evidence: [],
        };
        setScenario(blankScenario);
        setInitialScenarioCopy(JSON.parse(JSON.stringify(blankScenario)));
        setExecutionHistory([]);
        setExecutedExperimentIds([]);
        const result = await runAnalysis(blankScenario);
        setAnalysisResult(result);
        if (result.ranked_experiments.length > 0) {
          const top = result.ranked_experiments[0];
          setSelectedExpId(top.experiment_id);
          setPreviewExpId(top.experiment_id);
          const expObj = blankScenario.experiments.find(e => e.id === top.experiment_id);
          if (expObj && expObj.possible_outcomes.length > 0) {
            setPreviewOutcome(expObj.possible_outcomes[0]);
          }
        }
      } else {
        let loaded: AnalysisInput;
        if (presetId === 'CS-CAT-001') {
          loaded = await fetchCaseStudyScenario();
        } else if (presetId === 'CS-OER-002') {
          loaded = await fetchOerScenario();
        } else {
          loaded = await fetchDemoScenario();
        }
        setScenario(loaded);
        setInitialScenarioCopy(JSON.parse(JSON.stringify(loaded)));
        setExecutionHistory([]);
        setExecutedExperimentIds([]);
        const result = await runAnalysis(loaded);
        setAnalysisResult(result);
        if (result.ranked_experiments.length > 0) {
          const top = result.ranked_experiments[0];
          setSelectedExpId(top.experiment_id);
          setPreviewExpId(top.experiment_id);
          const expObj = loaded.experiments.find(e => e.id === top.experiment_id);
          if (expObj && expObj.possible_outcomes.length > 0) {
            setPreviewOutcome(expObj.possible_outcomes[0]);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load scenario preset.');
    } finally {
      setLoading(false);
    }
  };

  const executeCurrentAnalysis = async (customScenario?: AnalysisInput) => {
    const toAnalyze = customScenario || scenario;
    setAnalyzing(true);
    setError(null);
    try {
      const result = await runAnalysis(toAnalyze);
      setAnalysisResult(result);
      if (result.ranked_experiments.length > 0 && !selectedExpId) {
        setSelectedExpId(result.ranked_experiments[0].experiment_id);
      }
      return result;
    } catch (err: any) {
      setError(err.message || 'Analysis failed. Please inspect input probabilities and constraints.');
      return null;
    } finally {
      setAnalyzing(false);
    }
  };

  // Hypotheses manipulation
  const handleAddHypothesis = () => {
    const nextNum = scenario.hypotheses.length + 1;
    const newHyp: Hypothesis = {
      id: `H${nextNum}`,
      name: `Hypothesis ${nextNum}`,
      description: `Description of proposed mechanistic pathway H${nextNum}`,
      prior: 0.10,
      assumptions: [],
      evidence_ids: [],
      status: 'active',
    };
    const updated = [...scenario.hypotheses, newHyp];
    setScenario({ ...scenario, hypotheses: updated });
  };

  const handleRemoveHypothesis = (hId: string) => {
    if (scenario.hypotheses.length <= 2) {
      alert('At least two competing hypotheses are required for scientific disambiguation.');
      return;
    }
    const updated = scenario.hypotheses.filter(h => h.id !== hId);
    // Also remove any predictions referencing this hypothesis from experiments
    const updatedExps = scenario.experiments.map(exp => ({
      ...exp,
      predictions: exp.predictions.filter(p => p.hypothesis_id !== hId),
    }));
    setScenario({ ...scenario, hypotheses: updated, experiments: updatedExps });
  };

  const handlePriorChange = (hId: string, val: number) => {
    const updated = scenario.hypotheses.map(h =>
      h.id === hId ? { ...h, prior: isNaN(val) ? 0 : val } : h
    );
    setScenario({ ...scenario, hypotheses: updated });
  };

  const handleNormalizePriors = () => {
    const total = scenario.hypotheses.reduce((acc, h) => acc + (h.prior || 0), 0);
    if (total <= 0) {
      alert('Total prior sum is zero. Assign at least one positive prior value before normalizing.');
      return;
    }
    const updated = scenario.hypotheses.map(h => ({
      ...h,
      prior: parseFloat(((h.prior || 0) / total).toFixed(4)),
    }));
    setScenario({ ...scenario, hypotheses: updated });
  };

  // Experiment manipulation
  const handleAddExperiment = () => {
    const nextNum = scenario.experiments.length + 1;
    const defaultOutcomes = ['Positive_Response', 'Negative_Response'];
    const predictions: PredictedOutcome[] = [];
    scenario.hypotheses.forEach(h => {
      predictions.push({ outcome_label: defaultOutcomes[0], hypothesis_id: h.id, probability: 0.50 });
      predictions.push({ outcome_label: defaultOutcomes[1], hypothesis_id: h.id, probability: 0.50 });
    });

    const newExp: Experiment = {
      id: `EXP-0${nextNum}`,
      name: `Candidate Assay ${nextNum}`,
      description: `Protocol summary and operational procedure for Assay ${nextNum}.`,
      quantification_status: 'QUANTIFIED_BAYESIAN',
      possible_outcomes: defaultOutcomes,
      predictions,
      cost: 1.0,
      feasibility: 0.90,
      assumptions: ['Standard experimental conditions'],
      is_feasible: true,
      source_evidence_ids: [],
    };
    setScenario({ ...scenario, experiments: [...scenario.experiments, newExp] });
  };

  const handleRemoveExperiment = (expId: string) => {
    if (scenario.experiments.length <= 1) {
      alert('At least one candidate experiment is required.');
      return;
    }
    setScenario({
      ...scenario,
      experiments: scenario.experiments.filter(e => e.id !== expId),
    });
  };

  const handleLikelihoodChange = (expId: string, hId: string, outcome: string, val: number) => {
    const updatedExps = scenario.experiments.map(exp => {
      if (exp.id !== expId) return exp;
      const predictions = [...exp.predictions];
      const idx = predictions.findIndex(p => p.hypothesis_id === hId && p.outcome_label === outcome);
      if (idx >= 0) {
        predictions[idx] = { ...predictions[idx], probability: isNaN(val) ? 0 : val };
      } else {
        predictions.push({ outcome_label: outcome, hypothesis_id: hId, probability: isNaN(val) ? 0 : val });
      }
      return { ...exp, predictions };
    });
    setScenario({ ...scenario, experiments: updatedExps });
  };

  const handleNormalizeLikelihoodRow = (expId: string, hId: string) => {
    const exp = scenario.experiments.find(e => e.id === expId);
    if (!exp) return;
    const rowPreds = exp.predictions.filter(p => p.hypothesis_id === hId);
    const rowSum = rowPreds.reduce((acc, p) => acc + (p.probability || 0), 0);
    if (rowSum <= 0) {
      alert(`Likelihood sum under ${hId} is zero. Assign positive likelihood values before normalizing.`);
      return;
    }
    const updatedExps = scenario.experiments.map(e => {
      if (e.id !== expId) return e;
      const updatedPredictions = e.predictions.map(p => {
        if (p.hypothesis_id === hId) {
          return { ...p, probability: parseFloat(((p.probability || 0) / rowSum).toFixed(4)) };
        }
        return p;
      });
      return { ...e, predictions: updatedPredictions };
    });
    setScenario({ ...scenario, experiments: updatedExps });
  };

  // Outcome preview and Bayesian posterior update simulation
  const handleApplyOutcomeAsSequentialStep = async () => {
    if (!selectedExpScore || !previewOutcome || !previewExp) return;

    const posteriorsForOutcome = selectedExpScore.posterior_matrix[previewOutcome];
    if (!posteriorsForOutcome) {
      alert(`No posterior distribution found for outcome '${previewOutcome}'.`);
      return;
    }

    const prevPriorEntropy = selectedExpScore.prior_entropy;
    const posteriorValues = Object.values(posteriorsForOutcome);
    // Shannon entropy of new posterior: - sum(p * log2(p))
    const newEntropy = -posteriorValues.reduce((acc, p) => {
      return p > 1e-12 ? acc + p * Math.log2(p) : acc;
    }, 0);
    const realizedIG = Math.max(0, prevPriorEntropy - newEntropy);

    const stepNum = executionHistory.length + 1;
    const cumulativeCost = executionHistory.reduce((acc, s) => acc + s.stepCost, 0) + previewExp.cost;

    const historyEntry: SequentialHistoryStep = {
      stepNumber: stepNum,
      experimentId: previewExp.id,
      experimentName: previewExp.name,
      observedOutcome: previewOutcome,
      priorEntropy: prevPriorEntropy,
      posteriorEntropy: newEntropy,
      informationGain: realizedIG,
      stepCost: previewExp.cost,
      cumulativeCost,
      resultingPosterior: posteriorsForOutcome,
    };

    // Update scenario: update hypothesis priors to match new posterior, mark exp as executed
    const updatedHypotheses = scenario.hypotheses.map(h => ({
      ...h,
      prior: posteriorsForOutcome[h.id] !== undefined ? posteriorsForOutcome[h.id] : h.prior,
    }));

    const newExecutedIds = [...executedExperimentIds, previewExp.id];
    setExecutedExperimentIds(newExecutedIds);
    setExecutionHistory([...executionHistory, historyEntry]);

    const updatedScenario: AnalysisInput = {
      ...scenario,
      hypotheses: updatedHypotheses,
    };
    setScenario(updatedScenario);

    // Re-run backend analysis to dynamically re-rank remaining candidates under new priors
    const newResult = await executeCurrentAnalysis(updatedScenario);
    if (newResult) {
      // Pick next unexecuted candidate for preview
      const nextExp = newResult.ranked_experiments.find(e => !newExecutedIds.includes(e.experiment_id));
      if (nextExp) {
        setSelectedExpId(nextExp.experiment_id);
        setPreviewExpId(nextExp.experiment_id);
        const expObj = updatedScenario.experiments.find(e => e.id === nextExp.experiment_id);
        if (expObj && expObj.possible_outcomes.length > 0) {
          setPreviewOutcome(expObj.possible_outcomes[0]);
        }
      }
    }
  };

  const handleResetToInitialState = async () => {
    if (!initialScenarioCopy) return;
    setScenario(JSON.parse(JSON.stringify(initialScenarioCopy)));
    setExecutionHistory([]);
    setExecutedExperimentIds([]);
    const res = await executeCurrentAnalysis(initialScenarioCopy);
    if (res && res.ranked_experiments.length > 0) {
      const top = res.ranked_experiments[0];
      setSelectedExpId(top.experiment_id);
      setPreviewExpId(top.experiment_id);
      const expObj = initialScenarioCopy.experiments.find(e => e.id === top.experiment_id);
      if (expObj && expObj.possible_outcomes.length > 0) {
        setPreviewOutcome(expObj.possible_outcomes[0]);
      }
    }
  };

  // Helper metrics
  const totalPrior = scenario.hypotheses.reduce((acc, h) => acc + (h.prior || 0), 0);
  const isPriorValid = Math.abs(totalPrior - 1.0) < 0.001;

  const selectedExpScore = analysisResult?.ranked_experiments.find(s => s.experiment_id === (previewExpId || selectedExpId)) ||
    analysisResult?.unquantified_experiments.find(s => s.experiment_id === (previewExpId || selectedExpId));

  const previewExp = scenario.experiments.find(e => e.id === (previewExpId || selectedExpId));

  if (loading) {
    return (
      <div className="card" style={{ padding: '60px', textAlign: 'center' }}>
        <div className="brand-badge" style={{ display: 'inline-block', marginBottom: '16px' }}>JANUS</div>
        <h3>Loading Scientific Decision Workbench...</h3>
        <p style={{ color: 'var(--text-subtle)', marginTop: '8px' }}>Initializing formal Bayesian structures and parameter matrices.</p>
      </div>
    );
  }

  return (
    <div className="workbench-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Workbench Navigation Stepper Header */}
      <div className="card" style={{ padding: '16px 24px', backgroundColor: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-indigo">SCIENTIFIC DECISION WORKBENCH</span>
              <span className="badge badge-emerald">PHASE 7 MILESTONE</span>
              {scenario.is_synthetic ? (
                <span className="badge badge-amber">SYNTHETIC FIXTURE</span>
              ) : (
                <span className="badge badge-emerald">PRIMARY LITERATURE EVIDENCE</span>
              )}
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '6px' }}>
              Sequential Bayesian Experimental Design Interactive Workbench
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', marginTop: '2px' }}>
              Formulate scientific questions, specify competing mechanistic hypotheses, audit candidate likelihood tables, and inspect information-theoretic recommendations.
            </p>
          </div>

          {/* Preset Loaders */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Load Preset:</span>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              onClick={() => loadScenarioPreset('CS-CAT-001')}
              title="Pt/CeO2 Low-Temperature Water-Gas Shift Catalysis"
            >
              CS-CAT-001 (Pt/CeO2)
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              onClick={() => loadScenarioPreset('CS-OER-002')}
              title="Perovskite Oxygen Evolution Reaction Electrocatalysis"
            >
              CS-OER-002 (Perovskite OER)
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              onClick={() => loadScenarioPreset('demo')}
              title="Kinase Signaling Pathway Synthetic Benchmark"
            >
              Kinase Benchmark
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px', borderStyle: 'dashed' }}
              onClick={() => loadScenarioPreset('blank')}
              title="Start a fresh blank scenario from scratch"
            >
              + Blank Template
            </button>
          </div>
        </div>

        {/* Guided 5-Step Process Bar */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <button
            onClick={() => setCurrentStage('question')}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              textAlign: 'left',
              border: currentStage === 'question' ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
              backgroundColor: currentStage === 'question' ? 'var(--brand-light)' : 'transparent',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-subtle)' }}>Step 1</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Question & Scope</div>
          </button>

          <button
            onClick={() => setCurrentStage('hypotheses')}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              textAlign: 'left',
              border: currentStage === 'hypotheses' ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
              backgroundColor: currentStage === 'hypotheses' ? 'var(--brand-light)' : 'transparent',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-subtle)' }}>Step 2</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Hypotheses & Priors ({scenario.hypotheses.length})</div>
          </button>

          <button
            onClick={() => setCurrentStage('experiments')}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              textAlign: 'left',
              border: currentStage === 'experiments' ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
              backgroundColor: currentStage === 'experiments' ? 'var(--brand-light)' : 'transparent',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-subtle)' }}>Step 3</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Candidate Assays ({scenario.experiments.length})</div>
          </button>

          <button
            onClick={() => setCurrentStage('rankings')}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              textAlign: 'left',
              border: currentStage === 'rankings' ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
              backgroundColor: currentStage === 'rankings' ? 'var(--brand-light)' : 'transparent',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-subtle)' }}>Step 4</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Rankings & EIG</div>
          </button>

          <button
            onClick={() => setCurrentStage('preview')}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              textAlign: 'left',
              border: currentStage === 'preview' ? '2px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
              backgroundColor: currentStage === 'preview' ? 'var(--brand-light)' : 'transparent',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-subtle)' }}>Step 5</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Outcome Preview</div>
          </button>
        </div>
      </div>

      {/* Global Alerts */}
      {error && (
        <div className="alert-box alert-amber" style={{ padding: '12px 16px', borderRadius: '8px' }}>
          <strong>Input Validation Error:</strong> {error}
        </div>
      )}

      {/* STAGE 1: Scientific Question & Scope */}
      {currentStage === 'question' && (
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '16px' }}>
            1. Define the Scientific Question & Evaluation Scope
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                Scientific Question / Phenomenon Under Investigation:
              </label>
              <input
                type="text"
                className="input-field"
                value={scenario.scenario_name}
                onChange={e => setScenario({ ...scenario, scenario_name: e.target.value })}
                placeholder="e.g., Which reaction pathway dominates low-temperature water-gas shift on Pt/CeO2?"
                style={{ width: '100%', padding: '10px 12px', fontSize: '0.95rem' }}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '6px' }}>
                Clearly state the core scientific ambiguity or mechanistic uncertainty to be resolved by experimental evidence.
              </p>

              <div style={{ marginTop: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                  Scientific Domain & Provenance Mode:
                </label>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
                    <input
                      type="radio"
                      name="scenario_type"
                      checked={!scenario.is_synthetic}
                      onChange={() => setScenario({ ...scenario, is_synthetic: false, scenario_type: 'published_case_study' })}
                    />
                    Peer-Reviewed Literature Grounded (Empirical Catalysis / Operando)
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
                    <input
                      type="radio"
                      name="scenario_type"
                      checked={scenario.is_synthetic}
                      onChange={() => setScenario({ ...scenario, is_synthetic: true, scenario_type: 'synthetic_benchmark' })}
                    />
                    Synthetic / Algorithmic Benchmark Fixture
                  </label>
                </div>
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-surface-alt)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '8px' }}>Policy Settings</h4>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                Cost Penalization Factor (&alpha;):
              </label>
              <input
                type="number"
                step="0.01"
                min="0.0"
                max="2.0"
                className="input-field"
                value={scenario.cost_weight}
                onChange={e => setScenario({ ...scenario, cost_weight: parseFloat(e.target.value) || 0.0 })}
                style={{ width: '100%', padding: '8px 10px', fontSize: '0.9rem' }}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '6px' }}>
                Used in Composite Utility: <code>U(e) = Feasibility &times; [EIG / (1 + &alpha; &times; Cost)]</code>.
                When &alpha; = 0, ranking is purely based on Feasibility &times; EIG.
              </p>

              <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                <button
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  onClick={() => setCurrentStage('hypotheses')}
                >
                  Proceed to Hypotheses &rarr;
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STAGE 2: Hypotheses & Priors */}
      {currentStage === 'hypotheses' && (
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>2. Competing Scientific Hypotheses & Epistemic Priors</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-subtle)' }}>
                Define mutually exclusive explanations and assign epistemic prior probabilities reflecting baseline uncertainty.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn btn-secondary" onClick={handleNormalizePriors} title="Normalize priors so they sum to 1.0">
                Normalize Priors
              </button>
              <button className="btn btn-primary" onClick={handleAddHypothesis}>
                + Add Hypothesis
              </button>
            </div>
          </div>

          {/* Simplex Normalization Status Bar */}
          <div style={{
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            backgroundColor: isPriorValid ? 'var(--accent-emerald-bg)' : 'var(--accent-amber-bg)',
            border: `1px solid ${isPriorValid ? 'var(--accent-emerald)' : 'var(--accent-amber)'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div>
              <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                {isPriorValid ? 'Simplex Constraint Satisfied:' : 'Simplex Normalization Required:'}
              </span>{' '}
              <span style={{ fontSize: '0.85rem' }}>
                Current sum &sum; P(H<sub>k</sub>) = <strong>{totalPrior.toFixed(4)}</strong> (Target: 1.0000).
              </span>
            </div>
            {!isPriorValid && (
              <button
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 10px', backgroundColor: '#ffffff' }}
                onClick={handleNormalizePriors}
              >
                Auto-Normalize to 1.0
              </button>
            )}
          </div>

          {/* Visual Prior Distribution Bar */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', marginBottom: '6px' }}>
              PRIOR PROBABILITY DENSITY ALLOCATION:
            </div>
            <div style={{ display: 'flex', height: '24px', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
              {scenario.hypotheses.map((h, i) => {
                const colors = ['#4f46e5', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0284c7'];
                const widthPct = totalPrior > 0 ? ((h.prior || 0) / totalPrior) * 100 : 0;
                return (
                  <div
                    key={h.id}
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: colors[i % colors.length],
                      color: '#ffffff',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      textOverflow: 'ellipsis',
                      padding: '0 4px',
                    }}
                    title={`${h.id}: ${(widthPct).toFixed(1)}%`}
                  >
                    {widthPct >= 10 ? `${h.id}: ${((h.prior || 0) * 100).toFixed(0)}%` : h.id}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Hypotheses List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {scenario.hypotheses.map(h => (
              <div
                key={h.id}
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-surface)',
                  display: 'grid',
                  gridTemplateColumns: '120px 2fr 160px 80px',
                  gap: '16px',
                  alignItems: 'center'
                }}
              >
                <div>
                  <span className="mono" style={{ fontWeight: 700, fontSize: '0.9rem' }}>{h.id}</span>
                </div>
                <div>
                  <input
                    type="text"
                    className="input-field"
                    value={h.name}
                    onChange={e => {
                      const updated = scenario.hypotheses.map(item => item.id === h.id ? { ...item, name: e.target.value } : item);
                      setScenario({ ...scenario, hypotheses: updated });
                    }}
                    style={{ width: '100%', fontWeight: 600, fontSize: '0.9rem', marginBottom: '4px' }}
                    placeholder="Short Hypothesis Title"
                  />
                  <input
                    type="text"
                    className="input-field"
                    value={h.description}
                    onChange={e => {
                      const updated = scenario.hypotheses.map(item => item.id === h.id ? { ...item, description: e.target.value } : item);
                      setScenario({ ...scenario, hypotheses: updated });
                    }}
                    style={{ width: '100%', fontSize: '0.8rem', color: 'var(--text-muted)' }}
                    placeholder="Mechanistic details and physical pathway explanation"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)' }}>
                    Prior P({h.id}):
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.01"
                    max="1.0"
                    className="input-field"
                    value={h.prior}
                    onChange={e => handlePriorChange(h.id, parseFloat(e.target.value))}
                    style={{ width: '100%', fontSize: '0.9rem', fontWeight: 700 }}
                  />
                </div>
                <div>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleRemoveHypothesis(h.id)}
                    style={{ color: 'var(--accent-rose)', border: 'none', padding: '6px' }}
                    title="Remove hypothesis"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="btn btn-secondary" onClick={() => setCurrentStage('question')}>
              &larr; Back to Scope
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setCurrentStage('experiments')}
            >
              Proceed to Candidate Assays &rarr;
            </button>
          </div>
        </div>
      )}

      {/* STAGE 3: Candidate Experiments & Likelihood Matrices */}
      {currentStage === 'experiments' && (
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>3. Candidate Experiments & Conditional Likelihood Tables</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-subtle)' }}>
                Configure candidate assays, observable outcomes, and conditional probability distributions P(y | H<sub>k</sub>, e).
              </p>
            </div>
            <button className="btn btn-primary" onClick={handleAddExperiment}>
              + Add Candidate Assay
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {scenario.experiments.map(exp => (
              <div
                key={exp.id}
                style={{
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '20px',
                  backgroundColor: 'var(--bg-surface)'
                }}
              >
                {/* Header row: ID, Name, Cost, Feasibility, Delete */}
                <div style={{ display: 'grid', gridTemplateColumns: '120px 2fr 120px 140px 80px', gap: '16px', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <span className="mono" style={{ fontWeight: 700, fontSize: '0.95rem' }}>{exp.id}</span>
                  </div>
                  <div>
                    <input
                      type="text"
                      className="input-field"
                      value={exp.name}
                      onChange={e => {
                        const updated = scenario.experiments.map(item => item.id === exp.id ? { ...item, name: e.target.value } : item);
                        setScenario({ ...scenario, experiments: updated });
                      }}
                      style={{ width: '100%', fontWeight: 600, fontSize: '0.95rem' }}
                      placeholder="Assay Name"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)' }}>
                      Cost:
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      className="input-field"
                      value={exp.cost}
                      onChange={e => {
                        const updated = scenario.experiments.map(item => item.id === exp.id ? { ...item, cost: parseFloat(e.target.value) || 0.1 } : item);
                        setScenario({ ...scenario, experiments: updated });
                      }}
                      style={{ width: '100%', fontSize: '0.9rem' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)' }}>
                      Feasibility ({((exp.feasibility || 1.0) * 100).toFixed(0)}%):
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0.05"
                      max="1.0"
                      className="input-field"
                      value={exp.feasibility}
                      onChange={e => {
                        const updated = scenario.experiments.map(item => item.id === exp.id ? { ...item, feasibility: parseFloat(e.target.value) || 0.1 } : item);
                        setScenario({ ...scenario, experiments: updated });
                      }}
                      style={{ width: '100%', fontSize: '0.9rem' }}
                    />
                  </div>
                  <div>
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleRemoveExperiment(exp.id)}
                      style={{ color: 'var(--accent-rose)', border: 'none', padding: '6px' }}
                      title="Remove experiment"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <input
                    type="text"
                    className="input-field"
                    value={exp.description}
                    onChange={e => {
                      const updated = scenario.experiments.map(item => item.id === exp.id ? { ...item, description: e.target.value } : item);
                      setScenario({ ...scenario, experiments: updated });
                    }}
                    style={{ width: '100%', fontSize: '0.85rem', color: 'var(--text-muted)' }}
                    placeholder="Assay protocol, experimental setup, or spectroscopic conditions"
                  />
                </div>

                {/* Observable Outcomes Chips */}
                <div style={{ marginBottom: '16px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-subtle)', marginRight: '8px' }}>
                    Observable Outcomes:
                  </span>
                  {exp.possible_outcomes.map(o => (
                    <span key={o} className="badge badge-indigo" style={{ marginRight: '6px', fontSize: '0.75rem' }}>
                      {o}
                    </span>
                  ))}
                </div>

                {/* Conditional Likelihood Matrix */}
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ fontSize: '0.85rem' }}>
                    <thead>
                      <tr>
                        <th style={{ width: '220px' }}>Hypothesis (H<sub>k</sub>)</th>
                        {exp.possible_outcomes.map(o => (
                          <th key={o}>P({o} | H<sub>k</sub>)</th>
                        ))}
                        <th style={{ width: '120px' }}>Row Sum</th>
                        <th style={{ width: '100px' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scenario.hypotheses.map(h => {
                        const rowPreds = exp.predictions.filter(p => p.hypothesis_id === h.id);
                        const rowSum = rowPreds.reduce((acc, p) => acc + (p.probability || 0), 0);
                        const isRowValid = Math.abs(rowSum - 1.0) < 0.001;
                        return (
                          <tr key={h.id}>
                            <td>
                              <strong>{h.id}</strong>: <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{h.name}</span>
                            </td>
                            {exp.possible_outcomes.map(o => {
                              const pred = exp.predictions.find(p => p.hypothesis_id === h.id && p.outcome_label === o);
                              const prob = pred ? pred.probability : 0.0;
                              return (
                                <td key={o}>
                                  <input
                                    type="number"
                                    step="0.05"
                                    min="0.0"
                                    max="1.0"
                                    className="input-field"
                                    value={prob}
                                    onChange={e => handleLikelihoodChange(exp.id, h.id, o, parseFloat(e.target.value))}
                                    style={{ width: '90px', padding: '4px 6px', fontSize: '0.85rem' }}
                                  />
                                </td>
                              );
                            })}
                            <td>
                              <span style={{ fontWeight: 700, color: isRowValid ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                                {rowSum.toFixed(3)}
                              </span>{' '}
                              {isRowValid ? '✓' : '⚠️'}
                            </td>
                            <td>
                              {!isRowValid && (
                                <button
                                  className="btn btn-secondary"
                                  style={{ fontSize: '0.75rem', padding: '2px 6px' }}
                                  onClick={() => handleNormalizeLikelihoodRow(exp.id, h.id)}
                                >
                                  Normalize
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="btn btn-secondary" onClick={() => setCurrentStage('hypotheses')}>
              &larr; Back to Hypotheses
            </button>
            <button
              className="btn btn-primary"
              onClick={async () => {
                await executeCurrentAnalysis();
                setCurrentStage('rankings');
              }}
              disabled={analyzing}
            >
              {analyzing ? 'Computing EIG...' : 'Analyze & Rank Experiments &rarr;'}
            </button>
          </div>
        </div>
      )}

      {/* STAGE 4: Experiment Rankings & Recommendations */}
      {currentStage === 'rankings' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Action Bar */}
          <div className="card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>4. Information-Theoretic Rankings & Recommendation Explanations</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-subtle)' }}>
                Deterministic rankings calculated by the JANUS engine. Select any experiment below to inspect its diagnostic breakdown.
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => executeCurrentAnalysis()}
              disabled={analyzing}
            >
              {analyzing ? 'Re-calculating...' : 'Re-Run Analysis'}
            </button>
          </div>

          {analysisResult && (
            <>
              {/* Prior Entropy & Top Recommendation Banner */}
              {analysisResult.ranked_experiments.length > 0 && (
                <div
                  style={{
                    backgroundColor: 'var(--brand-light)',
                    border: '1px solid var(--brand-primary)',
                    borderRadius: '8px',
                    padding: '20px 24px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '16px'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="badge badge-indigo">OPTIMAL RECOMMENDATION</span>
                      <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                        {analysisResult.ranked_experiments[0].experiment_id}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '4px' }}>
                      {analysisResult.ranked_experiments[0].experiment_name}
                    </h4>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '750px' }}>
                      {analysisResult.ranked_experiments[0].explanation}
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: '20px', textAlign: 'center' }}>
                    <div style={{ backgroundColor: '#ffffff', padding: '12px 18px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)' }}>PRIOR ENTROPY</div>
                      <div className="mono" style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                        {analysisResult.ranked_experiments[0].prior_entropy.toFixed(4)} <span style={{ fontSize: '0.8rem' }}>bits</span>
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#ffffff', padding: '12px 18px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)' }}>EXPECTED INFO GAIN</div>
                      <div className="mono" style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                        {analysisResult.ranked_experiments[0].expected_information_gain.toFixed(4)} <span style={{ fontSize: '0.8rem' }}>bits</span>
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#ffffff', padding: '12px 18px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)' }}>COMPOSITE UTILITY</div>
                      <div className="mono" style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                        {analysisResult.ranked_experiments[0].composite_utility_score.toFixed(4)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Comparative Rankings Table */}
              <div className="card" style={{ padding: '20px' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px' }}>
                  Full Ranked Candidate Pool ({analysisResult.ranked_experiments.length} Quantified Assays)
                </h4>

                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th style={{ width: '80px' }}>Utility Rank</th>
                        <th style={{ width: '80px' }}>EIG Rank</th>
                        <th>Experiment</th>
                        <th>Expected Info Gain (EIG)</th>
                        <th>Feasibility</th>
                        <th>Cost</th>
                        <th>Composite Utility</th>
                        <th>Diagnostic Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisResult.ranked_experiments.map(s => {
                        const isSelected = s.experiment_id === (selectedExpId || analysisResult.ranked_experiments[0]?.experiment_id);
                        const isDivergent = s.utility_rank !== s.eig_rank;
                        return (
                          <tr
                            key={s.experiment_id}
                            style={{
                              backgroundColor: isSelected ? 'var(--brand-light)' : 'transparent',
                              cursor: 'pointer'
                            }}
                            onClick={() => {
                              setSelectedExpId(s.experiment_id);
                              setPreviewExpId(s.experiment_id);
                              const expObj = scenario.experiments.find(e => e.id === s.experiment_id);
                              if (expObj && expObj.possible_outcomes.length > 0) {
                                setPreviewOutcome(expObj.possible_outcomes[0]);
                              }
                            }}
                          >
                            <td>
                              <span className="badge badge-indigo" style={{ fontWeight: 700 }}>
                                #{s.utility_rank || s.rank}
                              </span>
                            </td>
                            <td>
                              <span className={`badge ${isDivergent ? 'badge-amber' : 'badge-emerald'}`}>
                                #{s.eig_rank}
                              </span>
                            </td>
                            <td>
                              <div style={{ fontWeight: 600 }}>{s.experiment_name}</div>
                              <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>{s.experiment_id}</div>
                            </td>
                            <td>
                              <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                                {s.expected_information_gain.toFixed(4)} bits
                              </span>
                            </td>
                            <td>{((s.feasibility || 0) * 100).toFixed(0)}%</td>
                            <td>{s.cost.toFixed(1)}</td>
                            <td>
                              <span className="mono" style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>
                                {s.composite_utility_score.toFixed(4)}
                              </span>
                            </td>
                            <td>
                              {s.is_informative ? (
                                <span className="badge badge-emerald">INFORMATIVE</span>
                              ) : (
                                <span className="badge badge-rose">UNINFORMATIVE (0 EIG)</span>
                              )}
                            </td>
                            <td>
                              <button
                                className="btn btn-secondary"
                                style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                                onClick={e => {
                                  e.stopPropagation();
                                  setSelectedExpId(s.experiment_id);
                                  setPreviewExpId(s.experiment_id);
                                  setCurrentStage('preview');
                                }}
                              >
                                Preview Outcome &rarr;
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Explanatory note on ranking divergence */}
                <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', marginTop: '12px' }}>
                  * <strong>Dual-Ranking Note:</strong> Utility Rank incorporates feasibility and cost penalties via <code>U(e) = Feas &times; [EIG / (1 + &alpha;&times;Cost)]</code>. Pure EIG Rank orders solely by raw mutual information in bits. Divergences indicate assays where high monetary or synchrotron costs outweigh slight analytical gain.
                </div>
              </div>

              {/* Deep Diagnostic Breakdown for Selected Assay */}
              {selectedExpScore && previewExp && (
                <div className="card" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                      <span className="badge badge-indigo">DEEP DIAGNOSTIC EXPLANATION</span>
                      <h4 style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>
                        {selectedExpScore.experiment_name} ({selectedExpScore.experiment_id})
                      </h4>
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        setPreviewExpId(selectedExpScore.experiment_id);
                        if (previewExp.possible_outcomes.length > 0) {
                          setPreviewOutcome(previewExp.possible_outcomes[0]);
                        }
                        setCurrentStage('preview');
                      }}
                    >
                      Inspect Simulated Posterior Updates &rarr;
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    {/* Left: Predicted Distributions under each hypothesis */}
                    <div style={{ backgroundColor: 'var(--bg-surface-alt)', padding: '16px', borderRadius: '8px' }}>
                      <h5 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px' }}>
                        Predicted Outcome Likelihoods P(y | H<sub>k</sub>):
                      </h5>
                      {scenario.hypotheses.map(h => (
                        <div key={h.id} style={{ marginBottom: '12px' }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 600, display: 'flex', justifyContent: 'space-between' }}>
                            <span>{h.id} ({h.name})</span>
                          </div>
                          <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                            {previewExp.possible_outcomes.map(o => {
                              const pred = previewExp.predictions.find(p => p.hypothesis_id === h.id && p.outcome_label === o);
                              const pVal = pred ? pred.probability : 0.0;
                              return (
                                <div key={o} style={{ flex: 1, backgroundColor: '#ffffff', padding: '6px 10px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                                  <div style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>{o}</div>
                                  <div className="mono" style={{ fontWeight: 700, fontSize: '0.85rem' }}>
                                    {(pVal * 100).toFixed(1)}%
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Right: Marginal Probabilities & Resulting Posteriors */}
                    <div style={{ backgroundColor: 'var(--bg-surface-alt)', padding: '16px', borderRadius: '8px' }}>
                      <h5 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px' }}>
                        Marginal Expectation P(y) & Resulting Bayesian Posteriors:
                      </h5>
                      {previewExp.possible_outcomes.map(o => {
                        const marginal = selectedExpScore.outcome_marginal_probabilities[o] || 0.0;
                        const posteriors = selectedExpScore.posterior_matrix[o] || {};
                        return (
                          <div key={o} style={{ marginBottom: '12px', backgroundColor: '#ffffff', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                              <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>Outcome: {o}</span>
                              <span className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>
                                P({o}) = {(marginal * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              {scenario.hypotheses.map(h => (
                                <div key={h.id} style={{ fontSize: '0.75rem' }}>
                                  <span style={{ color: 'var(--text-subtle)' }}>{h.id}: </span>
                                  <strong className="mono">{((posteriors[h.id] || 0) * 100).toFixed(1)}%</strong>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="btn btn-secondary" onClick={() => setCurrentStage('experiments')}>
              &larr; Back to Assays
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setCurrentStage('preview')}
            >
              Proceed to Outcome Preview &rarr;
            </button>
          </div>
        </div>
      )}

      {/* STAGE 5: Outcome Preview & Bayesian Posterior Updates */}
      {currentStage === 'preview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <span className="badge badge-emerald">STEP 5: SIMULATED EVIDENCE AUDIT</span>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '4px' }}>
                  Interactive Bayesian Outcome Preview
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-subtle)' }}>
                  Simulate potential observation outcomes to preview the exact Bayesian posterior update under the formal likelihood model.
                </p>
              </div>

              {executionHistory.length > 0 && (
                <button className="btn btn-secondary" onClick={handleResetToInitialState}>
                  Reset to Initial Priors
                </button>
              )}
            </div>

            {/* Mandatory Scientific Guardrail Alert */}
            <div
              style={{
                backgroundColor: 'var(--accent-amber-bg)',
                border: '1px solid var(--accent-amber)',
                borderRadius: '8px',
                padding: '12px 16px',
                marginBottom: '20px',
                fontSize: '0.85rem',
              }}
            >
              <strong>⚠️ SCIENTIFIC BOUNDARY ADVISORY:</strong> This outcome preview simulates the theoretical consequence of observing outcome <em>y</em> under the configured probability model. It represents mathematical deductive inference, <strong>not</strong> an empirical wet-lab observation. No physical measurement has occurred.
            </div>

            {/* Interactive Selectors: Experiment & Outcome */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                  Select Candidate Assay:
                </label>
                <select
                  className="input-field"
                  value={previewExpId || ''}
                  onChange={e => {
                    const newId = e.target.value;
                    setPreviewExpId(newId);
                    setSelectedExpId(newId);
                    const expObj = scenario.experiments.find(item => item.id === newId);
                    if (expObj && expObj.possible_outcomes.length > 0) {
                      setPreviewOutcome(expObj.possible_outcomes[0]);
                    }
                  }}
                  style={{ width: '100%', padding: '10px 12px', fontSize: '0.9rem', fontWeight: 600 }}
                >
                  {scenario.experiments.map(exp => (
                    <option key={exp.id} value={exp.id}>
                      {exp.id}: {exp.name} (Cost: {exp.cost}, Feas: {((exp.feasibility || 1.0) * 100).toFixed(0)}%)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                  Select Observable Outcome to Preview:
                </label>
                <select
                  className="input-field"
                  value={previewOutcome || ''}
                  onChange={e => setPreviewOutcome(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', fontSize: '0.9rem', fontWeight: 600 }}
                >
                  {previewExp?.possible_outcomes.map(o => (
                    <option key={o} value={o}>
                      Observation: {o}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Before-and-After Posterior Comparison Card */}
            {selectedExpScore && previewOutcome && (
              <div
                style={{
                  backgroundColor: 'var(--bg-surface-alt)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '24px',
                  marginBottom: '24px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                    Bayesian Belief Shift: Prior P(H<sub>k</sub>) &rarr; Posterior P(H<sub>k</sub> | {previewOutcome})
                  </h4>
                  <span className="badge badge-indigo">
                    Marginal Chance of this Outcome: {((selectedExpScore.outcome_marginal_probabilities[previewOutcome] || 0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {scenario.hypotheses.map(h => {
                    const prior = h.prior || 0.0;
                    const posterior = selectedExpScore.posterior_matrix[previewOutcome]?.[h.id] || 0.0;
                    const delta = posterior - prior;
                    const isPositive = delta > 0.001;
                    const isNegative = delta < -0.001;

                    return (
                      <div key={h.id} style={{ backgroundColor: '#ffffff', padding: '14px 18px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <div>
                            <strong>{h.id}</strong>: <span style={{ color: 'var(--text-muted)' }}>{h.name}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-subtle)' }}>
                              Prior: {(prior * 100).toFixed(1)}%
                            </span>
                            <span style={{ fontSize: '1rem', fontWeight: 700 }}>
                              &rarr; Posterior: {(posterior * 100).toFixed(1)}%
                            </span>
                            <span
                              className="mono"
                              style={{
                                fontSize: '0.85rem',
                                fontWeight: 700,
                                color: isPositive ? 'var(--accent-emerald)' : isNegative ? 'var(--accent-rose)' : 'var(--text-subtle)',
                              }}
                            >
                              ({delta > 0 ? '+' : ''}{(delta * 100).toFixed(1)}%)
                            </span>
                          </div>
                        </div>

                        {/* Bar comparison */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div style={{ display: 'flex', height: '8px', backgroundColor: 'var(--bg-surface-alt)', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{ width: `${prior * 100}%`, backgroundColor: '#64748b' }} title="Prior" />
                          </div>
                          <div style={{ display: 'flex', height: '12px', backgroundColor: 'var(--bg-surface-alt)', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{ width: `${posterior * 100}%`, backgroundColor: isPositive ? 'var(--accent-emerald)' : 'var(--brand-primary)' }} title="Posterior" />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Apply button to take a step in the sequential path */}
                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleApplyOutcomeAsSequentialStep}
                    disabled={analyzing}
                  >
                    Apply Outcome as Sequential Discovery Step &rarr;
                  </button>
                </div>
              </div>
            )}

            {/* Step History Log if sequential steps applied */}
            {executionHistory.length > 0 && (
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '20px' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px' }}>
                  Simulated Sequential Discovery Trajectory ({executionHistory.length} Steps Completed)
                </h4>

                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ fontSize: '0.85rem' }}>
                    <thead>
                      <tr>
                        <th>Step</th>
                        <th>Assay</th>
                        <th>Observed Outcome</th>
                        <th>Entropy Before</th>
                        <th>Entropy After</th>
                        <th>Realized Info Gain</th>
                        <th>Step Cost</th>
                        <th>Cumulative Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {executionHistory.map(s => (
                        <tr key={s.stepNumber}>
                          <td><strong>#{s.stepNumber}</strong></td>
                          <td>{s.experimentId} ({s.experimentName})</td>
                          <td><span className="badge badge-indigo">{s.observedOutcome}</span></td>
                          <td><span className="mono">{s.priorEntropy.toFixed(4)} b</span></td>
                          <td><span className="mono">{s.posteriorEntropy.toFixed(4)} b</span></td>
                          <td><span className="mono" style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>+{s.informationGain.toFixed(4)} b</span></td>
                          <td>{s.stepCost.toFixed(1)}</td>
                          <td><strong>{s.cumulativeCost.toFixed(1)}</strong></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="btn btn-secondary" onClick={() => setCurrentStage('rankings')}>
              &larr; Back to Rankings
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
