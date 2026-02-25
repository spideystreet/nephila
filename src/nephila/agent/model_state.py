from typing import Annotated
from pydantic import BaseModel
from langgraph.graph.message import add_messages


class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    cis_codes: list[str] = []
    interactions_checked: bool = False
    source_cis: str | None = None
