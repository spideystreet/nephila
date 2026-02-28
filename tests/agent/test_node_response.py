"""Unit tests for response_node() — no external dependencies."""
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from nephila.agent.nodes.node_response import response_node


def _state(messages: list) -> dict:
    return {"messages": messages}


class TestResponseNode:
    def test_cis_extracted_from_tool_message(self):
        state = _state([
            HumanMessage(content="info médicament?"),
            ToolMessage(content="Médicament trouvé. CIS 60001154 — DOLIPRANE.", tool_call_id="t1"),
        ])
        result = response_node(state)
        assert result["source_cis"] == "60001154"

    def test_no_tool_message_returns_none(self):
        state = _state([
            HumanMessage(content="bonjour"),
            AIMessage(content="Bonjour, comment puis-je vous aider ?"),
        ])
        result = response_node(state)
        assert result["source_cis"] is None

    def test_multiple_tool_messages_first_cis_wins(self):
        state = _state([
            HumanMessage(content="deux médicaments?"),
            ToolMessage(content="CIS 11111111 — MEDICAMENT_A", tool_call_id="t1"),
            ToolMessage(content="CIS 22222222 — MEDICAMENT_B", tool_call_id="t2"),
        ])
        result = response_node(state)
        assert result["source_cis"] == "11111111"

    def test_tool_message_without_cis_returns_none(self):
        state = _state([
            HumanMessage(content="interaction?"),
            ToolMessage(
                content="[Contre-indication] AMIODARONE + WARFARINE",
                tool_call_id="t1",
            ),
        ])
        result = response_node(state)
        assert result["source_cis"] is None

    def test_only_current_turn_cis_extracted(self):
        """CIS from a previous turn (before last HumanMessage) must be ignored."""
        state = _state([
            HumanMessage(content="first question"),
            ToolMessage(content="CIS 11111111 — OLD_DRUG", tool_call_id="old"),
            HumanMessage(content="new question"),
            ToolMessage(content="CIS 22222222 — NEW_DRUG", tool_call_id="new"),
        ])
        result = response_node(state)
        assert result["source_cis"] == "22222222"

    def test_no_cis_in_current_turn_returns_none(self):
        """Even if previous turn has a CIS, return None when current turn has none."""
        state = _state([
            HumanMessage(content="first question"),
            ToolMessage(content="CIS 11111111 — OLD_DRUG", tool_call_id="old"),
            HumanMessage(content="bonjour"),
            AIMessage(content="Comment puis-je vous aider ?"),
        ])
        result = response_node(state)
        assert result["source_cis"] is None
