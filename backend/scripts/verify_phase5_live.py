"""Live Verification Script for JANUS Phase 5: Independent Fetch.ai Hypothesis Analyst Agent.

Demonstrates:
1. Four distinct Fetch.ai uAgents running concurrently with distinct addresses and protocols:
   - Primary JANUS Coordinator Agent (Port 8008, Address: agent1q0hmkpdw4v...)
   - Independent Auditor Agent (Port 8009, Address: agent1qtce9c74t0f..., Protocol: janus_scientific_audit)
   - Independent Research Agent (Port 8010, Address: agent1q0hhnepntx..., Protocol: janus_scientific_research)
   - Independent Hypothesis Analyst Agent (Port 8011, Address: agent1qfmmvna5f..., Protocol: janus_scientific_hypothesis)
2. Live inter-agent literature retrieval and Crossref validation (Stage 1):
   - Primary Coordinator dispatches typed ScientificResearchRequest to Research Agent over Fetch.ai protocol.
   - Research Agent retrieves empirical claims, validates publication DOIs, and returns ScientificResearchResponse.
3. Live inter-agent hypothesis analysis & evidence linking (Stage 2):
   - Primary Coordinator dispatches retrieved evidence to Hypothesis Analyst Agent over Fetch.ai protocol.
   - Hypothesis Analyst Agent structures competing hypotheses, tags supporting and contradicting evidence IDs,
     discloses epistemic status and uncertainty, and verifies probability simplex normalization (sum P(H_k) == 1.0).
4. Deterministic Bayesian Experimental Design engine execution (Stage 4):
   - Computes Shannon entropy, EIG, feasibility, and composite utility ranking.
5. Independent Auditor verification (Stage 5):
   - Primary Coordinator dispatches ScientificAuditRequest to Auditor Agent over Fetch.ai protocol.
   - Auditor recomputes probability simplices, stochasticity, Shannon entropy bounds, and ranking order.
   - Strictly verifies 14/14 mandatory checks pass (AUDIT_PASSED).
6. Dynamic Bayesian observation conditioning & state continuity:
   - Evaluates observation update (H1 shifts from 50.00% to 89.84%).
   - Preserves state across turns without reinitializing scientific priors.
7. Truthful offline fallback handling:
   - Demonstrates honest ANALYSIS_UNAVAILABLE reporting when daemon is unreachable and fallback is disabled.
"""

import os
import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from uuid import uuid4

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup paths
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from agents.hypothesis_analyst_agent import create_hypothesis_analyst_uagent
from agents.research_agent import create_research_uagent
from agents.auditor_agent import create_auditor_uagent
from agents.tools import HypothesisAnalystTool, ResearchAgentTool, AuditorAgentTool
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import InvestigationInput
from agents.fetch_agent import (
    create_janus_uagent,
    parse_scientific_intent,
    parse_observation_intent,
    parse_status_or_history_intent,
    build_scientific_response,
    build_observation_response,
    build_investigation_status_response,
    save_investigation_state,
    resolve_investigation_id,
    get_or_restore_investigation,
)
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.engine import ScientificEngine
from app.schemas.hypothesis_analyst import HypothesisAnalysisRequest
from app.schemas.research import ScientificResearchRequest
from app.schemas.audit import ScientificAuditRequest


def run_hypothesis_daemon(port: int = 8011):
    """Starts the independent hypothesis analyst uAgent on a dedicated event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    analyst = create_hypothesis_analyst_uagent(
        name="janus_hypothesis_analyst",
        port=port,
        endpoint=[f"http://127.0.0.1:{port}/submit"],
    )
    analyst.run()


def run_research_daemon(port: int = 8010):
    """Starts the independent research uAgent on a dedicated event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    researcher = create_research_uagent(
        name="janus_research_agent",
        port=port,
        endpoint=[f"http://127.0.0.1:{port}/submit"],
    )
    researcher.run()


def run_auditor_daemon(port: int = 8009):
    """Starts the independent auditor uAgent on a dedicated event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    auditor = create_auditor_uagent(
        name="janus_auditor_agent",
        port=port,
        endpoint=[f"http://127.0.0.1:{port}/submit"],
    )
    auditor.run()


def main():
    print("=" * 80)
    print(" JANUS Phase 5: Live Four-Agent Multi-Agent Verification Demonstration")
    print("=" * 80)

    auditor_port = 8009
    research_port = 8010
    hypothesis_port = 8011
    auditor_endpoint = f"http://127.0.0.1:{auditor_port}/submit"
    research_endpoint = f"http://127.0.0.1:{research_port}/submit"
    hypothesis_endpoint = f"http://127.0.0.1:{hypothesis_port}/submit"

    # 1. Start Hypothesis Analyst Agent Daemon
    print(f"\n[1/8] Starting Independent Hypothesis Analyst uAgent Daemon on Port {hypothesis_port}...")
    t_hyp = threading.Thread(target=run_hypothesis_daemon, args=(hypothesis_port,), daemon=True)
    t_hyp.start()

    # 2. Start Research Agent Daemon
    print(f"[2/8] Starting Independent Research uAgent Daemon on Port {research_port}...")
    t_research = threading.Thread(target=run_research_daemon, args=(research_port,), daemon=True)
    t_research.start()

    # 3. Start Auditor Agent Daemon
    print(f"[3/8] Starting Independent Auditor uAgent Daemon on Port {auditor_port}...")
    t_audit = threading.Thread(target=run_auditor_daemon, args=(auditor_port,), daemon=True)
    t_audit.start()

    time.sleep(2.5)  # Allow sockets to bind

    # 4. Instantiate Primary Coordinator
    print("\n[4/8] Initializing Primary JANUS Coordinator Agent (Port 8008)...")
    coordinator = create_janus_uagent()
    print(f"  Primary Coordinator Name:    {coordinator.name}")
    print(f"  Primary Coordinator Address: {coordinator.address}")

    # Set endpoints in environment for tool dispatch
    os.environ["JANUS_HYPOTHESIS_ANALYST_ADDRESS"] = "agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d"
    os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = hypothesis_endpoint
    os.environ["JANUS_RESEARCH_AGENT_ADDRESS"] = "agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py"
    os.environ["JANUS_RESEARCH_AGENT_ENDPOINT"] = research_endpoint
    os.environ["JANUS_AUDITOR_ADDRESS"] = "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
    os.environ["JANUS_AUDITOR_ENDPOINT"] = auditor_endpoint

    print("\n  Multi-Agent Network Topology:")
    print(f"  - Primary Coordinator:   {coordinator.address} (Port 8008)")
    print(f"  - Independent Auditor:   {os.environ['JANUS_AUDITOR_ADDRESS']} (Port 8009, janus_scientific_audit)")
    print(f"  - Independent Research:  {os.environ['JANUS_RESEARCH_AGENT_ADDRESS']} (Port 8010, janus_scientific_research)")
    print(f"  - Hypothesis Analyst:    {os.environ['JANUS_HYPOTHESIS_ANALYST_ADDRESS']} (Port 8011, janus_scientific_hypothesis)")

    # 5. Direct Hypothesis Analyst uAgent Protocol Query
    print("\n[5/8] Dispatching Direct Inter-Agent Message to Hypothesis Analyst uAgent over Native Protocol...")
    sample_evidence = [
        {
            "id": "CLM-WGS-001",
            "statement": "At 200°C on Pt/CeO2, the rate of 12C-formate exchange during SSITKA is 0.14 of overall turnover.",
            "supports_hypotheses": ["H1", "H3"],
            "refutes_hypotheses": ["H2"],
            "confidence": 0.95,
        },
        {
            "id": "CLM-WGS-002",
            "statement": "Transient C16O pulsing over H218O-treated Pt/CeO2 yields 88% C16O2, proving direct lattice oxygen transfer.",
            "supports_hypotheses": ["H1"],
            "refutes_hypotheses": ["H2", "H3"],
            "confidence": 0.92,
        },
        {
            "id": "CLM-WGS-006",
            "statement": "DFT calculations show carboxyl (*COOH) decomposition barrier (0.58 eV) is significantly lower than formate decomposition (>1.4 eV).",
            "supports_hypotheses": ["H3"],
            "refutes_hypotheses": ["H2"],
            "confidence": 0.85,
        },
    ]

    direct_resp, direct_rec, pipeline_hyps = HypothesisAnalystTool.execute_hypothesis_analysis(
        research_question="Which reaction mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        investigation_id="INV-LIVE-PHASE5-DIRECT",
        case_study_id="CS-CAT-001",
        retrieved_evidence=sample_evidence,
        allow_local_fallback=False,
    )

    print(f"  Status:               {direct_resp.status}")
    print(f"  Responding Agent:     {direct_resp.agent_address}")
    print(f"  Simplex Sum:          {direct_resp.simplex_sum:.6f} (Valid: {direct_resp.is_simplex_valid})")
    print(f"  Hypotheses Evaluated: {len(direct_resp.hypotheses)}")
    for h in direct_resp.hypotheses:
        print(f"    - {h.id} ({h.name}, Prior={h.prior:.2f}): Status [{h.epistemic_status}]")
        print(f"      Supporting Evidence:   {h.supporting_evidence_ids or 'None'}")
        print(f"      Contradicting Evidence: {h.contradicting_evidence_ids or 'None'}")
        print(f"      Uncertainty Note:      {h.uncertainty_explanation[:80]}...")
    print(f"  Unresolved Questions: {len(direct_resp.unresolved_questions)}")

    assert direct_resp.status == "ANALYSIS_COMPLETED"
    assert direct_resp.is_simplex_valid is True
    assert direct_rec.status == "SUCCESS"
    h2 = next(h for h in direct_resp.hypotheses if h.id == "H2")
    assert h2.epistemic_status == "STRONGLY_CONTRADICTED"
    assert "CLM-WGS-001" in h2.contradicting_evidence_ids

    # 6. Full End-to-End Multi-Agent Scientific Investigation
    print("\n[6/8] Executing Full End-to-End Scientific Investigation with All 4 Agents...")
    inv_input = InvestigationInput(
        question="Which reaction mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inv_input)

    # Check Research Agent tool execution
    res_exec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_research_uagent"), None)
    assert res_exec is not None
    print(f"  Stage 1 (Research Agent):           [{res_exec.status}] Ingested {len(report.retrieved_evidence)} evidence claims")

    # Check Hypothesis Analyst tool execution
    hyp_exec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_hypothesis_analyst_uagent"), None)
    assert hyp_exec is not None
    print(f"  Stage 2 (Hypothesis Analyst Agent): [{hyp_exec.status}] Formulated {len(report.hypotheses)} competing hypotheses")

    # Check BED Ranking tool execution
    rank_exec = next((t for t in report.tool_executions if t.tool_name == "janus_information_theoretic_ranking"), None)
    assert rank_exec is not None
    top_exp = report.analysis_result.ranked_experiments[0]
    print(f"  Stage 4 (Bayesian BED Engine):      Top Recommendation: {top_exp.experiment_name} ({top_exp.experiment_id}) | EIG={top_exp.expected_information_gain:.4f} b")

    # Check Auditor Agent tool execution
    audit_exec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_auditor_uagent"), None)
    assert audit_exec is not None
    audit_out = audit_exec.output_data
    audit_status = audit_out.get("status")
    passed_chk = audit_out.get("passed_checks_count")
    total_chk = audit_out.get("total_checks_count")
    print(f"  Stage 5 (Independent Auditor Agent): [{audit_status}] Verified {passed_chk}/{total_chk} mandatory checks")
    assert audit_status == "AUDIT_PASSED"
    assert passed_chk == 14 and total_chk == 14

    # 7. Bayesian Observation Conditioning & State Continuity
    print("\n[7/8] Testing Dynamic Bayesian Observation Conditioning & State Continuity...")
    session_id = f"test-sess-{uuid4().hex[:8]}"
    sender_addr = "agent1quser_test_researcher_address"
    save_investigation_state(report, session_id=session_id, sender=sender_addr)

    obs_query = "observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O"
    obs_tuple = parse_observation_intent(obs_query)
    assert obs_tuple is not None
    obs_exp_id, obs_outcome = obs_tuple
    assert obs_exp_id == "EXP-WGS-02"

    obs_resp_text, obs_meta = build_observation_response(
        experiment_id=obs_exp_id,
        outcome=obs_outcome,
        session_id=session_id,
        sender=sender_addr,
    )
    print("  Observation successfully processed via Bayesian updating!")
    posteriors = obs_meta.get("posteriors", {})
    post_H1 = posteriors.get("H1", 0.0)
    post_H2 = posteriors.get("H2", 0.0)
    post_H3 = posteriors.get("H3", 0.0)
    print(f"  Updated Posteriors: H1 (Redox) = {post_H1*100:.2f}%, H2 (Formate) = {post_H2*100:.2f}%, H3 (Carboxyl) = {post_H3*100:.2f}%")
    assert post_H1 > 0.85, "H1 posterior must surge after observing EXP-WGS-02 lattice oxygen signal"

    # Status query test
    status_query = "status"
    assert parse_status_or_history_intent(status_query) is True
    active_inv_id = resolve_investigation_id(status_query, session_id=session_id, sender=sender_addr)
    active_report = get_or_restore_investigation(active_inv_id)
    assert active_report is not None
    status_text, status_meta = build_investigation_status_response(active_report, status_query)
    status_posteriors = status_meta.get("posteriors", {})
    assert status_posteriors.get("H1", 0.0) > 0.85
    print("  State continuity verified: Status query returned updated posterior distribution without reinitialization.")

    # 8. Truthful Offline Fallback Handling
    print("\n[8/8] Testing Truthful Offline Fallback Handling for Hypothesis Analyst...")
    os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = "http://127.0.0.1:59998/submit"
    os.environ["JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS"] = "1.0"
    try:
        off_resp, off_rec, off_hyps = HypothesisAnalystTool.execute_hypothesis_analysis(
            research_question="What is the mechanism?",
            investigation_id="INV-OFFLINE-VERIF",
            case_study_id="CS-CAT-001",
            timeout=1.0,
            allow_local_fallback=False,
        )
        assert off_resp.status == "ANALYSIS_UNAVAILABLE"
        assert off_rec.status == "WARNING"
        print(f"  Offline status reported honestly: [{off_resp.status}]")
        print("  Zero hallucinations: System correctly reported daemon unavailability without fabricating a passing result.")
    finally:
        os.environ["JANUS_HYPOTHESIS_ANALYST_ENDPOINT"] = hypothesis_endpoint
        os.environ.pop("JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS", None)

    print("\n" + "=" * 80)
    print(" ALL 8 PHASE 5 LIVE VERIFICATION CHECKS PASSED WITH 100% INTEGRITY")
    print("=" * 80)


if __name__ == "__main__":
    main()
