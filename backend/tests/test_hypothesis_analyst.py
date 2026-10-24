"""Tests for JANUS Independent Hypothesis Analyst uAgent (Phase 5).

Verifies:
1. Hypothesis analysis schemas serialization, deserialization, and boundary validation.
2. Distinct cryptographic identity (address, port, protocol) from coordinator, auditor, and research agents.
3. Authentic WGS mechanistic evaluation with explicit evidence links, contradiction identification, and rationales.
4. OER scenario evaluation with DEMS and DFT evidence linking.
5. Honest handling of empty evidence records (INSUFFICIENT_EVIDENCE, zero hallucinations).
6. Rigorous probability simplex normalization (sum P(H_k) == 1.0) and boundary preservation.
7. Explicit separation of physical model assumptions from empirical evidence.
8. Honest offline reporting (ANALYSIS_UNAVAILABLE, never faking success).
9. Graceful fallback when daemon is unreachable with transparent audit trail.
10. ScientificInvestigationOrchestrator Stage 2 integration.
11. Live inter-agent request/response message exchange over native Fetch.ai uAgents protocol.
"""

import os
import sys
import time
import math
import asyncio
import threading
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any

# Ensure backend directory is in sys.path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_test_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.schemas.hypothesis_analyst import (
    HypothesisEvidenceLink,
    HypothesisEvaluationItem,
    HypothesisAnalysisRequest,
    HypothesisAnalysisResponse,
)
from app.schemas.scientific import Hypothesis, Evidence
from agents.tools import (
    HypothesisAnalystTool,
    ResearchAgentTool,
    AuditorAgentTool,
)
from agents.hypothesis_analyst_agent import (
    create_hypothesis_analyst_uagent,
    perform_hypothesis_analysis,
    scientific_hypothesis_proto,
)
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import InvestigationInput, AgentRole, ToolExecutionRecord


def test_hypothesis_schemas_serialization_and_validation():
    """Verifies that hypothesis request, response, item, and link models serialize cleanly."""
    link = HypothesisEvidenceLink(
        evidence_id="CLM-WGS-001",
        relation_type="CONTRADICTING",
        rationale="Formate exchange rate is <15% of TOF, refuting formate as primary reactive intermediate.",
        confidence_weight=0.95,
    )
    assert link.evidence_id == "CLM-WGS-001"
    assert link.relation_type == "CONTRADICTING"
    assert link.confidence_weight == 0.95

    item = HypothesisEvaluationItem(
        id="H2",
        name="Associative Formate Mechanism",
        description="CO reacts with support OH forming formate intermediate decomposing to CO2 and H2.",
        prior=0.20,
        evidence_links=[link],
        supporting_evidence_ids=[],
        contradicting_evidence_ids=["CLM-WGS-001"],
        epistemic_status="STRONGLY_CONTRADICTED",
        uncertainty_explanation="Spectroscopic visibility in DRIFTS contrasts with slow SSITKA turnover kinetics.",
        assumptions=["Formates are kinetically competent intermediates"],
        mathematical_formulation="r = k * [HCOO-Ce]",
    )
    assert item.id == "H2"
    assert item.prior == 0.20
    assert len(item.contradicting_evidence_ids) == 1

    req = HypothesisAnalysisRequest(
        correlation_id="corr-hyp-101",
        investigation_id="INV-HYP-TEST-01",
        research_question="Which reaction mechanism dominates WGS on Pt/CeO2?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=[{"id": "CLM-WGS-001", "summary": "Formate exchange is 0.14 of TOF", "confidence": 0.95}],
        existing_priors={"H1": 0.50, "H2": 0.20, "H3": 0.30},
    )
    dumped_req = req.model_dump()
    assert dumped_req["correlation_id"] == "corr-hyp-101"
    restored_req = HypothesisAnalysisRequest.model_validate(dumped_req)
    assert restored_req.investigation_id == "INV-HYP-TEST-01"

    resp = HypothesisAnalysisResponse(
        correlation_id="corr-hyp-101",
        investigation_id="INV-HYP-TEST-01",
        status="ANALYSIS_COMPLETED",
        agent_address="agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d",
        timestamp=datetime.now(timezone.utc).isoformat(),
        hypotheses=[item],
        simplex_sum=1.0,
        is_simplex_valid=True,
        unresolved_questions=["What is the branching ratio at 250 C?"],
        warnings=[],
        summary="Analysis complete with 1 evaluated hypothesis.",
    )
    dumped_resp = resp.model_dump()
    assert dumped_resp["status"] == "ANALYSIS_COMPLETED"
    assert dumped_resp["is_simplex_valid"] is True


def test_hypothesis_analyst_identity_distinct():
    """Verifies that the Hypothesis Analyst agent has a distinct name, address, port, and protocol."""
    agent = create_hypothesis_analyst_uagent(port=8011)

    assert agent.name == "janus_hypothesis_analyst"
    expected_addr = "agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d"
    assert agent.address == expected_addr

    # Cryptographic address must be distinct from coordinator, auditor, and research agents
    auditor_addr = AuditorAgentTool.DEFAULT_AUDITOR_ADDRESS
    research_addr = ResearchAgentTool.DEFAULT_RESEARCH_AGENT_ADDRESS

    assert agent.address != auditor_addr
    assert agent.address != research_addr
    assert agent.address != "agent1q0hmkpdw4v28hmkkfqa56u2zwx3pzly44z7r8048pjtgw4lq8r5my29pn3t"

    # Verify protocol registration
    assert scientific_hypothesis_proto.name == "janus_scientific_hypothesis"
    assert scientific_hypothesis_proto.version == "1.0.0"


def test_wgs_hypothesis_analysis_and_evidence_linking():
    """Verifies authentic WGS mechanistic evaluation with explicit evidence links and contradiction tagging."""
    evidence_items = [
        {
            "id": "CLM-WGS-001",
            "statement": "At 200°C on Pt/CeO2, the rate of formate exchange during SSITKA is 0.14 of the overall catalytic turnover.",
            "supports_hypotheses": ["H1", "H3"],
            "refutes_hypotheses": ["H2"],
            "confidence": 0.95,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
        {
            "id": "CLM-WGS-002",
            "statement": "Transient isotopic pulsing of C16O over H218O-treated Pt/CeO2 yields 88% C16O2, proving lattice oxygen transfer.",
            "supports_hypotheses": ["H1"],
            "refutes_hypotheses": ["H2", "H3"],
            "confidence": 0.92,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
        {
            "id": "CLM-WGS-004",
            "statement": "Steady-state kinetic isotope effect r_H/r_D is 1.22, ruling out primary C-H bond cleavage in formates.",
            "supports_hypotheses": ["H1", "H3"],
            "refutes_hypotheses": ["H2"],
            "confidence": 0.90,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
        {
            "id": "CLM-WGS-006",
            "statement": "DFT calculations show carboxyl (*COOH) decomposition barrier (0.58 eV) is lower than formate decomposition (>1.4 eV).",
            "supports_hypotheses": ["H3"],
            "refutes_hypotheses": ["H2"],
            "confidence": 0.85,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
    ]

    req = HypothesisAnalysisRequest(
        correlation_id="corr-wgs-eval-01",
        investigation_id="INV-WGS-EVAL",
        research_question="Which reaction mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence_items,
    )

    resp = perform_hypothesis_analysis(
        request=req,
        agent_address="agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d",
    )

    assert resp.status == "ANALYSIS_COMPLETED"
    assert len(resp.hypotheses) == 3

    h_map = {h.id: h for h in resp.hypotheses}

    # H1: Redox mechanism
    h1 = h_map["H1"]
    assert h1.prior == 0.50
    assert "CLM-WGS-002" in h1.supporting_evidence_ids
    assert h1.epistemic_status == "VIABLE_CANDIDATE"
    assert len(h1.assumptions) >= 2
    assert "Pt-ceria perimeter" in h1.assumptions[0]
    assert h1.mathematical_formulation is not None

    # H2: Associative Formate mechanism
    h2 = h_map["H2"]
    assert h2.prior == 0.20
    assert "CLM-WGS-001" in h2.contradicting_evidence_ids
    assert "CLM-WGS-002" in h2.contradicting_evidence_ids
    assert "CLM-WGS-004" in h2.contradicting_evidence_ids
    assert h2.epistemic_status == "STRONGLY_CONTRADICTED"
    assert len(h2.contradicting_evidence_ids) >= 3

    # H3: Associative Carboxyl mechanism
    h3 = h_map["H3"]
    assert h3.prior == 0.30
    assert "CLM-WGS-006" in h3.supporting_evidence_ids
    assert h3.epistemic_status == "VIABLE_CANDIDATE"

    # Probability Simplex Invariant
    assert resp.is_simplex_valid is True
    assert abs(resp.simplex_sum - 1.0) < 1e-4

    # Unresolved Questions
    assert len(resp.unresolved_questions) >= 2


def test_oer_hypothesis_analysis_and_evidence_linking():
    """Verifies OER scenario hypothesis evaluation with DEMS and DFT evidence linking."""
    oer_evidence = [
        {
            "id": "EVD-OER-01",
            "statement": "In situ Raman spectroscopy identifies standard surface metal-oxo intermediates.",
            "supports_hypotheses": ["H1"],
            "refutes_hypotheses": [],
            "confidence": 0.90,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
        {
            "id": "EVD-OER-02",
            "statement": "Operando DEMS demonstrates significant lattice 18O integration into evolved O2 on La0.5Sr0.5CoO3-delta.",
            "supports_hypotheses": ["H2"],
            "refutes_hypotheses": ["H1"],
            "confidence": 0.95,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
    ]

    req = HypothesisAnalysisRequest(
        correlation_id="corr-oer-eval-01",
        investigation_id="INV-OER-EVAL",
        research_question="Does oxygen evolution on perovskites proceed via AEM or LOM?",
        case_study_id="CS-OER-002",
        retrieved_evidence=oer_evidence,
    )

    resp = perform_hypothesis_analysis(
        request=req,
        agent_address="agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d",
    )

    assert resp.status == "ANALYSIS_COMPLETED"
    assert len(resp.hypotheses) == 3
    h_map = {h.id: h for h in resp.hypotheses}

    # H1: AEM
    assert "EVD-OER-02" in h_map["H1"].contradicting_evidence_ids

    # H2: LOM
    assert "EVD-OER-02" in h_map["H2"].supporting_evidence_ids
    assert h_map["H2"].epistemic_status == "VIABLE_CANDIDATE"

    # Simplex sum invariant
    assert resp.is_simplex_valid is True
    assert abs(resp.simplex_sum - 1.0) < 1e-4


def test_empty_evidence_handling_insufficient_evidence():
    """Verifies that empty evidence leads to INSUFFICIENT_EVIDENCE with zero hallucinations."""
    req = HypothesisAnalysisRequest(
        correlation_id="corr-empty-01",
        investigation_id="INV-EMPTY-EVAL",
        research_question="Unknown reaction mechanism in novel high-entropy alloy?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=[],
    )

    resp = perform_hypothesis_analysis(
        request=req,
        agent_address="agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d",
    )

    assert resp.status == "INSUFFICIENT_EVIDENCE"
    assert len(resp.warnings) >= 1
    assert "No retrieved evidence items" in resp.warnings[0]

    for h in resp.hypotheses:
        assert len(h.evidence_links) == 0
        assert len(h.supporting_evidence_ids) == 0
        assert len(h.contradicting_evidence_ids) == 0
        assert h.epistemic_status == "INSUFFICIENT_EVIDENCE"

    assert resp.is_simplex_valid is True
    assert abs(resp.simplex_sum - 1.0) < 1e-4


def test_offline_daemon_handling_and_honest_reporting():
    """Verifies that when the daemon is offline and fallback is disabled, it returns ANALYSIS_UNAVAILABLE."""
    os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = "http://127.0.0.1:59999/submit"
    os.environ["JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS"] = "1.0"
    try:
        resp, record, pipeline_hyps = HypothesisAnalystTool.execute_hypothesis_analysis(
            research_question="What is the mechanism?",
            investigation_id="INV-OFFLINE-TEST",
            case_study_id="CS-CAT-001",
            timeout=1.0,
            allow_local_fallback=False,
        )

        assert resp.status == "ANALYSIS_UNAVAILABLE"
        assert record.status == "WARNING"
        assert "ANALYSIS_UNAVAILABLE" in resp.summary
        assert len(pipeline_hyps) == 0
    finally:
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_ENDPOINT", None)
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS", None)


def test_offline_daemon_with_fallback_engaged():
    """Verifies that when the daemon is offline and fallback is enabled, local evaluation engages honestly."""
    os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = "http://127.0.0.1:59999/submit"
    os.environ["JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS"] = "1.0"
    try:
        resp, record, pipeline_hyps = HypothesisAnalystTool.execute_hypothesis_analysis(
            research_question="What is the mechanism?",
            investigation_id="INV-OFFLINE-FALLBACK-TEST",
            case_study_id="CS-CAT-001",
            retrieved_evidence=[{"id": "CLM-WGS-001", "summary": "Formate rate is 0.14 of TOF", "supports_hypotheses": ["H1"], "refutes_hypotheses": ["H2"]}],
            timeout=1.0,
            allow_local_fallback=True,
        )

        assert resp.status == "ANALYSIS_UNAVAILABLE"
        assert record.status == "WARNING"
        assert record.input_arguments.get("fallback_engaged") is True
        assert len(pipeline_hyps) == 3
        assert sum(h.prior for h in pipeline_hyps) == pytest.approx(1.0, abs=1e-4)
    finally:
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_ENDPOINT", None)
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS", None)


def test_orchestrator_stage2_hypothesis_analyst_integration():
    """Verifies that ScientificInvestigationOrchestrator Stage 2 dispatches to HypothesisAnalystTool."""
    inp = InvestigationInput(
        question="Which mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inp)

    # Verify tool execution record is present
    hyp_rec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_hypothesis_analyst_uagent"), None)
    assert hyp_rec is not None, "Stage 2 must invoke janus_independent_hypothesis_analyst_uagent tool"
    assert hyp_rec.invoked_by == AgentRole.HYPOTHESIS
    assert "investigation_id" in hyp_rec.input_arguments

    # Verify hypotheses were ingested into report
    assert len(report.hypotheses) == 3
    assert sum(h.prior for h in report.hypotheses) == pytest.approx(1.0, abs=1e-4)

    # Verify Stage 2 log entry
    hyp_log = next((l for l in report.agent_logs if l.role == AgentRole.HYPOTHESIS and l.stage == "HYPOTHESIS_FORMULATION"), None)
    assert hyp_log is not None
    assert "Independent Hypothesis Analyst uAgent" in hyp_log.thought
    assert "Simplex sum" in hyp_log.thought


def test_live_hypothesis_inter_agent_communication_cycle():
    """
    Starts janus_hypothesis_analyst daemon on a test port in a background thread and tests
    a genuine synchronous request/response message exchange using HypothesisAnalystTool.
    """
    test_port = 8046
    test_endpoint = f"http://127.0.0.1:{test_port}/submit"

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ag = create_hypothesis_analyst_uagent(
            name="test_live_hypothesis_analyst",
            port=test_port,
            endpoint=[test_endpoint],
        )
        ag.run()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    time.sleep(2.0)  # Wait for uAgent socket binding

    os.environ["JANUS_HYPOTHESIS_ANALYST_ADDRESS"] = "agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d"
    os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = test_endpoint
    try:
        resp, record, pipeline_hyps = HypothesisAnalystTool.execute_hypothesis_analysis(
            research_question="Which reaction mechanism dominates in low-temperature water-gas shift on Pt/CeO2?",
            investigation_id="INV-LIVE-HYPOTHESIS-CYCLE",
            case_study_id="CS-CAT-001",
            retrieved_evidence=[
                {
                    "id": "CLM-WGS-001",
                    "statement": "Formate rate is 0.14 of TOF during SSITKA.",
                    "supports_hypotheses": ["H1", "H3"],
                    "refutes_hypotheses": ["H2"],
                    "confidence": 0.95,
                },
                {
                    "id": "CLM-WGS-002",
                    "statement": "Transient C16O over H218O gives 88% C16O2.",
                    "supports_hypotheses": ["H1"],
                    "refutes_hypotheses": ["H2"],
                    "confidence": 0.92,
                },
            ],
            timeout=6.0,
            allow_local_fallback=False,
        )

        assert resp.status == "ANALYSIS_COMPLETED"
        assert resp.agent_address == "agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d"
        assert len(resp.hypotheses) == 3
        assert resp.is_simplex_valid is True
        assert record.status == "SUCCESS"
        assert record.tool_name == "janus_independent_hypothesis_analyst_uagent"
        assert len(pipeline_hyps) == 3

        # Formate mechanism (H2) must be flagged as contradicted
        h2 = next(h for h in resp.hypotheses if h.id == "H2")
        assert h2.epistemic_status == "STRONGLY_CONTRADICTED"
        assert "CLM-WGS-001" in h2.contradicting_evidence_ids
    finally:
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_ADDRESS", None)
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_ENDPOINT", None)


# ==============================================================================
# Workstream A6: Regression Tests
# ==============================================================================

def test_regression_invalid_and_zero_priors():
    """Verifies that zero, negative, NaN, and Inf priors are safely rejected with ANALYSIS_UNAVAILABLE."""
    # Zero-total priors
    req_zero = HypothesisAnalysisRequest(
        correlation_id="corr-reg-zero",
        investigation_id="INV-REG-ZERO",
        research_question="Mechanism question?",
        case_study_id="CS-CAT-001",
        existing_priors={"H1": 0.0, "H2": 0.0, "H3": 0.0},
    )
    resp_zero = perform_hypothesis_analysis(req_zero, "agent1test")
    assert resp_zero.status == "ANALYSIS_UNAVAILABLE"
    assert resp_zero.is_simplex_valid is False
    assert resp_zero.simplex_sum == 0.0
    assert len(resp_zero.hypotheses) == 0
    assert any("zero or non-positive" in w for w in resp_zero.warnings)

    # Negative priors
    req_neg = HypothesisAnalysisRequest(
        correlation_id="corr-reg-neg",
        investigation_id="INV-REG-NEG",
        research_question="Mechanism question?",
        case_study_id="CS-CAT-001",
        existing_priors={"H1": -0.2, "H2": 0.7, "H3": 0.5},
    )
    resp_neg = perform_hypothesis_analysis(req_neg, "agent1test")
    assert resp_neg.status == "ANALYSIS_UNAVAILABLE"
    assert resp_neg.is_simplex_valid is False
    assert any("negative" in w for w in resp_neg.warnings)

    # NaN / Inf priors
    req_nan = HypothesisAnalysisRequest(
        correlation_id="corr-reg-nan",
        investigation_id="INV-REG-NAN",
        research_question="Mechanism question?",
        case_study_id="CS-CAT-001",
        existing_priors={"H1": float("nan"), "H2": 0.5, "H3": 0.5},
    )
    resp_nan = perform_hypothesis_analysis(req_nan, "agent1test")
    assert resp_nan.status == "ANALYSIS_UNAVAILABLE"
    assert resp_nan.is_simplex_valid is False
    assert any("non-finite" in w for w in resp_nan.warnings)


def test_regression_invalid_confidence_values():
    """Verifies that out-of-bounds, NaN, and malformed confidence values are safely clamped to [0.0, 1.0]."""
    evidence = [
        {"id": "EV-HIGH", "statement": "Statement", "supports_hypotheses": ["H1"], "confidence": 3.5},
        {"id": "EV-LOW", "statement": "Statement", "supports_hypotheses": ["H1"], "confidence": -1.2},
        {"id": "EV-NAN", "statement": "Statement", "supports_hypotheses": ["H1"], "confidence": float("nan")},
        {"id": "EV-STR", "statement": "Statement", "supports_hypotheses": ["H1"], "confidence": "invalid_num"},
    ]
    req = HypothesisAnalysisRequest(
        correlation_id="corr-reg-conf",
        investigation_id="INV-REG-CONF",
        research_question="WGS mechanism?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence,
    )
    resp = perform_hypothesis_analysis(req, "agent1test")
    assert resp.status == "ANALYSIS_COMPLETED"
    h1 = next(h for h in resp.hypotheses if h.id == "H1")
    for link in h1.evidence_links:
        assert 0.0 <= link.confidence_weight <= 1.0


def test_regression_missing_id_and_duplicate_evidence():
    """Verifies that evidence with missing IDs is safely ignored and duplicate evidence items are deduplicated."""
    evidence = [
        {"id": "", "statement": "No ID claim", "supports_hypotheses": ["H1"], "confidence": 0.9},
        {"id": "   ", "statement": "Whitespace ID", "supports_hypotheses": ["H1"], "confidence": 0.9},
        {"id": "EV-DUP-01", "statement": "Valid claim", "supports_hypotheses": ["H1"], "confidence": 0.9},
        {"id": "EV-DUP-01", "statement": "Duplicate claim", "supports_hypotheses": ["H1"], "confidence": 0.9},
    ]
    req = HypothesisAnalysisRequest(
        correlation_id="corr-reg-dup",
        investigation_id="INV-REG-DUP",
        research_question="WGS mechanism?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence,
    )
    resp = perform_hypothesis_analysis(req, "agent1test")
    h1 = next(h for h in resp.hypotheses if h.id == "H1")
    # Missing IDs must not produce empty links
    assert all(link.evidence_id.strip() != "" for link in h1.evidence_links)
    # EV-DUP-01 must only be linked once
    assert len([link for link in h1.evidence_links if link.evidence_id == "EV-DUP-01"]) == 1


def test_regression_contradictory_evidence_labels():
    """Verifies that evidence with contradictory tags or hypotheses with mixed evidence are transparently preserved."""
    # 1. Single item with both supporting and refuting tags
    evidence_conflicted = [
        {
            "id": "EV-CONFLICT-01",
            "statement": "Mixed isotopic signal.",
            "supports_hypotheses": ["H1"],
            "refutes_hypotheses": ["H1"],
            "confidence": 0.85,
        }
    ]
    req = HypothesisAnalysisRequest(
        correlation_id="corr-reg-conflict",
        investigation_id="INV-REG-CONFLICT",
        research_question="WGS mechanism?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence_conflicted,
    )
    resp = perform_hypothesis_analysis(req, "agent1test")
    h1 = next(h for h in resp.hypotheses if h.id == "H1")
    assert len(h1.evidence_links) == 1
    assert h1.evidence_links[0].relation_type == "INDIRECT"
    assert "conflicting tags" in h1.evidence_links[0].rationale

    # 2. Multiple items creating a contested candidate
    evidence_mixed = [
        {"id": "EV-SUP", "statement": "Supports H1", "supports_hypotheses": ["H1"], "confidence": 0.9},
        {"id": "EV-REF", "statement": "Refutes H1", "refutes_hypotheses": ["H1"], "confidence": 0.9},
    ]
    req2 = HypothesisAnalysisRequest(
        correlation_id="corr-reg-mixed",
        investigation_id="INV-REG-MIXED",
        research_question="WGS mechanism?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence_mixed,
    )
    resp2 = perform_hypothesis_analysis(req2, "agent1test")
    h1_mixed = next(h for h in resp2.hypotheses if h.id == "H1")
    assert "EV-SUP" in h1_mixed.supporting_evidence_ids
    assert "EV-REF" in h1_mixed.contradicting_evidence_ids
    assert any("contested" in w for w in resp2.warnings)


def test_regression_unsupported_scientific_domain():
    """Verifies that unsupported scientific domains return INSUFFICIENT_EVIDENCE with zero fabricated hypotheses."""
    req_unsupported = HypothesisAnalysisRequest(
        correlation_id="corr-reg-unsup",
        investigation_id="INV-REG-UNSUP",
        research_question="What causes lithium dendrite growth in solid-state batteries?",
        case_study_id="CS-BATTERY-888",
        retrieved_evidence=[{"id": "EV-BAT-01", "statement": "Dendrites grow along grain boundaries."}],
    )
    resp = perform_hypothesis_analysis(req_unsupported, "agent1test")
    assert resp.status == "INSUFFICIENT_EVIDENCE"
    assert len(resp.hypotheses) == 0
    assert resp.is_simplex_valid is False
    assert resp.simplex_sum == 0.0
    assert any("Unsupported scientific domain" in w for w in resp.warnings)
    assert "UNSUPPORTED_DOMAIN" in resp.summary

    # Ensure synthetic benchmark still operates as documented
    req_syn = HypothesisAnalysisRequest(
        correlation_id="corr-reg-syn",
        investigation_id="INV-REG-SYN",
        research_question="Kinase inhibition model?",
        case_study_id="SYN-001",
        retrieved_evidence=[],
    )
    resp_syn = perform_hypothesis_analysis(req_syn, "agent1test")
    assert len(resp_syn.hypotheses) == 3
    assert resp_syn.is_simplex_valid is True


def test_regression_false_positive_substring_matching():
    """Verifies that words like 'which1', 'KOH1', and 'H2O'/'H2 gas' do not trigger false positive hypothesis matches."""
    evidence = [
        {"id": "EV-FALSE-H1", "statement": "The catalyst which1 was calcined with KOH1 showed stability.", "confidence": 0.9},
        {"id": "EV-FALSE-H2", "statement": "Water dissociation produces H2 gas and H2O vapor rapidly.", "confidence": 0.9},
        {"id": "EV-TRUE-H2", "statement": "Recent spectroscopic studies confirm Hypothesis 2 is viable.", "confidence": 0.9},
    ]
    req = HypothesisAnalysisRequest(
        correlation_id="corr-reg-substr",
        investigation_id="INV-REG-SUBSTR",
        research_question="WGS mechanism?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence,
    )
    resp = perform_hypothesis_analysis(req, "agent1test")
    h1 = next(h for h in resp.hypotheses if h.id == "H1")
    h2 = next(h for h in resp.hypotheses if h.id == "H2")

    # EV-FALSE-H1 must NOT link to H1
    assert "EV-FALSE-H1" not in [link.evidence_id for link in h1.evidence_links]

    # EV-FALSE-H2 must NOT link to H2 (H2 gas / H2O is not Hypothesis 2)
    assert "EV-FALSE-H2" not in [link.evidence_id for link in h2.evidence_links]

    # EV-TRUE-H2 explicitly says "Hypothesis 2", so it MUST link to H2
    assert "EV-TRUE-H2" in [link.evidence_id for link in h2.evidence_links]


def test_regression_offline_fallback_consistency():
    """Verifies that offline fallback preserves daemon unavailability while reporting consistent simplex sums."""
    os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = "http://127.0.0.1:59999/submit"
    os.environ["JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS"] = "1.0"
    try:
        resp, record, pipeline_hyps = HypothesisAnalystTool.execute_hypothesis_analysis(
            research_question="What is the mechanism?",
            investigation_id="INV-REG-FALLBACK",
            case_study_id="CS-CAT-001",
            retrieved_evidence=[{"id": "CLM-WGS-001", "summary": "Formate rate is 0.14 of TOF", "supports_hypotheses": ["H1"]}],
            timeout=1.0,
            allow_local_fallback=True,
        )

        assert resp.status == "ANALYSIS_UNAVAILABLE"
        assert record.status == "WARNING"
        assert record.input_arguments.get("fallback_engaged") is True
        assert len(pipeline_hyps) == 3
        # Response simplex must correspond to the returned hypotheses (not 0.0)
        assert resp.is_simplex_valid is True
        assert resp.simplex_sum == pytest.approx(1.0, abs=1e-4)
        assert len(resp.hypotheses) == 3
        assert any("fallback analysis engaged" in w for w in resp.warnings)
    finally:
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_ENDPOINT", None)
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS", None)


def test_regression_confidence_and_verification_metadata_handling():
    """Verifies that bibliographic mismatch/missing DOI dampens confidence without negating scientific relation."""
    evidence = [
        {
            "id": "EV-ONLINE",
            "statement": "Online verified DOI.",
            "supports_hypotheses": ["H1"],
            "confidence": 0.90,
            "doi_verification_status": "BIBLIOGRAPHIC_VERIFIED_ONLINE",
        },
        {
            "id": "EV-MISMATCH",
            "statement": "Mismatch DOI metadata.",
            "supports_hypotheses": ["H1"],
            "confidence": 0.90,
            "doi_verification_status": "METADATA_MISMATCH",
        },
        {
            "id": "EV-NOTFOUND",
            "statement": "DOI not in Crossref.",
            "supports_hypotheses": ["H1"],
            "confidence": 0.90,
            "doi_verification_status": "DOI_NOT_FOUND",
        },
    ]
    req = HypothesisAnalysisRequest(
        correlation_id="corr-reg-meta",
        investigation_id="INV-REG-META",
        research_question="WGS mechanism?",
        case_study_id="CS-CAT-001",
        retrieved_evidence=evidence,
    )
    resp = perform_hypothesis_analysis(req, "agent1test")
    h1 = next(h for h in resp.hypotheses if h.id == "H1")
    link_map = {l.evidence_id: l for l in h1.evidence_links}

    # All three must maintain the SUPPORTING relation (bibliographic status does not disprove the science)
    assert link_map["EV-ONLINE"].relation_type == "SUPPORTING"
    assert link_map["EV-MISMATCH"].relation_type == "SUPPORTING"
    assert link_map["EV-NOTFOUND"].relation_type == "SUPPORTING"

    # Confidences are proportionally dampened for bibliographic uncertainty
    assert link_map["EV-ONLINE"].confidence_weight == 0.90
    assert link_map["EV-MISMATCH"].confidence_weight == 0.63  # round(0.9 * 0.7, 2)
    assert link_map["EV-NOTFOUND"].confidence_weight == 0.54  # round(0.9 * 0.6, 2)
