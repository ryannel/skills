# agent-relay

One command line, and one Python API, for driving **Claude Code**, **Codex** and **Antigravity** from a script or
from another agent. Start a turn, resume it, stop it, message a running session, open it in its desktop app, and read
each host's quota and banked resets, and get the same JSON back whichever host did the work.

It is a thin layer over each vendor's own CLI and its documented interfaces. It doesn't call any model API itself,
so every run uses the sign-in and plan of the CLI that runs it. Python 3.10+, standard library only, nothing to
build.

Contents: [Install](#install) · [Use](#use) · [What each host can do](#what-each-host-can-do) ·
[Experimental parts](#experimental-parts) · [State](#state) · [Author and licence](#author-and-licence)

## Install

As an agent skill, so your agent knows where the CLI is and when to reach for it:

```bash
npx skills add ryannel/skills --skill agent-relay
```

In Claude Code, through this repository's marketplace:

```bash
claude plugin marketplace add ryannel/skills
claude plugin install agent-relay@ryannel-skills
```

Or use the script directly from a clone: `python3 skills/agent-relay/scripts/relay.py --help`.

You need whichever of the three CLIs you want to drive, installed and signed in: `claude`, `codex` (on its own or
bundled with the ChatGPT desktop app), and `agy`. `relay.py check` tells you what it found.

## Use

```bash
relay.py check                                     # which CLIs are installed, signed in, and what each can do
relay.py run --host codex --cwd ~/repo --model gpt-6.2-sol --effort medium "Fix the failing test in api/"
relay.py run --host claude --session <id> "Now add a regression test"
relay.py stop --host claude --session <id>         # SIGINT, as Ctrl-C would: the turn is saved, not torn
relay.py send --host claude --session <id> "Stop after this file; the schema changed"
relay.py status --host claude --session <id>       # busy, idle, ended or unknown
relay.py open --host codex --session <id>          # in the Codex app
relay.py quota                                     # windows, pace, banked resets and when each is worth redeeming
relay.py models --host antigravity                 # IDs, efforts, list prices, retirement dates
```

Every command prints one JSON object:

```json
{"host": "codex", "status": "done", "session": "01a2…", "text": "the agent's last message",
 "model": "gpt-6.2-sol", "effort": "medium", "usage": {"input": 5447, "cached": 15232, "output": 5},
 "transcript": "~/.codex/sessions/…/rollout-…jsonl", "warnings": []}
```

`status` is `done`, `failed`, `interrupted`, `timeout`, `limited` (a usage limit stopped the turn), `refused` (the
turn finished, but the host refused a tool call), or `unsupported` (the host has no route for that operation, and
`text` says why). The exit code is 0 for `done` and `refused`, 2 for `unsupported`, and 1 otherwise.

From Python:

```python
import sys; sys.path.insert(0, "skills/agent-relay/scripts")
from relay import hosts

result = hosts.get("antigravity").run(
    hosts.Request(prompt="Summarise the open TODOs", cwd="/path/to/repo", model="gemini-4-neon"),
    on_event=lambda event: print(event.get("type")),   # each event the host streams, as it arrives
)
print(result.status, result.session, result.text)
```

`run` also takes `should_stop` (a function; return True to stop the turn), `tick`, and `watch` (sees new output
and can end a turn whose process outlives it).

## What each host can do

| | Claude Code | Codex | Antigravity |
|---|---|---|---|
| Run, resume | `claude -p --output-format stream-json` | `codex exec --json` | `agy -p --output-format stream-json` |
| Stop a turn | SIGINT | SIGINT | SIGINT |
| Message a running session | the session's inbox socket | `codex queue` | not available |
| Busy or idle | `claude agents --json` | the relay's own runs | the relay's own runs |
| Show in the desktop app | `claude --desktop --resume` in a terminal of its own, after the turn | `codex://threads/<id>` | not available |
| Run inside the desktop app | not available | **experimental** | not available |
| Quota | `/usage` and each turn's `rate_limit_event` | app-server `account/rateLimits/read` | `/usage` |

Where a host has no route, the relay says so with `unsupported` instead of pretending, so a caller can rely on the
interface and still see the gaps.

A few details worth knowing:

- **Headless Codex runs stay out of the app.** `codex exec` threads carry the `exec` source, which the app's thread
  list leaves out by default. Labelling them as the app's own (`--thread-source vscode`) would put every run in your
  Recents, so the relay doesn't.
- **Claude sessions the relay starts can be messaged.** Each gets `crossSessionInbound: accept`, so a `-p` session
  takes a message without the approval dialog it can't show, and a SessionStart hook records where its inbox socket
  is.
- **Run it outside your agent's sandbox.** Inside Codex's `workspace-write` sandbox another agent's CLI can't reach
  the network or its own sign-in, so it fails as signed out; the result then carries a warning saying so. The relay's
  own state falls back to the temporary directory there, so the relay itself still works.
- **Antigravity runs start one at a time.** Two `agy -p` runs starting at once can resume each other's live
  conversations, so a lock holds each start until the new run has announced its conversation.
- **Quota reads cost nothing.** None of them runs a model. Readings are kept in `~/.cache/agent-relay/quota`, so the
  pace of each window and the plan for each banked reset build up over time. **The relay never redeems a banked
  reset;** that is always yours to do.

## Experimental parts

These rest on behaviour the vendor doesn't document. Each is labelled in the code and in the result's `warnings`,
and each names what would retire it.

| What | Why it's experimental | What would retire it |
|---|---|---|
| `send` to Claude: the message line's format | The inbox socket and its auth line are documented; the line carrying the message isn't | Anthropic documenting the line, or a `claude send` command |
| `run --host codex --app` | Codex documents no way for another program to start or follow a turn in its desktop app. The relay creates the thread with the app-server, queues the turn with `codex queue`, wakes the app with the undocumented `codex://threads/wake/<id>` link, and follows the session file | [openai/codex#40134](https://github.com/openai/codex/issues/40134) (let the app use an external app-server) |
| Stopping an in-app Codex turn | Only possible when the app runs on the shared app-server daemon, which [openai/codex#41014](https://github.com/openai/codex/issues/41014) currently breaks; otherwise the relay pauses the goal, clears the queue and says the turn may still be running | #40134 or #41014 |
| Threads created for the app land in Recents | The relay sets the thread's project, which the app ignores | [openai/codex#40935](https://github.com/openai/codex/issues/40935) |
| Antigravity's mode passed through `--settings` | `--mode auto` is refused in print mode and falls back to the account's default | [google-antigravity/antigravity-cli#1787](https://github.com/google-antigravity/antigravity-cli/issues/1787) |
| Antigravity's start lock | Works around concurrent starts resuming live conversations | [google-antigravity/antigravity-cli#1884](https://github.com/google-antigravity/antigravity-cli/issues/1884) |

## State

Everything the relay keeps is under `~/.cache/agent-relay` (or `$AGENT_RELAY_STATE_DIR`): records of the turns it is
running, so `stop` and `status` work from another process; the inbox sockets of Claude sessions it started; and the
quota readings. Your own model catalogue entries go in `~/.config/agent-relay/models.json`, which overrides the
shipped one entry by entry.

The binaries are found on `PATH`, or set with `AGENT_RELAY_CLAUDE`, `AGENT_RELAY_CODEX` and `AGENT_RELAY_AGY`.

## Author and licence

By [ryannel](https://github.com/ryannel), part of [ryannel/skills](https://github.com/ryannel/skills).
[Orchestrate](https://github.com/ryannel/skills/tree/main/skills/orchestration), the same author's process for
building software with AI agents, uses agent-relay for every agent it starts.

MIT licence; see [LICENSE](../../LICENSE).
