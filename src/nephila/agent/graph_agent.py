"""
Nephila ReAct agent — LangGraph graph definition.
Architecture: agent (LLM + tools) → guardrail → response|warn
"""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

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

SYSTEM_PROMPT = """You are a French pharmaceutical information assistant specialized in the BDPM \
(Base de Données Publique des Médicaments).

Available tools:
- search_drug: semantic search in the BDPM drug database
- find_generics: find generic equivalents by CIS code
- check_interactions: ANSM drug interaction lookup
- get_rcp: get the official RCP (Résumé des Caractéristiques du Produit)

MANDATORY RULES:
1. Always call check_interactions before any drug recommendation.
2. Never give direct medical advice — always cite the RCP as your source.
3. Always include the CIS code when referring to a specific drug.
4. Report every interaction found with its ANSM constraint level.

CRITICAL — check_interactions takes TWO substances/classes and returns only their direct
interaction.
Always pass both drugs as separate arguments. Use ANSM pharmacological class names when known:
- warfarine, acenocoumarol, fluindione → 'ANTIVITAMINES K'
- aspirin (antiagrégant dose) → 'ANTIAGREGANTS PLAQUETTAIRES'
- ciprofloxacin, levofloxacin → 'FLUOROQUINOLONES'
- fluconazole, itraconazole → 'ANTIFONGIQUES AZOLÉS'
- MAOIs → 'INHIBITEURS DE LA MAO'
- SSRIs → 'INHIBITEURS DE RECAPTURE DE LA SEROTONINE'
- statins → 'STATINES'
- NSAIDs → 'ANTI-INFLAMMATOIRES NON STÉROÏDIENS'
When the class is unknown, pass the individual substance name as fallback."""


def build_agent() -> StateGraph:
    settings = PipelineSettings()

    llm = ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        default_headers={"X-Title": "Nephila"},
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    def agent_node(state: AgentState) -> dict:
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return {"messages": [llm_with_tools.invoke(messages)]}

    def routing(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "guardrail"

    builder: StateGraph = StateGraph(AgentState)
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


graph = build_agent()
