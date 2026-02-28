"""Response node — extracts CIS traceability metadata from the conversation."""

import re
from typing import Any

from langchain_core.messages import ToolMessage

from nephila.agent.model_state import AgentState, last_human_message_idx


def response_node(state: AgentState) -> dict[str, Any]:
    """Extract the primary source_cis from tool results for traceability."""
    messages = state["messages"]

    source_cis: str | None = None
    for msg in messages[last_human_message_idx(messages):]:
        if isinstance(msg, ToolMessage):
            content = str(msg.content)
            if "CIS " in content:
                match = re.search(r"CIS (\d+)", content)
                if match:
                    source_cis = match.group(1)
                    break

    return {"source_cis": source_cis}
