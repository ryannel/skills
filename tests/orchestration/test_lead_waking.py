"""Checks that the lead is woken for judgement and not to pass commands along: `run` and `plan` carry on through the
routine steps and stop at anything else, and `watch` wakes the lead at its check-in or at a warning sign, once for
each sign."""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import (PARSER, Clean, Repo, agent_loop, check_next_commands, milestone, release)  # noqa: E402

WT = "/repo/wt"


def run_cmd(*args):
    return agent_loop.loop_cmd(*args)


def result(word, command=None, by="lead", **fields):
    """A step's result line, with `next` as the script writes it."""
    then = {k: fields.pop(k) for k in ("decides", "ask") if k in fields}
    line = {"result": word, **fields}
    line["next"] = agent_loop.fit_next(agent_loop.next_cmd(command, by, "the reason", **then))
    return line


def steps(origin="run"):
    return {"origin": origin, "worktree": WT, "owed": [], "changes": {},
            "last_run": ["run", "--module", "WATER", "--worktree", WT, "--one-step"]}


class RoutineSteps(Clean):
    """Which results carry on to another step, and which end the command so the lead can judge them."""

    def follows(self, line, state=None):
        words, why = agent_loop.routine_next(line, state if state is not None else steps())
        return words, why

    def test_ready_for_review_goes_on_to_its_review_and_a_milestone_done_on_its_checks_to_the_next(self):
        words, _ = self.follows(result("READY_FOR_REVIEW", run_cmd("review", "--module", "WATER", "--milestone", "M1",
                                                                     "--commit", "abc", "--worktree", WT),
                                       module="WATER", milestone="M1", review=True))
        self.assertEqual(words[:5], ["review", "--module", "WATER", "--milestone", "M1"])
        words, _ = self.follows(result("READY_FOR_REVIEW", run_cmd("run", "--module", "WATER", "--worktree", WT),
                                       module="WATER", milestone="M1", review=False))
        self.assertEqual(words[0], "run")

    def test_a_pass_goes_on_to_the_modules_next_milestone_and_stops_when_the_module_is_finished(self):
        words, _ = self.follows(result("REVIEWED", run_cmd("run", "--module", "WATER", "--worktree", WT),
                                       module="WATER", milestone="M1", verdict="PASS"))
        self.assertEqual(words[0], "run")
        words, why = self.follows(result("REVIEWED", None, module="WATER", milestone="M2", verdict="PASS"))
        self.assertIsNone(words)
        self.assertIn("the reason", why)
        # the next milestone waits on another module: that is the lead's to arrange
        words, why = self.follows(result("REVIEWED", run_cmd("run", "--module", "PAY", "--worktree", WT),
                                         module="WATER", milestone="M1", verdict="PASS"))
        self.assertIsNone(words)
        self.assertIn("can't start here", why)

    def test_a_failed_review_goes_back_to_the_builder_until_the_counts_call_for_more(self):
        for word in ("same_builder", "new_builder_session"):
            line = result("REVIEWED", run_cmd("run", "--module", "WATER", "--worktree", WT, "--message", "read it"),
                          module="WATER", milestone="M1", verdict="FAIL", escalation=word)
            self.assertEqual(self.follows(line)[0][0], "run", word)
        diagnosis = result("REVIEWED", run_cmd("plan", "--worktree", WT, "--task", "find out why"), by="planner",
                           module="WATER", milestone="M1", verdict="FAIL", escalation="diagnosis")
        self.assertIsNone(self.follows(diagnosis)[0])
        human = result("REVIEWED", run_cmd("human", "reopen", "--module", "WATER", "--milestone", "M1", "--worktree",
                                           WT, "--text", "x"), module="WATER", milestone="M1", verdict="FAIL",
                       escalation="too_many_failed_reviews", decides="human", ask="Reopen it?")
        words, why = self.follows(human)
        self.assertIsNone(words)
        self.assertIn("human's", why)

    def test_results_that_need_judgement_stop_the_steps(self):
        again = run_cmd("run", "--module", "WATER", "--worktree", WT)
        for word in ("BLOCKED", "NEEDS_CONTEXT", "HOST_FAILED", "PAUSED", "KEPT", "WAITING", "FINISHED", "INVALID",
                     "CHECKS_FAILED", "NO_PROGRESS_FOR_HOURS", "STALLED", "REFUSED", "SCRIPT_FAILED",
                     "IN_PROGRESS_ELSEWHERE", "WRONG_MODEL_OR_EFFORT"):
            words, why = self.follows(result(word, again, module="WATER", milestone="M1"))
            self.assertIsNone(words, word)
            self.assertIn(word, why)
        # a next that isn't a plain command of this script: a visible run, an ask, the main branch broken
        visible = result("READY_FOR_REVIEW", "ORCHESTRATE_VISIBLE=1 " + again, module="WATER", milestone="M1")
        self.assertIsNone(self.follows(visible)[0])
        asked = result("READY_FOR_REVIEW", again, module="WATER", milestone="M1", ask="Are you there?")
        self.assertIsNone(self.follows(asked)[0])
        broken = result("READY_FOR_REVIEW", again, module="WATER", milestone="M1", main_broken="e2e fails on abc")
        words, why = self.follows(broken)
        self.assertIsNone(words)
        self.assertIn("main branch is broken", why)

    def test_a_run_whose_design_review_asks_for_changes_gets_one_revision_then_runs_again(self):
        state = steps("run")
        revise = run_cmd("plan", "--worktree", WT, "--task", "resolve the findings")
        changes = result("DESIGN_NOT_APPROVED", revise, by="planner", module="WATER",
                         design_review={"verdict": "DESIGN CHANGES"})
        words, _ = self.follows(changes, state)
        self.assertEqual(words[0], "plan")
        words, _ = self.follows(result("PLANNED", run_cmd("ready", "--worktree", WT), merged=True,
                                       design_review_owed=["WATER"]), state)
        self.assertEqual(words, state["last_run"])
        words, why = self.follows(changes, state)
        self.assertIsNone(words)
        self.assertIn("second time", why)

    def test_a_plan_goes_on_to_each_design_review_it_left_owed(self):
        state = steps("plan")
        planned = result("PLANNED", run_cmd("review", "--module", "WATER", "--milestone", "design", "--worktree", WT),
                         merged=True, design_review_owed=["WATER", "PAY"], modules=["WATER", "PAY"])
        words, _ = self.follows(planned, state)
        self.assertEqual(words[:3], ["review", "--module", "WATER"])
        ok = result("REVIEWED", run_cmd("run", "--module", "WATER", "--worktree", WT), module="WATER",
                    milestone="design", verdict="DESIGN OK")
        words, _ = self.follows(ok, state)
        self.assertEqual(words[:5], ["review", "--module", "PAY", "--milestone", "design"])
        changes = result("REVIEWED", run_cmd("plan", "--worktree", WT, "--task", "resolve them"), by="planner",
                         module="PAY", milestone="design", verdict="DESIGN CHANGES")
        self.assertEqual(self.follows(changes, state)[0][0], "plan")
        self.assertIsNone(self.follows(changes, state)[0])  # the second DESIGN CHANGES is the lead's to look at
        words, why = self.follows(dict(ok, module="PAY"), state)
        self.assertIsNone(words)
        self.assertIn("design is approved", why)
        unmerged = result("PLANNED", None, merged=False, problems=["couldn't merge"])
        self.assertIsNone(self.follows(unmerged, steps("plan"))[0])

    def test_later_steps_keep_what_the_lead_gave_the_first(self):
        a = PARSER.parse_args(["run", "--module", "WATER", "--worktree", WT, "--model", "m", "--effort", "high",
                               "--turn-timeout-hours", "3"])
        words = agent_loop.carried(["run", "--module", "WATER", "--worktree", WT, "--fresh"], a, "run")
        self.assertEqual(words[words.index("--model") + 1], "m")
        self.assertEqual(float(words[words.index("--turn-timeout-hours") + 1]), 3.0)
        self.assertIn("--one-step", words)
        review = agent_loop.carried(["review", "--module", "WATER", "--milestone", "M1", "--worktree", WT], a, "run")
        self.assertNotIn("--model", review)  # the builder's model isn't the reviewer's
        self.assertNotIn("--one-step", review)
        for words in (words, review):
            PARSER.parse_args(words)

    def test_the_lead_check_in_setting(self):
        problems = []
        self.assertEqual([agent_loop.check_in_s(v, problems) for v in ("3h", "90 minutes", "2", None)],
                         [10800.0, 5400.0, 7200.0, agent_loop.LEAD_CHECK_IN_S])
        self.assertEqual(agent_loop.check_in_s("soon", problems), agent_loop.LEAD_CHECK_IN_S)
        self.assertIn("lead check-in", problems[0])


class StepsInARepository(Repo):
    """`run` and `plan` as the lead starts them, each step a command of its own with the fake host."""

    def setUp(self):
        super().setUp()
        # the steps run as processes of their own, which read the hosts and the home folder from the environment
        os.environ.update(ORCHESTRATE_CODEX=agent_loop.CODEX, ORCHESTRATE_CLAUDE=agent_loop.CLAUDE,
                          CODEX_HOME=str(self.home), CLAUDE_CONFIG_DIR=str(self.root / "claude-home"),
                          HOME=str(self.root / "home"))

    def steps(self, *argv):
        argv = list(argv)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                agent_loop.run_steps(PARSER.parse_args(argv), argv)
        finally:
            release()
        line = json.loads(out.getvalue().splitlines()[-1])
        check_next_commands(line)
        return line

    def test_a_run_carries_on_through_the_module_and_stops_when_it_is_finished(self):
        line = self.steps("run", "--module", "WATER", "--worktree", str(self.wt))
        self.assertEqual([(s["step"], s["result"]) for s in line["steps_run"]],
                         [("run WATER M1", "READY_FOR_REVIEW"), ("run WATER M2", "READY_FOR_REVIEW"),
                          ("review WATER M2", "REVIEWED")], line)
        self.assertEqual((line["result"], line["verdict"]), ("REVIEWED", "PASS"))
        self.assertIn("finished", line["stopped_because"])
        self.assertTrue(agent_loop.recorded_done(self.read_done()["milestones"][1], self.read_record()))

    def test_a_failed_review_restarts_the_builder_and_a_diagnosis_stops_the_steps(self):
        m1 = milestone("M1", "not_started", ["open"], inspect="captures")
        m1["failed_reviews"] = 4  # the next failure leaves the builder at it; the one after calls for a diagnosis
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ["FAKE_REVIEW"] = "fail"
        line = self.steps("run", "--module", "WATER", "--worktree", str(self.wt))
        self.assertEqual([(s["step"], s["result"], s.get("escalation")) for s in line["steps_run"]],
                         [("run WATER M1", "READY_FOR_REVIEW", None), ("review WATER M1", "REVIEWED", "same_builder"),
                          ("run WATER M1", "READY_FOR_REVIEW", None), ("review WATER M1", "REVIEWED", "diagnosis")])
        self.assertEqual((line["escalation"], line["next"]["by"]), ("diagnosis", "planner"))
        self.assertIn("ended REVIEWED", line["stopped_because"])

    def test_a_plan_carries_on_into_the_design_review_it_left_owed(self):
        os.environ.update(FAKE_PLAN="replan", FAKE_REVIEW="design")
        line = self.steps("plan", "--worktree", str(self.wt), "--task", "re-plan WATER M1")
        self.assertEqual([(s["step"], s["result"]) for s in line["steps_run"]],
                         [("plan", "PLANNED"), ("review WATER design", "REVIEWED")], line)
        self.assertEqual(line["verdict"], "DESIGN OK")
        self.assertIn("design is approved", line["stopped_because"])

    def test_one_step_runs_one_step_and_a_pause_stops_the_steps(self):
        env = dict(os.environ)
        one = subprocess.run([sys.executable, str(agent_loop.LOOP), "run", "--module", "WATER", "--worktree",
                              str(self.wt), "--one-step"], capture_output=True, text=True, env=env, timeout=120)
        line = json.loads(one.stdout.splitlines()[-1])
        self.assertEqual(line["result"], "READY_FOR_REVIEW", line)
        self.assertNotIn("steps_run", line)
        run = subprocess.Popen([sys.executable, str(agent_loop.LOOP), "run", "--module", "WATER", "--worktree",
                                str(self.wt)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                               env=dict(env, FAKE_PASS="0", FAKE_SLEEP="30"))
        self.addCleanup(lambda: (run.kill(), run.wait(), run.stdout.close()))
        calls = len(self.calls())
        deadline = time.time() + 30
        while time.time() < deadline and len(self.calls()) == calls:
            time.sleep(0.05)
        paused = subprocess.run([sys.executable, str(agent_loop.LOOP), "pause", "--module", "WATER", "--worktree",
                                 str(self.wt)], capture_output=True, text=True, env=env, check=True)
        self.assertNotEqual(json.loads(paused.stdout)["paused"][0]["pid"], run.pid)  # the step holds the module
        out, _ = run.communicate(timeout=60)
        line = json.loads(out.splitlines()[-1])
        self.assertEqual((line["result"], [s["result"] for s in line["steps_run"]]), ("PAUSED", ["PAUSED"]), line)
        self.assertEqual(json.loads(Path(line["result_file"]).read_text())["result"], "PAUSED")


class Watching(Repo):
    """`watch` ends at the lead's check-in or at a new warning sign, with a summary the lead can act on."""

    def setUp(self):
        super().setUp()
        for name, value in (("WATCH_POLL_S", 0.01), ("WATCH_SIGNS_S", 0.0)):
            patch = mock.patch.object(agent_loop, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def check_in(self, every="1s"):
        settings = self.wt / "ORCHESTRATE.md"
        settings.write_text(settings.read_text() + f"- **Lead check-in:** {every}\n")
        self.commit_all()

    def watch(self, runs=False):
        return self.call(agent_loop.cmd_watch, worktree=str(self.wt), runs=runs)

    def test_the_check_in_wakes_the_lead_with_a_summary(self):
        self.check_in()
        started = time.time()
        line = self.watch()
        self.assertEqual(line["result"], "CHECK_IN", line)
        self.assertGreaterEqual(time.time() - started, 0.9)
        self.assertIn("check-in", line["woke_for"][0])
        self.assertIn("WATER M1: ready to build, with no builder", line["not_moving"][0])
        self.assertEqual(line["builders"]["ready_waiting"], ["WATER M1"])
        self.assertIn("watch", line["next"]["argv"])
        self.assertIn("flow", line)

    def test_each_warning_sign_wakes_the_lead_once(self):
        self.check_in()
        with mock.patch.object(agent_loop, "READY_IDLE_WARN_S", 0.0), \
                mock.patch.object(agent_loop, "LOW_DISK_BYTES", 1 << 62):
            first = self.watch()
            self.assertEqual(first["result"], "WARNING_SIGNS", first)
            self.assertEqual(len(first["woke_for"]), 2, first)
            self.assertTrue(any("ready work has waited" in w for w in first["woke_for"]))
            self.assertTrue(first["disk"]["low"])
            second = self.watch()
        self.assertEqual(second["result"], "CHECK_IN", second)  # the same signs don't wake it again
        self.assertEqual(len(second["warning_signs"]), 2)

    def test_the_same_items_failing_two_reviews_in_a_row(self):
        self.check_in("1h")
        record = self.wt / "docs/plans/WATER/RECORD.json"
        rec = json.loads(record.read_text())
        rec["milestones"]["M1"]["reviews"] = [
            {"verdict": "fail", "at": agent_loop.now(), "items": {"M1.1": "fail"}},
            {"verdict": "fail", "at": agent_loop.now(), "items": {"M1.1": "pass"},
             "findings": [{"name": "flat water", "item": "M1.1"}]}]
        record.write_text(json.dumps(rec))
        self.commit_all()
        line = self.watch()
        self.assertEqual(line["result"], "WARNING_SIGNS", line)
        self.assertIn("WATER M1 failed its last two reviews on the same items (M1.1)", line["woke_for"])
        self.assertEqual(line["moved"]["reviews_failed"], ["WATER M1", "WATER M1"])

    def test_a_builder_without_progress_a_queued_planner_and_a_broken_main_branch(self):
        self.check_in("1h")
        repo = agent_loop.repository_of(agent_loop.git_common_dir(self.wt))
        old = time.time() - 3 * 3600
        state = self.wt / ".git/orchestrate/WATER.json"
        state.parent.mkdir(exist_ok=True)
        state.write_text(json.dumps({"milestone": "M1", "progress_at": old}))
        loops = [{"pid": 4242, "role": "build", "module": "WATER", "milestone": "M1", "worktree": str(self.wt),
                  "started_at": old - 60, "repository": repo, "turns": 5},
                 {"pid": 4343, "role": "plan", "task": "plan PAY", "waiting_for": "another planner",
                  "started_at": old, "repository": repo}]
        broken = [{"check": "e2e", "commit": "abc", "text": "main-branch check `e2e` failed on abc"}]
        with mock.patch.object(agent_loop, "live_loops", lambda *a, **k: (loops, [])), \
                mock.patch.object(agent_loop, "main_broken", lambda *a, **k: broken):
            line = self.watch()
        self.assertEqual(line["result"], "WARNING_SIGNS", line)
        woke = " | ".join(line["woke_for"])
        for text in ("WATER M1: no item has newly passed", "a planner has waited 3h", "`e2e` failed on abc"):
            self.assertIn(text, woke)
        self.assertEqual(line["builders"]["running"], 1)
        self.assertEqual(line["main_branch"], ["main-branch check `e2e` failed on abc"])

    def test_with_runs_it_wakes_the_lead_when_a_run_ends(self):
        self.check_in("1h")
        ended = {"pid": 4242, "role": "steps", "module": "WATER", "milestone": None}
        seen = iter([{4242: ended}])
        with mock.patch.object(agent_loop, "top_runs", lambda worktree: next(seen, {})):
            line = self.watch(runs=True)
        self.assertEqual(line["result"], "RUN_ENDED", line)
        self.assertEqual(line["woke_for"], ["steps WATER ended"])
        self.assertIn("--runs", line["next"]["argv"])
