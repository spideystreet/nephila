"""Unit tests for routing() conditional edge — no external dependencies."""

from langchain_core.messages import AIMessage

from nephila.agent.graph_agent import routing


def _state(messages: list) -> dict:
    return {"messages": messages}


class TestRouting:
    def test_routes_to_guardrail_when_no_tool_calls(self):
        msg = AIMessage(content="Here is my answer.")
        assert routing(_state([msg])) == "guardrail"

    def test_routes_to_tools_when_tool_calls_present(self):
        msg = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "search_drug", "args": {"query": "aspirine"}, "type": "tool_call"}],
        )
        assert routing(_state([msg])) == "tools"

    def test_routes_to_guardrail_when_tool_calls_is_empty_list(self):
        """An empty tool_calls list must not trigger the tools branch."""
        msg = AIMessage(content="Done.", tool_calls=[])
        assert routing(_state([msg])) == "guardrail"

    def test_routes_to_guardrail_for_empty_content_no_calls(self):
        msg = AIMessage(content="")
        assert routing(_state([msg])) == "guardrail"
