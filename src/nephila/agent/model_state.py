from typing_extensions import NotRequired

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    cis_codes: NotRequired[list[str]]
    interactions_found: NotRequired[list[dict]]
    interactions_checked: NotRequired[bool]
    source_cis: NotRequired[str | None]
