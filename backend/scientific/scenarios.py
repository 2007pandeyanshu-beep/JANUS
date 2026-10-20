"""Synthetic Benchmark Scenarios for JANUS Disambiguation Testing

NOTE: ALL VALUES IN THIS MODULE ARE SYNTHETIC AND ILLUSTRATIVE.
They are engineered for mathematical verification of information-theoretic ranking
and do not represent proprietary or validated wet-lab experimental findings.
"""

from typing import List
from app.schemas.scientific import Hypothesis, Experiment, PredictedOutcome, Evidence, AnalysisInput


def get_demo_scenario() -> AnalysisInput:
    """
    Returns a mathematically transparent 3-hypothesis, 5-experiment synthetic benchmark
    based on kinase signaling pathway mechanism disambiguation.
    """
    evidence = [
        Evidence(
            id="EVD-01",
            title="Dose-Dependent Anti-Proliferative Phenotype",
            source="Synthetic In Vitro Observation (Ref: SYNTH-2026-X)",
            provenance="synthetic_fixture",
            summary="Novel small molecule 'JNS-401' exhibits nanomolar anti-proliferative response in cell culture, but the precise molecular target mechanism is unresolved.",
            confidence=0.95
        ),
        Evidence(
            id="EVD-02",
            title="Preliminary Mass Spectrometry Kinase Profiling",
            source="Synthetic Proteomics Screen (Ref: SYNTH-2026-MS)",
            provenance="synthetic_fixture",
            summary="Phosphoproteomic enrichment suggests involvement of Kinase X without ruling out direct allosteric modulation, ATP competition, or targeted degradation.",
            confidence=0.85
        )
    ]
    
    hypotheses = [
        Hypothesis(
            id="H1",
            name="Allosteric Modulation (Kinase X)",
            description="JNS-401 binds an allosteric pocket distal to the catalytic cleft, stabilizing an inactive conformation without competing against ATP.",
            prior=0.35,
            assumptions=[
                "Allosteric pocket exists and is accessible in physiological buffer",
                "Non-competitive kinetics with respect to ATP concentration"
            ],
            evidence_ids=["EVD-01", "EVD-02"],
            status="active"
        ),
        Hypothesis(
            id="H2",
            name="Competitive ATP-Site Inhibition",
            description="JNS-401 directly engages the conserved kinase ATP-binding pocket, competitively blocking substrate phosphorylation.",
            prior=0.45,
            assumptions=[
                "Molecule fits into the ATP hinge-region binding pocket",
                "Apparent IC50 will shift proportionally with increasing ATP concentrations"
            ],
            evidence_ids=["EVD-01"],
            status="active"
        ),
        Hypothesis(
            id="H3",
            name="Targeted Proteasomal Degradation",
            description="JNS-401 acts as a molecular glue or bifunctional degrader, inducing rapid ubiquitination and degradation of Kinase X.",
            prior=0.20,
            assumptions=[
                "Endogenous E3 ligase machinery is active in target tissue",
                "Total Kinase X protein abundance decreases over time"
            ],
            evidence_ids=["EVD-02"],
            status="active"
        )
    ]
    
    experiments = [
        Experiment(
            id="EXP-01",
            name="ATP Competition Assays (Kinase Kinetics)",
            description="Measure apparent enzyme inhibition (IC50) across a titration of ATP concentrations (10 uM to 1 mM).",
            possible_outcomes=["IC50_Shifts_With_ATP", "IC50_Constant_Independent_Of_ATP"],
            predictions=[
                # Under H1 (Allosteric): non-competitive, no shift
                PredictedOutcome(outcome_label="IC50_Shifts_With_ATP", hypothesis_id="H1", probability=0.05),
                PredictedOutcome(outcome_label="IC50_Constant_Independent_Of_ATP", hypothesis_id="H1", probability=0.95),
                # Under H2 (ATP-Competitive): competitive, shift observed
                PredictedOutcome(outcome_label="IC50_Shifts_With_ATP", hypothesis_id="H2", probability=0.95),
                PredictedOutcome(outcome_label="IC50_Constant_Independent_Of_ATP", hypothesis_id="H2", probability=0.05),
                # Under H3 (Degradation): cell-free recombinant assay unaffected by ATP
                PredictedOutcome(outcome_label="IC50_Shifts_With_ATP", hypothesis_id="H3", probability=0.08),
                PredictedOutcome(outcome_label="IC50_Constant_Independent_Of_ATP", hypothesis_id="H3", probability=0.92),
            ],
            cost=1.2,
            feasibility=0.95,
            assumptions=["Purified recombinant Kinase X enzyme maintains linear Michaelis-Menten kinetics"],
            is_feasible=True
        ),
        Experiment(
            id="EXP-02",
            name="Time-Course Western Blot (Protein Abundance)",
            description="Quantitative capillary immunoblotting measuring total Kinase X protein levels at 2h, 6h, 12h, and 24h post-treatment.",
            possible_outcomes=["Protein_Markedly_Depleted", "Protein_Abundance_Stable"],
            predictions=[
                # Under H1: pure inhibition, protein stable
                PredictedOutcome(outcome_label="Protein_Markedly_Depleted", hypothesis_id="H1", probability=0.02),
                PredictedOutcome(outcome_label="Protein_Abundance_Stable", hypothesis_id="H1", probability=0.98),
                # Under H2: pure inhibition, protein stable
                PredictedOutcome(outcome_label="Protein_Markedly_Depleted", hypothesis_id="H2", probability=0.02),
                PredictedOutcome(outcome_label="Protein_Abundance_Stable", hypothesis_id="H2", probability=0.98),
                # Under H3: degradation, protein depleted
                PredictedOutcome(outcome_label="Protein_Markedly_Depleted", hypothesis_id="H3", probability=0.95),
                PredictedOutcome(outcome_label="Protein_Abundance_Stable", hypothesis_id="H3", probability=0.05),
            ],
            cost=1.0,
            feasibility=0.90,
            assumptions=["Antibody is specific to Kinase X and unaffected by compound binding"],
            is_feasible=True
        ),
        Experiment(
            id="EXP-03",
            name="High-Resolution X-ray Co-Crystallography",
            description="Determine the atomic 3D structure of the Kinase X - JNS-401 co-crystal complex to identify binding locus unambiguously.",
            possible_outcomes=["Complex_Resolved_Allosteric_Site", "Complex_Resolved_ATP_Pocket", "No_Stable_Crystal_Complex"],
            predictions=[
                # Under H1
                PredictedOutcome(outcome_label="Complex_Resolved_Allosteric_Site", hypothesis_id="H1", probability=0.88),
                PredictedOutcome(outcome_label="Complex_Resolved_ATP_Pocket", hypothesis_id="H1", probability=0.02),
                PredictedOutcome(outcome_label="No_Stable_Crystal_Complex", hypothesis_id="H1", probability=0.10),
                # Under H2
                PredictedOutcome(outcome_label="Complex_Resolved_Allosteric_Site", hypothesis_id="H2", probability=0.02),
                PredictedOutcome(outcome_label="Complex_Resolved_ATP_Pocket", hypothesis_id="H2", probability=0.88),
                PredictedOutcome(outcome_label="No_Stable_Crystal_Complex", hypothesis_id="H2", probability=0.10),
                # Under H3
                PredictedOutcome(outcome_label="Complex_Resolved_Allosteric_Site", hypothesis_id="H3", probability=0.05),
                PredictedOutcome(outcome_label="Complex_Resolved_ATP_Pocket", hypothesis_id="H3", probability=0.05),
                PredictedOutcome(outcome_label="No_Stable_Crystal_Complex", hypothesis_id="H3", probability=0.90),
            ],
            cost=7.5,
            feasibility=0.60,
            assumptions=["Diffraction-grade crystals can be obtained with JNS-401 soak or co-crystallization"],
            is_feasible=True
        ),
        Experiment(
            id="EXP-04",
            name="Generic Single-Dose Cell Viability Screen (Control)",
            description="Standard 72-hour resazurin cell viability endpoint at single 1 uM compound concentration.",
            possible_outcomes=["Growth_Inhibited", "Growth_Unchanged"],
            predictions=[
                # All hypotheses produce identical downstream phenotypic outcomes
                PredictedOutcome(outcome_label="Growth_Inhibited", hypothesis_id="H1", probability=0.85),
                PredictedOutcome(outcome_label="Growth_Unchanged", hypothesis_id="H1", probability=0.15),
                PredictedOutcome(outcome_label="Growth_Inhibited", hypothesis_id="H2", probability=0.85),
                PredictedOutcome(outcome_label="Growth_Unchanged", hypothesis_id="H2", probability=0.15),
                PredictedOutcome(outcome_label="Growth_Inhibited", hypothesis_id="H3", probability=0.85),
                PredictedOutcome(outcome_label="Growth_Unchanged", hypothesis_id="H3", probability=0.15),
            ],
            cost=0.5,
            feasibility=1.0,
            assumptions=["Linear correlation between metabolic activity and viable cell count"],
            is_feasible=True
        ),
        Experiment(
            id="EXP-05",
            name="Non-Human Primate In Vivo Pharmacokinetics (Infeasible)",
            description="Large-animal systemic clearance and toxicology cohort study.",
            possible_outcomes=["Tolerated", "Toxic"],
            predictions=[
                PredictedOutcome(outcome_label="Tolerated", hypothesis_id="H1", probability=0.70),
                PredictedOutcome(outcome_label="Toxic", hypothesis_id="H1", probability=0.30),
                PredictedOutcome(outcome_label="Tolerated", hypothesis_id="H2", probability=0.70),
                PredictedOutcome(outcome_label="Toxic", hypothesis_id="H2", probability=0.30),
                PredictedOutcome(outcome_label="Tolerated", hypothesis_id="H3", probability=0.70),
                PredictedOutcome(outcome_label="Toxic", hypothesis_id="H3", probability=0.30),
            ],
            cost=50.0,
            feasibility=0.0,
            assumptions=["Approved IACUC protocol and primate facility availability"],
            is_feasible=False
        )
    ]
    
    return AnalysisInput(
        scenario_name="Kinase Signaling Pathway Disambiguation (Synthetic Benchmark)",
        hypotheses=hypotheses,
        experiments=experiments,
        evidence=evidence,
        is_synthetic=True,
        cost_weight=0.1
    )
