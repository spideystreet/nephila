from typing import Annotated
from typing_extensions import NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Required — Studio uses this as the chat input
    messages: Annotated[list, add_messages]
    # Optional — populated during graph execution
    cis_codes: NotRequired[list[str]]
    interactions_found: NotRequired[list[dict]]
    interactions_checked: NotRequired[bool]
    source_cis: NotRequired[str | None]
