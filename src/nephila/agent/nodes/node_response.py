"""Response node — extracts CIS traceability metadata from the conversation."""

import re

from langchain_core.messages import ToolMessage

from nephila.agent.model_state import AgentState


def response_node(state: AgentState) -> dict:
    """Extract the primary source_cis from tool results for traceability."""
    source_cis: str | None = None

    for msg in state["messages"]:
        if isinstance(msg, ToolMessage) and "CIS " in msg.content:
            match = re.search(r"CIS (\d+)", msg.content)
            if match:
                source_cis = match.group(1)
                break

    return {"source_cis": source_cis}
