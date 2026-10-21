"""JANUS Case Study Scenario: CS-OER-002

Oxygen Evolution Reaction Mechanism on Perovskite Electrocatalysts (La_{1-x}Sr_xCoO_{3-delta}).
Constructs the scenario from the frozen specification and evidence ledger:
- Competing Hypotheses:
  - H1: Adsorbate Evolution Mechanism (AEM) [prior = 0.35]
  - H2: Lattice Oxygen-Mediated Mechanism (LOM) [prior = 0.45]
  - H3: Oxide Path / Surface Radical Coupling (OPM) [prior = 0.20]
- 5 Candidate Assays:
  - EXP-OER-01: Operando 18O-Labeled DEMS (Cost = 5.5, Feas = 0.75)
  - EXP-OER-02: Multi-pH Overpotential Titration on RHE Scale (Cost = 1.2, Feas = 0.95)
  - EXP-OER-03: Operando EQCM Mass Loss Monitoring (Cost = 2.0, Feas = 0.88)
  - EXP-OER-04: In Situ Soft XAS at O K-edge (Cost = 7.0, Feas = 0.65)
  - EXP-OER-05: Ex-Situ HR-TEM Morphology Inspection (Cost = 0.8, Feas = 0.98, Negative Control)

All parameters conform strictly to docs/case_study/CS_OER_002_evidence_ledger.md.
"""

from typing import List
from app.schemas.scientific import (
    AnalysisInput,
    Hypothesis,
    Experiment,
    PredictedOutcome,
)


def get_oer_case_study_scenario() -> AnalysisInput:
    """
    Constructs the frozen CS-OER-002 benchmark scenario for the alkaline
    Oxygen Evolution Reaction mechanism on transition-metal perovskite oxides.
    """
    hypotheses = [
        Hypothesis(
            id="H1",
            name="Adsorbate Evolution Mechanism (AEM)",
            description="Conventional 4-step concerted proton-electron transfer on localized Co surface cations; scaling relation Delta G(*OOH) - Delta G(*OH) approx 3.2 eV limits overpotential.",
            prior=0.35,
            assumptions=[
                "Concerted proton-coupled electron transfers (CPET)",
                "Lattice oxygen acts solely as spectator framework",
                "Evolved O2 originates from electrolyte water"
            ],
            status="active"
        ),
        Hypothesis(
            id="H2",
            name="Lattice Oxygen-Mediated Mechanism (LOM)",
            description="Direct lattice oxygen redox via ligand holes in covalent Co-O bonds; direct O-O coupling between surface adsorbate and lattice oxygen creates surface oxygen vacancies (Vo).",
            prior=0.45,
            assumptions=[
                "High Co-O covalency positions O 2p-band center near Fermi level",
                "Direct participation of lattice oxygen in O-O bond formation",
                "Oxygen vacancy creation leads to surface amorphization and cation leaching"
            ],
            status="active"
        ),
        Hypothesis(
            id="H3",
            name="Oxide Path / Surface Radical Coupling (OPM)",
            description="Non-concerted direct homolytic radical coupling between adjacent surface oxyl species (*O_radical + *O_radical -> O2) without extracting bulk lattice oxygen into gas phase.",
            prior=0.20,
            assumptions=[
                "Adjacent surface oxyl radicals form under polarization",
                "Direct radical-radical coupling bypasses *OOH scaling bottleneck",
                "Surface remains predominantly stable without continuous bulk vacancy extraction"
            ],
            status="active"
        ),
    ]

    experiments: List[Experiment] = [
        # EXP-OER-01: Operando 18O-Labeled DEMS
        Experiment(
            id="EXP-OER-01",
            name="Operando 18O-Labeled DEMS",
            description="Pre-annealed 18O-labeled perovskite in flow-cell DEMS during alkaline OER in 16O water; tracks m/z 34 (16O18O) vs 32 (16O2).",
            possible_outcomes=[
                "Significant_Lattice_18O_In_O2",
                "Predominantly_Electrolyte_16O"
            ],
            predictions=[
                PredictedOutcome(
                    outcome_label="Significant_Lattice_18O_In_O2",
                    hypothesis_id="H1",
                    probability=0.08,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Background water-catalyst isotope exchange floor (Grimaud 2017)"
                ),
                PredictedOutcome(
                    outcome_label="Predominantly_Electrolyte_16O",
                    hypothesis_id="H1",
                    probability=0.92,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Concerted CPET uses electrolyte water exclusively"
                ),
                PredictedOutcome(
                    outcome_label="Significant_Lattice_18O_In_O2",
                    hypothesis_id="H2",
                    probability=0.88,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Direct lattice oxygen participation in O-O bond (Grimaud 2017)"
                ),
                PredictedOutcome(
                    outcome_label="Predominantly_Electrolyte_16O",
                    hypothesis_id="H2",
                    probability=0.12,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Residual accounts for incomplete 18O pre-enrichment"
                ),
                PredictedOutcome(
                    outcome_label="Significant_Lattice_18O_In_O2",
                    hypothesis_id="H3",
                    probability=0.15,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Surface radical oxygen atom exchange with electrolyte (Rong 2016)"
                ),
                PredictedOutcome(
                    outcome_label="Predominantly_Electrolyte_16O",
                    hypothesis_id="H3",
                    probability=0.85,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Radical coupling occurs between surface oxo species derived from water"
                ),
            ],
            cost=5.5,
            feasibility=0.75,
            quantification_status="QUANTIFIED_BAYESIAN",
            is_feasible=True
        ),

        # EXP-OER-02: Multi-pH Overpotential Titration on RHE Scale
        Experiment(
            id="EXP-OER-02",
            name="Multi-pH Overpotential Titration on RHE Scale",
            description="Rotating disk electrode OER chronopotentiometry across pH 12.0 - 14.3 on RHE scale; measures Delta eta / Delta pH slope.",
            possible_outcomes=[
                "Non_Nernstian_pH_Shift",
                "Near_Nernstian_pH_Invariance"
            ],
            predictions=[
                PredictedOutcome(
                    outcome_label="Non_Nernstian_pH_Shift",
                    hypothesis_id="H1",
                    probability=0.10,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Residual uncompensated resistance and trace Fe artifacts (Suntivich 2011)"
                ),
                PredictedOutcome(
                    outcome_label="Near_Nernstian_pH_Invariance",
                    hypothesis_id="H1",
                    probability=0.90,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Concerted CPET exhibits 0 mV/pH shift on RHE scale"
                ),
                PredictedOutcome(
                    outcome_label="Non_Nernstian_pH_Shift",
                    hypothesis_id="H2",
                    probability=0.85,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Decoupled chemical deprotonation yields 40-60 mV/pH shift (Grimaud 2017)"
                ),
                PredictedOutcome(
                    outcome_label="Near_Nernstian_pH_Invariance",
                    hypothesis_id="H2",
                    probability=0.15,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Residual accounts for diffusion and buffer limits"
                ),
                PredictedOutcome(
                    outcome_label="Non_Nernstian_pH_Shift",
                    hypothesis_id="H3",
                    probability=0.40,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Surface coverage effects induce moderate non-Nernstian shift (Rong 2016)"
                ),
                PredictedOutcome(
                    outcome_label="Near_Nernstian_pH_Invariance",
                    hypothesis_id="H3",
                    probability=0.60,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Radical coupling across majority of alkaline concentration range"
                ),
            ],
            cost=1.2,
            feasibility=0.95,
            quantification_status="QUANTIFIED_BAYESIAN",
            is_feasible=True
        ),

        # EXP-OER-03: Operando EQCM Mass Loss Monitoring
        Experiment(
            id="EXP-OER-03",
            name="Operando EQCM Mass Loss Monitoring",
            description="Acoustic frequency tracking of perovskite thin films on 5 MHz AT-cut quartz resonators during chronopotentiometric OER.",
            possible_outcomes=[
                "Continuous_Electrode_Mass_Loss",
                "Stable_Electrode_Mass"
            ],
            predictions=[
                PredictedOutcome(
                    outcome_label="Continuous_Electrode_Mass_Loss",
                    hypothesis_id="H1",
                    probability=0.05,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Viscoelastic damping and acoustic noise floor"
                ),
                PredictedOutcome(
                    outcome_label="Stable_Electrode_Mass",
                    hypothesis_id="H1",
                    probability=0.95,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Stable lattice framework; minimal steady-state dissolution"
                ),
                PredictedOutcome(
                    outcome_label="Continuous_Electrode_Mass_Loss",
                    hypothesis_id="H2",
                    probability=0.82,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Oxygen vacancy creation triggers continuous cation leaching (Mefford 2016)"
                ),
                PredictedOutcome(
                    outcome_label="Stable_Electrode_Mass",
                    hypothesis_id="H2",
                    probability=0.18,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Residual accounts for rapid vacancy refilling before cation detachment"
                ),
                PredictedOutcome(
                    outcome_label="Continuous_Electrode_Mass_Loss",
                    hypothesis_id="H3",
                    probability=0.12,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Mild surface reconstruction without bulk vacancy extraction (Rong 2016)"
                ),
                PredictedOutcome(
                    outcome_label="Stable_Electrode_Mass",
                    hypothesis_id="H3",
                    probability=0.88,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Bulk lattice remains intact under surface oxyl coupling"
                ),
            ],
            cost=2.0,
            feasibility=0.88,
            quantification_status="QUANTIFIED_BAYESIAN",
            is_feasible=True
        ),

        # EXP-OER-04: In Situ Soft XAS at O K-edge
        Experiment(
            id="EXP-OER-04",
            name="In Situ Soft XAS at O K-edge",
            description="Synchrotron fluorescence yield soft X-ray absorption at O K-edge (525-545 eV) in liquid cell; monitors pre-edge ligand hole growth at 529 eV.",
            possible_outcomes=[
                "Dynamic_Pre_Edge_Intensity_Growth",
                "Static_Or_Minimal_Pre_Edge_Shift"
            ],
            predictions=[
                PredictedOutcome(
                    outcome_label="Dynamic_Pre_Edge_Intensity_Growth",
                    hypothesis_id="H1",
                    probability=0.20,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Modest metal-centered Co3+ to Co4+ pre-edge spectral overlap"
                ),
                PredictedOutcome(
                    outcome_label="Static_Or_Minimal_Pre_Edge_Shift",
                    hypothesis_id="H1",
                    probability=0.80,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Absence of significant oxygen ligand hole accumulation"
                ),
                PredictedOutcome(
                    outcome_label="Dynamic_Pre_Edge_Intensity_Growth",
                    hypothesis_id="H2",
                    probability=0.85,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Sharp ligand hole growth on O 2p states prior to OER onset (Grimaud 2017)"
                ),
                PredictedOutcome(
                    outcome_label="Static_Or_Minimal_Pre_Edge_Shift",
                    hypothesis_id="H2",
                    probability=0.15,
                    derivation_mode="LITERATURE_DERIVED_WITH_DOMAIN_NOISE",
                    basis="Residual accounts for beam-induced photoreduction artifacts"
                ),
                PredictedOutcome(
                    outcome_label="Dynamic_Pre_Edge_Intensity_Growth",
                    hypothesis_id="H3",
                    probability=0.45,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Surface oxyl radical holes diluted by bulk spectator fluorescence (Rong 2016)"
                ),
                PredictedOutcome(
                    outcome_label="Static_Or_Minimal_Pre_Edge_Shift",
                    hypothesis_id="H3",
                    probability=0.55,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Bulk absorption dominates fluorescence yield signal"
                ),
            ],
            cost=7.0,
            feasibility=0.65,
            quantification_status="QUANTIFIED_BAYESIAN",
            is_feasible=True
        ),

        # EXP-OER-05: Ex-Situ HR-TEM Morphology Inspection (Negative Control)
        Experiment(
            id="EXP-OER-05",
            name="Ex-Situ HR-TEM Morphology Inspection",
            description="Pre- and post-mortem 200 kV transmission electron microscopy of particle size and lattice fringes. Uninformative negative control.",
            possible_outcomes=[
                "Particle_Sintering_Observed",
                "No_Morphological_Sintering"
            ],
            predictions=[
                PredictedOutcome(
                    outcome_label="Particle_Sintering_Observed",
                    hypothesis_id="H1",
                    probability=0.50,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Identical likelihood across hypotheses; uninformative regarding in-situ mechanism"
                ),
                PredictedOutcome(
                    outcome_label="No_Morphological_Sintering",
                    hypothesis_id="H1",
                    probability=0.50,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Identical likelihood across hypotheses; uninformative regarding in-situ mechanism"
                ),
                PredictedOutcome(
                    outcome_label="Particle_Sintering_Observed",
                    hypothesis_id="H2",
                    probability=0.50,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Identical likelihood across hypotheses; uninformative regarding in-situ mechanism"
                ),
                PredictedOutcome(
                    outcome_label="No_Morphological_Sintering",
                    hypothesis_id="H2",
                    probability=0.50,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Identical likelihood across hypotheses; uninformative regarding in-situ mechanism"
                ),
                PredictedOutcome(
                    outcome_label="Particle_Sintering_Observed",
                    hypothesis_id="H3",
                    probability=0.50,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Identical likelihood across hypotheses; uninformative regarding in-situ mechanism"
                ),
                PredictedOutcome(
                    outcome_label="No_Morphological_Sintering",
                    hypothesis_id="H3",
                    probability=0.50,
                    derivation_mode="EXPERT_DOMAIN_ASSUMPTION",
                    basis="Identical likelihood across hypotheses; uninformative regarding in-situ mechanism"
                ),
            ],
            cost=0.8,
            feasibility=0.98,
            quantification_status="QUANTIFIED_BAYESIAN",
            is_feasible=True
        ),
    ]

    return AnalysisInput(
        scenario_name="CS-OER-002: Perovskite Oxygen Evolution Reaction Mechanism",
        scenario_type="simulation_benchmark",
        case_study_id="CS-OER-002",
        hypotheses=hypotheses,
        experiments=experiments,
        evidence=[],
        is_synthetic=True,  # Explicitly labeled as simulation benchmark
        cost_weight=0.1
    )
