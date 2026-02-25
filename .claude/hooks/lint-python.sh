#!/bin/bash
# Auto-lint Python files after Edit/Write tool use.
# Receives tool input as JSON on stdin.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ "$FILE_PATH" =~ \.py$ ]] || exit 0

uv run ruff check --fix "$FILE_PATH" 2>/dev/null
uv run ruff format "$FILE_PATH" 2>/dev/null
exit 0
