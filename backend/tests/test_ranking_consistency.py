"""Regression tests for Phase 3.2: Ranking Consistency and Dual Metric Ordering.

Verifies:
1. Utility Ranking Order vs. EIG Ranking Order divergence for candidate assays.
2. Specific multi-criteria trade-off between EXP-WGS-03 (high EIG, high cost) and EXP-WGS-04 (moderate EIG, low cost).
3. Coincidence of EXP-WGS-02 as optimal under both objectives.
4. Non-fabrication of EXP-WGS-05 (remains unquantified with None ranks).
5. Exact analytical population moments in benchmark evaluation.
"""

import pytest
import numpy as np
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.engine import ScientificEngine
from evaluation.benchmark_evaluation import run_reproducible_benchmark


def test_dual_ranking_order_divergence():
    """
    Verifies that JANUS produces two distinct, mathematically valid rankings:
    - Utility Rank (primary): [EXP-WGS-02, EXP-WGS-01, EXP-WGS-04, EXP-WGS-03, EXP-WGS-06]
    - EIG Rank (pure info):   [EXP-WGS-02, EXP-WGS-01, EXP-WGS-03, EXP-WGS-04, EXP-WGS-06]
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)
    
    ranked = result.ranked_experiments
    assert len(ranked) == 5
    
    # 1. Primary Utility Ranking Order
    utility_order = [s.experiment_id for s in ranked]
    assert utility_order == [
        "EXP-WGS-02",  # Utility = 0.4171, Rank #1
        "EXP-WGS-01",  # Utility = 0.3944, Rank #2
        "EXP-WGS-04",  # Utility = 0.2797, Rank #3
        "EXP-WGS-03",  # Utility = 0.1601, Rank #4
        "EXP-WGS-06",  # Utility = 0.0000, Rank #5
    ]
    
    # Verify sequential utility ranks
    for idx, s in enumerate(ranked, start=1):
        assert s.utility_rank == idx
        assert s.rank == idx  # Backward compatibility
    
    # 2. Pure EIG Ranking Order
    eig_sorted = sorted(ranked, key=lambda s: s.eig_rank)
    eig_order = [s.experiment_id for s in eig_sorted]
    assert eig_order == [
        "EXP-WGS-02",  # EIG = 0.5593 bits, Rank #1
        "EXP-WGS-01",  # EIG = 0.4931 bits, Rank #2
        "EXP-WGS-03",  # EIG = 0.3775 bits, Rank #3
        "EXP-WGS-04",  # EIG = 0.3233 bits, Rank #4
        "EXP-WGS-06",  # EIG = 0.0000 bits, Rank #5
    ]
    
    for idx, s in enumerate(eig_sorted, start=1):
        assert s.eig_rank == idx


def test_ranking_divergence_wgs03_vs_wgs04():
    """
    Explicitly tests the exact mathematical cause of the ranking inversion:
    EXP-WGS-03 (Ce L3-edge XAS) has higher EIG than EXP-WGS-04 (KIE),
    but EXP-WGS-04 has higher composite utility due to feasibility and cost.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)
    scores = {s.experiment_id: s for s in result.ranked_experiments}
    
    s3 = scores["EXP-WGS-03"]
    s4 = scores["EXP-WGS-04"]
    
    # Raw EIG: EXP-WGS-03 > EXP-WGS-04
    assert s3.expected_information_gain > s4.expected_information_gain
    assert s3.expected_information_gain == pytest.approx(0.377465, abs=1e-4)
    assert s4.expected_information_gain == pytest.approx(0.323346, abs=1e-4)
    assert s3.eig_rank == 3
    assert s4.eig_rank == 4
    
    # Cost & Feasibility comparison
    assert s3.cost == 6.5  # Synchrotron beamline
    assert s4.cost == 1.1  # Benchtop mass spec
    assert s3.feasibility == 0.70
    assert s4.feasibility == 0.96
    
    # Composite Utility: EXP-WGS-04 > EXP-WGS-03
    alpha = 0.1
    expected_u3 = (0.70 * s3.expected_information_gain) / (1.0 + alpha * 6.5)
    expected_u4 = (0.96 * s4.expected_information_gain) / (1.0 + alpha * 1.1)
    
    assert s3.composite_utility_score == pytest.approx(expected_u3, abs=1e-4)
    assert s4.composite_utility_score == pytest.approx(expected_u4, abs=1e-4)
    assert s4.composite_utility_score > s3.composite_utility_score
    
    assert s4.utility_rank == 3
    assert s3.utility_rank == 4


def test_top_candidate_simultaneous_optimality():
    """
    Confirms that EXP-WGS-02 is strictly optimal under both pure EIG and composite utility.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)
    top = result.ranked_experiments[0]
    
    assert top.experiment_id == "EXP-WGS-02"
    assert top.utility_rank == 1
    assert top.eig_rank == 1
    assert top.expected_information_gain == pytest.approx(0.559251, abs=1e-4)
    assert top.composite_utility_score == pytest.approx(0.417068, abs=1e-4)


def test_unquantified_assay_preserves_none_ranks():
    """
    Confirms that EXP-WGS-05 is not assigned artificial ranks or fabricated probabilities.
    """
    scenario = get_wgs_case_study_scenario()
    result = ScientificEngine.execute_analysis(scenario)
    
    assert len(result.unquantified_experiments) == 1
    unq = result.unquantified_experiments[0]
    
    assert unq.experiment_id == "EXP-WGS-05"
    assert unq.rank is None
    assert unq.utility_rank is None
    assert unq.eig_rank is None
    assert unq.quantification_status == "UNQUANTIFIED_NEEDS_MEASUREMENT"
    assert unq.expected_information_gain == 0.0
    assert unq.composite_utility_score == 0.0


def test_benchmark_report_contains_dual_ranks():
    """
    Verifies that the reproducible benchmark evaluation report exposes both utility_rank
    and eig_rank for all candidates and for selected policies.
    """
    report = run_reproducible_benchmark(seed=42, monte_carlo_samples=1000)
    
    for c in report.candidate_experiments:
        assert "utility_rank" in c
        assert "eig_rank" in c
        assert "rank" in c
        assert c["utility_rank"] == c["rank"]
        assert 1 <= c["utility_rank"] <= 5
        assert 1 <= c["eig_rank"] <= 5
    
    # Check JANUS policy
    assert report.janus_policy.utility_rank == 1
    assert report.janus_policy.eig_rank == 1
    assert report.janus_policy.selected_experiment_ids == ["EXP-WGS-02"]
    
    # Check Cheapest policy
    assert report.cheapest_heuristic_policy.selected_experiment_ids == ["EXP-WGS-06"]
    assert report.cheapest_heuristic_policy.utility_rank == 5
    assert report.cheapest_heuristic_policy.eig_rank == 5
    
    # Exact analytical baseline values
    assert report.exact_random_baseline.exact_mean_eig == pytest.approx(0.3506, abs=1e-4)
    assert report.exact_random_baseline.exact_population_std_eig == pytest.approx(0.1940, abs=1e-4)
    assert report.exact_random_baseline.exact_mean_utility == pytest.approx(0.2503, abs=1e-4)
    assert report.exact_random_baseline.probability_of_selecting_optimal == pytest.approx(0.20, abs=1e-4)
    assert report.exact_random_baseline.exact_waste_rate == pytest.approx(0.20, abs=1e-4)
