"""Regression tests for Part 0 Scientific Discrepancy Resolutions.

1. WGS Prior Baseline and Sequential Update Invariant:
   - Proves CS-CAT-001 baseline priors are strictly (0.50, 0.20, 0.30) for (H1, H2, H3).
   - Proves that observation EXP-WGS-02 = Initial_CO2_Mainly_Lattice_16O deterministically updates
     H1 from 50.0% to 89.84375% (0.460 / 0.512).
   - Documents the root cause of the Phase 2 report documentation typo: the summary text conflated
     a toy unit test fixture (0.40, 0.35, 0.25) with the real case study (0.50, 0.20, 0.30).

2. Meunier 2007 Citation DOI Clerical Error Resolution:
   - Proves that CLM-WGS-003 and CLM-WGS-007 cite F. C. Meunier et al., J. Catal. 252 (2007) 18-22,
     whose authoritative publisher DOI is 10.1016/j.jcat.2007.09.003.
   - Proves that the previous erroneous DOI 10.1016/j.jcat.2007.09.006 (Conesa et al., Beckmann rearrangement)
     is correctly identified as METADATA_MISMATCH when checked against Meunier citation data.
"""

import pytest
import json
from scientific.evidence_ingestion import get_wgs_case_study_scenario, load_evidence_ledger
from scientific.sequential_engine import compute_bayesian_posterior_update
from scientific.engine import ScientificEngine
from agents.tools import CrossrefValidationTool, BibliographicVerificationStatus


def test_wgs_priors_calibrated_baseline_and_bayesian_update():
    """Verifies that CS-CAT-001 starts at 50/20/30 and updates to 89.84%, resolving the 40% typo."""
    scenario = get_wgs_case_study_scenario()

    # 1. Assert calibrated initial priors
    priors = {h.id: h.prior for h in scenario.hypotheses}
    assert priors["H1"] == 0.50, "H1 (Redox) must initialize at 0.50"
    assert priors["H2"] == 0.20, "H2 (Formate) must initialize at 0.20"
    assert priors["H3"] == 0.30, "H3 (Carboxyl) must initialize at 0.30"
    assert sum(priors.values()) == pytest.approx(1.0, abs=1e-6)

    # 2. Assert EXP-WGS-02 predictions for Initial_CO2_Mainly_Lattice_16O
    exp_wgs_02 = next(e for e in scenario.experiments if e.id == "EXP-WGS-02")
    preds = {p.hypothesis_id: p.probability for p in exp_wgs_02.predictions if p.outcome_label == "Initial_CO2_Mainly_Lattice_16O"}
    assert preds["H1"] == 0.92
    assert preds["H2"] == 0.08
    assert preds["H3"] == 0.12

    # 3. Compute Bayes update step-by-step
    # P(y, H1) = 0.50 * 0.92 = 0.460
    # P(y, H2) = 0.20 * 0.08 = 0.016
    # P(y, H3) = 0.30 * 0.12 = 0.036
    # Marginal P(y) = 0.460 + 0.016 + 0.036 = 0.512
    # P(H1|y) = 0.460 / 0.512 = 0.8984375 (~89.84%)
    expected_p_h1 = 0.460 / 0.512
    expected_p_h2 = 0.016 / 0.512
    expected_p_h3 = 0.036 / 0.512

    likelihood_matrix = {}
    for p in exp_wgs_02.predictions:
        if p.hypothesis_id not in likelihood_matrix:
            likelihood_matrix[p.hypothesis_id] = {}
        likelihood_matrix[p.hypothesis_id][p.outcome_label] = p.probability

    new_priors = compute_bayesian_posterior_update(
        prior=priors,
        observed_outcome="Initial_CO2_Mainly_Lattice_16O",
        likelihood_matrix=likelihood_matrix,
    )

    assert new_priors["H1"] == pytest.approx(expected_p_h1, abs=1e-4)
    assert new_priors["H2"] == pytest.approx(expected_p_h2, abs=1e-4)
    assert new_priors["H3"] == pytest.approx(expected_p_h3, abs=1e-4)
    assert pytest.approx(new_priors["H1"], abs=1e-4) == 0.8984


def test_meunier_2007_doi_authoritative_resolution():
    """Verifies that evidence ledger claims CLM-WGS-003 and CLM-WGS-007 resolve to 10.1016/j.jcat.2007.09.003."""
    ledger = load_evidence_ledger()
    clm_003 = next(c for c in ledger if c.id == "CLM-WGS-003")
    clm_007 = next(c for c in ledger if c.id == "CLM-WGS-007")

    # Authoritative DOI for J. Catal. 252 (2007) 18-22
    assert clm_003.source_doi == "10.1016/j.jcat.2007.09.003"
    assert clm_007.source_doi == "10.1016/j.jcat.2007.09.003"
    assert "Meunier" in clm_003.source
    assert "Meunier" in clm_007.source


def test_conesa_doi_detected_as_metadata_mismatch_against_meunier_claim():
    """Verifies that 10.1016/j.jcat.2007.09.006 (Conesa et al.) is flagged as METADATA_MISMATCH."""
    result = CrossrefValidationTool.verify_doi(
        doi="10.1016/j.jcat.2007.09.006",
        expected_title="Quantitative DRIFTS investigation of possible reaction mechanisms for the water-gas shift reaction",
        expected_citation="F. C. Meunier, J. Catal. 252 (2007) 18-22",
        expected_authors=["Meunier et al."],
        expected_year=2007,
    )
    assert result["status"] == BibliographicVerificationStatus.METADATA_MISMATCH
    assert result["mismatch_details"] is not None
    assert "CONESA" in str(result["mismatch_details"]).upper() or "CONESA" in str(result.get("bibliographic_metadata", {}).get("authors", "")).upper()
