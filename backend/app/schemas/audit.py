"""JANUS Multi-Agent Scientific Audit Protocol Schemas (Phase 3).

Defines the structured, strongly-typed contract between the primary JANUS gateway
and the independent Auditor uAgent (janus_auditor_uagent).
Compatible with uAgents native message envelopes and Model inheritance.
"""

from typing import List, Dict, Optional, Any
from uagents import Model


class AuditCheckItem(Model):
    """Result of an individual invariant or bibliographic audit check."""
    check_id: str
    status: str  # "PASS", "FAIL", or "WARNING"
    is_mandatory: bool = True
    message: str
    details: Dict[str, Any] = {}


class ScientificAuditRequest(Model):
    """
    Structured audit request dispatched by the primary JANUS scientific agent
    to the independent auditor agent.
    """
    correlation_id: str
    investigation_id: Optional[str] = None
    scenario_id: str
    hypotheses: List[Dict[str, Any]]
    experiments: List[Dict[str, Any]]
    ranked_scores: List[Dict[str, Any]]
    selected_recommendation: Dict[str, Any]
    evidence_ledger: List[Dict[str, Any]] = []
    is_sequential_update: bool = False
    initial_priors_before: Optional[Dict[str, float]] = None
    observed_experiment_id: Optional[str] = None
    observed_outcome: Optional[str] = None
    observed_posteriors: Optional[Dict[str, float]] = None


class ScientificAuditResponse(Model):
    """
    Structured audit verdict returned by the independent auditor agent
    to the primary JANUS scientific agent.
    """
    correlation_id: str
    status: str  # "AUDIT_PASSED", "AUDIT_FAILED", "AUDIT_UNAVAILABLE"
    auditor_address: str
    timestamp: str
    checks: List[AuditCheckItem] = []
    all_invariants_hold: bool = False
    passed_checks_count: int = 0
    total_checks_count: int = 0
    mandatory_checks_count: int = 0
    mandatory_passed_count: int = 0
    warnings_count: int = 0
    mismatches: List[str] = []
    bibliographic_mismatch_notices: List[str] = []
    verdict: str
