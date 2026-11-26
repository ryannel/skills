#!/usr/bin/env python3
"""Quota across agent hosts: each host's usage windows and banked resets, the history of both, and a plan for each
banked reset. Standard library only.

A reading is one host's account at one moment:

  {"host": "codex", "read_at": 1795600000.0, "source": "app-server", "plan": "promax",
   "windows": [{"name": "seven_day", "label": "weekly", "used_pct": 76.0, "resets_at": 1795881790.0}],
   "banked":  [{"id": "...", "kind": "full", "title": "Full reset", "granted_at": ..., "expires_at": ...,
                "status": "available"}]}

Where each host's reading comes from, the cheapest way each allows:

  codex        the bundled app-server's `account/rateLimits/read`, which returns the windows and the banked resets
               (`rateLimitResetCredits`) in one call and spends nothing. The caller passes in the call (`rpc`).
  claude       `claude -p /usage`, which runs no model and spends nothing, read from its text; and the
               `rate_limit_event` each `claude -p` turn prints, which the relay passes in as it sees them. Claude's
               banked resets come from that text when it shows them, else from the user (`bank`), because the only
               machine-readable source is a private endpoint that needs the sign-in token, which this module never
               reads.
  antigravity  `agy -p /usage --output-format json`, which runs no model; its shape is undocumented, so it is read
               defensively: any object with a remaining or used fraction and a reset time is a window.

Banked resets are never redeemed here, or anywhere in agent-relay: redeeming one is the user's decision. This module
only knows they exist, when they expire, what each is worth when, and what it would take to make one worth
redeeming before it expires (`reset_plan`).

Readings are appended to <cache>/agent-relay/quota/quota.jsonl, per account and not per repository, because quota belongs
to the account. A natural reset is seen when a window's `resets_at` moves on or its use falls; a redemption when a
banked reset leaves the available list. Both go to resets.jsonl. Agreed plans are in plans.json.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

HOSTS = ("codex", "claude", "antigravity")
_CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
# AGENT_RELAY_QUOTA_DIR, else ORCHESTRATE_QUOTA_DIR (its name before agent-relay), else <state>/quota. Readings and
# plans kept by orchestrate before 3.2.0, in ~/.cache/orchestrate, are copied over the first time.
STATE_DIR = Path(os.environ.get("AGENT_RELAY_QUOTA_DIR") or os.environ.get("ORCHESTRATE_QUOTA_DIR") or
                 Path(os.environ.get("AGENT_RELAY_STATE_DIR") or _CACHE / "agent-relay") / "quota")
LEGACY_DIR = _CACHE / "orchestrate"
READINGS = "quota.jsonl"
RESETS = "resets.jsonl"
PLANS = "plans.json"
BANKED = "banked.json"  # resets the user told agent-relay about, for a host that shows none it can read
FRESH_S = 10 * 60.0  # a reading younger than this is used as it is
KEEP_S = 15 * 86400.0  # readings older than this are dropped when the file is rewritten
RECENT_H = 12.0  # the burn rate is measured over this many hours
FLOOR_PCT = 5.0  # a host with less than this left in any window takes no new work
SOON_DAYS = 7.0  # a banked reset expiring within this is raised with the user
# Codex lets a banked reset be redeemed only while less than 80% of a window it covers is left, and its desktop app's
# own auto-use fires at 10% left or less (help.openai.com/en/articles/20001498).
REDEEMABLE_USED_PCT = 20.0  # a plan worth less than this is reported as lost
REDEEM_AT_USED_PCT = 90.0  # what a reset is worth at its best: nearly a whole window
EXPIRY_MARGIN_H = 6.0  # suggest redeeming at least this long before a reset expires
WINDOW_NAMES = {300: "five_hour", 10080: "seven_day", 43200: "monthly"}
LABELS = {"five_hour": "5-hour", "seven_day": "weekly", "monthly": "monthly"}
PERIOD_H = {"five_hour": 5, "seven_day": 168, "monthly": 720}


# ------------------------------------------------------------------------------------------------------ the store

def state_dir() -> Path:
    if not STATE_DIR.exists() and STATE_DIR.parent.name == "agent-relay" and LEGACY_DIR.is_dir():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        for name in (READINGS, RESETS, PLANS, BANKED):
            try:
                (STATE_DIR / name).write_bytes((LEGACY_DIR / name).read_bytes())
            except OSError:
                pass
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def _lines(name: str) -> list[dict]:
    try:
        text = (state_dir() / name).read_text()
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _append(name: str, row: dict) -> None:
    try:
        with open(state_dir() / name, "a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError:
        pass


def _read_json(name: str) -> dict:
    try:
        got = json.loads((state_dir() / name).read_text())
        return got if isinstance(got, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(name: str, data: dict) -> None:
    path = state_dir() / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    os.replace(tmp, path)


def readings(host: str | None = None, since: float = 0.0) -> list[dict]:
    return [r for r in _lines(READINGS) if (host is None or r.get("host") == host) and (r.get("read_at") or 0) >= since]


def latest(host: str, max_age_s: float | None = None, now: float | None = None) -> dict | None:
    """The newest stored reading of `host`, or None; with `max_age_s`, only one at most that old."""
    now = now or time.time()
    found = [r for r in readings(host) if r.get("windows") or r.get("banked")]
    if not found:
        return None
    best = max(found, key=lambda r: r.get("read_at") or 0)
    if max_age_s is not None and now - (best.get("read_at") or 0) > max_age_s:
        return None
    return best


def resets(host: str | None = None, since: float = 0.0) -> list[dict]:
    return [r for r in _lines(RESETS) if (host is None or r.get("host") == host) and (r.get("at") or 0) >= since]


def record(reading: dict) -> dict:
    """Stores a reading, and the natural resets and redemptions it shows against the one before it. Returns it."""
    if not reading or not reading.get("host"):
        return reading
    before = latest(reading["host"])
    _append(READINGS, reading)
    for event in changes(before, reading):
        _append(RESETS, event)
    _prune()
    return reading


def changes(before: dict | None, after: dict) -> list[dict]:
    """What happened between two readings of one host: windows that reset by themselves, and banked resets that were
    redeemed (or expired) since."""
    if not before:
        return []
    out, at = [], after.get("read_at") or time.time()
    old = {w.get("name"): w for w in before.get("windows") or []}
    for w in after.get("windows") or []:
        prev = old.get(w.get("name"))
        if not prev or prev.get("resets_at") is None or w.get("resets_at") is None:
            continue
        # use falling is what marks a reset; a reset time that moves on its own is a reading's rounding or a parse
        fell = (prev.get("used_pct") or 0) - (w.get("used_pct") or 0) > 15
        if fell:
            natural = prev["resets_at"] <= at + 60
            out.append({"host": after["host"], "at": at, "kind": "natural" if natural else "early", "window": w["name"],
                        "used_before_pct": prev.get("used_pct"), "used_after_pct": w.get("used_pct"),
                        "old_resets_at": prev["resets_at"], "new_resets_at": w["resets_at"]})
    now_ids = {b.get("id") for b in after.get("banked") or [] if b.get("status") == "available"}
    for b in before.get("banked") or []:
        if b.get("status") == "available" and b.get("id") not in now_ids:
            expired = (b.get("expires_at") or float("inf")) <= at
            out.append({"host": after["host"], "at": at, "kind": "banked_expired" if expired else "banked_redeemed",
                        "banked_id": b.get("id"), "title": b.get("title"), "expires_at": b.get("expires_at")})
    return out


def _prune() -> None:
    path = state_dir() / READINGS
    try:
        if path.stat().st_size < 4 << 20:
            return
    except OSError:
        return
    keep = [r for r in readings() if (r.get("read_at") or 0) >= time.time() - KEEP_S]
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in keep))
    os.replace(tmp, path)


# ---------------------------------------------------------------------------------------------------- the readers

def _epoch(value) -> float | None:
    """A time as epoch seconds, from seconds, milliseconds, or an ISO 8601 string."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value) / (1000.0 if value > 1e11 else 1.0)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def codex_reading(result: dict, now: float | None = None) -> dict:
    """A reading from the app-server's `account/rateLimits/read` result."""
    now = now or time.time()
    limits = (result or {}).get("rateLimits") or {}
    windows = []
    for key in ("primary", "secondary"):
        w = limits.get(key)
        if not isinstance(w, dict) or w.get("usedPercent") is None:
            continue
        minutes = w.get("windowDurationMins") or 0
        name = WINDOW_NAMES.get(minutes, f"{minutes}m")
        windows.append({"name": name, "label": LABELS.get(name, name), "used_pct": float(w["usedPercent"]),
                        "resets_at": _epoch(w.get("resetsAt"))})
    banked = []
    credits = ((result or {}).get("rateLimitResetCredits") or {}).get("credits") or []
    for c in credits:
        if not isinstance(c, dict):
            continue
        banked.append({"id": c.get("id"), "kind": "full", "title": c.get("title") or "Full reset",
                       "covers": [w["name"] for w in windows] or ["seven_day"],
                       "granted_at": _epoch(c.get("grantedAt")), "expires_at": _epoch(c.get("expiresAt")),
                       "status": c.get("status") or "available",
                       "redeem_where": "Codex: /usage, then Redeem reset; or the app's Settings > Usage & billing"})
    return {"host": "codex", "read_at": now, "source": "app-server", "plan": limits.get("planType"),
            "windows": windows, "banked": banked,
            "blocked": bool(limits.get("rateLimitReachedType")) or result.get("ordinaryUsageAllowed") is False}


def read_codex(rpc, now: float | None = None) -> dict | None:
    """Reads Codex through `rpc(method, params)`, a call on the bundled app-server. None when it can't."""
    try:
        result = rpc("account/rateLimits/read", {})
    except Exception as e:  # no app-server, signed out, or an older CLI
        return {"host": "codex", "read_at": now or time.time(), "source": "app-server", "error": str(e)[:200],
                "windows": [], "banked": []}
    return codex_reading(result, now)


CLAUDE_LINE = re.compile(r"^\s*Current (week|session)(?: \(([^)]*)\))?:\s*(\d+(?:\.\d+)?)% used(?:\s*\S\s*resets\s+(.+?))?\s*$",
                         re.IGNORECASE | re.MULTILINE)
CLAUDE_BANKED = re.compile(r"(?:use by|expires?|first expires)\s+(.+?)(?:\s*[·|]|$)", re.IGNORECASE)


def parse_when(text: str, now: float, tz_default: str | None = None) -> float | None:
    """A reset time as Claude's `/usage` prints it, such as "Dec 1 at 7pm (Europe/Stockholm)", "3pm (UTC)",
    "Mar 8, 2027" or an ISO date, as epoch seconds. A time with no date is the next one to come."""
    if not text:
        return None
    text = text.strip().rstrip(".")
    tzname = None
    m = re.search(r"\(([^)]+)\)\s*$", text)
    if m:
        tzname, text = m.group(1).strip(), text[:m.start()].strip()
    iso = _epoch(text) if re.match(r"\d{4}-\d\d-\d\d", text) else None
    if iso:
        return iso
    tz = timezone.utc
    if (tzname or tz_default) and ZoneInfo:
        try:
            tz = ZoneInfo(tzname or tz_default)
        except Exception:
            tz = datetime.now().astimezone().tzinfo or timezone.utc
    else:
        tz = datetime.now().astimezone().tzinfo or timezone.utc
    here = datetime.fromtimestamp(now, tz)
    text = re.sub(r"\s+at\s+", " ", text.replace(",", ""))
    clock = re.search(r"(\d{1,2})(?::(\d\d))?\s*(am|pm)\b", text, re.IGNORECASE)
    hour = minute = 0
    if clock:
        hour, minute = int(clock.group(1)) % 12, int(clock.group(2) or 0)
        if clock.group(3).lower() == "pm":
            hour += 12
        text = (text[:clock.start()] + text[clock.end():]).strip()
    date, has_year = None, bool(re.search(r"\b\d{4}\b", text))
    probe = text if has_year else f"{text} {here.year}"  # Python 3.15 refuses a day of month with no year
    for fmt in ("%b %d %Y", "%B %d %Y", "%d %b %Y", "%d %B %Y"):
        try:
            date = datetime.strptime(probe, fmt)
            break
        except ValueError:
            continue
    if date:
        when = datetime(date.year, date.month, date.day, hour, minute, tzinfo=tz)
        if not has_year and when.timestamp() < now - 86400 * 30:
            when = when.replace(year=date.year + 1)
        return when.timestamp()
    if clock:
        when = here.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if when.timestamp() <= now:
            when += timedelta(days=1)
        return when.timestamp()
    return None


def claude_usage_reading(text: str, now: float | None = None) -> dict:
    """A reading from the text `claude -p /usage` prints, such as "Current week (all models): 27% used · resets
    Dec 1 at 7pm (Europe/Stockholm)". "all models" is the weekly window; a named model is its own window, which
    routing only reads for that model; the session line is the 5-hour window."""
    now = now or time.time()
    windows = []
    for m in CLAUDE_LINE.finditer(text or ""):
        kind, scope, used, when = m.group(1).lower(), (m.group(2) or "").strip(), float(m.group(3)), m.group(4)
        if kind == "session":
            name, label = "five_hour", "5-hour"
        elif not scope or scope.lower() == "all models":
            name, label = "seven_day", "weekly"
        else:
            name, label = f"seven_day:{scope.lower()}", f"weekly ({scope})"
        windows.append({"name": name, "label": label, "used_pct": used, "resets_at": parse_when(when, now),
                        **({"model": scope.lower()} if name.startswith("seven_day:") else {})})
    banked = []
    for line in (text or "").splitlines():
        if not re.search(r"limit[- ]reset|resets? kept|reset for free", line, re.IGNORECASE):
            continue
        m = CLAUDE_BANKED.search(line)
        expires = parse_when(m.group(1), now) if m else None
        left = re.search(r"(\d+)\s+left", line)
        for i in range(int(left.group(1)) if left else 1):
            banked.append({"id": f"claude-usage-{int(expires or 0)}-{i}", "kind": "limit_reset",
                           "title": line.strip()[:120], "expires_at": expires, "status": "available",
                           "covers": ["seven_day", "five_hour"],
                           "redeem_where": "Claude: /limit-reset in Claude Code, or claude.ai Settings > Usage"})
    return {"host": "claude", "read_at": now, "source": "/usage", "windows": windows, "banked": banked}


def claude_event_windows(event: dict) -> list[dict]:
    """The windows a `rate_limit_event` from `claude -p` carries: `unifiedWindows` with each window's utilization
    (0 to 1) and reset time."""
    info = (event or {}).get("rate_limit_info") or {}
    out = []
    for key, w in (info.get("unifiedWindows") or {}).items():
        if not isinstance(w, dict) or w.get("utilization") is None:
            continue
        name = {"five_hour": "five_hour", "seven_day": "seven_day"}.get(key, key)
        out.append({"name": name, "label": LABELS.get(name, name), "used_pct": round(float(w["utilization"]) * 100, 1),
                    "resets_at": _epoch(w.get("resetsAt"))})
    if not out and info.get("utilization") is not None and info.get("rateLimitType"):
        name = info["rateLimitType"]
        out.append({"name": name, "label": LABELS.get(name, name), "used_pct": round(float(info["utilization"]) * 100, 1),
                    "resets_at": _epoch(info.get("resetsAt"))})
    return out


def note_claude_event(event: dict, now: float | None = None) -> dict | None:
    """Stores the windows from a `rate_limit_event`, merged into Claude's latest reading so the per-model windows and
    banked resets that only `/usage` shows are kept."""
    windows = claude_event_windows(event)
    if not windows:
        return None
    base = latest("claude") or {"host": "claude", "windows": [], "banked": []}
    names = {w["name"] for w in windows}
    reading = {**base, "read_at": now or time.time(), "source": "rate_limit_event",
               "windows": windows + [w for w in base.get("windows") or [] if w.get("name") not in names]}
    return record(reading)


def read_claude(claude: str, env: dict | None = None, timeout_s: float = 60.0, now: float | None = None) -> dict:
    """Runs `claude -p /usage`, which prints the plan's windows without running a model."""
    now = now or time.time()
    try:
        done = subprocess.run([claude, "-p", "/usage"], capture_output=True, text=True, timeout=timeout_s, env=env,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"host": "claude", "read_at": now, "source": "/usage", "error": str(e)[:200], "windows": [], "banked": []}
    reading = claude_usage_reading(done.stdout, now)
    if not reading["windows"]:
        reading["error"] = (done.stderr or done.stdout or "no usage lines")[-200:]
    if "subscription" not in (done.stdout or "") and "API" in (done.stdout or ""):
        reading["error"] = "Claude Code is using an API key, not the plan"
    reading["banked"] += [b for b in told("claude") if b["id"] not in {x["id"] for x in reading["banked"]}]
    return reading


def _walk(value, path=()):
    if isinstance(value, dict):
        yield path, value
        for k, v in value.items():
            yield from _walk(v, path + (str(k),))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, path + (str(i),))


AGY_WINDOWS = {"weekly": "seven_day", "5h": "five_hour", "daily": "one_day"}


def model_slug(display: str) -> str:
    """`Claude Opus 5.5` -> `claude-opus-5-5`: Antigravity names a group's models by display name, and its model IDs
    are those names in this form, with the effort after them (`gemini-4-neon-medium`)."""
    return re.sub(r"[^a-z0-9]+", "-", display.lower()).strip("-")


def agy_group_windows(groups: list) -> list[dict]:
    """Antigravity's `/usage` groups models that share quota ("Gemini Models"; "Claude and GPT models"), each with a
    weekly and a 5-hour bucket. Each window is named `<window>:<group>`, such as `seven_day:gemini`, and carries the
    group's models, so only the group a model is in limits it. A bucket never used has its reset at the epoch, which
    is kept as no reset time rather than one long past."""
    out = []
    for g in groups:
        if not isinstance(g, dict):
            continue
        group = model_slug(re.sub(r"\bmodels?\b", "", str(g.get("name") or "models"), flags=re.I)) or "models"
        listed = re.sub(r"^.*?:", "", str(g.get("description") or ""))
        models = [model_slug(m) for m in listed.split(",") if m.strip()]
        for b in g.get("buckets") or []:
            if not isinstance(b, dict) or not isinstance(b.get("remaining_fraction"), (int, float)):
                continue
            window = AGY_WINDOWS.get(str(b.get("window")), model_slug(str(b.get("window") or b.get("id") or "window")))
            reset = _epoch(b.get("reset_time"))
            kind = {"seven_day": "weekly", "five_hour": "5-hour", "one_day": "daily"}.get(window, window)
            out.append({"name": f"{window}:{group}", "label": f"{g.get('name') or group} {kind}",
                        "used_pct": round(max(0.0, min(100.0, (1 - float(b["remaining_fraction"])) * 100)), 1),
                        "resets_at": reset if reset and reset > 86400 * 365 else None, "models": models})
    return out


def agy_reading(payload, now: float | None = None) -> dict:
    """A reading from `agy -p /usage --output-format json`. Its shape is undocumented, so any object holding a
    remaining or used fraction (or percent) is a window, named by its own name, id, model or group and kind of window,
    with its reset time from `reset_time`, `resetTime`, `reset_in_seconds` or `resets_at`."""
    now = now or time.time()
    groups = ((payload.get("command") or {}).get("data") or {}).get("groups") if isinstance(payload, dict) else None
    if isinstance(groups, list) and groups:
        return {"host": "antigravity", "read_at": now, "source": "/usage", "plan": None,
                "windows": agy_group_windows(groups), "banked": told("antigravity")}
    if isinstance(payload, dict) and isinstance(payload.get("response"), str):
        try:
            payload = json.loads(payload["response"])
        except json.JSONDecodeError:
            pass
    windows, seen = [], set()
    for path, obj in _walk(payload):
        used = None
        for key in ("remaining_fraction", "remainingFraction"):
            if isinstance(obj.get(key), (int, float)):
                used = (1 - float(obj[key])) * 100
        for key in ("used_percent", "usedPercent", "used_percentage", "utilization"):
            if used is None and isinstance(obj.get(key), (int, float)):
                v = float(obj[key])
                used = v * 100 if key == "utilization" and v <= 1 else v
        if used is None and isinstance(obj.get("remaining_amount"), (int, float)) and \
                isinstance(obj.get("limit") or obj.get("total"), (int, float)) and (obj.get("limit") or obj.get("total")):
            used = 100 * (1 - float(obj["remaining_amount"]) / float(obj.get("limit") or obj.get("total")))
        if used is None:
            continue
        reset = None
        for key in ("reset_time", "resetTime", "resets_at", "resetsAt", "reset_at"):
            reset = reset or _epoch(obj.get(key))
        if reset is None and isinstance(obj.get("reset_in_seconds"), (int, float)):
            reset = now + float(obj["reset_in_seconds"])
        label = " ".join(str(obj.get(k)) for k in ("group", "model", "name", "displayName", "id", "window", "kind",
                                                    "bucket") if obj.get(k)) or "/".join(path[-2:]) or "quota"
        name = re.sub(r"\s+", "_", label.lower())
        if name in seen:
            name = f"{name}:{len(seen)}"
        seen.add(name)
        windows.append({"name": name, "label": label, "used_pct": round(max(0.0, min(100.0, used)), 1),
                        "resets_at": reset, **({"disabled": True} if obj.get("disabled") else {})})
    plan = None
    for _, obj in _walk(payload):
        plan = plan or obj.get("plan_tier") or obj.get("planTier") or obj.get("plan")
    return {"host": "antigravity", "read_at": now, "source": "/usage", "plan": plan if isinstance(plan, str) else None,
            "windows": windows, "banked": told("antigravity")}


def read_agy(agy: str, env: dict | None = None, timeout_s: float = 25.0, now: float | None = None) -> dict:
    now = now or time.time()
    try:
        done = subprocess.run([agy, "-p", "/usage", "--output-format", "json"], capture_output=True, text=True,
                              timeout=timeout_s, env=env, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"host": "antigravity", "read_at": now, "source": "/usage", "error": str(e)[:200], "windows": [],
                "banked": []}
    payload = None
    for chunk in (done.stdout.strip(), *done.stdout.strip().splitlines()[::-1]):
        try:
            payload = json.loads(chunk)
            break
        except (json.JSONDecodeError, ValueError):
            continue
    if payload is None:
        return {"host": "antigravity", "read_at": now, "source": "/usage", "windows": [], "banked": [],
                "error": (done.stderr or done.stdout or "no output")[-200:]}
    reading = agy_reading(payload, now)
    if not reading["windows"]:
        reading["error"] = "no quota figures in agy's /usage output"
        reading["raw"] = json.dumps(payload)[:2000]
    return reading


# ------------------------------------------------------------------------------------- resets the user tells about

def told(host: str) -> list[dict]:
    """The banked resets the user told agent-relay about for `host`, still available."""
    now = time.time()
    return [b for b in (_read_json(BANKED).get(host) or [])
            if b.get("status") == "available" and (b.get("expires_at") or float("inf")) > now]


def bank(host: str, expires_at: float, title: str = "", covers: list[str] | None = None) -> dict:
    """Records a banked reset the user says `host` gave them, for a host whose resets the relay can't read."""
    data = _read_json(BANKED)
    entry = {"id": f"{host}-told-{int(time.time())}", "kind": "told", "title": title or "Banked reset",
             "expires_at": expires_at, "granted_at": time.time(), "status": "available",
             "covers": covers or ["seven_day"],
             "redeem_where": {"claude": "Claude: /limit-reset in Claude Code, or claude.ai Settings > Usage",
                              "codex": "Codex: /usage, then Redeem reset"}.get(host, f"{host}'s own usage page")}
    data.setdefault(host, []).append(entry)
    _write_json(BANKED, data)
    return entry


def mark_used(banked_id: str) -> bool:
    """Marks a reset the user told about as used, once they say they redeemed it."""
    data, hit = _read_json(BANKED), False
    for entries in data.values():
        for b in entries:
            if b.get("id") == banked_id and b.get("status") == "available":
                b["status"], b["used_at"], hit = "redeemed", time.time(), True
    if hit:
        _write_json(BANKED, data)
        _append(RESETS, {"host": banked_id.split("-told-")[0], "at": time.time(), "kind": "banked_redeemed",
                         "banked_id": banked_id})
    return hit


# ------------------------------------------------------------------------------------------- plans the user agrees

def plans() -> dict:
    return _read_json(PLANS)


def agree(banked_id: str, host: str, said: str = "") -> dict:
    data = plans()
    data[banked_id] = {"host": host, "agreed_at": time.time(), "said": said}
    _write_json(PLANS, data)
    return data[banked_id]


def withdraw(banked_id: str) -> bool:
    data = plans()
    if banked_id not in data:
        return False
    del data[banked_id]
    _write_json(PLANS, data)
    return True


# ------------------------------------------------------------------------------------------------------- analysis

def burn_rate(host: str, window: str, resets_at: float | None, now: float | None = None,
              hours: float = RECENT_H) -> float | None:
    """The percent of `window` used per hour over the last `hours`, from stored readings within the same window (the
    same reset time). None when the readings span less than half an hour."""
    now = now or time.time()
    points = []
    for r in readings(host, since=now - hours * 3600):
        for w in r.get("windows") or []:
            if w.get("name") == window and w.get("used_pct") is not None and \
                    (resets_at is None or w.get("resets_at") is None or abs(w["resets_at"] - resets_at) < 3600):
                points.append((r["read_at"], w["used_pct"]))
    if len(points) < 2:
        return None
    points.sort()
    span_h = (points[-1][0] - points[0][0]) / 3600
    if span_h < 0.5:
        return None
    return max(0.0, (points[-1][1] - points[0][1]) / span_h)


def window_view(host: str, w: dict, now: float, rate: float | None = None) -> dict:
    """One window with its time to reset, burn rate and what is projected to be left, unused, at the reset."""
    if rate is None:
        rate = burn_rate(host, w["name"], w.get("resets_at"), now)
    left = max(0.0, 100.0 - (w.get("used_pct") or 0))
    hours = max(0.0, ((w.get("resets_at") or now) - now) / 3600)
    at_reset = None if rate is None else max(0.0, left - rate * hours)
    return {**w, "left_pct": round(left, 1), "hours_to_reset": round(hours, 1),
            "pct_per_hour": None if rate is None else round(rate, 2),
            "left_at_reset_pct": None if at_reset is None else round(at_reset, 1),
            "runs_out_in_h": None if not rate else round(left / rate, 1)}


def binding_windows(reading: dict, model: str | None = None) -> list[dict]:
    """The windows that limit a model on this host: every window not tied to a model, and the one tied to `model`."""
    out = []
    for w in reading.get("windows") or []:
        if w.get("disabled"):
            continue
        tied = w.get("model")
        if tied and (not model or tied not in model.lower()):
            continue
        if w.get("models") is not None:
            # a window shared by a group of models binds only the models in that group
            if model and not any(model.lower().startswith(m) for m in w["models"] if m):
                continue
            out.append(w)
            continue
        if reading["host"] == "antigravity" and model and not any(
                part in w["name"] for part in re.split(r"[-_ ]", model.lower()) if len(part) > 3 and part != "gemini"):
            # Antigravity's windows are per model or group; one naming another model doesn't bind this one
            named = re.search(r"(neon|carbon|hydrogen|argon|claude|opus|sonnet|gpt)", w["name"])
            if named:
                continue
        out.append(w)
    return out


def redeem_value(u: float, rate: float, begin: float, t: float, closes: float) -> float:
    """What redeeming at `t` gives back that can actually be spent: what is used by then (the window started at
    `begin` with `u` used), capped by what the same pace spends between `t` and the window's own reset at `closes`,
    since the reset doesn't move that day (Claude documents this; for Codex it is assumed until a redemption shows)."""
    used_then = min(100.0, u + rate * max(0.0, (t - begin) / 3600))
    return max(0.0, min(used_then, rate * max(0.0, (closes - t) / 3600), 100.0))


def best_moment(u: float, rate: float, begin: float, last: float, closes: float) -> tuple[float, float]:
    """(when to redeem in one window, what it gives back then), searched over the hours from `begin` to `last`."""
    if last <= begin:
        return begin, redeem_value(u, rate, begin, begin, closes)
    steps = 96
    best = (begin, -1.0)
    for i in range(steps + 1):
        t = begin + (last - begin) * i / steps
        v = redeem_value(u, rate, begin, t, closes)
        if v > best[1] + 1e-9:
            best = (t, v)
    return best


def reset_plan(host: str, b: dict, reading: dict, now: float | None = None, per_builder_pct_h: float | None = None,
               rate_hint: float | None = None, after: dict | None = None) -> dict:
    """What one banked reset is worth and what it would take to use it well, for the user to decide.

    A reset empties the window it covers but, as far as anyone has documented, leaves that window's own reset day
    where it was. So it is worth the quota it lets you spend that you couldn't otherwise: no more than what is used
    when it is redeemed, and no more than what the pace spends from then to the window's own reset. At a steady pace
    that peaks about halfway between the window filling and its reset, so a reset is worth most when the work wants
    more than one window holds. The plan finds the window and moment worth most before the reset expires, says what
    pace makes it worth REDEEM_AT_USED_PCT, and whether the measured pace gets there."""
    now = now or time.time()
    expires = b.get("expires_at") or (now + 365 * 86400)
    covers = set(b.get("covers") or ["seven_day"])
    windows = [w for w in reading.get("windows") or [] if w.get("name") in covers] or \
        [w for w in reading.get("windows") or [] if w.get("name") == "seven_day"] or (reading.get("windows") or [])[:1]
    base = {"id": b.get("id"), "host": host, "title": b.get("title"), "expires_at": expires,
            "expires_in_h": round(max(0.0, (expires - now) / 3600), 1), "agreed": b.get("id") in plans(),
            "redeem_where": b.get("redeem_where"), "raise_with_user": False}
    name = f"{host.capitalize()}'s banked reset ({b.get('title') or 'reset'}) expiring {when_text(expires)}"
    if not windows:
        return {**base, "status": "unknown", "say": f"{name}: no usage window is known for this host yet."}
    w = max(windows, key=lambda x: (x.get("name") == "seven_day", x.get("used_pct") or 0))
    used, natural = w.get("used_pct") or 0.0, w.get("resets_at") or expires
    base.update(window=w.get("label") or w.get("name"), used_pct=used, natural_reset_at=natural)
    if expires <= now:
        return {**base, "status": "expired", "say": f"{name} has expired."}
    rate = burn_rate(host, w["name"], w.get("resets_at"), now)
    rate = rate_hint if rate is None else rate
    if rate is None:
        return {**base, "status": "unmeasured",
                "say": f"{name}: the pace isn't measured yet (it needs readings over half an hour), so the plan for "
                       "it waits for one."}
    period = PERIOD_H.get(w.get("name"), 168) * 3600
    redeem_by = expires - EXPIRY_MARGIN_H * 3600
    # (used at the start, when spending starts, the last moment to redeem, the window's own reset)
    options = [(used, now, min(natural, redeem_by), natural)]
    if after and after.get("redeem_at"):  # an earlier reset is planned first: this one comes after it
        prev, prev_closes = after["redeem_at"], after.get("window_resets_at") or natural
        options = [(0.0, prev, min(prev_closes, redeem_by), prev_closes)] if prev < prev_closes else []
        options = [o for o in options if o[2] > o[1]]
    start = natural
    while start < redeem_by and len(options) < 60:
        if not after or start >= (after.get("window_resets_at") or 0):
            options.append((0.0, start, min(start + period, redeem_by), start + period))
        start += period
    if not options:
        return {**base, "status": "will_be_lost", "pct_per_hour": round(rate, 2), "worth_pct": 0.0,
                "raise_with_user": (expires - now) / 3600 <= SOON_DAYS * 24,
                "say": f"{name}: the reset expiring before it takes every window left before this one expires."}

    def value_at(pace: float) -> tuple[float, tuple]:
        best = (-1.0, None)
        for u, begin, last, closes in options:
            t, v = best_moment(u, pace, begin, last, closes)
            if v > best[0] + 0.05:
                best = (v, (u, begin, t, closes))
        return best
    value, (start_used, begin, redeem_at, closes) = value_at(rate)
    target = REDEEM_AT_USED_PCT
    lo, hi = 0.0, 100.0  # the pace that makes it worth the target, by bisection
    if value_at(hi)[0] < target:
        need = None
    else:
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if value_at(mid)[0] < target else (lo, mid)
        need = hi
    used_then = min(100.0, start_used + rate * max(0.0, (redeem_at - begin) / 3600))
    value_now = redeem_value(used, rate, now, now, natural) if now < redeem_by else 0.0
    if value_now >= REDEEMABLE_USED_PCT and value_now >= value * 0.95:  # waiting gains little: now is the moment
        status, redeem_at, used_then, value = "redeem_now", now, used, value_now
    elif value >= target * 0.95:
        status = "on_track"
    elif value >= REDEEMABLE_USED_PCT:
        status = "behind"
    else:
        status = "will_be_lost"
    builders = None
    if per_builder_pct_h and need and need > rate:
        builders = max(1, int(-(-(need - rate) // per_builder_pct_h)))
    soon = (expires - now) / 3600 <= SOON_DAYS * 24
    out = {**base, "status": status, "pct_per_hour": round(rate, 2),
           "need_pct_per_hour": None if need is None else round(need, 2), "worth_pct": round(value, 1),
           "window_from": begin, "redeem_at": redeem_at, "used_at_redeem_pct": round(used_then, 1),
           "window_resets_at": closes, "more_builders": builders,
           "raise_with_user": soon and status in ("behind", "will_be_lost", "redeem_now")}
    out["say"] = plan_sentence(name, out, b)
    return out


def when_text(ts: float | None) -> str:
    if not ts:
        return "unknown"
    return datetime.fromtimestamp(ts).astimezone().strftime("%a %d %b %H:%M")


def plan_sentence(name: str, p: dict, b: dict) -> str:
    rate, need, worth = p["pct_per_hour"], p.get("need_pct_per_hour"), p["worth_pct"]
    where = f" {b.get('redeem_where')}." if b.get("redeem_where") else ""
    when = (f"redeem it around {when_text(p['redeem_at'])}, at about {p['used_at_redeem_pct']:.0f}% used, which "
            f"leaves time before the window's own reset on {when_text(p['window_resets_at'])} to spend what it gives "
            "back")
    pace = (f"Making it worth {REDEEM_AT_USED_PCT:.0f}% takes about {need:.1f}%/h" if need else
            "No pace makes it worth the full amount before it expires")
    start = ""
    natural, begin = p.get("natural_reset_at"), p.get("window_from")
    if natural and begin and p["status"] != "redeem_now":
        period = PERIOD_H.get("seven_day" if p.get("window") == "weekly" else str(p.get("window")), 168) * 3600
        renewal = abs(begin - natural) < 60 or (p.get("window_resets_at") and
                                                abs(p["window_resets_at"] - period - begin) < 60)
        if renewal:
            start = (f" The window renews to empty on {when_text(begin)} whatever is left, so redeeming before then "
                     "gives back little; this counts from that renewal.")
        elif begin > natural:
            start = f" This counts from {when_text(begin)}, when the reset before it is planned to be redeemed."
    gap = (f"; {p['more_builders']} more builder{'s' if p['more_builders'] != 1 else ''} on {p['host']} would close "
           "the gap") if p.get("more_builders") else ""
    if p["status"] == "redeem_now":
        return (f"{name}: now is the moment to redeem it, if you agree: {p['used_pct']:.0f}% of the window is used and "
                f"at {rate:.1f}%/h you'd spend about {worth:.0f}% more before its own reset on "
                f"{when_text(p['window_resets_at'])}.{where}")
    if p["status"] == "on_track":
        return f"{name}: on track at {rate:.1f}%/h.{start} Best to {when}; it gives back about {worth:.0f}% then."
    if p["status"] == "behind":
        return (f"{name}: at {rate:.1f}%/h it is worth about {worth:.0f}% at best, if you {when}.{start} {pace}{gap}.")
    return (f"{name}: at {rate:.1f}%/h the work never needs more than the window holds before it expires, so it would "
            f"be worth about {worth:.0f}%, and lost.{start} {pace}{gap}.")


def summary(reading: dict | None, now: float | None = None, per_builder_pct_h: float | None = None,
            rate_hint: float | None = None) -> dict | None:
    """A reading with each window's view and each available banked reset's plan, for `quota`, routing and the
    dashboard."""
    if not reading:
        return None
    now = now or time.time()
    host = reading["host"]
    views = []
    for w in reading.get("windows") or []:
        rate = burn_rate(host, w["name"], w.get("resets_at"), now)
        views.append(window_view(host, w, now, rate if rate is not None or w.get("name") != "seven_day" else rate_hint))
    available = [b for b in reading.get("banked") or [] if b.get("status") == "available"]
    return {**reading, "age_s": round(now - (reading.get("read_at") or now)), "windows": views,
            "plans": sequenced_plans(host, available, reading, now, per_builder_pct_h, rate_hint)}


def sequenced_plans(host, available, reading, now, per_builder_pct_h=None, rate_hint=None) -> list[dict]:
    """Each banked reset's plan, the soonest to expire first, each one after the moment the one before it is planned
    to be redeemed, so two resets are never planned into the same spending."""
    out, prev = [], None
    for b in sorted(available, key=lambda x: x.get("expires_at") or float("inf")):
        p = reset_plan(host, b, reading, now, per_builder_pct_h, rate_hint, after=prev)
        out.append(p)
        if p.get("redeem_at") and p.get("status") in ("on_track", "behind", "redeem_now"):
            prev = p
    return out


def loss_score(view: dict, model: str | None = None) -> tuple[float, str, bool]:
    """(the quota this host would otherwise lose, why, whether it is open for new work). What would be lost is what
    is projected to be left at the next reset of the window that binds tightest; a host with less than FLOOR_PCT left
    in any binding window is closed."""
    windows = [w for w in binding_windows(view, model) if w.get("used_pct") is not None]
    if not windows:
        return 0.0, "no quota reading", True
    tight = min(windows, key=lambda w: w.get("left_pct", 100))
    if tight.get("left_pct", 100) < FLOOR_PCT:
        return 0.0, f"{tight.get('label')} window {tight.get('left_pct'):.0f}% left, resets {when_text(tight.get('resets_at'))}", False
    # a window never used has no reset to count down to; a 5-hour window is a throttle that renews all day, so what it
    # has left at its reset isn't lost: it only closes the host when it runs out (above)
    timed = ([w for w in windows if w.get("resets_at") and not str(w.get("name", "")).startswith("five_hour")]
             or [w for w in windows if w.get("resets_at")] or windows)
    soonest = min(timed, key=lambda w: w.get("hours_to_reset", 1e9))
    lost = soonest.get("left_at_reset_pct")
    if lost is None:
        lost = soonest.get("left_pct", 0.0)
        why = (f"{soonest.get('label')} {soonest.get('left_pct'):.0f}% left, resets in "
               f"{soonest.get('hours_to_reset'):.0f} h (no pace measured yet, so all of it counts as at risk)")
    else:
        why = (f"{soonest.get('label')} {soonest.get('left_pct'):.0f}% left, about {lost:.0f}% unused at its reset in "
               f"{soonest.get('hours_to_reset'):.0f} h")
    # a window bigger than its time left can bear is capped by the tightest window: quota beyond it can't be spent
    lost = min(lost, tight.get("left_pct", lost))
    return lost, why, True


def iso(ts: float | None) -> str | None:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None
