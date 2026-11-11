#!/bin/bash
# Links the orchestrate agent definitions into a project (or globally with --global), for Claude Code and Codex.
# Usage: install_agents.sh --global [--codex-only]   |   install_agents.sh <repo> [--codex-only]
# Prefer --global: project installs write absolute symlinks that break for teammates and CI if committed.
set -euo pipefail
here="$(cd "$(dirname "$0")/../agents" && pwd)"
if [ "${1:-}" = "--global" ]; then
  claude_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents"; codex_dir="${CODEX_HOME:-$HOME/.codex}/agents"
elif [ -n "${1:-}" ]; then
  claude_dir="$1/.claude/agents"; codex_dir="$1/.codex/agents"
else
  echo "usage: $0 --global|<repo> [--codex-only]" >&2; exit 2
fi
mkdir -p "$claude_dir" "$codex_dir"
# The reviewer was called orchestrate-evaluator before 2.0; drop links to it so the old name isn't offered.
for old in "$claude_dir/orchestrate-evaluator.md" "$codex_dir/orchestrate-evaluator.toml"; do
  if [ -L "$old" ]; then rm "$old"; echo "removed $old"; fi
done
if [ "${2:-}" != "--codex-only" ]; then for f in "$here"/claude/*.md; do ln -sfn "$f" "$claude_dir/$(basename "$f")"; echo "linked $claude_dir/$(basename "$f")"; done; fi
for f in "$here"/codex/*.toml; do ln -sfn "$f" "$codex_dir/$(basename "$f")"; echo "linked $codex_dir/$(basename "$f")"; done
