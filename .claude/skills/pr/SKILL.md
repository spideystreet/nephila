---
name: pr
description: Create a GitHub pull request following Nephila conventions (author spicode-bot, reviewer spideystreet). Invoke manually with /pr — do NOT trigger automatically.
disable-model-invocation: true
---

# Skill: Pull Request

Create a GitHub PR following the conventions defined in `.claude/rules/git.md`.

## Steps

1. **Pre-flight: docs sync** — run `/docs-up` first to ensure docs are up to date with code changes
2. `git log main..HEAD --oneline` — review commits included
2. Push if needed: `git push -u origin <branch>`
3. Create PR using the **GitHub MCP server** (`mcp__github__create_pull_request`):
   - `title`: `<type>(<scope>): <summary>`
   - `head`: current branch
   - `base`: `main`
   - `body`:
     ```
     ## Summary

     - <bullet point>

     ## Test plan

     - [ ] `uv run pytest <tests> -v`
     - [ ] Manual: <scenario>

     🤖 Generated with [Claude Code](https://claude.ai/claude-code)
     ```
4. Add reviewer via MCP: `mcp__github__create_pull_request_review` or `gh pr edit --add-reviewer spideystreet`

## Rules

- **Always prefer GitHub MCP tools** (`mcp__github__*`) over `gh` CLI for GitHub operations (create PR, list issues, add comments, etc.)
- Use `git` CLI only for local operations (log, push, diff, status)
