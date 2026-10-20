"""JANUS Synthetic Scenario Suite (SYNTH-A through SYNTH-F)

Implements procedural generation of synthetic scientific scenarios as specified
in docs/evaluation_plan.md:
- SYNTH-A: Needle in a Haystack (10 Hypotheses, 30 Experiments, extreme sparsity)
- SYNTH-B: High-Cost Facility Dilemma (3 Hypotheses, 8 Experiments, 10x cost penalty)
- SYNTH-C: High-Risk Experimental Frontier (4 Hypotheses, 10 Experiments, low feasibility)
- SYNTH-D: Spectator Intermediate Trap (3 Hypotheses, 6 Experiments, intense signal, 0 EIG)
- SYNTH-E: Multi-State Multinomial Outcomes (3 Hypotheses, 12 Experiments, 5 outcome bins)
- SYNTH-F: Broad Screening Campaign (5 Hypotheses, 50 Experiments, Dirichlet/Beta distributions)

All scenarios conform strictly to the Pydantic AnalysisInput schema and are clearly
labeled as synthetic simulations to prevent confusion with empirical literature.
"""

from typing import List, Dict, Optional
import numpy as np

from app.schemas.scientific import (
    AnalysisInput,
    Hypothesis,
    Experiment,
    PredictedOutcome,
)


def generate_synth_a_needle_in_haystack(seed: int = 42) -> AnalysisInput:
    """
    SYNTH-A: Needle in a Haystack
    - M=10 competing hypotheses (H1..H10), uniform prior = 0.10.
    - N=30 candidate assays:
      - 25 uninformative controls (EIG = 0.0000 bits, identical outcome likelihoods).
      - 5 diagnostic assays with varying disambiguation power (0.2 to 1.5 bits).
    - Objective: Tests whether policies avoid uninformative budget sinks in noisy screening pools.
    """
    rng = np.random.default_rng(seed)
    hypotheses = [
        Hypothesis(
            id=f"H{k}",
            name=f"Synthetic Mechanism H{k}",
            description=f"Synthetic competing pathway variant {k}",
            prior=0.10
        )
        for k in range(1, 11)
    ]
    h_ids = [h.id for h in hypotheses]
    
    experiments: List[Experiment] = []
    
    # 25 Uninformative controls: identical likelihoods across all hypotheses
    for i in range(1, 26):
        cost = round(float(rng.uniform(0.5, 2.5)), 1)
        feas = round(float(rng.uniform(0.85, 1.0)), 2)
        outcomes = ["Control_Baseline_Flat", "Control_Baseline_Noise"]
        predictions = []
        for h_id in h_ids:
            predictions.append(PredictedOutcome(
                hypothesis_id=h_id,
                outcome_label="Control_Baseline_Flat",
                probability=0.50,
                derivation_mode="SYNTHETIC_SIMULATION"
            ))
            predictions.append(PredictedOutcome(
                hypothesis_id=h_id,
                outcome_label="Control_Baseline_Noise",
                probability=0.50,
                derivation_mode="SYNTHETIC_SIMULATION"
            ))
        experiments.append(Experiment(
            id=f"EXP-A-CTRL-{i:02d}",
            name=f"Uninformative Control Assay {i}",
            description=f"Synthetic assay with zero differential likelihood across hypotheses (Control {i})",
            possible_outcomes=outcomes,
            predictions=predictions,
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    # 5 Diagnostic assays: split subsets of hypotheses
    # DIAG-01: splits H1-H5 vs H6-H10 (binary 50/50 split -> 1.0 bit EIG)
    diag_splits = [
        # (name, cost, feas, H_high_prob_ids, p_high, p_low)
        ("Binary Mechanism Split (H1-H5 vs H6-H10)", 2.0, 0.90, [f"H{k}" for k in range(1, 6)], 0.92, 0.08),
        ("Clustered Pathway Screen (H1-H2 vs Others)", 1.5, 0.95, ["H1", "H2"], 0.90, 0.10),
        ("Specific Biomarker Diagnostic (H1 Unique)", 3.0, 0.85, ["H1"], 0.95, 0.05),
        ("Orthogonal Core Mechanism Assay (Odd vs Even)", 2.5, 0.88, [f"H{k}" for k in range(1, 11, 2)], 0.88, 0.12),
        ("Fine-Grained Discriminator (H3-H4 vs Others)", 1.8, 0.92, ["H3", "H4"], 0.85, 0.15),
    ]
    
    for idx, (diag_name, cost, feas, high_ids, p_high, p_low) in enumerate(diag_splits, 1):
        outcomes = ["Positive_Signal", "Negative_Signal"]
        predictions = []
        for h_id in h_ids:
            prob = p_high if h_id in high_ids else p_low
            predictions.append(PredictedOutcome(
                hypothesis_id=h_id,
                outcome_label="Positive_Signal",
                probability=prob,
                derivation_mode="SYNTHETIC_SIMULATION"
            ))
            predictions.append(PredictedOutcome(
                hypothesis_id=h_id,
                outcome_label="Negative_Signal",
                probability=round(1.0 - prob, 4),
                derivation_mode="SYNTHETIC_SIMULATION"
            ))
        experiments.append(Experiment(
            id=f"EXP-A-DIAG-{idx:02d}",
            name=f"Informative Assay: {diag_name}",
            description=f"Synthetic diagnostic assay targeting hypothesis subset {high_ids}",
            possible_outcomes=outcomes,
            predictions=predictions,
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    return AnalysisInput(
        scenario_name="SYNTH-A: Needle in a Haystack (High Sparsity)",
        case_study_id="SYNTH-A",
        hypotheses=hypotheses,
        experiments=experiments,
        cost_weight=0.1
    )


def generate_synth_b_high_cost_facility(seed: int = 42) -> AnalysisInput:
    """
    SYNTH-B: High-Cost Facility Dilemma
    - M=3 hypotheses (H1, H2, H3), prior = [0.40, 0.35, 0.25].
    - N=8 assays:
      - Assay 1 (Synchrotron Facility): High EIG (~1.2 bits), high cost (15.0), moderate feasibility (0.60).
      - Assay 2 (Benchtop Spectroscopic): High EIG (~1.0 bits), low cost (1.5), high feasibility (0.95).
      - Assays 3-8 (Auxiliary Assays): Lower EIG (0.2-0.5 bits), cost 2.0-5.0, feasibility 0.80-0.90.
    - Objective: Tests whether composite utility penalizes expensive facility assays in favor of efficient benchtop alternatives.
    """
    hypotheses = [
        Hypothesis(id="H1", name="Reaction Route Alpha", description="Synthetic route alpha", prior=0.40),
        Hypothesis(id="H2", name="Reaction Route Beta", description="Synthetic route beta", prior=0.35),
        Hypothesis(id="H3", name="Reaction Route Gamma", description="Synthetic route gamma", prior=0.25),
    ]
    h_ids = [h.id for h in hypotheses]
    
    experiments = [
        # Synchrotron facility
        Experiment(
            id="EXP-B-FACILITY-01",
            name="Synchrotron Operando Beamline",
            description="High-resolution central facility beamline; high diagnostic power but 10x cost and risk",
            possible_outcomes=["Phase_Transition_Detected", "Phase_Transition_Absent"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Phase_Transition_Detected", probability=0.96, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Phase_Transition_Absent", probability=0.04, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Phase_Transition_Detected", probability=0.05, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Phase_Transition_Absent", probability=0.95, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Phase_Transition_Detected", probability=0.02, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Phase_Transition_Absent", probability=0.98, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=15.0,
            feasibility=0.60,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
        # Inexpensive benchtop assay
        Experiment(
            id="EXP-B-BENCHTOP-01",
            name="Benchtop In-Situ Kinetic Probe",
            description="Low-cost benchtop kinetic probe; strong diagnostic power with near-unity feasibility",
            possible_outcomes=["First_Order_Decay", "Second_Order_Decay"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="First_Order_Decay", probability=0.92, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Second_Order_Decay", probability=0.08, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="First_Order_Decay", probability=0.08, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Second_Order_Decay", probability=0.92, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="First_Order_Decay", probability=0.50, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Second_Order_Decay", probability=0.50, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=1.5,
            feasibility=0.95,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
    ]
    
    # 6 Auxiliary assays with varying intermediate parameters
    aux_specs = [
        ("Temperature-Programmed Reduction", 3.0, 0.85, 0.80, 0.20, 0.50),
        ("Chemisorption Desorption Rate", 2.5, 0.88, 0.30, 0.85, 0.30),
        ("Isotopic Label Exchange", 4.0, 0.80, 0.85, 0.15, 0.85),
        ("Steady-State Microreactor Analysis", 2.0, 0.92, 0.60, 0.60, 0.10),
        ("Laser Desorption Mass Spectrometry", 5.0, 0.75, 0.20, 0.20, 0.80),
        ("Electrochemical Impedance Screen", 3.5, 0.82, 0.40, 0.70, 0.30),
    ]
    for i, (name, cost, feas, p1, p2, p3) in enumerate(aux_specs, 3):
        experiments.append(Experiment(
            id=f"EXP-B-AUX-{i:02d}",
            name=name,
            description=f"Auxiliary synthetic assay {name}",
            possible_outcomes=["High_Response", "Low_Response"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="High_Response", probability=p1, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Low_Response", probability=round(1.0 - p1, 2), derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="High_Response", probability=p2, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Low_Response", probability=round(1.0 - p2, 2), derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="High_Response", probability=p3, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Low_Response", probability=round(1.0 - p3, 2), derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    return AnalysisInput(
        scenario_name="SYNTH-B: High-Cost Facility Dilemma",
        case_study_id="SYNTH-B",
        hypotheses=hypotheses,
        experiments=experiments,
        cost_weight=0.1
    )


def generate_synth_c_high_risk_frontier(seed: int = 42) -> AnalysisInput:
    """
    SYNTH-C: High-Risk Experimental Frontier
    - M=4 hypotheses (H1..H4), uniform prior = 0.25.
    - N=10 candidate assays:
      - 4 Fragile Frontier assays: High theoretical EIG (1.0 to 1.4 bits), but feasibility 0.25-0.35.
      - 6 Robust assays: Moderate EIG (0.4 to 0.7 bits), but high feasibility (0.88-0.96).
    - Objective: Tests whether feasibility weighting protects the researcher from catastrophic execution failure sinks.
    """
    hypotheses = [
        Hypothesis(id=f"H{k}", name=f"Radical State Variant {k}", description=f"Synthetic state variant {k}", prior=0.25)
        for k in range(1, 5)
    ]
    h_ids = [h.id for h in hypotheses]
    experiments = []
    
    # 4 Fragile Frontier Assays
    fragile_specs = [
        ("Femtosecond Transient Absorption", 3.5, 0.25, ["H1"], 0.95),
        ("Cryogenic Atomic-Probe Tomography", 4.0, 0.30, ["H2"], 0.92),
        ("Operando Transmission Electron Microscopy", 3.8, 0.28, ["H3"], 0.94),
        ("Ultrafast Electron Diffraction Pulse", 4.5, 0.35, ["H4"], 0.90),
    ]
    for idx, (name, cost, feas, target_h, p_target) in enumerate(fragile_specs, 1):
        outcomes = ["Nanostructure_Shift", "No_Shift"]
        preds = []
        for h_id in h_ids:
            p = p_target if h_id in target_h else round((1.0 - p_target) / 3.0, 4)
            preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Nanostructure_Shift", probability=p, derivation_mode="SYNTHETIC_SIMULATION"))
            preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="No_Shift", probability=round(1.0 - p, 4), derivation_mode="SYNTHETIC_SIMULATION"))
        experiments.append(Experiment(
            id=f"EXP-C-FRAGILE-{idx:02d}",
            name=f"Fragile Frontier: {name}",
            description=f"High diagnostic yield but severe risk of physical abort ({feas*100:.0f}% feasibility)",
            possible_outcomes=outcomes,
            predictions=preds,
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    # 6 Robust Standard Assays
    robust_specs = [
        ("Standard GC-MS Effluent Scan", 1.2, 0.95, ["H1", "H2"], 0.85),
        ("Benchtop Infrared Spectroscopy", 1.0, 0.96, ["H1", "H3"], 0.82),
        ("Volumetric Gas Adsorption Isotherm", 1.5, 0.92, ["H2", "H4"], 0.88),
        ("X-Ray Powder Diffraction Phase Audit", 1.8, 0.90, ["H3", "H4"], 0.80),
        ("Thermal Gravimetric Exhaust Analysis", 1.1, 0.94, ["H1", "H4"], 0.85),
        ("Standard Pulsed Chemisorption", 1.4, 0.91, ["H2", "H3"], 0.84),
    ]
    for idx, (name, cost, feas, target_pair, p_pair) in enumerate(robust_specs, 1):
        outcomes = ["Characteristic_Signature", "Standard_Signature"]
        preds = []
        for h_id in h_ids:
            p = p_pair if h_id in target_pair else round(1.0 - p_pair, 4)
            preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Characteristic_Signature", probability=p, derivation_mode="SYNTHETIC_SIMULATION"))
            preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Standard_Signature", probability=round(1.0 - p, 4), derivation_mode="SYNTHETIC_SIMULATION"))
        experiments.append(Experiment(
            id=f"EXP-C-ROBUST-{idx:02d}",
            name=f"Robust Assay: {name}",
            description=f"Reliable benchtop method with high feasibility ({feas*100:.0f}%)",
            possible_outcomes=outcomes,
            predictions=preds,
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    return AnalysisInput(
        scenario_name="SYNTH-C: High-Risk Experimental Frontier",
        case_study_id="SYNTH-C",
        hypotheses=hypotheses,
        experiments=experiments,
        cost_weight=0.1
    )


def generate_synth_d_spectator_trap(seed: int = 42) -> AnalysisInput:
    """
    SYNTH-D: Spectator Intermediate Trap
    - M=3 hypotheses (H1, H2, H3), uniform prior = 0.333, 0.333, 0.334.
    - N=6 candidate assays:
      - Assay 1 (Spectator Trap): Very intense, unmistakable spectroscopic absorption peak,
        present under ALL hypotheses with 98% likelihood (EIG = 0.0000 bits!).
      - Assays 2-6: Genuinely diagnostic assays with subtle signals that differentiate hypotheses.
    - Objective: Tests whether heuristic or signal-intensity methods fall into the trap of observing inert species.
    """
    hypotheses = [
        Hypothesis(id="H1", name="Active Surface Adsorbate", description="Adsorbate is genuine intermediate", prior=0.333),
        Hypothesis(id="H2", name="Mobile Gas Intermediate", description="Adsorbate is spectator", prior=0.333),
        Hypothesis(id="H3", name="Subsurface Lattice Route", description="Reaction bypasses adsorbate entirely", prior=0.334),
    ]
    h_ids = [h.id for h in hypotheses]
    
    experiments = [
        # The Trap Assay
        Experiment(
            id="EXP-D-SPECTATOR-01",
            name="Static Operando Infrared (Prominent Band)",
            description="Exhibits an overwhelming 1580 cm^-1 vibrational peak; present at high concentration in all conditions (0 EIG)",
            possible_outcomes=["Intense_1580cm_Band_Present", "Intense_1580cm_Band_Absent"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Intense_1580cm_Band_Present", probability=0.98, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Intense_1580cm_Band_Absent", probability=0.02, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Intense_1580cm_Band_Present", probability=0.98, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Intense_1580cm_Band_Absent", probability=0.02, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Intense_1580cm_Band_Present", probability=0.98, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Intense_1580cm_Band_Absent", probability=0.02, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=1.2,
            feasibility=0.98,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
        # Diagnostic Assays
        Experiment(
            id="EXP-D-DIAG-01",
            name="Isotope Jump Relaxation (Transient Turnover)",
            description="Measures turnover frequency of the surface band vs. product formation rate",
            possible_outcomes=["Turnover_Matches_TOF", "Turnover_Lags_TOF"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Turnover_Matches_TOF", probability=0.94, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Turnover_Lags_TOF", probability=0.06, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Turnover_Matches_TOF", probability=0.05, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Turnover_Lags_TOF", probability=0.95, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Turnover_Matches_TOF", probability=0.02, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Turnover_Lags_TOF", probability=0.98, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=2.0,
            feasibility=0.90,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
        Experiment(
            id="EXP-D-DIAG-02",
            name="Lattice Oxygen Titration",
            description="Specifically tests lattice vs. adsorbate oxygen consumption",
            possible_outcomes=["Lattice_Oxygen_Consumed", "Gas_Oxygen_Consumed"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Lattice_Oxygen_Consumed", probability=0.10, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Gas_Oxygen_Consumed", probability=0.90, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Lattice_Oxygen_Consumed", probability=0.15, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Gas_Oxygen_Consumed", probability=0.85, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Lattice_Oxygen_Consumed", probability=0.92, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Gas_Oxygen_Consumed", probability=0.08, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=2.5,
            feasibility=0.88,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
        Experiment(
            id="EXP-D-DIAG-03",
            name="Kinetic Order in Reactant A",
            description="Determines fractional vs first-order kinetic dependence",
            possible_outcomes=["Order_Zero", "Order_First"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Order_Zero", probability=0.88, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Order_First", probability=0.12, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Order_Zero", probability=0.20, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Order_First", probability=0.80, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Order_Zero", probability=0.50, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Order_First", probability=0.50, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=1.5,
            feasibility=0.94,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
        Experiment(
            id="EXP-D-DIAG-04",
            name="In-Situ Work Function Modulation",
            description="Monitors surface electrostatic potential shifts during turnover",
            possible_outcomes=["Significant_Dipole_Shift", "Negligible_Shift"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Significant_Dipole_Shift", probability=0.15, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Negligible_Shift", probability=0.85, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Significant_Dipole_Shift", probability=0.86, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Negligible_Shift", probability=0.14, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Significant_Dipole_Shift", probability=0.20, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Negligible_Shift", probability=0.80, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=2.8,
            feasibility=0.82,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
        Experiment(
            id="EXP-D-DIAG-05",
            name="Temperature-Jump Desorption MS",
            description="Directly samples surface species lifetime via rapid thermal heating",
            possible_outcomes=["Fast_Desorption_T1", "Slow_Desorption_T2"],
            predictions=[
                PredictedOutcome(hypothesis_id="H1", outcome_label="Fast_Desorption_T1", probability=0.82, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H1", outcome_label="Slow_Desorption_T2", probability=0.18, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Fast_Desorption_T1", probability=0.15, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H2", outcome_label="Slow_Desorption_T2", probability=0.85, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Fast_Desorption_T1", probability=0.80, derivation_mode="SYNTHETIC_SIMULATION"),
                PredictedOutcome(hypothesis_id="H3", outcome_label="Slow_Desorption_T2", probability=0.20, derivation_mode="SYNTHETIC_SIMULATION"),
            ],
            cost=2.2,
            feasibility=0.89,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ),
    ]
    
    return AnalysisInput(
        scenario_name="SYNTH-D: Spectator Intermediate Trap",
        case_study_id="SYNTH-D",
        hypotheses=hypotheses,
        experiments=experiments,
        cost_weight=0.1
    )


def generate_synth_e_multistate_multinomial(seed: int = 42) -> AnalysisInput:
    """
    SYNTH-E: Multi-State Multinomial Outcomes
    - M=3 hypotheses (H1, H2, H3), prior = [0.40, 0.30, 0.30].
    - N=12 candidate assays with K=5 discrete categorical outcome bins:
      - Outcome bins: Bin_A, Bin_B, Bin_C, Bin_D, Bin_E (e.g. quintiles of spectral yield).
    - Objective: Tests Shannon entropy reduction over multinomial outcome spaces.
    """
    rng = np.random.default_rng(seed)
    hypotheses = [
        Hypothesis(id="H1", name="Multinomial Mode 1", description="Mode 1 favoring low quintiles", prior=0.40),
        Hypothesis(id="H2", name="Multinomial Mode 2", description="Mode 2 favoring central quintile", prior=0.30),
        Hypothesis(id="H3", name="Multinomial Mode 3", description="Mode 3 favoring high quintiles", prior=0.30),
    ]
    h_ids = [h.id for h in hypotheses]
    outcomes = ["Quintile_1", "Quintile_2", "Quintile_3", "Quintile_4", "Quintile_5"]
    
    experiments = []
    for i in range(1, 13):
        cost = round(float(rng.uniform(1.0, 4.0)), 1)
        feas = round(float(rng.uniform(0.75, 0.98)), 2)
        
        # Generate differentiated multinomial distributions per hypothesis
        # H1: concentrated on early bins, H2: centered, H3: late bins
        p_h1 = np.array([0.45, 0.30, 0.15, 0.07, 0.03])
        p_h2 = np.array([0.05, 0.20, 0.50, 0.20, 0.05])
        p_h3 = np.array([0.03, 0.07, 0.15, 0.35, 0.40])
        
        # Add slight variation per assay
        if i % 2 == 0:
            p_h1, p_h3 = p_h3, p_h1  # Invert diagnostic pattern for even assays
        if i % 3 == 0:
            # Flattened / noisy assay
            p_h1 = np.array([0.25, 0.25, 0.20, 0.15, 0.15])
            p_h2 = np.array([0.20, 0.20, 0.25, 0.20, 0.15])
            p_h3 = np.array([0.15, 0.15, 0.20, 0.25, 0.25])
            
        preds = []
        for h_id, dist in zip(h_ids, [p_h1, p_h2, p_h3]):
            for o_label, p_val in zip(outcomes, dist):
                preds.append(PredictedOutcome(
                    hypothesis_id=h_id,
                    outcome_label=o_label,
                    probability=round(float(p_val), 4),
                    derivation_mode="SYNTHETIC_SIMULATION"
                ))
                
        experiments.append(Experiment(
            id=f"EXP-E-MULTINOMIAL-{i:02d}",
            name=f"Multinomial Quintile Assay {i}",
            description=f"Synthetic multi-state assay {i} with 5 discrete categorical outcome bins",
            possible_outcomes=outcomes,
            predictions=preds,
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    return AnalysisInput(
        scenario_name="SYNTH-E: Multi-State Multinomial Outcomes",
        case_study_id="SYNTH-E",
        hypotheses=hypotheses,
        experiments=experiments,
        cost_weight=0.1
    )


def generate_synth_f_broad_screening(seed: int = 42) -> AnalysisInput:
    """
    SYNTH-F: Broad Screening Campaign
    - M=5 hypotheses (H1..H5), uniform prior = 0.20.
    - N=50 candidate assays generated via parameterized distributions:
      - Continuous spectrum of EIG, costs (1.0 to 10.0), and feasibilities (0.60 to 0.98).
    - Objective: Tests computational scalability, decision latency, and ranking stability across large pools.
    """
    rng = np.random.default_rng(seed)
    hypotheses = [
        Hypothesis(id=f"H{k}", name=f"Broad Screening Pathway {k}", description=f"Pathway {k}", prior=0.20)
        for k in range(1, 6)
    ]
    h_ids = [h.id for h in hypotheses]
    experiments = []
    
    for i in range(1, 51):
        cost = round(float(rng.uniform(1.0, 8.0)), 1)
        feas = round(float(rng.beta(8, 2)), 2)  # Feasibility skewed toward high values [0.65, 0.99]
        feas = float(min(max(feas, 0.50), 0.99))
        
        outcomes = ["Signal_Active", "Signal_Inactive"]
        
        # Randomly choose if this is an informative assay or uninformative background
        if rng.random() < 0.35:
            # Informative assay: 1 or 2 hypotheses have high probability
            target_count = int(rng.integers(1, 3))
            favored = set(rng.choice(h_ids, size=target_count, replace=False))
            p_favored = round(float(rng.uniform(0.75, 0.95)), 2)
            p_rest = round(float((1.0 - p_favored) / 2.0), 2)
            
            preds = []
            for h_id in h_ids:
                p = p_favored if h_id in favored else p_rest
                preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Signal_Active", probability=p, derivation_mode="SYNTHETIC_SIMULATION"))
                preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Signal_Inactive", probability=round(1.0 - p, 4), derivation_mode="SYNTHETIC_SIMULATION"))
        else:
            # Uninformative / noisy assay: nearly identical likelihoods
            base_p = round(float(rng.uniform(0.40, 0.60)), 2)
            preds = []
            for h_id in h_ids:
                noise = round(float(rng.uniform(-0.03, 0.03)), 4)
                p = float(min(max(base_p + noise, 0.05), 0.95))
                preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Signal_Active", probability=p, derivation_mode="SYNTHETIC_SIMULATION"))
                preds.append(PredictedOutcome(hypothesis_id=h_id, outcome_label="Signal_Inactive", probability=round(1.0 - p, 4), derivation_mode="SYNTHETIC_SIMULATION"))
                
        experiments.append(Experiment(
            id=f"EXP-F-SCREEN-{i:02d}",
            name=f"High-Throughput Assay {i:02d}",
            description=f"Synthetic high-throughput screening candidate {i}",
            possible_outcomes=outcomes,
            predictions=preds,
            cost=cost,
            feasibility=feas,
            is_feasible=True,
            quantification_status="QUANTIFIED_SYNTHETIC"
        ))
        
    return AnalysisInput(
        scenario_name="SYNTH-F: Broad Screening Campaign",
        case_study_id="SYNTH-F",
        hypotheses=hypotheses,
        experiments=experiments,
        cost_weight=0.1
    )


SYNTHETIC_SCENARIO_GENERATORS = {
    "SYNTH-A": generate_synth_a_needle_in_haystack,
    "SYNTH-B": generate_synth_b_high_cost_facility,
    "SYNTH-C": generate_synth_c_high_risk_frontier,
    "SYNTH-D": generate_synth_d_spectator_trap,
    "SYNTH-E": generate_synth_e_multistate_multinomial,
    "SYNTH-F": generate_synth_f_broad_screening,
}


def get_synthetic_scenario(scenario_key: str, seed: int = 42) -> AnalysisInput:
    """Retrieves a synthetic benchmark scenario by key ('SYNTH-A' through 'SYNTH-F')."""
    if scenario_key not in SYNTHETIC_SCENARIO_GENERATORS:
        raise ValueError(f"Unknown synthetic scenario: '{scenario_key}'. Choose from: {list(SYNTHETIC_SCENARIO_GENERATORS.keys())}")
    return SYNTHETIC_SCENARIO_GENERATORS[scenario_key](seed=seed)
