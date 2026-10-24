"""Unit and integration test suite for JANUS Coordinator Critic/Review Stage (Phase 8).

Validates:
1. Review schema validation and JSON serialization.
2. Evidence sufficiency and bibliographic provenance evaluation (empty evidence gating).
3. Hypothesis consistency and probability simplex normalization (simplex violation gating).
4. Scientific computation validity and physical boundary checks (Arrhenius T <= 0, negative KIE).
5. Experiment ranking integrity, unquantified assays, and dual-ranking divergence.
6. Independent Auditor integration (AUDIT_FAILED gating, AUDIT_UNAVAILABLE qualification).
7. Three-state Conclusion Gate transitions (SUFFICIENTLY_SUPPORTED, REQUIRES_QUALIFICATION, WITHHOLD_CONCLUSIONS).
8. Coordinator workflow integration and sequential observation update re-auditing.
9. Backward compatibility of legacy `report.critic_review` items (CRT-001 through CRT-006).
"""

import pytest
from app.schemas.review import (
    ReviewStatus,
    ConclusionGateStatus,
    ReviewCategory,
    ReviewFindingItem,
    ScientificReviewRequest,
    ScientificReviewReport,
)
from agents.critic_engine import ScientificCriticEngine
from agents.tools import CriticReviewTool
from agents.orchestrator import ScientificInvestigationOrchestrator
from agents.types import (
    AgentRole,
    CriticSeverity,
    CriticItem,
    InvestigationInput,
    AgentInvestigationReport,
)
from scientific.evidence_ingestion import get_wgs_case_study_scenario


def _build_valid_request(
    auditor_status: str = "AUDIT_PASSED",
    is_math_verified: bool = True,
    case_study_id: str = "CS-CAT-001",
    is_synthetic: bool = False,
) -> ScientificReviewRequest:
    """Helper fixture building a valid, well-formed ScientificReviewRequest."""
    wgs = get_wgs_case_study_scenario()
    return ScientificReviewRequest(
        correlation_id="test-corr-001",
        investigation_id="INV-TEST-001",
        question="Which pathway governs low-temperature WGS on Pt/CeO2?",
        case_study_id=case_study_id,
        is_synthetic=is_synthetic,
        hypotheses=[h.model_dump() for h in wgs.hypotheses],
        candidate_experiments=[e.model_dump() for e in wgs.experiments],
        evidence=[ev.model_dump() for ev in wgs.evidence],
        ranked_experiments=[
            {
                "experiment_id": "EXP-WGS-02",
                "experiment_name": "In-situ SSITKA-DRIFTS C18O -> C16O2",
                "expected_information_gain": 0.8113,
                "composite_utility_score": 0.6875,
                "utility_rank": 1,
                "eig_rank": 1,
                "cost": 1.8,
                "feasibility": 1.0,
                "quantification_status": "QUANTIFIED",
            },
            {
                "experiment_id": "EXP-WGS-01",
                "experiment_name": "In-situ DRIFTS Formate Decomposition Rate",
                "expected_information_gain": 0.6500,
                "composite_utility_score": 0.5652,
                "utility_rank": 2,
                "eig_rank": 2,
                "cost": 1.5,
                "feasibility": 1.0,
                "quantification_status": "QUANTIFIED",
            },
        ],
        tool_executions=[
            {
                "tool_name": "chemical_kinetics_kie",
                "invoked_by": "SCIENTIFIC_TOOL_AGENT",
                "input_arguments": {"k_light": 0.11, "k_heavy": 0.05},
                "output_data": {"kie_value": 2.2, "status": "SUCCESS"},
                "execution_time_ms": 2.5,
                "status": "SUCCESS",
            }
        ],
        independent_verification={
            "is_verified": is_math_verified,
            "passed_checks": 14,
            "total_checks": 14,
            "summary": "All 14 mathematical invariants verified against axioms.",
        },
        auditor_address="agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg",
        auditor_status=auditor_status,
        auditor_verdict=f"Auditor verdict: status={auditor_status}",
        unquantified_experiments=[],
    )


# ======================================================================
# 1. REVIEW SCHEMA VALIDATION AND SERIALIZATION
# ======================================================================

def test_review_schemas_instantiation_and_serialization():
    """Verify that all review Pydantic models instantiate and serialize to/from dict/JSON."""
    finding = ReviewFindingItem(
        finding_id="REV-TST-001",
        category=ReviewCategory.HYPOTHESIS_CONSISTENCY,
        severity="VERIFIED",
        target_agent="HYPOTHESIS_AGENT",
        target_object="Hypothesis Prior Simplex",
        claim="Priors sum to 1.0",
        critique="Strictly normalized",
        evidence_basis="Kolmogorov axioms",
        recommendation="Maintain normalization",
        is_blocking=False,
    )
    assert finding.is_blocking is False

    report = ScientificReviewReport(
        correlation_id="corr-123",
        investigation_id="INV-123",
        status=ReviewStatus.REVIEW_COMPLETED,
        conclusion_gate=ConclusionGateStatus.SUFFICIENTLY_SUPPORTED,
        gate_rationale="All invariants and citations verified.",
        total_findings_count=1,
        blocking_findings_count=0,
        findings=[finding],
        evaluated_dimensions=["Hypothesis Consistency & Simplex Axioms"],
        disclosed_limitations=["None"],
        summary="Review passed cleanly.",
        timestamp="2026-10-24T12:00:00Z",
    )
    dumped = report.model_dump()
    assert dumped["conclusion_gate"] == "SUFFICIENTLY_SUPPORTED"
    assert dumped["total_findings_count"] == 1
    reconstructed = ScientificReviewReport.model_validate(dumped)
    assert reconstructed.conclusion_gate == ConclusionGateStatus.SUFFICIENTLY_SUPPORTED


# ======================================================================
# 2. EVIDENCE SUFFICIENCY & PROVENANCE
# ======================================================================

def test_critic_withholds_conclusions_when_evidence_empty():
    """Verify that zero evidence items triggers a blocking finding and WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request()
    req.evidence = []  # Zero evidence items

    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    assert report.blocking_findings_count >= 1
    ev_finding = next((f for f in report.findings if f.finding_id == "REV-EVD-001"), None)
    assert ev_finding is not None
    assert ev_finding.is_blocking is True
    assert "zero retrieved evidence" in ev_finding.claim


def test_critic_requires_qualification_for_synthetic_benchmarks():
    """Verify that synthetic benchmarks (SYN-001 / is_synthetic=True) require qualification."""
    req = _build_valid_request(is_synthetic=True, case_study_id="SYN-001")
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.REQUIRES_QUALIFICATION
    assert any("Synthetic" in lim for lim in report.disclosed_limitations)
    crt_002 = next((c for c in critic_items if c.id == "CRT-002"), None)
    assert crt_002 is not None
    assert "Synthetic Kinase Fixtures" in crt_002.target_claim_or_object


# ======================================================================
# 3. HYPOTHESIS CONSISTENCY & SIMPLEX NORMALIZATION
# ======================================================================

def test_critic_withholds_conclusions_on_simplex_sum_violation():
    """Verify that unnormalized hypothesis priors trigger a blocking finding and WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request()
    # Violate simplex sum: 0.5 + 0.5 + 0.3 = 1.30
    req.hypotheses = [
        {"id": "H1", "name": "Hypothesis 1", "prior": 0.50},
        {"id": "H2", "name": "Hypothesis 2", "prior": 0.50},
        {"id": "H3", "name": "Hypothesis 3", "prior": 0.30},
    ]
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    assert report.blocking_findings_count >= 1
    hyp_finding = next((f for f in report.findings if f.finding_id == "REV-HYP-002"), None)
    assert hyp_finding is not None
    assert hyp_finding.is_blocking is True
    assert "Probability simplex axiom violated" in hyp_finding.critique

    # Verify legacy CRT-001 is updated with challenge severity
    crt_001 = next(c for c in critic_items if c.id == "CRT-001")
    assert crt_001.severity == CriticSeverity.HIGH_SEVERITY_CHALLENGE
    assert crt_001.is_resolved is False


def test_critic_withholds_conclusions_on_negative_prior():
    """Verify that a negative prior probability triggers WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request()
    req.hypotheses = [
        {"id": "H1", "name": "Hypothesis 1", "prior": 1.20},
        {"id": "H2", "name": "Hypothesis 2", "prior": -0.20},
    ]
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    hyp_finding = next((f for f in report.findings if f.finding_id == "REV-HYP-002"), None)
    assert hyp_finding is not None
    assert hyp_finding.is_blocking is True


def test_critic_withholds_conclusions_on_fewer_than_two_hypotheses():
    """Verify that fewer than 2 hypotheses triggers WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request()
    req.hypotheses = [{"id": "H1", "name": "Single Hypothesis", "prior": 1.0}]

    report, critic_items = ScientificCriticEngine.evaluate(req)
    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    hyp_finding = next((f for f in report.findings if f.finding_id == "REV-HYP-001"), None)
    assert hyp_finding is not None
    assert hyp_finding.is_blocking is True


# ======================================================================
# 4. SCIENTIFIC COMPUTATION VALIDITY & PHYSICAL LIMITS
# ======================================================================

def test_critic_withholds_conclusions_on_invalid_temperature():
    """Verify that absolute temperature T <= 0 K triggers a blocking scientific computation finding."""
    req = _build_valid_request()
    req.tool_executions.append({
        "tool_name": "chemical_kinetics_arrhenius",
        "invoked_by": "SCIENTIFIC_TOOL_AGENT",
        "input_arguments": {"temperature_kelvin": -10.0, "activation_energy_j_per_mol": 45000.0},
        "output_data": {"rate_constant": 0.0},
        "execution_time_ms": 1.2,
        "status": "SUCCESS",
    })
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    blocking_findings = [f for f in report.findings if f.is_blocking and f.category == ReviewCategory.SCIENTIFIC_COMPUTATION]
    assert len(blocking_findings) >= 1
    assert "positive" in blocking_findings[0].critique.lower()


def test_critic_withholds_conclusions_on_negative_kie():
    """Verify that negative kinetic isotope effect ratio triggers WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request()
    req.tool_executions.append({
        "tool_name": "chemical_kinetics_kie",
        "invoked_by": "SCIENTIFIC_TOOL_AGENT",
        "input_arguments": {"k_light": -1.0, "k_heavy": 0.5},
        "output_data": {"kie_value": -2.0},
        "execution_time_ms": 1.2,
        "status": "SUCCESS",
    })
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    kie_finding = next((f for f in report.findings if "KIE" in f.target_object), None)
    assert kie_finding is not None
    assert kie_finding.is_blocking is True


def test_critic_requires_qualification_when_tool_fallback_engaged():
    """Verify that a specialist agent engaging local fallback requires qualification."""
    req = _build_valid_request()
    req.tool_executions.append({
        "tool_name": "janus_independent_scientific_tool_agent",
        "invoked_by": "SCIENTIFIC_TOOL_AGENT",
        "input_arguments": {"fallback_engaged": True},
        "output_data": {"fallback_engaged": True},
        "execution_time_ms": 3.0,
        "status": "WARNING",
    })
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.REQUIRES_QUALIFICATION
    assert any("fallback" in lim.lower() for lim in report.disclosed_limitations)


# ======================================================================
# 5. EXPERIMENT RANKING INTEGRITY & ASSAY CALIBRATION
# ======================================================================

def test_critic_flags_unquantified_assays_and_discloses_limitations():
    """Verify that unquantified assay (EXP-WGS-05) is flagged with CRT-002 and disclosed."""
    req = _build_valid_request()
    report, critic_items = ScientificCriticEngine.evaluate(req)

    crt_002 = next((c for c in critic_items if c.id == "CRT-002"), None)
    assert crt_002 is not None
    assert "EXP-WGS-05" in crt_002.target_claim_or_object
    assert crt_002.severity == CriticSeverity.UNRESOLVED_DISAGREEMENT
    assert any("EXP-WGS-05" in lim for lim in report.disclosed_limitations)


def test_critic_detects_dual_ranking_divergence():
    """Verify that divergence between Pure EIG and Composite Utility is flagged with CRT-003."""
    req = _build_valid_request()
    # Introduce divergence: EXP-01 is EIG #1 but drops to Utility #2 due to high cost
    req.ranked_experiments = [
        {
            "experiment_id": "EXP-WGS-02",
            "utility_rank": 1,
            "eig_rank": 2,
            "cost": 1.0,
            "feasibility": 1.0,
            "expected_information_gain": 0.70,
            "composite_utility_score": 0.63,
            "quantification_status": "QUANTIFIED",
        },
        {
            "experiment_id": "EXP-WGS-01",
            "utility_rank": 2,
            "eig_rank": 1,
            "cost": 5.0,
            "feasibility": 1.0,
            "expected_information_gain": 0.85,
            "composite_utility_score": 0.56,
            "quantification_status": "QUANTIFIED",
        },
    ]
    report, critic_items = ScientificCriticEngine.evaluate(req)

    crt_003 = next((c for c in critic_items if c.id == "CRT-003"), None)
    assert crt_003 is not None
    assert "Dual Ranking Divergence" in crt_003.target_claim_or_object
    assert crt_003.severity == CriticSeverity.WARNING
    assert report.conclusion_gate == ConclusionGateStatus.REQUIRES_QUALIFICATION


def test_critic_withholds_conclusions_if_top_recommendation_unquantified():
    """Verify that recommending an unquantified assay as #1 triggers WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request()
    req.ranked_experiments[0]["quantification_status"] = "UNQUANTIFIED_NEEDS_MEASUREMENT"

    report, critic_items = ScientificCriticEngine.evaluate(req)
    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    unq_finding = next((f for f in report.findings if f.finding_id == "REV-EXP-003"), None)
    assert unq_finding is not None
    assert unq_finding.is_blocking is True


# ======================================================================
# 6. INDEPENDENT AUDITOR INTEGRATION & INVARIANTS
# ======================================================================

def test_critic_withholds_conclusions_when_auditor_failed():
    """Verify that an AUDIT_FAILED from external Auditor uAgent forces WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request(auditor_status="AUDIT_FAILED")
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    assert report.blocking_findings_count >= 1
    aud_finding = next((f for f in report.findings if f.finding_id == "REV-AUD-002"), None)
    assert aud_finding is not None
    assert aud_finding.is_blocking is True
    assert aud_finding.severity == "HIGH_SEVERITY_CHALLENGE"

    crt_006 = next(c for c in critic_items if c.id == "CRT-006")
    assert crt_006.severity == CriticSeverity.HIGH_SEVERITY_CHALLENGE
    assert crt_006.is_resolved is False


def test_critic_withholds_conclusions_when_internal_verifier_fails():
    """Verify that an internal mathematical invariant failure forces WITHHOLD_CONCLUSIONS."""
    req = _build_valid_request(is_math_verified=False)
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS
    math_finding = next((f for f in report.findings if f.finding_id == "REV-AUD-001"), None)
    assert math_finding is not None
    assert math_finding.is_blocking is True

    crt_004 = next(c for c in critic_items if c.id == "CRT-004")
    assert crt_004.severity == CriticSeverity.HIGH_SEVERITY_CHALLENGE
    assert crt_004.is_resolved is False


def test_critic_requires_qualification_when_auditor_unavailable():
    """Verify that when external Auditor uAgent is AUDIT_UNAVAILABLE, conclusions require qualification."""
    req = _build_valid_request(auditor_status="AUDIT_UNAVAILABLE")
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.REQUIRES_QUALIFICATION
    assert any("unavailable" in lim.lower() for lim in report.disclosed_limitations)

    crt_006 = next(c for c in critic_items if c.id == "CRT-006")
    assert crt_006.severity == CriticSeverity.WARNING
    assert crt_006.is_resolved is False


def test_critic_grants_sufficiently_supported_when_all_criteria_met():
    """Verify that when empirical scenario passes all checks, SUFFICIENTLY_SUPPORTED is granted."""
    req = _build_valid_request(auditor_status="AUDIT_PASSED", is_math_verified=True)
    req.case_study_id = "CS-IDEAL-001"
    req.candidate_experiments = [e for e in req.candidate_experiments if e.get("id") != "EXP-WGS-05"]
    for ev in req.evidence:
        ev["verification_status"] = "VERIFIED_ONLINE"
    report, critic_items = ScientificCriticEngine.evaluate(req)

    assert report.conclusion_gate == ConclusionGateStatus.SUFFICIENTLY_SUPPORTED
    assert report.blocking_findings_count == 0
    assert "SUFFICIENTLY SUPPORTED" in report.gate_rationale


# ======================================================================
# 7. TOOL WRAPPER EXECUTION
# ======================================================================

def test_critic_review_tool_execution():
    """Verify CriticReviewTool.execute_review produces report, record, and legacy items."""
    req = _build_valid_request()
    report, record, items = CriticReviewTool.execute_review(req)

    assert isinstance(report, ScientificReviewReport)
    assert record.tool_name == "scientific_critic_review"
    assert record.invoked_by == AgentRole.CRITIC
    assert len(items) >= 4


# ======================================================================
# 8. COORDINATOR WORKFLOW INTEGRATION & BACKWARD COMPATIBILITY
# ======================================================================

def test_coordinator_workflow_produces_review_report_and_preserves_critic_review():
    """Verify end-to-end start_investigation populates review_report, synthesis, and critic_review."""
    inp = InvestigationInput(
        question="Which pathway governs low-temperature WGS on Pt/CeO2?",
        mode="deterministic_offline_demo",
        case_study_id="CS-CAT-001",
    )
    report = ScientificInvestigationOrchestrator.start_investigation(inp)

    # 1. review_report presence and type
    assert report.review_report is not None
    assert isinstance(report.review_report, ScientificReviewReport)
    assert report.review_report.conclusion_gate in [
        ConclusionGateStatus.SUFFICIENTLY_SUPPORTED,
        ConclusionGateStatus.REQUIRES_QUALIFICATION,
    ]
    assert report.review_report.total_findings_count >= 5

    # 2. Synthesis summary reflects conclusion gate
    assert "Conclusion Gate:" in report.synthesis_summary
    assert report.review_report.conclusion_gate.value in report.synthesis_summary

    # 3. Full backward compatibility: CRT-001 to CRT-006 present
    critic_ids = [c.id for c in report.critic_review]
    for expected_id in ["CRT-001", "CRT-002", "CRT-004", "CRT-005", "CRT-006"]:
        assert expected_id in critic_ids, f"{expected_id} must be preserved in report.critic_review"

    # CRT-006 must contain auditor address
    crt_006 = next(c for c in report.critic_review if c.id == "CRT-006")
    assert "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg" in crt_006.target_claim_or_object


def test_coordinator_sequential_update_reaudits_review_report():
    """Verify supplying evidence in sequential loop re-evaluates the review report."""
    inp = InvestigationInput(
        question="Which pathway governs low-temperature WGS on Pt/CeO2?",
        mode="deterministic_offline_demo",
        case_study_id="CS-CAT-001",
    )
    init_report = ScientificInvestigationOrchestrator.start_investigation(inp)
    inv_id = init_report.investigation_id

    # Supply sequential observation for EXP-WGS-02
    updated_report = ScientificInvestigationOrchestrator.supply_new_evidence_observation(
        investigation_id=inv_id,
        experiment_id="EXP-WGS-02",
        observed_outcome="Initial_CO2_Mainly_Lattice_16O",
    )

    assert updated_report.review_report is not None
    assert isinstance(updated_report.review_report, ScientificReviewReport)
    assert "Conclusion Gate:" in updated_report.synthesis_summary
