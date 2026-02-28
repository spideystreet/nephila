---
name: pr-status
description: Fetch and display the full status of the current PR — CI checks, reviews, and code comments — using GitHub MCP tools. Invoke manually with /pr-status.
disable-model-invocation: true
---

# Skill: PR Status

Display a complete dashboard of the current PR's remote state.

## Steps

### 1. Identify the current PR

Run `git branch --show-current` to get the branch name, then use `git log --oneline -1` to get the HEAD SHA.

Use `mcp__github__list_pull_requests` with `head: "spideystreet:<branch>"` and `state: "open"` to find the PR number.

If no open PR is found, report: "No open PR found for branch `<branch>`."

### 2. Fetch all PR data (in parallel)

Call all four MCP tools in a **single parallel batch**:

| MCP tool | Data |
|----------|------|
| `mcp__github__get_pull_request` | Title, state, author, base/head, mergeable, draft |
| `mcp__github__get_pull_request_status` | CI check runs (name, status, conclusion) |
| `mcp__github__get_pull_request_reviews` | Reviews (author, state, body) |
| `mcp__github__get_pull_request_comments` | Code review comments (path, line, body, diff_hunk) |

### 3. Format and display

Output a single formatted dashboard:

```
## PR #<number>: <title>

**State**: <open/closed/merged> | **Branch**: <head> → <base> | **Author**: @<login>

### CI Checks

| Check | Status | Conclusion |
|-------|--------|------------|
| <name> | <status> | <conclusion> |

### Reviews

- @<reviewer>: <state> (APPROVED / CHANGES_REQUESTED / COMMENTED)
  > <body excerpt if any>

### Code Comments

- @<author> `<path>#<line>`:
  ```diff
  <diff_hunk>
  ```
  > <body>
```

If a section has no items, show "None" instead of the table/list.

## Rules

- **Always use GitHub MCP tools** — never fall back to `gh` CLI
- Use `git` CLI only for local branch detection
- Call all four MCP tools in parallel to minimize latency
- Do not modify any files or state — this is a read-only skill
- Owner and repo are always `spideystreet` / `nephila`
