#!/usr/bin/env python3
"""PreToolUse nudge before a call that hands a prompt to another agent: Agent (Task on older Claude Code),
SendMessage, or a Bash command that starts `codex exec`, `claude -p`/`--print` or `codexctl send|start|goal`.

The first such call in a context is refused once with a one-line nudge to apply instructing-agents; the resend
passes. It nudges again after compaction or a long stretch of transcript. Each agent (main session or subagent)
has its own state, so subagents aren't stuck. Fails open on any error.

A Bash launch counts at the start of the command or after a separator (; & | ( ` newline, `then`, `do`), behind
any `env`, `nohup`, `time`, `timeout N` or `NAME=value` prefixes. Quoted text and heredoc bodies are blanked first, so a commit message
naming a launch passes, and so does a launch inside `sh -c '...'` or a script. The orchestrate loop's own launches
aren't matched: their prompts are templates the loop owns.

Shipped with the instructing-agents plugin as an inline `hooks` object in its entry in
.claude-plugin/marketplace.json, so installing the plugin installs the hook. Off in any folder under a path listed
in INSTRUCTING_AGENTS_NUDGE_SKIP (os.pathsep-separated); the default is ~/Workspace/scratch/ia-trial, where trigger
trials measure the skill description without the hook.
"""
import hashlib, json, os, re, sys, time

HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?^\s*\2\s*$", re.DOTALL | re.MULTILINE)
QUOTED = re.compile(r"""\$?'[^']*'|"(?:\\.|[^"\\])*\"""")
ARG = r"[^\s;&|()`]+"
OPT = rf"\s+-{ARG}(?:\s+[^-\s;&|()`][^\s;&|()`]*)?"  # an option, perhaps with its value
PREFIX = rf"(?:(?:\w+=(?:{ARG})?|env(?:{OPT})*|nohup|time|timeout(?:{OPT})*\s+{ARG})\s+)*"
LAUNCH = re.compile(
    rf"(?:^|[;&|(`\n]|\bthen\s|\bdo\s)\s*{PREFIX}(?:\S*/)?"
    rf"(?:codex(?:{OPT})*\s+(?:exec|e)(?:\s|$)"
    rf"|claude\s+(?:{ARG}\s+)*?(?:-p|--print)(?:\s|$)"
    rf"|(?:python3?\s+)?\S*codexctl(?:\.py)?\s+(?:send|start|goal)\b)")


def launches(command):
    """Whether a Bash command starts an agent with a prompt, judged with quoted text and heredoc bodies blanked."""
    return bool(LAUNCH.search(QUOTED.sub("Q", HEREDOC.sub(r"<<H\3", command))))


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
        if not launches((data.get("tool_input") or {}).get("command", "") or ""):
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


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
