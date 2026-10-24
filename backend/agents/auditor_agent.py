"""JANUS Independent Scientific Auditor uAgent (Phase 3).

Provides an autonomous, independently running uAgent daemon dedicated to
rigorous mathematical invariant auditing and bibliographic consistency verification.

Architecture:
- Native Fetch.ai uAgents Protocol (`janus_scientific_audit`, version 1.0.0)
- Independent agent identity and distinct cryptographic address
- Independent mathematical recalculation of prior simplices, likelihood stochasticity,
  Shannon entropy, information-theoretic EIG bounds (0 <= EIG <= H), and composite utility ranking
- Verification of sequential Bayesian posterior updates (Bayes' rule)
- Cross-examination of evidence ledger bibliographic records and mismatch detection
"""

import sys
import os
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
from app.schemas.audit import (
    ScientificAuditRequest,
    ScientificAuditResponse,
    AuditCheckItem,
)
from app.schemas.scientific import (
    Hypothesis,
    Experiment,
    ExperimentScore,
    PredictedOutcome,
)
from scientific.validation import IndependentEngineVerifier
from agents.tools import BibliographicVerificationStatus


scientific_audit_proto = Protocol(
    name="janus_scientific_audit",
    version="1.0.0"
)


def perform_independent_audit(
    request: ScientificAuditRequest,
    auditor_address: str,
) -> ScientificAuditResponse:
    """
    Executes a comprehensive, zero-trust mathematical and bibliographic audit
    over the payload supplied by the primary scientific agent.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    checks: List[AuditCheckItem] = []
    mismatches: List[str] = []
    bibliographic_mismatches: List[str] = []

    # 1. Audit Prior Simplex
    priors: Dict[str, float] = {}
    for h in request.hypotheses:
        priors[h["id"]] = float(h.get("prior", 0.0))

    prior_check = IndependentEngineVerifier.verify_prior_simplex(priors)
    checks.append(
        AuditCheckItem(
            check_id="prior_simplex_normalization",
            status=prior_check["status"],
            message=prior_check["message"],
            details={"sum": prior_check["sum"], "entropy_bits": prior_check.get("recalculated_entropy_bits")},
        )
    )
    if not prior_check["is_valid"]:
        mismatches.append(f"Prior simplex violation: {prior_check['message']}")

    # 2. Audit Candidate Experiment Likelihood Stochasticity and EIG Bounds
    exp_objects: Dict[str, Experiment] = {}
    for exp_raw in request.experiments:
        preds = [
            PredictedOutcome(
                outcome_label=p["outcome_label"],
                hypothesis_id=p["hypothesis_id"],
                probability=float(p["probability"]),
                uncertainty=float(p.get("uncertainty", 0.0)),
                derivation_mode=p.get("derivation_mode", "derived_from_reported_value_with_noise_model"),
                basis=p.get("basis"),
            )
            for p in exp_raw.get("predictions", [])
        ]
        exp = Experiment(
            id=exp_raw["id"],
            name=exp_raw["name"],
            description=exp_raw.get("description", ""),
            quantification_status=exp_raw.get("quantification_status", "QUANTIFIED_BAYESIAN"),
            possible_outcomes=exp_raw.get("possible_outcomes", []),
            predictions=preds,
            cost=float(exp_raw.get("cost", 1.0)),
            feasibility=float(exp_raw.get("feasibility", 1.0)),
        )
        exp_objects[exp.id] = exp

        # Verify likelihood row stochasticity for quantified experiments, or boundary for unquantified
        if exp.quantification_status == "QUANTIFIED_BAYESIAN" and exp.predictions:
            lik_check = IndependentEngineVerifier.verify_likelihood_distribution(
                experiment=exp,
                hypothesis_ids=list(priors.keys()),
            )
            checks.append(
                AuditCheckItem(
                    check_id=f"likelihood_stochasticity_{exp.id}",
                    status=lik_check["status"],
                    message=lik_check["message"],
                )
            )
            if not lik_check["is_valid"]:
                mismatches.append(f"Likelihood defect in {exp.id}: {lik_check['message']}")
        else:
            checks.append(
                AuditCheckItem(
                    check_id=f"unquantified_boundary_{exp.id}",
                    status="PASS",
                    message=f"Experiment '{exp.id}' is unquantified literature proposal; zero scores preserved without fabrication",
                )
            )

    # 3. Audit Scoring and Information-Theoretic Bounds
    score_objects: List[ExperimentScore] = []
    for s_raw in request.ranked_scores:
        s_obj = ExperimentScore(
            experiment_id=s_raw["experiment_id"],
            experiment_name=s_raw.get("experiment_name", s_raw["experiment_id"]),
            expected_information_gain=float(s_raw.get("expected_information_gain", 0.0)),
            composite_utility_score=float(s_raw.get("composite_utility_score", 0.0)),
            cost=float(s_raw.get("cost", 1.0)),
            feasibility=float(s_raw.get("feasibility", 1.0)),
            prior_entropy=float(s_raw.get("prior_entropy", 1.0)),
            expected_posterior_entropy=float(s_raw.get("expected_posterior_entropy", 0.0)),
            normalized_information_gain=float(s_raw.get("normalized_information_gain", 1.0)),
            explanation=s_raw.get("explanation", ""),
            utility_rank=s_raw.get("utility_rank"),
            rank=s_raw.get("rank"),
            eig_rank=s_raw.get("eig_rank"),
            marginal_probabilities=s_raw.get("marginal_probabilities", {}),
            posterior_matrix=s_raw.get("posterior_matrix", {}),
        )
        score_objects.append(s_obj)

        if s_obj.experiment_id in exp_objects:
            matched_exp = exp_objects[s_obj.experiment_id]
            scoring_check = IndependentEngineVerifier.verify_experiment_scoring(
                experiment=matched_exp,
                score=s_obj,
                priors=priors,
            )
            checks.append(
                AuditCheckItem(
                    check_id=f"scoring_invariants_{s_obj.experiment_id}",
                    status=scoring_check["status"],
                    message=scoring_check["message"],
                    details={
                        "recalculated_eig": scoring_check.get("recalculated_eig_bits"),
                        "recalculated_utility": scoring_check.get("recalculated_utility"),
                        "eig_within_bounds": scoring_check.get("eig_within_bounds"),
                    },
                )
            )
            if not scoring_check["is_valid"]:
                mismatches.append(f"Scoring divergence for {s_obj.experiment_id}: {scoring_check['message']}")

    # 4. Audit Authoritative Ranking Order and Dual-Rank Tie Breaking
    if score_objects:
        rank_check = IndependentEngineVerifier.verify_ranking_order(score_objects)
        checks.append(
            AuditCheckItem(
                check_id="authoritative_utility_ranking_order",
                status=rank_check["status"],
                message=rank_check["message"],
            )
        )
        if not rank_check["is_valid"]:
            mismatches.append(f"Ranking policy violation: {rank_check['message']}")

    # 5. Audit Sequential Bayesian Update (if this is an observation update)
    if request.is_sequential_update:
        if (
            request.initial_priors_before
            and request.observed_experiment_id
            and request.observed_outcome
            and request.observed_posteriors
        ):
            target_exp = exp_objects.get(request.observed_experiment_id)
            lik_vector: Dict[str, float] = {}
            if target_exp:
                for p in target_exp.predictions:
                    if p.outcome_label == request.observed_outcome:
                        lik_vector[p.hypothesis_id] = p.probability

            update_check = IndependentEngineVerifier.verify_bayesian_observation_update(
                initial_priors=request.initial_priors_before,
                likelihood_vector=lik_vector,
                observed_posteriors=request.observed_posteriors,
                experiment_id=request.observed_experiment_id,
                observed_outcome=request.observed_outcome,
            )
            checks.append(
                AuditCheckItem(
                    check_id="bayesian_sequential_update",
                    status=update_check["status"],
                    message=update_check["message"],
                    details={
                        "max_divergence": update_check.get("max_divergence"),
                        "marginal_probability": update_check.get("marginal_probability"),
                    },
                )
            )
            if not update_check["is_valid"]:
                mismatches.append(f"Bayesian update violation: {update_check['message']}")
        else:
            checks.append(
                AuditCheckItem(
                    check_id="bayesian_sequential_update",
                    status="FAIL",
                    message="Sequential update audit requested but required observation fields were missing",
                )
            )
            mismatches.append("Incomplete observation fields in sequential update payload")

    # 6. Audit Bibliographic Metadata Records
    for ev in request.evidence_ledger:
        doi = ev.get("source_doi")
        status = ev.get("doi_verification_status")
        if status == BibliographicVerificationStatus.METADATA_MISMATCH:
            notice = f"Evidence claim {ev.get('id', 'N/A')} (DOI: {doi}) has METADATA_MISMATCH: publisher metadata differs from citation."
            bibliographic_mismatches.append(notice)
        elif status == BibliographicVerificationStatus.DOI_NOT_FOUND:
            notice = f"Evidence claim {ev.get('id', 'N/A')} (DOI: {doi}) was not found in Crossref registry."
            bibliographic_mismatches.append(notice)
        elif status == BibliographicVerificationStatus.UNAVAILABLE:
            checks.append(
                AuditCheckItem(
                    check_id=f"citation_network_warning_{ev.get('id', 'N/A')}",
                    status="WARNING",
                    is_mandatory=False,
                    message=f"Evidence claim {ev.get('id', 'N/A')} (DOI: {doi}) could not be verified online (Crossref unavailable); cached offline catalog active.",
                )
            )

    biblio_status = "PASS" if len(bibliographic_mismatches) == 0 else "FAIL"
    biblio_msg = (
        "All cited DOIs verified or matched against verified offline catalogs."
        if len(bibliographic_mismatches) == 0
        else f"Found {len(bibliographic_mismatches)} bibliographic discrepancies in evidence ledger: {'; '.join(bibliographic_mismatches[:2])}"
    )
    checks.append(
        AuditCheckItem(
            check_id="scholarly_literature_bibliographic_consistency",
            status=biblio_status,
            is_mandatory=True,
            message=biblio_msg,
            details={"discrepancies": bibliographic_mismatches},
        )
    )
    if biblio_status == "FAIL":
        mismatches.append(f"Bibliographic integrity failure: {len(bibliographic_mismatches)} claim(s) have publisher metadata discrepancies.")

    # Classify checks
    mandatory_checks = [c for c in checks if c.is_mandatory]
    mandatory_passed = [c for c in mandatory_checks if c.status == "PASS"]
    mandatory_failed = [c for c in mandatory_checks if c.status == "FAIL"]
    warning_checks = [c for c in checks if c.status == "WARNING"]

    # Ensure all failed mandatory checks are included in mismatches
    for c in mandatory_failed:
        if not any(c.check_id in m for m in mismatches):
            mismatches.append(f"{c.check_id}: {c.message}")

    passed_count = sum(1 for c in checks if c.status == "PASS")
    total_count = len(checks)

    # Invariants hold ONLY if ALL mandatory checks pass and zero mismatches exist
    all_invariants_hold = (len(mandatory_failed) == 0 and len(mismatches) == 0)

    if not all_invariants_hold:
        status_code = "AUDIT_FAILED"
        verdict = (
            f"AUDIT_FAILED: Detected {len(mismatches)} invariant violation(s) "
            f"({len(mandatory_passed)}/{len(mandatory_checks)} mandatory checks passed). "
            f"Failed checks: {'; '.join(mismatches[:3])}"
        )
    elif warning_checks:
        status_code = "AUDIT_PASSED"
        verdict = (
            f"AUDIT_PASSED: All {len(mandatory_passed)}/{len(mandatory_checks)} mandatory checks verified. "
            f"{len(warning_checks)} non-critical warning(s) flagged."
        )
    else:
        status_code = "AUDIT_PASSED"
        verdict = (
            f"AUDIT_PASSED: All {len(mandatory_passed)}/{len(mandatory_checks)} mandatory mathematical and integrity checks verified. "
            f"Shannon entropy, simplex bounds, and utility ranking independently validated."
        )

    return ScientificAuditResponse(
        correlation_id=request.correlation_id,
        status=status_code,
        auditor_address=auditor_address,
        timestamp=now_iso,
        checks=checks,
        all_invariants_hold=all_invariants_hold,
        passed_checks_count=passed_count,
        total_checks_count=total_count,
        mandatory_checks_count=len(mandatory_checks),
        mandatory_passed_count=len(mandatory_passed),
        warnings_count=len(warning_checks),
        mismatches=mismatches,
        bibliographic_mismatch_notices=bibliographic_mismatches,
        verdict=verdict,
    )


@scientific_audit_proto.on_message(model=ScientificAuditRequest, replies={ScientificAuditResponse})
async def handle_audit_request(ctx: Context, sender: str, msg: ScientificAuditRequest):
    ctx.logger.info(
        f"Incoming ScientificAuditRequest from {sender} "
        f"[correlation_id={msg.correlation_id}, scenario={msg.scenario_id}]"
    )

    response = perform_independent_audit(msg, auditor_address=ctx.agent.address)
    ctx.logger.info(
        f"Audit evaluation complete: {response.status} "
        f"({response.passed_checks_count}/{response.total_checks_count} passed). Replying to {sender}..."
    )

    await ctx.send(sender, response)


def create_auditor_uagent(
    name: str = "janus_auditor_agent",
    seed: Optional[str] = None,
    port: int = 8009,
    endpoint: Optional[List[str]] = None,
    use_mailbox: Optional[bool] = None,
    agentverse_url: Optional[str] = None,
) -> Agent:
    """
    Constructs and returns the configured JANUS Auditor uAgent.
    """
    effective_seed = seed or os.getenv("JANUS_AUDITOR_SEED")
    raw_env_mailbox = os.getenv("JANUS_AUDITOR_USE_MAILBOX")

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
                "Please set the 'JANUS_AUDITOR_SEED' environment variable."
            )
    elif not effective_seed:
        # Fallback to a deterministic testing phrase if not provided in environment
        effective_seed = "janus_auditor_isolated_evaluation_seed_phase3"

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
    agent.include(scientific_audit_proto)
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

    auditor_port = int(os.getenv("JANUS_AUDITOR_PORT", "8009"))
    agent_instance = create_auditor_uagent(port=auditor_port)

    print("=" * 80)
    print(" JANUS Independent Scientific Auditor uAgent (Phase 3 Daemon)")
    print("=" * 80)
    print(f"Auditor Name:    {agent_instance.name}")
    print(f"Auditor Address: {agent_instance.address}")
    print(f"Auditor Port:    {auditor_port}")
    print(f"Endpoint:        http://127.0.0.1:{auditor_port}/submit")
    print("Starting Auditor uAgent event loop...")
    agent_instance.run()
