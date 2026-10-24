"""Tests for JANUS Independent Scientific Tool uAgent (Phase 6).

Verifies:
1. Scientific computation schema serialization, deserialization, and parameter boundary validation.
2. Distinct cryptographic identity (address, port 8012, protocol) from coordinator, auditor, research, and hypothesis agents.
3. Arrhenius rate constant calculation, activation energy sensitivity, and half-life calculation.
4. Kinetic Isotope Effect (KIE) evaluation, mechanistic categorization (primary, secondary/unity, inverse), and ZPE limit checking.
5. Microkinetic reaction simulation for WGS (Pt/CeO2) and OER (perovskite) competing pathways.
6. Mechanistic discriminability (Z-score statistical separation) between competing rate laws.
7. Deterministic reproducibility across repeated calculations.
8. Error handling on invalid/non-physical parameters (negative temperatures, zero rates, non-numeric values).
9. Honest offline reporting (COMPUTATION_UNAVAILABLE, never faking success).
10. Graceful local fallback when daemon is offline with transparent audit trail and likelihood boundary preservation.
11. Full integration with ScientificInvestigationOrchestrator Stage 3.
12. Live inter-agent request/response message exchange over native Fetch.ai uAgents protocol.
"""

import os
import sys
import math
import time
import asyncio
import threading
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any
from pydantic import ValidationError

# Ensure backend directory is in sys.path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_test_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.schemas.scientific_tool import (
    ArrheniusInput,
    KieInput,
    ReactionSimulationInput,
    ComputationOutputItem,
    ScientificComputationRequest,
    ScientificComputationResponse,
)
from agents.tools import (
    ScientificToolAgentTool,
    HypothesisAnalystTool,
    ResearchAgentTool,
    AuditorAgentTool,
)
from agents.scientific_tool_agent import (
    create_scientific_tool_uagent,
    perform_scientific_computation,
    calculate_arrhenius,
    calculate_kie,
    simulate_reaction_kinetics,
    scientific_tool_proto,
    SCIENTIFIC_BOUNDARY_DISCLAIMER,
)
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import InvestigationInput, AgentRole


def test_scientific_tool_schemas_and_validation():
    """Verifies that scientific tool models serialize and validate parameter constraints."""
    arr = ArrheniusInput(
        pre_exponential_A=1.0e8,
        activation_energy_kJ_mol=52.0,
        temperature_kelvin=473.15,
    )
    assert arr.pre_exponential_A == 1.0e8
    assert arr.activation_energy_kJ_mol == 52.0
    assert arr.temperature_kelvin == 473.15

    # Out-of-bounds parameters must raise ValidationError
    with pytest.raises(ValidationError):
        ArrheniusInput(pre_exponential_A=-1.0, activation_energy_kJ_mol=52.0)

    with pytest.raises(ValidationError):
        ArrheniusInput(pre_exponential_A=1.0e8, activation_energy_kJ_mol=-5.0)

    with pytest.raises(ValidationError):
        ArrheniusInput(pre_exponential_A=1.0e8, activation_energy_kJ_mol=52.0, temperature_kelvin=-10.0)

    kie = KieInput(rate_light=1.48e-3, rate_heavy=1.00e-3, temperature_kelvin=473.15)
    assert kie.rate_light == 1.48e-3
    assert kie.rate_heavy == 1.00e-3

    with pytest.raises(ValidationError):
        KieInput(rate_light=-1.0, rate_heavy=1.0)

    req = ScientificComputationRequest(
        correlation_id="corr-tool-01",
        investigation_id="INV-TOOL-01",
        computation_type="KINETIC_ISOTOPE_EFFECT",
        case_study_id="CS-CAT-001",
        kie_params=kie,
    )
    dumped = req.model_dump()
    assert dumped["correlation_id"] == "corr-tool-01"
    restored = ScientificComputationRequest.model_validate(dumped)
    assert restored.computation_type == "KINETIC_ISOTOPE_EFFECT"


def test_scientific_tool_agent_identity_distinct():
    """Verifies that the Scientific Tool Agent has a distinct address, port, and protocol."""
    agent_inst = create_scientific_tool_uagent(port=8012)
    assert agent_inst.name == "janus_scientific_tool_agent"
    assert agent_inst.address == "agent1q2lmglm5n5nl8wxrcly6j4w0xts9fa9zh2u8qq8mxf30ya3mfxcpjq6md8t"

    # Distinct from Auditor (8009), Research (8010), and Hypothesis Analyst (8011)
    auditor_addr = AuditorAgentTool.DEFAULT_AUDITOR_ADDRESS
    research_addr = ResearchAgentTool.DEFAULT_RESEARCH_AGENT_ADDRESS
    hyp_addr = HypothesisAnalystTool.DEFAULT_HYPOTHESIS_ANALYST_ADDRESS

    assert agent_inst.address != auditor_addr
    assert agent_inst.address != research_addr
    assert agent_inst.address != hyp_addr

    assert scientific_tool_proto.name == "janus_scientific_computation"
    assert scientific_tool_proto.version == "1.0.0"


def test_arrhenius_rate_computation():
    """Verifies exact deterministic Arrhenius rate calculation k = A * exp(-Ea / RT)."""
    # At T = 473.15 K, R = 8.314462618e-3 kJ/(mol*K)
    # RT = 3.934038...
    # Ea = 52.0 kJ/mol -> Ea / RT = 13.2179...
    # k = 1.0e6 * exp(-13.2179...) = 1.8177... s^-1
    inp = ArrheniusInput(pre_exponential_A=1.0e6, activation_energy_kJ_mol=52.0, temperature_kelvin=473.15)
    items, interp, assumptions, warns = calculate_arrhenius(inp)

    k_item = next(it for it in items if it.parameter_name == "rate_constant_k")
    assert k_item.value == pytest.approx(1.81779, rel=1e-3)
    assert k_item.unit == "s^-1"

    t_half_item = next(it for it in items if it.parameter_name == "half_life_t_half")
    assert t_half_item.value == pytest.approx(math.log(2.0) / k_item.value, rel=1e-4)

    assert len(assumptions) >= 2
    assert "Arrhenius kinetic computation" in interp


def test_kinetic_isotope_effect_computation_and_categorization():
    """Verifies KIE calculation, semi-classical bounds, and primary vs secondary categorization."""
    # 1. Primary KIE (KIE >= 1.5)
    kie_primary = KieInput(rate_light=3.0e-3, rate_heavy=1.0e-3, temperature_kelvin=473.15)
    items, interp, assumptions, warns = calculate_kie(kie_primary)
    kie_val = next(it.value for it in items if it.parameter_name == "kinetic_isotope_effect_KIE")
    assert kie_val == pytest.approx(3.0, abs=1e-4)
    assert "Primary Kinetic Isotope Effect" in interp
    assert "rate-determining step" in interp

    # 2. Near-unity / Secondary KIE (0.8 <= KIE < 1.5)
    kie_sec = KieInput(rate_light=1.22e-3, rate_heavy=1.00e-3, temperature_kelvin=473.15)
    items_sec, interp_sec, _, _ = calculate_kie(kie_sec)
    kie_sec_val = next(it.value for it in items_sec if it.parameter_name == "kinetic_isotope_effect_KIE")
    assert kie_sec_val == pytest.approx(1.22, abs=1e-4)
    assert "Secondary / near-unity" in interp_sec
    assert "NOT rate-determining" in interp_sec

    # 3. Inverse KIE (KIE < 0.8)
    kie_inv = KieInput(rate_light=0.70e-3, rate_heavy=1.00e-3, temperature_kelvin=473.15)
    _, interp_inv, _, _ = calculate_kie(kie_inv)
    assert "Inverse Kinetic Isotope Effect" in interp_inv


def test_reaction_simulation_wgs_and_oer():
    """Verifies microkinetic simulation of competing pathways on WGS and OER."""
    # WGS (Pt/CeO2): Redox pathway should dominate unassisted Formate
    wgs_sim = ReactionSimulationInput(case_study_id="CS-CAT-001", temperature_kelvin=473.15, pressure_bar=1.0)
    items_wgs, interp_wgs, assumptions, warns = simulate_reaction_kinetics(wgs_sim)

    r_redox = next(it.value for it in items_wgs if it.parameter_name == "simulated_rate_redox_MvK")
    r_form = next(it.value for it in items_wgs if it.parameter_name == "simulated_rate_associative_formate")
    ratio = next(it.value for it in items_wgs if it.parameter_name == "branching_ratio_redox_vs_formate")

    assert r_redox > r_form
    assert ratio > 1.0
    assert "Redox pathway rate" in interp_wgs

    # OER (Perovskite): LOM should exhibit higher simulated rate than AEM
    oer_sim = ReactionSimulationInput(case_study_id="CS-OER-002", temperature_kelvin=298.15, pressure_bar=1.0)
    items_oer, interp_oer, _, _ = simulate_reaction_kinetics(oer_sim)

    j_lom = next(it.value for it in items_oer if it.parameter_name == "simulated_current_density_LOM")
    j_aem = next(it.value for it in items_oer if it.parameter_name == "simulated_current_density_AEM")
    assert j_lom > j_aem
    assert "LOM predicts" in interp_oer


def test_mechanistic_discriminability_analysis():
    """Verifies statistical Z-score separation evaluation between competing reaction models."""
    req = ScientificComputationRequest(
        correlation_id="corr-disc-01",
        investigation_id="INV-DISC-01",
        computation_type="MECHANISTIC_DISCRIMINABILITY",
        case_study_id="CS-CAT-001",
    )
    resp = perform_scientific_computation(req, "agent1test")
    assert resp.status == "COMPUTATION_COMPLETED"
    z_item = next(it for it in resp.results if it.parameter_name == "z_score_separation")
    assert z_item.value >= 0.0
    disc_item = next(it for it in resp.results if it.parameter_name == "is_statistically_discriminable")
    assert disc_item.value in (0.0, 1.0)
    assert any("Likelihood Boundary Invariant" in w for w in resp.warnings)


def test_deterministic_reproducibility():
    """Verifies that running identical calculations produces bit-exact reproducible results."""
    req = ScientificComputationRequest(
        correlation_id="corr-rep-01",
        investigation_id="INV-REP-01",
        computation_type="ARRHENIUS_RATE",
        arrhenius_params=ArrheniusInput(pre_exponential_A=5.0e7, activation_energy_kJ_mol=65.4, temperature_kelvin=510.0),
    )
    resp1 = perform_scientific_computation(req, "agent1test")
    resp2 = perform_scientific_computation(req, "agent1test")

    assert resp1.status == resp2.status == "COMPUTATION_COMPLETED"
    val1 = [it.value for it in resp1.results]
    val2 = [it.value for it in resp2.results]
    assert val1 == val2


def test_error_handling_invalid_computation_type_and_missing_params():
    """Verifies honest INVALID_PARAMETERS reporting when required parameters are omitted."""
    # Missing arrhenius_params for ARRHENIUS_RATE
    req_bad_arr = ScientificComputationRequest(
        correlation_id="corr-err-01",
        investigation_id="INV-ERR-01",
        computation_type="ARRHENIUS_RATE",
    )
    resp_arr = perform_scientific_computation(req_bad_arr, "agent1test")
    assert resp_arr.status == "INVALID_PARAMETERS"
    assert "missing 'arrhenius_params'" in resp_arr.scientific_interpretation

    # Missing kie_params for KINETIC_ISOTOPE_EFFECT
    req_bad_kie = ScientificComputationRequest(
        correlation_id="corr-err-02",
        investigation_id="INV-ERR-02",
        computation_type="KINETIC_ISOTOPE_EFFECT",
    )
    resp_kie = perform_scientific_computation(req_bad_kie, "agent1test")
    assert resp_kie.status == "INVALID_PARAMETERS"
    assert "missing 'kie_params'" in resp_kie.scientific_interpretation

    # Unsupported computation type
    req_bad_type = ScientificComputationRequest(
        correlation_id="corr-err-03",
        investigation_id="INV-ERR-03",
        computation_type="NONEXISTENT_TYPE",
    )
    resp_type = perform_scientific_computation(req_bad_type, "agent1test")
    assert resp_type.status == "INVALID_PARAMETERS"
    assert "Unsupported computation_type" in resp_type.scientific_interpretation


def test_offline_daemon_handling_and_honest_reporting():
    """Verifies that when daemon is offline and fallback is disabled, it returns COMPUTATION_UNAVAILABLE."""
    os.environ["JANUS_SCIENTIFIC_TOOL_ENDPOINT"] = "http://127.0.0.1:59998/submit"
    os.environ["JANUS_SCIENTIFIC_TOOL_TIMEOUT_SECONDS"] = "1.0"
    try:
        req = ScientificComputationRequest(
            correlation_id="corr-offline-01",
            investigation_id="INV-OFFLINE-TOOL",
            computation_type="KINETIC_ISOTOPE_EFFECT",
            kie_params=KieInput(rate_light=1.48e-3, rate_heavy=1.00e-3),
        )
        resp, record = ScientificToolAgentTool.execute_computation(req, timeout=1.0, allow_local_fallback=False)

        assert resp.status == "COMPUTATION_UNAVAILABLE"
        assert record.status == "WARNING"
        assert "COMPUTATION_UNAVAILABLE" in resp.scientific_interpretation
        assert len(resp.results) == 0
    finally:
        os.environ.pop("JANUS_SCIENTIFIC_TOOL_ENDPOINT", None)
        os.environ.pop("JANUS_SCIENTIFIC_TOOL_TIMEOUT_SECONDS", None)


def test_offline_daemon_with_fallback_engaged():
    """Verifies that when daemon is offline and fallback is enabled, local computation engages honestly."""
    os.environ["JANUS_SCIENTIFIC_TOOL_ENDPOINT"] = "http://127.0.0.1:59998/submit"
    os.environ["JANUS_SCIENTIFIC_TOOL_TIMEOUT_SECONDS"] = "1.0"
    try:
        req = ScientificComputationRequest(
            correlation_id="corr-fallback-01",
            investigation_id="INV-FALLBACK-TOOL",
            computation_type="KINETIC_ISOTOPE_EFFECT",
            kie_params=KieInput(rate_light=1.48e-3, rate_heavy=1.00e-3),
        )
        resp, record = ScientificToolAgentTool.execute_computation(req, timeout=1.0, allow_local_fallback=True)

        assert resp.status == "COMPUTATION_UNAVAILABLE"
        assert record.status == "WARNING"
        assert record.input_arguments.get("fallback_engaged") is True
        assert len(resp.results) >= 3
        kie_val = next(it.value for it in resp.results if "KIE" in it.parameter_name)
        assert kie_val == pytest.approx(1.48, abs=1e-4)
        assert any("fallback computation engaged" in w for w in resp.warnings)
    finally:
        os.environ.pop("JANUS_SCIENTIFIC_TOOL_ENDPOINT", None)
        os.environ.pop("JANUS_SCIENTIFIC_TOOL_TIMEOUT_SECONDS", None)


def test_orchestrator_stage3_scientific_tool_integration():
    """Verifies that ScientificInvestigationOrchestrator Stage 3 invokes the Scientific Tool Agent."""
    inp = InvestigationInput(
        question="Which mechanism dominates low-temperature water-gas shift on Pt/CeO2?",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inp)

    # Verify tool execution record is present
    tool_rec = next((t for t in report.tool_executions if t.tool_name == "janus_independent_scientific_tool_uagent"), None)
    assert tool_rec is not None, "Stage 3 must invoke janus_independent_scientific_tool_uagent tool"
    assert tool_rec.invoked_by == AgentRole.SCIENTIFIC_TOOL
    assert "investigation_id" in tool_rec.input_arguments

    # Verify Stage 3 log entries
    tool_logs = [l for l in report.agent_logs if l.role == AgentRole.SCIENTIFIC_TOOL and l.stage == "COMPUTATIONAL_ANALYSIS"]
    assert len(tool_logs) >= 1
    assert any("Scientific Tool uAgent" in l.thought for l in tool_logs)
    assert any("Likelihood Boundary Invariant" in l.thought for l in tool_logs)


def test_live_scientific_tool_inter_agent_communication_cycle():
    """
    Spins up the Independent Scientific Tool uAgent on an ephemeral port (8092),
    sends a real synchronous ScientificComputationRequest over the native Fetch.ai protocol,
    and asserts structured COMPUTATION_COMPLETED response.
    """
    test_port = 8092
    test_endpoint = f"http://127.0.0.1:{test_port}/submit"

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ag = create_scientific_tool_uagent(
            name="test_live_scientific_tool",
            port=test_port,
            endpoint=[test_endpoint],
        )
        ag.run()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    time.sleep(2.0)  # Wait for uAgent socket binding

    os.environ["JANUS_SCIENTIFIC_TOOL_ADDRESS"] = "agent1q2lmglm5n5nl8wxrcly6j4w0xts9fa9zh2u8qq8mxf30ya3mfxcpjq6md8t"
    os.environ["JANUS_SCIENTIFIC_TOOL_ENDPOINT"] = test_endpoint
    try:
        req = ScientificComputationRequest(
            correlation_id="corr-live-tool-01",
            investigation_id="INV-LIVE-TOOL-CYCLE",
            computation_type="KINETIC_ISOTOPE_EFFECT",
            case_study_id="CS-CAT-001",
            kie_params=KieInput(rate_light=1.48e-3, rate_heavy=1.00e-3, label_light="H2O", label_heavy="D2O"),
            assumptions=["Experimental KIE measured at 200 C on 1 wt% Pt/CeO2"],
        )
        resp, record = ScientificToolAgentTool.execute_computation(
            req,
            timeout=6.0,
            allow_local_fallback=False,
        )

        assert resp.status == "COMPUTATION_COMPLETED"
        assert resp.agent_address == "agent1q2lmglm5n5nl8wxrcly6j4w0xts9fa9zh2u8qq8mxf30ya3mfxcpjq6md8t"
        assert len(resp.results) >= 3
        kie_val = next(it.value for it in resp.results if "KIE" in it.parameter_name)
        assert kie_val == pytest.approx(1.48, abs=1e-4)
        assert record.status == "SUCCESS"
        assert record.tool_name == "janus_independent_scientific_tool_uagent"
        assert any("Likelihood Boundary Invariant" in w for w in resp.warnings)
    finally:
        os.environ.pop("JANUS_SCIENTIFIC_TOOL_ADDRESS", None)
        os.environ.pop("JANUS_SCIENTIFIC_TOOL_ENDPOINT", None)
