#!/bin/bash
# PreToolUse guard: block obviously destructive Bash commands.
# Claude Code calls this before executing a Bash tool call.
# Exit 2 = block the tool call; Claude sees the stderr message.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

[[ "$TOOL_NAME" == "Bash" ]] || exit 0

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

block() {
  echo "BLOCKED: $1" >&2
  echo "Command was: $COMMAND" >&2
  exit 2
}

# Destructive file operations
[[ "$COMMAND" =~ rm[[:space:]]+-[^[:space:]]*r[^[:space:]]*[[:space:]]+-[^[:space:]]*f ]] && block "rm -rf detected"
[[ "$COMMAND" =~ rm[[:space:]]+-[^[:space:]]*f[^[:space:]]*[[:space:]]+-[^[:space:]]*r ]] && block "rm -rf detected"

# Hard git resets
[[ "$COMMAND" =~ git[[:space:]]+reset[[:space:]]+--hard ]] && block "git reset --hard detected"
[[ "$COMMAND" =~ git[[:space:]]+checkout[[:space:]]+\. ]] && block "git checkout . (discards all changes) detected"
[[ "$COMMAND" =~ git[[:space:]]+restore[[:space:]]+\. ]] && block "git restore . (discards all changes) detected"
[[ "$COMMAND" =~ git[[:space:]]+clean[[:space:]]+-[^[:space:]]*f ]] && block "git clean -f detected"

# Force push
[[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+.*--force ]] && block "git push --force detected"
[[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+.*-f[[:space:]] ]] && block "git push -f detected"
[[ "$COMMAND" =~ git[[:space:]]+push[[:space:]]+-f$ ]] && block "git push -f detected"

exit 0
