"""Unit tests for guardrail_node() and should_warn() — no external dependencies."""
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from nephila.agent.nodes.node_guardrail import guardrail_node, should_warn


def _state(messages: list) -> dict:
    return {"messages": messages}


# ---------------------------------------------------------------------------
# guardrail_node
# ---------------------------------------------------------------------------


class TestGuardrailNode:
    def test_no_tool_messages_returns_empty(self):
        state = _state([HumanMessage(content="Bonjour")])
        result = guardrail_node(state)
        assert result["interactions_found"] == []

    def test_single_interaction_parsed(self):
        state = _state([
            HumanMessage(content="interaction?"),
            ToolMessage(
                content="[Contre-indication] AMIODARONE + WARFARINE",
                tool_call_id="t1",
            ),
        ])
        result = guardrail_node(state)
        assert len(result["interactions_found"]) == 1
        assert result["interactions_found"][0]["niveau_contrainte"] == "Contre-indication"
        assert "AMIODARONE" in result["interactions_found"][0]["detail"]

    def test_multiline_tool_message_parsed(self):
        content = (
            "[Contre-indication] AMIODARONE + WARFARINE\n"
            "[Association déconseillée] AMIODARONE + FLECAINIDE\n"
        )
        state = _state([
            HumanMessage(content="interaction?"),
            ToolMessage(content=content, tool_call_id="t1"),
        ])
        result = guardrail_node(state)
        assert len(result["interactions_found"]) == 2

    def test_mirror_deduplication(self):
        """A+B and B+A count as the same pair."""
        content = (
            "[Contre-indication] AMIODARONE + WARFARINE\n"
            "[Contre-indication] WARFARINE + AMIODARONE\n"
        )
        state = _state([
            HumanMessage(content="interaction?"),
            ToolMessage(content=content, tool_call_id="t1"),
        ])
        result = guardrail_node(state)
        assert len(result["interactions_found"]) == 1

    def test_only_current_turn_inspected(self):
        """Tool messages from a previous turn (before last HumanMessage) are ignored."""
        state = _state([
            HumanMessage(content="first question"),
            ToolMessage(
                content="[Contre-indication] OLD_A + OLD_B",
                tool_call_id="old",
            ),
            HumanMessage(content="new question"),
            ToolMessage(
                content="[Précaution d'emploi] NEW_A + NEW_B",
                tool_call_id="new",
            ),
        ])
        result = guardrail_node(state)
        assert len(result["interactions_found"]) == 1
        assert result["interactions_found"][0]["niveau_contrainte"] == "Précaution d'emploi"

# ---------------------------------------------------------------------------
# should_warn
# ---------------------------------------------------------------------------


class TestShouldWarn:
    def test_empty_interactions_returns_response(self):
        assert should_warn({"messages": [], "interactions_found": []}) == "response"

    def test_precaution_emploi_returns_response(self):
        state = {
            "messages": [],
            "interactions_found": [
                {"niveau_contrainte": "Précaution d'emploi", "detail": "A + B"}
            ],
        }
        assert should_warn(state) == "response"

    def test_contre_indication_returns_warn(self):
        state = {
            "messages": [],
            "interactions_found": [
                {"niveau_contrainte": "Contre-indication", "detail": "A + B"}
            ],
        }
        assert should_warn(state) == "warn"

    def test_association_deconseillee_returns_warn(self):
        state = {
            "messages": [],
            "interactions_found": [
                {"niveau_contrainte": "Association déconseillée", "detail": "A + B"}
            ],
        }
        assert should_warn(state) == "warn"

    def test_mixed_case_contre_indication(self):
        """Case-insensitive comparison must still trigger warn."""
        state = {
            "messages": [],
            "interactions_found": [
                {"niveau_contrainte": "CONTRE-INDICATION", "detail": "A + B"}
            ],
        }
        assert should_warn(state) == "warn"

    def test_missing_key_returns_response(self):
        assert should_warn({"messages": []}) == "response"
