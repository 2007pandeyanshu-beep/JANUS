"""Unit tests for Card Selection Parsing and ACP Integration (Workstream D & Dynamic UI).

Verifies:
- Multi-mode observation parsing: typed text, JSON card payload, action tokens, planner prose
- Equivalence between typed command and JSON card selection
- Rich interactive card structure (citations with verification badges, independent verification, interactive actions)
- Session isolation and state continuity preservation across sequential interactions
"""

import pytest
import json
from agents.fetch_agent import (
    parse_observation_intent,
    generate_asione_card,
    build_observation_response,
    build_scientific_response,
    serialize_metadata_payload,
    deserialize_metadata_payload,
    SUPPORTED_SCENARIOS,
)
from scientific.evidence_ingestion import get_wgs_case_study_scenario
from scientific.engine import ScientificEngine


def test_parse_observation_intent_modes():
    """Tests all supported observation input modalities."""
    expected_exp = "EXP-WGS-02"
    expected_out = "Initial_CO2_Mainly_Lattice_16O"

    # 1. Standard text command
    res1 = parse_observation_intent("observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O")
    assert res1 == (expected_exp, expected_out)

    # 2. Outcome statement
    res2 = parse_observation_intent("outcome for EXP-WGS-02 is Initial_CO2_Mainly_Lattice_16O")
    assert res2 == (expected_exp, expected_out)

    # 3. Direct key-value assignment
    res3 = parse_observation_intent("EXP-WGS-02 = Initial_CO2_Mainly_Lattice_16O")
    assert res3 == (expected_exp, expected_out)

    # 4. JSON payload from UI card callback
    json_payload = json.dumps({"experiment_id": "EXP-WGS-02", "outcome": "Initial_CO2_Mainly_Lattice_16O"})
    res4 = parse_observation_intent(json_payload)
    assert res4 == (expected_exp, expected_out)

    # 5. JSON with nested command
    json_cmd = json.dumps({"command": "observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O"})
    res5 = parse_observation_intent(json_cmd)
    assert res5 == (expected_exp, expected_out)

    # 6. JSON with action_id
    json_act = json.dumps({"action_id": "observe_EXP-WGS-02_Initial_CO2_Mainly_Lattice_16O"})
    res6 = parse_observation_intent(json_act)
    assert res6 == (expected_exp, expected_out)

    # 7. Direct action token string
    res7 = parse_observation_intent("observe_EXP-WGS-02_Initial_CO2_Mainly_Lattice_16O")
    assert res7 == (expected_exp, expected_out)

    # 8. Conversational planner prose
    prose = "The user selected experiment EXP-WGS-02 with outcome Initial_CO2_Mainly_Lattice_16O"
    res8 = parse_observation_intent(prose)
    assert res8 == (expected_exp, expected_out)


def test_text_vs_json_card_equivalence():
    """Verifies that submitting an observation via typed text or via JSON card payload yields identical Bayesian updates."""
    session_text = "test-session-text-mode"
    session_json = "test-session-json-mode"

    # Text mode execution
    exp_text, out_text = parse_observation_intent("observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O")
    narrative_text, card_text = build_observation_response(exp_text, out_text, session_id=session_text)

    # JSON card mode execution
    json_input = json.dumps({"experiment_id": "EXP-WGS-02", "outcome": "Initial_CO2_Mainly_Lattice_16O"})
    exp_json, out_json = parse_observation_intent(json_input)
    narrative_json, card_json = build_observation_response(exp_json, out_json, session_id=session_json)

    assert card_text["posteriors"] == card_json["posteriors"]
    assert card_text["next_recommended_experiment"] == card_json["next_recommended_experiment"]
    assert card_text["remaining_candidates_count"] == card_json["remaining_candidates_count"]


def test_interactive_card_payload_rich_fields():
    """Verifies that generated ASI:One interactive cards contain verification metadata and structured actions."""
    scenario = get_wgs_case_study_scenario()
    analysis = ScientificEngine.execute_analysis(scenario)
    top_score = analysis.ranked_experiments[0]

    card = generate_asione_card(
        scenario_id="CS-CAT-001",
        scenario_name="Pt/CeO2 WGS",
        top_score=top_score,
        all_scores=analysis.ranked_experiments,
        evidence_list=scenario.evidence,
    )

    # Check citations have verification fields
    assert "citations" in card
    for cite in card["citations"]:
        assert "doi_verification_status" in cite
        assert "doi" in cite

    # Check independent verification metadata is present
    assert "independent_verification" in card
    assert card["independent_verification"]["engine_invariants_audited"] is True
    assert "boundary_notice" in card["independent_verification"]

    # Check interactive actions contain explicit action fields
    assert "interactive_actions" in card
    for action in card["interactive_actions"]:
        assert "action_id" in action
        assert "label" in action
        assert "command" in action
        assert "experiment_id" in action
        assert "outcome" in action


def test_metadata_envelope_with_interactive_card():
    """Verifies that full card payloads serialize into ASI:One MetadataContent and deserialize intact."""
    scenario = get_wgs_case_study_scenario()
    analysis = ScientificEngine.execute_analysis(scenario)
    top_score = analysis.ranked_experiments[0]

    card = generate_asione_card(
        scenario_id="CS-CAT-001",
        scenario_name="Pt/CeO2 WGS",
        top_score=top_score,
        all_scores=analysis.ranked_experiments,
        evidence_list=scenario.evidence,
    )

    serialized = serialize_metadata_payload(card)
    assert "card_payload" in serialized
    assert serialized["card_protocol_version"] == "1"
    assert serialized["requires_card_interaction"] == "true"

    deserialized = deserialize_metadata_payload(serialized)
    assert deserialized["scenario_id"] == "CS-CAT-001"
    assert deserialized["recommended_experiment"]["id"] == top_score.experiment_id
    assert len(deserialized["interactive_actions"]) == len(card["interactive_actions"])
