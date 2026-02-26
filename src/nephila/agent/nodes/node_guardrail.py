"""
Mandatory guardrail node — runs before every final response.
Parses interaction tool results and flags critical constraint levels.
"""
import re

from langchain_core.messages import ToolMessage

from nephila.agent.model_state import AgentState

CRITICAL_LEVELS = frozenset({"contre-indication", "association déconseillée"})


def guardrail_node(state: AgentState) -> dict:
    """Extract interaction records from tool messages and flag critical ones."""
    messages = state["messages"]

    # Only inspect tool messages from the current turn (after the last HumanMessage)
    last_human_idx = 0
    for i, msg in enumerate(messages):
        if getattr(msg, "type", None) == "human":
            last_human_idx = i

    interactions: list[dict] = []
    for msg in messages[last_human_idx:]:
        if not isinstance(msg, ToolMessage):
            continue
        # Match lines like "[Contre-indication] SUBSTANCE_A + SUBSTANCE_B"
        for match in re.finditer(r"\[([^\]]+)\]\s+(.+?)(?:\n|$)", msg.content):
            level, detail = match.group(1), match.group(2)
            interactions.append({"niveau_contrainte": level, "detail": detail})

    return {"interactions_found": interactions, "interactions_checked": True}


def should_warn(state: AgentState) -> str:
    """Conditional edge: route to 'warn' if a critical interaction is found, else 'response'."""
    for interaction in state.get("interactions_found", []):
        if interaction.get("niveau_contrainte", "").lower() in CRITICAL_LEVELS:
            return "warn"
    return "response"
