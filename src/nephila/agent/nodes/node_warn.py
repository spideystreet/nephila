"""Warn node — prepends a structured interaction warning to the agent's response."""

from langchain_core.messages import AIMessage

from nephila.agent.model_state import AgentState

CRITICAL_LEVELS = frozenset({"contre-indication", "association déconseillée"})


def warn_node(state: AgentState) -> dict:
    """Prepend critical interaction warnings to the agent's response instead of blocking it."""
    critical = [
        i
        for i in state.get("interactions_found", [])
        if i.get("niveau_contrainte", "").lower() in CRITICAL_LEVELS
    ]

    warning_lines = "\n".join(f"• [{i['niveau_contrainte']}] {i['detail']}" for i in critical)

    warning_prefix = (
        "⚠️ INTERACTIONS CRITIQUES DÉTECTÉES (ANSM Thésaurus) :\n\n"
        f"{warning_lines}\n\n"
        "Toute décision thérapeutique doit être validée avec un professionnel de santé "
        "et le RCP officiel du médicament.\n\n"
        "---\n\n"
    )

    # Replace the last AI message in-place (same id) to avoid duplicate output
    for msg in reversed(state["messages"]):
        if msg.type == "ai" and not getattr(msg, "tool_calls", None):
            return {"messages": [AIMessage(id=msg.id, content=warning_prefix + msg.content)]}

    return {"messages": [AIMessage(content=warning_prefix)]}
