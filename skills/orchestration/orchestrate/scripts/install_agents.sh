#!/bin/bash
# Links the orchestrate agent definitions into a project (or globally with --global), for Claude Code and Codex.
# Usage: install_agents.sh <repo>   |   install_agents.sh --global
set -euo pipefail
here="$(cd "$(dirname "$0")/../agents" && pwd)"
if [ "${1:-}" = "--global" ]; then
  claude_dir="$HOME/.claude/agents"; codex_dir="${CODEX_HOME:-$HOME/.codex}/agents"
elif [ -n "${1:-}" ]; then
  claude_dir="$1/.claude/agents"; codex_dir="$1/.codex/agents"
else
  echo "usage: $0 <repo> | --global" >&2; exit 2
fi
mkdir -p "$claude_dir" "$codex_dir"
for f in "$here"/claude/*.md; do ln -sfn "$f" "$claude_dir/$(basename "$f")"; echo "linked $claude_dir/$(basename "$f")"; done
for f in "$here"/codex/*.toml; do ln -sfn "$f" "$codex_dir/$(basename "$f")"; echo "linked $codex_dir/$(basename "$f")"; done
