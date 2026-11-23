# Waking the lead: the script's job

## The problem

Today the lead is woken only by processes it remembers to start: each module as a background `run`, and `watch`
in the background, started again each time it ends. On 23 Nov the Thrum lead (a Claude desktop session) sat idle
with no builders and no `watch`; only a 19-minute main-branch check was running, so nothing moved and nothing would
wake it. Any design that depends on the lead remembering fails the same way, so the script has to own it.

## What each host offers (researched 23 Nov 2026)

### Claude Code (CLI 2.1.319 and the desktop app's Code tab, 2.1.325)

- **Cross-session messaging: an inbox socket per session.** Since 2.1.224 every session binds a Unix socket and
  exports its path and a per-session token to its Bash commands as `CLAUDE_CODE_MESSAGING_SOCKET` and
  `CLAUDE_CODE_MESSAGING_TOKEN` (docs: code.claude.com/docs/en/cross-session-messaging.md, "The session's inbox
  socket"; env-vars.md). "When the receiving session is idle, Claude Code starts a new turn with the message." A
  script that sends `{"type":"auth","token":...}` first is verified as the session's own child, which the
  inbound rules deliver even when no `crossSessionInbound` setting applies. The message line is
  `{"type":"user","message":{"role":"user","content":"..."}}`; the docs don't spell that out, so I took it from the
  hint the binary prints in its debug log (`[uds-messaging] Inject messages ...`).
  - **Verified:** a throwaway `claude -p` session in the scratchpad ended its turn and sat idle, waiting on a
    background `sleep`. A Python script posted the auth line and a user line to its socket. Claude Code started a
    new turn within a second, and the session wrote the file the message asked for. The transcript shows the
    `result` of the first turn, then a fresh `init` and the turn the message started.
  - **Present but not exercised:** the desktop app's sessions export the same variables (this session's
    environment has `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and a socket under `/tmp/cc-socks/`). I didn't post to a
    real desktop session, because the only one at hand is the user's own. The docs say a desktop session can't show
    the hold dialog, so a message that the inbound rules *hold* waits there unseen. A lead that bypasses permission
    prompts holds messages from senders that don't, and the token is what makes ours count as its own child.
  - **Limits:** the socket lives as long as the session's process, and a resumed session binds a new one. A
    session started with `--bare` binds none. `crossSessionInbound: refuse` drops everything.
- **A finished background task wakes the session.** `run_in_background` Bash and the Monitor tool both do this.
  It is documented for `-p` sessions (headless.md: "Claude then takes one more turn with the outcome"), and it is
  how the lead is woken today. It needs the lead to start the process, and it dies with the session.
- **Rejected for waking:** `claude -p --resume <id>` while the session is open (sessions.md: two processes write one
  transcript and messages go missing, and the open session never sees the turn). `claude --bg --resume` (for
  background sessions, not the desktop app's). Channels (`--channels`, a launch flag, research preview).
  `Notification idle_prompt` hooks (no way to inject). A `Stop` hook that blocks the stop: documented and
  workable, but it lives in the user's settings, so it is a proposal below.
- **Who the lead is:** `CLAUDE_CODE_SESSION_ID` (documented in env-vars.md), `CLAUDECODE=1`,
  `CLAUDE_CODE_ENTRYPOINT` (`claude-desktop` in the app, `sdk-cli` under `-p`), `CLAUDE_PID`.

### Codex (CLI 0.171.0-alpha.13, the desktop app's threads)

- **Who the lead is:** `CODEX_THREAD_ID` and `CODEX_SESSION_ID` (the same value) are set in every shell command
  a turn runs. Verified with a throwaway `codex exec` in the scratchpad, which printed both along with
  `CODEX_SANDBOX=seatbelt`.
- **Waking an app thread:** `codex queue --thread <id> --resume --message <text>` stores the message in
  `~/.codex/queue_1.sqlite`. The desktop app delivers a queued message to an idle thread it holds (codexctl
  README, "send"). The script already starts every visible builder turn this way (`codex_queue`), so the path is in
  daily use. The IPC socket that `codexctl send` uses to steer a running turn refuses connections today, so a
  wake can't interrupt a running turn: it waits for the turn to end, which is what we want anyway.
- **Not an app thread:** on the throwaway `exec` thread, `codex queue --resume` printed "message was queued, but
  could not resume thread ...: start a local daemon", and nothing ran (verified; the thread was then deleted with
  `codex delete --force`, which also removed the queued row). So for a lead in the Codex CLI's terminal UI, a
  queued message waits until that thread next takes a turn. The script tells the two apart by the thread's
  rollout header: `originator` `codex_work_desktop` (the app) or `orchestrate`, with `source: "vscode"`, against
  `codex_exec` / `exec` and the CLI's own.
- **Background processes:** a process started with `start_new_session` from inside a Codex turn outlived the turn
  (verified). A finished background process doesn't wake an idle Codex session, though. In the CLI the lead
  waits on `watch` in the foreground, polling it, as it does today.

### Google Antigravity (agy CLI, app and IDE)

- No documented way for another process to put a message into a live conversation. The CLI has `-p` with
  `--conversation <id>` to resume one headlessly (antigravity.google/docs/cli/headless.md), which starts a separate
  process on the conversation, the same problem as `claude -p --resume`. No environment variable carrying the
  conversation id is documented. (Antigravity isn't installed here, so none of this was run.)
- Hooks (antigravity.google/docs/hooks.md): a `Stop` hook gets `conversationId` and `fullyIdle` ("false means
  background tasks are still running"), and returning `"decision": "continue"` with a `reason` keeps the agent
  going. Hooks live in `.agents/hooks.json` in the workspace or `~/.gemini/config/hooks.json`.
- So the way in is the one every host has: a background command the lead started, whose end it notices (the
  `run_command` tool's async mode and `manage_task`). The script can't push, so it insists the lead keep `watch`
  running, and a `Lead wake` command line lets the user give a host's own way in when one appears.

## The design

### A supervisor per repository, which the script keeps alive

`agent_loop.py supervise --worktree <main checkout>` is a detached process (its own session, so it outlives the
command and the lead's turn). It holds `<git common dir>/orchestrate/supervisor.lock` with `flock` for its life,
which keeps it to one per repository. A second one finds the lock taken and exits at once.

**Started and restored by any command.** Every command that names a worktree checks the lock in `main()`. If it is
free, the project has settings, and the supervisor didn't stop for a reason that still holds, the command starts
one. So a reboot, a crash, a closed session or a lead that forgot all mend themselves the next time any agent (lead,
builder, reviewer, planner) runs any command. A machine that sleeps suspends the supervisor and it carries on when
the machine wakes. Its records are timestamps, so the check-in and the warning signs just see the time that passed.

**What it does by itself (routine):**
- Reads the records each minute and the runs every few seconds, using `watch`'s own reading (`watch_look`,
  `watch_signs`, `watch_summary`), so there is one definition of a warning sign and of what the lead is told.
- Keeps the configured number of builders busy. While the settings' `Builders:` line has a count and slots are
  free, it starts `run --module <M>` for each module whose next step is `can_start`, as the lead would, but only
  where the module's latest result left nothing for the lead. That means no result yet, or a result whose `next` is
  a plain `run` of that module, or WAITING on another module. Anything else (BLOCKED, PAUSED, CHECKS_FAILED,
  STALLED, a `--message`, a `--fresh`, a `decides: human`) waits for the lead, because those are its judgement. A
  module the user paused stays paused. No `Builders:` count means the lead hasn't asked the user yet (stage 3),
  so it starts nothing. Each `run` it starts carries on through the routine steps (`run_steps`) as today.
- Starts the main-branch checks that are due (already part of `watch_look`).

**What it wakes the lead for (judgement):** every top-level `run`, `review` or `plan` that ends, with its result and
`next`. These end only at something that isn't routine, because `run_steps` carries on through the rest. Also a
new warning sign, the lead check-in, and the end of the build: every module finished, or nothing left that can
move without the user. In both of those it wakes the lead once and exits, so a project waiting on the user doesn't
wake the lead every three hours. Wakes within a few seconds of each other go out as one message.

**When it stops:** the build is finished, nothing can move without the user and nothing is running, a whole-repo
`pause` (the user stopped everything), `supervise --stop`, or a newer copy of the script (the next command starts
the new one). It writes why to `supervisor.json`. After a stop for "finished" or "waiting on the user", a command
starts it again only once the main branch's tip has moved, which is what a `human` decision, an `adopt` or a
merged plan does. After a user's stop, only the lead's next `run`, `plan`, `watch` or `supervise` restarts it.

### Waking goes through a host adapter

The lead's commands record how to reach it in `<git common dir>/orchestrate/lead.json` (mode 600): host, session
or thread id, the Claude socket and token, its working folder. A command records this only when it is a lead's:
one of the lead's commands, not run by a session the script started (`ORCHESTRATE_ROLE`), not a step of a run,
and not run by the supervisor. Builders' `merge`, `check` and the other commands meant for them never record.

`WAKE_ADAPTERS` has one entry per way in:

| Lead on | How it is woken | Push? |
|---|---|---|
| Claude Code, CLI or desktop | a message on the session's inbox socket, with its token | yes |
| Codex desktop app thread | `codex queue --thread <id> --resume --message` | yes |
| Codex CLI | no push that runs now; `watch` in the foreground | no |
| Antigravity, any other host | the `Lead wake` command line if the user gave one; otherwise `watch` | no, unless configured |

Every wake is also written to `wake.json` with a sequence number, before any push. A live `watch` (it records its
pid in `waiter.json`) ends on the next sequence number, and the push is skipped while one is running, so a lead is
never woken twice for one thing. When a push fails (the session has gone, the socket refuses), the wake stays in
`wake.json` marked undelivered, and the lead's next command carries it as `missed_wake`.

### The script insists, so the skill needn't

Every result of a lead's command gets a `wake` field when the lead can't be reached by push and no `watch` is
running. The field names the `watch` command to start in the background, and the result also carries a loud
warning: "nothing can wake you". With a push path and a live supervisor the field is left out, so a Claude Code or
Codex-app lead never has to think about it. `watch` itself now waits on the supervisor rather than reading the
records itself. If none is running it starts one, and it starts one again if the one it waits on dies. It still
ends with the same results (CHECK_IN, WARNING_SIGNS, RUN_ENDED) and the same summary, so the lead reads a wake the
same way whichever path brought it.

New setting, in `settings --template`: `- **Lead wake:** auto`. `auto` (the default) uses the table above. `watch`
turns push off, for a user who would rather the lead were woken only by its own `watch`. A command containing
`{message}` (and optionally `{session}`) is run to wake the lead on a host the script doesn't know.

### What changes in the lead skill

Stage 4's "start each module as a background run; keep watch running and restart it" becomes: the script keeps
builders busy and wakes you. Start a `run` yourself when your judgement calls for one, such as a `--message`, a
`--fresh` or a host change. If a result carries `wake`, start that command in the background. The SKILL.md table
row for `watch` says the same.

## What I rejected

- **Making the lead's discipline stricter** (more lines in the skill). That is what failed this morning.
- **A launchd agent (or systemd unit) that keeps the supervisor alive across reboots.** It would close the last gap,
  a machine that reboots while no agent runs any command. It is a machine-wide service, though, so it stays a
  proposal for the user. The gap it closes is small, because a rebooted machine also ended the lead's session, and
  the user's next message to the lead restores everything.
- **A `Stop` hook in the user's Claude settings (or `.agents/hooks.json` for Antigravity)** that blocks the lead
  from ending a turn while work can move and nothing can wake it. This would be the host-level guarantee on hosts
  with no push. It writes user or project configuration outside this repository, so it stays a proposal.
- **`claude -p --resume <lead session>` as a push.** It forks the transcript, and the open session never sees it.
- **Steering a running Codex turn over the app's IPC.** The socket refuses connections today, and a wake should
  wait for the lead's turn to end anyway.
- **Having the supervisor make the lead's decisions** (restarting a stalled builder with `--fresh`, answering a
  BLOCKED). These are judgement, which the lead skill gives the lead.

## Proposals that need the user

1. A launchd agent `com.orchestrate.supervisor` that runs `agent_loop.py supervise --all` at login. Not built.
2. A project-level `Stop` hook for Claude Code and Antigravity leads that refuses to stop while `next`/`wake` says
   nothing can wake the lead. Not built.
3. If the user's Claude settings ever set `crossSessionInbound` to `hold` or `refuse`, the socket push stops
   working. The script reports such a push as delivered, because the socket accepted it. Worth checking once on
   Thrum: run a lead command, then `supervise --test-wake` (below) to see a test message arrive.
