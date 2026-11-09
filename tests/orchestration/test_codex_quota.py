"""Checks for codex_quota: reading rollouts incrementally and within budget, idle exclusion, the tokens-to-percent
fit, and usage from elsewhere. Rollouts are small synthetic files in the shape Codex writes, never real ones."""

import json
import math
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills/orchestration/build/scripts"
sys.path.insert(0, str(SCRIPTS))
import codex_quota  # noqa: E402

H = 3600.0
NOW = float(int(time.time()))  # files are written now, and the reader goes by their mtime
RESETS = NOW + 100 * H  # the window started 68 h before NOW


def stamp(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class Rollout:
    """Writes one thread's rollout file as Codex does: compact JSON lines, cumulative token totals per call, and the
    account's weekly snapshot on each call."""

    def __init__(self, home: Path, thread: str, start: float, cwd="/w", origin="Codex Desktop", source="vscode",
                 name=None, prompt="hello"):
        day = datetime.fromtimestamp(start, timezone.utc)
        folder = home / "sessions" / day.strftime("%Y/%m/%d")
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"rollout-{day.strftime('%Y-%m-%dT%H-%M-%S')}-{thread}.jsonl"
        self.thread, self.total, self.n = thread, [0, 0, 0], 0
        self.write(start, "session_meta", {"id": thread, "cwd": cwd, "originator": origin, "source": source,
                                           "base_instructions": {"text": "x" * 200}})
        self.event(start, "item_completed", item={"type": "UserMessage",
                                                   "content": [{"type": "text", "text": prompt}]})
        if name:
            with open(home / "session_index.jsonl", "a") as handle:
                handle.write(json.dumps({"id": thread, "thread_name": name}) + "\n")

    def write(self, t: float, kind: str, payload: dict) -> None:
        with open(self.path, "a") as handle:
            handle.write(json.dumps({"timestamp": stamp(t), "ordinal": self.n, "type": kind, "payload": payload},
                                    separators=(",", ":")) + "\n")
        self.n += 1

    def event(self, t: float, kind: str, **payload) -> None:
        self.write(t, "event_msg", {"type": kind, **payload})

    def call(self, t: float, uncached: int, used: float | None, cached: int = 0, output: int = 0,
             resets: float = RESETS) -> None:
        self.total = [self.total[0] + uncached + cached, self.total[1] + cached, self.total[2] + output]
        usage = {"input_tokens": self.total[0], "cached_input_tokens": self.total[1], "output_tokens": self.total[2]}
        limits = None if used is None else {"limit_id": "codex", "primary": {
            "used_percent": float(used), "window_minutes": 10080, "resets_at": int(resets)}}
        self.event(t, "token_count", info={"total_token_usage": usage, "last_token_usage": usage},
                   rate_limits=limits)

    def turn(self, turn: str, start: float, end: float | None, calls, model="gpt-6.1-sol", effort="medium") -> None:
        """calls: [(time, uncached tokens, used percent)]"""
        self.event(start, "task_started", turn_id=turn, started_at=int(start))
        self.write(start, "turn_context", {"turn_id": turn, "model": model, "effort": effort})
        for t, tokens, used in calls:
            self.call(t, tokens, used)
        if end is not None:
            self.event(end, "task_complete", turn_id=turn, started_at=int(start), completed_at=int(end))


def floor_usage(k_per_mtok: float, base: float = 0.0):
    """The account figure Codex reports: whole percents, rounded down."""
    return lambda tokens: math.floor(base + k_per_mtok * tokens / 1e6)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "codex"
        self.cache = Path(self.tmp.name) / "cache.json"

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, budget=10.0, **kw):
        return codex_quota.read(budget_s=budget, home=self.home, cache=self.cache, now=NOW, **kw)

    def steady(self, thread="t1", start=NOW - 20 * H, turns=4, turn_h=1.0, gap_h=3.0, k=0.5, calls=20,
               tokens=1_000_000, base=0.0, used_from=None, **kw):
        """A thread whose turns each spend `calls` x `tokens` uncached tokens, with usage at `k` %/M tokens."""
        r = Rollout(self.home, thread, start, **kw)
        usage, spent, t = used_from or floor_usage(k, base), 0, start
        for n in range(turns):
            seq = []
            for i in range(calls):
                spent += tokens
                seq.append((t + (i + 1) * turn_h * H / (calls + 1), tokens, usage(spent)))
            r.turn(f"{thread}-turn{n}", t, t + turn_h * H, seq)
            t += (turn_h + gap_h) * H
        return r


class Reading(Base):
    def test_reads_turns_tokens_and_samples(self):
        self.steady(name="build CORE M1")
        reading = self.read()
        self.assertTrue(reading["complete"])
        self.assertEqual(len(reading["turns"]), 4)
        self.assertEqual(reading["threads"]["t1"]["name"], "build CORE M1")
        self.assertEqual(reading["threads"]["t1"]["prompts"], ["hello"])
        self.assertEqual(sum(r["uncached"] for r in reading["recs"]), 80_000_000)
        self.assertEqual(reading["latest"][1], 40.0)

    def test_marker_quoted_inside_an_item_is_not_an_event(self):
        r = self.steady(turns=1)
        quoted = '{"payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":99}}}}'
        r.write(NOW - 10 * H, "response_item", {"type": "custom_tool_call_output", "output": "x" * 300 + quoted})
        reading = self.read()
        self.assertNotIn(99.0, [s[1] for s in codex_quota.samples(reading["recs"])])

    def test_reads_incrementally_and_stops_at_its_budget(self):
        r = self.steady(turns=1)
        first = self.read()
        self.assertTrue(first["complete"])
        r.turn("late", NOW - H, NOW - 0.5 * H, [(NOW - 0.6 * H, 2_000_000, 12)])
        second = self.read()
        self.assertEqual(max(s[1] for s in codex_quota.samples(second["recs"])), 12)
        self.assertEqual(len(second["turns"]), 2)
        self.steady(thread="t2", turns=1)
        partial = self.read(budget=0.0)
        self.assertFalse(partial["complete"])
        self.assertGreater(partial["behind_bytes"], 0)
        self.assertTrue(self.read()["complete"])  # the next call carries on

    def test_enters_a_long_file_at_the_horizon(self):
        r = Rollout(self.home, "long", NOW - 30 * 86400)
        padding = "y" * 4000
        for i in range(600):  # about 2.5 MB of old history, before the horizon
            r.write(NOW - 30 * 86400 + i * 60, "response_item", {"type": "message", "text": padding})
        r.turn("old", NOW - 29 * 86400, NOW - 29 * 86400 + 60, [(NOW - 29 * 86400 + 30, 5_000_000, 80)])
        for i in range(600):
            r.write(NOW - 20 * 86400 + i * 60, "response_item", {"type": "message", "text": padding})
        r.turn("new", NOW - 2 * H, NOW - H, [(NOW - 1.5 * H, 1_000_000, 3), (NOW - 1.2 * H, 1_000_000, 4)])
        reading = self.read()
        self.assertEqual({t["turn"] for t in reading["turns"]}, {"new"})
        self.assertEqual(codex_quota.cache_for(self.home).name.startswith("rollouts-"), True)


class Analysis(Base):
    def test_idle_time_is_excluded_from_burn(self):
        # Four one-hour turns three hours apart: 20 % over 13 wall hours, but only 4 active hours.
        self.steady(k=0.25, turns=4, turn_h=1.0, gap_h=3.0)
        reading = self.read()
        acc = codex_quota.account(reading)
        burn = acc["burn"]
        self.assertAlmostEqual(burn["active_hours"], 4.0, delta=0.1)
        lo, mid, hi = burn["per_active_hour"]
        self.assertTrue(lo <= 20 / 4 <= hi, burn)
        self.assertGreater(lo, 20 / 13 * 2)  # the wall-clock rate would be about 1.5 %/h

    def test_builder_hours_count_parallel_threads_separately(self):
        start = NOW - 10 * H
        a = Rollout(self.home, "a", start)
        b = Rollout(self.home, "b", start)
        a.turn("a1", start, start + 2 * H, [(start + i * 0.1 * H, 1_000_000, 0.5 * i) for i in range(1, 20)])
        b.turn("b1", start, start + 2 * H, [(start + i * 0.1 * H + 1, 1_000_000, 0.5 * i) for i in range(1, 20)])
        reading = self.read()
        burn = codex_quota.account(reading)["burn"]
        self.assertAlmostEqual(burn["active_hours"], 2.0, delta=0.05)
        self.assertAlmostEqual(burn["per_builder_hour"]["gpt-6.1-sol/medium"]["hours"], 4.0, delta=0.05)

    def test_fit_recovers_the_rate_and_its_range_holds_it(self):
        self.steady(k=0.5, turns=6, calls=30)  # 180 M tokens, 90 %
        f = codex_quota.fit(self.read())
        self.assertIsNone(f.get("note"))
        lo, hi = f["range"]
        self.assertTrue(lo <= 0.5 <= hi, f)
        self.assertLess(hi - lo, 0.05)
        self.assertEqual(codex_quota.cost([10_000_000, 0, 0], f)[1], round(f["per_mtok"] * 10, 2))

    def test_fit_says_too_little_data(self):
        self.steady(k=0.05, turns=1, calls=10)  # half a percent of rise
        f = codex_quota.fit(self.read())
        self.assertIsNone(f["per_mtok"])
        self.assertIn("too little data", f["note"])

    def test_weights_split_cached_and_output_tokens(self):
        r = Rollout(self.home, "w", NOW - 10 * H)
        r.event(NOW - 10 * H, "task_started", turn_id="w1", started_at=int(NOW - 10 * H))
        r.call(NOW - 9 * H, 1, 0)
        r.call(NOW - 8 * H, 1_000, 1, cached=10_000, output=100)
        recs = self.read()["recs"]
        self.assertEqual((recs[-1]["uncached"], recs[-1]["cached"], recs[-1]["output"]), (1_000, 10_000, 100))
        self.assertEqual(codex_quota.weighted(1_000, 10_000, 100), 1_000 + 1_000 + 800)

    def test_unexplained_jump_is_usage_from_elsewhere(self):
        # Steady local use at 0.5 %/M, then 10 % appears during a long idle gap with no local tokens.
        def usage(tokens):
            return math.floor(0.5 * tokens / 1e6 + (10 if tokens > 60_000_000 else 0))
        self.steady(k=0.5, turns=6, calls=20, gap_h=2.0, used_from=usage)
        acc = codex_quota.account(self.read())
        self.assertAlmostEqual(acc["outside"]["pct"], 10, delta=1.5)
        self.assertTrue(acc["fit"]["range"][0] <= 0.5 <= acc["fit"]["range"][1], acc["fit"])

    def test_no_outside_usage_when_local_use_explains_it(self):
        self.steady(k=0.5, turns=6, calls=20)
        self.assertEqual(codex_quota.account(self.read())["outside"]["pct"], 0)


if __name__ == "__main__":
    unittest.main()
