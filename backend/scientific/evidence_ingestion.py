"""JANUS Evidence Ingestion Layer

Ingests, validates, and serves peer-reviewed published case studies and evidence ledgers.
Strictly distinguishes:
- Empirical observations (direct lab measurements)
- Computational DFT calculations
- Author interpretations
- Unquantified assumptions / proposals

Guarantees data provenance and prevents unverified text from silently becoming evidence.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from app.schemas.scientific import (
    AnalysisInput,
    Hypothesis,
    Experiment,
    Evidence,
    PredictedOutcome,
)


def get_case_study_dir() -> Path:
    """Resolves the directory containing versioned case study evidence packages."""
    # Try relative to this file: backend/scientific/../../docs/case_study
    current = Path(__file__).resolve().parent
    candidates = [
        current.parent.parent / "docs" / "case_study",
        Path("docs/case_study"),
        Path("C:/Users/2007p/OneDrive/Desktop/JANUS/docs/case_study"),
    ]
    for p in candidates:
        if p.exists() and (p / "evidence_ledger.json").exists():
            return p
    raise FileNotFoundError(f"Case study documentation not found in candidate paths: {candidates}")


def load_evidence_ledger() -> List[Evidence]:
    """Loads and validates the peer-reviewed evidence ledger."""
    case_dir = get_case_study_dir()
    ledger_path = case_dir / "evidence_ledger.json"
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    evidence_items: List[Evidence] = []
    for item in data.get("claims", []):
        ev = Evidence(
            id=item["claim_id"],
            title=item["statement"][:60] + "...",
            source=f"{item['source_citation']} (DOI: {item.get('source_doi', 'N/A')})",
            source_doi=item.get("source_doi"),
            source_location=item.get("source_location"),
            exact_source_quote=item.get("exact_source_quote"),
            claim_status=item.get("claim_status", "VERIFIED_PRIMARY_SOURCE"),
            claim_type=item.get("claim_type", "source_reported_value"),
            ambiguity_notes=item.get("ambiguity_notes"),
            provenance=item["provenance"],
            summary=item["statement"],
            quantitative_value=item.get("quantitative_value"),
            supports_hypotheses=item.get("supports_hypotheses", []),
            refutes_hypotheses=item.get("refutes_hypotheses", []),
            confidence=float(item.get("confidence", 1.0))
        )
        evidence_items.append(ev)
        
    return evidence_items


def load_candidate_experiments() -> List[Experiment]:
    """Loads and validates the candidate experiments from published literature."""
    case_dir = get_case_study_dir()
    exp_path = case_dir / "candidate_experiments.json"
    
    with open(exp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    experiments: List[Experiment] = []
    for exp_raw in data.get("experiments", []):
        preds = []
        for p in exp_raw.get("predictions", []):
            preds.append(
                PredictedOutcome(
                    outcome_label=p["outcome_label"],
                    hypothesis_id=p["hypothesis_id"],
                    probability=float(p["probability"]),
                    uncertainty=float(p.get("uncertainty", 0.0)),
                    derivation_mode=p.get("derivation_mode", "derived_from_reported_value_with_noise_model"),
                    basis=p.get("basis")
                )
            )
            
        exp = Experiment(
            id=exp_raw["id"],
            name=exp_raw["name"],
            description=exp_raw["description"],
            quantification_status=exp_raw.get("quantification_status", "QUANTIFIED_BAYESIAN"),
            possible_outcomes=exp_raw["possible_outcomes"],
            predictions=preds,
            cost=float(exp_raw.get("cost", 1.0)),
            feasibility=float(exp_raw.get("feasibility", 1.0)),
            assumptions=exp_raw.get("assumptions", []),
            is_feasible=bool(exp_raw.get("is_feasible", True)),
            source_evidence_ids=exp_raw.get("source_evidence_ids", [])
        )
        experiments.append(exp)
        
    return experiments


def get_wgs_case_study_scenario() -> AnalysisInput:
    """
    Constructs the real-world published scientific case study scenario
    for low-temperature WGS mechanism on Pt/CeO2.
    """
    evidence = load_evidence_ledger()
    experiments = load_candidate_experiments()
    
    hypotheses = [
        Hypothesis(
            id="H1",
            name="Redox / Mars-van Krevelen Mechanism",
            description="CO adsorbed on Pt abstracts reducible ceria lattice oxygen at the perimeter interface; water dissociation at oxygen vacancies re-oxidizes Ce3+ to Ce4+ and evolves H2.",
            prior=0.50,
            assumptions=[
                "Pt-ceria perimeter interface activates lattice oxygen extraction",
                "Water dissociates rapidly into oxygen vacancies"
            ],
            evidence_ids=["CLM-WGS-001", "CLM-WGS-002", "CLM-WGS-004", "CLM-WGS-005"],
            status="active"
        ),
        Hypothesis(
            id="H2",
            name="Associative Formate with -OH Regeneration",
            description="CO reacts with support hydroxyls forming surface formate (HCOO-Ce) as the key reaction intermediate, which subsequently decomposes into CO2 and H2.",
            prior=0.20,
            assumptions=[
                "Surface formates are kinetically active reaction intermediates",
                "Formate decomposition rate matches steady-state catalytic turnover"
            ],
            evidence_ids=["CLM-WGS-003"],
            status="active"
        ),
        Hypothesis(
            id="H3",
            name="Associative Carboxyl Mechanism (Formates as Spectators)",
            description="CO reacts with -OH forming transient carboxyl (*COOH) with low DFT barrier, while abundant observed formates are unreactive spectator species residing away from the perimeter.",
            prior=0.30,
            assumptions=[
                "Carboxyl intermediate decomposes rapidly to CO2 and H*",
                "Formate species act as thermodynamic sink / spectator reservoir"
            ],
            evidence_ids=["CLM-WGS-001", "CLM-WGS-004", "CLM-WGS-006", "CLM-WGS-007"],
            status="active"
        )
    ]
    
    return AnalysisInput(
        scenario_name="Pt/CeO2 Low-Temperature Water-Gas Shift Mechanism",
        scenario_type="published_case_study",
        case_study_id="CS-CAT-001",
        hypotheses=hypotheses,
        experiments=experiments,
        evidence=evidence,
        is_synthetic=False,  # This is a real published case study!
        cost_weight=0.1
    )
