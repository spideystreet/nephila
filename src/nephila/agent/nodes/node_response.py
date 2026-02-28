"""Response node — extracts CIS traceability metadata from the conversation."""

import re
from typing import Any

from langchain_core.messages import ToolMessage

from nephila.agent.model_state import AgentState


def response_node(state: AgentState) -> dict[str, Any]:
    """Extract the primary source_cis from tool results for traceability."""
    messages = state["messages"]

    # Only inspect tool messages from the current turn (after the last HumanMessage)
    last_human_idx = 0
    for i, msg in reversed(list(enumerate(messages))):
        if getattr(msg, "type", None) == "human":
            last_human_idx = i
            break

    source_cis: str | None = None
    for msg in messages[last_human_idx:]:
        if isinstance(msg, ToolMessage) and "CIS " in str(msg.content):
            match = re.search(r"CIS (\d+)", str(msg.content))
            if match:
                source_cis = match.group(1)
                break

    return {"source_cis": source_cis}
