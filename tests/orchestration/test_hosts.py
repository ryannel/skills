"""Checks for the third host and for routing across hosts: the Agents table, the Antigravity adapter's parsing, the
quota readers for each host, reset detection, the banked-reset plan, and `route`. Every reading is a synthetic one
in the shape the host returns; no host is run."""

import json
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Clean, agent_loop  # noqa: E402

hq = agent_loop.host_quota
H = 3600.0

TABLE = """# Settings

## Agents
| Role            | Codex              | Claude                 | Antigravity          |
|-----------------|--------------------|------------------------|----------------------|
| Planner         | gpt-6.2-sol high   | claude-opus-5-5 high   | gemini-4-carbon high |
| Builder         | gpt-6.2-sol medium | claude-opus-5-5 medium | gemini-4-neon medium |
| Reviewer        | gpt-6.2-sol medium | -                      | gemini-4-neon        |

## Other
"""


def codex_result(used: float, resets_at: float, credits=()):
    return {"rateLimits": {"primary": {"usedPercent": used, "windowDurationMins": 10080,
                                       "resetsAt": int(resets_at)}, "planType": "promax"},
            "rateLimitResetCredits": {"availableCount": len(credits), "credits": [
                {"id": cid, "resetType": "codexRateLimits", "status": "available", "title": "Full reset",
                 "grantedAt": "2026-11-01T00:00:00Z", "expiresAt": int(exp)} for cid, exp in credits]}}


class QuotaDir(Clean):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        old = hq.STATE_DIR
        hq.STATE_DIR = Path(folder.name)
        self.addCleanup(setattr, hq, "STATE_DIR", old)


class AgentsTable(Clean):
    def test_reads_cells_and_blanks(self):
        problems = []
        t = agent_loop.agents_table(TABLE, set(agent_loop.BUILT_IN_HOSTS), problems)
        self.assertEqual(problems, [])
        self.assertEqual(t["hosts"], ["codex", "claude", "antigravity"])
        self.assertEqual(t["allowed"]["review"], ["codex", "antigravity"])
        self.assertEqual(t["allowed"]["design"], ["codex", "antigravity"], "design falls back to the reviewer row")
        self.assertEqual(t["roles"]["plan"]["hosts"]["antigravity"], {"model": "gemini-4-carbon", "effort": "high"})
        self.assertEqual(t["roles"]["review"]["hosts"]["antigravity"], {"model": "gemini-4-neon", "effort": None})

    def test_bad_cell_and_column(self):
        problems = []
        agent_loop.agents_table(TABLE.replace("| Antigravity ", "| Bard ").replace("gpt-6.2-sol medium |",
                                                                                   "a b medium |", 1),
                                set(agent_loop.BUILT_IN_HOSTS), problems)
        self.assertTrue(any("Bard" in p or "bard" in p for p in problems), problems)
        self.assertTrue(any("Builder on codex" in p for p in problems), problems)

    def test_table_wins_over_lines(self):
        lines = {"build": {"effort": None, "hosts": {"codex": {"model": "gpt-old", "effort": "low"}}}}
        t = agent_loop.agents_table(TABLE, set(agent_loop.BUILT_IN_HOSTS), [])
        merged = agent_loop.merge_roles(lines, t)
        self.assertEqual(merged["build"]["hosts"]["codex"]["model"], "gpt-6.2-sol")

    def test_builders_by_host(self):
        text = "- **Builders:** 2 Codex, one Claude and 1 Antigravity builder\n"
        self.assertEqual(agent_loop.builders_by_host(text, set(agent_loop.BUILT_IN_HOSTS)),
                         {"codex": 2, "claude": 1, "antigravity": 1})
        self.assertEqual(agent_loop.builders_count(text), 4)


class Antigravity(Clean):
    STREAM = "\n".join(json.dumps(x) for x in [
        {"event": "init", "init": {"conversation_id": "c-1", "model": "gemini-4-neon"}},
        {"event": "step_update", "step_update": {"step_type": "agent_response", "text_delta": "Hel", "state": "RUNNING"}},
        {"event": "step_update", "step_update": {"step_type": "agent_response", "text_delta": "lo", "state": "DONE"}},
        {"event": "result", "result": {"conversation_id": "c-1", "status": "SUCCESS", "response": "Hello\nDONE",
                                       "usage": {"input_tokens": 1000, "output_tokens": 50, "thinking_tokens": 25,
                                                 "cache_read_tokens": 400}}}])

    def test_parse(self):
        session, message, model, error = agent_loop.parse_output("antigravity", self.STREAM)
        self.assertEqual((session, model, error), ("c-1", "gemini-4-neon", False))
        self.assertTrue(message.endswith("DONE"))

    def test_error_status(self):
        bad = self.STREAM.replace('"SUCCESS"', '"ERROR"')
        self.assertTrue(agent_loop.parse_output("antigravity", bad)[3])

    def test_usage(self):
        use = agent_loop.usage_of("antigravity", self.STREAM)
        self.assertEqual((use["input"], use["cached"], use["output"]), (600, 400, 75))

    def test_command(self):
        prof = {}
        with tempfile.TemporaryDirectory() as d:
            subprocess_run = __import__("subprocess").run
            subprocess_run(["git", "init", "-q", d], check=True)
            args, env = agent_loop.host_command("antigravity", prof, "gemini-4-neon", "medium", Path(d), "hi",
                                                "c-1")
        self.assertEqual(json.loads(args[args.index("--settings") + 1]), {"agentMode": "auto"})
        self.assertNotIn("--mode", args, "agy's print mode refuses --mode auto before it has signed in")
        self.assertEqual(args[args.index("--conversation") + 1], "c-1")
        self.assertEqual(env["AGY_CLI_DISABLE_AUTO_UPDATE"], "true")
        self.assertNotIn("GEMINI_API_KEY", env)

    def test_denials(self):
        self.assertEqual(len(agent_loop.agy_denials("run_command was soft-denied: needs approval\nok\n")), 1)


class Readers(QuotaDir):
    def test_codex(self):
        now = time.time()
        r = hq.codex_reading(codex_result(76, now + 60 * H, [("a", now + 5 * 24 * H)]), now)
        self.assertEqual(r["windows"][0]["name"], "seven_day")
        self.assertEqual(r["windows"][0]["used_pct"], 76.0)
        self.assertEqual(r["banked"][0]["expires_at"], float(int(now + 5 * 24 * H)))
        self.assertEqual(r["plan"], "promax")

    def test_claude_usage_text(self):
        now = time.mktime((2026, 11, 26, 12, 0, 0, 0, 0, -1))
        text = ("You are currently using your subscription to power your Claude Code usage\n\n"
                "Current week (all models): 27% used · resets Dec 1 at 7pm (Europe/Stockholm)\n"
                "Current week (Fable): 47% used · resets Dec 1 at 7pm (Europe/Stockholm)\n")
        r = hq.claude_usage_reading(text, now)
        names = [w["name"] for w in r["windows"]]
        self.assertEqual(names, ["seven_day", "seven_day:fable"])
        from datetime import datetime
        from zoneinfo import ZoneInfo
        self.assertEqual(r["windows"][0]["resets_at"],
                         datetime(2026, 12, 1, 19, 0, tzinfo=ZoneInfo("Europe/Stockholm")).timestamp())

    def test_claude_event(self):
        event = {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
            "seven_day": {"utilization": 0.31, "resetsAt": int(time.time() + 50 * H)},
            "five_hour": {"utilization": 0.5, "resetsAt": int(time.time() + 2 * H)}}}}
        hq.note_claude_event(event)
        got = {w["name"]: w["used_pct"] for w in hq.latest("claude")["windows"]}
        self.assertEqual(got, {"seven_day": 31.0, "five_hour": 50.0})

    def test_agy_defensive(self):
        payload = {"plan_tier": "ultra", "models": [
            {"model": "gemini-4-neon", "window": "5h", "remaining_fraction": 0.25, "reset_in_seconds": 3600},
            {"model": "gemini-4-carbon", "window": "weekly", "used_percent": 10, "reset_time": "2026-12-01T00:00:00Z"}]}
        r = hq.agy_reading(payload, 1000.0)
        self.assertEqual(r["plan"], "ultra")
        self.assertEqual([w["used_pct"] for w in r["windows"]], [75.0, 10.0])
        self.assertEqual(r["windows"][0]["resets_at"], 4600.0)

    def test_detects_natural_reset_and_redemption(self):
        now = time.time()
        hq.record(hq.codex_reading(codex_result(95, now + 10 * H, [("a", now + 90 * H)]), now - H))
        hq.record(hq.codex_reading(codex_result(2, now + 178 * H, []), now))
        kinds = {e["kind"] for e in hq.resets("codex")}
        self.assertEqual(kinds, {"early", "banked_redeemed"}, "the window moved on before its own reset: a redemption")


class Plans(QuotaDir):
    """Today's Codex account as a fixture: 76% used, the weekly reset 60 h away, banked resets expiring in about 5½
    and 16½ days, all use at 1.11%/h."""

    def plans(self, rate):
        now = time.time()
        reading = hq.codex_reading(codex_result(76, now + 60 * H, [("first", now + 133.5 * H),
                                                                   ("second", now + 397.5 * H)]), now)
        return hq.summary(reading, now, rate_hint=rate)["plans"]

    def test_first_is_behind_at_todays_pace(self):
        first, second = self.plans(1.11)
        self.assertEqual(first["status"], "behind")
        self.assertTrue(first["raise_with_user"], "it expires within a week")
        self.assertAlmostEqual(first["need_pct_per_hour"], 1.33, delta=0.05)
        self.assertGreater(first["window_from"], time.time() + 59 * H, "spends the next window, not this one")
        self.assertEqual(second["status"], "on_track")
        self.assertGreater(second["window_from"], first["window_resets_at"] - 1, "the second never shares its window")

    def test_faster_pace_is_on_track(self):
        first, _ = self.plans(1.5)
        self.assertEqual(first["status"], "on_track")
        self.assertFalse(first["raise_with_user"])

    def test_idle_is_lost(self):
        first, _ = self.plans(0.1)
        self.assertEqual(first["status"], "will_be_lost")

    def test_redeem_now(self):
        now = time.time()
        reading = hq.codex_reading(codex_result(97, now + 120 * H, [("x", now + 30 * H)]), now)
        (p,) = hq.summary(reading, now, rate_hint=1.0)["plans"]
        self.assertEqual(p["status"], "redeem_now")
        self.assertIn("if you agree", p["say"])

    def test_unmeasured(self):
        (p, _) = self.plans(None)
        self.assertEqual(p["status"], "unmeasured")

    def test_never_redeems(self):
        source = "".join((Path(agent_loop.__file__).parent / f).read_text() for f in ("agent_loop.py", "host_quota.py"))
        calls = re.findall(r"""["']account/rateLimitResetCredit/consume["']""", source)
        self.assertEqual(calls, [], "nothing in the script redeems a banked reset")


class Routing(QuotaDir):
    def setUp(self):
        super().setUp()
        self.prof = {"agents_table": agent_loop.agents_table(TABLE, set(agent_loop.BUILT_IN_HOSTS), []),
                     "effort": "medium", "builders_by_host": {}}
        self.prof["roles"] = agent_loop.merge_roles({}, self.prof["agents_table"])
        old = agent_loop.host_installed
        agent_loop.host_installed = lambda host: True
        self.addCleanup(setattr, agent_loop, "host_installed", old)

    def reading(self, host, used, reset_h, banked=()):
        now = time.time()
        hq.record({"host": host, "read_at": now, "windows": [{"name": "seven_day", "label": "weekly",
                                                               "used_pct": used, "resets_at": now + reset_h * H}],
                   "banked": [{"id": b, "status": "available", "expires_at": now + 100 * H, "covers": ["seven_day"]}
                              for b in banked]})

    def test_most_to_lose_wins(self):
        self.reading("codex", 70, 10)
        self.reading("claude", 20, 100)
        self.reading("antigravity", 50, 5)
        got = agent_loop.route(self.prof, "build")
        self.assertEqual(got["host"], "claude")
        self.assertEqual((got["model"], got["effort"]), ("claude-opus-5-5", "medium"))

    def test_floor_closes_a_host(self):
        self.reading("codex", 97, 100)
        self.reading("claude", 99, 100)
        self.reading("antigravity", 90, 100)
        self.assertEqual(agent_loop.route(self.prof, "build")["host"], "antigravity")

    def test_all_out(self):
        for h in agent_loop.BUILT_IN_HOSTS:
            self.reading(h, 99, 100)
        self.assertIsNone(agent_loop.route(self.prof, "build", fallback=None)["host"])
        self.assertTrue(agent_loop.route(self.prof, "build")["all_out"])

    def test_row_limits_hosts(self):
        self.reading("claude", 0, 160)
        self.reading("codex", 50, 100)
        self.reading("antigravity", 50, 100)
        self.assertNotEqual(agent_loop.route(self.prof, "review")["host"], "claude", "no Claude reviewer cell")

    def test_sticks_while_open(self):
        self.reading("codex", 50, 100)
        self.reading("claude", 0, 160)
        self.reading("antigravity", 50, 100)
        got = agent_loop.route(self.prof, "build", stick="codex")
        self.assertEqual(got["host"], "codex")
        self.assertIn("stays on codex", got["why"])

    def test_cap(self):
        self.reading("claude", 0, 160)
        self.reading("codex", 50, 100)
        self.prof["builders_by_host"] = {"claude": 1}
        old = agent_loop.builders_on
        agent_loop.builders_on = lambda worktree: {"claude": 1}
        self.addCleanup(setattr, agent_loop, "builders_on", old)
        self.assertNotEqual(agent_loop.route(self.prof, "build", worktree=Path("."))["host"], "claude")

    def test_agreed_plan_pulls_work(self):
        self.reading("codex", 10, 150, banked=["r1"])
        self.reading("claude", 0, 160)
        self.reading("antigravity", 0, 160)
        old = hq.burn_rate
        hq.burn_rate = lambda *a, **k: 0.2
        self.addCleanup(setattr, hq, "burn_rate", old)
        before = agent_loop.route(self.prof, "build")["host"]
        hq.agree("r1", "codex", "yes, push codex")
        after = agent_loop.route(self.prof, "build")["host"]
        hq.withdraw("r1")
        self.assertNotEqual(before, "codex")
        self.assertEqual(after, "codex")
        self.assertEqual(agent_loop.route(self.prof, "build")["host"], before)

    def test_no_table_no_route(self):
        self.assertIsNone(agent_loop.route({"agents_table": {}}, "build"))


class Catalogue(Clean):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.mine = Path(folder.name) / "models.json"
        old = agent_loop.USER_MODELS
        agent_loop.USER_MODELS = self.mine
        self.addCleanup(setattr, agent_loop, "USER_MODELS", old)

    def test_shipped_catalogue_covers_the_template_table(self):
        cat = agent_loop.catalogue()
        known = {(m["host"], m["id"]) for m in cat["models"]}
        problems = []
        table = agent_loop.agents_table(agent_loop.SETTINGS_TEMPLATE, set(agent_loop.BUILT_IN_HOSTS), problems)
        for entry in table["roles"].values():
            for host, cell in entry["hosts"].items():
                self.assertIn((host, cell["model"]), known)
        self.assertEqual(agent_loop.table_findings({"agents_table": table}, cat), [])

    def test_users_copy_overrides_and_adds(self):
        self.mine.write_text(json.dumps({"checked": "2099-01-01", "models": [
            {"host": "antigravity", "id": "gemini-4-neon", "retires": "2000-01-01"},
            {"host": "codex", "id": "gpt-9", "name": "GPT-9", "efforts": ["high"]}]}))
        cat = agent_loop.catalogue()
        self.assertEqual(cat["checked"], "2099-01-01")
        by = {(m["host"], m["id"]): m for m in cat["models"]}
        self.assertEqual(by[("antigravity", "gemini-4-neon")]["retires"], "2000-01-01")
        self.assertEqual(by[("antigravity", "gemini-4-neon")]["name"], "Gemini 4 Neon", "the rest of the entry stays")
        self.assertEqual(by[("codex", "gpt-9")]["from"], "yours")
        table = agent_loop.agents_table(TABLE.replace("gpt-6.2-sol medium", "gpt-9 low"),
                                        set(agent_loop.BUILT_IN_HOSTS), [])
        found = agent_loop.table_findings({"agents_table": table}, cat)
        self.assertTrue(any("gemini-4-neon was retired" in f for f in found), found)
        self.assertTrue(any("gpt-9 doesn't take effort low" in f for f in found), found)

    def test_unknown_model_and_price_change(self):
        table = agent_loop.agents_table(TABLE.replace("gpt-6.2-sol high", "gpt-6.9 high"),
                                        set(agent_loop.BUILT_IN_HOSTS), [])
        found = agent_loop.table_findings({"agents_table": table}, agent_loop.catalogue())
        self.assertEqual(found, ["Planner on codex: gpt-6.9 isn't in the catalogue; check the ID (the models skill "
                                 "can add it)"])
        carbon = {"price": {"input": 2.0, "output": 10.0}, "price_changes": [{"from": "2026-12-01", "input": 4.0}]}
        self.assertEqual(agent_loop.price_now(carbon, "2026-11-30")["input"], 2.0)
        self.assertEqual(agent_loop.price_now(carbon, "2026-12-01"), {"input": 4.0, "output": 10.0})


class AgentsCell(Clean):
    def test_sets_one_cell(self):
        out = agent_loop.set_agents_cell(TABLE, "Reviewer", "Claude", "claude-sonnet-5-5 medium")
        t = agent_loop.agents_table(out, set(agent_loop.BUILT_IN_HOSTS), [])
        self.assertEqual(t["roles"]["review"]["hosts"]["claude"], {"model": "claude-sonnet-5-5", "effort": "medium"})
        self.assertEqual(t["roles"]["build"], agent_loop.agents_table(TABLE, set(agent_loop.BUILT_IN_HOSTS),
                                                                      [])["roles"]["build"])
        off = agent_loop.set_agents_cell(out, "Builder", "antigravity", "-")
        t = agent_loop.agents_table(off, set(agent_loop.BUILT_IN_HOSTS), [])
        self.assertEqual(t["allowed"]["build"], ["codex", "claude"])


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class AntigravityLive(Clean):
    """Against output saved from agy 1.5.18 on 2026-11-26: a `/usage` reading and a one-word turn."""

    def test_usage_groups_bind_only_their_models(self):
        r = hq.agy_reading(json.loads((FIXTURES / "agy_usage.json").read_text()), now=1795675485.0)
        self.assertEqual([w["name"] for w in r["windows"]], ["seven_day:gemini", "five_hour:gemini",
                                                              "seven_day:claude-and-gpt", "five_hour:claude-and-gpt"])
        self.assertIsNone(r["windows"][2]["resets_at"], "a bucket never used resets at the epoch, kept as no time")
        self.assertEqual([w["name"] for w in hq.binding_windows(r, "gemini-4-neon")],
                         ["seven_day:gemini", "five_hour:gemini"])
        self.assertEqual([w["name"] for w in hq.binding_windows(r, "claude-opus-5-5")],
                         ["seven_day:claude-and-gpt", "five_hour:claude-and-gpt"])
        full = {**r, "windows": [{**w, "used_pct": 98.0} if w["name"].endswith("claude-and-gpt") else w
                                 for w in r["windows"]]}
        view = {**full, "windows": [hq.window_view("antigravity", w, 1795675485.0, 0.0) for w in full["windows"]]}
        self.assertTrue(hq.loss_score(view, "gemini-4-neon")[2], "the Claude group running out doesn't close Gemini")
        self.assertFalse(hq.loss_score(view, "claude-opus-5-5")[2])
        self.assertEqual(r["windows"][0]["label"], "Gemini Models weekly")

    def test_five_hour_window_closes_but_does_not_rank(self):
        now = 1795675485.0
        r = hq.agy_reading(json.loads((FIXTURES / "agy_usage.json").read_text()), now=now)
        view = {**r, "windows": [hq.window_view("antigravity", w, now, None) for w in r["windows"]]}
        lost, why, open_ = hq.loss_score(view, "gemini-4-neon")
        self.assertTrue(open_)
        self.assertIn("weekly", why, "the weekly window is what would be lost, not the 5-hour throttle")
        spent = {**view, "windows": [{**w, "used_pct": 97.0, "left_pct": 3.0} if w["name"] == "five_hour:gemini" else w
                                     for w in view["windows"]]}
        self.assertFalse(hq.loss_score(spent, "gemini-4-neon")[2], "a spent 5-hour window still closes the host")

    def test_turn_parses(self):
        out = (FIXTURES / "agy_turn.jsonl").read_text()
        session, text, model, _ = agent_loop.parse_output("antigravity", out)
        self.assertEqual((session, text.strip(), model), ("9e9d32cf-4cd1-48d8-af05-beacdd982adc", "PONG", "gemini-4-neon"))
        self.assertEqual(agent_loop.usage_of("antigravity", out)["output"], 49, "thinking counts as output")


if __name__ == "__main__":
    unittest.main()
