"""Warn node — emits a structured warning when critical drug interactions are detected."""
from langchain_core.messages import AIMessage

from nephila.agent.model_state import AgentState

CRITICAL_LEVELS = frozenset({"contre-indication", "association déconseillée"})


def warn_node(state: AgentState) -> dict:
    """Generate a warning response blocking the answer when critical interactions are found."""
    critical = [
        i for i in state.interactions_found
        if i.get("niveau_contrainte", "").lower() in CRITICAL_LEVELS
    ]

    warning_lines = "\n".join(
        f"• [{i['niveau_contrainte']}] {i['detail']}" for i in critical
    )

    message = AIMessage(
        content=(
            "DRUG INTERACTION ALERT\n\n"
            "Critical interactions detected — a direct response cannot be provided:\n\n"
            f"{warning_lines}\n\n"
            "Please consult the official RCP and a healthcare professional "
            "before any therapeutic decision.\n"
            "Source: ANSM Thésaurus des interactions médicamenteuses."
        )
    )
    return {"messages": [message]}
