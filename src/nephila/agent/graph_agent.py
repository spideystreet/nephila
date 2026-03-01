"""
Nephila ReAct agent — LangGraph graph definition.
Architecture: agent (LLM + tools) → guardrail → response|warn
"""

import threading
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from pydantic import SecretStr

from nephila.agent.model_state import AgentState
from nephila.agent.nodes.node_guardrail import guardrail_node, should_warn
from nephila.agent.nodes.node_response import response_node
from nephila.agent.nodes.node_warn import warn_node
from nephila.agent.tools.tool_check_interactions import check_interactions
from nephila.agent.tools.tool_find_generics import find_generics
from nephila.agent.tools.tool_get_rcp import get_rcp
from nephila.agent.tools.tool_search_drug import search_drug
from nephila.pipeline.config_pipeline import PipelineSettings

TOOLS = [search_drug, find_generics, check_interactions, get_rcp]
RECURSION_LIMIT = 25

SYSTEM_PROMPT = """\
Tu es un assistant pharmaceutique français spécialisé dans la BDPM.

RÈGLES OBLIGATOIRES :
1. Toujours appeler check_interactions avant toute recommandation.
2. Ne jamais donner de conseil médical direct — toujours citer le RCP.
3. Toujours inclure le code CIS quand tu mentionnes un médicament.
4. Rapporter chaque interaction trouvée avec son niveau de contrainte ANSM.
5. Si check_interactions ne trouve pas d'interaction, le signaler tel quel \
— ne jamais compléter avec des connaissances pharmacologiques hors outil.

FORMAT DE RÉPONSE — STRICT :
- Direct et concis. 3 à 5 phrases maximum.
- Prose simple, pas de listes à puces ni titres.
- Ne jamais poser de questions de suivi.
- Énoncer le niveau d'interaction, le risque et la précaution clé."""


def routing(state: AgentState) -> str:
    """Conditional edge: route to tools if there are pending tool calls, else to guardrail."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "guardrail"


def build_agent() -> CompiledStateGraph:  # type: ignore[type-arg]
    settings = PipelineSettings()

    llm = ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=SecretStr(settings.openrouter_api_key),
        model=settings.openrouter_model,
        default_headers={"X-Title": "Nephila"},
    )
    # Sequential tool calls required: guardrail inspects ALL tool results before routing.
    llm_with_tools = llm.bind_tools(TOOLS, parallel_tool_calls=False)

    def agent_node(state: AgentState) -> dict[str, Any]:
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return {"messages": [llm_with_tools.invoke(messages)]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("response", response_node)
    builder.add_node("warn", warn_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", routing, {"tools": "tools", "guardrail": "guardrail"})
    builder.add_edge("tools", "agent")
    builder.add_conditional_edges(
        "guardrail", should_warn, {"response": "response", "warn": "warn"}
    )
    builder.add_edge("response", END)
    builder.add_edge("warn", END)

    return builder.compile()


_graph: CompiledStateGraph | None = None  # type: ignore[type-arg]
_graph_lock = threading.Lock()


def get_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Lazy singleton — avoids requiring env vars at import time."""
    global _graph  # noqa: PLW0603
    if _graph is None:
        with _graph_lock:
            if _graph is None:
                _graph = build_agent()
    return _graph


# LangGraph Studio / langgraph dev expects a module-level `graph` attribute.
# Use __getattr__ so the graph is only built when actually accessed at runtime.
def __getattr__(name: str) -> object:
    if name == "graph":
        return get_graph()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
