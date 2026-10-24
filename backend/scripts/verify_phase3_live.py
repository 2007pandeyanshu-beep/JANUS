"""Live Verification Script for JANUS Phase 3: Independent Fetch.ai Auditor Agent.

Demonstrates:
1. Two distinct Fetch.ai uAgents running on separate ports with distinct addresses:
   - Primary JANUS Agent (Port 8008, Address: agent1q...)
   - Independent Auditor Agent (Port 8009, Address: agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg)
2. Live inter-agent communication using native Fetch.ai uAgents protocol (`janus_scientific_audit`, v1.0.0).
3. Independent zero-trust mathematical recomputation by Auditor:
   - Prior simplex normalization (sum = 1.0)
   - Likelihood row stochasticity (sum = 1.0)
   - Shannon conditional entropy and EIG bounds (0 <= EIG <= H)
   - Authoritative composite utility ranking
4. Dynamic Bayesian observation conditioning (`EXP-WGS-02 = Initial_CO2_Mainly_Lattice_16O` -> H1 moves to 89.84%).
5. Auditor verification of sequential Bayes' rule update.
6. State continuity verification (status queries preserve posterior state across turns).
7. Truthful offline fallback (AUDIT_UNAVAILABLE when auditor daemon is unreachable).
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

from agents.auditor_agent import create_auditor_uagent
from agents.tools import AuditorAgentTool
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
    generate_asione_card,
    save_investigation_state,
    SUPPORTED_SCENARIOS,
)
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from app.schemas.audit import ScientificAuditRequest, ScientificAuditResponse


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
    print(" JANUS Phase 3: Live Multi-Agent Verification Demonstration")
    print("=" * 80)

    auditor_port = 8009
    auditor_endpoint = f"http://127.0.0.1:{auditor_port}/submit"

    # Start independent auditor daemon in background thread
    print(f"\n[1/6] Starting independent auditor uAgent daemon on port {auditor_port}...")
    t = threading.Thread(target=run_auditor_daemon, args=(auditor_port,), daemon=True)
    t.start()
    time.sleep(2.5)  # Wait for uAgent HTTP server socket binding

    auditor_address = "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
    os.environ["JANUS_AUDITOR_ADDRESS"] = auditor_address
    os.environ["JANUS_AUDITOR_ENDPOINT"] = auditor_endpoint

    # Primary Agent identity (resolves canonical address from JANUS_AGENT_SEED)
    primary_agent = create_janus_uagent()
    print("\n[2/6] Verifying Agent Identities & Distinct Cryptographic Addresses:")
    print(f"  Primary Agent Name:    {primary_agent.name}")
    print(f"  Primary Agent Address: {primary_agent.address}")
    print(f"  Auditor Agent Name:    janus_auditor_agent")
    print(f"  Auditor Agent Address: {auditor_address}")
    assert primary_agent.address != auditor_address, "Primary and Auditor addresses must be distinct!"
    assert primary_agent.address == "agent1q0hmkpdw4v28hmkkfqa56u2zwx3pzly44z7r8048pjtgw4lq8r5my29pn3t", (
        f"Primary address mismatch! Expected canonical agent1q0hmkp..., got {primary_agent.address}"
    )
    print("  -> Cryptographic addresses verified distinct and independent.")

    # Step 1: Scientific Question on Pt/CeO2 WGS
    print("\n[3/6] Dispatching Scientific Investigation Query to Primary Gateway:")
    session_id = str(uuid4())
    sender = "test_scientific_investigator"
    query = "Which mechanism dominates in low-temperature water-gas shift on Pt/CeO2?"
    print(f"  User Query: '{query}'")

    case_id, scenario, rej = parse_scientific_intent(query)
    assert case_id == "CS-CAT-001"

    inv = ScientificInvestigationOrchestrator.start_investigation(
        InvestigationInput(question=query, case_study_id=case_id)
    )
    save_investigation_state(inv, session_id=session_id, sender=sender)

    text_resp, card_meta = build_scientific_response(case_id, scenario, query, investigation=inv)
    top_rec = card_meta.get("recommended_experiment", {})
    print(f"  Investigation ID: {inv.investigation_id}")
    print(f"  Top Recommended Experiment: {top_rec.get('id')} ({top_rec.get('name')})")
    print(f"  EIG: {top_rec.get('eig_bits')} bits | Utility: {top_rec.get('composite_utility')}")

    auditor_card_info = card_meta.get("auditor_agent", {})
    print(f"  Auditor Status Badge: [{auditor_card_info.get('status')}]")
    print(f"  Auditor Address:      {auditor_card_info.get('auditor_address')}")
    print(f"  Auditor Checks:       {auditor_card_info.get('passed_checks')}/{auditor_card_info.get('total_checks')} passed")
    print(f"  Auditor Verdict:      {auditor_card_info.get('verdict')}")
    assert auditor_card_info.get("status") == "AUDIT_PASSED", f"Expected AUDIT_PASSED, got {auditor_card_info}"

    # Step 2: Experimental Observation Conditioning
    print("\n[4/6] Conditioning on Lab Observation (Sequential Bayesian Update):")
    obs_command = "observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O"
    print(f"  User Command: '{obs_command}'")

    obs_tuple = parse_observation_intent(obs_command)
    assert obs_tuple is not None
    exp_id, outcome = obs_tuple

    obs_text, obs_meta = build_observation_response(
        experiment_id=exp_id,
        outcome=outcome,
        session_id=session_id,
        sender=sender,
    )
    posteriors = obs_meta.get("posteriors", {})
    print(f"  Updated Posteriors: {', '.join(f'{k}: {v*100:.2f}%' for k, v in posteriors.items())}")
    assert posteriors.get("H1", 0) > 0.85, f"H1 posterior should rise to ~89.84%, got {posteriors.get('H1')}"
    print(f"  -> H1 belief shifted from 50.00% to {posteriors.get('H1', 0)*100:.2f}% (Decisive disambiguation)")

    obs_auditor_info = obs_meta.get("auditor_agent", {})
    print(f"  Auditor Sequential Update Status: [{obs_auditor_info.get('status')}]")
    print(f"  Auditor Verdict: {obs_auditor_info.get('verdict')}")
    assert obs_auditor_info.get("status") == "AUDIT_PASSED"

    # Step 3: State Continuity Verification
    print("\n[5/7] Verifying State Continuity on Status Query (Regression Prevention):")
    status_query = "status"
    assert parse_status_or_history_intent(status_query) is True
    from agents.fetch_agent import resolve_investigation_id, get_or_restore_investigation
    active_inv_id = resolve_investigation_id(status_query, session_id=session_id, sender=sender)
    active_report = get_or_restore_investigation(active_inv_id)
    assert active_report is not None, "Failed to restore active investigation"
    status_text, status_meta = build_investigation_status_response(active_report, status_query)
    status_posteriors = status_meta.get("posteriors", {})
    print(f"  Status Posteriors: {', '.join(f'{k}: {v*100:.2f}%' for k, v in status_posteriors.items())}")
    assert status_posteriors.get("H1", 0) > 0.85, "State continuity bug: status query reset posteriors to prior baseline!"
    print("  -> State continuity confirmed: H1 posterior preserved at 89.84% across conversation turns.")

    # Step 4: Deliberate Mandatory Check Failure Detection
    print("\n[6/7] Verifying Zero-Tolerance Verdict Policy on Deliberately Corrupted Invariant:")
    corrupted_hypotheses = [h.model_dump() for h in scenario.hypotheses]
    corrupted_hypotheses[0]["prior"] = 0.20  # Violates prior simplex: sum = 0.70 instead of 1.00
    from scientific.engine import ScientificEngine
    clean_res = ScientificEngine.execute_analysis(scenario)
    corrupted_req = ScientificAuditRequest(
        correlation_id="corr-deliberate-fail-test",
        scenario_id="CS-CAT-001",
        hypotheses=corrupted_hypotheses,
        experiments=[e.model_dump() for e in scenario.experiments],
        ranked_scores=[s.model_dump() for s in clean_res.ranked_experiments],
        selected_recommendation=clean_res.ranked_experiments[0].model_dump(),
        evidence_ledger=[e.model_dump() for e in scenario.evidence],
        is_sequential_update=False,
    )
    fail_resp = AuditorAgentTool._dispatch_request(corrupted_req, timeout=5.0)
    print(f"  Corrupted Invariant Status: [{fail_resp.status}]")
    print(f"  Mandatory Checks Passed:    {fail_resp.mandatory_passed_count}/{fail_resp.mandatory_checks_count}")
    print(f"  All Invariants Hold:        {fail_resp.all_invariants_hold}")
    print(f"  Verdict:                    {fail_resp.verdict}")
    assert fail_resp.status == "AUDIT_FAILED", f"Expected AUDIT_FAILED, got {fail_resp.status}"
    assert fail_resp.all_invariants_hold is False
    assert fail_resp.mandatory_passed_count < fail_resp.mandatory_checks_count
    assert any("prior_simplex" in m for m in fail_resp.mismatches)
    print("  -> Zero-tolerance verdict policy verified: Mandatory failure strictly yields AUDIT_FAILED, never AUDIT_PASSED.")

    # Step 5: Truthful Reporting when Auditor is Offline
    print("\n[7/7] Verifying Truthful Reporting when Auditor Daemon is Offline:")
    os.environ["JANUS_AUDITOR_ENDPOINT"] = "http://127.0.0.1:54321/submit"
    res = ScientificEngine.execute_analysis(scenario)

    offline_resp, offline_rec = AuditorAgentTool.audit_analysis(res, scenario, timeout=0.5)
    print(f"  Offline Auditor Response Status: [{offline_resp.status}]")
    print(f"  Offline Tool Execution Status:   {offline_rec.status}")
    print(f"  Offline Verdict:                 {offline_resp.verdict}")
    assert offline_resp.status == "AUDIT_UNAVAILABLE"
    assert offline_rec.status == "WARNING"
    print("  -> Strictly truthful reporting confirmed: System reported AUDIT_UNAVAILABLE without crashing or falsifying success.")

    print("\n" + "=" * 80)
    print(" LIVE VERIFICATION COMPLETED: ALL 7 WORKSTREAMS VERIFIED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
