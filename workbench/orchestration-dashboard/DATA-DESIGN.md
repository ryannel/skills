# Delivery history and dashboard for orchestrate

Status: built in orchestrate 2.5.0 (`delivery_history.py`, `dashboard.html`, the `history` and `dashboard`
commands). Thrum's backfill: 2,355 sessions, 17,346 turns, 172 milestones, about 12 MB on disk and a 5 MB page.
`render.sh` here re-draws `preview.html` from it.

## What it is for

Two kinds of reader use the same records.

The human reviews a delivery:

1. **How is the project going?** Milestones Done over time, what is Waiting or Blocked, how many builders and
   reviewers ran, what it has cost so far.
2. **What did a version of the script or skills change?** Cost per milestone, failed-review rate, compactions, time
   to Done and errors, before and after each orchestrate release.
3. **The retro.** What the project cost by module, role, model and host, where the spend bought nothing, and what
   to change next time.

An agent diagnoses the orchestration itself. It needs the failures: turns that failed, timed out or were stopped,
with the host's error; results the script refused; failed checks; usage limits hit; turns that ran on a model other
than the one pinned; compactions; reviews that failed, with their repeated findings. It needs them as JSON it can
query, linked to the session, milestone and version they came from, so it can propose a fix to a skill or to
`agent_loop.py` and later check whether the fix worked.

## The principle: extract once, then the transcripts can go

Claude Code and Codex transcripts are raw input, not the record. Claude deletes them after 30 days. Codex keeps
them, but they total 48 GB on this machine and move when the app changes its storage. The importer reads each
session's file, writes down what the dashboard needs, and from then on everything reads only what it wrote.

- **Numbers, names, times and outcomes; no conversation.** It keeps tokens by kind, models, compactions, tool counts
  and timings, errors and how each turn ended. It keeps no message text, tool output or screenshots. A session
  comes down to a few KB.
- **Tagged when written.** Module, milestone, role and script version go on the row while the ledger and titles
  that identify them still exist.
- **Safe to run again.** Rows are keyed by host, session and turn id, and each file's read position is saved, so a
  second run adds nothing and a growing session is read from where the last run stopped.
- **Kept outside everything that gets cleaned up**: `~/.orchestrate/history/<project>/`, or
  `$ORCHESTRATE_HISTORY_DIR`. Not in the hosts' folders, and not only in `.git/`, which goes with the clone.

## One importer, one source of truth

The importer is the only thing that turns host files into rows. The script's per-turn ledger row is not widened
in parallel. The ledger's job becomes tagging: it says which session served which module, milestone and role.

**Tokens come from the host's own files, never from the ledger**, wherever the host file still exists. The ledger's
Codex rows from before 2.1.0 count a resumed session's earlier tokens again. The ledger is used for tokens only
for a session whose host file is gone, and those rows are marked `from_ledger`.

**One row per host turn.** A Codex turn runs from `task_started` to `task_complete` or `turn_aborted`. Its tokens
are the sum of its `token_usage_record` lines, one per model response, deduplicated by response id. Older
rollouts without those lines fall back to the rise in `token_count.total_token_usage` across the turn. A Claude
turn runs from one prompt the human or the script typed to the next. Claude writes one line per content block and
repeats the message's usage on each, so usage is deduplicated by message id.

**Running totals are never summed.** Codex's `total_token_usage` and Claude's `cost-state` are totals for the whole
session, and a resumed Claude session carries its predecessors' totals.

**Auto-review and subagent threads are sessions of their own**, each pointing to the session it served, or to
`unknown`. They are never folded into a builder's turn, so nothing is counted twice. Codex auto-review rollouts
carry `parent_thread_id` in `session_meta`. Codex subagents carry it in `source.subagent.thread_spawn`. Claude
subagents are separate files under `<session>/subagents/`.

**Tags** come from, in order: the ledger row for that session, closest in time to the turn; the thread ledger and
the script's session titles; the parent session, for auto-review and subagents; otherwise `interactive`. Before the
script existed there is no way to tell the lead's sessions from the human's, so both are `interactive`.

## Measuring cost

The hosts bill the plans, not the API, so there is no true dollar figure. Three measures are kept, each labelled
for what it is:

- **Tokens by kind**: `prompt` (all input), `cache_read`, `cache_write` (Claude split into 5-minute and 1-hour),
  `output`, `reasoning`. Fresh input is `prompt - cache_read - cache_write`.
- **Weighted tokens**, the cross-host measure. Each kind is weighted by its price relative to fresh input. For
  Claude: cache read 0.1, 5-minute write 1.25, 1-hour write 2, output 5. For Codex: cached 0.1, output 8, as
  `codex_quota.py` uses. A turn that re-reads a large cached context then weighs what it costs, instead of
  dominating a raw token count. (14.0B of Thrum's 14.2B Codex ledger tokens are cache reads.)
- **Claude list price in USD**, from each model's own `costUSD` in Claude's `cost-state`, spread over turns by
  weighted tokens. **Codex share of the weekly limit**, from `codex_quota.py`'s fitted tokens-to-percent figure.
  Whole-percent snapshots are kept only as events when they change.

## What is stored

| File | One row per | Holds |
|---|---|---|
| `sessions.jsonl` | host session | host, kind (`script`, `interactive`, `auto-review`, `subagent`), parent, tags, model and effort, CLI version, folder, start and end, turns, totals, compactions |
| `turns.jsonl` | host turn | tags, start, end, duration, time to first token, model, effort, tokens by kind, weighted tokens, USD (Claude), model calls, peak context and window, tool calls as `{name: [count, ms, errors]}`, how it ended, script version |
| `events.jsonl` | rare thing | errors and signals, listed below, each with time, session, turn, tags and a short detail |
| `milestones.jsonl` | milestone | module, id, status, size (done-when items), authorised, Ready for Review and Done times, each review's verdict, time, host, model and findings with repeats |
| `checks.jsonl` | automated check run | command, exit, time |
| `state.json` | source file | read position, size and time last read |

**Events.** Errors: `turn_failed` (with a class read from stderr: `auth`, `usage_limit`, `model`, `app`, `other`),
`turn_timed_out`, `turn_stopped`, `host_error`, `turn_aborted`, `script_refused` (results such as `ERROR`, `INVALID`,
`BLOCKED`, `DESIGN_NOT_APPROVED`), `check_failed`, `off_pinned_model`, `goal_limited`. Signals: `compaction` (Claude
with tokens before and after and time taken; Codex with before and after taken from the token counts around it),
`limit_changed`, `review_failed`, `version_seen`.

**Size.** One row per turn, not per model call. Thrum's threads average 150 model calls and 150 tool calls per
turn-and-a-half, so per-call rows would be about 30 MB, while per-turn rows are well under 1 MB. The whole folder is
a few MB for Thrum. No rollover, compression or branch until it is bigger than that.

**Never extracted**: message text, tool output, screenshots, check logs (62 MB in Thrum), job output (14 MB).

## Step 1: the backfill

The same importer, run over everything still on disk for the project:

- **Codex**: the thread index (`~/.codex/state_5.sqlite`, threads whose folder is the repository or one of its
  worktrees) gives the thread list, and each rollout is found by id under `sessions/` and `archived_sessions/`
  (`.jsonl.zst`, read with the standard library's `compression.zstd`). The index's `rollout_path` can be stale.
- **Claude**: the project folders under `~/.claude/projects/` named after the repository and its worktrees, and
  each session's `subagents/` folder.
- **The script's ledgers**: `usage.jsonl` and `threads.jsonl` for tags, `results/` for refusals, `checks/` for checks.
- **The plan**: each module's record and done-when file at the main branch's tip give the milestones and their
  reviews.

There is no cloud endpoint that returns old plan sessions. The Codex app-server and Claude's OpenTelemetry export
only serve sessions from now on, and the Anthropic and OpenAI usage APIs only cover API keys.

## Step 2: as it runs

- After each turn the script runs, it extracts that session.
- `report`, `history` and `dashboard` sweep for every session that ended without being extracted: the app's turns,
  auto-review threads, subagents, interactive sessions.
- Plan rows in the ledger get the module and milestone they plan for, when there is one.
- Every result the script prints is appended to `<git dir>/orchestrate/results.jsonl` with its time, so the history
  of results survives the `results/` files being overwritten.

## The dashboard

`dashboard` writes one self-contained HTML file, with the data embedded, to the history folder, and can open it.
`dashboard --json` prints the same model for an agent. `history --json` prints the summary and the latest
errors.

Views: overview, spend, agents, milestones, errors, versions, retro. Release markers sit on every time chart.
Versions are compared per milestone and by milestone size, with the count on each side shown.

## What the review changed

An independent review checked the first draft against the real files. What it changed:

- Ledger tokens were going to be copied. They double count resumed sessions before 2.1.0, so tokens now come from
  host files.
- Auto-review cost was in three places. It is now in one: its own sessions.
- Claude subagents are separate files, not side-chain lines. Claude usage repeats per content block.
- Auto-review threads can't be joined by folder and time reliably. Most of Thrum's ran in the root folder for the
  human's own threads. They now use `parent_thread_id`, or `unknown`.
- Codex subagent threads (about 400, 2.4B tokens in Thrum) were missing.
- Plan rows carry no module, lock and check records carry no milestone, and `results/` keeps only the latest
  file. Step 2 now records those.
- Per-turn limit snapshots were dropped, since whole percents rarely move within a turn.
- Branch storage, hourly lock rollups, monthly rollover and gzip were dropped until the data needs them.
- Claude's transcripts for Thrum go back to 3 Nov, so the 30-day deletion starts around 3 Dec, not already.
