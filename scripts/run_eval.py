"""
Nephila — LangSmith evaluation script.

Loads test cases from tests/e2e/prompts.yaml, syncs them to a LangSmith dataset,
runs the agent against each case, and publishes scored results to LangSmith.

Usage:
    uv run dotenv -f .env run -- python scripts/run_eval.py

Results visible at: https://smith.langchain.com → Datasets & Experiments
"""

import re
import unicodedata
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langsmith import Client
from langsmith.evaluation import evaluate

load_dotenv()

PROMPTS_FILE = Path(__file__).parent.parent / "tests" / "e2e" / "prompts.yaml"
DATASET_NAME = "nephila-interaction-tests"

CRITICAL_LEVELS = {"contre-indication", "association déconseillée"}


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


def _verify_data(cases: list[dict]) -> bool:
    """Pre-flight: call check_interactions directly for each interaction case.

    Compares the real DB constraint level with the test's expect_warn flag.
    Returns True if all cases are consistent, False if mismatches found.
    """
    from nephila.agent.tools.tool_check_interactions import check_interactions

    interaction_cases = [c for c in cases if c.get("substance_a") and c.get("substance_b")]
    if not interaction_cases:
        print("  No interaction cases with substance_a/substance_b — skipping verification.")
        return True

    print(f"\n{'=' * 72}")
    print("DATA VERIFICATION — calling check_interactions directly (no LLM)")
    print(f"{'=' * 72}\n")

    mismatches = 0
    for case in interaction_cases:
        case_id = case["id"]
        sa, sb = case["substance_a"], case["substance_b"]
        expect_warn = case.get("expect_warn", False)

        result = check_interactions.invoke({"substance_a": sa, "substance_b": sb})

        # Extract constraint levels from the tool result
        levels = re.findall(r"\[([^\]]+)\]", result)
        levels_lower = [lvl.lower() for lvl in levels]

        has_critical = any(lvl in CRITICAL_LEVELS for lvl in levels_lower)
        no_interaction = "aucune interaction" in result.lower()

        # Determine what the DB says
        if no_interaction:
            db_verdict = "no interaction found"
            db_should_warn = False
        elif has_critical:
            db_verdict = f"CRITICAL ({', '.join(levels)})"
            db_should_warn = True
        else:
            db_verdict = f"non-critical ({', '.join(levels)})"
            db_should_warn = False

        # Compare
        match = db_should_warn == expect_warn
        status = "OK" if match else "MISMATCH"
        if not match:
            mismatches += 1

        print(f"[{status}] {case_id}")
        print(f"       substances: {sa} + {sb}")
        print(f"       DB result:  {db_verdict}")
        print(f"       expect_warn={expect_warn} → DB says warn={db_should_warn}")
        if not match:
            print("       >>> TEST EXPECTATION IS WRONG or DATA IS MISSING <<<")
        print()

    print(f"{'=' * 72}")
    if mismatches:
        print(f"DATA VERIFICATION: {mismatches} MISMATCH(ES) — fix prompts.yaml or check DB data")
    else:
        print(f"DATA VERIFICATION: all {len(interaction_cases)} interaction cases consistent")
    print(f"{'=' * 72}\n")

    return mismatches == 0


def _strip_accents(s: str) -> str:
    """Lowercase and strip accents for accent-insensitive comparison."""
    nfkd = unicodedata.normalize("NFKD", s)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


def interaction_evaluator(
    inputs: dict,  # noqa: ARG001
    outputs: dict,
    reference_outputs: dict,
) -> dict:
    """Score the agent response against expected patterns defined in prompts.yaml."""
    messages = outputs.get("messages", [])
    last = messages[-1] if messages else None
    response: str = (getattr(last, "content", None) or str(last) or "") if last else ""
    response_norm = _strip_accents(response)

    errors: list[str] = []

    for term in reference_outputs.get("expect_in", []):
        term_norm = _strip_accents(term)
        # Fall back to raw comparison for non-ASCII-only terms (e.g. emoji ⚠️)
        if term_norm:
            found = term_norm in response_norm
        else:
            found = term in response
        if not found:
            errors.append(f"missing: '{term}'")

    for term in reference_outputs.get("expect_not", []):
        term_norm = _strip_accents(term)
        if term_norm:
            found = term_norm in response_norm
        else:
            found = term in response
        if found:
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
    from nephila.agent.graph_agent import RECURSION_LIMIT, build_agent

    cases: list[dict] = yaml.safe_load(PROMPTS_FILE.read_text())
    client = Client()

    # Step 0: verify test expectations against real DB data
    _verify_data(cases)

    print(f"Syncing {len(cases)} cases → LangSmith dataset '{DATASET_NAME}'...")
    _sync_dataset(client, cases)

    agent = build_agent()

    def target(inputs: dict) -> dict:
        result = agent.invoke(
            {"messages": [HumanMessage(content=inputs["prompt"])]},
            {"recursion_limit": RECURSION_LIMIT},
        )
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
