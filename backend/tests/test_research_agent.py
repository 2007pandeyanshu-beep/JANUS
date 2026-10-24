"""Tests for JANUS Independent Scientific Research uAgent (Phase 4).

Verifies:
1. Research request, response, and evidence schemas serialization and field validation.
2. Distinct agent identity and cryptographic address between Primary, Auditor, and Research agents.
3. Authentic scientific literature retrieval and Crossref bibliographic validation on WGS and OER scenarios.
4. Honest empty results handling (RESEARCH_EMPTY, zero hallucinations).
5. Discrepancy and mismatch detection (RESEARCH_PARTIAL with actionable warnings).
6. Honest reporting when daemon is offline (RESEARCH_UNAVAILABLE, never fabricating success).
7. Traceable provenance, author extraction, and relevance explanations.
8. Full correlation ID and investigation ID preservation across turns.
9. ScientificInvestigationOrchestrator Stage 1 integration.
10. Live inter-agent request/response message exchange over native Fetch.ai uAgents protocol.
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
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_test_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.schemas.research import (
    ScientificResearchRequest,
    ScientificResearchResponse,
    ResearchEvidenceItem,
)
from app.schemas.scientific import Evidence
from agents.tools import (
    ResearchAgentTool,
    AuditorAgentTool,
    LiteratureRetrievalTool,
    CrossrefValidationTool,
    BibliographicVerificationStatus,
)
from agents.research_agent import (
    create_research_uagent,
    perform_scientific_research,
    scientific_research_proto,
)
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import InvestigationInput, AgentRole, ToolExecutionRecord


def test_research_schemas_serialization_and_validation():
    """Verifies that research request, response, and evidence models serialize cleanly."""
    item = ResearchEvidenceItem(
        id="CLM-TEST-001",
        title="Operando DRIFTS Study of WGS Formate Intermediates",
        authors=["F. C. Meunier", "D. Tibiletti"],
        source="Meunier et al., J. Catal. 252 (2007) 18–22",
        source_doi="10.1016/j.jcat.2007.10.004",
        source_url="https://doi.org/10.1016/j.jcat.2007.10.004",
        provenance="empirical_drifts",
        summary="Formate bands observed during transient WGS pulse tests.",
        relevance_explanation="Directly informs associative vs redox mechanism comparison.",
        confidence=0.95,
        doi_verification_status="BIBLIOGRAPHIC_VERIFIED_ONLINE",
        doi_verification_message="Publisher record matched exactly",
        bibliographic_metadata={"year": 2007, "journal": "Journal of Catalysis"},
    )
    assert item.id == "CLM-TEST-001"
    assert item.confidence == 0.95

    req = ScientificResearchRequest(
        correlation_id="corr-test-101",
        investigation_id="INV-UNITTEST-01",
        research_question="Which reaction mechanism dominates WGS on Pt/CeO2?",
        case_study_id="CS-CAT-001",
        topic_context="Pt/CeO2 low temperature WGS",
        max_results=5,
    )
    dumped_req = req.model_dump()
    assert dumped_req["correlation_id"] == "corr-test-101"
    assert dumped_req["investigation_id"] == "INV-UNITTEST-01"

    restored_req = ScientificResearchRequest.model_validate(dumped_req)
    assert restored_req.research_question == req.research_question

    resp = ScientificResearchResponse(
        correlation_id="corr-test-101",
        investigation_id="INV-UNITTEST-01",
        status="RESEARCH_COMPLETED",
        agent_address="agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py",
        timestamp=datetime.now(timezone.utc).isoformat(),
        evidence_items=[item],
        total_evidence_count=1,
        verified_online_count=1,
        cached_offline_count=0,
        metadata_mismatch_count=0,
        not_found_count=0,
        warnings=[],
        execution_summary="RESEARCH_COMPLETED: 1 item verified online.",
    )
    dumped_resp = resp.model_dump()
    assert dumped_resp["status"] == "RESEARCH_COMPLETED"
    assert len(dumped_resp["evidence_items"]) == 1

    restored_resp = ScientificResearchResponse.model_validate(dumped_resp)
    assert restored_resp.status == "RESEARCH_COMPLETED"
    assert restored_resp.total_evidence_count == 1


def test_research_agent_identity_distinct():
    """Verifies that Research uAgent has its own seed, protocol, and distinct address."""
    research_agent = create_research_uagent(port=8010)
    assert research_agent.name == "janus_research_agent"
    assert research_agent.address.startswith("agent1")
    assert research_agent.address == "agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py"

    # Distinct from Auditor Agent address
    from agents.auditor_agent import create_auditor_uagent
    auditor_agent = create_auditor_uagent(port=8009)
    assert research_agent.address != auditor_agent.address

    # Distinct from Primary Agent address
    from agents.fetch_agent import create_janus_uagent
    primary_agent = create_janus_uagent(seed="janus_primary_evaluation_seed_demo")
    assert research_agent.address != primary_agent.address
    assert auditor_agent.address != primary_agent.address


def test_perform_scientific_research_wgs_scenario():
    """Verifies authentic retrieval and Crossref validation for WGS case study inquiry."""
    req = ScientificResearchRequest(
        correlation_id="corr-wgs-research-test",
        investigation_id="INV-WGS-TEST",
        research_question="Which reaction mechanism dominates in low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
        max_results=7,
    )
    resp = perform_scientific_research(
        request=req,
        agent_address="agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py",
    )

    assert resp.status == "RESEARCH_COMPLETED"
    assert resp.investigation_id == "INV-WGS-TEST"
    assert resp.correlation_id == "corr-wgs-research-test"
    assert resp.total_evidence_count >= 4
    assert resp.metadata_mismatch_count == 0
    assert resp.not_found_count == 0
    assert resp.verified_online_count >= 1

    # Check evidence structure and provenance
    for item in resp.evidence_items:
        assert item.id.startswith("CLM-WGS-")
        assert len(item.title) > 5
        assert len(item.source) > 5
        assert item.source_doi is not None
        assert item.doi_verification_status in (
            "BIBLIOGRAPHIC_VERIFIED_ONLINE",
            "BIBLIOGRAPHIC_CACHED_OFFLINE",
        )
        assert item.relevance_explanation is not None
        assert len(item.relevance_explanation) > 10


def test_perform_scientific_research_oer_scenario():
    """Verifies authentic retrieval and Crossref validation for OER perovskite inquiry."""
    req = ScientificResearchRequest(
        correlation_id="corr-oer-research-test",
        investigation_id="INV-OER-TEST",
        research_question="Which reaction mechanism dominates oxygen evolution on La_{1-x}Sr_xCoO_{3-delta}?",
        case_study_id="CS-OER-002",
        max_results=5,
    )
    resp = perform_scientific_research(
        request=req,
        agent_address="agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py",
    )

    assert resp.status == "RESEARCH_COMPLETED"
    assert resp.total_evidence_count == 4
    assert resp.verified_online_count == 4
    assert resp.metadata_mismatch_count == 0
    assert resp.not_found_count == 0

    # Ensure EVD-OER-04 (acscatal.5b02432) is verified online
    oer_04 = next((e for e in resp.evidence_items if e.id == "EVD-OER-04"), None)
    assert oer_04 is not None
    assert oer_04.source_doi == "10.1021/acscatal.5b02432"
    assert oer_04.doi_verification_status == "BIBLIOGRAPHIC_VERIFIED_ONLINE"


def test_perform_scientific_research_empty_results():
    """Verifies strictly honest handling of unknown/empty domain without fabricating citations."""
    req = ScientificResearchRequest(
        correlation_id="corr-empty-test",
        investigation_id="INV-EMPTY-TEST",
        research_question="Quantum decoherence of topological Majorana fermions in 2D semiconductor-superconductor nanowires",
        case_study_id="UNKNOWN_DOMAIN_999",
    )
    resp = perform_scientific_research(
        request=req,
        agent_address="agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py",
    )

    assert resp.status == "RESEARCH_EMPTY"
    assert resp.total_evidence_count == 0
    assert len(resp.evidence_items) == 0
    assert "No empirical literature evidence found" in resp.execution_summary
    assert len(resp.warnings) >= 1


def test_perform_scientific_research_detects_metadata_mismatch():
    """Verifies that a bibliographic discrepancy is flagged as RESEARCH_PARTIAL with warnings."""
    # Mock LiteratureRetrievalTool to return an item with an intentionally mismatched DOI
    mismatched_ev = Evidence(
        id="CLM-SYN-001",
        title="Operando DRIFTS Study of WGS Formate Intermediates",
        source="Meunier et al., J. Catal. 252 (2007) 18–22",
        source_doi="10.1016/j.jcat.2007.09.006",  # Resolves to Conesa paper on Beckmann rearrangement!
        provenance="literature_derived",
        summary="Claims formate bands observed.",
        confidence=0.8,
    )

    with patch.object(LiteratureRetrievalTool, "execute", return_value=([mismatched_ev], MagicMock())):
        req = ScientificResearchRequest(
            correlation_id="corr-mismatch-test",
            investigation_id="INV-MISMATCH-TEST",
            research_question="Test question",
            case_study_id="SYN-001",
        )
        resp = perform_scientific_research(
            request=req,
            agent_address="agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py",
        )

        assert resp.status == "RESEARCH_PARTIAL"
        assert resp.metadata_mismatch_count == 1
        assert len(resp.warnings) >= 1
        assert any("METADATA_MISMATCH" in w for w in resp.warnings)


def test_research_agent_tool_truthful_when_offline():
    """
    Verifies strictly truthful reporting: when research daemon is offline or unreachable,
    ResearchAgentTool returns RESEARCH_UNAVAILABLE and does NOT claim the uAgent was reached.
    """
    # Point to an unallocated port
    os.environ["JANUS_RESEARCH_AGENT_ENDPOINT"] = "http://127.0.0.1:54322/submit"
    try:
        # Strict mode: fallback disabled
        resp, record, pipeline_ev = ResearchAgentTool.execute_research(
            research_question="Which reaction mechanism dominates WGS on Pt/CeO2?",
            investigation_id="INV-OFFLINE-TEST",
            case_study_id="CS-CAT-001",
            timeout=0.5,
            allow_local_fallback=False,
        )

        assert resp.status == "RESEARCH_UNAVAILABLE"
        assert record.status == "WARNING"
        assert len(pipeline_ev) == 0
        assert "RESEARCH_UNAVAILABLE" in resp.execution_summary
        assert "connection failed" in resp.execution_summary or "unreachable" in resp.execution_summary

        # Resilient mode: fallback enabled
        resp_fb, record_fb, pipeline_ev_fb = ResearchAgentTool.execute_research(
            research_question="Which reaction mechanism dominates WGS on Pt/CeO2?",
            investigation_id="INV-OFFLINE-FALLBACK",
            case_study_id="CS-CAT-001",
            timeout=0.5,
            allow_local_fallback=True,
        )

        assert resp_fb.status == "RESEARCH_UNAVAILABLE"
        assert record_fb.status == "WARNING"
        assert record_fb.input_arguments.get("fallback_engaged") is True
        assert len(pipeline_ev_fb) >= 4  # Local fallback preserved pipeline viability
    finally:
        os.environ.pop("JANUS_RESEARCH_AGENT_ENDPOINT", None)


def test_correlation_and_investigation_id_preservation():
    """Verifies that incoming correlation and investigation identifiers are strictly echoed."""
    test_corr_id = "corr-custom-trace-uuid-8899"
    test_inv_id = "INV-CUSTOM-77"

    req = ScientificResearchRequest(
        correlation_id=test_corr_id,
        investigation_id=test_inv_id,
        research_question="Which WGS reaction mechanism dominates on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    resp = perform_scientific_research(
        request=req,
        agent_address="agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py",
    )

    assert resp.correlation_id == test_corr_id
    assert resp.investigation_id == test_inv_id


def test_orchestrator_stage1_research_agent_integration():
    """Verifies that ScientificInvestigationOrchestrator Stage 1 dispatches to ResearchAgentTool."""
    inp = InvestigationInput(
        question="Which mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inp)

    # Verify tool execution record is present
    research_rec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_research_uagent"), None)
    assert research_rec is not None, "Stage 1 must invoke janus_independent_research_uagent tool"
    assert research_rec.invoked_by == AgentRole.RESEARCH
    assert "investigation_id" in research_rec.input_arguments

    # Verify evidence items were ingested into report
    assert len(report.retrieved_evidence) >= 4

    # Verify Stage 1 logs indicate Research uAgent dispatch
    dispatch_log = next((l for l in report.agent_logs if l.stage == "RESEARCH_AGENT_DISPATCH"), None)
    assert dispatch_log is not None
    assert "janus_scientific_research" in dispatch_log.action_taken


def test_live_research_inter_agent_communication_cycle():
    """
    Starts janus_research_agent daemon on a test port in a background thread and tests
    a genuine synchronous request/response message exchange using ResearchAgentTool.
    """
    test_port = 8045
    test_endpoint = f"http://127.0.0.1:{test_port}/submit"

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ag = create_research_uagent(
            name="test_live_research_agent",
            port=test_port,
            endpoint=[test_endpoint],
        )
        ag.run()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    time.sleep(2.0)  # Wait for uAgent socket binding

    os.environ["JANUS_RESEARCH_AGENT_ADDRESS"] = "agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py"
    os.environ["JANUS_RESEARCH_AGENT_ENDPOINT"] = test_endpoint
    try:
        resp, record, pipeline_ev = ResearchAgentTool.execute_research(
            research_question="Which reaction mechanism dominates in low-temperature water-gas shift on Pt/CeO2?",
            investigation_id="INV-LIVE-RESEARCH-CYCLE",
            case_study_id="CS-CAT-001",
            timeout=6.0,
            allow_local_fallback=False,
        )

        assert resp.status == "RESEARCH_COMPLETED"
        assert resp.agent_address == "agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py"
        assert resp.total_evidence_count >= 4
        assert resp.verified_online_count >= 1
        assert record.status == "SUCCESS"
        assert record.tool_name == "janus_independent_research_uagent"
        assert len(pipeline_ev) >= 4
    finally:
        os.environ.pop("JANUS_RESEARCH_AGENT_ADDRESS", None)
        os.environ.pop("JANUS_RESEARCH_AGENT_ENDPOINT", None)
