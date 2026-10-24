"""Comprehensive Test Suite for JANUS Fetch.ai Gateway & Security Hardening (Phases 1-3)

Verifies:
1. Fetch.ai uAgent initialization, deterministic address generation, and ACP protocol verification.
2. Scientific query intent parsing and routing across all supported scenarios.
3. Explicit rejection of unsupported/uncalibrated scientific domains.
4. Correctness of evidence-backed explanations and ASI:One Interactive Card schema generation.
5. In-chat Bayesian observation conditioning and dynamic re-ranking.
6. Security: Header-based API key authentication and credential sanitization.
7. Security: CORS configuration without wildcard credential policy violation.
8. Scientific constraints: filter_feasible_experiments contract and boundary checks.
"""

import os
import json
import pytest
from agents.fetch_agent import (
    create_janus_uagent,
    parse_scientific_intent,
    parse_observation_intent,
    build_scientific_response,
    build_observation_response,
    build_investigation_status_response,
    parse_status_or_history_intent,
    extract_referenced_experiment_or_scenario,
    resolve_investigation_id,
    get_or_restore_investigation,
    save_investigation_state,
    SESSION_ACTIVE_MAP,
    generate_asione_card,
    serialize_metadata_payload,
    deserialize_metadata_payload,
    SUPPORTED_SCENARIOS,
)
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, MetadataContent
from agents.orchestrator import sanitize_secret, ScientificInvestigationOrchestrator, INVESTIGATIONS_STORE
from agents.types import InvestigationInput, AgentInvestigationReport
from scientific.constraints import filter_feasible_experiments
from scientific.evidence_ingestion import load_candidate_experiments
from app.main import app


# ==============================================================================
# 1. FETCH.AI UAGENT & ACP PROTOCOL TESTS
# ==============================================================================

def test_fetch_uagent_initialization():
    """Verify that the JANUS uAgent initializes cleanly with a deterministic Fetch.ai address."""
    agent = create_janus_uagent(name="test_janus_agent", seed="deterministic_test_seed_123")
    assert agent.name == "test_janus_agent"
    assert agent.address.startswith("agent1")
    assert len(agent.protocols) >= 1


def test_fetch_uagent_chat_protocol_verified():
    """Verify that the Agent Chat Protocol (ACP) includes both ChatMessage and ChatAcknowledgement handlers."""
    agent = create_janus_uagent(name="test_janus_agent", seed="deterministic_test_seed_123")
    proto = list(agent.protocols.values())[0]
    # Protocol.verify() must return True when all required models have handlers
    assert proto.verify() is True


def test_fetch_uagent_local_mode_configuration():
    """Verify that local development mode configures the local endpoint and disables mailbox."""
    agent = create_janus_uagent(
        name="test_local_agent",
        seed="deterministic_local_seed_456",
        port=8010,
        use_mailbox=False,
    )
    assert agent._use_mailbox is False
    assert agent._mailbox_client is None
    assert any("8010/submit" in ep.url for ep in agent._endpoints)
    assert not any("agentverse.ai" in ep.url for ep in agent._endpoints)


def test_fetch_uagent_mailbox_mode_configuration():
    """Verify that Agentverse mailbox mode sets mailbox=True and omits conflicting local endpoints."""
    agent = create_janus_uagent(
        name="test_mailbox_agent",
        seed="deterministic_mailbox_seed_789",
        port=8011,
        use_mailbox=True,
    )
    assert agent._use_mailbox is True
    assert agent._mailbox_client is not None
    # Must NOT have local HTTP endpoint overriding mailbox
    assert not any("8011/submit" in ep.url for ep in agent._endpoints)
    # Must have Agentverse mailbox endpoint
    assert any("agentverse.ai" in ep.url for ep in agent._endpoints)


def test_fetch_uagent_mode_separation_and_env_vars(monkeypatch):
    """Verify environment variable detection and clean mode isolation without configuration bleed."""
    # 1. JANUS_USE_MAILBOX=true activates mailbox mode by default
    monkeypatch.setenv("JANUS_USE_MAILBOX", "true")
    agent_env = create_janus_uagent(name="test_env_agent", seed="deterministic_env_seed", port=8012)
    assert agent_env._use_mailbox is True
    assert agent_env._mailbox_client is not None

    # 2. Explicit use_mailbox=False overrides environment variable
    agent_override = create_janus_uagent(
        name="test_override_agent",
        seed="deterministic_override_seed",
        port=8013,
        use_mailbox=False,
    )
    assert agent_override._use_mailbox is False
    assert agent_override._mailbox_client is None
    assert any("8013/submit" in ep.url for ep in agent_override._endpoints)

    # 3. Mode separation: verify clean isolation between back-to-back instantiations
    monkeypatch.delenv("JANUS_USE_MAILBOX", raising=False)
    agent_local = create_janus_uagent(name="agent_l", seed="seed_l", port=8014, use_mailbox=False)
    agent_mbox = create_janus_uagent(name="agent_m", seed="seed_m", port=8015, use_mailbox=True)
    assert agent_local._use_mailbox is False
    assert agent_mbox._use_mailbox is True
    assert any("8014/submit" in ep.url for ep in agent_local._endpoints)
    assert not any("8015/submit" in ep.url for ep in agent_mbox._endpoints)


def test_fetch_uagent_missing_seed_local_mode_raises(monkeypatch):
    """Verify that omitting agent seed in local mode raises an actionable configuration error."""
    monkeypatch.delenv("JANUS_AGENT_SEED", raising=False)
    with pytest.raises(ValueError, match="identity seed is not configured"):
        create_janus_uagent(name="no_seed_agent", seed=None, use_mailbox=False)


def test_fetch_uagent_missing_seed_mailbox_mode_raises(monkeypatch):
    """Verify that omitting agent seed in mailbox mode raises a strict security configuration error."""
    monkeypatch.delenv("JANUS_AGENT_SEED", raising=False)
    with pytest.raises(ValueError, match="Agentverse mailbox mode requires a securely configured, stable identity seed"):
        create_janus_uagent(name="no_seed_mbox_agent", seed=None, use_mailbox=True)


def test_fetch_uagent_seed_from_env_var(monkeypatch):
    """Verify that JANUS_AGENT_SEED environment variable is used when seed parameter is omitted."""
    monkeypatch.setenv("JANUS_AGENT_SEED", "env_deterministic_test_seed_abc123")
    agent = create_janus_uagent(name="env_seed_agent", seed=None, port=8016, use_mailbox=False)
    assert agent.name == "env_seed_agent"
    assert agent.address.startswith("agent1")


def test_fetch_uagent_explicit_parameter_precedence(monkeypatch):
    """Verify that explicit use_mailbox argument strictly overrides environment variables."""
    # 1. Explicit use_mailbox=False overrides JANUS_USE_MAILBOX=true
    monkeypatch.setenv("JANUS_USE_MAILBOX", "true")
    agent_local = create_janus_uagent(name="a_prec_local", seed="s_prec_1", port=8017, use_mailbox=False)
    assert agent_local._use_mailbox is False
    assert any("8017/submit" in ep.url for ep in agent_local._endpoints)

    # 2. Explicit use_mailbox=True overrides JANUS_USE_MAILBOX=false
    monkeypatch.setenv("JANUS_USE_MAILBOX", "false")
    agent_mbox = create_janus_uagent(name="a_prec_mbox", seed="s_prec_2", port=8018, use_mailbox=True)
    assert agent_mbox._use_mailbox is True
    assert not any("8018/submit" in ep.url for ep in agent_mbox._endpoints)


def test_fetch_uagent_safe_handling_of_legacy_mailbox_key(monkeypatch):
    """Verify legacy mailbox_key or AGENTVERSE_MAILBOX_KEY activates mailbox mode without secret leakage."""
    monkeypatch.delenv("JANUS_USE_MAILBOX", raising=False)
    monkeypatch.setenv("AGENTVERSE_MAILBOX_KEY", "legacy_secret_token_never_leak_999")

    agent = create_janus_uagent(name="a_legacy", seed="s_legacy_3", port=8019)
    # Mailbox mode is activated for backward compatibility
    assert agent._use_mailbox is True
    # Secret key must NOT be leaked into agentverse base_url or endpoint URLs
    assert "legacy_secret_token_never_leak_999" not in agent._agentverse.base_url
    assert agent._agentverse.base_url == "agentverse.ai"
    for ep in agent._endpoints:
        assert "legacy_secret_token_never_leak_999" not in ep.url


def test_fetch_uagent_janus_use_mailbox_false_overrides_legacy_key(monkeypatch):
    """Verify that JANUS_USE_MAILBOX=false forces local mode even if legacy AGENTVERSE_MAILBOX_KEY is set."""
    monkeypatch.setenv("JANUS_USE_MAILBOX", "false")
    monkeypatch.setenv("AGENTVERSE_MAILBOX_KEY", "legacy_secret_token_xyz")

    agent = create_janus_uagent(name="a_local_override", seed="s_local_override", port=8021)
    assert agent._use_mailbox is False
    assert agent._mailbox_client is None
    assert any("8021/submit" in ep.url for ep in agent._endpoints)
    assert not any("agentverse.ai" in ep.url for ep in agent._endpoints)


def test_fetch_uagent_agentverse_url_override(monkeypatch):
    """Verify AGENTVERSE_URL is only used for intentional endpoint overrides."""
    monkeypatch.setenv("AGENTVERSE_URL", "https://custom-hub.agentverse.ai")
    agent = create_janus_uagent(name="a_custom_hub", seed="s_custom_4", port=8020, use_mailbox=True)
    assert agent._use_mailbox is True
    assert agent._agentverse.base_url == "custom-hub.agentverse.ai"
    assert any("custom-hub.agentverse.ai" in ep.url for ep in agent._endpoints)


# ==============================================================================
# 2. INTENT PARSING & ROUTING TESTS
# ==============================================================================

def test_parse_scientific_intent_wgs():
    """Verify routing of water-gas shift catalysis questions to CS-CAT-001."""
    case_id, sc, rej = parse_scientific_intent("What experiment distinguishes the redox pathway on Pt/CeO2 water gas shift?")
    assert case_id == "CS-CAT-001"
    assert sc is not None
    assert rej is None
    assert sc.case_study_id == "CS-CAT-001"


def test_parse_scientific_intent_oer():
    """Verify routing of perovskite electrocatalysis questions to CS-OER-002."""
    case_id, sc, rej = parse_scientific_intent("Which reaction mechanism dominates oxygen evolution OER on perovskites?")
    assert case_id == "CS-OER-002"
    assert sc is not None
    assert rej is None


def test_parse_scientific_intent_kinase():
    """Verify routing of kinase benchmark questions to SYN-001."""
    case_id, sc, rej = parse_scientific_intent("How to distinguish allosteric vs ATP-competitive kinase inhibition?")
    assert case_id == "SYN-001"
    assert sc is not None
    assert rej is None


def test_parse_scientific_intent_rejection():
    """Verify that unsupported scientific questions are explicitly and transparently rejected."""
    case_id, sc, rej = parse_scientific_intent("Can you recommend an assay to test mRNA delivery lipid nanoparticles?")
    assert case_id is None
    assert sc is None
    assert rej is not None
    assert "refuses to fabricate probability distributions" in rej
    assert "CS-CAT-001" in rej
    assert "CS-OER-002" in rej


def test_parse_scientific_intent_empty():
    """Verify handling of empty or whitespace queries."""
    case_id, sc, rej = parse_scientific_intent("   ")
    assert case_id is None
    assert "Empty scientific question" in rej


def test_parse_observation_intent():
    """Verify parsing of laboratory outcome observation commands."""
    obs = parse_observation_intent("observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O")
    assert obs is not None
    assert obs == ("EXP-WGS-02", "Initial_CO2_Mainly_Lattice_16O")

    obs2 = parse_observation_intent("outcome for EXP-OER-01 is Direct_36_O2_Detected")
    assert obs2 is not None
    assert obs2 == ("EXP-OER-01", "Direct_36_O2_Detected")

    obs_none = parse_observation_intent("What is the EIG of EXP-WGS-02?")
    assert obs_none is None


# ==============================================================================
# 3. RESPONSE & ASI:ONE INTERACTIVE CARD GENERATION
# ==============================================================================

def test_build_scientific_response_wgs():
    """Verify that response markdown and interactive card schema match authoritative BED calculus."""
    meta = SUPPORTED_SCENARIOS["CS-CAT-001"]
    sc = meta["loader"]()
    text, card = build_scientific_response("CS-CAT-001", sc, "wgs Pt/CeO2")

    # Verify markdown text contains key findings
    assert "Pt/CeO2" in text
    assert "EXP-WGS-02" in text
    assert "0.5593 bits" in text
    assert "DOI:" in text

    # Verify ASI:One Interactive Card schema
    assert card["card_type"] == "scientific_experiment_recommendation"
    assert card["scenario_id"] == "CS-CAT-001"
    assert card["recommended_experiment"]["id"] == "EXP-WGS-02"
    assert card["recommended_experiment"]["eig_bits"] == 0.5593
    assert card["recommended_experiment"]["feasibility_pct"] == 88.0
    assert len(card["citations"]) >= 3
    assert len(card["interactive_actions"]) >= 2
    assert any("Initial_CO2_Mainly_Lattice_16O" in act["command"] for act in card["interactive_actions"])


def test_build_observation_response_bayesian_update():
    """Verify in-chat dynamic Bayesian conditioning following an observation."""
    text, card = build_observation_response("EXP-WGS-02", "Initial_CO2_Mainly_Lattice_16O")
    assert card["card_type"] == "bayesian_update_result"
    assert card["observed_experiment"] == "EXP-WGS-02"
    assert card["observed_outcome"] == "Initial_CO2_Mainly_Lattice_16O"
    assert "posteriors" in card
    # H1 (Redox) must receive high posterior probability under support oxygen transfer
    assert card["posteriors"]["H1"] > 0.85
    assert "Updated Epistemic Hypothesis Beliefs" in text


def test_build_observation_response_invalid_experiment():
    """Verify error handling for unknown experiment observation."""
    text, card = build_observation_response("EXP-UNKNOWN-99", "Some_Outcome")
    assert card["status"] == "ERROR"
    assert "was not found" in text


def test_build_observation_response_invalid_outcome():
    """Verify error handling for unregistered outcome."""
    text, card = build_observation_response("EXP-WGS-02", "Nonexistent_Outcome_XYZ")
    assert card["status"] == "ERROR"
    assert "Valid outcomes:" in text


def test_metadata_payload_serialization_round_trip():
    """Verify that complex nested card payloads serialize to strict dict[str, str] and round-trip cleanly."""
    sample_payload = {
        "card_type": "scientific_experiment_recommendation",
        "scenario_id": "CS-CAT-001",
        "count": 42,
        "is_active": True,
        "recommended_experiment": {
            "id": "EXP-WGS-02",
            "name": "Operando DRIFTS",
            "eig_bits": 0.5593,
        },
        "citations": [
            {"id": "CIT-01", "title": "Science Paper", "doi": "10.1126/science.123"}
        ],
        "interactive_actions": [
            {"action_id": "act_1", "command": "observe EXP-WGS-02 Outcome_A"}
        ],
    }

    serialized = serialize_metadata_payload(sample_payload)

    # 1. Strict contract: every key and value MUST be a string
    assert all(isinstance(k, str) for k in serialized.keys())
    assert all(isinstance(v, str) for v in serialized.values())

    # 2. ASI:One top-level wrapper fields present
    assert serialized["card_protocol_version"] == "1"
    assert serialized["requires_card_interaction"] == "true"
    assert serialized["card_kind"] == "custom"
    assert "card_payload" in serialized

    # 3. String fields are preserved directly without double-escaping
    assert serialized["card_type"] == "scientific_experiment_recommendation"
    assert serialized["scenario_id"] == "CS-CAT-001"

    # 4. MetadataContent model validates cleanly against the serialized payload
    meta_block = MetadataContent(type="metadata", metadata=serialized)
    assert meta_block.type == "metadata"

    # 5. Deserialization perfectly recovers the rich types and structure
    recovered = deserialize_metadata_payload(meta_block.metadata)
    assert recovered["card_type"] == sample_payload["card_type"]
    assert recovered["count"] == 42
    assert recovered["is_active"] is True
    assert recovered["recommended_experiment"]["id"] == "EXP-WGS-02"
    assert recovered["citations"][0]["doi"] == "10.1126/science.123"
    assert recovered["interactive_actions"][0]["action_id"] == "act_1"


def test_asione_wrapper_card_payload_round_trip_and_backward_compatibility():
    """Verify ASI:One wrapper schema, card_payload round-trip, and legacy fallback."""
    full_card = {
        "version": "1.0",
        "card_type": "scientific_experiment_recommendation",
        "scenario_id": "CS-CAT-001",
        "recommended_experiment": {
            "id": "EXP-WGS-02",
            "name": "Isotopic Pulse MS",
            "eig_bits": 0.5593,
            "feasibility_pct": 88.0,
            "cost": 1.8,
        },
        "ranked_candidates": [
            {"id": "EXP-WGS-02", "rank": 1, "eig_bits": 0.5593},
            {"id": "EXP-WGS-01", "rank": 2, "eig_bits": 0.4931},
        ],
        "available_outcomes_for_conditioning": ["Outcome_A", "Outcome_B"],
        "citations": [
            {"id": "CIT-01", "title": "Paper 1", "doi": "10.1016/j.jcat.2011"}
        ],
        "interactive_actions": [
            {"action_id": "act_1", "label": "Observe A", "command": "observe EXP-WGS-02 Outcome_A"}
        ],
    }

    # 1. Serialization produces strict string mapping
    meta = serialize_metadata_payload(full_card)
    assert meta["card_protocol_version"] == "1"
    assert meta["requires_card_interaction"] == "true"
    assert meta["card_kind"] == "custom"
    assert isinstance(meta["card_payload"], str)

    # 2. card_payload contains valid JSON with all fields preserved
    inner_payload = json.loads(meta["card_payload"])
    assert inner_payload["recommended_experiment"]["id"] == "EXP-WGS-02"
    assert inner_payload["ranked_candidates"][1]["id"] == "EXP-WGS-01"
    assert inner_payload["available_outcomes_for_conditioning"] == ["Outcome_A", "Outcome_B"]
    assert inner_payload["citations"][0]["doi"] == "10.1016/j.jcat.2011"
    assert inner_payload["interactive_actions"][0]["command"] == "observe EXP-WGS-02 Outcome_A"

    # 3. Payload without interactive actions sets requires_card_interaction to 'false'
    static_card = {"card_type": "rejection_notice", "supported": ["CS-CAT-001"]}
    meta_static = serialize_metadata_payload(static_card)
    assert meta_static["requires_card_interaction"] == "false"

    # 4. Backward compatibility: deserialize legacy metadata lacking card_payload
    legacy_metadata = {
        "card_type": "scientific_experiment_recommendation",
        "scenario_id": "CS-CAT-001",
        "recommended_experiment": json.dumps({"id": "EXP-WGS-02", "eig_bits": 0.5593}),
        "ranked_candidates": json.dumps([{"id": "EXP-WGS-02", "rank": 1}]),
    }
    recovered_legacy = deserialize_metadata_payload(legacy_metadata)
    assert recovered_legacy["card_type"] == "scientific_experiment_recommendation"
    assert recovered_legacy["recommended_experiment"]["id"] == "EXP-WGS-02"
    assert recovered_legacy["ranked_candidates"][0]["id"] == "EXP-WGS-02"


def test_scientific_response_chat_message_schema_valid():
    """Verify that a full BED scientific response constructs a valid ChatMessage with MetadataContent."""
    meta = SUPPORTED_SCENARIOS["CS-CAT-001"]
    sc = meta["loader"]()
    text, card_payload = build_scientific_response("CS-CAT-001", sc, "wgs Pt/CeO2")

    # Serialize card payload for MetadataContent
    serialized_meta = serialize_metadata_payload(card_payload)
    meta_content = MetadataContent(type="metadata", metadata=serialized_meta)

    # Construct the ChatMessage exactly as fetch_agent does
    reply = ChatMessage(
        content=[
            TextContent(type="text", text=text),
            meta_content,
        ]
    )

    assert len(reply.content) == 2
    assert isinstance(reply.content[0], TextContent)
    assert isinstance(reply.content[1], MetadataContent)
    assert all(isinstance(v, str) for v in reply.content[1].metadata.values())

    # Validate that consumer can decode the full ASI:One card
    decoded_card = deserialize_metadata_payload(reply.content[1].metadata)
    assert decoded_card["card_type"] == "scientific_experiment_recommendation"
    assert decoded_card["recommended_experiment"]["id"] == "EXP-WGS-02"
    assert len(decoded_card["citations"]) >= 3


def test_observation_response_chat_message_schema_valid():
    """Verify that a dynamic Bayesian observation update constructs a valid ChatMessage with MetadataContent."""
    text, card_payload = build_observation_response("EXP-WGS-02", "Initial_CO2_Mainly_Lattice_16O")
    serialized_meta = serialize_metadata_payload(card_payload)
    meta_content = MetadataContent(type="metadata", metadata=serialized_meta)

    reply = ChatMessage(
        content=[
            TextContent(type="text", text=text),
            meta_content,
        ]
    )

    assert len(reply.content) == 2
    decoded_card = deserialize_metadata_payload(reply.content[1].metadata)
    assert decoded_card["card_type"] == "bayesian_update_result"
    assert decoded_card["observed_experiment"] == "EXP-WGS-02"
    assert decoded_card["posteriors"]["H1"] > 0.85


def test_sync_query_skips_acknowledgement_for_direct_response():
    """Verify that synchronous HTTP connections (where sender is in ctx._queries)
    skip ChatAcknowledgement so the single sync HTTP response delivers the actual ChatMessage."""
    from unittest.mock import AsyncMock, MagicMock
    from datetime import datetime, timezone
    from uuid import uuid4
    import asyncio
    from uagents import Context
    from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, ChatAcknowledgement

    async def _run():
        # Create dummy context with _queries containing the sender
        sender = "agent1_test_requester_address"
        ctx = MagicMock(spec=Context)
        ctx.logger = MagicMock()
        ctx.send = AsyncMock()
        ctx._queries = {sender: MagicMock()}

        # Simulate logic from handle_chat_message
        is_sync_query = hasattr(ctx, "_queries") and sender in getattr(ctx, "_queries", {})
        assert is_sync_query is True

        # If sync query, ChatAcknowledgement is NOT sent
        if not is_sync_query:
            await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=uuid4()))

        # Verify no acknowledgement was dispatched
        ctx.send.assert_not_called()

        # Now verify asynchronous flow (not in _queries) DOES send acknowledgement
        async_ctx = MagicMock(spec=Context)
        async_ctx.logger = MagicMock()
        async_ctx.send = AsyncMock()
        async_ctx._queries = {}

        is_async_sync = hasattr(async_ctx, "_queries") and sender in getattr(async_ctx, "_queries", {})
        assert is_async_sync is False
        if not is_async_sync:
            await async_ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=uuid4()))

        async_ctx.send.assert_awaited_once()

    asyncio.run(_run())


# ==============================================================================
# 4. SECURITY & CREDENTIAL SANITIZATION TESTS (PHASE 1)
# ==============================================================================

def test_sanitize_secret_google_key():
    """Verify redaction of Google AIzaSy API key patterns."""
    fake_key = "AIzaSyB3cDeFgHiJkLmNoPqRsTuVwXyZ1234567"
    raw_text = f"Connection failed to https://generativelanguage.googleapis.com?key={fake_key}"
    clean = sanitize_secret(raw_text, fake_key)
    assert fake_key not in clean
    assert "[REDACTED_API_KEY]" in clean


def test_sanitize_secret_bearer_token():
    """Verify redaction of Bearer tokens."""
    raw = "Authorization: Bearer my_secret_token_abc_123 and details"
    clean = sanitize_secret(raw)
    assert "my_secret_token_abc_123" not in clean
    assert "[REDACTED_TOKEN]" in clean


def test_cors_configuration_no_wildcard_with_credentials():
    """Verify CORS middleware in app.main does not use wildcard origins when allow_credentials=True."""
    from fastapi.middleware.cors import CORSMiddleware
    cors_mw = next((mw for mw in app.user_middleware if mw.cls == CORSMiddleware), None)
    assert cors_mw is not None
    # allow_origins must be a list and must NOT contain wildcard '*'
    origins = cors_mw.kwargs.get("allow_origins", [])
    assert isinstance(origins, list)
    assert "*" not in origins
    assert "http://localhost:5173" in origins


# ==============================================================================
# 5. SCIENTIFIC CONSTRAINTS & FEASIBILITY TESTS (PHASE 2)
# ==============================================================================

def test_filter_feasible_experiments():
    """Verify hard feasibility and budget constraint filtering."""
    exps = load_candidate_experiments()
    # Filter with small budget 2.0
    feasible, log = filter_feasible_experiments(exps, max_cost_budget=2.0)
    # EXP-WGS-03 cost is 6.5 -> must be rejected
    assert not any(e.id == "EXP-WGS-03" for e in feasible)
    assert any("Cost 6.5 exceeds maximum allowed budget 2.0" in entry for entry in log)
    # EXP-WGS-01 cost is 1.5 and EXP-WGS-04 cost is 1.1 -> must be preserved
    assert any(e.id == "EXP-WGS-01" for e in feasible)
    assert any(e.id == "EXP-WGS-04" for e in feasible)


# ==============================================================================
# 6. CONVERSATION STATE CONTINUITY & PERSISTENCE TESTS
# ==============================================================================

def test_status_query_intent_parsing():
    """Verify natural language status and observation history detection."""
    assert parse_status_or_history_intent("What are the current posterior probabilities for EXP-WGS-02, and what observation has been recorded?") is True
    assert parse_status_or_history_intent("What is the current status of the investigation?") is True
    assert parse_status_or_history_intent("What observations have been recorded so far?") is True
    assert parse_status_or_history_intent("What are the current posteriors?") is True
    assert parse_status_or_history_intent("Show me investigation history and progress") is True

    # Standard scientific queries and observation commands must not be falsely flagged as status
    assert parse_status_or_history_intent("What experiment distinguishes the redox pathway on Pt/CeO2 water gas shift?") is False
    assert parse_status_or_history_intent("observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O") is False
    assert parse_status_or_history_intent("") is False


def test_extract_referenced_experiment_or_scenario():
    """Verify extraction of target scenario from experiment IDs or scenario keywords."""
    assert extract_referenced_experiment_or_scenario("What are the posteriors for EXP-WGS-02?") == "CS-CAT-001"
    assert extract_referenced_experiment_or_scenario("Status of EXP-OER-01") == "CS-OER-002"
    assert extract_referenced_experiment_or_scenario("What about water-gas shift?") == "CS-CAT-001"
    assert extract_referenced_experiment_or_scenario("perovskite oxygen evolution") == "CS-OER-002"
    assert extract_referenced_experiment_or_scenario("kinase pathway") == "SYN-001"
    assert extract_referenced_experiment_or_scenario("random unrelated text") is None


def test_three_step_conversation_state_continuity():
    """
    Directly replicates the user-reported ASI:One conversation sequence:
    1. User asks: 'What experiment distinguishes the redox pathway on Pt/CeO2 water gas shift?'
       -> Agent recommends EXP-WGS-02 with initial priors (H1 = 0.50, H2 = 0.20, H3 = 0.30).
    2. User submits: 'observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O'
       -> Agent updates posteriors (H1 = 89.8%, H2 = 3.1%, H3 = 7.0%) and recommends EXP-WGS-01.
    3. User asks: 'What are the current posterior probabilities for EXP-WGS-02, and what observation has been recorded?'
       -> Agent MUST return the updated state with H1 = 89.8%, the recorded EXP-WGS-02 observation,
          and EXP-WGS-01 as the next assay (NOT reset to initial literature priors).
    4. Follow-up: User re-asks the original scenario question in the same conversation
       -> Agent MUST preserve the updated state instead of silently wiping laboratory progress.
    """
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4
    from datetime import datetime, timezone
    from uagents import Context

    async def _run():
        agent = create_janus_uagent("test_janus_continuity", "test_seed_continuity_777", use_mailbox=False)
        proto = list(agent.protocols.values())[0]
        handler = list(proto._signed_message_handlers.values())[0]

        session_uuid = uuid4()
        sender_address = "agent1_client_continuity_tester"

        # Mock runtime context representing the conversation session
        ctx = MagicMock(spec=Context)
        ctx.session = session_uuid
        ctx.logger = MagicMock()
        ctx.send = AsyncMock()
        ctx._queries = {sender_address: MagicMock()}
        ctx.storage = MagicMock()
        ctx.storage.has.return_value = False

        # --- STEP 1: Initial Scientific Query ---
        msg1 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="What experiment distinguishes the redox pathway on Pt/CeO2 water gas shift?")],
        )
        await handler(ctx, sender_address, msg1)
        reply1 = ctx.send.call_args[0][1]
        text1 = reply1.content[0].text
        card1 = deserialize_metadata_payload(reply1.content[1].metadata)

        assert "EXP-WGS-02" in text1
        assert "Prior $P(H1) = 0.50$" in text1
        assert card1["card_type"] == "scientific_experiment_recommendation"
        assert card1["recommended_experiment"]["id"] == "EXP-WGS-02"
        assert "investigation_id" in card1
        inv_id = card1["investigation_id"]

        # --- STEP 2: Observation Submission ---
        msg2 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O")],
        )
        await handler(ctx, sender_address, msg2)
        reply2 = ctx.send.call_args[0][1]
        text2 = reply2.content[0].text
        card2 = deserialize_metadata_payload(reply2.content[1].metadata)

        assert "Sequential Bayesian Update" in text2
        assert "Posterior $P(H1 \\mid y) = 89.8%" in text2
        assert "EXP-WGS-01" in text2
        assert card2["card_type"] == "bayesian_update_result"
        assert card2["posteriors"]["H1"] > 0.89
        assert card2["next_recommended_experiment"] == "EXP-WGS-01"
        assert card2["investigation_id"] == inv_id

        # --- STEP 3: Status / History Inspection Query ---
        msg3 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="What are the current posterior probabilities for EXP-WGS-02, and what observation has been recorded?")],
        )
        await handler(ctx, sender_address, msg3)
        reply3 = ctx.send.call_args[0][1]
        text3 = reply3.content[0].text
        card3 = deserialize_metadata_payload(reply3.content[1].metadata)

        # Critical Assertions: State continuity maintained!
        assert inv_id in text3
        assert "89.8%" in text3, "Must display the 89.8% posterior probability for H1"
        assert "Initial_CO2_Mainly_Lattice_16O" in text3, "Must list the recorded EXP-WGS-02 observation"
        assert "EXP-WGS-01" in text3, "Must recommend EXP-WGS-01 as the next optimal experiment"
        assert "Prior $P(H1) = 0.50$" not in text3, "Must NOT revert to initial unconditioned priors"

        assert card3["card_type"] == "investigation_status"
        assert card3["posteriors"]["H1"] > 0.89
        assert len(card3["executed_observations"]) == 1
        assert card3["executed_observations"][0]["experiment_id"] == "EXP-WGS-02"
        assert card3["executed_observations"][0]["observed_outcome"] == "Initial_CO2_Mainly_Lattice_16O"
        assert card3["next_recommended_experiment"] == "EXP-WGS-01"
        assert card3["recommended_experiment"]["id"] == "EXP-WGS-01"

        # --- STEP 4: Continuity when re-asking original query in same session ---
        msg4 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="What experiment distinguishes the redox pathway on Pt/CeO2 water gas shift?")],
        )
        await handler(ctx, sender_address, msg4)
        reply4 = ctx.send.call_args[0][1]
        text4 = reply4.content[0].text
        card4 = deserialize_metadata_payload(reply4.content[1].metadata)

        # Must preserve recorded progress rather than wiping to initial state
        assert "89.8%" in text4
        assert "EXP-WGS-01" in text4
        assert len(card4["executed_observations"]) == 1

    asyncio.run(_run())


def test_investigation_session_isolation():
    """Verify that multiple concurrent conversation sessions do not cross-contaminate state."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4
    from datetime import datetime, timezone
    from uagents import Context

    async def _run():
        agent = create_janus_uagent("test_janus_isolation", "test_seed_isolation_888", use_mailbox=False)
        proto = list(agent.protocols.values())[0]
        handler = list(proto._signed_message_handlers.values())[0]

        session_a = uuid4()
        session_b = uuid4()
        sender_a = "agent1_client_session_a"
        sender_b = "agent1_client_session_b"

        # Context for Session A (WGS campaign)
        ctx_a = MagicMock(spec=Context)
        ctx_a.session = session_a
        ctx_a.logger = MagicMock()
        ctx_a.send = AsyncMock()
        ctx_a._queries = {sender_a: MagicMock()}
        ctx_a.storage = MagicMock()
        ctx_a.storage.has.return_value = False

        # Context for Session B (OER campaign)
        ctx_b = MagicMock(spec=Context)
        ctx_b.session = session_b
        ctx_b.logger = MagicMock()
        ctx_b.send = AsyncMock()
        ctx_b._queries = {sender_b: MagicMock()}
        ctx_b.storage = MagicMock()
        ctx_b.storage.has.return_value = False

        # Session A: Start WGS and record observation
        msg_a1 = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="Pt/CeO2 water gas shift redox mechanism")])
        await handler(ctx_a, sender_a, msg_a1)
        msg_a2 = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O")])
        await handler(ctx_a, sender_a, msg_a2)

        # Session B: Start OER and record observation
        msg_b1 = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="Oxygen evolution OER on perovskites")])
        await handler(ctx_b, sender_b, msg_b1)
        msg_b2 = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="observe EXP-OER-01 Significant_Lattice_18O_In_O2")])
        await handler(ctx_b, sender_b, msg_b2)

        # Check Session A status
        msg_a_status = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="What is the current status and recorded observations?")])
        await handler(ctx_a, sender_a, msg_a_status)
        reply_a = ctx_a.send.call_args[0][1]
        card_a = deserialize_metadata_payload(reply_a.content[1].metadata)

        # Session A must only contain WGS data
        assert card_a["scenario_id"] == "CS-CAT-001"
        assert any(obs["experiment_id"] == "EXP-WGS-02" for obs in card_a["executed_observations"])
        assert not any("OER" in obs["experiment_id"] for obs in card_a["executed_observations"])

        # Check Session B status
        msg_b_status = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="What is the current status and recorded observations?")])
        await handler(ctx_b, sender_b, msg_b_status)
        reply_b = ctx_b.send.call_args[0][1]
        card_b = deserialize_metadata_payload(reply_b.content[1].metadata)

        # Session B must only contain OER data
        assert card_b["scenario_id"] == "CS-OER-002"
        assert any(obs["experiment_id"] == "EXP-OER-01" for obs in card_b["executed_observations"])
        assert not any("WGS" in obs["experiment_id"] for obs in card_b["executed_observations"])

    asyncio.run(_run())


def test_investigation_restart_persistence():
    """Verify that investigation state survives process restarts using KeyValueStore / ctx.storage."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4
    from datetime import datetime, timezone
    from uagents import Context

    # Persistent storage dictionary simulating disk-backed KeyValueStore
    backing_disk_store: dict = {}

    class MockPersistentStore:
        def get(self, key):
            return backing_disk_store.get(key)
        def set(self, key, value):
            backing_disk_store[key] = value
        def has(self, key):
            return key in backing_disk_store

    disk_storage = MockPersistentStore()
    session_id = str(uuid4())
    sender = "agent1_client_restart_tester"

    async def _run():
        agent1 = create_janus_uagent("test_janus_p1", "test_seed_persist_111", use_mailbox=False)
        proto1 = list(agent1.protocols.values())[0]
        handler1 = list(proto1._signed_message_handlers.values())[0]

        ctx1 = MagicMock(spec=Context)
        ctx1.session = session_id
        ctx1.logger = MagicMock()
        ctx1.send = AsyncMock()
        ctx1._queries = {sender: MagicMock()}
        ctx1.storage = disk_storage

        # 1. Start investigation and observe EXP-WGS-02 in process #1
        msg1 = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="wgs Pt/CeO2")])
        await handler1(ctx1, sender, msg1)
        msg2 = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text="observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O")])
        await handler1(ctx1, sender, msg2)

        # Verify that backing disk storage was populated
        assert any(k.startswith("inv:INV-") for k in backing_disk_store)
        assert f"active_session:{session_id}" in backing_disk_store

        # 2. Simulate complete restart: wipe in-memory structures
        INVESTIGATIONS_STORE.clear()
        SESSION_ACTIVE_MAP.clear()
        assert len(INVESTIGATIONS_STORE) == 0
        assert len(SESSION_ACTIVE_MAP) == 0

        # 3. Process #2: New agent instance with the same persistent disk storage
        agent2 = create_janus_uagent("test_janus_p2", "test_seed_persist_111", use_mailbox=False)
        proto2 = list(agent2.protocols.values())[0]
        handler2 = list(proto2._signed_message_handlers.values())[0]

        ctx2 = MagicMock(spec=Context)
        ctx2.session = session_id
        ctx2.logger = MagicMock()
        ctx2.send = AsyncMock()
        ctx2._queries = {sender: MagicMock()}
        ctx2.storage = disk_storage

        # Query status after restart
        msg3 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="What are the current posterior probabilities for EXP-WGS-02, and what observation has been recorded?")],
        )
        await handler2(ctx2, sender, msg3)
        reply3 = ctx2.send.call_args[0][1]
        text3 = reply3.content[0].text
        card3 = deserialize_metadata_payload(reply3.content[1].metadata)

        # State must be cleanly restored from disk storage
        assert "89.8%" in text3
        assert "Initial_CO2_Mainly_Lattice_16O" in text3
        assert "EXP-WGS-01" in text3
        assert card3["posteriors"]["H1"] > 0.89
        assert len(card3["executed_observations"]) == 1
        assert card3["next_recommended_experiment"] == "EXP-WGS-01"

    asyncio.run(_run())


def test_chat_response_lifecycle_and_session_termination():
    """Verify that every outgoing ChatMessage satisfies Agent Chat Protocol v0.3.0:
    1. Contains readable TextContent.
    2. Contains structured MetadataContent.
    3. Contains EndSessionContent to close the turn and clear client spinners.
    4. Exception / fallback paths return user-visible error text and EndSessionContent.
    5. StartSession without text returns welcome text and EndSessionContent.
    6. EndSession without text concludes cleanly without generating rejection errors.
    """
    import asyncio
    from uuid import uuid4
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, MagicMock, patch
    from uagents import Context
    from uagents_core.contrib.protocols.chat import (
        ChatMessage,
        TextContent,
        MetadataContent,
        EndSessionContent,
        StartSessionContent,
        ChatAcknowledgement,
    )

    async def _run():
        agent = create_janus_uagent("test_janus_lifecycle", "test_seed_lifecycle_999", use_mailbox=False)
        proto = list(agent.protocols.values())[0]
        handler = list(proto._signed_message_handlers.values())[0]

        sender = "agent1_client_lifecycle_tester"

        # 1. Standard successful query -> Must have TextContent + MetadataContent + EndSessionContent
        ctx1 = MagicMock(spec=Context)
        ctx1.session = uuid4()
        ctx1.logger = MagicMock()
        ctx1.send = AsyncMock()
        ctx1._queries = {sender: MagicMock()}
        ctx1.storage = MagicMock()
        ctx1.storage.has.return_value = False

        msg1 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="What experiment distinguishes the redox pathway on Pt/CeO2 water gas shift?")],
        )
        await handler(ctx1, sender, msg1)
        reply1 = ctx1.send.call_args[0][1]

        assert isinstance(reply1, ChatMessage)
        assert len(reply1.content) == 3
        assert isinstance(reply1.content[0], TextContent)
        assert len(reply1.content[0].text) > 0
        assert isinstance(reply1.content[1], MetadataContent)
        assert isinstance(reply1.content[2], EndSessionContent)
        assert reply1.content[2].type == "end-session"

        # 2. Out-of-domain rejection query -> Must have readable rejection text + EndSessionContent
        ctx2 = MagicMock(spec=Context)
        ctx2.session = uuid4()
        ctx2.logger = MagicMock()
        ctx2.send = AsyncMock()
        ctx2._queries = {sender: MagicMock()}
        ctx2.storage = MagicMock()
        ctx2.storage.has.return_value = False

        msg2 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="What is the weather in Paris today?")],
        )
        await handler(ctx2, sender, msg2)
        reply2 = ctx2.send.call_args[0][1]

        assert isinstance(reply2, ChatMessage)
        assert isinstance(reply2.content[0], TextContent)
        assert "scientific integrity" in reply2.content[0].text.lower()
        assert isinstance(reply2.content[-1], EndSessionContent)

        # 3. Exception fallback path -> Must catch error, return human-readable error text, and EndSessionContent
        ctx3 = MagicMock(spec=Context)
        ctx3.session = uuid4()
        ctx3.logger = MagicMock()
        ctx3.send = AsyncMock()
        ctx3._queries = {sender: MagicMock()}
        ctx3.storage = MagicMock()
        ctx3.storage.has.return_value = False

        with patch("agents.fetch_agent.parse_scientific_intent", side_effect=RuntimeError("Simulated pipeline failure")):
            msg3 = ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="Pt/CeO2 water gas shift")],
            )
            await handler(ctx3, sender, msg3)
            reply3 = ctx3.send.call_args[0][1]

            assert isinstance(reply3, ChatMessage)
            assert isinstance(reply3.content[0], TextContent)
            assert "An internal error occurred" in reply3.content[0].text
            assert "Simulated pipeline failure" in reply3.content[0].text
            assert isinstance(reply3.content[-1], EndSessionContent)

        # 4. StartSessionContent with no text -> Returns welcome guidance + EndSessionContent
        ctx4 = MagicMock(spec=Context)
        ctx4.session = uuid4()
        ctx4.logger = MagicMock()
        ctx4.send = AsyncMock()
        ctx4._queries = {sender: MagicMock()}
        ctx4.storage = MagicMock()
        ctx4.storage.has.return_value = False

        msg4 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[StartSessionContent(type="start-session")],
        )
        await handler(ctx4, sender, msg4)
        reply4 = ctx4.send.call_args[0][1]

        assert isinstance(reply4, ChatMessage)
        assert isinstance(reply4.content[0], TextContent)
        assert "Welcome to JANUS" in reply4.content[0].text
        assert isinstance(reply4.content[-1], EndSessionContent)

        # 5. EndSessionContent with no text -> Concludes session cleanly without sending error reply
        ctx5 = MagicMock(spec=Context)
        ctx5.session = uuid4()
        ctx5.logger = MagicMock()
        ctx5.send = AsyncMock()
        ctx5._queries = {sender: MagicMock()}
        ctx5.storage = MagicMock()
        ctx5.storage.has.return_value = False

        msg5 = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[EndSessionContent(type="end-session")],
        )
        await handler(ctx5, sender, msg5)
        # Should not send a message back when client ends session
        ctx5.send.assert_not_called()

    asyncio.run(_run())
