"""Tests for JANUS Independent Scientific Auditor uAgent (Phase 3).

Verifies:
1. Audit request and response contract schema serialization.
2. Distinct agent identity and address between Primary Agent and Auditor Agent.
3. Auditor independent recalculation of mathematical invariants:
   - Prior simplex normalization
   - Likelihood row stochasticity
   - Shannon entropy and EIG bounds (0 <= EIG <= H)
   - Authoritative composite utility ranking
   - Sequential Bayesian posterior update (Bayes' rule)
4. Corrupted invariant detection (AUDIT_FAILED for bad priors, bad likelihoods, violated bounds, false rankings).
5. Truthful reporting when daemon is offline or unreachable (AUDIT_UNAVAILABLE, never claim verified).
6. Orchestrator Stage 5 Critic integration (CRT-006 recording external auditor verdict).
7. Live synchronous inter-agent message exchange over native Fetch.ai uAgents protocol.
"""

import os
import sys
import math
import threading
import time
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any

from app.schemas.audit import (
    ScientificAuditRequest,
    ScientificAuditResponse,
    AuditCheckItem,
)
from app.schemas.scientific import (
    AnalysisInput,
    AnalysisResult,
    Hypothesis,
    Experiment,
    Evidence,
    ExperimentScore,
    PredictedOutcome,
)
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.engine import ScientificEngine
from scientific.sequential_engine import compute_bayesian_posterior_update
from scientific.validation import IndependentEngineVerifier
from agents.tools import AuditorAgentTool
from agents.auditor_agent import (
    create_auditor_uagent,
    perform_independent_audit,
    scientific_audit_proto,
)
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import InvestigationInput, CriticSeverity


def test_audit_schemas_serialization():
    """Verifies that ScientificAuditRequest and ScientificAuditResponse serialize cleanly."""
    check = AuditCheckItem(
        check_id="prior_simplex_normalization",
        status="PASS",
        message="Simplex satisfied",
        details={"sum": 1.0},
    )
    assert check.status == "PASS"

    resp = ScientificAuditResponse(
        correlation_id="corr-123",
        status="AUDIT_PASSED",
        auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=[check],
        all_invariants_hold=True,
        passed_checks_count=1,
        total_checks_count=1,
        mismatches=[],
        bibliographic_mismatch_notices=[],
        verdict="All invariants hold",
    )
    dumped = resp.model_dump()
    assert dumped["status"] == "AUDIT_PASSED"
    assert dumped["correlation_id"] == "corr-123"

    restored = ScientificAuditResponse.model_validate(dumped)
    assert restored.all_invariants_hold is True
    assert len(restored.checks) == 1


def test_auditor_agent_identity_and_address_distinct():
    """Verifies that Auditor uAgent has its own seed, port, protocol, and distinct address."""
    auditor = create_auditor_uagent(port=8009)
    assert auditor.address == "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
    assert auditor.name == "janus_auditor_agent"

    # Distinct from any primary agent seed address
    from agents.fetch_agent import create_janus_uagent
    primary = create_janus_uagent(seed="janus_primary_evaluation_seed_demo")
    assert auditor.address != primary.address
    assert auditor.address.startswith("agent1")
    assert primary.address.startswith("agent1")


def test_perform_independent_audit_valid_analysis():
    """Verifies that a valid deterministic analysis on CS-CAT-001 receives AUDIT_PASSED."""
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    req = ScientificAuditRequest(
        correlation_id="corr-valid-1",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in result.ranked_experiments],
        selected_recommendation=result.ranked_experiments[0].model_dump(),
        evidence_ledger=[ev.model_dump() for ev in scenario.evidence],
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_PASSED"
    assert resp.all_invariants_hold is True
    assert resp.passed_checks_count == resp.total_checks_count
    assert len(resp.mismatches) == 0


def test_perform_independent_audit_detects_corrupted_priors():
    """Verifies that an unnormalized prior distribution triggers AUDIT_FAILED."""
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    # Corrupt priors so sum = 0.70 instead of 1.00
    corrupted_hypotheses = [h.model_dump() for h in scenario.hypotheses]
    corrupted_hypotheses[0]["prior"] = 0.20  # sum = 0.20 + 0.20 + 0.30 = 0.70

    req = ScientificAuditRequest(
        correlation_id="corr-corrupt-priors",
        scenario_id="CS-CAT-001",
        hypotheses=corrupted_hypotheses,
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in result.ranked_experiments],
        selected_recommendation=result.ranked_experiments[0].model_dump(),
        evidence_ledger=[],
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_FAILED"
    assert resp.all_invariants_hold is False
    assert any("prior_simplex" in c.check_id and c.status == "FAIL" for c in resp.checks)
    assert any("Prior simplex violation" in m for m in resp.mismatches)


def test_perform_independent_audit_detects_corrupted_likelihoods():
    """Verifies that non-stochastic likelihood rows trigger AUDIT_FAILED."""
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    corrupted_experiments = [e.model_dump() for e in scenario.experiments]
    # Corrupt predictions for EXP-WGS-01 so probabilities sum to 1.50
    for p in corrupted_experiments[0]["predictions"]:
        if p["hypothesis_id"] == "H1":
            p["probability"] = 0.99  # was 0.90, will cause sum > 1.0

    req = ScientificAuditRequest(
        correlation_id="corr-corrupt-lik",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=corrupted_experiments,
        ranked_scores=[s.model_dump() for s in result.ranked_experiments],
        selected_recommendation=result.ranked_experiments[0].model_dump(),
        evidence_ledger=[],
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_FAILED"
    assert resp.all_invariants_hold is False
    assert any("likelihood_stochasticity" in c.check_id and c.status == "FAIL" for c in resp.checks)


def test_perform_independent_audit_detects_violated_eig_bounds():
    """Verifies that an EIG exceeding Shannon prior entropy H(P) triggers AUDIT_FAILED."""
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    corrupted_scores = [s.model_dump() for s in result.ranked_experiments]
    # Invariant: 0 <= EIG <= H(P). Set EIG to 5.0 (impossible since H(P) <= log2(3) ~ 1.585)
    corrupted_scores[0]["expected_information_gain"] = 5.0

    req = ScientificAuditRequest(
        correlation_id="corr-corrupt-eig",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=corrupted_scores,
        selected_recommendation=corrupted_scores[0],
        evidence_ledger=[],
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_FAILED"
    assert resp.all_invariants_hold is False
    assert any("scoring_invariants" in c.check_id and c.status == "FAIL" for c in resp.checks)


def test_perform_independent_audit_detects_corrupted_ranking_order():
    """Verifies that inverted utility scores trigger an authoritative ranking violation."""
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    corrupted_scores = [s.model_dump() for s in result.ranked_experiments]
    # Swap rank 0 and rank 1 without swapping utility values
    corrupted_scores[0], corrupted_scores[1] = corrupted_scores[1], corrupted_scores[0]
    corrupted_scores[0]["rank"] = 1
    corrupted_scores[1]["rank"] = 2

    req = ScientificAuditRequest(
        correlation_id="corr-corrupt-rank",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=corrupted_scores,
        selected_recommendation=corrupted_scores[0],
        evidence_ledger=[],
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_FAILED"
    assert resp.all_invariants_hold is False
    assert any("authoritative_utility_ranking_order" in c.check_id and c.status == "FAIL" for c in resp.checks)


def test_perform_independent_audit_sequential_update_valid():
    """Verifies that an authentic sequential Bayesian update receives AUDIT_PASSED."""
    scenario = get_wgs_case_study_scenario()
    init_priors = {h.id: h.prior for h in scenario.hypotheses}

    # Simulate observing EXP-WGS-02 = Initial_CO2_Mainly_Lattice_16O
    exp_02 = next(e for e in scenario.experiments if e.id == "EXP-WGS-02")
    out_label = "Initial_CO2_Mainly_Lattice_16O"
    lik_vector = {p.hypothesis_id: p.probability for p in exp_02.predictions if p.outcome_label == out_label}
    # Marginal P(y) = 0.50*0.92 + 0.20*0.08 + 0.30*0.12 = 0.512
    # P(H1|y) = 0.460 / 0.512 = 0.8984375
    calc_posteriors = {
        "H1": (init_priors["H1"] * lik_vector["H1"]) / 0.512,
        "H2": (init_priors["H2"] * lik_vector["H2"]) / 0.512,
        "H3": (init_priors["H3"] * lik_vector["H3"]) / 0.512,
    }

    updated_hypotheses = [
        Hypothesis(id=h.id, name=h.name, prior=calc_posteriors[h.id], description=h.description)
        for h in scenario.hypotheses
    ]
    remaining_experiments = [e for e in scenario.experiments if e.id != "EXP-WGS-02"]
    re_ranked_scenario = AnalysisInput(
        scenario_name="WGS re-ranked",
        scenario_type="published_case_study",
        case_study_id="CS-CAT-001",
        hypotheses=updated_hypotheses,
        experiments=remaining_experiments,
        evidence=scenario.evidence,
        cost_weight=0.1,
    )
    re_ranked_result = ScientificEngine.execute_analysis(re_ranked_scenario)

    req = ScientificAuditRequest(
        correlation_id="corr-seq-valid",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in updated_hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in re_ranked_result.ranked_experiments],
        selected_recommendation=re_ranked_result.ranked_experiments[0].model_dump(),
        evidence_ledger=[],
        is_sequential_update=True,
        initial_priors_before=init_priors,
        observed_experiment_id="EXP-WGS-02",
        observed_outcome=out_label,
        observed_posteriors=calc_posteriors,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_PASSED"
    assert resp.all_invariants_hold is True
    assert any("bayesian_sequential_update" in c.check_id and c.status == "PASS" for c in resp.checks)


def test_perform_independent_audit_sequential_update_detects_bad_posteriors():
    """Verifies that falsified posterior beliefs trigger AUDIT_FAILED on sequential update."""
    scenario = get_wgs_case_study_scenario()
    init_priors = {h.id: h.prior for h in scenario.hypotheses}
    result = ScientificEngine.execute_analysis(scenario)

    out_label = "Initial_CO2_Mainly_Lattice_16O"
    # Fabricated posteriors that do not match Bayes' rule
    fake_posteriors = {"H1": 0.333, "H2": 0.333, "H3": 0.334}

    req = ScientificAuditRequest(
        correlation_id="corr-seq-corrupt",
        scenario_id="CS-CAT-001",
        hypotheses=[{"id": hid, "prior": val, "name": hid} for hid, val in fake_posteriors.items()],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in result.ranked_experiments if s.experiment_id != "EXP-WGS-02"],
        selected_recommendation=result.ranked_experiments[1].model_dump(),
        evidence_ledger=[],
        is_sequential_update=True,
        initial_priors_before=init_priors,
        observed_experiment_id="EXP-WGS-02",
        observed_outcome=out_label,
        observed_posteriors=fake_posteriors,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_FAILED"
    assert resp.all_invariants_hold is False
    assert any("bayesian_sequential_update" in c.check_id and c.status == "FAIL" for c in resp.checks)


def test_auditor_agent_tool_truthful_when_offline():
    """
    Verifies strictly truthful reporting: when auditor daemon is offline or unreachable,
    AuditorAgentTool returns AUDIT_UNAVAILABLE and NEVER fabricates AUDIT_PASSED.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    # Point to an unallocated port to guarantee connection refused
    os.environ["JANUS_AUDITOR_ENDPOINT"] = "http://127.0.0.1:54321/submit"
    try:
        resp, record = AuditorAgentTool.audit_analysis(
            analysis_result=result,
            scenario_input=scenario,
            correlation_id="corr-offline-test",
            timeout=0.5,
        )

        assert resp.status == "AUDIT_UNAVAILABLE"
        assert resp.all_invariants_hold is False
        assert "AUDIT_UNAVAILABLE" in resp.verdict
        assert record.status == "WARNING"
        assert record.tool_name == "janus_independent_auditor_uagent"
    finally:
        os.environ.pop("JANUS_AUDITOR_ENDPOINT", None)


def test_orchestrator_stage5_critic_registers_auditor_status():
    """
    Verifies that ScientificInvestigationOrchestrator Stage 5 Critic registers CRT-006
    recording the external auditor uAgent's verdict and address.
    """
    inp = InvestigationInput(
        question="Which WGS reaction mechanism dominates on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inp)

    # Check that CRT-006 is present in critic items
    crt_006 = next((c for c in report.critic_review if c.id == "CRT-006"), None)
    assert crt_006 is not None, "CRT-006 must be recorded by Stage 5 Critic"
    assert "Independent Auditor uAgent" in crt_006.target_claim_or_object
    assert "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg" in crt_006.target_claim_or_object

    # Check analysis_result.independent_verification contains auditor_uagent dict
    assert report.analysis_result is not None
    assert report.analysis_result.independent_verification is not None
    assert "auditor_uagent" in report.analysis_result.independent_verification


def test_live_inter_agent_communication_cycle():
    """
    Starts janus_auditor_uagent daemon on a test port in a background thread and tests
    a genuine synchronous request/response message exchange using AuditorAgentTool.
    """
    import asyncio
    test_port = 8044
    test_endpoint = f"http://127.0.0.1:{test_port}/submit"

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ag = create_auditor_uagent(
            name="test_live_auditor",
            port=test_port,
            endpoint=[test_endpoint],
        )
        ag.run()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    time.sleep(2.0)  # Wait for uAgent server to bind socket

    os.environ["JANUS_AUDITOR_ADDRESS"] = "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
    os.environ["JANUS_AUDITOR_ENDPOINT"] = test_endpoint
    try:
        scenario = get_wgs_case_study_scenario()
        result = ScientificEngine.execute_analysis(scenario)

        resp, record = AuditorAgentTool.audit_analysis(
            analysis_result=result,
            scenario_input=scenario,
            correlation_id="corr-live-inter-agent",
            timeout=5.0,
        )

        assert resp.status == "AUDIT_PASSED"
        assert resp.all_invariants_hold is True
        assert resp.auditor_address == "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
        assert record.status == "SUCCESS"
        assert record.tool_name == "janus_independent_auditor_uagent"
    finally:
        os.environ.pop("JANUS_AUDITOR_ADDRESS", None)
        os.environ.pop("JANUS_AUDITOR_ENDPOINT", None)


def test_perform_independent_audit_all_14_mandatory_checks_pass():
    """
    Verifies that the canonical WGS case study produces exactly 14/14 checks,
    all 14 mandatory checks pass, status is AUDIT_PASSED, and zero mismatches exist.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    req = ScientificAuditRequest(
        correlation_id="corr-all-14-pass",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in result.ranked_experiments],
        selected_recommendation=result.ranked_experiments[0].model_dump(),
        evidence_ledger=[ev.model_dump() for ev in scenario.evidence],
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_PASSED"
    assert resp.all_invariants_hold is True
    assert resp.total_checks_count == 14
    assert resp.passed_checks_count == 14
    assert resp.mandatory_checks_count == 14
    assert resp.mandatory_passed_count == 14
    assert resp.warnings_count == 0
    assert len(resp.mismatches) == 0
    assert "All 14/14 mandatory mathematical and integrity checks verified" in resp.verdict


def test_perform_independent_audit_bibliographic_mismatch_yields_audit_failed():
    """
    Verifies that if Check 14 (scholarly_literature_bibliographic_consistency) detects
    a METADATA_MISMATCH, the audit truthfully evaluates to AUDIT_FAILED and cannot report success.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    # Corrupt one evidence record with METADATA_MISMATCH
    corrupted_evidence = [ev.model_dump() for ev in scenario.evidence]
    corrupted_evidence[0]["doi_verification_status"] = "METADATA_MISMATCH"

    req = ScientificAuditRequest(
        correlation_id="corr-biblio-mismatch",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in result.ranked_experiments],
        selected_recommendation=result.ranked_experiments[0].model_dump(),
        evidence_ledger=corrupted_evidence,
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_FAILED"
    assert resp.all_invariants_hold is False
    assert resp.passed_checks_count == 13
    assert resp.total_checks_count == 14
    assert resp.mandatory_passed_count == 13
    assert resp.mandatory_checks_count == 14
    biblio_check = next(c for c in resp.checks if c.check_id == "scholarly_literature_bibliographic_consistency")
    assert biblio_check.status == "FAIL"
    assert biblio_check.is_mandatory is True
    assert any("Bibliographic integrity failure" in m for m in resp.mismatches)
    assert resp.verdict.startswith("AUDIT_FAILED")


def test_perform_independent_audit_warning_distinguished_from_failure():
    """
    Verifies that non-critical warnings (e.g. UNAVAILABLE network lookup on offline cache)
    are distinguished from mandatory failures: audit status is AUDIT_PASSED, warnings_count > 0.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)

    # Set one evidence record to UNAVAILABLE
    warning_evidence = [ev.model_dump() for ev in scenario.evidence]
    warning_evidence[0]["doi_verification_status"] = "UNAVAILABLE"

    req = ScientificAuditRequest(
        correlation_id="corr-warning-test",
        scenario_id="CS-CAT-001",
        hypotheses=[h.model_dump() for h in scenario.hypotheses],
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in result.ranked_experiments],
        selected_recommendation=result.ranked_experiments[0].model_dump(),
        evidence_ledger=warning_evidence,
        is_sequential_update=False,
    )

    resp = perform_independent_audit(req, auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg")
    assert resp.status == "AUDIT_PASSED"
    assert resp.all_invariants_hold is True
    assert resp.mandatory_passed_count == resp.mandatory_checks_count
    assert resp.warnings_count >= 1
    assert any(c.status == "WARNING" and not c.is_mandatory for c in resp.checks)
    assert "non-critical warning(s) flagged" in resp.verdict


def test_text_narratives_and_asione_metadata_use_same_truthful_verdict():
    """
    Verifies that build_scientific_response and build_observation_response output
    the exact same auditor verdict and status in both the text narrative and the card metadata.
    """
    from agents.fetch_agent import build_scientific_response, build_observation_response
    scenario = get_wgs_case_study_scenario()

    # Case 1: When auditor daemon is offline -> AUDIT_UNAVAILABLE in both text and metadata
    text_offline, card_offline = build_scientific_response("CS-CAT-001", scenario, "Which mechanism?")
    aud_offline_meta = card_offline["auditor_agent"]
    assert aud_offline_meta["status"] == "AUDIT_UNAVAILABLE"
    assert "[AUDIT_UNAVAILABLE]" in text_offline
    assert aud_offline_meta["verdict"] in text_offline

    # Case 2: Observation update offline -> AUDIT_UNAVAILABLE in both text and metadata
    inv = ScientificInvestigationOrchestrator.start_investigation(
        InvestigationInput(question="Test question", case_study_id="CS-CAT-001")
    )
    from agents.fetch_agent import save_investigation_state
    save_investigation_state(inv, session_id="test-session-sync")
    obs_text, obs_card = build_observation_response(
        experiment_id="EXP-WGS-02",
        outcome="Initial_CO2_Mainly_Lattice_16O",
        session_id="test-session-sync",
    )
    obs_aud_meta = obs_card["auditor_agent"]
    assert obs_aud_meta["status"] in ("AUDIT_PASSED", "AUDIT_UNAVAILABLE")
    assert f"[{obs_aud_meta['status']}]" in obs_text
    assert obs_aud_meta["verdict"] in obs_text
