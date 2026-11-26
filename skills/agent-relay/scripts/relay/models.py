"""The model catalogue: which models each host offers for agent work, the efforts each takes, its list price and
when it retires. models.json beside this file ships with the relay; a copy at ~/.config/agent-relay/models.json
overrides an entry with the same host and id, and adds new ones, so a model released today can be added without
waiting for a release. List prices are for comparing hosts only: a subscription is charged by its plan's quota."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .hosts import HOSTS

SHIPPED = Path(__file__).with_name("models.json")
_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
USER_FILES = (_CONFIG / "orchestrate" / "models.json", _CONFIG / "agent-relay" / "models.json")  # later wins


def _load(path: Path) -> dict:
    try:
        got = json.loads(path.read_text())
        return got if isinstance(got, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def catalogue(user_files=None) -> dict:
    """{"checked", "models"}: the shipped catalogue with the user's copies over it, entry by entry."""
    shipped = _load(SHIPPED)
    entries = {(m.get("host"), m.get("id")): {**m, "from": "shipped"} for m in shipped.get("models") or []}
    checked = [shipped.get("checked")]
    for path in USER_FILES if user_files is None else user_files:
        mine = _load(path)
        checked.append(mine.get("checked"))
        for m in mine.get("models") or []:
            key = (m.get("host"), m.get("id"))
            entries[key] = {**entries.get(key, {}), **m, "from": "yours"}
    order = lambda m: (HOSTS.index(m["host"]) if m.get("host") in HOSTS else 9, m.get("id") or "")  # noqa: E731
    return {"checked": max(filter(None, checked), default=None), "models": sorted(entries.values(), key=order)}


def price_now(m: dict, day: str | None = None) -> dict:
    """A model's list price on `day` (today by default), with any announced change that has come into force."""
    day = day or datetime.now().strftime("%Y-%m-%d")
    price = dict(m.get("price") or {})
    for change in sorted(m.get("price_changes") or [], key=lambda c: c.get("from") or ""):
        if (change.get("from") or "9999") <= day:
            price.update({k: v for k, v in change.items() if k != "from"})
    return price


def find(host: str, model_id: str) -> dict | None:
    return next((m for m in catalogue()["models"] if m.get("host") == host and m.get("id") == model_id), None)


def text(models: list[dict], checked: str | None) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"Model catalogue, checked {checked}; list prices per million tokens (input / cached / output), for "
             "comparing hosts, not what a plan charges"]
    for host in dict.fromkeys(m["host"] for m in models):
        lines.append(f"\n{host}")
        for m in (x for x in models if x["host"] == host):
            p = price_now(m)
            money = "/".join("-" if p.get(k) is None else f"${p[k]:g}" for k in ("input", "cached", "output"))
            change = next((f"; from {c['from']} ${c.get('input'):g}/${c.get('output'):g}"
                           for c in m.get("price_changes") or [] if c.get("from", "") > today), "")
            lines.append(f"  {m['id']} ({m.get('name')}): {m.get('for')}. "
                         f"Efforts {', '.join(m.get('efforts') or []) or 'not listed'}"
                         f"{', default ' + m['default_effort'] if m.get('default_effort') else ''}. {money}{change}"
                         f"{'. Retires ' + m['retires'] if m.get('retires') else ''}"
                         f"{' (your copy)' if m.get('from') == 'yours' else ''}")
    return "\n".join(lines)
