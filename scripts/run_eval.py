"""
Nephila — LangSmith evaluation script.

Loads test cases from tests/e2e/prompts.yaml, syncs them to a LangSmith dataset,
runs the agent against each case, and publishes scored results to LangSmith.

Usage:
    uv run dotenv -f .env run -- python scripts/run_eval.py

Results visible at: https://smith.langchain.com → Datasets & Experiments
"""

from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langsmith import Client
from langsmith.evaluation import evaluate

load_dotenv()

PROMPTS_FILE = Path(__file__).parent.parent / "tests" / "e2e" / "prompts.yaml"
DATASET_NAME = "nephila-interaction-tests"


def _sync_dataset(client: Client, cases: list[dict]) -> None:
    """Create or refresh the LangSmith dataset from prompts.yaml."""
    datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        for ex in client.list_examples(dataset_id=str(datasets[0].id)):
            client.delete_example(ex.id)
        dataset = datasets[0]
    else:
        dataset = client.create_dataset(
            DATASET_NAME,
            description="Nephila agent interaction test cases (tests/e2e/prompts.yaml)",
        )

    client.create_examples(
        dataset_id=str(dataset.id),
        examples=[
            {
                "inputs": {"prompt": case["prompt"]},
                "outputs": {
                    "expect_warn": case.get("expect_warn", False),
                    "expect_in": case.get("expect_in", []),
                    "expect_not": case.get("expect_not", []),
                },
                "metadata": {"id": case["id"]},
            }
            for case in cases
        ],
    )
    print(f"  {len(cases)} examples synced to '{DATASET_NAME}'")


def interaction_evaluator(
    inputs: dict,  # noqa: ARG001
    outputs: dict,
    reference_outputs: dict,
) -> dict:
    """Score the agent response against expected patterns defined in prompts.yaml."""
    messages = outputs.get("messages", [])
    last = messages[-1] if messages else None
    response: str = (getattr(last, "content", None) or str(last) or "") if last else ""
    response_lower = response.lower()

    errors: list[str] = []

    for term in reference_outputs.get("expect_in", []):
        if term.lower() not in response_lower:
            errors.append(f"missing: '{term}'")

    for term in reference_outputs.get("expect_not", []):
        if term.lower() in response_lower:
            errors.append(f"unexpected: '{term}'")

    has_warn = "⚠️" in response
    if reference_outputs.get("expect_warn") and not has_warn:
        errors.append("missing warn notice")
    elif not reference_outputs.get("expect_warn") and has_warn:
        errors.append("unexpected warn notice")

    return {
        "key": "interaction_check",
        "score": 0 if errors else 1,
        "comment": "; ".join(errors) if errors else "OK",
    }


def main() -> None:
    from nephila.agent.graph_agent import build_agent

    cases: list[dict] = yaml.safe_load(PROMPTS_FILE.read_text())
    client = Client()

    print(f"Syncing {len(cases)} cases → LangSmith dataset '{DATASET_NAME}'...")
    _sync_dataset(client, cases)

    agent = build_agent()

    def target(inputs: dict) -> dict:
        result = agent.invoke({"messages": [HumanMessage(content=inputs["prompt"])]})
        return {"messages": result["messages"]}

    print("Running evaluation (sequential, 1 case at a time)...")
    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[interaction_evaluator],
        experiment_prefix="nephila",
        max_concurrency=1,
    )

    print(f"\nExperiment: {results.experiment_name}")
    print("View results → https://smith.langchain.com → Datasets & Experiments")


if __name__ == "__main__":
    main()
