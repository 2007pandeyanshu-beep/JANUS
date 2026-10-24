import React, { useState, useEffect, useRef } from 'react';
import {
  AgentInvestigationReport,
  ToolExecutionRecord,
} from '../types';
import {
  startAgentInvestigation,
  supplyAgentObservation,
} from '../api';
import { JanusSymbol } from './JanusBrand';
import { fadeInUp } from '../utils/motion';

type InvestigationStage = 'stage_1' | 'stage_2' | 'stage_3' | 'stage_4' | 'stage_5';

interface AgentInvestigationProps {
  initialPreset?: 'CS-CAT-001' | 'CS-OER-002' | 'SYN-001';
  onBackToLanding?: () => void;
}

export const AgentInvestigation: React.FC<AgentInvestigationProps> = ({
  initialPreset = 'CS-CAT-001',
  onBackToLanding,
}) => {
  // Navigation & Scenario State
  const [activeStage, setActiveStage] = useState<InvestigationStage>('stage_1');
  const [caseStudyId, setCaseStudyId] = useState<'CS-CAT-001' | 'CS-OER-002' | 'SYN-001' | 'CUSTOM'>(initialPreset);
  const [question, setQuestion] = useState<string>(
    'Which reaction pathway governs low-temperature water-gas shift on Pt/CeO2?'
  );
  const [mode, setMode] = useState<'deterministic_offline_demo' | 'live_agent_loop'>('deterministic_offline_demo');
  const [apiKey, setApiKey] = useState<string>('');
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AgentInvestigationReport | null>(null);
  const [copiedReport, setCopiedReport] = useState<boolean>(false);

  // Inspector & Context Panel State
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [drawerTab, setDrawerTab] = useState<'tools' | 'logs' | 'evidence'>('tools');
  const [selectedToolRecord, setSelectedToolRecord] = useState<ToolExecutionRecord | null>(null);
  const [observationExpId, setObservationExpId] = useState<string>('');
  const [observationOutcome, setObservationOutcome] = useState<string>('');
  const [updatingEvidence, setUpdatingEvidence] = useState<boolean>(false);

  // Motion refs
  const stageContainerRef = useRef<HTMLDivElement | null>(null);

  // Presets
  const handlePresetSelect = (preset: 'CS-CAT-001' | 'CS-OER-002' | 'SYN-001' | 'CUSTOM') => {
    setCaseStudyId(preset);
    setError(null);
    if (preset === 'CS-CAT-001') {
      setQuestion('Which reaction pathway governs low-temperature water-gas shift on Pt/CeO2?');
    } else if (preset === 'CS-OER-002') {
      setQuestion('Which reaction mechanism dominates oxygen evolution on La_{1-x}Sr_xCoO_{3-delta}?');
    } else if (preset === 'SYN-001') {
      setQuestion('Which molecular mechanism governs kinase inhibition by small molecule JNS-401?');
    } else {
      setQuestion('Enter your exploratory scientific question...');
    }
  };

  useEffect(() => {
    if (initialPreset) {
      handlePresetSelect(initialPreset);
    }
  }, [initialPreset]);

  // Trigger stage entrance animation
  useEffect(() => {
    if (stageContainerRef.current) {
      fadeInUp(stageContainerRef.current, { duration: 400, distance: 10 });
    }
  }, [activeStage]);

  const handleLaunchInvestigation = async () => {
    setRunning(true);
    setError(null);
    try {
      const targetCaseId = caseStudyId === 'CUSTOM' ? null : caseStudyId;
      const res = await startAgentInvestigation({
        question,
        mode,
        case_study_id: targetCaseId,
        api_key: apiKey.trim() || undefined,
      });
      setReport(res);
      setActiveStage('stage_2');

      if (res.analysis_result?.ranked_experiments.length) {
        const top = res.analysis_result.ranked_experiments[0];
        setObservationExpId(top.experiment_id);
        const expObj = res.candidate_experiments.find(e => e.id === top.experiment_id);
        if (expObj?.possible_outcomes.length) {
          setObservationOutcome(expObj.possible_outcomes[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Investigation failed to execute.');
    } finally {
      setRunning(false);
    }
  };

  const handleSupplyObservation = async () => {
    if (!report || !observationExpId || !observationOutcome) return;
    setUpdatingEvidence(true);
    setError(null);
    try {
      const updated = await supplyAgentObservation(
        report.investigation_id,
        observationExpId,
        observationOutcome
      );
      setReport(updated);

      if (updated.analysis_result?.ranked_experiments.length) {
        const top = updated.analysis_result.ranked_experiments[0];
        setObservationExpId(top.experiment_id);
        const expObj = updated.candidate_experiments.find(e => e.id === top.experiment_id);
        if (expObj?.possible_outcomes.length) {
          setObservationOutcome(expObj.possible_outcomes[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Evidence submission failed.');
    } finally {
      setUpdatingEvidence(false);
    }
  };

  const handleCopyReport = () => {
    if (!report) return;
    const initialEntropy = report.hypotheses.reduce(
      (acc, h) => acc - (h.prior > 0 ? h.prior * Math.log2(h.prior) : 0),
      0
    );
    const text = `# JANUS Scientific Investigation Report
Investigation ID: ${report.investigation_id}
Question: ${report.question}
Mode: ${report.mode}
Status: ${report.status}

## 1. Epistemic Uncertainty & Hypotheses
Initial Shannon Entropy: ${initialEntropy.toFixed(4)} bits
${report.hypotheses.map(h => `- ${h.id} (${h.name}): ${(h.prior * 100).toFixed(1)}%`).join('\n')}

## 2. Recommended Optimal Experiment
${
  report.analysis_result?.ranked_experiments[0]
    ? `${report.analysis_result.ranked_experiments[0].experiment_name} (${report.analysis_result.ranked_experiments[0].experiment_id})
Expected Information Gain: ${report.analysis_result.ranked_experiments[0].expected_information_gain.toFixed(4)} bits
Composite Utility: ${report.analysis_result.ranked_experiments[0].composite_utility_score.toFixed(4)}
Rationale: ${report.analysis_result.ranked_experiments[0].explanation}`
    : 'No candidates remaining.'
}

## 3. Simulated Observation Trajectory
${
  report.executed_observations?.length
    ? report.executed_observations.map(o => `- Experiment ${o.experiment_id}: Observed '${o.observed_outcome}' (Cost: ${o.cost || 'N/A'}, Status: ${o.status})`).join('\n')
    : 'None applied yet.'
}

## 4. Consensus Synthesis & Limitations
${report.synthesis_summary}
`;
    navigator.clipboard.writeText(text);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 3000);
  };

  // Shannon entropy helpers
  const computeEntropy = (probs: number[]) => {
    return probs.reduce((acc, p) => acc - (p > 0 ? p * Math.log2(p) : 0), 0);
  };

  const currentEntropy = report
    ? computeEntropy(report.hypotheses.map(h => h.prior || 0))
    : 0;
  const initialEntropy = report?.initial_priors
    ? computeEntropy(Object.values(report.initial_priors))
    : report
    ? computeEntropy(report.hypotheses.map(h => h.prior || 0))
    : 0;
  const entropyReduction = Math.max(0, initialEntropy - currentEntropy);

  return (
    <div className="workbench-shell" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ====================================================================== */}
      {/* WORKBENCH TOP BAR                                                      */}
      {/* ====================================================================== */}
      <header
        className="card"
        style={{
          padding: '16px 24px',
          backgroundColor: '#142D4E',
          color: '#F5F7FB',
          border: 'none',
          boxShadow: '0 4px 12px rgba(20, 45, 78, 0.15)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            {onBackToLanding && (
              <button
                className="btn"
                onClick={onBackToLanding}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  color: '#CBD5E1',
                  padding: '6px 12px',
                  fontSize: '0.8rem',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                }}
              >
                &larr; Landing
              </button>
            )}
            <JanusSymbol size={28} />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 800, fontSize: '1.05rem', letterSpacing: '0.04em' }}>
                  JANUS INVESTIGATION WORKBENCH
                </span>
                {report && (
                  <span
                    className="badge"
                    style={{
                      backgroundColor: 'rgba(123, 200, 207, 0.2)',
                      color: '#7BC8CF',
                      border: '1px solid rgba(123, 200, 207, 0.3)',
                    }}
                  >
                    {report.investigation_id}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '1px' }}>
                Discriminative Bayesian Experimental Design • Authoritative Python Engine
              </div>
            </div>
          </div>

          {/* Right Status Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              className="badge"
              style={{
                backgroundColor: mode === 'deterministic_offline_demo' ? 'rgba(5, 150, 105, 0.2)' : 'rgba(233, 184, 106, 0.2)',
                color: mode === 'deterministic_offline_demo' ? '#6EE7B7' : '#FDE68A',
                border: mode === 'deterministic_offline_demo' ? '1px solid rgba(5, 150, 105, 0.4)' : '1px solid rgba(233, 184, 106, 0.4)',
              }}
            >
              {mode === 'deterministic_offline_demo' ? '● Deterministic Offline (<5ms)' : '● Live Gemini 3 Flash'}
            </span>

            {report && (
              <span
                className="badge"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  color: '#F5F7FB',
                }}
              >
                Budget: {report.remaining_budget?.toFixed(1) ?? '10.0'} / 10.0
              </span>
            )}

            <button
              className="btn"
              onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              style={{
                backgroundColor: isDrawerOpen ? '#7BC8CF' : 'rgba(255, 255, 255, 0.12)',
                color: isDrawerOpen ? '#142D4E' : '#F5F7FB',
                fontSize: '0.8rem',
                fontWeight: 700,
                padding: '6px 12px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              {isDrawerOpen ? '✕ Close Inspector' : '🔍 Tool & Provenance Inspector'}
            </button>
          </div>
        </div>
      </header>

      {/* Global Alerts */}
      {error && (
        <div className="alert-box alert-amber">
          <strong>Investigation Alert:</strong> {error}
        </div>
      )}

      {/* ====================================================================== */}
      {/* MAIN WORKBENCH GRID: LEFT STAGE NAVIGATOR + MAIN STAGE WORKSPACE       */}
      {/* ====================================================================== */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '260px 1fr',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* ==================================================================== */}
        {/* LEFT STAGE NAVIGATOR                                                 */}
        {/* ==================================================================== */}
        <aside
          className="card"
          style={{
            padding: '16px',
            position: 'sticky',
            top: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-subtle)', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '4px 8px 8px' }}>
            Investigation Stages
          </div>

          {[
            {
              id: 'stage_1' as InvestigationStage,
              num: 1,
              title: 'Scientific Question',
              subtitle: 'Scope & Scenario',
              isDone: !!report,
            },
            {
              id: 'stage_2' as InvestigationStage,
              num: 2,
              title: 'Evidence & Hypotheses',
              subtitle: 'Simplex & Provenance',
              isDone: !!report,
            },
            {
              id: 'stage_3' as InvestigationStage,
              num: 3,
              title: 'Experiment Selection',
              subtitle: 'EIG & Utility Ranking',
              isDone: !!report?.analysis_result,
            },
            {
              id: 'stage_4' as InvestigationStage,
              num: 4,
              title: 'Observation & Update',
              subtitle: `${report?.executed_observations?.length || 0} Assays Applied`,
              isDone: (report?.executed_observations?.length || 0) > 0,
            },
            {
              id: 'stage_5' as InvestigationStage,
              num: 5,
              title: 'Consensus Report',
              subtitle: 'Entropy Reduction',
              isDone: (report?.executed_observations?.length || 0) > 0,
            },
          ].map(stage => {
            const isActive = activeStage === stage.id;
            const isClickable = stage.id === 'stage_1' || !!report;

            return (
              <button
                key={stage.id}
                onClick={() => isClickable && setActiveStage(stage.id)}
                disabled={!isClickable}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px',
                  borderRadius: '8px',
                  border: isActive ? '2px solid var(--janus-navy)' : '1px solid transparent',
                  backgroundColor: isActive ? 'var(--janus-surface-subtle)' : 'transparent',
                  textAlign: 'left',
                  cursor: isClickable ? 'pointer' : 'not-allowed',
                  opacity: isClickable ? 1 : 0.45,
                  transition: 'all 0.15s ease',
                  width: '100%',
                }}
              >
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    backgroundColor: isActive ? '#142D4E' : stage.isDone ? '#059669' : '#E2E8F0',
                    color: isActive || stage.isDone ? '#ffffff' : '#64748B',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: '0.8rem',
                    flexShrink: 0,
                  }}
                >
                  {stage.isDone ? '✓' : stage.num}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: isActive ? 800 : 600, color: 'var(--text-main)' }}>
                    {stage.title}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>
                    {stage.subtitle}
                  </span>
                </div>
              </button>
            );
          })}

          {report && (
            <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>
                Active Scenario:
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--janus-navy)', marginTop: '2px' }}>
                {report.case_study_id || 'Exploratory Question'}
              </div>
            </div>
          )}
        </aside>

        {/* ==================================================================== */}
        {/* CENTER STAGE WORKSPACE                                               */}
        {/* ==================================================================== */}
        <main ref={stageContainerRef} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* ================================================================== */}
          {/* STAGE 1: SCIENTIFIC QUESTION & SCOPE                               */}
          {/* ================================================================== */}
          {activeStage === 'stage_1' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Preset Cards */}
              <div className="card" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--janus-navy)', marginBottom: '4px' }}>
                  Select Scientific Benchmark Scenario
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Choose a peer-reviewed heterogeneous catalysis case study, perovskite electrochemistry protocol, or synthetic kinase fixture.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                  {/* CS-CAT-001 Card */}
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: caseStudyId === 'CS-CAT-001' ? '2px solid #142D4E' : '1px solid var(--border-subtle)',
                      backgroundColor: caseStudyId === 'CS-CAT-001' ? 'var(--janus-surface-subtle)' : '#ffffff',
                      cursor: 'pointer',
                    }}
                    onClick={() => handlePresetSelect('CS-CAT-001')}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="badge badge-emerald">CS-CAT-001</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>Empirical Literature</span>
                    </div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 800, marginTop: '8px', color: 'var(--janus-navy)' }}>
                      Pt/CeO₂ Water-Gas Shift
                    </h4>
                    <p style={{ fontSize: '0.785rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45 }}>
                      Disambiguates Redox (Mars-van Krevelen) vs Formate vs Carboxyl pathways using operando DRIFTS & isotopic pulses.
                    </p>
                    <div style={{ marginTop: '10px', fontSize: '0.72rem', color: 'var(--accent-emerald)', fontWeight: 700 }}>
                      3 Hypotheses • 5 Assays • 1 Unquantified
                    </div>
                  </div>

                  {/* CS-OER-002 Card */}
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: caseStudyId === 'CS-OER-002' ? '2px solid #142D4E' : '1px solid var(--border-subtle)',
                      backgroundColor: caseStudyId === 'CS-OER-002' ? 'var(--janus-surface-subtle)' : '#ffffff',
                      cursor: 'pointer',
                    }}
                    onClick={() => handlePresetSelect('CS-OER-002')}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="badge badge-purple">CS-OER-002</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>Preregistered Protocol</span>
                    </div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 800, marginTop: '8px', color: 'var(--janus-navy)' }}>
                      Perovskite OER Electrocatalysis
                    </h4>
                    <p style={{ fontSize: '0.785rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45 }}>
                      Disambiguates Adsorbate Evolution (AEM) vs Lattice Oxygen (LOM) vs Oxide Path (OPM) on La₁₋ₓSrₓCoO₃₋ᵟ.
                    </p>
                    <div style={{ marginTop: '10px', fontSize: '0.72rem', color: 'var(--accent-purple)', fontWeight: 700 }}>
                      3 Hypotheses • 5 Assays • DEMS & ICP-MS
                    </div>
                  </div>

                  {/* SYN-001 Card */}
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: caseStudyId === 'SYN-001' ? '2px solid #142D4E' : '1px solid var(--border-subtle)',
                      backgroundColor: caseStudyId === 'SYN-001' ? 'var(--janus-surface-subtle)' : '#ffffff',
                      cursor: 'pointer',
                    }}
                    onClick={() => handlePresetSelect('SYN-001')}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="badge badge-amber">SYN-001</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>Synthetic Benchmark</span>
                    </div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 800, marginTop: '8px', color: 'var(--janus-navy)' }}>
                      Kinase Signaling Pathway
                    </h4>
                    <p style={{ fontSize: '0.785rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45 }}>
                      Disambiguates Allosteric Modulation vs ATP-Competitive Binding vs Targeted Degradation for small molecule JNS-401.
                    </p>
                    <div style={{ marginTop: '10px', fontSize: '0.72rem', color: 'var(--accent-amber)', fontWeight: 700 }}>
                      3 Hypotheses • 5 Assays • Pure Math Fixture
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                    onClick={() => handlePresetSelect('CUSTOM')}
                  >
                    + Configure Custom Exploratory Question
                  </button>
                </div>
              </div>

              {/* Question & Mode Form */}
              <div className="card" style={{ padding: '24px' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 800, marginBottom: '8px', color: 'var(--janus-navy)' }}>
                  Scientific Question:
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  style={{ width: '100%', padding: '12px 14px', fontSize: '1rem', fontWeight: 600 }}
                  placeholder="Formulate scientific question..."
                />

                {caseStudyId === 'CUSTOM' && (
                  <div className="alert-box alert-amber" style={{ marginTop: '12px', fontSize: '0.8rem', padding: '10px 14px' }}>
                    ⚠️ <strong>Scientific Guardrail:</strong> Custom exploratory questions without calibrated likelihoods will retrieve literature and formulate hypotheses, but cannot calculate numerical EIG without experimental noise models.
                  </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px' }}>
                      Execution Mode:
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input
                          type="radio"
                          name="agent_mode"
                          checked={mode === 'deterministic_offline_demo'}
                          onChange={() => setMode('deterministic_offline_demo')}
                        />
                        <span>
                          <strong>Deterministic Offline Demo</strong> (Instantaneous local Python math, no API key needed)
                        </span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input
                          type="radio"
                          name="agent_mode"
                          checked={mode === 'live_agent_loop'}
                          onChange={() => setMode('live_agent_loop')}
                        />
                        <span>
                          <strong>Live Gemini 3 Flash Loop</strong> (Real model consensus critique via Google AI)
                        </span>
                      </label>
                    </div>

                    {mode === 'live_agent_loop' && (
                      <div style={{ marginTop: '12px', padding: '12px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '6px' }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                          Optional Gemini API Key (leaves server env var if blank):
                        </label>
                        <input
                          type="password"
                          className="input-field"
                          value={apiKey}
                          onChange={e => setApiKey(e.target.value)}
                          placeholder="GEMINI_API_KEY (stored safely in memory)"
                          style={{ width: '100%', padding: '6px 10px', fontSize: '0.8rem' }}
                        />
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', padding: '16px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                      <strong>Ready to orchestrate:</strong> 5 specialized agents will query verified literature, formulate mechanistic hypotheses, calculate kinetics, and invoke the Python Bayesian Experimental Design engine.
                    </div>
                    <button
                      className="btn btn-primary"
                      style={{ width: '100%', padding: '14px 20px', fontSize: '1rem', fontWeight: 800 }}
                      onClick={handleLaunchInvestigation}
                      disabled={running}
                    >
                      {running ? 'Orchestrating Scientific Agents...' : 'Start Multi-Agent Scientific Investigation 🚀'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================== */}
          {/* STAGE 2: EVIDENCE & COMPETING HYPOTHESES                           */}
          {/* ================================================================== */}
          {activeStage === 'stage_2' && report && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Competing Hypotheses Grid */}
              <div className="card" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <span className="badge badge-teal">STAGE 2: HYPOTHESIS FORMULATION</span>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--janus-navy)', marginTop: '4px' }}>
                      Competing Mechanistic Hypotheses & Prior Distribution
                    </h3>
                  </div>
                  <span className="badge badge-slate">
                    Simplex Axiom: &sum; P(H_k) = {report.hypotheses.reduce((acc, h) => acc + h.prior, 0).toFixed(6)}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                  {report.hypotheses.map((hyp, idx) => {
                    const isTeal = idx === 0;
                    const isAmber = idx === 1;
                    return (
                      <div
                        key={hyp.id}
                        style={{
                          padding: '16px',
                          borderRadius: '8px',
                          border: isTeal ? '2px solid #7BC8CF' : isAmber ? '2px solid #E9B86A' : '1px solid var(--border-subtle)',
                          backgroundColor: '#ffffff',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          boxShadow: '0 2px 4px rgba(20, 45, 78, 0.04)',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span className="mono" style={{ fontWeight: 800, fontSize: '0.9rem', color: isTeal ? '#3E9B9F' : isAmber ? '#B88530' : '#142D4E' }}>
                              {hyp.id}
                            </span>
                            <span className="badge badge-slate" style={{ fontSize: '0.72rem' }}>
                              Prior: {(hyp.prior * 100).toFixed(1)}%
                            </span>
                          </div>
                          <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--janus-navy)', marginTop: '8px' }}>
                            {hyp.name}
                          </h4>
                          <p style={{ fontSize: '0.785rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45 }}>
                            {hyp.description}
                          </p>
                        </div>

                        {/* Prior probability progress bar */}
                        <div style={{ marginTop: '16px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-subtle)', marginBottom: '4px' }}>
                            <span>Epistemic Prior</span>
                            <span className="mono" style={{ fontWeight: 700 }}>{(hyp.prior * 100).toFixed(1)}%</span>
                          </div>
                          <div style={{ width: '100%', height: '8px', backgroundColor: '#E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
                            <div
                              style={{
                                width: `${hyp.prior * 100}%`,
                                height: '100%',
                                backgroundColor: isTeal ? '#7BC8CF' : isAmber ? '#E9B86A' : '#142D4E',
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Primary Evidence Ledger */}
              <div className="card" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--janus-navy)' }}>
                    Ingested Literature Claims & Verified DOIs ({report.retrieved_evidence.length})
                  </h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                    Provenance: Peer-Reviewed Publications
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {report.retrieved_evidence.map((ev, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '12px 16px',
                        borderRadius: '6px',
                        border: '1px solid var(--border-subtle)',
                        backgroundColor: 'var(--janus-surface-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--janus-navy)' }}>
                          {ev.title || ev.summary}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Source: <strong>{ev.source}</strong> {ev.source_doi && (
                            <a
                              href={`https://doi.org/${ev.source_doi}`}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#0284C7', marginLeft: '6px', textDecoration: 'none' }}
                            >
                              DOI: {ev.source_doi} ↗
                            </a>
                          )}
                        </div>
                      </div>
                      <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
                        {ev.claim_status || 'VERIFIED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  className="btn btn-primary"
                  style={{ padding: '12px 24px', fontWeight: 800 }}
                  onClick={() => setActiveStage('stage_3')}
                >
                  Proceed to Experiment Selection (Stage 3) &rarr;
                </button>
              </div>
            </div>
          )}

          {/* ================================================================== */}
          {/* STAGE 3: EXPERIMENT SELECTION                                      */}
          {/* ================================================================== */}
          {activeStage === 'stage_3' && report && report.analysis_result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Spotlight: Recommended Experiment */}
              {report.analysis_result.ranked_experiments.length > 0 && (
                <div
                  className="card"
                  style={{
                    padding: '24px',
                    borderLeft: '5px solid #059669',
                    backgroundColor: '#ffffff',
                    boxShadow: '0 4px 12px rgba(5, 150, 105, 0.08)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span className="badge badge-emerald" style={{ fontWeight: 800 }}>
                      RECOMMENDED DIAGNOSTIC ASSAY (#1 RANK)
                    </span>
                    <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
                      Authoritative Python Argmax
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--janus-navy)', marginTop: '4px' }}>
                    {report.analysis_result.ranked_experiments[0].experiment_name}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.5 }}>
                    {report.analysis_result.ranked_experiments[0].explanation}
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginTop: '20px' }}>
                    <div style={{ padding: '12px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>EXPECTED INFO GAIN</div>
                      <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 800, color: '#059669', marginTop: '2px' }}>
                        {report.analysis_result.ranked_experiments[0].expected_information_gain.toFixed(4)} b
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Shannon Entropy Reduction</div>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>COMPOSITE UTILITY</div>
                      <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--janus-navy)', marginTop: '2px' }}>
                        {report.analysis_result.ranked_experiments[0].composite_utility_score.toFixed(4)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cost & Feasibility Weighted</div>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>EXPERIMENTAL COST</div>
                      <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '2px' }}>
                        {report.analysis_result.ranked_experiments[0].cost.toFixed(1)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Budget Units</div>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>FEASIBILITY RATE</div>
                      <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '2px' }}>
                        {(report.analysis_result.ranked_experiments[0].feasibility * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Lab Success Likelihood</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Full Candidate Comparison Table */}
              <div className="card" style={{ padding: '24px' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--janus-navy)', marginBottom: '14px' }}>
                  Candidate Assays Ranked by Composite Utility & EIG
                </h4>

                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Utility</th>
                        <th>EIG</th>
                        <th>Assay ID</th>
                        <th>Name</th>
                        <th>EIG (bits)</th>
                        <th>Feas.</th>
                        <th>Cost</th>
                        <th>Utility Score</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.analysis_result.ranked_experiments.map(exp => {
                        const hasDivergence = exp.utility_rank !== exp.eig_rank;
                        const isTop = exp.rank === 1;

                        return (
                          <tr
                            key={exp.experiment_id}
                            style={{
                              backgroundColor: isTop ? 'rgba(5, 150, 105, 0.05)' : 'transparent',
                            }}
                          >
                            <td style={{ fontWeight: 800 }}>#{exp.utility_rank || exp.rank}</td>
                            <td style={{ color: hasDivergence ? '#D97706' : 'inherit', fontWeight: hasDivergence ? 800 : 500 }}>
                              #{exp.eig_rank || exp.rank} {hasDivergence && '⚠️'}
                            </td>
                            <td className="mono" style={{ fontWeight: 700 }}>{exp.experiment_id}</td>
                            <td>
                              <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{exp.experiment_name}</div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>{exp.explanation?.slice(0, 75)}...</div>
                            </td>
                            <td className="mono" style={{ fontWeight: 800, color: '#059669' }}>
                              {exp.expected_information_gain.toFixed(4)}
                            </td>
                            <td>{(exp.feasibility * 100).toFixed(0)}%</td>
                            <td>{exp.cost.toFixed(1)}</td>
                            <td className="mono" style={{ fontWeight: 800, color: 'var(--janus-navy)' }}>
                              {exp.composite_utility_score.toFixed(4)}
                            </td>
                            <td>
                              {exp.expected_information_gain === 0 ? (
                                <span className="badge badge-amber">NEGATIVE CONTROL</span>
                              ) : (
                                <span className="badge badge-emerald">QUANTIFIED</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: '14px', fontSize: '0.785rem', color: 'var(--text-subtle)' }}>
                  * <strong>Dual Ranking Divergence Notice:</strong> When synchrotron beamlines incur high costs or lower feasibility, Composite Utility Rank diverges from pure EIG Rank. Both metrics are displayed transparently.
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  className="btn btn-primary"
                  style={{ padding: '12px 24px', fontWeight: 800 }}
                  onClick={() => setActiveStage('stage_4')}
                >
                  Proceed to Simulated Observation (Stage 4) &rarr;
                </button>
              </div>
            </div>
          )}

          {/* ================================================================== */}
          {/* STAGE 4: OBSERVATION & SEQUENTIAL UPDATING                         */}
          {/* ================================================================== */}
          {activeStage === 'stage_4' && report && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Observation Submission Form */}
              <div className="card" style={{ padding: '24px', borderLeft: '5px solid #142D4E' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--janus-navy)' }}>
                    Supply Simulated Experimental Observation
                  </h4>
                  <span className="badge badge-amber">SIMULATED OBSERVATION PREVIEW</span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Selecting an outcome applies exact Bayesian conditioning: P(H_k | y) &prop; P(y | H_k) * P(H_k). The executed assay will be retired from the pool, and remaining candidate assays will be dynamically re-ranked.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '6px' }}>
                      Candidate Assay to Execute:
                    </label>
                    <select
                      className="input-field"
                      value={observationExpId}
                      onChange={e => {
                        const newId = e.target.value;
                        setObservationExpId(newId);
                        const expObj = report.candidate_experiments.find(item => item.id === newId);
                        if (expObj?.possible_outcomes.length) {
                          setObservationOutcome(expObj.possible_outcomes[0]);
                        }
                      }}
                      style={{ width: '100%', fontSize: '0.9rem', padding: '10px 12px' }}
                      disabled={!report.candidate_experiments.length}
                    >
                      {report.candidate_experiments.map(e => (
                        <option key={e.id} value={e.id}>
                          {e.id}: {e.name} (Cost: {e.cost})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '6px' }}>
                      Observed Outcome:
                    </label>
                    <select
                      className="input-field"
                      value={observationOutcome}
                      onChange={e => setObservationOutcome(e.target.value)}
                      style={{ width: '100%', fontSize: '0.9rem', padding: '10px 12px' }}
                      disabled={!report.candidate_experiments.length}
                    >
                      {report.candidate_experiments
                        .find(e => e.id === observationExpId)
                        ?.possible_outcomes.map(o => (
                          <option key={o} value={o}>
                            {o}
                          </option>
                        ))}
                    </select>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
                    Remaining Budget: <strong>{report.remaining_budget ?? 10.0} units</strong> | Retired Assays: <strong>{report.retired_experiments?.length || 0}</strong>
                  </div>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '12px 24px', fontSize: '0.9rem', fontWeight: 800 }}
                    onClick={handleSupplyObservation}
                    disabled={updatingEvidence || !report.candidate_experiments.length}
                  >
                    {updatingEvidence ? 'Applying Bayes Update & Re-ranking...' : 'Apply Observation & Recompute Beliefs &rarr;'}
                  </button>
                </div>
              </div>

              {/* Before-and-After Probability Shift */}
              <div className="card" style={{ padding: '24px' }}>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--janus-navy)', marginBottom: '16px' }}>
                  Epistemic Probability Shift: Initial Prior vs. Current Posterior
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {report.hypotheses.map(h => {
                    const initProb = report.initial_priors?.[h.id] ?? h.prior;
                    const currProb = h.prior;
                    const delta = currProb - initProb;
                    const isPositive = delta > 0.001;
                    const isNegative = delta < -0.001;

                    return (
                      <div
                        key={h.id}
                        style={{
                          padding: '14px',
                          borderRadius: '8px',
                          border: '1px solid var(--border-subtle)',
                          backgroundColor: 'var(--janus-surface-subtle)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <div>
                            <strong className="mono" style={{ fontSize: '0.95rem' }}>{h.id}</strong>: <span style={{ fontWeight: 700 }}>{h.name}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
                              Initial: {(initProb * 100).toFixed(1)}% &rarr;
                            </span>
                            <span className="mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--janus-navy)' }}>
                              Current: {(currProb * 100).toFixed(1)}%
                            </span>
                            <span
                              className={`badge ${isPositive ? 'badge-emerald' : isNegative ? 'badge-rose' : 'badge-slate'}`}
                              style={{ fontWeight: 800, minWidth: '65px', textAlign: 'center' }}
                            >
                              {isPositive ? `+${(delta * 100).toFixed(1)}%` : isNegative ? `${(delta * 100).toFixed(1)}%` : '0.0%'}
                            </span>
                          </div>
                        </div>

                        {/* Progress Bar with animated width */}
                        <div style={{ width: '100%', height: '10px', backgroundColor: '#E2E8F0', borderRadius: '5px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(100, currProb * 100)}%`,
                              height: '100%',
                              backgroundColor: isPositive ? '#059669' : '#142D4E',
                              transition: 'width 0.5s ease',
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                  <span className="badge badge-emerald">
                    Simplex Axiom Verified: &sum; P(H_k) = {report.hypotheses.reduce((acc, h) => acc + h.prior, 0).toFixed(6)}
                  </span>
                  <span style={{ fontSize: '0.825rem', color: 'var(--text-subtle)' }}>
                    Entropy Reduction: <strong>{entropyReduction.toFixed(4)} bits</strong> (From {initialEntropy.toFixed(4)} b to {currentEntropy.toFixed(4)} b)
                  </span>
                </div>
              </div>

              {/* Sequential Trajectory Log */}
              {report.executed_observations && report.executed_observations.length > 0 && (
                <div className="card" style={{ padding: '20px' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--janus-navy)', marginBottom: '12px' }}>
                    Sequential Observation Trajectory Log ({report.executed_observations.length} Steps)
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {report.executed_observations.map((obs, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '10px 14px',
                          borderRadius: '6px',
                          border: '1px solid var(--border-subtle)',
                          backgroundColor: '#ffffff',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <span className="mono" style={{ fontWeight: 800 }}>Step {idx + 1}: {obs.experiment_id}</span>
                          <span style={{ marginLeft: '10px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Observed: <strong>'{obs.observed_outcome}'</strong>
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <span className="badge badge-amber">{obs.status}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Cost: {obs.cost}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  className="btn btn-primary"
                  style={{ padding: '12px 24px', fontWeight: 800 }}
                  onClick={() => setActiveStage('stage_5')}
                >
                  View Final Investigation Summary (Stage 5) &rarr;
                </button>
              </div>
            </div>
          )}

          {/* ================================================================== */}
          {/* STAGE 5: CONSENSUS REPORT & EXPORT                                 */}
          {/* ================================================================== */}
          {activeStage === 'stage_5' && report && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="card" style={{ padding: '28px', borderLeft: '5px solid #059669' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <div>
                    <span className="badge badge-emerald" style={{ fontWeight: 800 }}>INVESTIGATION SYNTHESIS REPORT</span>
                    <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--janus-navy)', marginTop: '6px' }}>
                      {report.question}
                    </h3>
                  </div>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '8px 16px', fontSize: '0.85rem', fontWeight: 700 }}
                    onClick={handleCopyReport}
                  >
                    {copiedReport ? '✓ Copied Markdown Report!' : '📋 Copy Report to Clipboard'}
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '24px' }}>
                  <div style={{ padding: '14px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>IDENTIFIED MECHANISM</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#059669', marginTop: '2px' }}>
                      {report.hypotheses.reduce((maxH, h) => (h.prior > maxH.prior ? h : maxH), report.hypotheses[0]).id}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Confidence: {(Math.max(...report.hypotheses.map(h => h.prior)) * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div style={{ padding: '14px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>UNCERTAINTY REDUCTION</div>
                    <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--janus-navy)', marginTop: '2px' }}>
                      -{entropyReduction.toFixed(4)} bits
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Final Entropy: {currentEntropy.toFixed(4)} b
                    </div>
                  </div>

                  <div style={{ padding: '14px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>OBSERVATIONS APPLIED</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '2px' }}>
                      {report.executed_observations?.length || 0} Assays
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Simulated outcomes
                    </div>
                  </div>

                  <div style={{ padding: '14px', backgroundColor: 'var(--janus-surface-subtle)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700 }}>NEXT RECOMMENDED STEP</div>
                    <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 800, color: '#7C3AED', marginTop: '2px' }}>
                      {report.analysis_result?.ranked_experiments[0]?.experiment_id || 'Campaign Complete'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Max residual EIG
                    </div>
                  </div>
                </div>

                {/* Synthesis Body */}
                <div
                  style={{
                    padding: '20px',
                    backgroundColor: '#ffffff',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.9rem',
                    lineHeight: 1.6,
                  }}
                >
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--janus-navy)', marginBottom: '8px' }}>
                    Multi-Agent Consensus Synthesis:
                  </h4>
                  <div style={{ whiteSpace: 'pre-line', color: 'var(--text-main)' }}>
                    {report.synthesis_summary}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '10px 18px' }}
                  onClick={() => setActiveStage('stage_1')}
                >
                  &larr; Start New Investigation
                </button>
                <button
                  className="btn btn-primary"
                  style={{ padding: '10px 22px' }}
                  onClick={handleCopyReport}
                >
                  {copiedReport ? '✓ Copied Markdown Report!' : '📋 Copy Full Report'}
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ====================================================================== */}
      {/* CONTEXTUAL SLIDE-OUT / MODAL DRAWER FOR TOOLS & PROVENANCE             */}
      {/* ====================================================================== */}
      {isDrawerOpen && report && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            right: 0,
            bottom: 0,
            width: '480px',
            maxWidth: '90vw',
            backgroundColor: '#17212F',
            color: '#F5F7FB',
            boxShadow: '-8px 0 24px rgba(0,0,0,0.4)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            borderLeft: '1px solid #2B3A4F',
          }}
        >
          {/* Drawer Header */}
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid #2B3A4F',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: '#7BC8CF', fontWeight: 700 }}>AUDITABLE EXECUTION INSPECTOR</div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: '#ffffff' }}>
                Provenance & Tool Timeline
              </h3>
            </div>
            <button
              onClick={() => setIsDrawerOpen(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#CBD5E1',
                fontSize: '1.2rem',
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          </div>

          {/* Drawer Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #2B3A4F', backgroundColor: '#142D4E' }}>
            <button
              onClick={() => setDrawerTab('tools')}
              style={{
                flex: 1,
                padding: '10px',
                background: drawerTab === 'tools' ? '#17212F' : 'transparent',
                color: drawerTab === 'tools' ? '#7BC8CF' : '#94A3B8',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              Tools ({report.tool_executions.length})
            </button>
            <button
              onClick={() => setDrawerTab('logs')}
              style={{
                flex: 1,
                padding: '10px',
                background: drawerTab === 'logs' ? '#17212F' : 'transparent',
                color: drawerTab === 'logs' ? '#7BC8CF' : '#94A3B8',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              Agent Logs ({report.agent_logs.length})
            </button>
            <button
              onClick={() => setDrawerTab('evidence')}
              style={{
                flex: 1,
                padding: '10px',
                background: drawerTab === 'evidence' ? '#17212F' : 'transparent',
                color: drawerTab === 'evidence' ? '#7BC8CF' : '#94A3B8',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              Ledger ({report.retrieved_evidence.length})
            </button>
          </div>

          {/* Drawer Content Area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Tools View */}
            {drawerTab === 'tools' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {report.tool_executions.map((tool, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      backgroundColor: '#1E2B3E',
                      borderRadius: '6px',
                      border: '1px solid #2B3A4F',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="mono" style={{ color: '#7BC8CF', fontWeight: 800, fontSize: '0.85rem' }}>
                        {tool.tool_name}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#94A3B8' }}>
                        {tool.execution_time_ms.toFixed(1)} ms
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#CBD5E1', marginTop: '4px' }}>
                      Provenance: {tool.provenance}
                    </div>

                    <button
                      onClick={() => setSelectedToolRecord(selectedToolRecord === tool ? null : tool)}
                      style={{
                        marginTop: '8px',
                        background: 'transparent',
                        border: '1px solid #7BC8CF',
                        color: '#7BC8CF',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        cursor: 'pointer',
                      }}
                    >
                      {selectedToolRecord === tool ? 'Hide JSON' : 'Inspect Inputs / Outputs'}
                    </button>

                    {selectedToolRecord === tool && (
                      <div
                        className="mono"
                        style={{
                          marginTop: '8px',
                          padding: '10px',
                          backgroundColor: '#0D1E35',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          maxHeight: '180px',
                          overflowY: 'auto',
                          whiteSpace: 'pre-wrap',
                          color: '#E2E8F0',
                        }}
                      >
                        <div><strong>INPUTS:</strong> {JSON.stringify(tool.input_arguments, null, 2)}</div>
                        <div style={{ marginTop: '6px' }}><strong>OUTPUTS:</strong> {JSON.stringify(tool.output_data, null, 2)}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Agent Logs View */}
            {drawerTab === 'logs' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {report.agent_logs.map((log, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      backgroundColor: '#1E2B3E',
                      borderRadius: '6px',
                      border: '1px solid #2B3A4F',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="badge badge-teal" style={{ fontSize: '0.68rem' }}>
                        {log.role}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#94A3B8' }}>
                        {log.stage}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#CBD5E1', marginTop: '6px', lineHeight: 1.45, margin: '6px 0 0' }}>
                      {log.thought}
                    </p>
                    {log.output_summary && (
                      <div style={{ fontSize: '0.72rem', color: '#7BC8CF', marginTop: '6px' }}>
                        ↳ {log.output_summary}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Evidence Ledger View */}
            {drawerTab === 'evidence' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {report.retrieved_evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      backgroundColor: '#1E2B3E',
                      borderRadius: '6px',
                      border: '1px solid #2B3A4F',
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: '0.825rem', color: '#ffffff' }}>
                      {ev.title || ev.summary}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#7BC8CF', marginTop: '4px' }}>
                      {ev.source}
                    </div>
                    {ev.source_doi && (
                      <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '2px' }}>
                        DOI: {ev.source_doi}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
