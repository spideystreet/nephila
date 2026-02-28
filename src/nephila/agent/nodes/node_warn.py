"""Warn node — appends a compact interaction notice to the agent's response."""

from typing import Any

from langchain_core.messages import AIMessage

from nephila.agent.model_state import CRITICAL_LEVELS, AgentState


def warn_node(state: AgentState) -> dict[str, Any]:
    """Append a single-line interaction notice after the agent's response."""
    critical = [
        i
        for i in state.get("interactions_found", [])
        if i.get("niveau_contrainte", "").lower() in CRITICAL_LEVELS
    ]

    pairs = ", ".join(f"{i['detail']} ({i['niveau_contrainte']})" for i in critical)
    notice = f"\n\n⚠️ Interaction(s) ANSM détectée(s) : {pairs}."

    # Replace the last AI message in-place (same id) to avoid duplicate output
    for msg in reversed(state["messages"]):
        if msg.type == "ai" and not getattr(msg, "tool_calls", None):
            return {"messages": [AIMessage(id=msg.id, content=str(msg.content) + notice)]}

    return {"messages": [AIMessage(content=notice)]}
