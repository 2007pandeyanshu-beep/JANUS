"""JANUS Independent Hypothesis Analyst uAgent (Phase 5).

Provides an autonomous, independently running Fetch.ai uAgent dedicated to
evidence-grounded hypothesis formulation, mechanistic evidence linking,
epistemic status assignment, and probability simplex verification.

Architecture:
- Native Fetch.ai uAgents Protocol (`janus_scientific_hypothesis`, version 1.0.0)
- Independent agent identity and distinct cryptographic address (Port 8011)
- Explicit evidence linking (supporting, contradicting, indirect) with mechanistic rationales
- Transparent separation of empirical findings from physical model assumptions
- Rigorous preservation of probability simplex axioms (sum P(H_k) == 1.0)
- Zero duplication of the Bayesian Experimental Design (BED) engine or Auditor verification
"""

import sys
import os
import math
import re
from pathlib import Path

# Prevent local backend/agents directory from shadowing standard library 'types' during direct script execution
_script_dir = os.path.dirname(os.path.abspath(__file__))
if sys.path and sys.path[0] == _script_dir:
    sys.path.pop(0)

_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from uagents import Agent, Context, Protocol
from app.schemas.hypothesis_analyst import (
    HypothesisEvidenceLink,
    HypothesisEvaluationItem,
    HypothesisAnalysisRequest,
    HypothesisAnalysisResponse,
)


scientific_hypothesis_proto = Protocol(
    name="janus_scientific_hypothesis",
    version="1.0.0"
)


# ==============================================================================
# Domain Knowledge Bases for Mechanistic Hypotheses & Evidence Relationships
# ==============================================================================

_WGS_HYPOTHESIS_TEMPLATES = [
    {
        "id": "H1",
        "name": "Redox / Mars-van Krevelen Mechanism",
        "description": (
            "CO adsorbed on Pt abstracts reducible ceria lattice oxygen at the perimeter interface; "
            "water dissociation at oxygen vacancies re-oxidizes Ce3+ to Ce4+ and evolves H2."
        ),
        "default_prior": 0.50,
        "assumptions": [
            "Pt-ceria perimeter interface activates lattice oxygen extraction",
            "Water dissociates rapidly into oxygen vacancies",
            "Lattice oxygen diffusion from ceria subsurface replenishes active interfacial sites",
        ],
        "mathematical_formulation": "r_CO2 = k_red * theta_CO * [O_lattice]; r_H2 = k_ox * P_H2O * [V_O]",
        "uncertainty_explanation": (
            "Moderate uncertainty regarding the exact spatial extent of the perimeter boundary zone "
            "and temperature-dependent vacancy migration kinetics in nano-crystallite ceria."
        ),
    },
    {
        "id": "H2",
        "name": "Associative Formate Mechanism",
        "description": (
            "CO reacts with support hydroxyls forming surface formate (HCOO-Ce) as the key reaction "
            "intermediate, which subsequently decomposes into CO2 and H2."
        ),
        "default_prior": 0.20,
        "assumptions": [
            "Surface formates are kinetically active reaction intermediates",
            "Formate decomposition rate matches steady-state catalytic turnover",
            "C-H bond cleavage in bidentate formate controls overall reaction rate",
        ],
        "mathematical_formulation": "r_CO2 = k_decomp * [HCOO-Ce]",
        "uncertainty_explanation": (
            "Substantial epistemic conflict: high spectroscopic visibility in DRIFTS contrasts with "
            "SSITKA transient kinetics proving exchange rates are <15% of turnover frequency."
        ),
    },
    {
        "id": "H3",
        "name": "Associative Carboxyl Mechanism (Formates as Spectators)",
        "description": (
            "CO reacts with -OH forming transient carboxyl (*COOH) with low DFT barrier, "
            "while abundant observed formates are unreactive spectator species residing away from the perimeter."
        ),
        "default_prior": 0.30,
        "assumptions": [
            "Carboxyl intermediate (*COOH) decomposes rapidly to CO2 and H*",
            "Formate species act as thermodynamic sink / spectator reservoir on ceria terraces",
            "Hydroxyl transfer from ceria to interfacial Pt occurs with low activation barrier",
        ],
        "mathematical_formulation": "r_CO2 = k_carb * [CO*] * [OH*] / (1 + K_ads * [HCOO*])",
        "uncertainty_explanation": (
            "Carboxyl intermediates have very short vibrational lifetimes (<10 ps) making direct "
            "spectroscopic observation challenging against high background spectator formate absorption."
        ),
    },
]

_OER_HYPOTHESIS_TEMPLATES = [
    {
        "id": "H1",
        "name": "Adsorbate Evolution Mechanism (AEM)",
        "description": (
            "Conventional concerted four-step proton-coupled electron transfer (PCET) on localized transition "
            "metal active sites (* -> *OH -> *O -> *OOH -> O2) without lattice oxygen participation."
        ),
        "default_prior": 0.35,
        "assumptions": [
            "Metal-oxygen scaling relations strictly couple *OH and *OOH adsorption energies (Delta G ~ 3.2 eV)",
            "All oxygen atoms in evolved O2 originate exclusively from electrolyte water",
            "Catalyst surface remains crystalline and stoichiometric under operational bias",
        ],
        "mathematical_formulation": "eta_theor = max(Delta G_1, Delta G_2, Delta G_3, Delta G_4) / e - 1.23 V",
        "uncertainty_explanation": (
            "Electrochemical scaling relations impose a theoretical overpotential limit of ~0.37 V, "
            "which cannot explain anomalously low overpotentials observed on dynamic amorphized surfaces."
        ),
    },
    {
        "id": "H2",
        "name": "Lattice Oxygen Mechanism (LOM)",
        "description": (
            "Direct participation of lattice oxygen from the near-surface oxide framework in O-O bond "
            "formation, driven by high metal-oxygen covalency and O 2p band positioning near the Fermi level."
        ),
        "default_prior": 0.45,
        "assumptions": [
            "High metal-oxygen covalency places O 2p-band center close to Fermi level under anodic potential",
            "Direct participation of lattice oxygen creates surface oxygen vacancies",
            "Continuous oxygen vacancy generation induces surface reconstruction and metal dissolution",
        ],
        "mathematical_formulation": "r_O2 = k_LOM * [O_lattice] * [O_adsorbed]; accompanied by J_dissolution",
        "uncertainty_explanation": (
            "Coupling between high activity via LOM and accelerated catalyst degradation/dissolution "
            "requires careful quantification of lattice exchange yields under steady-state conditions."
        ),
    },
    {
        "id": "H3",
        "name": "Oxide Path / Surface Radical Coupling (OPM)",
        "description": (
            "Non-concerted direct homolytic radical coupling between adjacent surface oxyl species "
            "(*O_radical + *O_radical -> O2) without extracting bulk lattice oxygen into gas phase."
        ),
        "default_prior": 0.20,
        "assumptions": [
            "Adjacent surface oxyl radicals form under high anodic polarization",
            "Direct radical-radical coupling bypasses *OOH scaling bottleneck",
            "Surface framework remains stable without continuous bulk vacancy extraction",
        ],
        "mathematical_formulation": "r_O2 = k_OPM * [O_rad]^2",
        "uncertainty_explanation": (
            "Requires specific high-density dual active site motifs; sensitive to local coordination geometry "
            "and electric double-layer field gradients."
        ),
    },
]

# Synthetic Kinase Benchmark Fixtures (Strictly for SYN-001, DEMO, KINASE benchmarks)
_SYNTHETIC_KINASE_TEMPLATES = [
    {
        "id": "H1",
        "name": "Targeted Allosteric Mechanism",
        "description": "Ligand binding at allosteric regulatory domain induces conformational inactivation.",
        "default_prior": 0.35,
        "assumptions": ["Allosteric site binding induces long-range structural stabilization"],
        "mathematical_formulation": "v = V_max * [S] / (K_m * (1 + [I]/K_i) + [S])",
        "uncertainty_explanation": "Allosteric communication pathways exhibit conformational heterogeneity.",
    },
    {
        "id": "H2",
        "name": "Competitive Catalytic Cleft Binding",
        "description": "Direct steric and electrostatic competition at primary catalytic active cleft.",
        "default_prior": 0.45,
        "assumptions": ["Inhibitor directly occludes substrate access to catalytic residues"],
        "mathematical_formulation": "v = V_max * [S] / (K_m + [S] * (1 + [I]/K_i))",
        "uncertainty_explanation": "High affinity can be confounded by rapid off-rate kinetics in cellular milieus.",
    },
    {
        "id": "H3",
        "name": "Targeted Degradation / Ternary Complex Formation",
        "description": "Bifunctional recruiter induces ubiquitination and proteasomal degradation.",
        "default_prior": 0.20,
        "assumptions": ["Stable ternary complex formation is necessary and rate-limiting"],
        "mathematical_formulation": "Rate_degrad = k_cat * [TernaryComplex]",
        "uncertainty_explanation": "Hook effect at high concentrations reduces effective ternary complex concentration.",
    },
]

# Backwards compatibility alias
_GENERIC_HYPOTHESIS_TEMPLATES = _SYNTHETIC_KINASE_TEMPLATES


def _matches_hypothesis_reference(hyp_id: str, text: str) -> bool:
    """
    Checks if text contains an explicit reference to a specific hypothesis ID
    using word-boundary regex to prevent false-positive substring matching
    (e.g., prevents matching 'which1' for 'H1', or 'H2O'/'H2 gas' for 'H2').
    """
    hid = hyp_id.lower().strip()
    num = hid.lstrip("h")
    # Match "hypothesis 1", "hyp 1", "h-1"
    explicit_patterns = [
        rf"\bhypothesis\s*{re.escape(num)}\b",
        rf"\bhyp\s*{re.escape(num)}\b",
        rf"\bh-{re.escape(num)}\b",
    ]
    # For H2, in chemistry domains H2 commonly represents molecular hydrogen gas,
    # so we require explicit hypothesis syntax rather than matching raw isolated 'h2'.
    if hid != "h2":
        explicit_patterns.append(rf"\b{re.escape(hid)}\b")

    for pat in explicit_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def _build_evidence_link(
    hyp_id: str,
    ev_item: Dict[str, Any],
    case_study_id: str,
) -> Optional[HypothesisEvidenceLink]:
    """
    Evaluates epistemic relationship between a specific retrieved evidence item and a hypothesis.
    Returns HypothesisEvidenceLink or None if no direct or indirect relation exists.
    """
    ev_id = str(ev_item.get("id") or ev_item.get("claim_id") or "").strip()
    if not ev_id:
        return None

    summary = (ev_item.get("summary") or ev_item.get("statement") or "").lower()
    title = (ev_item.get("title") or "").lower()

    # Safe confidence parsing and bounding to [0.0, 1.0]
    raw_conf = ev_item.get("confidence", 0.9)
    try:
        raw_confidence = float(raw_conf)
        if math.isnan(raw_confidence) or math.isinf(raw_confidence):
            raw_confidence = 0.5
        else:
            raw_confidence = max(0.0, min(1.0, raw_confidence))
    except (ValueError, TypeError):
        raw_confidence = 0.5

    doi_status = str(ev_item.get("doi_verification_status", "BIBLIOGRAPHIC_VERIFIED_ONLINE") or "")

    # Weight confidence based on bibliographic verification state.
    # Note: Bibliographic uncertainty dampens confidence weight, but does not refute empirical findings.
    if doi_status == "METADATA_MISMATCH":
        confidence = round(max(0.2, raw_confidence * 0.7), 2)
    elif doi_status == "DOI_NOT_FOUND":
        confidence = round(max(0.1, raw_confidence * 0.6), 2)
    else:
        confidence = round(raw_confidence, 2)

    supports_list = [str(x).upper() for x in ev_item.get("supports_hypotheses", [])]
    refutes_list = [str(x).upper() for x in ev_item.get("refutes_hypotheses", [])]
    target_id = hyp_id.upper()

    # Case 1: Explicitly tagged in evidence item metadata
    if target_id in supports_list and target_id in refutes_list:
        # Conflicting signals present on same evidence record: do not discard!
        return HypothesisEvidenceLink(
            evidence_id=ev_id,
            relation_type="INDIRECT",
            rationale=(
                f"Evidence {ev_id} contains conflicting tags for {hyp_id} (both supporting and refuting). "
                f"Preserved as ambiguous/indirect evidence requiring manual experimental clarification."
            ),
            confidence_weight=round(confidence * 0.5, 2),
        )
    if target_id in supports_list:
        return HypothesisEvidenceLink(
            evidence_id=ev_id,
            relation_type="SUPPORTING",
            rationale=f"Evidence {ev_id} directly confirms mechanistic predictions of {hyp_id} ({summary[:100]}...).",
            confidence_weight=confidence,
        )
    if target_id in refutes_list:
        return HypothesisEvidenceLink(
            evidence_id=ev_id,
            relation_type="CONTRADICTING",
            rationale=f"Evidence {ev_id} empirically contradicts key assumptions of {hyp_id} ({summary[:100]}...).",
            confidence_weight=confidence,
        )

    # Case 2: WGS Domain-specific semantic matching
    if case_study_id in ("CS-CAT-001", "WGS"):
        # Formate spectator evidence (CLM-WGS-001, CLM-WGS-004, Meunier 2007)
        if "formate" in summary and ("slow" in summary or "spectator" in summary or "0.14" in summary or "tof" in summary):
            if hyp_id == "H2":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="CONTRADICTING",
                    rationale="Formate exchange rate is <15% of turnover frequency, contradicting formate as active catalytic intermediate.",
                    confidence_weight=confidence,
                )
            elif hyp_id in ("H1", "H3"):
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="SUPPORTING",
                    rationale="Demonstration that formates are spectators rules out the associative formate pathway, indirectly supporting redox/carboxyl routes.",
                    confidence_weight=confidence,
                )

        # Lattice oxygen / redox evidence (CLM-WGS-002, CLM-WGS-005, Ce3+ reduction)
        if "lattice oxygen" in summary or "ce3+" in summary or "c16o2" in summary or "redox" in summary:
            if hyp_id == "H1":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="SUPPORTING",
                    rationale="Transient isotopic pulsing and Ce L3-edge XANES demonstrate direct lattice oxygen transfer and reversible Ce3+/Ce4+ redox cycling.",
                    confidence_weight=confidence,
                )
            elif hyp_id == "H2":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="CONTRADICTING",
                    rationale="Dominance of lattice oxygen abstraction in initial transient product contradicts direct hydroxyl-formate decomposition.",
                    confidence_weight=confidence,
                )

        # Carboxyl DFT / barrier evidence (CLM-WGS-006, 0.58 eV)
        if "carboxyl" in summary or "0.58 ev" in summary or "dft" in summary:
            if hyp_id == "H3":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="SUPPORTING",
                    rationale="DFT+U calculations identify a low 0.58 eV barrier for *COOH decomposition, supporting viable associative carboxyl pathway.",
                    confidence_weight=confidence,
                )
            elif hyp_id == "H2":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="CONTRADICTING",
                    rationale="High formate decomposition barrier (>1.4 eV) in computational models disfavors unassisted formate pathway.",
                    confidence_weight=confidence,
                )

        # Kinetic isotope effect (CLM-WGS-004, KIE 1.15 - 1.30)
        if "kinetic isotope effect" in summary or "kie" in summary or "1.22" in summary:
            if hyp_id in ("H1", "H3"):
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="SUPPORTING",
                    rationale="Low KIE (1.15-1.30) indicates C-H cleavage is not rate-determining, consistent with redox or carboxyl mechanisms.",
                    confidence_weight=confidence,
                )
            elif hyp_id == "H2":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="CONTRADICTING",
                    rationale="Expected primary KIE for formate C-H cleavage is >= 1.8; observed KIE of 1.22 refutes formate rate-determining step.",
                    confidence_weight=confidence,
                )

    # Case 3: OER Domain-specific semantic matching
    elif case_study_id in ("CS-OER-002", "OER"):
        if "dems" in summary or "lattice" in summary or "18o" in summary:
            if hyp_id == "H2":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="SUPPORTING",
                    rationale="Operando DEMS demonstrates significant lattice 18O integration into evolved O2, directly verifying the Lattice Oxygen Mechanism.",
                    confidence_weight=confidence,
                )
            elif hyp_id == "H1":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="CONTRADICTING",
                    rationale="Conventional AEM predicts 100% electrolyte oxygen in product; lattice oxygen evolution contradicts pure AEM.",
                    confidence_weight=confidence,
                )
        if "scaling" in summary or "dft" in summary or "3.2 ev" in summary:
            if hyp_id == "H1":
                return HypothesisEvidenceLink(
                    evidence_id=ev_id,
                    relation_type="SUPPORTING",
                    rationale="DFT calculations confirm standard adsorbate scaling relations (Delta G_OOH - Delta G_OH ~ 3.2 eV) characteristic of AEM.",
                    confidence_weight=confidence,
                )

    # Default fallback: check if explicit hypothesis reference exists in text
    if _matches_hypothesis_reference(hyp_id, summary):
        return HypothesisEvidenceLink(
            evidence_id=ev_id,
            relation_type="INDIRECT",
            rationale=f"Evidence {ev_id} explicitly references {hyp_id} mechanisms or associated intermediates.",
            confidence_weight=round(confidence * 0.7, 2),
        )

    return None


def perform_hypothesis_analysis(
    request: HypothesisAnalysisRequest,
    agent_address: str,
) -> HypothesisAnalysisResponse:
    """
    Executes evidence-grounded hypothesis evaluation and formulation over retrieved evidence.
    Ensures probability simplex normalization and rigorous distinction between evidence vs assumptions.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    case_study = request.case_study_id or "CS-CAT-001"
    evidence_items = request.retrieved_evidence or []
    warnings: List[str] = []

    # 1. Select appropriate template catalog or reject unsupported domains
    if case_study in ("CS-CAT-001", "WGS"):
        templates = _WGS_HYPOTHESIS_TEMPLATES
        domain_name = "Pt/CeO2 Low-Temperature Water-Gas Shift"
    elif case_study in ("CS-OER-002", "OER"):
        templates = _OER_HYPOTHESIS_TEMPLATES
        domain_name = "Perovskite / Transition Metal Oxide OER"
    elif case_study in ("SYN-001", "DEMO", "KINASE"):
        templates = _SYNTHETIC_KINASE_TEMPLATES
        domain_name = f"Synthetic Benchmark Fixtures ({case_study})"
    else:
        # Unsupported domain: reject ungrounded hypothesis generation
        return HypothesisAnalysisResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="INSUFFICIENT_EVIDENCE",
            agent_address=agent_address,
            timestamp=now_iso,
            hypotheses=[],
            simplex_sum=0.0,
            is_simplex_valid=False,
            unresolved_questions=[],
            warnings=[
                f"Unsupported scientific domain '{case_study}'. JANUS only contains verified mechanistic "
                f"templates for WGS ('CS-CAT-001'), OER ('CS-OER-002'), and synthetic benchmarks "
                f"('SYN-001', 'DEMO', 'KINASE'). Ungrounded hypotheses will not be fabricated."
            ],
            summary=(
                f"UNSUPPORTED_DOMAIN: Scientific domain '{case_study}' has no verified hypothesis templates "
                f"in JANUS knowledge base. Hypothesis formulation aborted to prevent scientific hallucinations."
            ),
        )

    # 2. Check for empty evidence
    if not evidence_items:
        warnings.append("No retrieved evidence items were provided. Hypotheses evaluated solely against baseline prior definitions.")
        status = "INSUFFICIENT_EVIDENCE"
    else:
        status = "ANALYSIS_COMPLETED"

    # 3. Determine prior distribution with strict mathematical validation
    assigned_priors: Dict[str, float] = {}
    if request.existing_priors is not None:
        invalid_reason = None
        for k, v in request.existing_priors.items():
            if not isinstance(v, (int, float)):
                invalid_reason = f"Prior for {k} is non-numeric: {v}"
                break
            if math.isnan(v) or math.isinf(v):
                invalid_reason = f"Prior for {k} is non-finite (NaN or Inf)"
                break
            if v < 0.0:
                invalid_reason = f"Prior for {k} is negative ({v})"
                break

        sum_priors = sum(request.existing_priors.values()) if not invalid_reason else 0.0
        if not invalid_reason and sum_priors <= 1e-9:
            invalid_reason = f"Total sum of priors is zero or non-positive ({sum_priors})"

        if invalid_reason:
            warnings.append(
                f"Invalid existing_priors rejected: {invalid_reason}. "
                f"Analysis aborted to preserve mathematical simplex integrity."
            )
            return HypothesisAnalysisResponse(
                correlation_id=request.correlation_id,
                investigation_id=request.investigation_id,
                status="ANALYSIS_UNAVAILABLE",
                agent_address=agent_address,
                timestamp=now_iso,
                hypotheses=[],
                simplex_sum=0.0,
                is_simplex_valid=False,
                unresolved_questions=[],
                warnings=warnings,
                summary=f"ANALYSIS_UNAVAILABLE: Prior distribution rejected due to mathematical axiom violation: {invalid_reason}.",
            )

        if abs(sum_priors - 1.0) < 1e-4:
            assigned_priors = dict(request.existing_priors)
        else:
            warnings.append(f"Provided existing_priors sum to {sum_priors:.4f} != 1.0; re-normalizing onto simplex.")
            assigned_priors = {k: v / sum_priors for k, v in request.existing_priors.items()}
    else:
        assigned_priors = {t["id"]: t["default_prior"] for t in templates}

    # 4. Evaluate each hypothesis against retrieved evidence
    evaluated_hypotheses: List[HypothesisEvaluationItem] = []

    for tmpl in templates:
        hyp_id = tmpl["id"]
        prior_val = assigned_priors.get(hyp_id, tmpl["default_prior"])

        links: List[HypothesisEvidenceLink] = []
        seen_link_ids = set()
        supporting_ids: List[str] = []
        contradicting_ids: List[str] = []

        for ev in evidence_items:
            link = _build_evidence_link(hyp_id, ev, case_study)
            if link and link.evidence_id not in seen_link_ids:
                seen_link_ids.add(link.evidence_id)
                links.append(link)
                if link.relation_type == "SUPPORTING":
                    supporting_ids.append(link.evidence_id)
                elif link.relation_type == "CONTRADICTING":
                    contradicting_ids.append(link.evidence_id)

        # Deduplicate IDs
        supporting_ids = sorted(list(set(supporting_ids)))
        contradicting_ids = sorted(list(set(contradicting_ids)))

        # Determine epistemic status
        if not evidence_items:
            epistemic_status = "INSUFFICIENT_EVIDENCE"
        elif len(contradicting_ids) >= 2 or (len(contradicting_ids) >= 1 and len(supporting_ids) == 0):
            epistemic_status = "STRONGLY_CONTRADICTED"
        elif len(supporting_ids) >= 1 and len(contradicting_ids) >= 1:
            epistemic_status = "VIABLE_CANDIDATE"  # Contested
            warnings.append(
                f"Hypothesis {hyp_id} is contested: has {len(supporting_ids)} supporting and "
                f"{len(contradicting_ids)} contradicting evidence links."
            )
        elif len(supporting_ids) >= 1:
            epistemic_status = "VIABLE_CANDIDATE"
        else:
            epistemic_status = "INSUFFICIENT_EVIDENCE"

        item = HypothesisEvaluationItem(
            id=hyp_id,
            name=tmpl["name"],
            description=tmpl["description"],
            prior=prior_val,
            evidence_links=links,
            supporting_evidence_ids=supporting_ids,
            contradicting_evidence_ids=contradicting_ids,
            epistemic_status=epistemic_status,
            uncertainty_explanation=tmpl["uncertainty_explanation"],
            assumptions=tmpl["assumptions"],
            mathematical_formulation=tmpl.get("mathematical_formulation"),
        )
        evaluated_hypotheses.append(item)

    # 5. Rigorous Simplex Validation
    simplex_sum = sum(h.prior for h in evaluated_hypotheses)
    is_simplex_valid = abs(simplex_sum - 1.0) < 1e-4

    if not is_simplex_valid:
        warnings.append(f"Simplex normalization discrepancy: sum={simplex_sum:.6f}. Normalizing to preserve Bayesian invariants.")
        for h in evaluated_hypotheses:
            h.prior = round(h.prior / simplex_sum, 6)
        simplex_sum = sum(h.prior for h in evaluated_hypotheses)
        is_simplex_valid = abs(simplex_sum - 1.0) < 1e-4

    # 6. Formulate Unresolved Mechanistic Questions
    if case_study in ("CS-CAT-001", "WGS"):
        unresolved_questions = [
            "What is the quantitative branching ratio between perimeter redox vacancy oxygen transfer vs interfacial carboxyl decomposition under high-pressure (P > 10 bar) steady-state operation?",
            "Can operando isotope transient kinetics distinguish very short-lived carboxyl (*COOH) intermediates from background spectator formate absorption at temperatures >220°C?",
            "What is the exact rate of lattice oxygen replenishment from ceria subsurface bulk to interfacial perimeter sites?",
        ]
    elif case_study in ("CS-OER-002", "OER"):
        unresolved_questions = [
            "Does the Lattice Oxygen Mechanism (LOM) inevitably trigger irreversible surface reconstruction and transition metal dissolution during extended cycling?",
            "Can local structural tailoring decouple lattice oxygen activation from cation vacancy destabilization?",
        ]
    else:
        unresolved_questions = [
            "Which mechanistic pathway dominates across dynamic operational parameter ranges?",
            "What critical diagnostic experiment offers maximum Bayesian Information Gain to distinguish these candidates?",
        ]

    # 7. Formulate Human-Readable Summary
    summary_lines = [
        f"Hypothesis Analyst Agent evaluated {len(evaluated_hypotheses)} competing mechanistic hypotheses for {domain_name}.",
        f"Simplex Validation: Sum P(H_k) = {simplex_sum:.4f} (Valid: {is_simplex_valid}).",
    ]
    for h in evaluated_hypotheses:
        sup_str = ", ".join(h.supporting_evidence_ids) or "None"
        contra_str = ", ".join(h.contradicting_evidence_ids) or "None"
        summary_lines.append(
            f"- {h.id} ({h.name}, P={h.prior:.2f}): Status [{h.epistemic_status}]. "
            f"Supporting: [{sup_str}] | Contradicting: [{contra_str}]."
        )
    if warnings:
        summary_lines.append(f"Warnings: {'; '.join(warnings)}")

    execution_summary = "\n".join(summary_lines)

    return HypothesisAnalysisResponse(
        correlation_id=request.correlation_id,
        investigation_id=request.investigation_id,
        status=status,
        agent_address=agent_address,
        timestamp=now_iso,
        hypotheses=evaluated_hypotheses,
        simplex_sum=round(simplex_sum, 6),
        is_simplex_valid=is_simplex_valid,
        unresolved_questions=unresolved_questions,
        warnings=warnings,
        summary=execution_summary,
    )


# ==============================================================================
# Protocol Handler
# ==============================================================================

@scientific_hypothesis_proto.on_message(
    model=HypothesisAnalysisRequest,
    replies={HypothesisAnalysisResponse}
)
async def handle_hypothesis_request(ctx: Context, sender: str, msg: HypothesisAnalysisRequest):
    """
    Handles incoming hypothesis analysis requests from the primary JANUS Coordinator.
    """
    ctx.logger.info(
        f"Received HypothesisAnalysisRequest from {sender} "
        f"[Investigation: {msg.investigation_id}, Case Study: {msg.case_study_id}, "
        f"Evidence Items: {len(msg.retrieved_evidence)}]"
    )

    response = perform_hypothesis_analysis(msg, agent_address=ctx.agent.address)

    ctx.logger.info(
        f"Hypothesis analysis complete: status={response.status}, "
        f"hypotheses={len(response.hypotheses)}, simplex_sum={response.simplex_sum}. "
        f"Replying to {sender}..."
    )

    await ctx.send(sender, response)


# ==============================================================================
# Agent Factory & Standalone Runner
# ==============================================================================

def create_hypothesis_analyst_uagent(
    name: str = "janus_hypothesis_analyst",
    seed: Optional[str] = None,
    port: int = 8011,
    endpoint: Optional[List[str]] = None,
    use_mailbox: Optional[bool] = None,
    agentverse_url: Optional[str] = None,
) -> Agent:
    """
    Constructs and returns the configured JANUS Independent Hypothesis Analyst uAgent.
    """
    effective_seed = seed or os.getenv("JANUS_HYPOTHESIS_ANALYST_SEED")
    raw_env_mailbox = os.getenv("JANUS_HYPOTHESIS_ANALYST_USE_MAILBOX")

    if use_mailbox is not None:
        is_mailbox = bool(use_mailbox)
    elif raw_env_mailbox is not None and raw_env_mailbox.strip():
        is_mailbox = raw_env_mailbox.strip().lower() in ("true", "1", "yes")
    else:
        is_mailbox = False

    if is_mailbox:
        if not effective_seed:
            raise ValueError(
                "Agentverse mailbox mode requires a securely configured, persistent identity seed. "
                "Please set the 'JANUS_HYPOTHESIS_ANALYST_SEED' environment variable."
            )
    elif not effective_seed:
        effective_seed = "janus_hypothesis_analyst_evaluation_seed_phase5"

    agent_kwargs: Dict[str, Any] = {
        "name": name,
        "seed": effective_seed,
        "port": port,
    }

    try:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        agent_kwargs["loop"] = loop
    except Exception:
        pass

    if is_mailbox:
        agent_kwargs["mailbox"] = True
        effective_agentverse = agentverse_url or os.getenv("AGENTVERSE_URL")
        if effective_agentverse:
            agent_kwargs["agentverse"] = effective_agentverse
    else:
        agent_kwargs["mailbox"] = False
        agent_kwargs["endpoint"] = endpoint or [f"http://127.0.0.1:{port}/submit"]

    agent = Agent(**agent_kwargs)
    agent.include(scientific_hypothesis_proto)
    return agent


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).resolve().parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()
    except ImportError:
        pass

    hypothesis_port = int(os.getenv("JANUS_HYPOTHESIS_ANALYST_PORT", "8011"))
    agent_instance = create_hypothesis_analyst_uagent(port=hypothesis_port)

    print("=" * 80)
    print(" JANUS Independent Hypothesis Analyst uAgent (Phase 5 Daemon)")
    print("=" * 80)
    print(f"Agent Name:    {agent_instance.name}")
    print(f"Agent Address: {agent_instance.address}")
    print(f"Agent Port:    {hypothesis_port}")
    print(f"Protocol:      janus_scientific_hypothesis (v1.0.0)")
    print("Starting daemon server...")
    agent_instance.run()
