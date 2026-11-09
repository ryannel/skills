#!/usr/bin/env python3
"""Codex account usage telemetry, read from Codex's local rollout files. Standard library only.

Codex writes one `rollout-*.jsonl` per thread under `$CODEX_HOME/sessions`. Each model call adds a `token_count`
event with the thread's token totals and the account's usage-limit snapshot (`rate_limits.primary`: the weekly window's
`used_percent`, in whole percents, and `resets_at`). `task_started`, `task_complete` and `turn_aborted` bound each turn,
and `turn_context` names its model and effort. From those this module measures:

  burn      the percent used per hour while a turn was running, idle time excluded: per active hour (any local turn
            running) and per builder-hour (summed over top-level threads' turns).
  fit       a tokens-to-percent conversion fitted from the usage snapshots against the local tokens spent between
            them, with the range whole-percent readings allow. It turns any thread's or turn's tokens into a percent.
  outside   rises in the usage figure that the local tokens between two snapshots can't explain, even at the top of
            the fitted range: usage from elsewhere (another machine, the web or cloud tasks).

It reads incrementally: what it has read is cached (default ~/.cache/codex_quota/, one file per Codex home, holding
offsets and a few compact records per turn and percent), each file is entered at the horizon's start by binary search on
its timestamps, and a scan stops at its deadline and carries on next call, saying how much it left unread.

The interface is host-neutral where that costs nothing: `read()` returns samples, turns, threads and token records as
plain data, and the analysis functions take those, so another host's reader could feed them.

CLI: codex_quota.py [--budget SECONDS] [--json]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HOST = "codex"
WEEK_S = 7 * 86400
WINDOW_MINUTES = 10080
HORIZON_S = 8 * 86400  # how far back records are kept: the current weekly window plus a day for the fit
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "codex_quota"
CACHE_VERSION = 3
CHUNK = 16 << 20
HEAD = 2 << 20
HEADER_SPAN = 200  # a marker counts only this near the start of its line, so text quoting it inside an item doesn't

# Cost weights for one model call, relative to an uncached input token: cached input is billed at about a tenth, and
# output (reasoning included) at several times input. These are API price ratios, not a fit; only their scale is
# fitted (see `fit`). Turns spent mostly re-reading a cached context are where a wrong ratio would show.
WEIGHTS = {"uncached": 1.0, "cached": 0.1, "output": 8.0}

MARKERS = {kind: [f'"type":"{kind}"'.encode(), f'"type": "{kind}"'.encode()]
           for kind in ("token_count", "task_started", "task_complete", "turn_aborted", "turn_context")}
TIMESTAMP = re.compile(rb'"timestamp":\s*"([^"]+)"')


def parse_time(text: str) -> float:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def weighted(u: float, c: float, o: float, weights: dict = WEIGHTS) -> float:
    return u * weights["uncached"] + c * weights["cached"] + o * weights["output"]


# ----------------------------------------------------------------------------------------------------------- reading

def _new_entry() -> dict:
    # recs: [t0, t1, used, resets_at, turn, uncached, cached, output, calls]; used/resets are None when the call
    # carried no weekly snapshot. turns: {turn: [start, end, model, effort]}.
    return {"offset": 0, "meta": {}, "turns": {}, "recs": [], "turn": None, "total": None}


def _head(path: str, entry: dict) -> None:
    """Thread facts from the file's start: its session_meta line and the first user prompts."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(HEAD)
    except OSError:
        return
    lines = head.split(b"\n")
    meta = {}
    try:
        p = json.loads(lines[0]).get("payload") or {}
        source = p.get("source")
        kind, parent = "app", None
        if isinstance(source, dict):
            spawn = (source.get("subagent") or {})
            if isinstance(spawn, dict) and "thread_spawn" in spawn:
                kind, parent = "subagent", (spawn["thread_spawn"] or {}).get("parent_thread_id")
            else:
                kind = "guardian" if "guardian" in json.dumps(source) else "subagent"
        elif source == "exec":
            kind = "exec"
        meta = {"id": p.get("id"), "cwd": p.get("cwd"), "origin": p.get("originator"), "kind": kind,
                "parent": parent}
    except (ValueError, AttributeError, IndexError):
        pass
    prompts = []
    for line in lines[1:-1]:
        if b'"UserMessage"' not in line[:600] or b"item_completed" not in line[:200]:
            continue
        try:
            item = json.loads(line)["payload"]["item"]
            text = " ".join(c.get("text", "") for c in item.get("content") or [] if isinstance(c, dict))
        except (ValueError, KeyError, TypeError):
            continue
        prompts.append(text[:400])
        if len(prompts) == 2:
            break
    meta["prompts"] = prompts
    entry["meta"] = meta


def _offset_at(handle, size: int, since: float) -> int:
    """A line start at or shortly before the first line timestamped `since` or later (binary search on timestamps)."""
    lo, hi = 0, size
    while hi - lo > (1 << 20):
        mid = (lo + hi) // 2
        handle.seek(mid)
        handle.readline()
        pos = handle.tell()
        if pos >= hi:
            hi = mid
            continue
        m = TIMESTAMP.search(handle.read(96))
        if not m:
            return lo
        try:
            t = parse_time(m.group(1).decode())
        except ValueError:
            return lo
        if t < since:
            lo = pos
        else:
            hi = mid
    return lo


def _event(entry: dict, kind: str, e: dict) -> None:
    p = e.get("payload") or {}
    turns = entry["turns"]
    if kind == "task_started":
        entry["turn"] = p.get("turn_id")
        turns.setdefault(entry["turn"], [None, None, None, None])[0] = p.get("started_at") or parse_time(e["timestamp"])
    elif kind in ("task_complete", "turn_aborted"):
        t = turns.setdefault(p.get("turn_id"), [p.get("started_at"), None, None, None])
        t[1] = p.get("completed_at") or parse_time(e["timestamp"])
        if t[0] is None:
            t[0] = p.get("started_at")
    elif kind == "turn_context":
        t = turns.setdefault(p.get("turn_id"), [None, None, None, None])
        t[2], t[3] = p.get("model"), p.get("effort")
        entry["turn"] = entry["turn"] or p.get("turn_id")
    elif kind == "token_count":
        when = parse_time(e["timestamp"])
        used = resets = None
        limits = p.get("rate_limits") or {}
        primary = limits.get("primary") or {}
        if limits.get("limit_id") in (None, "codex") and primary.get("window_minutes") == WINDOW_MINUTES \
                and primary.get("used_percent") is not None:
            used, resets = float(primary["used_percent"]), float(primary["resets_at"])
        total = ((p.get("info") or {}).get("total_token_usage")) or None
        u = c = o = 0
        if total:
            now_total = [total.get("input_tokens", 0) - total.get("cached_input_tokens", 0),
                         total.get("cached_input_tokens", 0), total.get("output_tokens", 0)]
            if entry["total"] is not None:
                u, c, o = (max(0, a - b) for a, b in zip(now_total, entry["total"]))
            entry["total"] = now_total
        turn = entry["turn"]
        if turn in turns and turns[turn][0] is None:
            turns[turn][0] = when
        recs = entry["recs"]
        last = recs[-1] if recs else None
        if last and last[4] == turn and (used is None or last[2] in (None, used)) \
                and (resets is None or last[3] in (None, resets)) and when - last[1] < 900:
            last[1] = when
            last[2] = last[2] if used is None else used
            last[3] = last[3] if resets is None else resets
            last[5] += u
            last[6] += c
            last[7] += o
            last[8] += 1
        else:
            recs.append([when, when, used, resets, turn, u, c, o, 1])


def _scan(path: str, entry: dict, size: int, deadline: float) -> None:
    with open(path, "rb") as handle:
        handle.seek(entry["offset"])
        tail = b""
        while entry["offset"] + len(tail) < size:
            if time.monotonic() > deadline:
                return
            chunk = handle.read(min(CHUNK, size - entry["offset"] - len(tail)))
            if not chunk:
                return
            buf = tail + chunk
            end = buf.rfind(b"\n") + 1
            if end == 0:
                tail = buf  # one line longer than the chunk: keep reading it
                continue
            body, tail = buf[:end], buf[end:]
            hits = []
            for kind, marks in MARKERS.items():
                for mark in marks:
                    i = body.find(mark)
                    while i >= 0:
                        start = body.rfind(b"\n", 0, i) + 1
                        if i - start < HEADER_SPAN:
                            hits.append((start, kind))
                        i = body.find(mark, i + 1)
            seen = set()
            for start, kind in sorted(hits):
                if start in seen:
                    continue
                seen.add(start)
                stop = body.find(b"\n", start)
                try:
                    e = json.loads(body[start:stop])
                    if e.get("type") != kind and (e.get("payload") or {}).get("type") != kind:
                        continue
                    _event(entry, kind, e)
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue
            entry["offset"] += end


def _prune(entry: dict, horizon: float) -> None:
    entry["recs"] = [r for r in entry["recs"] if r[1] >= horizon]
    live = {r[4] for r in entry["recs"]} | {entry["turn"]}
    entry["turns"] = {k: v for k, v in entry["turns"].items()
                      if k in live or (v[1] or v[0] or 0) >= horizon}


def _load_cache(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
        if data.get("version") == CACHE_VERSION:
            return data
    except (OSError, ValueError, AttributeError):
        pass
    return {"version": CACHE_VERSION, "files": {}}


def _save_cache(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".rollouts-")
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, separators=(",", ":"))
        os.replace(tmp, path)
    except OSError:
        pass


def rollouts(home: Path) -> list[str]:
    """Live and archived rollout files (archived ones still count against the window they ran in)."""
    return glob.glob(str(home / "sessions" / "**" / "rollout-*.jsonl"), recursive=True) + \
        glob.glob(str(home / "archived_sessions" / "rollout-*.jsonl"))


def latest_sample(home: Path = None, files: int = 6, nbytes: int = 2 << 20) -> tuple | None:
    """(time, used_percent, resets_at) from the tails of the newest rollouts: the current reading, cheaply."""
    paths = rollouts(home or CODEX_HOME)
    best = None
    for path in sorted(paths, key=_mtime)[-files:]:
        try:
            with open(path, "rb") as handle:
                size = os.fstat(handle.fileno()).st_size
                handle.seek(max(0, size - nbytes))
                data = handle.read()
        except OSError:
            continue
        for line in reversed(data.split(b"\n")):
            if not any(m in line[:HEADER_SPAN] for m in MARKERS["token_count"]):
                continue
            entry = _new_entry()
            try:
                _event(entry, "token_count", json.loads(line))
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            rec = entry["recs"][-1]
            if rec[2] is not None:
                if best is None or rec[0] > best[0]:
                    best = (rec[0], rec[2], rec[3])
                break
    return best


def _mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def thread_names(home: Path = None) -> dict:
    names = {}
    try:
        with open((home or CODEX_HOME) / "session_index.jsonl") as handle:
            for line in handle:
                try:
                    d = json.loads(line)
                    names[d["id"]] = d.get("thread_name")
                except (ValueError, KeyError, TypeError):
                    continue
    except OSError:
        pass
    return names


def cache_for(home: Path) -> Path:
    """One cache per Codex home, so a test's or another account's files never replace this one's."""
    return CACHE_DIR / f"rollouts-{hashlib.sha256(str(home.resolve()).encode()).hexdigest()[:12]}.json"


def read(budget_s: float = 3.0, home: Path | None = None, cache: Path | None | bool = True, now: float | None = None,
         horizon_s: float = HORIZON_S) -> dict:
    """Everything the analysis needs from the last `horizon_s`, as plain data:
    {host, now, complete, behind_bytes, latest, threads: {id: meta}, turns: [{thread, turn, start, end, model,
    effort}], recs: [{thread, turn, t0, t1, used, resets, uncached, cached, output}]}.
    Stops reading at `budget_s` and says how much it left (`complete`, `behind_bytes`)."""
    home = home or CODEX_HOME
    cache = cache_for(home) if cache is True else cache or None
    now = now or time.time()
    deadline = time.monotonic() + budget_s
    horizon = now - horizon_s
    data = _load_cache(cache) if cache else {"version": CACHE_VERSION, "files": {}}
    files = data["files"]
    paths = {}  # file name -> (path, size); keyed by name so a thread moved to the archive keeps its progress
    for path in rollouts(home):
        try:
            st = os.stat(path)
        except OSError:
            continue
        if st.st_mtime >= horizon:
            paths[os.path.basename(path)] = (path, st.st_size)
    for gone in set(files) - set(paths):
        del files[gone]
    behind = 0
    # Smallest backlog first, so a short budget finishes as many threads as it can; the rest carry on next call.
    for name, (path, size) in sorted(paths.items(),
                                     key=lambda kv: kv[1][1] - (files.get(kv[0]) or {}).get("offset", 0)):
        entry = files.get(name)
        if entry is not None and size < entry["offset"]:
            entry = None  # rewritten
        if entry is None and time.monotonic() > deadline:
            behind += size  # not started: left whole for the next call
            continue
        if entry is None:
            entry = _new_entry()
            _head(path, entry)
            try:
                with open(path, "rb") as handle:
                    entry["offset"] = _offset_at(handle, size, horizon)
            except OSError:
                continue
            if entry["offset"] == 0:
                entry["total"] = [0, 0, 0]  # read from the start, so the first call's tokens count too
            files[name] = entry
        if entry["offset"] < size and time.monotonic() < deadline:
            try:
                _scan(path, entry, size, deadline)
            except OSError:
                pass
        behind += max(0, size - entry["offset"])
        _prune(entry, horizon)
    if cache and (paths or files):
        _save_cache(cache, data)
    names = thread_names(home)
    threads, turns, recs = {}, [], []
    for name, entry in files.items():
        meta = dict(entry["meta"])
        tid = meta.get("id") or name[:-len(".jsonl")][-36:]
        meta["name"] = names.get(tid)
        threads[tid] = meta
        for turn, (start, end, model, effort) in entry["turns"].items():
            turns.append({"thread": tid, "turn": turn, "start": start, "end": end, "model": model, "effort": effort})
        for r in entry["recs"]:
            recs.append({"thread": tid, "turn": r[4], "t0": r[0], "t1": r[1], "used": r[2], "resets": r[3],
                         "uncached": r[5], "cached": r[6], "output": r[7]})
    recs.sort(key=lambda r: (r["t0"], r["t1"]))
    # A turn with no end yet runs to its last record, or to now when its file is still being written.
    last_seen = {}
    for r in recs:
        last_seen[(r["thread"], r["turn"])] = max(last_seen.get((r["thread"], r["turn"]), 0), r["t1"])
    for t in turns:
        if t["end"] is None:
            t["end"] = last_seen.get((t["thread"], t["turn"])) or t["start"]
    latest = latest_sample(home)
    return {"host": HOST, "now": now, "complete": behind == 0, "behind_bytes": behind, "latest": latest,
            "threads": threads, "turns": [t for t in turns if t["start"]], "recs": recs}


# ---------------------------------------------------------------------------------------------------------- analysis

def samples(recs: list[dict]) -> list[tuple[float, float, float]]:
    """(time, used_percent, resets_at) readings, oldest first."""
    out = []
    for r in recs:
        if r["used"] is not None:
            out.append((r["t0"], r["used"], r["resets"]))
            if r["t1"] != r["t0"]:
                out.append((r["t1"], r["used"], r["resets"]))
    return sorted(out)


def window_of(reading: dict) -> tuple[float, float, float] | None:
    """(window start, resets_at, used now) for the current weekly window, from the newest reading."""
    s = samples(reading["recs"])
    latest = reading.get("latest")
    if s and (latest is None or s[-1][0] >= latest[0]):
        latest = s[-1]
    if not latest:
        return None
    return latest[2] - WEEK_S, latest[2], latest[1]


def same_window(a: float | None, b: float | None) -> bool:
    return a is not None and b is not None and abs(a - b) < 3600  # resets_at can wobble by seconds


def merge(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = []
    for lo, hi in sorted(i for i in intervals if i[1] > i[0]):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def clip(intervals, lo: float, hi: float) -> list[tuple[float, float]]:
    return [(max(a, lo), min(b, hi)) for a, b in intervals if b > lo and a < hi]


def length(intervals) -> float:
    return sum(b - a for a, b in intervals)


def top_level(meta: dict) -> bool:
    return meta.get("kind") not in ("subagent", "guardian")


def windows(recs: list[dict]) -> list[float]:
    """The weekly windows the readings fall in, by their resets_at, oldest first."""
    out = []
    for rs in sorted({r["resets"] for r in recs if r["resets"] is not None}):
        if not out or not same_window(out[-1], rs):
            out.append(rs)
    return out


def points(recs: list[dict], resets: float, weights: dict) -> list[tuple[float, float, float]]:
    """(time, cumulative local weighted tokens, used percent) at each reading in one window, the percent as a
    running maximum (threads report the account figure a call or two apart)."""
    out, tokens, used = [], 0.0, None
    for r in recs:
        if r["t1"] < resets - WEEK_S or r["t0"] > resets:
            continue
        tokens += weighted(r["uncached"], r["cached"], r["output"], weights)
        if r["used"] is not None and same_window(r["resets"], resets):
            used = r["used"] if used is None else max(used, r["used"])
            out.append((r["t1"], tokens, used))
    return out


def _slope(pts) -> float | None:
    if len(pts) < 2:
        return None
    mw = sum(p[1] for p in pts) / len(pts)
    mu = sum(p[2] for p in pts) / len(pts)
    den = sum((p[1] - mw) ** 2 for p in pts)
    return sum((p[1] - mw) * (p[2] - mu) for p in pts) / den if den > 0 else None


def _rms(pts, k: float) -> float:
    mw = sum(p[1] for p in pts) / len(pts)
    mu = sum(p[2] for p in pts) / len(pts)
    return (sum((p[2] - mu - k * (p[1] - mw)) ** 2 for p in pts) / len(pts)) ** 0.5


def _fit_window(pts) -> dict | None:
    """Slope of percent on tokens, after setting aside rises the tokens before them can't explain."""
    k = _slope(pts)
    if not k or k <= 0:
        return None
    cleaned, jumps = pts, []
    for _ in range(3):
        k_hi = k * 1.5
        found, shift, adjusted = [], 0.0, [pts[0]]
        for a, b in zip(pts, pts[1:]):
            rise, tokens = b[2] - a[2], b[1] - a[1]
            if rise - 1 > k_hi * tokens:  # more than whole-percent rounding plus the most these tokens could cost
                extra = rise - k * tokens
                found.append({"t0": a[0], "t1": b[0], "rise": rise, "outside": round(extra, 1),
                              "at_least": round(rise - 1 - k_hi * tokens, 1)})
                shift += extra
            adjusted.append((b[0], b[1], b[2] - shift))
        k_new = _slope(adjusted)
        if not k_new or k_new <= 0:
            break
        k, cleaned, jumps = k_new, adjusted, found
        if not found:
            break
    return {"k": k, "rms": _rms(cleaned, k), "rise": cleaned[-1][2] - cleaned[0][2],
            "tokens": cleaned[-1][1] - cleaned[0][1], "pts": cleaned, "jumps": jumps}


CACHED_GRID = (0.05, 0.1, 0.25)  # around the API ratio of a tenth; the readings rarely tell these apart
OUTPUT_GRID = (4.0, 8.0, 16.0)
MIN_RISE = 5.0       # percent of local rise below which there's too little data to fit
WEIGHT_RISE = 15.0   # percent of local rise needed before the token weights are chosen from the data too


def fit(reading: dict, weights: dict | None = None) -> dict:
    """Percent of the weekly limit per million weighted tokens, fitted on the newest window with enough local rise.

    The usage figure is regressed on the local tokens spent before each reading. A rise those tokens can't explain
    (beyond one percent of rounding, at half again the fitted rate) is set aside as outside usage and the fit repeats.
    With at least WEIGHT_RISE percent to fit on and no `weights` given, the cached-input and output weights are chosen
    from small grids by the smallest residual; otherwise the API price ratios in WEIGHTS hold. The range is the wider of
    whole-percent rounding ((rise +- 1) / tokens) and the slopes fitted on each half of the window alone."""
    recs = reading["recs"]
    wins = windows(recs)
    target, best = None, None
    for rs in reversed(wins):
        base = weights or WEIGHTS
        trial = _fit_window(points(recs, rs, base))
        if trial and trial["rise"] >= MIN_RISE:
            target = rs
            break
    if target is None:
        return {"per_mtok": None, "note": "too little data: no weekly window with enough local use to fit", "outside": []}
    grid = [weights] if weights else (
        [{"uncached": 1.0, "cached": c, "output": o} for c in CACHED_GRID for o in OUTPUT_GRID]
        if trial["rise"] >= WEIGHT_RISE else [WEIGHTS])
    fits = [(w, f) for w in grid if (f := _fit_window(points(recs, target, w)))]
    w, f = min(fits, key=lambda wf: wf[1]["rms"])
    # Weights the readings can't tell apart from the best (residual within a quarter of a percent, or 25%) stay in
    # the range: they share out the same total differently between threads with more or less cached context.
    plausible = [(pw, pf) for pw, pf in fits if pf["rms"] <= max(f["rms"] * 1.25, f["rms"] + 0.25)]
    k, pts = f["k"], f["pts"]
    rows = []
    for pw, pf in plausible:
        band = [pf["k"] * max(0.0, pf["rise"] - 1) / pf["rise"], pf["k"] * (pf["rise"] + 1) / pf["rise"]]
        half = len(pf["pts"]) // 2
        for part in (pf["pts"][:half + 1], pf["pts"][half:]):
            if len(part) >= 3 and part[-1][2] - part[0][2] >= MIN_RISE:
                ks = _slope(part)
                if ks and ks > 0:
                    band = [min(band[0], ks), max(band[1], ks)]
        rows.append({"weights": pw, "per_mtok": [round(band[0] * 1e6, 5), round(pf["k"] * 1e6, 5),
                                                 round(band[1] * 1e6, 5)]})
    band = [rows[[r["weights"] for r in rows].index(w)]["per_mtok"][0] / 1e6,
            rows[[r["weights"] for r in rows].index(w)]["per_mtok"][2] / 1e6]
    others = []
    for rs in wins:
        if rs != target:
            o = _fit_window(points(recs, rs, w))
            if o and o["rise"] >= MIN_RISE:
                others.append({"resets_at": iso(rs), "per_mtok": round(o["k"] * 1e6, 4), "rise": round(o["rise"])})
    # Jumps in the current window too, if the fit came from an earlier one.
    jumps = list(f["jumps"])
    if wins and wins[-1] != target:
        k_hi = band[1]
        cur = points(recs, wins[-1], w)
        for a, b in zip(cur, cur[1:]):
            rise, tokens = b[2] - a[2], b[1] - a[1]
            if rise - 1 > k_hi * tokens:
                jumps.append({"t0": a[0], "t1": b[0], "rise": rise, "outside": round(rise - k * tokens, 1),
                              "at_least": round(rise - 1 - k_hi * tokens, 1)})
    return {"per_mtok": round(k * 1e6, 5), "range": [round(band[0] * 1e6, 5), round(band[1] * 1e6, 5)],
            "weights": w, "plausible": rows, "rms_pct": round(f["rms"], 2), "rise": round(f["rise"], 1),
            "mtok": round(f["tokens"] / 1e6, 1), "readings": len(pts), "window": iso(target),
            "other_windows": others, "outside": jumps}


def cost(tokens, f: dict) -> list[float] | None:
    """[low, central, high] percent for raw tokens (uncached, cached, output), or None without a usable fit. The range
    spans every plausible weighting's band, so it widens for work whose cached share differs from the window's."""
    if not f or f.get("per_mtok") is None:
        return None
    u, c, o = tokens
    mid = weighted(u, c, o, f["weights"]) * f["per_mtok"] / 1e6
    lo = hi = mid
    for row in f.get("plausible") or [{"weights": f["weights"], "per_mtok": [f["range"][0], 0, f["range"][1]]}]:
        t = weighted(u, c, o, row["weights"]) / 1e6
        lo, hi = min(lo, t * row["per_mtok"][0]), max(hi, t * row["per_mtok"][2])
    return [round(lo, 2), round(mid, 2), round(hi, 2)]


def tokens_by(reading: dict, key, lo: float = 0.0, hi: float = float("inf")) -> dict:
    """Raw tokens [uncached, cached, output] spent in [lo, hi], summed by `key(rec)`."""
    out = {}
    for r in reading["recs"]:
        if lo <= r["t0"] <= hi:
            acc = out.setdefault(key(r), [0, 0, 0])
            acc[0] += r["uncached"]
            acc[1] += r["cached"]
            acc[2] += r["output"]
    return out


def add(*triples) -> list:
    return [sum(t[i] for t in triples) for i in range(3)]


def burn(reading: dict, f: dict, lo: float, hi: float, outside_pct: float = 0.0) -> dict:
    """Percent per hour while a turn was running, over [lo, hi].

    per_active_hour: the measured rise, less outside usage, over the hours when any local turn ran (idle excluded).
    per_builder_hour: by model and effort, the fitted cost of top-level threads' turns over their summed hours, so
    four threads running at once count four builder-hours."""
    current = window_of(reading)
    s = [x for x in samples(reading["recs"]) if lo <= x[0] <= hi and current and same_window(x[2], current[1])]
    active = merge(clip([(t["start"], t["end"]) for t in reading["turns"]], lo, hi))
    hours = length(active) / 3600
    out = {"active_hours": round(hours, 1), "per_active_hour": None}
    if len(s) >= 2 and hours >= 0.5:
        rise = max(x[1] for x in s) - s[0][1] - outside_pct
        if rise >= 3:
            out["per_active_hour"] = [round(max(0.0, rise - 1) / hours, 2), round(rise / hours, 2),
                                      round((rise + 1) / hours, 2)]
        else:
            out["note"] = f"too little data: {round(rise, 1)}% of local rise over {round(hours, 1)} active hours"
    else:
        out["note"] = "too little data: fewer than two readings or under half an active hour"
    threads = reading["threads"]
    groups = {}
    for t in reading["turns"]:
        if not top_level(threads.get(t["thread"]) or {}) or not t["model"]:
            continue
        span = clip([(t["start"], t["end"])], lo, hi)
        if not span:
            continue
        g = groups.setdefault(f"{t['model']}/{t['effort']}", {"hours": 0.0, "turns": set()})
        g["hours"] += length(span) / 3600
        g["turns"].add((t["thread"], t["turn"]))
    by_turn = tokens_by(reading, lambda r: (r["thread"], r["turn"]), lo, hi)
    out["per_builder_hour"] = {}
    for name, g in sorted(groups.items(), key=lambda kv: -kv[1]["hours"]):
        if g["hours"] < 0.25:
            continue
        c = cost(add(*(by_turn[k] for k in g["turns"] if k in by_turn)) if g["turns"] else [0, 0, 0], f)
        out["per_builder_hour"][name] = {"hours": round(g["hours"], 1),
                                         "pct_per_hour": [round(x / g["hours"], 2) for x in c] if c else None}
    return out


def outside(f: dict, lo: float, hi: float) -> dict:
    """Rises no local rollout explains, within [lo, hi]: usage from elsewhere."""
    jumps = [j for j in f.get("outside") or [] if lo <= j["t1"] <= hi]
    return {"pct": round(sum(j["outside"] for j in jumps), 1), "at_least": round(sum(j["at_least"] for j in jumps), 1),
            "jumps": [{"at": iso(j["t1"]), "rise": j["rise"], "outside": j["outside"]} for j in jumps[-10:]]}


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).astimezone().strftime("%a %d %b %H:%M")


def account(reading: dict, weights: dict | None = None) -> dict | None:
    """The account picture for the current weekly window: used, reset, fit, burn and outside usage."""
    w = window_of(reading)
    if not w:
        return None
    lo, resets, used = w
    now = reading["now"]
    f = fit(reading, weights)
    out_side = outside(f, lo, resets)
    return {"host": reading["host"], "used_percent": used, "resets_at": iso(resets), "resets_ts": resets,
            "window_start": lo, "hours_left": round(max(0.0, resets - now) / 3600, 1),
            "fit": {k: v for k, v in f.items() if k != "outside"}, "_fit": f,
            "burn": burn(reading, f, lo, now, out_side["pct"]), "outside": out_side,
            "complete": reading["complete"], "behind_mb": round(reading["behind_bytes"] / 1e6)}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Codex weekly-limit usage from local rollout files.")
    ap.add_argument("--budget", type=float, default=60.0, help="seconds to spend reading (the cache keeps progress)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    reading = read(budget_s=a.budget)
    acc = account(reading)
    if a.json or not acc:
        print(json.dumps(acc))
        return
    f, b = acc["fit"], acc["burn"]
    print(f"weekly limit: {acc['used_percent']:.0f}% used; resets {acc['resets_at']} (in {acc['hours_left']} h)")
    if f.get("per_mtok") is not None:
        print(f"  fit: {f['per_mtok']} %/M weighted tokens (range {f['range'][0]}-{f['range'][1]}) "
              f"from {f['rise']}% over {f['mtok']} M" + (f"; {f['note']}" if f.get("note") else ""))
    else:
        print(f"  fit: {f.get('note')}")
    print(f"  burn: {b['per_active_hour']} %/active h over {b['active_hours']} h" +
          (f" ({b['note']})" if b.get("note") else ""))
    for name, g in b["per_builder_hour"].items():
        print(f"    {name}: {g['pct_per_hour']} %/builder-h over {g['hours']} h")
    print(f"  outside: {acc['outside']['pct']}% unexplained by local rollouts")
    if not acc["complete"]:
        print(f"  (scan incomplete: {acc['behind_mb']} MB unread; run again to finish)")


if __name__ == "__main__":
    main()
