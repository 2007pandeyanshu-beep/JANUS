import React, { useEffect, useRef } from 'react';
import { JanusSymbol } from './JanusBrand';
import {
  fadeInUp,
  setupHeroExperimentDiagramAnimation,
  observeSectionReveal,
  safeCancel,
  prefersReducedMotion,
} from '../utils/motion';

interface LandingPageProps {
  onStartInvestigation: (preset?: 'CS-CAT-001' | 'CS-OER-002' | 'SYN-001') => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStartInvestigation }) => {
  // Hero Animation Refs
  const heroTextRef = useRef<HTMLDivElement | null>(null);
  const hypNode1Ref = useRef<SVGGElement | null>(null);
  const hypNode2Ref = useRef<SVGGElement | null>(null);
  const hypNode3Ref = useRef<SVGGElement | null>(null);
  const path1Ref = useRef<SVGPathElement | null>(null);
  const path2Ref = useRef<SVGPathElement | null>(null);
  const path3Ref = useRef<SVGPathElement | null>(null);
  const expNodeRef = useRef<SVGGElement | null>(null);
  const pulseRing1Ref = useRef<SVGCircleElement | null>(null);
  const pulseRing2Ref = useRef<SVGCircleElement | null>(null);
  const eigBadgeRef = useRef<SVGGElement | null>(null);

  // Section Refs for Viewport Reveals
  const problemSectionRef = useRef<HTMLElement | null>(null);
  const workflowSectionRef = useRef<HTMLElement | null>(null);
  const benchmarksSectionRef = useRef<HTMLElement | null>(null);
  const evaluationSectionRef = useRef<HTMLElement | null>(null);
  const ctaSectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // 1. Hero Text Entrance
    if (heroTextRef.current) {
      fadeInUp(heroTextRef.current, { duration: 650, distance: 18 });
    }

    // 2. Hero Experiment Selection Diagram Animation
    const hypNodes = [hypNode1Ref.current, hypNode2Ref.current, hypNode3Ref.current].filter(Boolean) as SVGGElement[];
    const paths = [path1Ref.current, path2Ref.current, path3Ref.current].filter(Boolean) as SVGPathElement[];
    const rings = [pulseRing1Ref.current, pulseRing2Ref.current].filter(Boolean) as SVGCircleElement[];

    const diagramAnim = setupHeroExperimentDiagramAnimation({
      hypothesisNodes: hypNodes,
      connectorPaths: paths,
      recommendedNode: expNodeRef.current,
      pulseRings: rings,
      badgeTag: eigBadgeRef.current,
    });

    // 3. Viewport-aware scroll reveals for sections
    const cleanups: (() => void)[] = [];

    if (!prefersReducedMotion()) {
      [problemSectionRef, workflowSectionRef, benchmarksSectionRef, evaluationSectionRef, ctaSectionRef].forEach((ref) => {
        if (ref.current) {
          const cleanup = observeSectionReveal(ref.current, () => {
            fadeInUp(ref.current, { duration: 550, distance: 16 });
          }, 0.12);
          cleanups.push(cleanup);
        }
      });
    }

    return () => {
      safeCancel(diagramAnim);
      cleanups.forEach((c) => c());
    };
  }, []);

  const scrollToWorkflow = () => {
    const el = document.getElementById('how-it-works');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div
      className="landing-page"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '88px',
        maxWidth: '1240px',
        margin: '0 auto',
        paddingBottom: '80px',
      }}
    >
      {/* ====================================================================== */}
      {/* 1. HERO SECTION: MINIMAL, SCIENTIFIC, DISTINCTIVE                      */}
      {/* ====================================================================== */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: '1.08fr 1fr',
          gap: '48px',
          alignItems: 'center',
          paddingTop: '32px',
          paddingBottom: '16px',
        }}
      >
        {/* Left: Headline & Primary Action */}
        <div ref={heroTextRef} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Subtle Tagline Badge */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                backgroundColor: '#EBF6FC',
                color: '#079FF0',
                border: '1px solid rgba(7, 159, 240, 0.25)',
                padding: '6px 14px',
                borderRadius: '9999px',
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#079FF0' }}></span>
              Bayesian Experimental Design for Science
            </span>
          </div>

          {/* Hero Headline: Clean Dark Slate + Electric Blue Accent */}
          <h1
            style={{
              fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
              fontSize: 'clamp(40px, 4.2vw, 58px)',
              fontWeight: 800,
              lineHeight: 1.12,
              letterSpacing: '-0.03em',
              color: '#243640',
              margin: 0,
            }}
          >
            Don't just predict.
            <br />
            <span style={{ color: '#079FF0' }}>Decide what to test next.</span>
          </h1>

          {/* Supporting Text: Controlled line length & high contrast */}
          <p
            style={{
              fontSize: '1.125rem',
              lineHeight: 1.65,
              color: '#5A7184',
              margin: 0,
              maxWidth: '540px',
            }}
          >
            JANUS disambiguates competing scientific explanations through literature-grounded agents,
            computational tools, and authoritative Bayesian experimental design.
          </p>

          {/* Primary Action Button */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '6px', flexWrap: 'wrap' }}>
            <button
              onClick={() => onStartInvestigation('CS-CAT-001')}
              style={{
                backgroundColor: '#079FF0',
                color: '#ffffff',
                fontSize: '0.95rem',
                fontWeight: 700,
                padding: '14px 28px',
                borderRadius: '10px',
                border: 'none',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 16px rgba(7, 159, 240, 0.32)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#028ce0';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#079FF0';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              Start an investigation &rarr;
            </button>

            <button
              onClick={scrollToWorkflow}
              style={{
                backgroundColor: '#ffffff',
                color: '#243640',
                fontSize: '0.95rem',
                fontWeight: 600,
                padding: '13px 22px',
                borderRadius: '10px',
                border: '1px solid #CBD5E1',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#F5F8F9';
                e.currentTarget.style.borderColor = '#94A3B8';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#ffffff';
                e.currentTarget.style.borderColor = '#CBD5E1';
              }}
            >
              Explore how JANUS works
            </button>
          </div>

          {/* Minimal Trust & Provenance Bar */}
          <div
            style={{
              display: 'flex',
              gap: '24px',
              fontSize: '0.85rem',
              color: '#5A7184',
              marginTop: '12px',
              borderTop: '1px solid #E2E8F0',
              paddingTop: '18px',
            }}
          >
            <div>
              <strong style={{ color: '#243640' }}>Closed-Form EIG:</strong> 100% Python calculations
            </div>
            <div>
              <strong style={{ color: '#243640' }}>Evidence Grounded:</strong> Verified DOI citations
            </div>
          </div>
        </div>

        {/* Right: Distinctive Experiment-Selection Scientific Diagram */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '20px',
            border: '1px solid #E2E8F0',
            padding: '28px 24px',
            boxShadow: '0 10px 30px -4px rgba(36, 54, 64, 0.07), 0 4px 12px -2px rgba(36, 54, 64, 0.04)',
            position: 'relative',
          }}
        >
          {/* Header of Visual */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid #F1F5F9',
              paddingBottom: '14px',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <JanusSymbol size={20} />
              <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#243640', letterSpacing: '0.04em' }}>
                EXPERIMENT DISAMBIGUATION MAP
              </span>
            </div>
            <span
              style={{
                fontSize: '0.72rem',
                fontFamily: "'JetBrains Mono', monospace",
                color: '#079FF0',
                fontWeight: 700,
                backgroundColor: '#EBF6FC',
                padding: '3px 8px',
                borderRadius: '6px',
              }}
            >
              CS-CAT-001 (Pt/CeO₂)
            </span>
          </div>

          {/* Diagrammatic SVG Canvas */}
          <svg
            viewBox="0 0 440 280"
            style={{ width: '100%', height: 'auto', overflow: 'visible' }}
            aria-label="Hypothesis to Experiment Convergence Diagram"
          >
            <defs>
              <linearGradient id="curveGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#079FF0" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#079FF0" stopOpacity="1" />
              </linearGradient>
              <linearGradient id="curveGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#A8DFF6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#079FF0" stopOpacity="1" />
              </linearGradient>
              <linearGradient id="curveGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#94A3B8" stopOpacity="0.7" />
                <stop offset="100%" stopColor="#079FF0" stopOpacity="1" />
              </linearGradient>
            </defs>

            {/* Column 1 Guide: Competing Hypotheses */}
            <text x="30" y="24" fill="#7A8E9E" fontSize="10" fontFamily="'Plus Jakarta Sans', sans-serif" fontWeight="700">
              COMPETING HYPOTHESES (Priors)
            </text>

            {/* Column 2 Guide: Decisive Experiment */}
            <text x="260" y="24" fill="#7A8E9E" fontSize="10" fontFamily="'Plus Jakarta Sans', sans-serif" fontWeight="700">
              RECOMMENDED EXPERIMENT (Argmax)
            </text>

            {/* Connecting Smooth Splines (Hypotheses -> Decisive Experiment Node) */}
            <path
              ref={path1Ref}
              d="M 140,68 C 190,68 220,135 280,135"
              fill="none"
              stroke="url(#curveGrad1)"
              strokeWidth="2.5"
            />
            <path
              ref={path2Ref}
              d="M 140,135 C 190,135 230,135 280,135"
              fill="none"
              stroke="url(#curveGrad2)"
              strokeWidth="2.5"
            />
            <path
              ref={path3Ref}
              d="M 140,202 C 190,202 220,135 280,135"
              fill="none"
              stroke="url(#curveGrad3)"
              strokeWidth="2"
              strokeDasharray="4 3"
            />

            {/* Hypothesis 1 Box (H1: Redox) */}
            <g ref={hypNode1Ref}>
              <rect x="20" y="46" width="125" height="42" rx="8" fill="#F5F8F9" stroke="#E2E8F0" strokeWidth="1.5" />
              <text x="32" y="64" fill="#243640" fontSize="11" fontWeight="800" fontFamily="'Plus Jakarta Sans', sans-serif">
                H1: Redox (MvK)
              </text>
              <text x="32" y="78" fill="#079FF0" fontSize="10" fontWeight="700" fontFamily="'JetBrains Mono', monospace">
                P(H1) = 0.50
              </text>
            </g>

            {/* Hypothesis 2 Box (H2: Formate) */}
            <g ref={hypNode2Ref}>
              <rect x="20" y="114" width="125" height="42" rx="8" fill="#F5F8F9" stroke="#E2E8F0" strokeWidth="1.5" />
              <text x="32" y="132" fill="#243640" fontSize="11" fontWeight="800" fontFamily="'Plus Jakarta Sans', sans-serif">
                H2: Formate Path
              </text>
              <text x="32" y="146" fill="#079FF0" fontSize="10" fontWeight="700" fontFamily="'JetBrains Mono', monospace">
                P(H2) = 0.20
              </text>
            </g>

            {/* Hypothesis 3 Box (H3: Carboxyl) */}
            <g ref={hypNode3Ref}>
              <rect x="20" y="181" width="125" height="42" rx="8" fill="#F5F8F9" stroke="#E2E8F0" strokeWidth="1.5" />
              <text x="32" y="199" fill="#243640" fontSize="11" fontWeight="800" fontFamily="'Plus Jakarta Sans', sans-serif">
                H3: Carboxyl Path
              </text>
              <text x="32" y="213" fill="#7A8E9E" fontSize="10" fontWeight="700" fontFamily="'JetBrains Mono', monospace">
                P(H3) = 0.30
              </text>
            </g>

            {/* Pulse rings from decisive experiment */}
            <circle ref={pulseRing1Ref} cx="280" cy="135" r="16" fill="none" stroke="#079FF0" strokeWidth="1.5" opacity="0" />
            <circle ref={pulseRing2Ref} cx="280" cy="135" r="26" fill="none" stroke="#A8DFF6" strokeWidth="1.2" opacity="0" />

            {/* Decisive Experiment Node & Card */}
            <g ref={expNodeRef}>
              <rect
                x="250"
                y="100"
                width="170"
                height="70"
                rx="10"
                fill="#ffffff"
                stroke="#079FF0"
                strokeWidth="2"
                filter="drop-shadow(0 4px 12px rgba(7, 159, 240, 0.18))"
              />
              <text x="264" y="122" fill="#079FF0" fontSize="9" fontWeight="800" fontFamily="'JetBrains Mono', monospace">
                OPTIMAL CANDIDATE #1
              </text>
              <text x="264" y="139" fill="#243640" fontSize="12" fontWeight="800" fontFamily="'Plus Jakarta Sans', sans-serif">
                EXP-WGS-02
              </text>
              <text x="264" y="154" fill="#5A7184" fontSize="10" fontFamily="'Plus Jakarta Sans', sans-serif">
                Isotopic Pulse MS (18O/16O)
              </text>
            </g>

            {/* EIG Callout Badge */}
            <g ref={eigBadgeRef}>
              <rect x="264" y="184" width="142" height="28" rx="6" fill="#EBF6FC" stroke="#BAE6FD" strokeWidth="1" />
              <text x="274" y="202" fill="#079FF0" fontSize="10.5" fontWeight="800" fontFamily="'JetBrains Mono', monospace">
                Max EIG: 0.5593 bits
              </text>
            </g>
          </svg>

          {/* Bottom Caption Bar */}
          <div
            style={{
              marginTop: '16px',
              padding: '10px 14px',
              backgroundColor: '#F5F8F9',
              borderRadius: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.785rem',
            }}
          >
            <span style={{ color: '#5A7184' }}>Initial Epistemic Entropy: <strong>1.4855 bits</strong></span>
            <span style={{ color: '#059669', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
              Expected Regret: 0.0000 b
            </span>
          </div>
        </div>
      </section>

      {/* ====================================================================== */}
      {/* 2. THE SCIENTIFIC PROBLEM: EQUFINALITY & AMBIGUITY                     */}
      {/* ====================================================================== */}
      <section
        ref={problemSectionRef}
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '40px',
          alignItems: 'center',
          backgroundColor: '#ffffff',
          borderRadius: '20px',
          padding: '44px 40px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 4px 20px -2px rgba(36, 54, 64, 0.04)',
        }}
      >
        {/* Left: Problem Statement */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <span
            style={{
              color: '#079FF0',
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            The Core Scientific Dilemma
          </span>
          <h2
            style={{
              fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
              fontSize: '2.1rem',
              fontWeight: 800,
              lineHeight: 1.22,
              letterSpacing: '-0.02em',
              color: '#243640',
              margin: 0,
            }}
          >
            Multiple hypotheses explain the exact same observations.
          </h2>
          <p style={{ fontSize: '1rem', lineHeight: 1.65, color: '#5A7184', margin: 0 }}>
            In physical chemistry, materials science, and biology, several contradictory mechanisms often
            fit existing steady-state reaction data or spectrum peaks equally well. This is scientific
            <strong> equifinality</strong>.
          </p>
          <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#5A7184', margin: 0 }}>
            Standard AI models predict forward properties ($x \to y$). JANUS solves the inverse decision problem:
            prescribing the precise experimental perturbation that forces competing explanations to make
            divergent, testable predictions.
          </p>
        </div>

        {/* Right: Comparative Demonstration Card */}
        <div
          style={{
            backgroundColor: '#F5F8F9',
            borderRadius: '16px',
            padding: '28px',
            border: '1px solid #E2E8F0',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#243640', letterSpacing: '0.02em' }}>
            HETEROGENEOUS CATALYSIS CASE STUDY (CS-CAT-001)
          </div>

          {/* Comparison Row 1: The Ambiguity */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '10px',
              padding: '14px 16px',
              border: '1px solid #E2E8F0',
            }}
          >
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#E11D48' }}>
              ✕ The Forward Modeling Trap:
            </div>
            <div style={{ fontSize: '0.825rem', color: '#5A7184', marginTop: '4px', lineHeight: 1.5 }}>
              In-situ DRIFTS detects intense surface formate peaks. Both Redox (H1) and Formate (H2) models fit
              the raw spectrum. Formate could be an active intermediate or an unreactive spectator pool.
            </div>
          </div>

          {/* Comparison Row 2: The Decisive Solution */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '10px',
              padding: '14px 16px',
              border: '1px solid rgba(7, 159, 240, 0.3)',
              boxShadow: '0 2px 8px rgba(7, 159, 240, 0.08)',
            }}
          >
            <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#079FF0' }}>
              ✓ JANUS Information-Theoretic Resolution:
            </div>
            <div style={{ fontSize: '0.825rem', color: '#243640', marginTop: '4px', lineHeight: 1.5 }}>
              JANUS prescribes <strong>EXP-WGS-02</strong> (Transient isotopic ¹⁸O / ¹⁶O pulse MS).
              Under Redox, product CO₂ contains support ¹⁶O; under Associative paths, it contains
              ¹⁸O. Ambiguity collapses in a single targeted run.
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================== */}
      {/* 3. HOW THE INVESTIGATION WORKFLOW WORKS                                 */}
      {/* ====================================================================== */}
      <section id="how-it-works" ref={workflowSectionRef} style={{ display: 'flex', flexDirection: 'column', gap: '36px' }}>
        <div style={{ textAlign: 'center', maxWidth: '680px', margin: '0 auto' }}>
          <span
            style={{
              color: '#079FF0',
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            The 5-Stage Scientific Architecture
          </span>
          <h2
            style={{
              fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
              fontSize: '2.2rem',
              fontWeight: 800,
              letterSpacing: '-0.02em',
              color: '#243640',
              marginTop: '6px',
            }}
          >
            How JANUS Guides an Investigation
          </h2>
          <p style={{ fontSize: '1.05rem', lineHeight: 1.6, color: '#5A7184', margin: '8px 0 0' }}>
            A disciplined human-in-the-loop pipeline combining peer-reviewed evidence with authoritative
            closed-form Bayesian calculations.
          </p>
        </div>

        {/* 5-Step Horizontal Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
          {[
            {
              step: '01',
              title: 'Scientific Question',
              desc: 'Define competing hypotheses with initial prior probabilities constrained to the mathematical simplex.',
            },
            {
              step: '02',
              title: 'Evidence Grounding',
              desc: 'Retrieve verified peer-reviewed literature with real DOIs and execute chemical kinetics analytical tools.',
            },
            {
              step: '03',
              title: 'Bayesian Ranking',
              desc: 'Authoritative Python calculation of Expected Information Gain (EIG) and cost-weighted Composite Utility.',
            },
            {
              step: '04',
              title: 'Sequential Update',
              desc: 'Apply simulated or confirmed observations to compute exact posteriors P(H_k | y) and retire executed assays.',
            },
            {
              step: '05',
              title: 'Consensus Report',
              desc: 'Generate presentation-ready synthesis with measured entropy reduction and explicit boundary disclosures.',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="card"
              style={{
                padding: '24px 18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                backgroundColor: '#ffffff',
                border: '1px solid #E2E8F0',
                borderRadius: '16px',
                position: 'relative',
              }}
            >
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.85rem',
                  fontWeight: 800,
                  color: '#079FF0',
                  backgroundColor: '#EBF6FC',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  alignSelf: 'flex-start',
                }}
              >
                {item.step}
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#243640', margin: '4px 0 0' }}>
                {item.title}
              </h3>
              <p style={{ fontSize: '0.825rem', color: '#5A7184', lineHeight: 1.5, margin: 0 }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ====================================================================== */}
      {/* 4. EVIDENCE EVALUATION & HYPOTHESIS BENCHMARKS                         */}
      {/* ====================================================================== */}
      <section ref={benchmarksSectionRef} style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <span
              style={{
                color: '#079FF0',
                fontSize: '0.8rem',
                fontWeight: 800,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              Curated Scientific Benchmarks
            </span>
            <h2
              style={{
                fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
                fontSize: '2rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                color: '#243640',
                marginTop: '4px',
              }}
            >
              Explore Supported Research Scenarios
            </h2>
          </div>
          <span style={{ fontSize: '0.875rem', color: '#5A7184' }}>
            All numerical predictions calibrated against peer-reviewed publications
          </span>
        </div>

        {/* 3 Benchmark Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
          {/* Card 1: CS-CAT-001 */}
          <div
            className="card"
            style={{
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onClick={() => onStartInvestigation('CS-CAT-001')}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge badge-emerald">CS-CAT-001</span>
                <span style={{ fontSize: '0.75rem', color: '#5A7184' }}>Empirical Catalysis</span>
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#243640', marginTop: '12px' }}>
                Pt/CeO₂ Water-Gas Shift
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#5A7184', marginTop: '6px', lineHeight: 1.55 }}>
                Disambiguates Redox (Mars-van Krevelen) vs. Formate vs. Carboxyl pathways using steady-state DRIFTS,
                SSITKA, and transient pulse MS.
              </p>
              <div
                style={{
                  marginTop: '16px',
                  padding: '10px 14px',
                  backgroundColor: '#F5F8F9',
                  borderRadius: '8px',
                  fontSize: '0.785rem',
                  fontFamily: "'JetBrains Mono', monospace",
                  color: '#243640',
                }}
              >
                Top Experiment: <strong>EXP-WGS-02</strong> (EIG: 0.5593 b)
              </div>
            </div>

            <button
              className="btn btn-primary"
              style={{ marginTop: '22px', width: '100%', padding: '12px' }}
              onClick={(e) => {
                e.stopPropagation();
                onStartInvestigation('CS-CAT-001');
              }}
            >
              Launch CS-CAT-001 &rarr;
            </button>
          </div>

          {/* Card 2: CS-OER-002 */}
          <div
            className="card"
            style={{
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onClick={() => onStartInvestigation('CS-OER-002')}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge badge-purple">CS-OER-002</span>
                <span style={{ fontSize: '0.75rem', color: '#5A7184' }}>Preregistered Protocol</span>
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#243640', marginTop: '12px' }}>
                Perovskite OER Electrocatalysis
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#5A7184', marginTop: '6px', lineHeight: 1.55 }}>
                Disambiguates Adsorbate Evolution (AEM) vs. Lattice Oxygen (LOM) vs. Radical Oxide Path (OPM) on
                La₁₋ₓSrₓCoO₃₋ᵟ perovskites.
              </p>
              <div
                style={{
                  marginTop: '16px',
                  padding: '10px 14px',
                  backgroundColor: '#F5F8F9',
                  borderRadius: '8px',
                  fontSize: '0.785rem',
                  fontFamily: "'JetBrains Mono', monospace",
                  color: '#243640',
                }}
              >
                Top Experiment: <strong>EXP-OER-03</strong> (EIG: 0.4646 b)
              </div>
            </div>

            <button
              className="btn btn-primary"
              style={{ marginTop: '22px', width: '100%', padding: '12px' }}
              onClick={(e) => {
                e.stopPropagation();
                onStartInvestigation('CS-OER-002');
              }}
            >
              Launch CS-OER-002 &rarr;
            </button>
          </div>

          {/* Card 3: SYN-001 */}
          <div
            className="card"
            style={{
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #E2E8F0',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onClick={() => onStartInvestigation('SYN-001')}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge badge-blue">SYN-001</span>
                <span style={{ fontSize: '0.75rem', color: '#5A7184' }}>Synthetic Benchmark</span>
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#243640', marginTop: '12px' }}>
                Kinase Signaling Pathway
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#5A7184', marginTop: '6px', lineHeight: 1.55 }}>
                Disambiguates Allosteric Modulation vs. ATP-Competitive Binding vs. Targeted Degradation for small
                molecule JNS-401.
              </p>
              <div
                style={{
                  marginTop: '16px',
                  padding: '10px 14px',
                  backgroundColor: '#F5F8F9',
                  borderRadius: '8px',
                  fontSize: '0.785rem',
                  fontFamily: "'JetBrains Mono', monospace",
                  color: '#243640',
                }}
              >
                Top Experiment: <strong>EXP-01</strong> (EIG: 0.6861 b)
              </div>
            </div>

            <button
              className="btn btn-primary"
              style={{ marginTop: '22px', width: '100%', padding: '12px' }}
              onClick={(e) => {
                e.stopPropagation();
                onStartInvestigation('SYN-001');
              }}
            >
              Launch SYN-001 &rarr;
            </button>
          </div>
        </div>
      </section>

      {/* ====================================================================== */}
      {/* 5. EXPERIMENT RANKING & EXPECTED INFORMATION GAIN BENCHMARK            */}
      {/* ====================================================================== */}
      <section
        ref={evaluationSectionRef}
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '20px',
          padding: '40px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 4px 20px -2px rgba(36, 54, 64, 0.04)',
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 1fr', gap: '36px', alignItems: 'center' }}>
          <div>
            <span
              style={{
                color: '#079FF0',
                fontSize: '0.8rem',
                fontWeight: 800,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              Empirical Policy Audit
            </span>
            <h2
              style={{
                fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
                fontSize: '1.85rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                color: '#243640',
                marginTop: '4px',
              }}
            >
              Zero EIG Regret Against Combinatorial Bound
            </h2>
            <p style={{ fontSize: '0.95rem', color: '#5A7184', lineHeight: 1.65, marginTop: '8px' }}>
              In statistical audits across 150 matched campaigns on CS-CAT-001, JANUS achieved a $1.60\times$
              information gain multiplier over uniform random choice while completely eliminating uninformative
              blank control waste traps.
            </p>

            <div
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                backgroundColor: '#F5F8F9',
                borderRadius: '8px',
                borderLeft: '3px solid #079FF0',
                fontSize: '0.825rem',
                color: '#5A7184',
                lineHeight: 1.5,
              }}
            >
              <strong style={{ color: '#243640' }}>Transparent Disclosures:</strong> Simulated outcomes are
              discretized diagnostic categories, not live robotic measurements. Unquantified proposals lacking
              calibrated likelihoods (EXP-WGS-05) are held out to prevent numerical fabrication.
            </div>
          </div>

          {/* Results Table */}
          <div
            style={{
              backgroundColor: '#F5F8F9',
              borderRadius: '12px',
              padding: '20px',
              border: '1px solid #E2E8F0',
            }}
          >
            <div
              style={{
                fontSize: '0.75rem',
                color: '#079FF0',
                fontWeight: 800,
                fontFamily: "'JetBrains Mono', monospace",
                marginBottom: '10px',
              }}
            >
              CS-CAT-001 STATISTICAL BENCHMARK (N=5 ASSAYS)
            </div>
            <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #CBD5E1', color: '#7A8E9E' }}>
                  <th style={{ padding: '8px 0', textAlign: 'left', fontWeight: 700 }}>Policy</th>
                  <th style={{ padding: '8px 0', textAlign: 'right', fontWeight: 700 }}>EIG (bits)</th>
                  <th style={{ padding: '8px 0', textAlign: 'right', fontWeight: 700 }}>Regret</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid #E2E8F0' }}>
                  <td style={{ padding: '10px 0', fontWeight: 800, color: '#079FF0' }}>JANUS Engine</td>
                  <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 800, fontFamily: "'JetBrains Mono', monospace" }}>
                    0.5593 b
                  </td>
                  <td style={{ padding: '10px 0', textAlign: 'right', color: '#059669', fontWeight: 800, fontFamily: "'JetBrains Mono', monospace" }}>
                    0.0000 b
                  </td>
                </tr>
                <tr style={{ borderBottom: '1px solid #E2E8F0' }}>
                  <td style={{ padding: '10px 0', color: '#243640' }}>Uniform Random</td>
                  <td style={{ padding: '10px 0', textAlign: 'right', fontFamily: "'JetBrains Mono', monospace" }}>
                    0.3506 b
                  </td>
                  <td style={{ padding: '10px 0', textAlign: 'right', color: '#E11D48', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                    +0.2086 b
                  </td>
                </tr>
                <tr>
                  <td style={{ padding: '10px 0', color: '#243640' }}>Cheapest Heuristic</td>
                  <td style={{ padding: '10px 0', textAlign: 'right', fontFamily: "'JetBrains Mono', monospace" }}>
                    0.0000 b
                  </td>
                  <td style={{ padding: '10px 0', textAlign: 'right', color: '#E11D48', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                    +0.5593 b
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ====================================================================== */}
      {/* 6. FINAL CALL TO ACTION & FOOTER                                       */}
      {/* ====================================================================== */}
      <section
        ref={ctaSectionRef}
        style={{
          textAlign: 'center',
          padding: '56px 32px',
          backgroundColor: '#ffffff',
          borderRadius: '20px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 4px 20px -2px rgba(36, 54, 64, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <JanusSymbol size={36} />
        <h2
          style={{
            fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif",
            fontSize: '2.2rem',
            fontWeight: 800,
            letterSpacing: '-0.02em',
            color: '#243640',
            margin: 0,
          }}
        >
          Accelerate your scientific decision-making
        </h2>
        <p style={{ color: '#5A7184', fontSize: '1.05rem', maxWidth: '620px', lineHeight: 1.6, margin: 0 }}>
          Launch the 5-stage interactive investigation workbench to see how JANUS identifies the most informative
          assays under real budget constraints.
        </p>

        <button
          onClick={() => onStartInvestigation('CS-CAT-001')}
          style={{
            marginTop: '8px',
            backgroundColor: '#079FF0',
            color: '#ffffff',
            fontSize: '1rem',
            fontWeight: 700,
            padding: '15px 36px',
            borderRadius: '10px',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 4px 18px rgba(7, 159, 240, 0.35)',
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#028ce0';
            e.currentTarget.style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#079FF0';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          Launch Guided Investigation &rarr;
        </button>

        {/* Minimal Footer */}
        <div
          style={{
            marginTop: '36px',
            borderTop: '1px solid #E2E8F0',
            paddingTop: '20px',
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.8rem',
            color: '#7A8E9E',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>JANUS Scientific Intelligence Core • Bayesian Experimental Design</div>
          <div>Calibrated with Kalamaras et al. (2011) & Mefford et al. (2016)</div>
        </div>
      </section>
    </div>
  );
};
