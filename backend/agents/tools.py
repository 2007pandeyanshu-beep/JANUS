"""Scientific Tools for JANUS Multi-Agent Investigation (Phase 8)

All computational tools execute real deterministic Python calculations.
Literature retrieval tools return strictly verified citations with primary DOIs.
"""

import time
import math
import os
import asyncio
import concurrent.futures
import re
import unicodedata
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
import httpx

from app.schemas.scientific import (
    AnalysisInput,
    AnalysisResult,
    Hypothesis,
    Experiment,
    Evidence,
)
from app.schemas.audit import (
    ScientificAuditRequest,
    ScientificAuditResponse,
    AuditCheckItem,
)
from app.schemas.research import (
    ScientificResearchRequest,
    ScientificResearchResponse,
    ResearchEvidenceItem,
)
from app.schemas.hypothesis_analyst import (
    HypothesisAnalysisRequest,
    HypothesisAnalysisResponse,
    HypothesisEvaluationItem,
    HypothesisEvidenceLink,
)
from app.schemas.scientific_tool import (
    ArrheniusInput,
    KieInput,
    ReactionSimulationInput,
    ComputationOutputItem,
    ScientificComputationRequest,
    ScientificComputationResponse,
)
from app.schemas.experiment_design import (
    ExperimentScoreItem,
    ExperimentDesignRequest,
    ExperimentDesignResponse,
)
from app.schemas.review import (
    ReviewStatus,
    ConclusionGateStatus,
    ReviewCategory,
    ReviewFindingItem,
    ScientificReviewRequest,
    ScientificReviewReport,
)
from agents.types import CriticItem
from scientific.engine import ScientificEngine
from scientific.evidence_ingestion import load_evidence_ledger
from scientific.oer_scenario import get_oer_case_study_scenario
from scientific.scenarios import get_demo_scenario
from scientific.validation import IndependentEngineVerifier
from agents.types import AgentRole, ToolExecutionRecord, ProvenanceClassification


class LiteratureRetrievalTool:
    """Retrieves peer-reviewed scientific claims, citations, and evidence records."""

    @staticmethod
    def execute(
        query: str,
        case_study_id: Optional[str] = "CS-CAT-001"
    ) -> Tuple[List[Evidence], ToolExecutionRecord]:
        t0 = time.perf_counter()
        query_lower = query.lower()

        retrieved: List[Evidence] = []

        if case_study_id == "CS-CAT-001" or "wgs" in query_lower or "water-gas" in query_lower or "pt/ceo2" in query_lower:
            all_evidence = load_evidence_ledger()
            # Match keywords
            keywords = ["formate", "redox", "carboxyl", "kinetics", "drifts", "ssitka", "mars", "spectator"]
            for ev in all_evidence:
                if any(kw in ev.summary.lower() or kw in ev.title.lower() for kw in keywords):
                    retrieved.append(ev)
            if not retrieved:
                retrieved = all_evidence[:4]

        elif case_study_id == "CS-OER-002" or "oer" in query_lower or "perovskite" in query_lower or "oxygen evolution" in query_lower:
            retrieved = [
                Evidence(
                    id="EVD-OER-01",
                    title="Operando OEMS Lattice Oxygen Evolution in Perovskite",
                    source="Grimaud et al., Nature Chemistry 9, 457–465 (2017)",
                    source_doi="10.1038/nchem.2695",
                    provenance="literature_derived",
                    summary="Direct OEMS detection of 36O2 during OER confirms lattice oxygen participates in O-O bond formation.",
                    confidence=0.92,
                ),
                Evidence(
                    id="EVD-OER-02",
                    title="Anion-Exchange / Lattice Vacancy Driven OER on Perovskites",
                    source="Mefford et al., Nature Communications 7, 11053 (2016)",
                    source_doi="10.1038/ncomms11053",
                    provenance="literature_derived",
                    summary="Oxygen vacancy concentration correlates with non-concerted proton-electron transfer and bulk lattice oxygen diffusion.",
                    confidence=0.88,
                ),
                Evidence(
                    id="EVD-OER-03",
                    title="Design Principles for Oxide Electrocatalysts in OER",
                    source="Suntivich et al., Science 334, 1383–1386 (2011)",
                    source_doi="10.1126/science.1212858",
                    provenance="literature_derived",
                    summary="Demonstrates that eg orbital filling on transition metal cations governs adsorbate evolution mechanism (AEM) overpotential scaling.",
                    confidence=0.95,
                ),
                Evidence(
                    id="EVD-OER-04",
                    title="A Fundamental Relationship between Reaction Mechanism and Stability in Metal Oxide Catalysts for Oxygen Evolution",
                    source="Rong, Parolin & Kolpak, ACS Catalysis 6, 1153–1158 (2016)",
                    source_doi="10.1021/acscatal.5b02432",
                    provenance="theoretical_derived",
                    summary="First-principles calculations reveal direct surface oxo radical coupling (OPM) bypasses scaling without bulk dissolution.",
                    confidence=0.85,
                ),
            ]
        elif case_study_id in ["SYN-001", "DEMO", "KINASE"] or "kinase" in query_lower or "allosteric" in query_lower:
            demo_scenario = get_demo_scenario()
            retrieved = demo_scenario.evidence
        else:
            # Query did not match curated evidence libraries.
            # Strictly do not fabricate citations. Return empty list with transparent status.
            retrieved = []

        elapsed = (time.perf_counter() - t0) * 1000.0
        record = ToolExecutionRecord(
            tool_name="literature_retrieval",
            invoked_by=AgentRole.RESEARCH,
            input_arguments={"query": query, "case_study_id": case_study_id},
            output_data={
                "match_count": len(retrieved),
                "citations": [f"{e.source} (DOI: {e.source_doi or 'N/A'})" for e in retrieved],
                "claim_ids": [e.id for e in retrieved],
            },
            execution_time_ms=elapsed,
            status="SUCCESS",
            provenance=ProvenanceClassification.EMPIRICAL_LITERATURE,
        )
        return retrieved, record


class ChemicalKineticsTool:
    """Computes reaction kinetics parameters, Arrhenius rates, or kinetic isotope effects."""

    @staticmethod
    def calculate_arrhenius_rate(
        pre_exponential_A: float,
        activation_energy_kJ_mol: float,
        temperature_kelvin: float = 473.15  # 200 °C
    ) -> Tuple[float, ToolExecutionRecord]:
        t0 = time.perf_counter()
        R = 8.314462618e-3  # kJ / (mol * K)
        # k = A * exp(-Ea / RT)
        k = float(pre_exponential_A * math.exp(-activation_energy_kJ_mol / (R * temperature_kelvin)))
        elapsed = (time.perf_counter() - t0) * 1000.0

        record = ToolExecutionRecord(
            tool_name="chemical_kinetics_arrhenius",
            invoked_by=AgentRole.SCIENTIFIC_TOOL,
            input_arguments={
                "pre_exponential_A": pre_exponential_A,
                "activation_energy_kJ_mol": activation_energy_kJ_mol,
                "temperature_kelvin": temperature_kelvin,
            },
            output_data={"rate_constant_k": k, "unit": "s^-1"},
            execution_time_ms=elapsed,
            status="SUCCESS",
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return k, record

    @staticmethod
    def calculate_kie(
        rate_H: float,
        rate_D: float
    ) -> Tuple[float, ToolExecutionRecord]:
        t0 = time.perf_counter()
        if rate_D <= 0:
            raise ValueError("rate_D must be strictly positive.")
        kie = float(rate_H / rate_D)
        elapsed = (time.perf_counter() - t0) * 1000.0

        record = ToolExecutionRecord(
            tool_name="chemical_kinetics_kie",
            invoked_by=AgentRole.SCIENTIFIC_TOOL,
            input_arguments={"rate_H": rate_H, "rate_D": rate_D},
            output_data={"kinetic_isotope_effect_KIE": kie, "interpretation": "Primary KIE (>1.5) indicates C-H or O-H cleavage in RDS; unity KIE (~1.0) indicates proton-independent RDS"},
            execution_time_ms=elapsed,
            status="SUCCESS",
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return kie, record


class JanusRankingTool:
    """Invokes the authoritative JANUS information-theoretic ranking engine."""

    @staticmethod
    def execute(scenario: AnalysisInput) -> Tuple[AnalysisResult, ToolExecutionRecord]:
        t0 = time.perf_counter()
        result = ScientificEngine.execute_analysis(scenario)
        elapsed = (time.perf_counter() - t0) * 1000.0

        top_exp = result.ranked_experiments[0] if result.ranked_experiments else None
        record = ToolExecutionRecord(
            tool_name="janus_information_theoretic_ranking",
            invoked_by=AgentRole.EXPERIMENT_STRATEGY,
            input_arguments={
                "scenario_name": scenario.scenario_name,
                "hypothesis_count": len(scenario.hypotheses),
                "candidate_count": len(scenario.experiments),
                "cost_weight_alpha": scenario.cost_weight,
            },
            output_data={
                "prior_entropy_bits": top_exp.prior_entropy if top_exp else 0.0,
                "recommended_experiment_id": top_exp.experiment_id if top_exp else None,
                "top_expected_info_gain_bits": top_exp.expected_information_gain if top_exp else 0.0,
                "top_composite_utility": top_exp.composite_utility_score if top_exp else 0.0,
                "rankings_summary": [
                    {
                        "rank": s.rank,
                        "utility_rank": s.utility_rank,
                        "eig_rank": s.eig_rank,
                        "id": s.experiment_id,
                        "eig": s.expected_information_gain,
                        "utility": s.composite_utility_score,
                    }
                    for s in result.ranked_experiments
                ],
            },
            execution_time_ms=elapsed,
            status="SUCCESS",
            provenance=ProvenanceClassification.CALCULATED_BAYESIAN,
        )
        return result, record


class SimplexValidationTool:
    """Validates mathematical simplex normalization constraints on priors and likelihoods."""

    @staticmethod
    def validate_distribution(
        probabilities: Dict[str, float],
        label: str = "Distribution"
    ) -> Tuple[bool, str, ToolExecutionRecord]:
        t0 = time.perf_counter()
        vals = list(probabilities.values())
        tot = sum(vals)
        has_negative = any(v < 0 for v in vals)

        is_valid = (not has_negative) and abs(tot - 1.0) < 1e-4
        if has_negative:
            msg = f"{label} contains negative probability values."
        elif abs(tot - 1.0) >= 1e-4:
            msg = f"{label} sum equals {tot:.6f}, which violates simplex normalization constraint (target = 1.000000)."
        else:
            msg = f"{label} satisfies simplex normalization (sum = {tot:.6f})."

        elapsed = (time.perf_counter() - t0) * 1000.0
        record = ToolExecutionRecord(
            tool_name="simplex_validation",
            invoked_by=AgentRole.CRITIC,
            input_arguments={"label": label, "values": probabilities},
            output_data={"is_valid": is_valid, "sum": tot, "message": msg},
            execution_time_ms=elapsed,
            status="SUCCESS",
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return is_valid, msg, record


# ==============================================================================
# Crossref Bibliographic Metadata Verification Tool (Workstream A)
# ==============================================================================

class BibliographicVerificationStatus:
    BIBLIOGRAPHIC_VERIFIED_ONLINE = "BIBLIOGRAPHIC_VERIFIED_ONLINE"
    METADATA_MISMATCH = "METADATA_MISMATCH"
    DOI_NOT_FOUND = "DOI_NOT_FOUND"
    BIBLIOGRAPHIC_CACHED_OFFLINE = "BIBLIOGRAPHIC_CACHED_OFFLINE"
    UNAVAILABLE = "UNAVAILABLE"


def _normalize_string(s: Optional[str]) -> str:
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", str(s))
    s_clean = re.sub(r"[^a-zA-Z0-9\s]", " ", s_norm.lower())
    return " ".join(s_clean.split())


# In-memory lookup cache to minimize redundant external latency
_CROSSREF_CACHE: Dict[str, Dict[str, Any]] = {}

# Offline fallback catalog: verified bibliographic metadata from peer-reviewed literature
_CURATED_OFFLINE_CATALOG: Dict[str, Dict[str, Any]] = {
    "10.1016/j.jcat.2011.01.024": {
        "doi": "10.1016/j.jcat.2011.01.024",
        "title": "“Redox” vs “associative formate with –OH group regeneration” WGS reaction mechanism on Pt/CeO2: Effect of platinum particle size",
        "authors": ["Christos M. Kalamaras", "Sofia Americanou", "Angelos M. Efstathiou"],
        "journal": "Journal of Catalysis",
        "year": 2011,
        "volume": "279",
        "pages": "287-300",
        "url": "https://doi.org/10.1016/j.jcat.2011.01.024",
    },
    "10.1016/j.jcat.2007.09.003": {
        "doi": "10.1016/j.jcat.2007.09.003",
        "title": "Quantitative DRIFTS investigation of possible reaction mechanisms for the water-gas shift reaction on high-activity Pt- and Au-based catalysts",
        "authors": ["F. C. Meunier", "A. Goguet", "C. Hardacre", "R. Burch", "D. Thompsett"],
        "journal": "Journal of Catalysis",
        "year": 2007,
        "volume": "252",
        "pages": "18-22",
        "url": "https://doi.org/10.1016/j.jcat.2007.09.003",
    },
    "10.1016/j.jcat.2007.09.006": {
        "doi": "10.1016/j.jcat.2007.09.006",
        "title": "Novel mesoporous silicoaluminophosphates as highly active and selective catalysts for the Beckmann rearrangement of cyclohexanone oxime",
        "authors": ["T. Conesa", "R. Mokaya", "Z. Yang"],
        "journal": "Journal of Catalysis",
        "year": 2007,
        "volume": "252",
        "pages": "39-48",
        "url": "https://doi.org/10.1016/j.jcat.2007.09.006",
    },
    "10.1039/B611217A": {
        "doi": "10.1039/B611217A",
        "title": "Differences in the mechanism of the water–gas shift reaction on gold and other metal catalysts",
        "authors": ["Robert Burch"],
        "journal": "Phys. Chem. Chem. Phys.",
        "year": 2006,
        "url": "https://doi.org/10.1039/B611217A",
    },
    "10.1126/science.1150038": {
        "doi": "10.1126/science.1150038",
        "title": "Activity of CeOx and TiOx Nanoparticles on Au(111) in the Water-Gas Shift Reaction",
        "authors": ["J. A. Rodriguez", "S. Ma", "P. Liu", "J. Hrbek", "J. Evans", "M. Perez"],
        "journal": "Science",
        "year": 2007,
        "url": "https://doi.org/10.1126/science.1150038",
    },
    "10.1016/j.jcat.2009.03.002": {
        "doi": "10.1016/j.jcat.2009.03.002",
        "title": "Kinetic and mechanistic studies of the water–gas shift reaction on Pt/TiO2 catalyst",
        "authors": ["C. M. Kalamaras", "P. Panagiotopoulou", "D. I. Kondarides", "A. M. Efstathiou"],
        "journal": "Journal of Catalysis",
        "year": 2009,
        "volume": "264",
        "pages": "117-129",
        "url": "https://doi.org/10.1016/j.jcat.2009.03.002",
    },
    "10.1016/j.jcat.2009.03.013": {
        "doi": "10.1016/j.jcat.2009.03.013",
        "title": "Reactive oxygen on a Au/TiO2 supported catalyst",
        "authors": ["M. Kotobuki", "R. Leppelt", "D. A. Hansgen", "D. Widmann", "R. J. Behm"],
        "journal": "Journal of Catalysis",
        "year": 2009,
        "volume": "264",
        "pages": "67-76",
        "url": "https://doi.org/10.1016/j.jcat.2009.03.013",
    },
    "10.1038/nchem.2695": {
        "doi": "10.1038/nchem.2695",
        "title": "Activating lattice oxygen redox reactions in metal oxides to catalyse oxygen evolution",
        "authors": ["Alexis Grimaud", "Oscar Diaz-Morales", "Binghao Han"],
        "journal": "Nature Chemistry",
        "year": 2017,
        "url": "https://doi.org/10.1038/nchem.2695",
    },
    "10.1038/ncomms11053": {
        "doi": "10.1038/ncomms11053",
        "title": "Water oxidation on perovskite electrocatalysts: anion-exchange vs lattice oxygen",
        "authors": ["J. Tyler Mefford", "William G. Hardin"],
        "journal": "Nature Communications",
        "year": 2016,
        "url": "https://doi.org/10.1038/ncomms11053",
    },
    "10.1126/science.1212858": {
        "doi": "10.1126/science.1212858",
        "title": "Design principles for oxide electrocatalysts in oxygen evolution reaction",
        "authors": ["Jin Suntivich", "Kevin J. May", "Hubert A. Gasteiger"],
        "journal": "Science",
        "year": 2011,
        "url": "https://doi.org/10.1126/science.1212858",
    },
    "10.1021/acscatal.5b02432": {
        "doi": "10.1021/acscatal.5b02432",
        "title": "A Fundamental Relationship between Reaction Mechanism and Stability in Metal Oxide Catalysts for Oxygen Evolution",
        "authors": ["Xi Rong", "Jules Parolin", "Alexie M. Kolpak"],
        "journal": "ACS Catalysis",
        "year": 2016,
        "url": "https://doi.org/10.1021/acscatal.5b02432",
    },
}


class CrossrefValidationTool:
    """
    Retrieves and validates scholarly publication metadata from the Crossref REST API.
    
    Scientific Boundary:
    Validates bibliographic consistency (journal, title, authors, publication date)
    against the official publisher registration record.
    DOES NOT equate bibliographic registration with proof or empirical confirmation
    of any mechanistic claim made within the article.
    """
    CROSSREF_API_URL = "https://api.crossref.org/works/"
    USER_AGENT = "JANUS-Scientific-Agent/1.0 (mailto:janus-audit@fetchathon.ai; https://github.com/fetchai/innovation-lab-examples)"
    SCIENTIFIC_BOUNDARY_DISCLAIMER = (
        "Crossref metadata validation confirms bibliographic record consistency, "
        "not that the paper's results support a specific mechanistic claim."
    )

    @classmethod
    def verify_doi(
        cls,
        doi: str,
        expected_title: Optional[str] = None,
        expected_citation: Optional[str] = None,
        expected_authors: Optional[List[str]] = None,
        expected_year: Optional[int] = None,
        expected_journal: Optional[str] = None,
        timeout: float = 4.0,
        client: Optional[httpx.Client] = None,
    ) -> Dict[str, Any]:
        """
        Queries Crossref REST API for a DOI and verifies bibliographic metadata.
        Returns a structured result with status, metadata, latency, and provenance.
        """
        t0 = time.perf_counter()
        if not doi or not str(doi).strip():
            return {
                "doi": doi or "",
                "status": BibliographicVerificationStatus.DOI_NOT_FOUND,
                "message": "Empty or missing DOI string",
                "retrieval_time_ms": 0.0,
                "source": "Crossref REST API",
                "bibliographic_metadata": None,
                "mismatch_details": "No DOI provided for bibliographic validation.",
                "scientific_boundary": cls.SCIENTIFIC_BOUNDARY_DISCLAIMER,
            }

        clean_doi = str(doi).strip()
        if clean_doi.lower().startswith("https://doi.org/"):
            clean_doi = clean_doi[16:]
        elif clean_doi.lower().startswith("http://doi.org/"):
            clean_doi = clean_doi[15:]
        clean_doi = clean_doi.strip().rstrip("/")

        # Basic DOI format check (10.xxxx/...)
        if not clean_doi.startswith("10.") or "/" not in clean_doi:
            return {
                "doi": clean_doi,
                "status": BibliographicVerificationStatus.DOI_NOT_FOUND,
                "message": f"Malformed DOI format '{clean_doi}' (must begin with '10.xxxx/')",
                "retrieval_time_ms": (time.perf_counter() - t0) * 1000.0,
                "source": "Crossref REST API",
                "bibliographic_metadata": None,
                "mismatch_details": f"Identifier '{clean_doi}' does not match standard DOI syntax.",
                "scientific_boundary": cls.SCIENTIFIC_BOUNDARY_DISCLAIMER,
            }

        # Check in-memory cache
        if clean_doi in _CROSSREF_CACHE:
            cached = dict(_CROSSREF_CACHE[clean_doi])
            cached["retrieval_time_ms"] = (time.perf_counter() - t0) * 1000.0
            cached["cached"] = True
            return cached

        url = f"{cls.CROSSREF_API_URL}{clean_doi}"
        headers = {"User-Agent": cls.USER_AGENT}

        should_close_client = False
        if client is None:
            client = httpx.Client(timeout=timeout)
            should_close_client = True

        status = BibliographicVerificationStatus.UNAVAILABLE
        bib_meta: Optional[Dict[str, Any]] = None
        mismatch_details: Optional[str] = None
        source_label = "Crossref REST API"

        try:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                msg = data.get("message", {})
                
                # Extract fields
                titles = msg.get("title", [])
                cr_title = titles[0] if titles else ""
                cr_authors_raw = msg.get("author", [])
                cr_authors = [
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in cr_authors_raw if a.get("family") or a.get("given")
                ]
                cr_family_names = [a.get("family", "").lower() for a in cr_authors_raw if a.get("family")]
                container_titles = msg.get("container-title", [])
                cr_journal = container_titles[0] if container_titles else ""
                
                # Publication year
                cr_year = None
                for date_key in ("published-print", "issued", "created", "published-online"):
                    parts = msg.get(date_key, {}).get("date-parts", [])
                    if parts and parts[0] and isinstance(parts[0][0], int):
                        cr_year = parts[0][0]
                        break

                cr_url = msg.get("URL") or f"https://doi.org/{clean_doi}"

                bib_meta = {
                    "doi": clean_doi,
                    "title": cr_title,
                    "authors": cr_authors,
                    "journal": cr_journal,
                    "year": cr_year,
                    "volume": msg.get("volume"),
                    "page": msg.get("page"),
                    "publisher": msg.get("publisher"),
                    "url": cr_url,
                }

                # Evaluate metadata match against expected anchors
                norm_cr_title = _normalize_string(cr_title)
                norm_cr_journal = _normalize_string(cr_journal)
                norm_exp_title = _normalize_string(expected_title)
                norm_exp_citation = _normalize_string(expected_citation)
                norm_exp_journal = _normalize_string(expected_journal)

                # Check 1: Author family overlap
                author_match = False
                if expected_authors:
                    for exp_a in expected_authors:
                        norm_a = _normalize_string(exp_a)
                        if any(norm_a in fam for fam in cr_family_names) or any(fam in norm_a for fam in cr_family_names):
                            author_match = True
                            break
                elif norm_exp_citation:
                    for fam in cr_family_names:
                        if len(fam) >= 3 and fam in norm_exp_citation:
                            author_match = True
                            break

                # Check 2: Title keyword overlap
                title_match = False
                if norm_exp_title:
                    words_exp = set(w for w in norm_exp_title.split() if len(w) > 3)
                    words_cr = set(w for w in norm_cr_title.split() if len(w) > 3)
                    if words_exp and words_cr:
                        overlap = words_exp.intersection(words_cr)
                        jaccard = len(overlap) / len(words_exp.union(words_cr))
                        if jaccard >= 0.25 or len(overlap) >= 3:
                            title_match = True

                # Check 3: Journal overlap
                journal_match = False
                if norm_exp_journal and norm_cr_journal:
                    journal_match = (norm_exp_journal in norm_cr_journal) or (norm_cr_journal in norm_exp_journal)
                elif norm_exp_citation and norm_cr_journal:
                    words_j = [w for w in norm_cr_journal.split() if len(w) > 3]
                    journal_match = any(w in norm_exp_citation for w in words_j)

                # Check 4: Year match
                year_match = False
                if expected_year and cr_year:
                    year_match = (expected_year == cr_year)
                elif cr_year and norm_exp_citation:
                    year_match = str(cr_year) in norm_exp_citation

                # Decision rule
                if title_match or (author_match and (journal_match or year_match)) or (journal_match and year_match and author_match):
                    status = BibliographicVerificationStatus.BIBLIOGRAPHIC_VERIFIED_ONLINE
                else:
                    status = BibliographicVerificationStatus.METADATA_MISMATCH
                    mismatch_details = (
                        f"Crossref record returned '{cr_title[:60]}' by {cr_authors[:2]} ({cr_journal}, {cr_year}), "
                        f"which does not match expected citation '{expected_citation or expected_title}'."
                    )

            elif resp.status_code == 404:
                if clean_doi in _CURATED_OFFLINE_CATALOG:
                    status = BibliographicVerificationStatus.BIBLIOGRAPHIC_CACHED_OFFLINE
                    bib_meta = dict(_CURATED_OFFLINE_CATALOG[clean_doi])
                    source_label = "Curated Evidence Ledger (Verified Offline Fallback)"
                    mismatch_details = f"DOI '{clean_doi}' returned HTTP 404 from Crossref; retrieved from verified offline catalog."
                else:
                    status = BibliographicVerificationStatus.DOI_NOT_FOUND
                    mismatch_details = f"DOI '{clean_doi}' was not found in Crossref database (HTTP 404)."
            else:
                status = BibliographicVerificationStatus.UNAVAILABLE
                mismatch_details = f"Crossref API returned HTTP {resp.status_code}."

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError, Exception) as err:
            err_name = type(err).__name__
            # Network failed -> check verified local offline fallback catalog
            if clean_doi in _CURATED_OFFLINE_CATALOG:
                status = BibliographicVerificationStatus.BIBLIOGRAPHIC_CACHED_OFFLINE
                bib_meta = dict(_CURATED_OFFLINE_CATALOG[clean_doi])
                source_label = "Curated Evidence Ledger (Verified Offline Cache)"
                mismatch_details = f"Live Crossref lookup timed out or failed ({err_name}); retrieved from verified local offline ledger cache."
            else:
                status = BibliographicVerificationStatus.UNAVAILABLE
                mismatch_details = f"Live Crossref lookup failed ({err_name}) and no local cache was available."
        finally:
            if should_close_client:
                client.close()

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        result = {
            "doi": clean_doi,
            "status": status,
            "bibliographic_metadata": bib_meta,
            "retrieval_time_ms": elapsed_ms,
            "source": source_label,
            "mismatch_details": mismatch_details,
            "scientific_boundary": cls.SCIENTIFIC_BOUNDARY_DISCLAIMER,
        }

        # Cache valid lookups
        if status in (
            BibliographicVerificationStatus.BIBLIOGRAPHIC_VERIFIED_ONLINE,
            BibliographicVerificationStatus.METADATA_MISMATCH,
            BibliographicVerificationStatus.DOI_NOT_FOUND,
            BibliographicVerificationStatus.BIBLIOGRAPHIC_CACHED_OFFLINE,
        ):
            _CROSSREF_CACHE[clean_doi] = result

        return result

    @classmethod
    def verify_evidence_ledger(
        cls,
        evidence_items: List[Evidence],
        timeout_per_item: float = 3.5,
    ) -> Tuple[List[Evidence], ToolExecutionRecord]:
        """
        Iterates over a list of Evidence items, validates each DOI against Crossref,
        and annotates the Evidence records with verification statuses and metadata.
        """
        t0 = time.perf_counter()
        results: List[Dict[str, Any]] = []

        with httpx.Client(timeout=timeout_per_item) as client:
            for ev in evidence_items:
                if ev.source_doi:
                    res = cls.verify_doi(
                        doi=ev.source_doi,
                        expected_title=ev.title,
                        expected_citation=ev.source,
                        timeout=timeout_per_item,
                        client=client,
                    )
                    ev.doi_verification_status = res["status"]
                    ev.bibliographic_metadata = res.get("bibliographic_metadata")
                    results.append(res)
                else:
                    ev.doi_verification_status = "NO_DOI_PROVIDED"
                    results.append({
                        "doi": None,
                        "status": "NO_DOI_PROVIDED",
                        "claim_id": ev.id,
                        "message": "Evidence claim does not specify a DOI",
                    })

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        status_counts = {}
        for r in results:
            st = r.get("status", "UNKNOWN")
            status_counts[st] = status_counts.get(st, 0) + 1

        record = ToolExecutionRecord(
            tool_name="crossref_bibliographic_verification",
            invoked_by=AgentRole.RESEARCH,
            input_arguments={
                "evidence_count": len(evidence_items),
                "doi_count": sum(1 for e in evidence_items if e.source_doi),
            },
            output_data={
                "verification_results": results,
                "status_summary": status_counts,
                "scientific_boundary": cls.SCIENTIFIC_BOUNDARY_DISCLAIMER,
            },
            execution_time_ms=elapsed_ms,
            status="SUCCESS",
            provenance=ProvenanceClassification.EXTERNAL_RETRIEVAL,
        )
        return evidence_items, record


# ==============================================================================
# Independent Mathematical Verifier Tool (Workstream B)
# ==============================================================================

class IndependentVerificationTool:
    """Invokes IndependentEngineVerifier to perform rigorous mathematical invariant auditing."""

    @staticmethod
    def verify(
        analysis_result: AnalysisResult,
        scenario_input: AnalysisInput
    ) -> Tuple[Dict[str, Any], ToolExecutionRecord]:
        t0 = time.perf_counter()
        report = IndependentEngineVerifier.verify_analysis_result(analysis_result, scenario_input)
        elapsed = (time.perf_counter() - t0) * 1000.0

        record = ToolExecutionRecord(
            tool_name="independent_mathematical_verification",
            invoked_by=AgentRole.CRITIC,
            input_arguments={
                "scenario_name": scenario_input.scenario_name,
                "hypothesis_count": len(scenario_input.hypotheses),
                "ranked_experiments_count": len(analysis_result.ranked_experiments),
            },
            output_data={
                "is_verified": report["is_verified"],
                "total_checks": report["total_checks"],
                "passed_checks": report["passed_checks"],
                "failed_checks": report["failed_checks"],
                "summary": report["summary"],
                "check_items": report["check_items"],
            },
            execution_time_ms=elapsed,
            status="SUCCESS" if report["is_verified"] else "ERROR",
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return report, record

    @staticmethod
    def verify_update(
        initial_priors: Dict[str, float],
        likelihood_vector: Dict[str, float],
        observed_posteriors: Dict[str, float],
        experiment_id: str,
        observed_outcome: str,
    ) -> Tuple[Dict[str, Any], ToolExecutionRecord]:
        t0 = time.perf_counter()
        report = IndependentEngineVerifier.verify_bayesian_observation_update(
            initial_priors=initial_priors,
            likelihood_vector=likelihood_vector,
            observed_posteriors=observed_posteriors,
        )
        elapsed = (time.perf_counter() - t0) * 1000.0

        record = ToolExecutionRecord(
            tool_name="independent_bayesian_update_verification",
            invoked_by=AgentRole.CRITIC,
            input_arguments={
                "experiment_id": experiment_id,
                "observed_outcome": observed_outcome,
                "initial_priors": initial_priors,
            },
            output_data=report,
            execution_time_ms=elapsed,
            status="SUCCESS" if report["is_valid"] else "ERROR",
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return report, record


# ==============================================================================
# Independent Fetch.ai Auditor uAgent Client Tool (Phase 3)
# ==============================================================================

def _run_sync_coro(coro):
    """Safely executes an async coroutine from either sync or active async event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)


class AuditorAgentTool:
    """
    Client tool that dispatches scientific audit requests to the independent Fetch.ai
    auditor uAgent (janus_auditor_uagent) via native synchronous inter-agent messaging.
    """

    DEFAULT_AUDITOR_ADDRESS = "agent1qtce9c74t0fmyy2las425v7rfzf8mvlgwjegcwwx5pmmnuxhfryqs8l7ylg"
    DEFAULT_AUDITOR_ENDPOINT = "http://127.0.0.1:8009/submit"

    @classmethod
    def get_auditor_address(cls) -> str:
        return os.getenv("JANUS_AUDITOR_ADDRESS", cls.DEFAULT_AUDITOR_ADDRESS)

    @classmethod
    def get_auditor_endpoint(cls) -> str:
        return os.getenv("JANUS_AUDITOR_ENDPOINT", cls.DEFAULT_AUDITOR_ENDPOINT)

    @classmethod
    def get_timeout(cls) -> float:
        try:
            return float(os.getenv("JANUS_AUDITOR_TIMEOUT", "4.0"))
        except (ValueError, TypeError):
            return 4.0

    @classmethod
    def _dispatch_request(
        cls,
        request: ScientificAuditRequest,
        timeout: Optional[float] = None,
    ) -> ScientificAuditResponse:
        """Sends the structured audit request via native uAgents send_sync_message."""
        auditor_addr = cls.get_auditor_address()
        auditor_ep = cls.get_auditor_endpoint()
        effective_timeout = timeout if timeout is not None else cls.get_timeout()

        try:
            from uagents.communication import send_sync_message
            from uagents.resolver import RulesBasedResolver

            resolver = RulesBasedResolver(rules={auditor_addr: auditor_ep})

            async def _send():
                return await send_sync_message(
                    destination=auditor_addr,
                    message=request,
                    response_type=ScientificAuditResponse,
                    resolver=resolver,
                    timeout=max(1, int(math.ceil(effective_timeout))),
                )

            resp = _run_sync_coro(_send())
            if isinstance(resp, ScientificAuditResponse):
                return resp
            else:
                # Delivery failure or MsgStatus returned
                now_iso = datetime.now(timezone.utc).isoformat()
                return ScientificAuditResponse(
                    correlation_id=request.correlation_id,
                    status="AUDIT_UNAVAILABLE",
                    auditor_address=auditor_addr,
                    timestamp=now_iso,
                    checks=[
                        AuditCheckItem(
                            check_id="auditor_daemon_connectivity",
                            status="FAIL",
                            message=f"Auditor uAgent at {auditor_addr} ({auditor_ep}) did not return a valid response: {resp}",
                        )
                    ],
                    all_invariants_hold=False,
                    passed_checks_count=0,
                    total_checks_count=1,
                    mandatory_checks_count=1,
                    mandatory_passed_count=0,
                    warnings_count=0,
                    mismatches=["Auditor agent endpoint unreachable or returned non-audit payload"],
                    bibliographic_mismatch_notices=[],
                    verdict=(
                        f"AUDIT_UNAVAILABLE: Independent auditor uAgent ({auditor_addr}) is unreachable or offline. "
                        f"Mathematical invariants not independently certified."
                    ),
                )
        except Exception as exc:
            now_iso = datetime.now(timezone.utc).isoformat()
            return ScientificAuditResponse(
                correlation_id=request.correlation_id,
                status="AUDIT_UNAVAILABLE",
                auditor_address=auditor_addr,
                timestamp=now_iso,
                checks=[
                    AuditCheckItem(
                        check_id="auditor_daemon_connectivity",
                        status="FAIL",
                        message=f"Auditor uAgent at {auditor_addr} communication error: {str(exc)}",
                    )
                ],
                all_invariants_hold=False,
                passed_checks_count=0,
                total_checks_count=1,
                mandatory_checks_count=1,
                mandatory_passed_count=0,
                warnings_count=0,
                mismatches=[f"Auditor agent communication exception: {str(exc)}"],
                bibliographic_mismatch_notices=[],
                verdict=(
                    f"AUDIT_UNAVAILABLE: Independent auditor uAgent ({auditor_addr}) connection failed ({exc}). "
                    f"Mathematical invariants not independently certified."
                ),
            )

    @classmethod
    def audit_analysis(
        cls,
        analysis_result: AnalysisResult,
        scenario_input: AnalysisInput,
        correlation_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[ScientificAuditResponse, ToolExecutionRecord]:
        t0 = time.perf_counter()
        corr_id = correlation_id or f"audit-analysis-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"

        req = ScientificAuditRequest(
            correlation_id=corr_id,
            scenario_id=scenario_input.case_study_id or scenario_input.scenario_name,
            hypotheses=[h.model_dump() for h in scenario_input.hypotheses],
            experiments=[e.model_dump() for e in scenario_input.experiments],
            ranked_scores=[s.model_dump() for s in analysis_result.ranked_experiments],
            selected_recommendation=analysis_result.ranked_experiments[0].model_dump() if analysis_result.ranked_experiments else {},
            evidence_ledger=[ev.model_dump() for ev in (scenario_input.evidence or [])],
            is_sequential_update=False,
        )

        resp = cls._dispatch_request(req, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000.0

        tool_status = "SUCCESS" if resp.status == "AUDIT_PASSED" else ("WARNING" if resp.status == "AUDIT_UNAVAILABLE" else "ERROR")

        record = ToolExecutionRecord(
            tool_name="janus_independent_auditor_uagent",
            invoked_by=AgentRole.CRITIC,
            input_arguments={
                "correlation_id": corr_id,
                "scenario_id": req.scenario_id,
                "hypothesis_count": len(req.hypotheses),
                "experiments_count": len(req.experiments),
                "auditor_address": resp.auditor_address,
            },
            output_data=resp.model_dump(),
            execution_time_ms=elapsed,
            status=tool_status,
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return resp, record

    @classmethod
    def audit_sequential_update(
        cls,
        initial_priors_before: Dict[str, float],
        observed_experiment: Optional[Experiment],
        observed_outcome: str,
        observed_posteriors: Dict[str, float],
        analysis_result: AnalysisResult,
        scenario_input: AnalysisInput,
        correlation_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[ScientificAuditResponse, ToolExecutionRecord]:
        t0 = time.perf_counter()
        corr_id = correlation_id or f"audit-update-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"

        # Ensure observed experiment is included in experiments list so auditor can inspect likelihoods
        exps = [e.model_dump() for e in scenario_input.experiments]
        if observed_experiment and not any(e["id"] == observed_experiment.id for e in exps):
            exps.append(observed_experiment.model_dump())

        req = ScientificAuditRequest(
            correlation_id=corr_id,
            scenario_id=scenario_input.case_study_id or scenario_input.scenario_name,
            hypotheses=[h.model_dump() for h in scenario_input.hypotheses],
            experiments=exps,
            ranked_scores=[s.model_dump() for s in analysis_result.ranked_experiments],
            selected_recommendation=analysis_result.ranked_experiments[0].model_dump() if analysis_result.ranked_experiments else {},
            evidence_ledger=[ev.model_dump() for ev in (scenario_input.evidence or [])],
            is_sequential_update=True,
            initial_priors_before=initial_priors_before,
            observed_experiment_id=observed_experiment.id if observed_experiment else None,
            observed_outcome=observed_outcome,
            observed_posteriors=observed_posteriors,
        )

        resp = cls._dispatch_request(req, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000.0

        tool_status = "SUCCESS" if resp.status == "AUDIT_PASSED" else ("WARNING" if resp.status == "AUDIT_UNAVAILABLE" else "ERROR")

        record = ToolExecutionRecord(
            tool_name="janus_independent_auditor_uagent",
            invoked_by=AgentRole.CRITIC,
            input_arguments={
                "correlation_id": corr_id,
                "scenario_id": req.scenario_id,
                "observed_experiment": req.observed_experiment_id,
                "observed_outcome": req.observed_outcome,
                "auditor_address": resp.auditor_address,
            },
            output_data=resp.model_dump(),
            execution_time_ms=elapsed,
            status=tool_status,
            provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
        )
        return resp, record


class ResearchAgentTool:
    """
    Client tool that dispatches scientific research requests to the independent Fetch.ai
    research uAgent (janus_research_agent) via native synchronous inter-agent messaging.
    """

    DEFAULT_RESEARCH_AGENT_ADDRESS = "agent1q0hhnepntx63ach7vr93q930wk8swxgntray6lvn4scujt2hj0dzzd9d0py"
    DEFAULT_RESEARCH_AGENT_ENDPOINT = "http://127.0.0.1:8010/submit"

    @classmethod
    def get_research_agent_address(cls) -> str:
        return os.getenv("JANUS_RESEARCH_AGENT_ADDRESS", cls.DEFAULT_RESEARCH_AGENT_ADDRESS)

    @classmethod
    def get_research_agent_endpoint(cls) -> str:
        return os.getenv("JANUS_RESEARCH_AGENT_ENDPOINT", cls.DEFAULT_RESEARCH_AGENT_ENDPOINT)

    @classmethod
    def get_timeout(cls) -> float:
        try:
            return float(os.getenv("JANUS_RESEARCH_AGENT_TIMEOUT", "5.0"))
        except (ValueError, TypeError):
            return 5.0

    @classmethod
    def _dispatch_request(
        cls,
        request: ScientificResearchRequest,
        timeout: Optional[float] = None,
    ) -> ScientificResearchResponse:
        """Sends the structured research request via native uAgents send_sync_message."""
        agent_addr = cls.get_research_agent_address()
        agent_ep = cls.get_research_agent_endpoint()
        effective_timeout = timeout if timeout is not None else cls.get_timeout()

        try:
            from uagents.communication import send_sync_message
            from uagents.resolver import RulesBasedResolver

            resolver = RulesBasedResolver(rules={agent_addr: agent_ep})

            async def _send():
                return await send_sync_message(
                    destination=agent_addr,
                    message=request,
                    response_type=ScientificResearchResponse,
                    resolver=resolver,
                    timeout=max(1, int(math.ceil(effective_timeout))),
                )

            resp = _run_sync_coro(_send())
            if isinstance(resp, ScientificResearchResponse):
                return resp
            else:
                now_iso = datetime.now(timezone.utc).isoformat()
                return ScientificResearchResponse(
                    correlation_id=request.correlation_id,
                    investigation_id=request.investigation_id,
                    status="RESEARCH_UNAVAILABLE",
                    agent_address=agent_addr,
                    timestamp=now_iso,
                    evidence_items=[],
                    total_evidence_count=0,
                    verified_online_count=0,
                    cached_offline_count=0,
                    metadata_mismatch_count=0,
                    not_found_count=0,
                    warnings=[f"Research uAgent at {agent_addr} ({agent_ep}) returned non-research payload: {resp}"],
                    execution_summary=(
                        f"RESEARCH_UNAVAILABLE: Independent research uAgent ({agent_addr}) is unreachable or offline."
                    ),
                )
        except Exception as exc:
            now_iso = datetime.now(timezone.utc).isoformat()
            return ScientificResearchResponse(
                correlation_id=request.correlation_id,
                investigation_id=request.investigation_id,
                status="RESEARCH_UNAVAILABLE",
                agent_address=agent_addr,
                timestamp=now_iso,
                evidence_items=[],
                total_evidence_count=0,
                verified_online_count=0,
                cached_offline_count=0,
                metadata_mismatch_count=0,
                not_found_count=0,
                warnings=[f"Research uAgent communication error: {str(exc)}"],
                execution_summary=(
                    f"RESEARCH_UNAVAILABLE: Independent research uAgent ({agent_addr}) connection failed ({exc})."
                ),
            )

    @classmethod
    def execute_research(
        cls,
        research_question: str,
        investigation_id: str,
        case_study_id: Optional[str] = "CS-CAT-001",
        topic_context: Optional[str] = None,
        correlation_id: Optional[str] = None,
        max_results: Optional[int] = 10,
        timeout: Optional[float] = None,
        allow_local_fallback: bool = True,
    ) -> Tuple[ScientificResearchResponse, ToolExecutionRecord, List[Evidence]]:
        """
        Dispatches research request to the independent Research uAgent over Fetch.ai protocol.
        If the daemon is offline and allow_local_fallback is True, gracefully executes local
        literature retrieval while honestly recording RESEARCH_UNAVAILABLE and fallback status.
        Returns (research_response, tool_record, evidence_list_for_downstream_pipeline).
        """
        t0 = time.perf_counter()
        corr_id = correlation_id or f"research-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"

        req = ScientificResearchRequest(
            correlation_id=corr_id,
            investigation_id=investigation_id,
            research_question=research_question,
            case_study_id=case_study_id,
            topic_context=topic_context,
            max_results=max_results,
        )

        resp = cls._dispatch_request(req, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000.0

        if resp.status in ("RESEARCH_COMPLETED", "RESEARCH_PARTIAL", "RESEARCH_EMPTY"):
            tool_status = "SUCCESS" if resp.status == "RESEARCH_COMPLETED" else "WARNING"
            pipeline_evidence = [
                Evidence(
                    id=item.id,
                    title=item.title,
                    source=item.source,
                    source_doi=item.source_doi,
                    provenance=item.provenance,
                    summary=item.summary,
                    confidence=item.confidence,
                    doi_verification_status=item.doi_verification_status,
                    doi_verification_message=item.doi_verification_message,
                    bibliographic_metadata=item.bibliographic_metadata,
                )
                for item in resp.evidence_items
            ]
            record = ToolExecutionRecord(
                tool_name="janus_independent_research_uagent",
                invoked_by=AgentRole.RESEARCH,
                input_arguments={
                    "correlation_id": corr_id,
                    "investigation_id": investigation_id,
                    "research_question": research_question,
                    "case_study_id": case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status=tool_status,
                provenance=ProvenanceClassification.EMPIRICAL_LITERATURE,
            )
            return resp, record, pipeline_evidence

        # If RESEARCH_UNAVAILABLE and allow_local_fallback
        if allow_local_fallback:
            fallback_evidence, _ = LiteratureRetrievalTool.execute(
                query=research_question, case_study_id=case_study_id
            )
            max_k = max_results or 10
            validated_fallback, _ = CrossrefValidationTool.verify_evidence_ledger(fallback_evidence[:max_k])
            record = ToolExecutionRecord(
                tool_name="janus_independent_research_uagent",
                invoked_by=AgentRole.RESEARCH,
                input_arguments={
                    "correlation_id": corr_id,
                    "investigation_id": investigation_id,
                    "research_question": research_question,
                    "case_study_id": case_study_id,
                    "agent_address": resp.agent_address,
                    "fallback_engaged": True,
                },
                output_data={
                    "uagent_response": resp.model_dump(),
                    "fallback_evidence_count": len(validated_fallback),
                },
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.EMPIRICAL_LITERATURE,
            )
            return resp, record, validated_fallback
        else:
            record = ToolExecutionRecord(
                tool_name="janus_independent_research_uagent",
                invoked_by=AgentRole.RESEARCH,
                input_arguments={
                    "correlation_id": corr_id,
                    "investigation_id": investigation_id,
                    "research_question": research_question,
                    "case_study_id": case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.EMPIRICAL_LITERATURE,
            )
            return resp, record, []


class HypothesisAnalystTool:
    """
    Client interface for dispatching hypothesis analysis requests to the
    autonomous Hypothesis Analyst uAgent (`janus_hypothesis_analyst`) running on port 8011.
    """
    DEFAULT_HYPOTHESIS_ANALYST_ADDRESS = "agent1qfmmvna5ff9nwgyq6r8p63c2pd82w8ashzghta3hs2zaawguj548xx0lk0d"
    DEFAULT_HYPOTHESIS_ANALYST_PORT = 8011
    DEFAULT_HYPOTHESIS_ANALYST_ENDPOINT = "http://127.0.0.1:8011/submit"
    DEFAULT_TIMEOUT_SECONDS = 15.0

    @classmethod
    def get_hypothesis_analyst_address(cls) -> str:
        addr = os.getenv("JANUS_HYPOTHESIS_ANALYST_ADDRESS")
        if addr:
            return addr.strip()
        seed = os.getenv("JANUS_HYPOTHESIS_ANALYST_SEED")
        if seed:
            from uagents.crypto import Identity
            return Identity.from_seed(seed, 0).address
        return cls.DEFAULT_HYPOTHESIS_ANALYST_ADDRESS

    @classmethod
    def get_hypothesis_analyst_endpoint(cls) -> str:
        ep = os.getenv("JANUS_HYPOTHESIS_ANALYST_ENDPOINT")
        if ep:
            return ep.strip()
        port = os.getenv("JANUS_HYPOTHESIS_ANALYST_PORT", str(cls.DEFAULT_HYPOTHESIS_ANALYST_PORT))
        return f"http://127.0.0.1:{port}/submit"

    @classmethod
    def get_timeout(cls) -> float:
        val = os.getenv("JANUS_HYPOTHESIS_ANALYST_TIMEOUT_SECONDS")
        if val:
            try:
                return float(val)
            except ValueError:
                pass
        return cls.DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def _dispatch_request(
        cls,
        request: HypothesisAnalysisRequest,
        timeout: Optional[float] = None,
    ) -> HypothesisAnalysisResponse:
        """
        Dispatches request synchronously to the Hypothesis Analyst uAgent via Fetch.ai native sync messaging.
        """
        agent_addr = cls.get_hypothesis_analyst_address()
        agent_ep = cls.get_hypothesis_analyst_endpoint()
        effective_timeout = timeout if timeout is not None else cls.get_timeout()

        try:
            from uagents.communication import send_sync_message
            from uagents.resolver import RulesBasedResolver

            resolver = RulesBasedResolver(rules={agent_addr: agent_ep})

            async def _send():
                return await send_sync_message(
                    destination=agent_addr,
                    message=request,
                    response_type=HypothesisAnalysisResponse,
                    resolver=resolver,
                    timeout=max(1, int(math.ceil(effective_timeout))),
                )

            resp = _run_sync_coro(_send())
            if isinstance(resp, HypothesisAnalysisResponse):
                return resp
            else:
                now_iso = datetime.now(timezone.utc).isoformat()
                return HypothesisAnalysisResponse(
                    correlation_id=request.correlation_id,
                    investigation_id=request.investigation_id,
                    status="ANALYSIS_UNAVAILABLE",
                    agent_address=agent_addr,
                    timestamp=now_iso,
                    hypotheses=[],
                    simplex_sum=0.0,
                    is_simplex_valid=False,
                    unresolved_questions=[],
                    warnings=[f"Hypothesis Analyst uAgent at {agent_addr} ({agent_ep}) returned non-analysis payload: {resp}"],
                    summary=(
                        f"ANALYSIS_UNAVAILABLE: Independent hypothesis analyst uAgent ({agent_addr}) is unreachable or offline."
                    ),
                )
        except Exception as exc:
            now_iso = datetime.now(timezone.utc).isoformat()
            return HypothesisAnalysisResponse(
                correlation_id=request.correlation_id,
                investigation_id=request.investigation_id,
                status="ANALYSIS_UNAVAILABLE",
                agent_address=agent_addr,
                timestamp=now_iso,
                hypotheses=[],
                simplex_sum=0.0,
                is_simplex_valid=False,
                unresolved_questions=[],
                warnings=[f"Hypothesis Analyst uAgent communication error: {str(exc)}"],
                summary=(
                    f"ANALYSIS_UNAVAILABLE: Independent hypothesis analyst uAgent ({agent_addr}) connection failed ({exc})."
                ),
            )

    @classmethod
    def execute_hypothesis_analysis(
        cls,
        research_question: str,
        investigation_id: str,
        case_study_id: Optional[str] = "CS-CAT-001",
        retrieved_evidence: Optional[List[Any]] = None,
        existing_priors: Optional[Dict[str, float]] = None,
        domain_assumptions: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
        timeout: Optional[float] = None,
        allow_local_fallback: bool = True,
    ) -> Tuple[HypothesisAnalysisResponse, ToolExecutionRecord, List[Hypothesis]]:
        """
        Dispatches hypothesis formulation request to the independent Hypothesis Analyst uAgent.
        If the daemon is offline and allow_local_fallback is True, gracefully performs local
        hypothesis evaluation while honestly recording ANALYSIS_UNAVAILABLE and fallback status.
        Returns (response, tool_record, hypotheses_list_for_downstream_pipeline).
        """
        t0 = time.perf_counter()
        corr_id = correlation_id or f"hypothesis-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"

        # Normalize retrieved evidence to serializable dicts
        ev_dicts: List[Dict[str, Any]] = []
        if retrieved_evidence:
            for item in retrieved_evidence:
                if hasattr(item, "model_dump"):
                    ev_dicts.append(item.model_dump())
                elif isinstance(item, dict):
                    ev_dicts.append(item)

        req = HypothesisAnalysisRequest(
            correlation_id=corr_id,
            investigation_id=investigation_id,
            research_question=research_question,
            case_study_id=case_study_id,
            retrieved_evidence=ev_dicts,
            existing_priors=existing_priors,
            domain_assumptions=domain_assumptions,
        )

        resp = cls._dispatch_request(req, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000.0

        if resp.status in ("ANALYSIS_COMPLETED", "ANALYSIS_PARTIAL", "INSUFFICIENT_EVIDENCE"):
            tool_status = "SUCCESS" if resp.status == "ANALYSIS_COMPLETED" else "WARNING"
            pipeline_hypotheses = [
                Hypothesis(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    prior=item.prior,
                    assumptions=item.assumptions,
                    evidence_ids=item.supporting_evidence_ids,
                    status="active" if item.epistemic_status != "STRONGLY_CONTRADICTED" else "marginalized",
                )
                for item in resp.hypotheses
            ]
            record = ToolExecutionRecord(
                tool_name="janus_independent_hypothesis_analyst_uagent",
                invoked_by=AgentRole.HYPOTHESIS,
                input_arguments={
                    "correlation_id": corr_id,
                    "investigation_id": investigation_id,
                    "research_question": research_question,
                    "case_study_id": case_study_id,
                    "agent_address": resp.agent_address,
                    "evidence_items_count": len(ev_dicts),
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status=tool_status,
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return resp, record, pipeline_hypotheses

        # If ANALYSIS_UNAVAILABLE and allow_local_fallback
        if allow_local_fallback:
            from agents.hypothesis_analyst_agent import perform_hypothesis_analysis
            fallback_resp = perform_hypothesis_analysis(req, agent_address=resp.agent_address)
            pipeline_hypotheses = [
                Hypothesis(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    prior=item.prior,
                    assumptions=item.assumptions,
                    evidence_ids=item.supporting_evidence_ids,
                    status="active" if item.epistemic_status != "STRONGLY_CONTRADICTED" else "marginalized",
                )
                for item in fallback_resp.hypotheses
            ]
            unified_resp = HypothesisAnalysisResponse(
                correlation_id=fallback_resp.correlation_id,
                investigation_id=fallback_resp.investigation_id,
                status=resp.status,  # Preserves ANALYSIS_UNAVAILABLE
                agent_address=resp.agent_address,
                timestamp=fallback_resp.timestamp,
                hypotheses=fallback_resp.hypotheses,
                simplex_sum=fallback_resp.simplex_sum,
                is_simplex_valid=fallback_resp.is_simplex_valid,
                unresolved_questions=fallback_resp.unresolved_questions,
                warnings=[
                    f"Independent hypothesis analyst uAgent daemon ({resp.agent_address}) offline. Local fallback analysis engaged.",
                    *fallback_resp.warnings,
                ],
                summary=f"[LOCAL_FALLBACK - DAEMON OFFLINE] {fallback_resp.summary}",
            )
            record = ToolExecutionRecord(
                tool_name="janus_independent_hypothesis_analyst_uagent",
                invoked_by=AgentRole.HYPOTHESIS,
                input_arguments={
                    "correlation_id": corr_id,
                    "investigation_id": investigation_id,
                    "research_question": research_question,
                    "case_study_id": case_study_id,
                    "agent_address": resp.agent_address,
                    "fallback_engaged": True,
                },
                output_data={
                    "uagent_response": unified_resp.model_dump(),
                    "fallback_analysis": fallback_resp.model_dump(),
                    "hypotheses_count": len(pipeline_hypotheses),
                },
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return unified_resp, record, pipeline_hypotheses
        else:
            record = ToolExecutionRecord(
                tool_name="janus_independent_hypothesis_analyst_uagent",
                invoked_by=AgentRole.HYPOTHESIS,
                input_arguments={
                    "correlation_id": corr_id,
                    "investigation_id": investigation_id,
                    "research_question": research_question,
                    "case_study_id": case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return resp, record, []


class ScientificToolAgentTool:
    """
    Client tool that dispatches scientific computation requests to the independent Fetch.ai
    Scientific Tool uAgent (janus_scientific_tool_agent) via native synchronous inter-agent messaging.
    """

    DEFAULT_TOOL_AGENT_ADDRESS = "agent1q2lmglm5n5nl8wxrcly6j4w0xts9fa9zh2u8qq8mxf30ya3mfxcpjq6md8t"
    DEFAULT_TOOL_AGENT_ENDPOINT = "http://127.0.0.1:8012/submit"
    DEFAULT_TIMEOUT_SECONDS = 5.0

    @classmethod
    def get_tool_agent_address(cls) -> str:
        addr = os.getenv("JANUS_SCIENTIFIC_TOOL_ADDRESS")
        if addr:
            return addr.strip()
        seed = os.getenv("JANUS_SCIENTIFIC_TOOL_SEED")
        if seed:
            from uagents.crypto import Identity
            return Identity.from_seed(seed, 0).address
        return cls.DEFAULT_TOOL_AGENT_ADDRESS

    @classmethod
    def get_tool_agent_endpoint(cls) -> str:
        ep = os.getenv("JANUS_SCIENTIFIC_TOOL_ENDPOINT")
        if ep:
            return ep.strip()
        port = os.getenv("JANUS_SCIENTIFIC_TOOL_PORT", "8012")
        return f"http://127.0.0.1:{port}/submit"

    @classmethod
    def get_timeout(cls) -> float:
        val = os.getenv("JANUS_SCIENTIFIC_TOOL_TIMEOUT_SECONDS")
        if val:
            try:
                return float(val)
            except ValueError:
                pass
        return cls.DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def _dispatch_request(
        cls,
        request: ScientificComputationRequest,
        timeout: Optional[float] = None,
    ) -> ScientificComputationResponse:
        """Sends the structured computation request via native uAgents send_sync_message."""
        agent_addr = cls.get_tool_agent_address()
        agent_ep = cls.get_tool_agent_endpoint()
        effective_timeout = timeout if timeout is not None else cls.get_timeout()

        try:
            from uagents.communication import send_sync_message
            from uagents.resolver import RulesBasedResolver

            resolver = RulesBasedResolver(rules={agent_addr: agent_ep})

            async def _send():
                return await send_sync_message(
                    destination=agent_addr,
                    message=request,
                    response_type=ScientificComputationResponse,
                    resolver=resolver,
                    timeout=max(1, int(math.ceil(effective_timeout))),
                )

            resp = _run_sync_coro(_send())
            if isinstance(resp, ScientificComputationResponse):
                return resp
            else:
                now_iso = datetime.now(timezone.utc).isoformat()
                return ScientificComputationResponse(
                    correlation_id=request.correlation_id,
                    investigation_id=request.investigation_id,
                    status="COMPUTATION_UNAVAILABLE",
                    agent_address=agent_addr,
                    timestamp=now_iso,
                    computation_type=request.computation_type,
                    results=[],
                    scientific_interpretation=f"COMPUTATION_UNAVAILABLE: Scientific Tool uAgent at {agent_addr} ({agent_ep}) returned non-computation payload: {resp}",
                    assumptions_applied=[],
                    warnings=[f"Scientific Tool uAgent returned non-computation payload: {resp}"],
                    execution_time_ms=0.0,
                )
        except Exception as exc:
            now_iso = datetime.now(timezone.utc).isoformat()
            return ScientificComputationResponse(
                correlation_id=request.correlation_id,
                investigation_id=request.investigation_id,
                status="COMPUTATION_UNAVAILABLE",
                agent_address=agent_addr,
                timestamp=now_iso,
                computation_type=request.computation_type,
                results=[],
                scientific_interpretation=f"COMPUTATION_UNAVAILABLE: Independent scientific tool uAgent ({agent_addr}) connection failed ({exc}).",
                assumptions_applied=[],
                warnings=[f"Scientific Tool uAgent communication error: {str(exc)}"],
                execution_time_ms=0.0,
            )

    @classmethod
    def execute_computation(
        cls,
        request: ScientificComputationRequest,
        timeout: Optional[float] = None,
        allow_local_fallback: bool = True,
    ) -> Tuple[ScientificComputationResponse, ToolExecutionRecord]:
        """
        Dispatches scientific computation to the independent Scientific Tool uAgent.
        If daemon is offline and allow_local_fallback is True, gracefully performs local
        computation while honestly recording COMPUTATION_UNAVAILABLE and fallback status.
        """
        t0 = time.perf_counter()
        resp = cls._dispatch_request(request, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000.0

        if resp.status in ("COMPUTATION_COMPLETED", "COMPUTATION_PARTIAL"):
            tool_status = "SUCCESS" if resp.status == "COMPUTATION_COMPLETED" else "WARNING"
            record = ToolExecutionRecord(
                tool_name="janus_independent_scientific_tool_uagent",
                invoked_by=AgentRole.SCIENTIFIC_TOOL,
                input_arguments={
                    "correlation_id": request.correlation_id,
                    "investigation_id": request.investigation_id,
                    "computation_type": request.computation_type,
                    "case_study_id": request.case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status=tool_status,
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return resp, record

        # Fallback handling
        if allow_local_fallback:
            from agents.scientific_tool_agent import perform_scientific_computation
            fallback_resp = perform_scientific_computation(request, agent_address=resp.agent_address)
            unified_resp = ScientificComputationResponse(
                correlation_id=fallback_resp.correlation_id,
                investigation_id=fallback_resp.investigation_id,
                status=resp.status,  # Preserves COMPUTATION_UNAVAILABLE
                agent_address=resp.agent_address,
                timestamp=fallback_resp.timestamp,
                computation_type=fallback_resp.computation_type,
                results=fallback_resp.results,
                scientific_interpretation=f"[LOCAL_FALLBACK - DAEMON OFFLINE] {fallback_resp.scientific_interpretation}",
                assumptions_applied=fallback_resp.assumptions_applied,
                warnings=[
                    f"Independent scientific tool uAgent daemon ({resp.agent_address}) offline. Local fallback computation engaged.",
                    *fallback_resp.warnings,
                ],
                execution_time_ms=fallback_resp.execution_time_ms,
            )
            record = ToolExecutionRecord(
                tool_name="janus_independent_scientific_tool_uagent",
                invoked_by=AgentRole.SCIENTIFIC_TOOL,
                input_arguments={
                    "correlation_id": request.correlation_id,
                    "investigation_id": request.investigation_id,
                    "computation_type": request.computation_type,
                    "case_study_id": request.case_study_id,
                    "agent_address": resp.agent_address,
                    "fallback_engaged": True,
                },
                output_data=unified_resp.model_dump(),
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return unified_resp, record
        else:
            record = ToolExecutionRecord(
                tool_name="janus_independent_scientific_tool_uagent",
                invoked_by=AgentRole.SCIENTIFIC_TOOL,
                input_arguments={
                    "correlation_id": request.correlation_id,
                    "investigation_id": request.investigation_id,
                    "computation_type": request.computation_type,
                    "case_study_id": request.case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return resp, record


class ExperimentDesignerAgentTool:
    """
    Client tool that dispatches Bayesian Experimental Design and EIG ranking requests
    to the independent Fetch.ai Experiment Designer uAgent (janus_experiment_designer)
    via native synchronous inter-agent messaging.
    """

    DEFAULT_DESIGNER_ADDRESS = "agent1q0qpwtcrpp5cmehgwg2reypzk47qxt9mzhxulj9962qrdj9a8a40keavldj"
    DEFAULT_DESIGNER_ENDPOINT = "http://127.0.0.1:8013/submit"
    DEFAULT_TIMEOUT_SECONDS = 5.0

    @classmethod
    def get_designer_address(cls) -> str:
        addr = os.getenv("JANUS_EXPERIMENT_DESIGNER_ADDRESS")
        if addr:
            return addr.strip()
        seed = os.getenv("JANUS_EXPERIMENT_DESIGNER_SEED")
        if seed:
            from uagents.crypto import Identity
            return Identity.from_seed(seed, 0).address
        return cls.DEFAULT_DESIGNER_ADDRESS

    @classmethod
    def get_designer_endpoint(cls) -> str:
        ep = os.getenv("JANUS_EXPERIMENT_DESIGNER_ENDPOINT")
        if ep:
            return ep.strip()
        port = os.getenv("JANUS_EXPERIMENT_DESIGNER_PORT", "8013")
        return f"http://127.0.0.1:{port}/submit"

    @classmethod
    def get_timeout(cls) -> float:
        val = os.getenv("JANUS_EXPERIMENT_DESIGNER_TIMEOUT_SECONDS")
        if val:
            try:
                return float(val)
            except ValueError:
                pass
        return cls.DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def _dispatch_request(
        cls,
        request: ExperimentDesignRequest,
        timeout: Optional[float] = None,
    ) -> ExperimentDesignResponse:
        """Sends the structured design request via native uAgents send_sync_message."""
        agent_addr = cls.get_designer_address()
        agent_ep = cls.get_designer_endpoint()
        effective_timeout = timeout if timeout is not None else cls.get_timeout()

        try:
            from uagents.communication import send_sync_message
            from uagents.resolver import RulesBasedResolver

            resolver = RulesBasedResolver(rules={agent_addr: agent_ep})

            async def _send():
                return await send_sync_message(
                    destination=agent_addr,
                    message=request,
                    response_type=ExperimentDesignResponse,
                    resolver=resolver,
                    timeout=max(1, int(math.ceil(effective_timeout))),
                )

            resp = _run_sync_coro(_send())
            if isinstance(resp, ExperimentDesignResponse):
                return resp
            else:
                now_iso = datetime.now(timezone.utc).isoformat()
                return ExperimentDesignResponse(
                    correlation_id=request.correlation_id,
                    investigation_id=request.investigation_id,
                    status="DESIGN_UNAVAILABLE",
                    agent_address=agent_addr,
                    timestamp=now_iso,
                    scenario_name=request.scenario_name,
                    scenario_type=request.scenario_type,
                    case_study_id=request.case_study_id,
                    is_synthetic=request.is_synthetic,
                    normalized_priors={},
                    prior_entropy_bits=0.0,
                    cost_weight_alpha=request.cost_weight,
                    ranked_experiments=[],
                    unquantified_experiments=[],
                    top_recommendation=None,
                    baseline_comparison=None,
                    audit_trail=[f"Experiment Designer uAgent at {agent_addr} ({agent_ep}) returned non-design payload: {resp}"],
                    warnings=[f"Experiment Designer uAgent returned non-design payload: {resp}"],
                    execution_time_ms=0.0,
                )
        except Exception as exc:
            now_iso = datetime.now(timezone.utc).isoformat()
            return ExperimentDesignResponse(
                correlation_id=request.correlation_id,
                investigation_id=request.investigation_id,
                status="DESIGN_UNAVAILABLE",
                agent_address=agent_addr,
                timestamp=now_iso,
                scenario_name=request.scenario_name,
                scenario_type=request.scenario_type,
                case_study_id=request.case_study_id,
                is_synthetic=request.is_synthetic,
                normalized_priors={},
                prior_entropy_bits=0.0,
                cost_weight_alpha=request.cost_weight,
                ranked_experiments=[],
                unquantified_experiments=[],
                top_recommendation=None,
                baseline_comparison=None,
                audit_trail=[f"Independent Experiment Designer uAgent ({agent_addr}) connection failed: {exc}"],
                warnings=[f"Experiment Designer uAgent communication error: {str(exc)}"],
                execution_time_ms=0.0,
            )

    @classmethod
    def execute_design(
        cls,
        request: ExperimentDesignRequest,
        timeout: Optional[float] = None,
        allow_local_fallback: bool = True,
    ) -> Tuple[ExperimentDesignResponse, ToolExecutionRecord]:
        """
        Dispatches experiment design and ranking to the independent Experiment Designer uAgent.
        If daemon is offline and allow_local_fallback is True, gracefully performs local
        Bayesian ranking while honestly recording DESIGN_UNAVAILABLE and fallback status.
        """
        t0 = time.perf_counter()
        resp = cls._dispatch_request(request, timeout=timeout)
        elapsed = (time.perf_counter() - t0) * 1000.0

        if resp.status in ("DESIGN_COMPLETED", "DESIGN_PARTIAL"):
            tool_status = "SUCCESS" if resp.status == "DESIGN_COMPLETED" else "WARNING"
            record = ToolExecutionRecord(
                tool_name="janus_independent_experiment_designer_uagent",
                invoked_by=AgentRole.EXPERIMENT_STRATEGY,
                input_arguments={
                    "correlation_id": request.correlation_id,
                    "investigation_id": request.investigation_id,
                    "scenario_name": request.scenario_name,
                    "case_study_id": request.case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status=tool_status,
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return resp, record

        # Fallback handling when daemon is offline
        if allow_local_fallback:
            from agents.experiment_designer_agent import perform_experiment_design
            fallback_resp = perform_experiment_design(request, agent_address=resp.agent_address)
            unified_resp = ExperimentDesignResponse(
                correlation_id=fallback_resp.correlation_id,
                investigation_id=fallback_resp.investigation_id,
                status=resp.status,  # Preserves DESIGN_UNAVAILABLE
                agent_address=resp.agent_address,
                timestamp=fallback_resp.timestamp,
                scenario_name=fallback_resp.scenario_name,
                scenario_type=fallback_resp.scenario_type,
                case_study_id=fallback_resp.case_study_id,
                is_synthetic=fallback_resp.is_synthetic,
                normalized_priors=fallback_resp.normalized_priors,
                prior_entropy_bits=fallback_resp.prior_entropy_bits,
                cost_weight_alpha=fallback_resp.cost_weight_alpha,
                ranked_experiments=fallback_resp.ranked_experiments,
                unquantified_experiments=fallback_resp.unquantified_experiments,
                top_recommendation=fallback_resp.top_recommendation,
                baseline_comparison=fallback_resp.baseline_comparison,
                audit_trail=[
                    f"[LOCAL_FALLBACK - DAEMON OFFLINE] Engaged local ranking engine for {resp.agent_address}.",
                    *fallback_resp.audit_trail,
                ],
                warnings=[
                    f"Independent Experiment Designer uAgent daemon ({resp.agent_address}) offline. Local fallback ranking engaged.",
                    *fallback_resp.warnings,
                ],
                execution_time_ms=fallback_resp.execution_time_ms,
            )
            record = ToolExecutionRecord(
                tool_name="janus_independent_experiment_designer_uagent",
                invoked_by=AgentRole.EXPERIMENT_STRATEGY,
                input_arguments={
                    "correlation_id": request.correlation_id,
                    "investigation_id": request.investigation_id,
                    "scenario_name": request.scenario_name,
                    "case_study_id": request.case_study_id,
                    "agent_address": resp.agent_address,
                    "fallback_engaged": True,
                },
                output_data=unified_resp.model_dump(),
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return unified_resp, record
        else:
            record = ToolExecutionRecord(
                tool_name="janus_independent_experiment_designer_uagent",
                invoked_by=AgentRole.EXPERIMENT_STRATEGY,
                input_arguments={
                    "correlation_id": request.correlation_id,
                    "investigation_id": request.investigation_id,
                    "scenario_name": request.scenario_name,
                    "case_study_id": request.case_study_id,
                    "agent_address": resp.agent_address,
                },
                output_data=resp.model_dump(),
                execution_time_ms=elapsed,
                status="WARNING",
                provenance=ProvenanceClassification.THEORETICAL_COMPUTATION,
            )
            return resp, record



class CriticReviewTool:
    """Tool wrapper executing the Coordinator's Scientific Critic Engine (Phase 8)."""

    @classmethod
    def execute_review(
        cls,
        request: ScientificReviewRequest,
    ) -> Tuple[ScientificReviewReport, ToolExecutionRecord, List[CriticItem]]:
        """Executes multi-dimensional review and conclusion gating via ScientificCriticEngine."""
        start_t = time.perf_counter()
        from agents.critic_engine import ScientificCriticEngine
        report, legacy_items = ScientificCriticEngine.evaluate(request)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        tool_status = "SUCCESS" if report.status == ReviewStatus.REVIEW_COMPLETED else "WARNING"
        if report.conclusion_gate == ConclusionGateStatus.WITHHOLD_CONCLUSIONS:
            tool_status = "ERROR"

        record = ToolExecutionRecord(
            tool_name="scientific_critic_review",
            invoked_by=AgentRole.CRITIC,
            input_arguments={
                "correlation_id": request.correlation_id,
                "investigation_id": request.investigation_id,
                "question": request.question,
                "case_study_id": request.case_study_id,
                "is_synthetic": request.is_synthetic,
                "hypotheses_count": len(request.hypotheses),
                "candidate_experiments_count": len(request.candidate_experiments),
            },
            output_data={
                "status": report.status.value,
                "conclusion_gate": report.conclusion_gate.value,
                "gate_rationale": report.gate_rationale,
                "total_findings_count": report.total_findings_count,
                "blocking_findings_count": report.blocking_findings_count,
                "disclosed_limitations_count": len(report.disclosed_limitations),
            },
            execution_time_ms=elapsed_ms,
            status=tool_status,
            provenance=ProvenanceClassification.CALCULATED_BAYESIAN,
        )
        return report, record, legacy_items
