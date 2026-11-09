"""Checks for agent_loop's mechanical decisions: milestone choice, escalation, claims, profile, pins, locks and
report lines."""

import argparse
import contextlib
import io
import json
import os
import sqlite3
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills/orchestration/build/scripts"))
import agent_loop  # noqa: E402


def done(*milestones):
    return {"module": "WATER", "milestones": list(milestones)}


def item(iid, status="open", **proof):
    proof = proof or {"check": "true"}
    return {"id": iid, "statement": f"{iid} works", **proof, "status": status, "evidence": ""}


def milestone(mid, state, statuses, fails=0, **proof):
    items = [item(f"{mid}.{i}", s, **proof) for i, s in enumerate(statuses, 1)]
    return {"id": mid, "name": mid, "state": state, "fails": fails, "replans": 0, "items": items}


class Decisions(unittest.TestCase):
    def test_picks_in_progress_before_open(self):
        d = done(milestone("M1", "done", ["pass"]), milestone("M2", "open", ["open"]),
                 milestone("M3", "in_progress", ["open"]))
        self.assertEqual(agent_loop.pick_milestone(d, None)["id"], "M3")

    def test_named_milestone_must_exist(self):
        with self.assertRaises(SystemExit):
            agent_loop.pick_milestone(done(milestone("M1", "open", ["open"])), "M9")

    def test_escalation_ladder(self):
        self.assertEqual([agent_loop.escalation(n) for n in range(6)],
                         ["none", "same-session", "same-session", "fresh-session", "replan", "replan"])
        self.assertEqual(agent_loop.escalation(4, replans=1), "park")
        self.assertEqual(agent_loop.escalation(2, replans=1), "same-session")

    def test_forecast_from_last_day(self):
        h, now, reset = 3600, 1_000_000.0, 1_000_000.0 + 72 * 3600
        samples = [(now - 24 * h, 40.0, reset), (now - 12 * h, 45.0, reset), (now, 50.0, reset)]
        f = agent_loop.forecast(samples, now)
        self.assertEqual(f["per_day"], 10.0)
        self.assertIsNone(f["runs_out"])  # 50% left, 30% used by the reset
        fast = [(now - 24 * h, 20.0, reset), (now, 50.0, reset)]
        self.assertIsNotNone(agent_loop.forecast(fast, now)["runs_out"])  # 30%/day, 50% left, 72 h to reset
        old_window = [(now - 20 * h, 90.0, now - 10 * h), (now - 2 * h, 1.0, reset), (now, 2.0, reset)]
        self.assertEqual(agent_loop.forecast(old_window, now)["per_day"], 12.0)

    def test_report_word_reads_only_the_last_line(self):
        self.assertEqual(agent_loop.report_word("work\nevidence\nBLOCKED: no Metal device"), "BLOCKED")
        self.assertEqual(agent_loop.report_word("`DONE`"), "DONE")
        self.assertIsNone(agent_loop.report_word("DONE\nActually the milestone is not complete yet."))
        self.assertIsNone(agent_loop.report_word("still working"))

    def test_profile_reads_labelled_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                "- **Plans:** [docs/design/modules](docs/design/modules/)  *(read by the loop)*\n"
                "- **Evidence:** docs/my evidence  *(loop)*\n"
                "- **Check:** `npm run check`  *(loop)*\n"
                "- **Branch:** trunk  *(loop: integrate here)*\n"
                "- **Codex sandbox:** danger-full-access  *(loop)*\n"
                "- **Codex generator:** gpt-6.1-sol, high\n- **Writable roots:** ~/.cargo, ~/.npm\n")
            p = agent_loop.profile(Path(tmp), strict=True)
            self.assertEqual((p["plans"], p["branch"], p["model"], p["effort"], p["evidence"], p["check"], p["sandbox"]),
                             ("docs/design/modules", "trunk", "gpt-6.1-sol", "high", "docs/my evidence",
                              "npm run check", "danger-full-access"))
            self.assertEqual(p["roots"], ["~/.cargo", "~/.npm"])
            self.assertEqual(p["graded_examples"], "docs/my evidence/graded-examples.md")
            self.assertEqual(agent_loop.profile(Path(tmp, "missing"))["plans"], "docs/modules")

    def test_profile_strict_rejects_missing_unfilled_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                agent_loop.profile(Path(tmp), strict=True)  # no ORCHESTRATE.md at all
            for bad in ("- **Evidence:** <where review files go>\n", "- **Codex sandbox:** open\n",
                        "- **Codex generator:** gpt-6.1-sol turbo\n", "- **Integrate:** pull-request\n"):
                Path(tmp, "ORCHESTRATE.md").write_text(bad)
                with self.assertRaises(SystemExit, msg=bad):
                    agent_loop.profile(Path(tmp), strict=True)

    def test_pin_mismatch_lists_wrong_turns_and_skips_partial_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            rollout = Path(tmp) / "rollout.jsonl"
            lines = [
                json.dumps({"type": "turn_context", "payload": {"turn_id": "a", "model": "gpt-6.1-sol", "effort": "medium"}}),
                json.dumps({"type": "turn_context", "payload": {"turn_id": "b", "model": "gpt-6.1-sol", "effort": "xhigh"}}),
                '{"type": "turn_context", "payload": {"turn_id": "c", "mod',
            ]
            rollout.write_text("\n".join(lines))
            self.assertEqual(agent_loop.pin_mismatches(rollout), ["b: gpt-6.1-sol/xhigh"])

    def test_checks_alone_close_a_middle_milestone_but_not_the_last(self):
        d = done(milestone("M1", "open", ["pass"]), milestone("M2", "open", ["open"]))
        self.assertEqual(agent_loop.pick_milestone(d, None)["id"], "M2")
        self.assertFalse(agent_loop.needs_review(d["milestones"][0], d))
        self.assertTrue(agent_loop.needs_review(d["milestones"][1], d))
        reviewed = milestone("M1", "open", ["pass"], inspect="frame sequence of the wake")
        self.assertEqual(agent_loop.pick_milestone(done(reviewed, milestone("M2", "open", ["open"])), None)["id"], "M1")

    def test_validate_rejects_items_with_no_proof_and_empty_milestones(self):
        bare = milestone("M1", "open", ["open"])
        del bare["items"][0]["check"]
        self.assertTrue(any("nothing proves it" in p for p in agent_loop.validate(done(bare))))
        self.assertTrue(any("no items" in p for p in agent_loop.validate(done(milestone("M1", "open", [])))))
        dup = done(milestone("M1", "open", ["open"]), milestone("M1", "open", ["open"]))
        self.assertTrue(any("duplicate" in p for p in agent_loop.validate(dup)))
        self.assertEqual(agent_loop.validate(done(milestone("M1", "open", ["open"]))), [])

    def test_builder_marked_done_on_a_reviewed_milestone_is_still_owed_review(self):
        m = milestone("M1", "done", ["pass"], inspect="captures")
        d = done(m, milestone("M2", "open", ["open"]))
        self.assertTrue(agent_loop.awaiting_review(m, d))
        for i in m["items"]:
            i["verdict"] = "pass"
        self.assertFalse(agent_loop.awaiting_review(m, d))

    def test_definitions_ignore_claims_but_not_checks(self):
        m = milestone("M1", "open", ["open"])
        before = agent_loop.definitions(m)
        m["items"][0].update(status="pass", evidence="log", verdict="pass")
        self.assertEqual(agent_loop.definitions(m), before)
        m["items"][0]["check"] = "true # weakened"
        self.assertNotEqual(agent_loop.definitions(m), before)


FAKE_CODEX = """#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
if "--help" in sys.argv:
    print("usage: codex exec [--json]")
    sys.exit(0)
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
wt = os.environ["FAKE_WT"]
path = Path(wt) / "docs/modules/WATER-DONE.json"
if os.environ.get("FAKE_PASS") == "1":
    d = json.loads(path.read_text())
    for m in d["milestones"]:
        if m["state"] in ("open", "in_progress"):
            m["state"] = os.environ.get("FAKE_STATE", "claimed")
            for i in m["items"]:
                i["status"] = "pass"
                i["evidence"] = "run log"
                if os.environ.get("FAKE_WEAKEN") == "1":
                    i["check"] = "true"
            break
    path.write_text(json.dumps(d))
    if os.environ.get("FAKE_COMMIT", "1") == "1":
        subprocess.run(["git", "-C", wt, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "pass"])
        subprocess.run(["git", "-C", wt, "push", "-q", "origin", "main"])
print(json.dumps({"type": "thread.started", "thread_id": "t1"}))
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": os.environ.get("FAKE_REPLY", "DONE")}}))
"""


FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
log = os.environ.get("FAKE_LOG") or open(os.environ["FAKE_LOG_FILE_HINT"]).read()
with open(sys.argv[0] + ".log", "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
                        "api_key": "ANTHROPIC_API_KEY" in os.environ}) + "\\n")
wt = os.getcwd()
path = Path(wt) / "docs/modules/WATER-DONE.json"
d = json.loads(path.read_text())
for m in d["milestones"]:
    if m["state"] in ("open", "in_progress"):
        m["state"] = "claimed"
        for i in m["items"]:
            i["status"], i["evidence"] = "pass", "run log"
        break
path.write_text(json.dumps(d))
subprocess.run(["git", "-C", wt, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "pass"])
subprocess.run(["git", "-C", wt, "push", "-q", "origin", "main"])
model = sys.argv[sys.argv.index("--model") + 1]
print(json.dumps({"type": "system", "subtype": "init", "session_id": "s1", "model": model}))
print(json.dumps({"type": "result", "subtype": "success", "session_id": "s1", "result": "DONE", "is_error": False}))
"""


class Needs(unittest.TestCase):
    def test_unmet_needs_hold_a_milestone_back(self):
        core = done(milestone("M1", "done", ["pass"]), milestone("M2", "open", ["open"]))
        water = done(dict(milestone("M1", "open", ["open"]), needs=["CORE:M2"]), milestone("M2", "open", ["open"]))
        with self.assertRaises(SystemExit) as e:
            agent_loop.pick_milestone(water, None, "WATER", {"CORE": core, "WATER": water})
        self.assertEqual(e.exception.waiting, [{"milestone": "M1", "needs": ["CORE:M2"]}])
        core["milestones"][1]["state"] = "done"
        self.assertEqual(agent_loop.pick_milestone(water, None, "WATER", {"CORE": core})["id"], "M1")
        self.assertEqual(agent_loop.pick_milestone(water, None, "WATER", {"CORE": core})["id"], "M1")

    def test_needs_are_validated_and_pinned(self):
        bad = done(dict(milestone("M1", "open", ["open"]), needs="CORE:M2"))
        self.assertTrue(any("needs" in p for p in agent_loop.validate(bad)))
        a = milestone("M1", "open", ["open"])
        b = dict(a, needs=["CORE:M1"])
        self.assertNotEqual(agent_loop.definitions(a), agent_loop.definitions(b))
        self.assertEqual(agent_loop.unmet(b, "WATER", {}), ["CORE:M1 (not planned)"])

    def test_profile_reads_hosts_models_and_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                "- **Claude model:** claude-opus-5-5\n- **Effort:** high\n"
                "- **Host gemini:** `gemini -p {prompt} -m {model}`\n- **Host bad:** gemini\n")
            with contextlib.redirect_stderr(io.StringIO()):
                p = agent_loop.profile(Path(tmp))
            self.assertEqual((p["models"]["codex"], p["models"]["claude"], p["effort"]),
                             ("gpt-6.1-sol", "claude-opus-5-5", "high"))
            self.assertEqual(p["hosts"], {"gemini": "gemini -p {prompt} -m {model}"})
            args, env = agent_loop.host_command("gemini", p, "g-2", "medium", Path(tmp), "do it now", None)
            self.assertEqual(args, ["gemini", "-p", "do it now", "-m", "g-2"])

    def test_claude_environment_drops_keys_but_keeps_config_dir(self):
        os.environ.update(ANTHROPIC_API_KEY="x", CLAUDE_CONFIG_DIR="/c", CLAUDECODE="1")
        try:
            env = agent_loop.clean_env()
        finally:
            for k in ("ANTHROPIC_API_KEY", "CLAUDE_CONFIG_DIR", "CLAUDECODE"):
                os.environ.pop(k, None)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], "/c")

    def test_claude_stream_parsing(self):
        out = "\n".join(json.dumps(e) for e in [
            {"type": "system", "subtype": "init", "session_id": "s9", "model": "claude-opus-5-5"},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "working"}]}},
            {"type": "result", "result": "BLOCKED: no device", "is_error": False}])
        self.assertEqual(agent_loop.parse_output("claude", out), ("s9", "BLOCKED: no device", "claude-opus-5-5", False))


class RunLoop(unittest.TestCase):
    """Drives cmd_run against a fake codex and a throwaway repo with an origin."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.wt, self.origin, self.home = root / "wt", root / "origin.git", root / "codex-home"
        self.home.mkdir()
        git = lambda *a, cwd=None: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)
        git("init", "--bare", "-b", "main", str(self.origin))
        git("init", "-b", "main", str(self.wt))
        (self.wt / "docs/modules").mkdir(parents=True)
        (self.wt / "ORCHESTRATE.md").write_text("- **Plans:** docs/modules\n")
        self.write_done([milestone("M1", "open", ["open"]), milestone("M2", "open", ["open"])])
        git("add", "-A", cwd=self.wt)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "init", cwd=self.wt)
        git("remote", "add", "origin", str(self.origin), cwd=self.wt)
        git("push", "-q", "origin", "main", cwd=self.wt)
        fake = root / "codex"
        fake.write_text(FAKE_CODEX)
        fake.chmod(0o755)
        self.log = root / "log"
        self.saved = (agent_loop.CODEX, agent_loop.CODEX_HOME)
        agent_loop.CODEX, agent_loop.CODEX_HOME = str(fake), self.home
        for key in ("FAKE_STATE", "FAKE_WEAKEN"):
            os.environ.pop(key, None)
        os.environ.update(FAKE_LOG=str(self.log), FAKE_WT=str(self.wt), FAKE_PASS="1", FAKE_REPLY="DONE",
                          FAKE_COMMIT="1")

    def tearDown(self):
        agent_loop.CODEX, agent_loop.CODEX_HOME = self.saved
        self.tmp.cleanup()

    def write_done(self, milestones):
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(done(*milestones)))

    def read_done(self):
        return json.loads((self.wt / "docs/modules/WATER-DONE.json").read_text())

    def commit_all(self):
        subprocess.run(["git", "-C", str(self.wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "x"],
                       check=True)
        subprocess.run(["git", "-C", str(self.wt), "push", "-q", "origin", "main"], check=True)

    def run_loop(self, **kw):
        args = dict(module="WATER", worktree=str(self.wt), milestone=None, fresh=False, message=None,
                    budget_hours=4.0, turn_timeout_hours=0.1, host=None, model=None, effort=None)
        args.update(kw)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            agent_loop.cmd_run(argparse.Namespace(**args))
        return json.loads(out.getvalue().splitlines()[-1])

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def test_claims_with_the_commit_when_everything_holds(self):
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("CLAIMED", False))
        self.assertEqual(result["commit"], agent_loop.head_commit(self.wt))
        self.assertIn("quota", result)

    def test_rerun_after_failed_review_resumes_in_the_worktree_with_message(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frame sequence of the wake")])
        self.commit_all()
        self.assertEqual(self.run_loop()["review"], True)
        d = self.read_done()
        d["milestones"][0].update(state="in_progress", fails=1)
        d["milestones"][0]["items"][0]["verdict"] = "fail"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(d))
        self.commit_all()
        self.run_loop(milestone="M1", message="FINDINGS")
        last = self.calls()[-1]
        argv = last["argv"]
        self.assertEqual(argv[argv.index("resume") + 1], "t1")
        self.assertIn("-C", argv[:argv.index("resume")])
        self.assertIn("--add-dir", argv[:argv.index("resume")])
        self.assertEqual(argv[-1], "FINDINGS")
        self.assertEqual(Path(last["cwd"]).resolve(), self.wt.resolve())

    def test_a_changed_pin_starts_a_fresh_session(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: x")
        self.run_loop()
        (self.wt / "ORCHESTRATE.md").write_text("- **Plans:** docs/modules\n- **Codex generator:** gpt-6.1-sol high\n")
        self.commit_all()
        self.run_loop()
        self.assertNotIn("resume", self.calls()[-1]["argv"])

    def test_weakened_checks_are_rejected(self):
        os.environ.update(FAKE_WEAKEN="1")
        self.write_done([milestone("M1", "open", ["open"], check="exit 0 && test -f real-proof")])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual(result["result"], "INVALID")
        self.assertIn("definitions", result["problems"][0])

    def test_invalid_file_stops_before_any_turn(self):
        bare = milestone("M1", "open", ["open"])
        del bare["items"][0]["check"]
        self.write_done([bare])
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "INVALID")
        self.assertFalse(self.log.exists())

    def test_uncommitted_pass_is_not_claimed(self):
        os.environ.update(FAKE_COMMIT="0")
        state = self.run_loop(budget_hours=0.0)
        self.assertEqual(state["result"], "BUDGET")
        saved = json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
        self.assertIn("uncommitted", saved["claim_blocked"])

    def test_untracked_files_block_the_claim(self):
        (self.wt / "helper.sh").write_text("echo hi\n")
        self.run_loop(budget_hours=0.0)
        saved = json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
        self.assertIn("untracked", saved["claim_blocked"])

    def test_failed_fetch_blocks_the_claim(self):
        subprocess.run(["git", "-C", str(self.wt), "remote", "set-url", "origin", str(self.wt.parent / "gone.git")],
                       check=True)
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working")
        d = self.read_done()
        d["milestones"][0]["state"] = "claimed"
        for i in d["milestones"][0]["items"]:
            i.update(status="pass", evidence="log")
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(d))
        subprocess.run(["git", "-C", str(self.wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "x"],
                       check=True)
        self.run_loop(milestone="M1", budget_hours=0.0)
        saved = json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
        self.assertIn("fetch", saved["claim_blocked"])

    def test_failing_item_check_goes_back_to_generator(self):
        self.write_done([milestone("M1", "open", ["open"], check="exit 3"), milestone("M2", "open", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "BUDGET")
        saved = json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
        self.assertIn("M1.1 `exit 3` exited 3", saved["claim_blocked"])

    def test_failing_profile_check_blocks_the_claim(self):
        (self.wt / "ORCHESTRATE.md").write_text("- **Plans:** docs/modules\n- **Check:** `sh -c 'exit 4'`\n")
        self.commit_all()
        self.run_loop(budget_hours=0.0)
        saved = json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
        self.assertIn("Check `sh -c 'exit 4'` exited 4", saved["claim_blocked"])

    def test_done_without_a_claim_never_finishes_as_done(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "UNCLAIMED")
        self.assertIn("items not yet pass", result["reasons"][0])
        self.assertEqual(len(self.calls()), 3)

    def test_builder_done_on_reviewed_milestone_is_not_a_claim(self):
        os.environ.update(FAKE_STATE="done")
        self.write_done([milestone("M1", "open", ["open"], inspect="captures"), milestone("M2", "open", ["open"])])
        self.commit_all()
        self.run_loop(budget_hours=0.0)
        saved = json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
        self.assertIn("set its state to claimed", saved["claim_blocked"])

    def test_claimed_milestone_blocks_the_next_until_reviewed(self):
        self.write_done([milestone("M1", "claimed", ["pass"], inspect="captures"), milestone("M2", "open", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["milestone"]), ("REVIEW_OWED", "M1"))

    def test_second_blocked_report_with_an_active_goal_finishes(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        self.assertEqual(len(self.calls()), 2)

    def test_paused_goal_stops_before_dispatching_another_turn(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'paused')")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        self.assertEqual(len(self.calls()), 1)

    def test_quota_reads_only_the_weekly_codex_limit_and_survives_bad_lines(self):
        sessions = self.home / "sessions"
        sessions.mkdir()
        def line(ts, limit_id, used, window):
            return json.dumps({"timestamp": ts, "type": "event_msg", "payload": {"type": "token_count", "rate_limits": {
                "limit_id": limit_id, "primary": {"used_percent": used, "window_minutes": window,
                                                  "resets_at": 4_000_000_000}}}})
        (sessions / "rollout-x.jsonl").write_text("\n".join([
            line("2026-11-08T10:00:00Z", "codex", 47.0, 10080), line("2026-11-08T11:00:00Z", "premium", 0.0, 0),
            '{"type": "event_msg", "payload": {"type": "token_count", "rate']))
        self.assertEqual(agent_loop.quota_samples(0), [(1794132000.0, 47.0, 4e9)])

    def test_lock_takes_worktree_after_the_name_and_runs_there(self):
        marker = self.wt.parent / "where"
        with self.assertRaises(SystemExit) as exit_:
            agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=None, command_args=[
                "--worktree", str(self.wt), "--", "sh", "-c", f"pwd > {marker}"]))
        self.assertEqual(exit_.exception.code, 0)
        self.assertEqual(Path(marker.read_text().strip()).resolve(), self.wt.resolve())

    def test_claude_builder_claims_with_a_clean_environment(self):
        fake = Path(self.tmp.name) / "claude"
        fake.write_text(FAKE_CLAUDE.replace('log = os.environ.get("FAKE_LOG") or open(os.environ["FAKE_LOG_FILE_HINT"]).read()\n', ""))
        fake.chmod(0o755)
        saved = agent_loop.CLAUDE
        agent_loop.CLAUDE = str(fake)
        os.environ["ANTHROPIC_API_KEY"] = "secret"
        try:
            result = self.run_loop(host="claude")
        finally:
            agent_loop.CLAUDE = saved
            os.environ.pop("ANTHROPIC_API_KEY", None)
        self.assertEqual(result["result"], "CLAIMED")
        call = json.loads(Path(str(fake) + ".log").read_text().splitlines()[0])
        self.assertFalse(call["api_key"])
        self.assertIn("--effort", call["argv"])
        self.assertEqual(call["argv"][call["argv"].index("--model") + 1], "claude-opus-5-5")

    def test_waiting_when_needs_are_unmet(self):
        self.write_done([dict(milestone("M1", "open", ["open"]), needs=["CORE:M1"])])
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "WAITING")

    def test_ready_lists_ready_waiting_and_finished(self):
        (self.wt / "docs/modules/CORE-DONE.json").write_text(json.dumps(
            {"module": "CORE", "milestones": [milestone("M1", "done", ["pass"])]}).replace('"evidence": ""', '"evidence": "x", "verdict": "pass"'))
        self.write_done([dict(milestone("M1", "open", ["open"]), needs=["CORE:M1"]),
                         dict(milestone("M2", "open", ["open"]), needs=["CORE:M9"])])
        subprocess.run(["git", "-C", str(self.wt), "add", "-A"], check=True)
        self.commit_all()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_ready(argparse.Namespace(worktree=str(self.wt)))
        r = json.loads(out.getvalue())
        self.assertEqual(r["ready"], [{"module": "WATER", "milestone": "M1", "state": "open"}])
        self.assertEqual(r["finished"], [{"module": "CORE", "parked": []}])

    def test_reviewer_overreach_flags_builder_fields_and_other_files(self):
        before = agent_loop.head_commit(self.wt)
        d = self.read_done()
        d["milestones"][0]["items"][0].update(verdict="fail", status="pass")
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(d))
        (self.wt / "src.txt").write_text("fix")
        subprocess.run(["git", "-C", str(self.wt), "add", "-A"], check=True)
        self.commit_all()
        problems = agent_loop.reviewer_overreach(self.wt, agent_loop.profile(self.wt), "WATER", before,
                                                 agent_loop.head_commit(self.wt))
        self.assertTrue(any("src.txt" in p for p in problems))
        self.assertTrue(any("status or evidence" in p for p in problems))

    def test_lock_refuses_outside_a_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=tmp, command_args=["--", "true"]))


if __name__ == "__main__":
    unittest.main()
