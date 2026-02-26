from typing import Any, NotRequired

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    cis_codes: NotRequired[list[str]]
    interactions_found: NotRequired[list[dict[str, Any]]]
    interactions_checked: NotRequired[bool]
    source_cis: NotRequired[str | None]
