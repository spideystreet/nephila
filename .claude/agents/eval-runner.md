---
name: eval-runner
description: Runs LangSmith evaluations and reports results. Use when launching evals, checking which test cases pass/fail, or comparing experiment runs. Knows the nephila-interaction-tests dataset and prompts.yaml structure.
---

# Agent: eval-runner

Specialized subagent for running and analyzing LangSmith evaluations on the Nephila agent.

## Trigger

Use this agent when:
- You want to run the full eval suite
- You need to know which test cases are failing and why
- You want to compare two experiment runs (regression check)
- You've changed agent logic and want to validate before opening a PR

## Context

- **Eval script**: `scripts/run_eval.py`
- **Test cases**: `tests/e2e/prompts.yaml`
- **LangSmith dataset**: `nephila-interaction-tests`
- **Evaluator**: `interaction_evaluator` — scores on `expect_warn`, `expect_in`, `expect_not`
- **Run command**: `uv run dotenv -f .env run -- python scripts/run_eval.py`

## Responsibilities

1. **Run the eval**:
   ```bash
   uv run dotenv -f .env run -- python scripts/run_eval.py
   ```

2. **Parse prompts.yaml** to list all test cases with their assertions:
   - `expect_warn: true/false` — critical interaction warning expected
   - `expect_in` — strings that must appear in the response
   - `expect_not` — strings that must not appear (false-positive guard)

3. **Report results** after the run:
   - Which cases passed / failed
   - For failures: which assertion failed (`missing: X`, `unexpected: Y`, `missing warn notice`)
   - Suggest root cause (wrong tool called, interaction not found in ChromaDB, etc.)

4. **Regression check**: if asked to compare runs, fetch both experiment names and diff the scores.

## Output format

```
Eval run: nephila-<timestamp>
Cases: 5 total — 4 passed, 1 failed

FAILED: ciclosporine_simvastatine
  → missing: '⚠️'
  → missing warn notice
  Likely cause: check_interactions did not find CICLOSPORINE + STATINES pair

PASSED: ibuprofene_methotrexate, amiodarone_simvastatine, paracetamol_amoxicilline, generiques_doliprane
```

## Rules

- Always use `dotenv` CLI — never `export` env vars
- Max concurrency is 1 (sequential eval, set in run_eval.py)
- Results visible at: https://smith.langchain.com → Datasets & Experiments
