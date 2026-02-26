"""Unit tests for warn_node() — no external dependencies."""
from langchain_core.messages import AIMessage, HumanMessage

from nephila.agent.nodes.node_warn import warn_node


def _state(messages: list, interactions: list) -> dict:
    return {"messages": messages, "interactions_found": interactions}


CRITICAL_INTERACTION = {"niveau_contrainte": "Contre-indication", "detail": "AMIODARONE + WARFARINE"}
DECONSEILLE_INTERACTION = {
    "niveau_contrainte": "Association déconseillée",
    "detail": "AMIODARONE + FLECAINIDE",
}
PE_INTERACTION = {"niveau_contrainte": "Précaution d'emploi", "detail": "A + B"}


class TestWarnNode:
    def test_warning_prefix_prepended_to_last_ai_message(self):
        ai_msg = AIMessage(id="msg-1", content="Voici l'analyse.")
        state = _state(
            messages=[HumanMessage(content="?"), ai_msg],
            interactions=[CRITICAL_INTERACTION],
        )
        result = warn_node(state)
        new_msg = result["messages"][0]
        assert new_msg.content.startswith("⚠️")
        assert "Voici l'analyse." in new_msg.content

    def test_original_message_id_preserved(self):
        ai_msg = AIMessage(id="msg-abc", content="Analyse.")
        state = _state(
            messages=[HumanMessage(content="?"), ai_msg],
            interactions=[CRITICAL_INTERACTION],
        )
        result = warn_node(state)
        assert result["messages"][0].id == "msg-abc"

    def test_only_critical_interactions_in_warning(self):
        """PE interactions must not appear in the warning block."""
        state = _state(
            messages=[HumanMessage(content="?"), AIMessage(id="x", content="Analyse.")],
            interactions=[CRITICAL_INTERACTION, PE_INTERACTION],
        )
        result = warn_node(state)
        content = result["messages"][0].content
        assert "AMIODARONE + WARFARINE" in content
        assert "A + B" not in content

    def test_both_critical_levels_included(self):
        state = _state(
            messages=[HumanMessage(content="?"), AIMessage(id="x", content="Analyse.")],
            interactions=[CRITICAL_INTERACTION, DECONSEILLE_INTERACTION],
        )
        result = warn_node(state)
        content = result["messages"][0].content
        assert "AMIODARONE + WARFARINE" in content
        assert "AMIODARONE + FLECAINIDE" in content

    def test_no_ai_message_creates_empty_ai_message(self):
        """When no AI message exists, warn_node creates one with only the prefix."""
        state = _state(
            messages=[HumanMessage(content="?")],
            interactions=[CRITICAL_INTERACTION],
        )
        result = warn_node(state)
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert "⚠️" in result["messages"][0].content
