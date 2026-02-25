from typing import Annotated

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    cis_codes: list[str] = Field(default_factory=list)
    interactions_found: list[dict] = Field(default_factory=list)
    interactions_checked: bool = False
    source_cis: str | None = None
