#!/usr/bin/env python3
"""PreToolUse nudge before a call that hands a prompt to another agent: Agent (Task on older Claude Code),
SendMessage, or a Bash command that starts `codex exec`, `claude -p` or `codexctl send|start|goal`.

The first such call in a context is refused once with a one-line nudge to apply instructing-agents; the resend
passes. It nudges again after compaction or a long stretch of transcript. Each agent (main session or subagent)
has its own state, so subagents aren't stuck. Fails open on any error.

Shipped with the instructing-agents plugin (hooks/hooks.json next to this file), so installing the plugin
installs the hook. Off in any folder under a path listed in INSTRUCTING_AGENTS_NUDGE_SKIP (os.pathsep-separated);
the default is ~/Workspace/scratch/ia-trial, where trigger trials measure the skill description without the hook.
"""
import hashlib, json, os, re, sys, time

# A launch only at the start of the command or after a shell separator, so prose in a commit message doesn't count.
LAUNCH = re.compile(r'(^|[;&|(]\s*|\bthen\s+|\bdo\s+)(\S*/)?(codex\s+(exec|e)\s|claude\s+(\S+\s+)*-p(\s|$)|(python3?\s+)?\S*codexctl(\.py)?\s+(send|start|goal)\b)')
NUDGE = "This hands a prompt to another agent. Apply the instructing-agents skill to it, then resend."
HANDOFF_TOOLS = ("Agent", "Task", "SendMessage")
REWARN_BYTES = 400_000  # heuristic, not measured: transcript bytes run well ahead of conversation tokens
DEFAULT_SKIP = "~/Workspace/scratch/ia-trial"


def state_dir():
    # The plugin's own data folder when the host provides one; else beside the host's config.
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("PLUGIN_DATA")
    if base:
        return os.path.join(base, "handoff-nudge")
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(config, "hooks", ".state")


def skipped(cwd):
    cwd = os.path.realpath(cwd or os.getcwd())
    for entry in os.environ.get("INSTRUCTING_AGENTS_NUDGE_SKIP", DEFAULT_SKIP).split(os.pathsep):
        if entry and cwd.startswith(os.path.realpath(os.path.expanduser(entry))):
            return True
    return False


def size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def compacted_since(path, offset):
    try:
        with open(path, "rb") as f:
            f.seek(offset)
            return b'"compact_boundary"' in f.read()
    except OSError:
        return False


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    if tool == "Bash":
        if not LAUNCH.search((data.get("tool_input") or {}).get("command", "") or ""):
            return
    elif tool not in HANDOFF_TOOLS:
        return
    if skipped(data.get("cwd", "")):
        return
    path = data.get("transcript_path", "") or ""
    key = hashlib.sha1(f'{data.get("session_id","")}|{data.get("agent_id","")}|{path}'.encode()).hexdigest()
    state = state_dir()
    os.makedirs(state, exist_ok=True)
    marker = os.path.join(state, key)
    now = size(path)
    try:
        with open(marker) as f:
            at = int(f.read().strip() or 0)
        if now - at < REWARN_BYTES and not compacted_since(path, at):
            return
    except (OSError, ValueError):
        pass
    with open(marker, "w") as f:
        f.write(str(now))
    for name in os.listdir(state):  # drop state older than a week
        p = os.path.join(state, name)
        if time.time() - os.path.getmtime(p) > 7 * 86400:
            os.remove(p)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
        "permissionDecision": "deny", "permissionDecisionReason": NUDGE}}))


try:
    main()
except Exception:
    pass
