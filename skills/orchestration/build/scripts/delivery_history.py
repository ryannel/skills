#!/usr/bin/env python3
"""The delivery history: what every agent session in a project cost, how it ended and what went wrong, extracted
from the hosts' own session files into a few small JSONL files that outlive them. Standard library only.

Claude Code deletes its transcripts after 30 days, and Codex's rollouts run to tens of gigabytes and move when the
app changes its storage. So the history is read once from those files and kept as numbers, names, times and
outcomes, with no message text, tool output or screenshots. A session comes down to a few kilobytes.

The grain is one host turn: a Codex turn from `task_started` to `task_complete` or `turn_aborted`, or a Claude turn
from one typed prompt to the next. Model calls and tool calls inside a turn are summed into that turn's row. Rare
things that matter on their own, such as an error, a compaction or a change in the weekly limit, are events.

Tokens come from the host files, never from the script's usage ledger, because the ledger's Codex rows before 2.1.0
count a resumed session's earlier tokens again. The ledger tags sessions with the module, milestone and role they
served. A session whose host file is gone keeps the ledger's figures, marked `from_ledger`.

Auto-review and subagent threads are sessions of their own that point to the session they served, so nothing is
counted twice.

Files, in `$ORCHESTRATE_HISTORY_DIR/<project>/` (default `~/.orchestrate/history/<project>/`):

  sessions.jsonl    one row per host session
  turns.jsonl       one row per host turn
  events.jsonl      errors and signals
  milestones.jsonl  one row per milestone, from the plan at the main branch's tip
  checks.jsonl      one row per automated check run
  state.json        each source file's read position

`agent_loop.py` calls `extract()` and writes the milestones. The CLI here prints a summary for a history folder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
HISTORY_ROOT = Path(os.environ.get("ORCHESTRATE_HISTORY_DIR") or Path.home() / ".orchestrate" / "history")

# Price of each token kind relative to a fresh input token. Claude's are Anthropic's list ratios (cache writes kept
# for five minutes cost 1.25x, for an hour 2x). Codex's are the ratios codex_quota.py fits the weekly limit with.
WEIGHTS = {
    "claude": {"fresh": 1.0, "cache_read": 0.1, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "output": 5.0},
    "codex": {"fresh": 1.0, "cache_read": 0.1, "cache_write": 1.0, "output": 8.0},
}
TOKEN_KINDS = ("prompt", "cache_read", "cache_write", "cache_write_1h", "output", "reasoning")
REFUSALS = {"ERROR", "SCRIPT_FAILED", "INVALID", "BLOCKED", "DESIGN_NOT_APPROVED", "HOST_FAILED", "NOT_STARTED"}
TYPE_RE = re.compile(rb'"type":\s*"([A-Za-z_]+)"')
TS_RE = re.compile(rb'"timestamp":\s*"([^"]+)"')
CALL_ID_RE = re.compile(rb'(?<!\\)"call_id":\s*"([^"]+)"')
NAME_RE = re.compile(rb'(?<!\\)"name":\s*"([^"]+)"')
NAMESPACE_RE = re.compile(rb'(?<!\\)"namespace":\s*"([^"]+)"')
TOOL_USE_ID_RE = re.compile(rb'(?<!\\)"tool_use_id":\s*"([^"]+)"')
IS_ERROR_RE = re.compile(rb'(?<!\\)"is_error":\s*true')
BIG_LINE = 200_000  # lines longer than this are tool output or screenshots; read only their ids, never parse them


# ------------------------------------------------------------------------------------------------------------ basics

def parse_time(text: str | None) -> float | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def iso(ts: float | None) -> str | None:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None


def project_dir(repo: Path) -> Path:
    """The history folder for a repository: its folder name and a short hash of its path, so two clones of the same
    name never share one."""
    repo = Path(repo).resolve()
    return HISTORY_ROOT / f"{repo.name}-{hashlib.sha1(str(repo).encode()).hexdigest()[:6]}"


def lines_of(path: Path, start: int = 0):
    """(line bytes, offset after the line) from `start`. A `.zst` file, which Codex writes when it archives a thread,
    is read whole with the standard library's zstd (Python 3.14+); it never grows, so its offset is its size."""
    if str(path).endswith(".zst"):
        try:
            from compression import zstd  # type: ignore
        except ImportError:
            return
        try:
            with zstd.open(path, "rb") as handle:
                data = handle.read()
        except OSError:
            return
        size = path.stat().st_size
        for line in data.split(b"\n"):
            if line:
                yield line, size
        return
    try:
        with open(path, "rb") as handle:
            handle.seek(start)
            pos = start
            for line in handle:
                pos += len(line)
                if not line.endswith(b"\n"):
                    return  # mid-write; read it next time
                yield line, pos
    except OSError:
        return


def weighted(host: str, t: dict) -> float:
    """Tokens weighted by price relative to fresh input, the measure that compares one turn's cost with another's."""
    w = WEIGHTS.get(host) or WEIGHTS["codex"]
    write_1h = t.get("cache_write_1h", 0)
    write = t.get("cache_write", 0)
    fresh = max(t.get("prompt", 0) - t.get("cache_read", 0) - write, 0)
    if host == "claude":
        return (fresh + t.get("cache_read", 0) * w["cache_read"] + (write - write_1h) * w["cache_write_5m"]
                + write_1h * w["cache_write_1h"] + t.get("output", 0) * w["output"])
    return fresh + t.get("cache_read", 0) * w["cache_read"] + write * w["cache_write"] + t.get("output", 0) * w["output"]


def add_tokens(total: dict, t: dict) -> dict:
    for k in TOKEN_KINDS:
        if t.get(k):
            total[k] = total.get(k, 0) + t[k]
    return total


def short(text, n: int = 300) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


# ------------------------------------------------------------------------------------------------------------- Codex

def codex_effort(p: dict) -> str | None:
    return p.get("effort") or ((p.get("collaboration_mode") or {}).get("settings") or {}).get("reasoning_effort")


def read_codex(path: Path, start: int = 0, meta: dict | None = None) -> dict:
    """One Codex rollout, from byte `start`: {meta, turns, events, offset}. `offset` is just past the last line at
    which no turn was open, so the next read starts at a turn boundary and needs nothing carried over but `meta`.
    Turns still open at the end are returned with `ended` "open", and are read again in full next time."""
    meta = dict(meta or {})
    turns: dict[str, dict] = {}
    order: list[str] = []
    events: list[dict] = []
    current = None
    calls: dict[str, tuple] = {}
    last_total = None
    last_context = None
    pending_compaction = None
    limits: dict = {}
    safe = start
    tid = meta.get("id")

    def turn_for(turn_id, ts):
        nonlocal current
        if turn_id and turn_id in turns:
            return turns[turn_id]
        return current

    for line, pos in lines_of(path, start):
        head = line[:300]
        kinds = TYPE_RE.findall(head)
        if not kinds:
            continue
        top = kinds[0]
        tsm = TS_RE.search(head)
        ts = parse_time(tsm.group(1).decode()) if tsm else None
        if top == b"compacted":
            pending_compaction = {"kind": "compaction", "at": iso(ts), "turn": current["turn"] if current else None,
                                  "before": last_context}
            events.append(pending_compaction)
            if current:
                current["compactions"] = current.get("compactions", 0) + 1
            continue
        if top == b"response_item":
            sub = kinds[1] if len(kinds) > 1 else b""
            if sub in (b"function_call", b"custom_tool_call", b"local_shell_call", b"web_search_call"):
                cid = CALL_ID_RE.search(line)
                name = NAME_RE.search(line)
                ns = NAMESPACE_RE.search(line)
                label = (name.group(1).decode() if name else sub.decode())
                if ns and ns.group(1).decode() not in ("functions",):
                    label = f"{ns.group(1).decode()}.{label}"
                if current is not None:
                    tools = current.setdefault("tools", {})
                    tools.setdefault(label, [0, 0, 0])[0] += 1
                    if cid:
                        calls[cid.group(1).decode()] = (current, label, ts)
            elif sub in (b"function_call_output", b"custom_tool_call_output"):
                cid = CALL_ID_RE.search(line)
                if cid and cid.group(1).decode() in calls:
                    turn, label, t0 = calls.pop(cid.group(1).decode())
                    if t0 and ts:
                        turn["tools"][label][1] += int((ts - t0) * 1000)
            continue
        if len(line) > BIG_LINE:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        p = e.get("payload") or {}
        if top == b"session_meta":
            src = p.get("source")
            spawn = (src.get("subagent") or {}).get("thread_spawn") if isinstance(src, dict) else None
            other = (src.get("subagent") or {}).get("other") if isinstance(src, dict) else None
            tid = p.get("id") or tid
            meta.update({k: v for k, v in {
                "id": tid, "cwd": p.get("cwd"), "cli": p.get("cli_version"), "originator": p.get("originator"),
                "source": src if isinstance(src, str) else ("auto-review" if other == "guardian" else
                                                            "subagent" if spawn else json.dumps(src)[:60]),
                "thread_source": p.get("thread_source"),
                "parent": p.get("parent_thread_id") or (spawn or {}).get("parent_thread_id"),
                "nickname": (spawn or {}).get("agent_nickname"), "agent_path": (spawn or {}).get("agent_path"),
                "started": p.get("timestamp") or iso(ts)}.items() if v is not None})
            continue
        if top == b"turn_context":
            t = turn_for(p.get("turn_id"), ts)
            if t is not None:
                t["model"] = p.get("model") or t.get("model")
                t["effort"] = codex_effort(p) or t.get("effort")
            meta["model"], meta["effort"] = p.get("model") or meta.get("model"), codex_effort(p) or meta.get("effort")
            continue
        if top == b"token_usage_record":
            if p.get("thread_id") and tid and p["thread_id"] != tid:
                continue  # another thread's response, recorded here
            t = turn_for(p.get("turn_id"), ts)
            u = p.get("usage") or {}
            if t is not None:
                t.setdefault("_responses", {})[p.get("response_id") or len(t.get("_responses", {}))] = u
            continue
        if top != b"event_msg":
            continue
        sub = p.get("type")
        if sub == "task_started":
            turn_id = p.get("turn_id") or f"t{len(order)}"
            current = {"turn": turn_id, "start": ts or p.get("started_at"), "window": p.get("model_context_window"),
                       "model": meta.get("model"), "effort": meta.get("effort"), "_total0": last_total,
                       "_ctx": [], "ended": "open"}
            turns[turn_id] = current
            order.append(turn_id)
        elif sub == "token_count":
            info = p.get("info") or {}
            total = info.get("total_token_usage")
            last = info.get("last_token_usage") or {}
            if isinstance(total, dict):
                last_total = total
                if current is not None:
                    current["_total1"] = total
            ctx = last.get("total_tokens") or None
            if ctx:
                last_context = ctx
                if current is not None:
                    current["_ctx"].append(ctx)
                    if info.get("model_context_window"):
                        current["window"] = info["model_context_window"]
                if pending_compaction is not None and pending_compaction.get("after") is None:
                    pending_compaction["after"] = ctx
                    pending_compaction = None
            for name, lim in (p.get("rate_limits") or {}).items():
                if isinstance(lim, dict) and lim.get("used_percent") is not None:
                    key = (lim.get("window_minutes"), lim.get("resets_at"))
                    if limits.get(name) != (key, lim["used_percent"]):
                        limits[name] = (key, lim["used_percent"])
                        events.append({"kind": "limit_changed", "at": iso(ts), "limit": name,
                                       "used_percent": lim["used_percent"], "window_minutes": lim.get("window_minutes"),
                                       "resets_at": iso(lim.get("resets_at")),
                                       "turn": current["turn"] if current else None})
        elif sub in ("task_complete", "turn_complete", "turn_aborted"):
            t = turn_for(p.get("turn_id"), ts)
            if t is not None:
                t["end"] = ts or p.get("completed_at")
                t["ended"] = "aborted" if sub == "turn_aborted" else "complete"
                if p.get("duration_ms"):
                    t["duration_ms"] = p["duration_ms"]
                if p.get("time_to_first_token_ms"):
                    t["ttft_ms"] = p["time_to_first_token_ms"]
                if sub == "turn_aborted":
                    events.append({"kind": "turn_aborted", "at": iso(ts), "turn": t["turn"],
                                   "detail": short(p.get("reason"), 120)})
            if t is current:
                current = None
            if not any(turns[k]["ended"] == "open" for k in order):
                safe = pos
        elif sub and "error" in sub:
            events.append({"kind": "host_error", "at": iso(ts), "turn": current["turn"] if current else None,
                           "detail": short(p.get("message") or p.get("error") or p, 300), "error_type": sub})
        elif sub == "thread_settings_applied":
            s = p.get("thread_settings") or {}
            meta["model"] = s.get("model") or meta.get("model")
            meta["effort"] = s.get("reasoning_effort") or meta.get("effort")

    out_turns = []
    for k in order:
        t = turns[k]
        tokens = {}
        responses = t.pop("_responses", {})
        if responses:
            for u in responses.values():
                add_tokens(tokens, {"prompt": u.get("input_tokens") or 0, "cache_read": u.get("cached_input_tokens") or 0,
                                    "cache_write": u.get("cache_write_input_tokens") or 0,
                                    "output": u.get("output_tokens") or 0,
                                    "reasoning": u.get("reasoning_output_tokens") or 0})
            t["calls"] = len(responses)
        else:
            a, b = t.get("_total0") or {}, t.get("_total1") or {}
            for name, key in (("prompt", "input_tokens"), ("cache_read", "cached_input_tokens"),
                              ("cache_write", "cache_write_input_tokens"), ("output", "output_tokens"),
                              ("reasoning", "reasoning_output_tokens")):
                rise = (b.get(key) or 0) - (a.get(key) or 0)
                if rise > 0:
                    tokens[name] = rise
            t["calls"] = len(t["_ctx"])
        t.pop("_total0", None)
        t.pop("_total1", None)
        ctx = t.pop("_ctx")
        t["tokens"] = tokens
        if ctx:
            t["peak_context"] = max(ctx)
            t["end_context"] = ctx[-1]
        t["start"], t["end"] = iso(t.get("start")), iso(t.get("end"))
        if not t.get("duration_ms") and t["start"] and t["end"]:
            t["duration_ms"] = int((parse_time(t["end"]) - parse_time(t["start"])) * 1000)
        out_turns.append({k2: v for k2, v in t.items() if v not in (None, {}, [])})
    if str(path).endswith(".zst"):
        safe = path.stat().st_size
    return {"meta": meta, "turns": out_turns, "events": events, "offset": safe}


# ------------------------------------------------------------------------------------------------------------ Claude

def claude_prompt(e: dict) -> bool:
    """Whether a `user` line is a prompt typed by the human or the script, and so starts a turn. Tool results, the
    compaction summary and the host's own meta lines don't."""
    if e.get("isMeta") or e.get("isCompactSummary") or e.get("isVisibleInTranscriptOnly"):
        return False
    content = (e.get("message") or {}).get("content")
    if isinstance(content, str):
        return not content.startswith(("<local-command", "<command-name>", "<bash-"))
    if isinstance(content, list):
        kinds = {c.get("type") for c in content if isinstance(c, dict)}
        return "tool_result" not in kinds and bool(kinds & {"text", "image"})
    return False


def claude_units(cost_state: dict | None) -> dict:
    """USD per weighted token for each model, from a `cost-state` line: each model's list-price cost divided by its
    weighted tokens. The ratio holds whatever the session's history, so it prices any turn on that model."""
    units = {}
    for model, u in ((cost_state or {}).get("modelUsage") or {}).items():
        if not isinstance(u, dict) or not u.get("costUSD"):
            continue
        w = weighted("claude", {"prompt": (u.get("inputTokens") or 0) + (u.get("cacheReadInputTokens") or 0)
                                + (u.get("cacheCreationInputTokens") or 0),
                                "cache_read": u.get("cacheReadInputTokens") or 0,
                                "cache_write": u.get("cacheCreationInputTokens") or 0,
                                "cache_write_1h": u.get("cacheCreationEphemeral1hInputTokens") or 0,
                                "output": u.get("outputTokens") or 0})
        if w:
            units[model] = u["costUSD"] / w
    return units


def read_claude(path: Path, start: int = 0, meta: dict | None = None) -> dict:
    """One Claude Code transcript from byte `start`: {meta, turns, events, offset}. `offset` is the start of the
    last turn's prompt, because a turn has no end marker: the next read takes that turn again in full."""
    meta = dict(meta or {})
    units = dict(meta.pop("units", {}) or {})
    turns: list[dict] = []
    events: list[dict] = []
    cur = None
    msgs: dict = {}
    calls: dict = {}
    safe = start
    line_start = start

    def close():
        if cur is None:
            return
        tokens, by_model, weights = {}, {}, {}
        for mid, (model, u) in msgs.items():
            cw = u.get("cache_creation") or {}
            t = {"prompt": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                 + (u.get("cache_creation_input_tokens") or 0),
                 "cache_read": u.get("cache_read_input_tokens") or 0,
                 "cache_write": u.get("cache_creation_input_tokens") or 0,
                 "cache_write_1h": cw.get("ephemeral_1h_input_tokens") or 0,
                 "output": u.get("output_tokens") or 0,
                 "reasoning": (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0}
            add_tokens(tokens, t)
            by_model[model] = by_model.get(model, 0) + t["output"] + 1
            weights[model] = weights.get(model, 0) + weighted("claude", t)
        cur["tokens"] = tokens
        cur["calls"] = len(msgs)
        if by_model:
            cur["model"] = max(by_model, key=by_model.get)
            if all(m in units for m in weights):
                cur["usd"] = round(sum(w * units[m] for m, w in weights.items()), 6)
        ctx = [c for c in cur.pop("_ctx") if c]
        if ctx:
            cur["peak_context"], cur["end_context"] = max(ctx), ctx[-1]
        if cur.get("start") and cur.get("end"):
            cur["duration_ms"] = int((parse_time(cur["end"]) - parse_time(cur["start"])) * 1000)
        turns.append({k: v for k, v in cur.items() if v not in (None, {}, [])})

    for line, pos in lines_of(path, start):
        this_start, line_start = line_start, pos
        if len(line) > BIG_LINE:
            tid = TOOL_USE_ID_RE.search(line)
            tsm = TS_RE.search(line[:600]) or TS_RE.search(line[-600:])
            if tid and tid.group(1).decode() in calls:
                t0, label = calls.pop(tid.group(1).decode())
                ts = parse_time(tsm.group(1).decode()) if tsm else None
                if cur is not None and label in cur.get("tools", {}):
                    if t0 and ts:
                        cur["tools"][label][1] += int((ts - t0) * 1000)
                    if IS_ERROR_RE.search(line):
                        cur["tools"][label][2] += 1
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        kind = e.get("type")
        ts_text = e.get("timestamp")
        if e.get("sessionId") and not meta.get("id"):
            meta["id"] = e["sessionId"]
        for src, dst in (("cwd", "cwd"), ("version", "cli"), ("gitBranch", "branch"), ("entrypoint", "entrypoint")):
            if e.get(src) and not meta.get(dst):
                meta[dst] = e[src]
        if ts_text and not meta.get("started"):
            meta["started"] = ts_text
        if kind == "cost-state":
            units.update(claude_units(e))
            continue
        if kind == "user":
            if claude_prompt(e):
                close()
                safe = this_start
                cur = {"turn": e.get("uuid") or e.get("promptId"), "start": ts_text, "end": ts_text, "_ctx": [],
                       "ended": "complete", "origin": e.get("promptSource") or e.get("turnOrigin")}
                msgs, calls = {}, {}
                continue
            content = (e.get("message") or {}).get("content")
            if isinstance(content, list) and cur is not None:
                ts = parse_time(ts_text)
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") in calls:
                        t0, label = calls.pop(c["tool_use_id"])
                        if t0 and ts:
                            cur["tools"][label][1] += int((ts - t0) * 1000)
                        if c.get("is_error"):
                            cur["tools"][label][2] += 1
                cur["end"] = ts_text or cur["end"]
            continue
        if kind == "assistant" and cur is not None:
            m = e.get("message") or {}
            if isinstance(m.get("usage"), dict):
                msgs[m.get("id") or e.get("uuid")] = (m.get("model") or "?", m["usage"])
                u = m["usage"]
                cur["_ctx"].append((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                                   + (u.get("cache_creation_input_tokens") or 0) + (u.get("output_tokens") or 0))
            ts = parse_time(ts_text)
            for c in m.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("id") not in calls:
                    label = c.get("name") or "?"
                    cur.setdefault("tools", {}).setdefault(label, [0, 0, 0])[0] += 1
                    calls[c.get("id")] = (ts, label)
            if e.get("isApiErrorMessage") or e.get("error"):
                text = next((c.get("text") for c in m.get("content") or [] if isinstance(c, dict) and c.get("text")),
                            e.get("error"))
                events.append({"kind": "host_error", "at": ts_text, "turn": cur["turn"], "detail": short(text, 300),
                               "error_type": str(e.get("error") or "api_error")})
            if m.get("stop_reason") == "max_tokens":
                events.append({"kind": "host_error", "at": ts_text, "turn": cur["turn"], "error_type": "max_tokens",
                               "detail": "a reply hit the output token limit"})
            cur["end"] = ts_text or cur["end"]
            continue
        if kind == "system" and e.get("subtype") == "compact_boundary":
            cm = e.get("compactMetadata") or {}
            events.append({"kind": "compaction", "at": ts_text, "turn": cur["turn"] if cur else None,
                           "before": cm.get("preTokens"), "after": cm.get("postTokens"),
                           "duration_ms": cm.get("durationMs"), "trigger": cm.get("trigger")})
            if cur is not None:
                cur["compactions"] = cur.get("compactions", 0) + 1
    close()
    meta["units"] = units
    if turns and turns[-1].get("end"):
        meta["last"] = turns[-1]["end"]
    return {"meta": meta, "turns": turns, "events": events, "offset": safe}


# --------------------------------------------------------------------------------------------------------- discovery

def roots_of(repo: Path, worktrees: list[str]) -> list[str]:
    roots = {str(Path(repo).resolve())}
    for w in worktrees:
        try:
            roots.add(str(Path(w).resolve()))
        except OSError:
            pass
    return sorted(roots)


def under(cwd: str | None, roots: list[str]) -> bool:
    if not cwd:
        return False
    return any(cwd == r or cwd.startswith(r.rstrip("/") + "/") for r in roots)


def codex_files() -> dict[str, Path]:
    """Every Codex rollout on this machine by thread id, live and archived. The thread index's `rollout_path` can
    be stale after the app moves a thread, so files are found by name."""
    out: dict[str, Path] = {}
    for folder in (CODEX_HOME / "sessions", CODEX_HOME / "archived_sessions"):
        for dirpath, _, names in os.walk(folder):
            for name in names:
                if name.startswith("rollout-") and (name.endswith(".jsonl") or name.endswith(".jsonl.zst")):
                    stem = name[: -len(".jsonl.zst")] if name.endswith(".zst") else name[: -len(".jsonl")]
                    tid = stem[-36:]
                    path = Path(dirpath) / name
                    if tid not in out or name.endswith(".jsonl"):
                        out[tid] = path
    return out


def codex_threads(roots: list[str]) -> dict[str, dict]:
    """Thread facts from Codex's thread index for threads whose folder is the repository or under it."""
    out: dict[str, dict] = {}
    for db in sorted(CODEX_HOME.glob("state_*.sqlite")):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2)
            cols = {r[1] for r in con.execute("pragma table_info(threads)")}
            want = [c for c in ("id", "cwd", "title", "source", "model", "reasoning_effort", "git_branch", "git_sha",
                                "archived", "created_at", "agent_role", "agent_nickname") if c in cols]
            for row in con.execute(f"select {','.join(want)} from threads"):
                d = dict(zip(want, row))
                if under(d.get("cwd"), roots):
                    out[d["id"]] = d
            con.close()
        except sqlite3.Error:
            continue
    return out


def codex_goals(ids: set[str]) -> list[dict]:
    out = []
    for db in sorted(CODEX_HOME.glob("goals_*.sqlite")):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2)
            for tid, status, used, secs, upd in con.execute(
                    "select thread_id, status, tokens_used, time_used_seconds, updated_at_ms from thread_goals"):
                if tid in ids:
                    out.append({"thread": tid, "status": status, "tokens_used": used, "seconds": secs,
                                "at": iso(upd / 1000 if upd else None)})
            con.close()
        except sqlite3.Error:
            continue
    return out


def claude_slug(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def claude_files(roots: list[str]) -> list[tuple[Path, str | None]]:
    """(transcript, parent session) for every Claude session whose folder is the repository or under it, subagents
    included. A project folder is named after the session's folder with every other character made a dash, so a
    name match is confirmed against the `cwd` its first lines carry."""
    base = CLAUDE_HOME / "projects"
    slugs = [claude_slug(r) for r in roots]
    out = []
    try:
        folders = [d for d in base.iterdir() if d.is_dir() and any(d.name == s or d.name.startswith(s + "-")
                                                                   for s in slugs)]
    except OSError:
        return out
    for folder in folders:
        files = sorted(folder.glob("*.jsonl"))
        if not files:
            continue
        if not any(folder.name == s for s in slugs) and not under(first_cwd(files[0]), roots):
            continue
        for f in files:
            out.append((f, None))
            sub = folder / f.stem / "subagents"
            if sub.is_dir():
                out.extend((s, f.stem) for s in sorted(sub.glob("*.jsonl")))
    return out


def first_cwd(path: Path) -> str | None:
    for line, _ in lines_of(path):
        m = re.search(rb'"cwd":\s*"([^"]+)"', line[:4000])
        if m:
            return m.group(1).decode()
    return None


# ------------------------------------------------------------------------------------------------------------ ledgers

def read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        with open(path) as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        pass
    return rows


def stderr_class(text: str | None) -> str:
    t = (text or "").lower()
    if "refresh token" in t or "log in" in t or "login" in t or "unauthor" in t:
        return "auth"
    if "usage limit" in t or "rate limit" in t or "quota" in t or "429" in t:
        return "usage_limit"
    if "model" in t and ("unrecognized" in t or "not found" in t or "unknown" in t):
        return "model"
    if "codex app" in t or "app didn't" in t:
        return "app"
    if "timed out" in t:
        return "timeout"
    return "other"


def ledger_events(rows: list[dict]) -> list[dict]:
    """Failed, timed-out and stopped turns from the script's usage ledger. Exit 124 is the script's own time limit
    on a turn, which pauses it; 130 a stop."""
    out = []
    for r in rows:
        code = r.get("exit")
        if code in (0, None):
            continue
        kind = "turn_timed_out" if code == 124 else "turn_stopped" if code in (130, -15, 143) else "turn_failed"
        out.append({"kind": kind, "at": r.get("at"), "host": r.get("host"), "session": r.get("session"),
                    "exit": code, "class": stderr_class(r.get("stderr")) if kind == "turn_failed" else None,
                    "detail": short(r.get("stderr"), 400) if r.get("stderr") else None,
                    **{k: r.get(k) for k in ("role", "module", "milestone", "model", "effort", "path", "version")}})
    return out


def result_events(orchestrate: Path) -> list[dict]:
    """Every result the script printed: the full list in results.jsonl where it exists (2.4.0 on), and the latest
    one per milestone and command from results/ for older runs. Refusals are marked as errors."""
    rows = read_jsonl(orchestrate / "results.jsonl")
    seen = {(r.get("result"), r.get("at")) for r in rows}
    for f in sorted((orchestrate / "results").glob("*.json")) if (orchestrate / "results").is_dir() else []:
        try:
            r = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(r, dict):
            continue
        r.setdefault("at", iso(f.stat().st_mtime))
        if (r.get("result"), r.get("at")) not in seen:
            rows.append(r)
    out = []
    for r in rows:
        word = r.get("result")
        if not word or word == "RUNNING":
            continue
        out.append({"kind": "script_refused" if word in REFUSALS else "result", "at": r.get("at"), "result": word,
                    "module": r.get("module"), "milestone": r.get("milestone"), "host": r.get("host"),
                    "model": r.get("model"), "verdict": r.get("verdict"), "version": r.get("version"),
                    "detail": short(r.get("reason") or r.get("why") or r.get("blocked") or r.get("last_line"), 400)})
    return out


def check_rows(orchestrate: Path) -> list[dict]:
    out = []
    folder = orchestrate / "checks"
    for f in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            r = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(r, dict) and r.get("command"):
            out.append({"command": short(r["command"], 160), "exit": r.get("exit"), "at": r.get("at"),
                        "role": r.get("role"), "module": r.get("module"), "milestone": r.get("milestone"),
                        "seconds": r.get("seconds")})
    return out


# -------------------------------------------------------------------------------------------------------------- store

FILES = ("sessions", "turns", "events", "milestones", "checks")


def key_of(kind: str, row: dict) -> str:
    if kind == "sessions":
        return f"{row.get('host')}:{row.get('session')}"
    if kind == "turns":
        return f"{row.get('host')}:{row.get('session')}:{row.get('turn')}"
    if kind == "milestones":
        return f"{row.get('module')}:{row.get('milestone')}"
    if kind == "checks":
        return f"{row.get('command')}:{row.get('at')}"
    blob = json.dumps({k: row.get(k) for k in ("kind", "at", "session", "turn", "result", "limit", "used_percent",
                                               "module", "milestone", "thread", "status")}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def load(folder: Path) -> dict:
    data = {kind: {key_of(kind, r): r for r in read_jsonl(folder / f"{kind}.jsonl")} for kind in FILES}
    try:
        data["state"] = json.loads((folder / "state.json").read_text())
    except (OSError, ValueError):
        data["state"] = {}
    return data


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    os.replace(tmp, path)


def save(folder: Path, data: dict) -> None:
    for kind in FILES:
        rows = sorted(data[kind].values(), key=lambda r: (str(r.get("at") or r.get("start") or r.get("started") or ""),
                                                          key_of(kind, r)))
        write_atomic(folder / f"{kind}.jsonl", "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows))
    write_atomic(folder / "state.json", json.dumps(data["state"], indent=0))


# ------------------------------------------------------------------------------------------------------------ extract

def tag_turns(turns: list[dict], rows: list[dict]) -> None:
    """Gives each turn the ledger row that the script wrote when that turn ended: the first row at or after the
    turn's end, less a margin for clocks; otherwise the session's last row."""
    if not rows:
        return
    rows = sorted(rows, key=lambda r: r.get("at") or "")
    for t in turns:
        end = parse_time(t.get("end") or t.get("start")) or 0
        row = next((r for r in rows if (parse_time(r.get("at")) or 0) >= end - 300), rows[-1])
        for k in ("role", "module", "milestone", "version", "path"):
            if row.get(k) is not None:
                t[k] = row[k]
        if row.get("task"):
            t["task"] = short(row["task"], 100)
        if row.get("model"):
            t["pinned_model"] = row["model"]
        if row.get("effort"):
            t["pinned_effort"] = row["effort"]
            t.setdefault("effort", row["effort"])


def model_matches(pinned: str, seen: str) -> bool:
    a, b = pinned.lower().split("[")[0], seen.lower().split("[")[0]
    return a == b or a.startswith(b) or b.startswith(a)


def extract(repo: Path, orchestrate: Path, worktrees: list[str], title_parts=None, budget_s: float = 600.0,
            full: bool = False, only: set[str] | None = None, codex_fit: dict | None = None,
            cost_of=None, modules: list[str] | None = None) -> dict:
    """Reads every session of this repository that has grown since the last run into the history folder, tags it
    from the ledgers, and returns a summary of what changed. `only` limits the read to those session ids (the
    script passes the session a turn just ran). `title_parts` is the script's parser for its session titles.
    `cost_of(tokens, fit)` turns Codex tokens into a share of the weekly limit. Never raises on a bad file."""
    started = time.time()
    folder = project_dir(repo)
    data = load(folder)
    if full:
        data["state"] = {}
    state = data["state"]
    roots = roots_of(repo, worktrees)
    ledger = read_jsonl(orchestrate / "usage.jsonl")
    by_session: dict[str, list] = {}
    for r in ledger:
        if r.get("session"):
            by_session.setdefault(r["session"], []).append(r)
    script_threads = {d.get("thread"): d for d in read_jsonl(orchestrate / "threads.jsonl") if d.get("thread")}
    read_files = skipped = 0
    seen_sessions: set[str] = set()

    sources: list[tuple[str, str, Path, str | None]] = []
    index = codex_threads(roots)
    files = codex_files() if index or by_session else {}
    for tid in sorted(set(index) | {s for s, rows in by_session.items() if rows[0].get("host") == "codex"}):
        if tid in files:
            sources.append(("codex", tid, files[tid], None))
    for path, parent in claude_files(roots):
        sid = path.stem if parent is None else f"{parent}/{path.stem}"
        sources.append(("claude", sid, path, parent))

    for host, sid, path, parent in sources:
        if only and sid not in only and (parent or "") not in only:
            continue
        if time.time() - started > budget_s:
            skipped += 1
            continue
        key = f"{host}:{sid}"
        try:
            st = path.stat()
        except OSError:
            continue
        prev = state.get(key) or {}
        if prev.get("size") == st.st_size and prev.get("mtime") == int(st.st_mtime) and not full:
            seen_sessions.add(sid)
            continue
        start = prev.get("offset", 0) if prev.get("path") == str(path) and prev.get("size", 0) <= st.st_size else 0
        try:
            got = (read_codex if host == "codex" else read_claude)(path, start, prev.get("meta"))
        except Exception as exc:  # one unreadable file never stops the rest
            state[key] = {"path": str(path), "error": short(exc, 200), "size": st.st_size, "mtime": int(st.st_mtime)}
            continue
        read_files += 1
        seen_sessions.add(sid)
        meta = got["meta"]
        state[key] = {"path": str(path), "offset": got["offset"], "size": st.st_size, "mtime": int(st.st_mtime),
                      "meta": meta}
        # Drop this session's turns from the re-read point on; they are about to be written again.
        if start == 0:
            for k in [k for k in data["turns"] if k.startswith(key + ":")]:
                del data["turns"][k]
        for t in got["turns"]:
            t.update(host=host, session=sid)
            data["turns"][key_of("turns", t)] = t
        session_turns = [t for k, t in data["turns"].items() if k.startswith(key + ":")]
        info = index.get(sid) or {}
        parent_id = parent or meta.get("parent")
        kind = ("subagent" if (parent or meta.get("source") == "subagent") else
                "auto-review" if meta.get("source") == "auto-review" else
                "script" if (sid in by_session or sid in script_threads) else "interactive")
        tag_turns(session_turns, by_session.get(sid) or [])
        for t in session_turns:  # a planner's ledger row names no module; its task usually does
            if t.get("role") == "plan" and not t.get("module") and t.get("task") and modules:
                hit = next((m for m in modules if re.search(rf"(?<![A-Z0-9-]){re.escape(m)}(?![A-Z0-9-])",
                                                            t["task"])), None)
                if hit:
                    t["module"] = hit
        for t in session_turns:
            t["kind"] = kind
            if not t.get("role"):
                title = (script_threads.get(sid) or {}).get("title") or info.get("title")
                parts = title_parts(title) if (title_parts and title) else None
                if parts:
                    t["role"], t["module"], t["milestone"] = parts
                elif (script_threads.get(sid) or {}).get("role"):
                    t["role"] = script_threads[sid]["role"]
            t["weighted"] = round(weighted(host, t.get("tokens") or {}))
            if host == "codex" and cost_of and codex_fit:
                tok = t.get("tokens") or {}
                pct = cost_of([max(tok.get("prompt", 0) - tok.get("cache_read", 0), 0), tok.get("cache_read", 0),
                               tok.get("output", 0)], codex_fit)
                if pct:
                    t["limit_pct"] = pct[1]
        totals: dict = {}
        for t in session_turns:
            add_tokens(totals, t.get("tokens") or {})
        starts = [t["start"] for t in session_turns if t.get("start")]
        ends = [t.get("end") or t.get("start") for t in session_turns if t.get("end") or t.get("start")]
        data["sessions"][key] = {k: v for k, v in {
            "host": host, "session": sid, "kind": kind, "parent": parent_id,
            "parent_known": bool(parent_id) if kind in ("auto-review", "subagent") else None,
            "cwd": meta.get("cwd"), "cli": meta.get("cli"), "model": meta.get("model") or info.get("model"),
            "effort": meta.get("effort") or info.get("reasoning_effort"), "branch": meta.get("branch") or info.get("git_branch"),
            "nickname": meta.get("nickname"), "title": short(info.get("title"), 120) if info.get("title") else None,
            "start": min(starts) if starts else meta.get("started"), "end": max(ends) if ends else None,
            "turns": len(session_turns), "tokens": totals,
            "weighted": round(sum(t.get("weighted", 0) for t in session_turns)),
            "usd": round(sum(t.get("usd", 0) for t in session_turns), 4) or None,
            "compactions": sum(t.get("compactions", 0) for t in session_turns),
            **{k: session_turns[-1].get(k) for k in ("role", "module", "milestone") if session_turns}}.items()
            if v not in (None, {}, "")}
        for ev in got["events"]:
            ev.update(host=host, session=sid)
            match = next((t for t in session_turns if t.get("turn") == ev.get("turn")), None)
            for k in ("role", "module", "milestone", "kind"):
                if match and match.get(k) and k != "kind":
                    ev[k] = match[k]
            ev["session_kind"] = kind
            data["events"][key_of("events", ev)] = {k: v for k, v in ev.items() if v is not None}
        for t in session_turns:
            if t.get("pinned_model") and t.get("model") and not model_matches(t["pinned_model"], t["model"]):
                ev = {"kind": "off_pinned_model", "at": t.get("start"), "host": host, "session": sid,
                      "turn": t.get("turn"), "detail": f"pinned {t['pinned_model']}, ran {t['model']}",
                      **{k: t.get(k) for k in ("role", "module", "milestone")}}
                data["events"][key_of("events", ev)] = {k: v for k, v in ev.items() if v is not None}

    # Auto-review and subagent sessions take the tags of the session they served.
    sessions = data["sessions"]
    by_id = {s["session"]: s for s in sessions.values()}
    for s in sessions.values():
        if s.get("kind") in ("auto-review", "subagent") and s.get("parent") in by_id:
            p = by_id[s["parent"]]
            for k in ("role", "module", "milestone"):
                if p.get(k) and not s.get(k):
                    s[k] = p[k]
            s["parent_kind"] = p.get("kind")
    for t in data["turns"].values():
        s = sessions.get(f"{t.get('host')}:{t.get('session')}") or {}
        if s.get("kind") in ("auto-review", "subagent"):
            for k in ("role", "module", "milestone"):
                if s.get(k) and not t.get(k):
                    t[k] = s[k]
            t["parent_kind"] = s.get("parent_kind")

    # Sessions the ledger knows whose host file is gone keep the ledger's figures.
    have = {s["session"] for s in sessions.values()}
    for sid, rows in by_session.items():
        if sid in have or (only and sid not in only):
            continue
        host = rows[0].get("host") or "?"
        key = f"{host}:{sid}"
        for i, r in enumerate(rows):
            u = r.get("usage") or {}
            if not any(u.get(k) for k in ("input", "cached", "output")):
                continue
            tok = {"prompt": (u.get("input") or 0) + (u.get("cached") or 0), "cache_read": u.get("cached") or 0,
                   "output": u.get("output") or 0}
            t = {"host": host, "session": sid, "turn": f"ledger-{i}", "end": r.get("at"), "start": r.get("at"),
                 "model": r.get("model"), "effort": r.get("effort"), "tokens": tok, "kind": "script",
                 "from_ledger": True, "weighted": round(weighted(host, tok)), "ended": "complete" if not r.get("exit") else "failed",
                 **({"usd": u["cost_usd"]} if u.get("cost_usd") else {}),
                 **{k: r.get(k) for k in ("role", "module", "milestone", "version", "path") if r.get(k) is not None}}
            data["turns"][key_of("turns", t)] = t
        sessions[key] = {"host": host, "session": sid, "kind": "script", "from_ledger": True,
                         "start": rows[0].get("at"), "end": rows[-1].get("at"), "turns": len(rows),
                         "model": rows[-1].get("model"), "effort": rows[-1].get("effort"),
                         **{k: rows[-1].get(k) for k in ("role", "module", "milestone") if rows[-1].get(k)}}

    if not only:
        for ev in ledger_events(ledger) + result_events(orchestrate):
            data["events"][key_of("events", ev)] = {k: v for k, v in ev.items() if v is not None}
        for c in check_rows(orchestrate):
            data["checks"][key_of("checks", c)] = {k: v for k, v in c.items() if v is not None}
            if c.get("exit") not in (0, "0", None):
                ev = {"kind": "check_failed", "at": c.get("at"), "detail": c["command"], "exit": c.get("exit"),
                      **{k: c.get(k) for k in ("module", "milestone")}}
                data["events"][key_of("events", ev)] = {k: v for k, v in ev.items() if v is not None}
        codex_ids = {s["session"] for s in sessions.values() if s.get("host") == "codex"}
        for g in codex_goals(codex_ids):
            if g["status"] in ("usage_limited", "budget_limited", "blocked"):
                s = sessions.get(f"codex:{g['thread']}") or {}
                ev = {"kind": "goal_limited", "at": g["at"], "host": "codex", "session": g["thread"],
                      "status": g["status"], "detail": f"goal {g['status'].replace('_', ' ')}",
                      **{k: s.get(k) for k in ("role", "module", "milestone")}}
                data["events"][key_of("events", ev)] = {k: v for k, v in ev.items() if v is not None}
        firsts: dict[str, str] = {}
        for t in data["turns"].values():
            v, at = t.get("version"), t.get("start") or t.get("end")
            if v and at and (v not in firsts or at < firsts[v]):
                firsts[v] = at
        for v, at in firsts.items():
            ev = {"kind": "version_seen", "at": at, "version": v, "detail": f"orchestrate {v} first ran"}
            data["events"][key_of("events", {**ev, "result": v})] = ev

    state["_last_run"] = iso(time.time())
    state["_schema"] = SCHEMA
    save(folder, data)
    return {"folder": str(folder), "files_read": read_files, "files_left": skipped,
            "sessions": len(data["sessions"]), "turns": len(data["turns"]), "events": len(data["events"]),
            "seconds": round(time.time() - started, 1),
            "bytes": sum((folder / f"{k}.jsonl").stat().st_size for k in FILES if (folder / f"{k}.jsonl").exists())}


def write_milestones(repo: Path, rows: list[dict]) -> None:
    folder = project_dir(repo)
    data = load(folder)
    data["milestones"] = {key_of("milestones", r): r for r in rows}
    for r in rows:
        for rv in r.get("reviews") or []:
            if rv.get("verdict") == "fail":
                ev = {"kind": "review_failed", "at": rv.get("at"), "module": r["module"], "milestone": r["milestone"],
                      "host": rv.get("host"), "model": rv.get("model"),
                      "detail": ", ".join(f["name"] + (" (repeated)" if f.get("repeat") else "")
                                          for f in rv.get("findings") or [])[:400] or "failed review"}
                data["events"][key_of("events", ev)] = {k: v for k, v in ev.items() if v is not None}
    save(folder, data)


# ---------------------------------------------------------------------------------------------------------- summary

def rows(folder: Path) -> dict:
    return {kind: read_jsonl(folder / f"{kind}.jsonl") for kind in FILES}


ERROR_KINDS = ("turn_failed", "turn_timed_out", "turn_stopped", "host_error", "turn_aborted", "script_refused",
               "check_failed", "off_pinned_model", "goal_limited", "review_failed")


def summary(folder: Path, recent: int = 25) -> dict:
    """The figures an agent reads first: totals by host, role, kind and model, the errors by kind with the latest
    ones, and the costliest milestones. The dashboard shows the same records in full."""
    d = rows(folder)
    def group(key):
        out: dict = {}
        for t in d["turns"]:
            g = out.setdefault(str(key(t)), {"turns": 0, "weighted": 0, "usd": 0.0, "limit_pct": 0.0, "tokens": {}})
            g["turns"] += 1
            g["weighted"] += t.get("weighted", 0)
            g["usd"] += t.get("usd", 0) or 0
            g["limit_pct"] += t.get("limit_pct", 0) or 0
            add_tokens(g["tokens"], t.get("tokens") or {})
        for g in out.values():
            g["usd"], g["limit_pct"] = round(g["usd"], 2), round(g["limit_pct"], 1)
        return dict(sorted(out.items(), key=lambda kv: -kv[1]["weighted"]))
    errors = [e for e in d["events"] if e.get("kind") in ERROR_KINDS]
    counts: dict = {}
    for e in errors:
        k = e["kind"] + (f":{e['class']}" if e.get("class") else "")
        counts[k] = counts.get(k, 0) + 1
    ms = {}
    for t in d["turns"]:
        if t.get("module") and t.get("milestone"):
            g = ms.setdefault(f"{t['module']} {t['milestone']}", {"weighted": 0, "turns": 0})
            g["weighted"] += t.get("weighted", 0)
            g["turns"] += 1
    return {"folder": str(folder), "sessions": len(d["sessions"]), "turns": len(d["turns"]),
            "by_host": group(lambda t: t.get("host")), "by_kind": group(lambda t: t.get("kind")),
            "by_role": group(lambda t: t.get("role") or "-"), "by_model": group(lambda t: t.get("model") or "-"),
            "by_version": group(lambda t: t.get("version") or "-"),
            "errors": counts, "recent_errors": sorted(errors, key=lambda e: e.get("at") or "")[-recent:],
            "costliest_milestones": sorted(ms.items(), key=lambda kv: -kv[1]["weighted"])[:10]}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Summarise a delivery history folder. agent_loop.py's `history` command "
                                             "fills it.")
    ap.add_argument("folder", nargs="?", help="a history folder; default: the one for the current repository")
    a = ap.parse_args(argv)
    folder = Path(a.folder) if a.folder else project_dir(Path.cwd())
    print(json.dumps(summary(folder), indent=1))


if __name__ == "__main__":
    main()
