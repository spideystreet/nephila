---
name: pr
description: Create a GitHub pull request following Nephila conventions (author spicode-bot, reviewer spideystreet). Invoke manually with /pr — do NOT trigger automatically.
disable-model-invocation: true
---

# Skill: Pull Request

Create a GitHub PR following the conventions defined in `.claude/rules/git.md`.

## Steps

1. `git log main..HEAD --oneline` — review commits included
2. Push if needed: `git push -u origin <branch>`
3. Create PR:
   ```bash
   gh pr create \
     --title "<type>(<scope>): <summary>" \
     --body "$(cat <<'EOF'
   ## Summary

   - <bullet point>

   ## Test plan

   - [ ] `uv run pytest <tests> -v`
   - [ ] Manual: <scenario>

   🤖 Generated with [Claude Code](https://claude.ai/claude-code)
   EOF
   )"
   ```
4. `gh pr edit --add-reviewer spideystreet`
