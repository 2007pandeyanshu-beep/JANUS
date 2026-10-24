"""Unit tests for Live Scientific Evidence Verification via Crossref REST API (Workstream A).

Verifies:
- Live/mocked Crossref bibliographic metadata retrieval
- Status classifications: BIBLIOGRAPHIC_VERIFIED_ONLINE, METADATA_MISMATCH, DOI_NOT_FOUND, BIBLIOGRAPHIC_CACHED_OFFLINE, UNAVAILABLE
- Provenance recording (DOI, source, status, mismatch details)
- Scientific boundary disclaimer (bibliographic validation != empirical claim proof)
- Graceful handling of network timeouts, 404s, malformed responses
- Cache lifetime and offline fallback behavior
"""

import pytest
import httpx
from unittest.mock import patch
from app.schemas.scientific import Evidence
from agents.tools import (
    CrossrefValidationTool,
    BibliographicVerificationStatus,
    _CROSSREF_CACHE,
    _CURATED_OFFLINE_CATALOG,
    _normalize_string,
)


@pytest.fixture(autouse=True)
def clear_crossref_cache():
    """Clear in-memory Crossref cache between test runs."""
    _CROSSREF_CACHE.clear()
    yield
    _CROSSREF_CACHE.clear()


def test_normalize_string_helper():
    """Tests whitespace, punctuation, and unicode normalization."""
    raw = "  Low-Temperature   Water-Gas Shift: Reaction Mechanisms!  "
    normalized = _normalize_string(raw)
    assert normalized == "low temperature water gas shift reaction mechanisms"


def test_crossref_verification_successful_match():
    """Tests HTTP 200 where publisher metadata matches expected title and authors."""
    mock_crossref_json = {
        "status": "ok",
        "message": {
            "DOI": "10.1016/j.jcat.2011.01.024",
            "title": ["Pt/CeO2 low-temperature water-gas shift catalysts"],
            "author": [{"family": "Kalamaras"}, {"family": "Idriss"}],
            "container-title": ["Journal of Catalysis"],
            "issued": {"date-parts": [[2011]]},
            "URL": "https://doi.org/10.1016/j.jcat.2011.01.024",
        },
    }

    mock_resp = httpx.Response(status_code=200, json=mock_crossref_json)

    with patch.object(httpx.Client, "get", return_value=mock_resp):
        result = CrossrefValidationTool.verify_doi(
            doi="10.1016/j.jcat.2011.01.024",
            expected_title="Pt/CeO2 low-temperature water gas shift",
            expected_authors=["Kalamaras et al."],
            expected_year=2011,
        )

        assert result["status"] == BibliographicVerificationStatus.BIBLIOGRAPHIC_VERIFIED_ONLINE
        assert result["bibliographic_metadata"]["doi"] == "10.1016/j.jcat.2011.01.024"
        assert result["bibliographic_metadata"]["year"] == 2011
        assert "scientific_boundary" in result
        assert "not that the paper's results support" in result["scientific_boundary"]


def test_crossref_verification_metadata_mismatch():
    """Tests HTTP 200 where publisher metadata contradicts expected title and authors."""
    mock_crossref_json = {
        "status": "ok",
        "message": {
            "DOI": "10.1016/j.jcat.2007.09.006",
            "title": ["Redox behavior of ceria-zirconia mixed oxides"],
            "author": [{"family": "Conesa"}, {"family": "Martinez"}],
            "container-title": ["Journal of Catalysis"],
            "issued": {"date-parts": [[2007]]},
            "URL": "https://doi.org/10.1016/j.jcat.2007.09.006",
        },
    }

    mock_resp = httpx.Response(status_code=200, json=mock_crossref_json)

    with patch.object(httpx.Client, "get", return_value=mock_resp):
        result = CrossrefValidationTool.verify_doi(
            doi="10.1016/j.jcat.2007.09.006",
            expected_title="Formate intermediate operando DRIFTS study on Pt/CeO2",
            expected_authors=["Meunier et al."],
            expected_year=2008,
        )

        assert result["status"] == BibliographicVerificationStatus.METADATA_MISMATCH
        assert result["mismatch_details"] is not None


def test_crossref_verification_not_found_fallback_to_offline():
    """Tests HTTP 404 from Crossref falling back to curated offline catalog."""
    test_doi = "10.1039/B611217A"
    assert test_doi in _CURATED_OFFLINE_CATALOG

    mock_resp = httpx.Response(status_code=404)

    with patch.object(httpx.Client, "get", return_value=mock_resp):
        result = CrossrefValidationTool.verify_doi(
            doi=test_doi,
            expected_title="Formate intermediate WGS",
            expected_authors=["Meunier et al."],
        )

        assert result["status"] == BibliographicVerificationStatus.BIBLIOGRAPHIC_CACHED_OFFLINE
        assert result["bibliographic_metadata"]["doi"] == test_doi
        assert "offline" in result["source"].lower()


def test_crossref_verification_timeout_fallback_to_offline():
    """Tests network timeout falling back to curated offline catalog without crashing."""
    test_doi = "10.1016/j.jcat.2011.01.024"

    with patch.object(httpx.Client, "get", side_effect=httpx.TimeoutException("Connection timed out")):
        result = CrossrefValidationTool.verify_doi(
            doi=test_doi,
            expected_title="Pt/CeO2 low-temperature water-gas shift catalysts",
        )

        assert result["status"] == BibliographicVerificationStatus.BIBLIOGRAPHIC_CACHED_OFFLINE
        assert result["bibliographic_metadata"] is not None


def test_crossref_verification_unknown_doi_unresolvable():
    """Tests an invalid DOI not in Crossref and not in offline cache."""
    invalid_doi = "10.9999/nonexistent.study.doi.12345"
    mock_resp = httpx.Response(status_code=404)

    with patch.object(httpx.Client, "get", return_value=mock_resp):
        result = CrossrefValidationTool.verify_doi(doi=invalid_doi)

        assert result["status"] == BibliographicVerificationStatus.DOI_NOT_FOUND
        assert result["bibliographic_metadata"] is None


def test_crossref_verify_evidence_ledger():
    """Tests verifying a full ledger of Evidence items and updating their status fields."""
    evidences = [
        Evidence(
            id="EVD-01",
            title="Spectroscopic identification of Pt-O-Ce active sites in water-gas shift",
            authors=["Rodriguez et al."],
            journal="Science",
            year=2007,
            source="Science 318, 1757-1760 (2007)",
            source_doi="10.1126/science.1150038",
            provenance="empirical_observation",
            summary="DRIFTS and isotopic evidence for Pt-O-Ce active boundary sites in WGS.",
        ),
        Evidence(
            id="EVD-02",
            title="Formate intermediate in low-temperature water-gas shift over Pt/CeO2",
            authors=["Meunier et al."],
            journal="Journal of Catalysis",
            year=2007,
            source="J. Catal. 247, 277-287 (2007)",
            source_doi="10.1016/j.jcat.2007.09.006",
            provenance="empirical_observation",
            summary="Operando spectroscopic study evaluating surface formate decomposition rates.",
        ),
    ]

    mock_resp_map = {
        "10.1126/science.1150038": {
            "status": "ok",
            "message": {
                "DOI": "10.1126/science.1150038",
                "title": ["Spectroscopic identification of Pt-O-Ce active sites in water-gas shift"],
                "author": [{"family": "Rodriguez"}],
                "container-title": ["Science"],
                "issued": {"date-parts": [[2007]]},
                "URL": "https://doi.org/10.1126/science.1150038",
            },
        },
        "10.1016/j.jcat.2007.09.006": {
            "status": "ok",
            "message": {
                "DOI": "10.1016/j.jcat.2007.09.006",
                "title": ["Different title entirely"],
                "author": [{"family": "OtherAuthor"}],
                "container-title": ["Journal of Catalysis"],
                "issued": {"date-parts": [[2007]]},
                "URL": "https://doi.org/10.1016/j.jcat.2007.09.006",
            },
        },
    }

    def fake_get(url, **kwargs):
        for doi, payload in mock_resp_map.items():
            if doi in url:
                return httpx.Response(status_code=200, json=payload)
        return httpx.Response(status_code=404)

    with patch.object(httpx.Client, "get", side_effect=fake_get):
        verified_ledger, record = CrossrefValidationTool.verify_evidence_ledger(evidences)

        assert len(verified_ledger) == 2
        assert verified_ledger[0].doi_verification_status == BibliographicVerificationStatus.BIBLIOGRAPHIC_VERIFIED_ONLINE
        assert verified_ledger[1].doi_verification_status == BibliographicVerificationStatus.METADATA_MISMATCH
        assert verified_ledger[0].bibliographic_metadata is not None
        assert verified_ledger[0].bibliographic_metadata["journal"] == "Science"
        assert record.tool_name == "crossref_bibliographic_verification"
