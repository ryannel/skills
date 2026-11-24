"""The findings of the second-round review of 18 November 2026
(workbench/orchestration-review/whole-set-review-2026-11-18/findings.md, "Second-round review"), one test or more
for each, written to fail before its fix."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import (BASE_PROFILE, PROFILE, SCRIPTS, Clean, Repo, agent_loop, work_package, put)  # noqa: E402
import test_dead_ends as dead_ends  # noqa: E402  (a module, so its test classes don't run again here)

command = dead_ends.command


def live(where, role, module=None, parent=None, sleep=60):
    """A process that registers a loop record for `where`, as a run, plan or chain does, and waits. It ends when it is
    sent SIGTERM."""
    env = dict(os.environ, **({agent_loop.STEPS_ENV: str(parent)} if parent else {}))
    code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop\n"
            f"from pathlib import Path; agent_loop.loop_register(Path({str(where)!r}), {role!r}, module={module!r})\n"
            f"print('up', flush=True); time.sleep({sleep})\n")
    proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True, env=env)
    assert proc.stdout.readline().strip() == "up"
    return proc


def stop(*procs):
    for p in procs:
        if p.poll() is None:
            p.kill()
        p.wait()
        p.stdout.close()


class SetupBeforeTheBareMainBranch(Repo):
    """Script 1: with a Setup command, a branch that failed alone was told the main branch was broken, because the
    script tested the main branch without running the setup first."""

    builder = dead_ends.BrokenMainBranch.builder
    merge = dead_ends.BrokenMainBranch.merge

    def test_a_branch_that_breaks_the_tests_is_blamed_when_the_tests_need_the_setup(self):
        text = PROFILE.replace("none", "`test -f deps/installed && test ! -f b.txt`")
        (self.wt / "ORCHESTRATE.md").write_text(text + "- **Setup command:** mkdir -p deps && touch deps/installed\n")
        (self.wt / ".gitignore").write_text("deps/\n")
        self.commit_all()
        [b] = self.merge(self.builder("b"))
        self.assertEqual(b["result"], "FAILED", b)
        self.assertNotIn("main_broken", b)
        self.assertNotIn("fails on the main branch", b["detail"])


class ChainedSteps(Clean):
    """Script 2 and 3: what a `run` or `plan` keeps of its steps, and passes on to the next."""

    def test_a_plan_steps_report_stays_in_steps_run(self):
        line = {"result": "PLANNED", "report": "The user must choose the payment provider.\nPLANNED: a, b"}
        entry = agent_loop.step_entry(["plan", "--worktree", "x", "--task", "plan PAY"], line, 60)
        self.assertIn("the payment provider", entry["report"])

    def test_a_later_run_step_keeps_the_host_the_lead_gave(self):
        a = argparse.Namespace(host="claude", model="m", effort=None, review_host=None, no_progress_hours=4.0,
                               no_design_review=False, turn_timeout_hours=2.0)
        words = agent_loop.carried(["run", "--module", "WATER", "--worktree", "x"], a, "run")
        self.assertEqual(agent_loop.argv_flag(words, "--host"), "claude")


class AnotherModulesReplan(Repo):
    """Script 4: `merge` refused a branch that only lagged a re-plan of a module it hadn't touched."""

    replan_on_origin = dead_ends.ReplannedWhileBuilding.replan_on_origin

    def test_a_branch_of_another_module_behind_a_replan_merges(self):
        path = self.wt / "docs/plans/WATER/DONE.json"
        doc = json.loads(path.read_text())
        doc["work_packages"][0]["status"] = "in_progress"
        path.write_text(json.dumps(doc))
        self.commit_all()
        other = self.root / "pay-builder"
        self.git("worktree", "add", "-q", "-b", "build/pay", str(other), "origin/main")
        put(other / "src/pay.txt", "pay work")
        self.git("add", "-A", where=other)
        self.git("commit", "-qm", "PAY work", where=other)
        self.replan_on_origin()
        self.git("fetch", "-q", "origin", where=other)
        self.assertEqual(agent_loop.stale_definitions(other, agent_loop.profile(other), "origin/main"), [])


class PauseAChain(Repo):
    """Script 5: `pause` signalled only the holders of run locks, so a `run` between steps, or one whose planner or
    reviewer was working, carried on."""

    def test_pause_stops_a_run_carrying_on_through_its_steps(self):
        parent = live(self.wt, "steps", module="WATER")
        try:
            out = self.call(agent_loop.cmd_pause, module="WATER", worktree=str(self.wt))
            self.assertEqual(out["result"], "PAUSED", out)
            self.assertEqual([p["pid"] for p in out["paused"]], [parent.pid])
            self.assertEqual(parent.wait(timeout=10), -signal.SIGTERM)
        finally:
            stop(parent)

    def test_pause_of_the_whole_repository_stops_a_plan_between_steps(self):
        parent = live(self.wt, "steps")
        try:
            out = self.call(agent_loop.cmd_pause, module=None, worktree=str(self.wt))
            self.assertEqual(out["result"], "PAUSED", out)
            self.assertEqual(parent.wait(timeout=10), -signal.SIGTERM)
        finally:
            stop(parent)


class DiagnosisThatChangesSomethingElse(Repo):
    """Script 6: a diagnosis that fixed the fault outside the work package's items left it Waiting for Diagnosis."""

    def test_planned_on_a_diagnosis_settles_the_work_package(self):
        w1 = work_package("WP1", "in_progress", ["open"])
        w1["failed_reviews"] = agent_loop.FAILED_REVIEWS_TO_DIAGNOSE
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(agent_loop.escalation_of(self.read_done()["work_packages"][0]), "diagnosis")
        result = self.plan(task="Diagnose WATER WP1. It has failed review six times.")  # the planner changes PAY
        self.assertEqual(result["result"], "PLANNED", result)
        self.assertIn("WATER WP1", result.get("replanned", []))
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["failed_reviews"], w1["diagnoses"], w1["status"]), (0, 1, "in_progress"))
        self.assertEqual(agent_loop.escalation_of(w1), "none")


class AStuckRunsPlanner(Repo):
    """Script 7 and skills 2: the planner a stuck run sent had no ending the script would take when every item could
    be met, and a refused KEEP left the lead with no `next`."""

    def stuck(self):
        w1 = work_package("WP1", "in_progress", ["open"])
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()

    def test_the_planners_task_gives_the_keep_line(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="WP1.1 can't be met as written: no GPU.\nDONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "CHECKS_FAILED", result)
        self.assertIn("KEEP WATER WP1: builder:", command(result))

    def test_keep_for_the_builder_after_a_stuck_run_restarts_it(self):
        self.stuck()
        os.environ.update(FAKE_PLAN="keep_builder")
        result = self.plan(task="WATER WP1: its run stopped")
        self.assertEqual(result["result"], "KEPT", result)
        self.assertIn(" run ", command(result))
        self.assertIn("--fresh", command(result))
        self.assertEqual(self.read_done()["work_packages"][0]["diagnoses"], 0)

    def test_a_refused_keep_gives_the_planner_the_task_again(self):
        self.stuck()
        os.environ.update(FAKE_PLAN="keep_reviewer")
        result = self.plan(task="WATER WP1: its run stopped")
        self.assertEqual(result["result"], "INVALID", result)
        self.assertIn(" plan ", command(result))
        self.assertIn("refused", command(result))


class MainCheckSetup(Repo):
    """Script 9: a setup command that failed was recorded as the main-branch check failing, which led to a bisect and
    a broken main branch."""

    def test_a_failed_setup_is_an_attempt_that_couldnt_judge(self):
        spec = {"setup": "exit 3", "command": "true", "locks": [], "timeout_s": 30}
        got = agent_loop.main_check_attempt(self.wt, agent_loop.head_commit(self.wt), spec, self.root / "check")
        self.assertEqual(got["exit"], agent_loop.MAIN_CHECK_UNJUDGED_EXIT)
        self.assertEqual(agent_loop.main_check_result([got, got]), "unjudged")


class MainCheckStartRunsNow(Repo):
    """Delivery Lead: a main-branch check waited for its next scheduled run, so with `every 4h` a run asked for by hand
    sat idle for hours."""

    def setUp(self):
        super().setUp()
        settings = self.wt / "ORCHESTRATE.md"
        settings.write_text(settings.read_text() + "- **Main-branch check soak:** `true`; every 4h\n")
        self.commit_all()
        self.prof = agent_loop.profile(self.wt)
        self.folder = agent_loop.main_check_dir(self.wt, "soak")

    def test_a_run_started_by_hand_doesnt_wait_out_every(self):
        head = agent_loop.head_commit(self.wt)
        (self.folder / "runs").mkdir(parents=True, exist_ok=True)
        (self.folder / "runs" / "1-old.json").write_text(json.dumps(
            {"kind": "tip", "commit": "0" * 40, "result": "pass", "started_s": time.time(), "finished_s": time.time()}))
        got = agent_loop.main_check_runner(self.wt, self.prof, "soak", self.prof["main_checks"]["soak"], force=True)
        self.assertEqual((got["result"], got["commit"]), ("pass", head), got)


class PlannerFindingsAfterADiagnosis(Repo):
    """Script 10: a finding only a planner can settle went straight to the user after any earlier diagnosis, even
    one about something else."""

    def test_after_a_diagnosis_for_something_else_it_gets_a_diagnosis(self):
        m = {"failed_reviews": 1, "diagnoses": 1, "findings": [{"name": "x", "planner": "the items contradict"}]}
        self.assertEqual(agent_loop.escalation_of(m), "diagnosis")

    def test_after_a_diagnosis_for_a_planner_finding_too_it_goes_to_the_human(self):
        work = self.ready_for_review()
        os.environ.update(FAKE_REVIEW="fail", FAKE_FOR_PLANNER="the items contradict each other")
        self.review("WP1", commit=work)
        os.environ.update(FAKE_PLAN="keep_builder")
        self.assertEqual(self.plan(task="Diagnose WATER WP1")["result"], "KEPT")
        w1 = self.read_done()["work_packages"][0]
        self.assertTrue(w1[agent_loop.PLANNER_DIAGNOSED])
        w1["findings"] = [{"name": "y", "planner": "still contradictory"}]
        self.assertEqual(agent_loop.escalation_of(w1), "too_many_failed_reviews")


class BuildersLine(Clean):
    """Script 11: counts written against host names were undercounted."""

    def test_counts_before_host_names_add_up(self):
        for line in ("2 Codex, 1 Claude", "two Codex and one Claude", "2 Codex and 1 Claude builder",
                     "two Codex builders (one Claude builder for the UI)"):
            self.assertEqual(agent_loop.builders_count(f"- **Builders:** {line}\n"), 3, line)


class AChainHoldsItsBuilderSlot(Repo):
    """Script 12: while a `run` carrying on through its steps was in its review step, it had no build record, so
    `run` and `watch` counted its builder slot free."""

    def test_a_chain_counts_once_whichever_step_it_is_on(self):
        parent = live(self.wt, "steps", module="WATER")
        try:
            self.assertEqual([b["pid"] for b in agent_loop.builders_running(self.wt)], [parent.pid])
            child = live(self.wt, "build", module="WATER", parent=parent.pid)
            try:
                self.assertEqual([b["pid"] for b in agent_loop.builders_running(self.wt)], [parent.pid])
            finally:
                stop(child)
        finally:
            stop(parent)

    def test_watch_counts_the_chain_against_the_builders_line(self):
        settings = self.wt / "ORCHESTRATE.md"
        settings.write_text(BASE_PROFILE + "- **Builders:** one\n")
        self.commit_all()
        repo = agent_loop.repository_of(agent_loop.git_common_dir(self.wt))
        loops = [{"pid": 4242, "role": "steps", "module": "PAY", "repository": repo}]
        with mock.patch.object(agent_loop, "live_loops", lambda *a, **k: (loops, [])):
            look = agent_loop.watch_look(self.wt, agent_loop.profile(self.wt), {}, False)
        self.assertEqual(look["free"], 0)


class MainBrokenReachesTheLead(Repo):
    """Skills 1: a builder stopped by a broken main branch ended as needs_context, with `run --message` as its next,
    and the run's result didn't carry `main_broken`."""

    def test_a_builder_naming_main_broken_ends_the_run_with_it(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED main_broken: the test command fails at abc without me")
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "main_broken"), result)
        self.assertEqual(result["next"]["by"], "lead")
        self.assertNotEqual(self.read_done()["work_packages"][0]["status"], "blocked")

    def test_the_merges_main_broken_and_next_come_through(self):
        saved = self.wt / ".git/orchestrate" / agent_loop.MAIN_BROKEN_FILE
        saved.parent.mkdir(parents=True, exist_ok=True)
        broken = {"commit": "abc", "exit": 1, "culprit": {"commit": "abc", "subject": "Plan: plan PAY",
                                                          "modules": ["PAY"]}}
        nxt = agent_loop.main_broken_next(self.wt, agent_loop.profile(self.wt), broken)
        saved.write_text(json.dumps({"main_broken": broken, "next": nxt, "at": time.time() + 60}))
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: the main branch is broken")
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "main_broken"), result)
        self.assertEqual(result["main_broken"]["culprit"]["modules"], ["PAY"])
        self.assertIn(" plan ", command(result))
        self.assertIn(" run ", result["next"]["alternative"])

    def test_merge_saves_main_broken_for_the_run(self):
        case = dead_ends.BrokenMainBranch
        case.use_test_command(self, "test ! -f broken")
        case.break_main(self)
        where = case.builder(self, "a")
        [a] = case.merge(self, where)
        self.assertIn("main_broken", a)
        self.assertIn("BLOCKED main_broken", a["detail"])
        git_dir = Path(self.git("rev-parse", "--absolute-git-dir", where=where).stdout.strip())
        self.assertIn("main_broken", json.loads((git_dir / "orchestrate" / agent_loop.MAIN_BROKEN_FILE).read_text()))


class WatchStartsDueChecks(Repo):
    """Skills 3: the skill told the lead to run `main-check --due` each time it was woken; `watch` does it now."""

    def test_watch_starts_a_due_main_branch_check(self):
        settings = self.wt / "ORCHESTRATE.md"
        settings.write_text(settings.read_text() + "- **Main-branch check soak:** `true`; every 1m\n")
        self.commit_all()
        started = []
        with mock.patch.object(agent_loop, "main_check_spawn", lambda wt, name, force=False: started.append(name)):
            agent_loop.watch_look(self.wt, agent_loop.profile(self.wt), {}, True)
        self.assertEqual(started, ["soak"])


class WatchWording(Clean):
    """Skills 6: messaging a builder means pausing it first, and the free-slot sign names the builders allowed."""

    def test_watch_says_to_pause_before_messaging(self):
        self.assertIn("pause --module", agent_loop.WATCH_WHY)

    def test_the_free_slot_sign_names_the_builders_allowed(self):
        look = {"stamp": 2000.0, "builds": [], "progress": {}, "proj": {}, "loops": [], "disk": None, "broken": [],
                "since": {"ready_waiting": 1.0}, "limit": 3, "waiting": [{"module": "WATER", "work_package": "WP1"}]}
        text = agent_loop.watch_signs(look)["ready_waiting"]["text"]
        self.assertIn("fewer than the 3 builders allowed are running: WATER WP1", text)
        text = agent_loop.watch_signs({**look, "limit": None})["ready_waiting"]["text"]
        self.assertIn("no number limits the builders", text)


class StaleTemplateLines(Clean):
    """Skills 11: the prompts said the lead starts reviews, and repeated the escalation thresholds."""

    def test_the_templates_no_longer_say_the_lead_starts_reviews_or_give_thresholds(self):
        self.assertNotIn("The lead runs the design review", agent_loop.PLAN_TEMPLATE)
        self.assertNotIn("starts the reviewer", agent_loop.BUILD_TEMPLATE)
        self.assertNotIn("six failed reviews", agent_loop.FINDINGS_TEMPLATE)
