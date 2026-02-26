"""
CLI entry point for interacting with the Nephila agent.
Streams LangGraph events to stdout for local observability.

Usage:
    uv run python -m nephila.agent.cli_agent "Quelles interactions avec l'amiodarone ?"
"""
import sys

from langchain_core.messages import HumanMessage

from nephila.agent.graph_agent import graph


def run(query: str) -> None:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    for event in graph.stream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="updates",
    ):
        for node, data in event.items():
            print(f"[{node}]")
            msgs = data.get("messages", [])
            for msg in msgs:
                role = getattr(msg, "type", "msg")
                content = getattr(msg, "content", "")
                tool_calls = getattr(msg, "tool_calls", [])
                if tool_calls:
                    for tc in tool_calls:
                        print(f"  → tool_call: {tc['name']}({tc['args']})")
                elif content:
                    print(f"  {role}: {content[:300]}{'...' if len(content) > 300 else ''}")

            if "source_cis" in data and data["source_cis"]:
                print(f"  source_cis: {data['source_cis']}")
            if "interactions_found" in data and data["interactions_found"]:
                print(f"  interactions: {len(data['interactions_found'])} found")
            print()


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Quels médicaments contiennent du paracétamol ?"
    run(query)
