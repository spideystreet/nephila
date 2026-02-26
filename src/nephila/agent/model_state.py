from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    cis_codes: list[str]
    interactions_found: list[dict]
    interactions_checked: bool
    source_cis: str | None
