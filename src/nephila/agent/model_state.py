from collections.abc import Sequence
from typing import Any, NotRequired

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState

CRITICAL_LEVELS: frozenset[str] = frozenset({"contre-indication", "association déconseillée"})


def last_human_message_idx(messages: Sequence[BaseMessage]) -> int:
    """Return the index of the most recent HumanMessage, or 0 if none found."""
    for i in range(len(messages) - 1, -1, -1):
        if getattr(messages[i], "type", None) == "human":
            return i
    return 0


class AgentState(MessagesState):
    cis_codes: NotRequired[list[str]]
    interactions_found: NotRequired[list[dict[str, Any]]]
    source_cis: NotRequired[str | None]
