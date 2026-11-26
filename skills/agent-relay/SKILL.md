---
name: agent-relay
description: Runs another coding agent's CLI from inside this one, through one command for Claude Code, Codex and Antigravity. Starts, resumes and stops a turn, messages a running session, shows one in its desktop app, and reads quota, banked resets and the model catalogue, with the same JSON result from every host. Use when you need another agent or model to do a piece of work, a second opinion from a different vendor's model, to wake or steer a session that is already running, or to check how much quota each host has left. Not for spawning your own host's subagents, which its own tools do better.
license: MIT
---

# agent-relay

`scripts/relay.py` in this skill's folder drives the three agent CLIs, `claude`, `codex` and `agy` (Antigravity),
through their documented interfaces, and gives back the same JSON whichever host did the work. It needs Python 3.10
or later and nothing else, and it uses each CLI's own sign-in, so a run is charged to that host's plan.

Run `python3 <this folder>/scripts/relay.py check` first. It says which CLIs are installed and signed in, and which
operations each one can do here. The help (`relay.py <command> --help`) lists every option.

## Running a turn

```bash
relay.py run --host codex --cwd <repo> --model gpt-6.2-sol --effort medium --mode workspace-write "<prompt>"
relay.py run --host claude --cwd <repo> --session <id> "<the next message>"
```

A run is one turn: it returns when the agent has finished, with `session`, the ID to resume it with, `text`, the
agent's last message, `usage` and `status`. Give the prompt as `-` to read it from stdin, or `@file`. A prompt for
another agent should stand on its own, since that agent hasn't seen this conversation; the prompting-agents skill,
if you have it, covers how to write one.

`status` is what to act on. `done` means the host finished the turn, which isn't the same as the work being right:
read `text` and check the result as you would your own. `limited` means a usage limit stopped it, so another host or
a later time is the answer, not a retry. `refused` means Antigravity refused a tool call without stopping, so the
agent may have skipped a step it needed. `interrupted`, `timeout` and `failed` are what they say, and `unsupported`
means the host has no route for that operation: `text` says why.

`--mode` passes the host's own permission setting through by its own name, because the three hosts don't mean the
same thing by it: Claude's `--permission-mode`, Codex's `--sandbox`, Antigravity's agent mode. Leave it out to keep
the user's configuration. Choose the narrowest mode that lets the work get done, and ask the user before you choose a
mode that skips their approvals, since that is their decision about their machine.

Run the relay outside any sandbox your own host puts commands in. Inside Codex's sandbox, another agent's CLI can't
reach the network or read its own sign-in, so it fails as signed out, and the result's warnings say so. Ask for the
command to run outside the sandbox the way your host asks for any such command; if that isn't possible, tell the user,
since loosening the sandbox is their decision.

For what a model is good at and which efforts it takes, `relay.py models` prints the catalogue. For how each CLI
behaves beyond what the relay sets, read the vendor's own documentation, which is current where this skill isn't:
[Claude Code headless](https://code.claude.com/docs/en/headless),
[Codex non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode), and
[Antigravity headless mode](https://antigravity.google/docs/cli/headless/).

## Sessions that are already running

| | Claude Code | Codex | Antigravity |
|---|---|---|---|
| `stop` | a turn the relay started | a turn the relay started | a turn the relay started |
| `send` | the session's inbox, live sessions only | the thread's queue | not available |
| `status` | any live session | the relay's own runs; others read `unknown` | the relay's own runs |
| `open` | in Claude Desktop, once the turn has ended | in the Codex app (macOS) | not available |

`send` to Claude reaches a session the relay started, the session your command runs inside, or any session whose
inbox socket you pass with `--socket` (its `/status` shows it as the Peer address). A Claude session with no live
process has no inbox; resume it with `run --session` instead. `send` to Codex queues the message: a thread that the
Codex app or the app-server daemon holds runs it once idle, and any other thread runs it at its next resume.

## Quota and banked resets

`relay.py quota` shows each host's usage windows, how fast each is being used, and the banked resets the user holds,
with a plan for when each would be worth redeeming. None of the reads runs a model. The relay never redeems a banked
reset, and neither should you: tell the user what the plan says and leave the decision with them, because a reset
redeemed early gives back less of their quota.

## Experimental: Codex in the desktop app

`run --host codex --app` runs the turn in the Codex app, where the user can watch and steer it. OpenAI documents no
way for another program to do this, so it rests on undocumented app behaviour and may break with an app update; its
result carries a warning saying so. Use it when the user asks to see the work in the app, and run headless
otherwise.
