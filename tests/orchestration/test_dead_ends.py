"""Results that sent the lead to a command that refuses, or left it with nothing to run.

Each test reproduces one of the dead ends the whole-set review of 18 November 2026 found
(workbench/orchestration-review/whole-set-review-2026-11-18/findings.md) and checks that the result now carries a
`next` that works."""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import (PROFILE, SCRIPTS, Repo, agent_loop, milestone, put, release)  # noqa: E402


def command(result):
    """The `next` command as the words a lead would run, so text in it reads without the shell's quoting."""
    then = result.get("next") or {}
    return " ".join(then["argv"]) if then.get("argv") else then.get("command") or ""


class RunEndings(Repo):
    """CHECKS_FAILED, STALLED and NO_PROGRESS_FOR_HOURS used to end with no `next`, and the skill sent the lead to
    `review`, which refuses a milestone that isn't Ready for Review."""

    def assert_fresh_run(self, result, *words):
        self.assertIn(" run ", command(result), result)
        self.assertIn("--fresh", command(result))
        self.assertIn("--message", command(result))
        for w in words:
            self.assertIn(w, command(result))
        self.assertIn(" plan ", result["next"]["alternative"])

    def test_checks_failed_restarts_the_builder_with_the_reasons(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "CHECKS_FAILED")
        self.assert_fresh_run(result, "items not yet pass: M1.1")

    def test_a_builder_that_says_an_item_cant_be_met_is_sent_to_a_planner(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="M1.1 can't be met as written: the target has no GPU.\nDONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "CHECKS_FAILED")
        self.assertIn(" plan ", command(result))
        self.assertIn("the target has no GPU", command(result))
        self.assertIn("--fresh", result["next"]["alternative"])

    def test_stalled_restarts_the_builder_with_the_open_items(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working on it")
        result = self.run_loop()
        self.assertEqual(result["result"], "STALLED")
        self.assert_fresh_run(result, "M1.1")

    def test_no_progress_restarts_the_builder(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working on it")
        result = self.run_loop(no_progress_hours=0.0)
        self.assertEqual(result["result"], "NO_PROGRESS_FOR_HOURS")
        self.assert_fresh_run(result)

    def test_checks_only_says_what_to_run_after_a_failure(self):
        result = self.run_loop(checks_only=True)
        self.assertEqual(result["result"], "CHECKS_FAILED")
        self.assertIn("--checks-only", command(result))

    def test_a_review_of_a_milestone_not_ready_for_review_points_to_the_module_not_back_at_itself(self):
        result = self.review("M1", commit="HEAD")
        self.assertEqual(result["result"], "INVALID")
        self.assertNotIn(" review ", command(result), result)
        self.assertIn(" run ", command(result))


class PendingMainCheck(Repo):
    """An item's check that asks a main-branch check exits 75 while that check hasn't judged the commit. That used to
    count as a failure: the builder got a turn to fix nothing, and the DONE counted towards CHECKS_FAILED."""

    def test_a_check_waiting_on_a_main_branch_check_is_asked_again_without_a_builder_turn(self):
        agent_loop.PENDING_CHECK_POLL_S = 0.01
        judged = self.root / "judged"
        check = f"test -f {judged} && exit 0; touch {judged}; exit 75"
        self.write_done([milestone("M1", "not_started", ["open"], check=check),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertEqual(len(self.calls()), 1)  # the one builder turn that did the work
        self.assertEqual(self.state()["not_ready_turns"], 0)
        self.assertNotIn("waiting_on_main_check", self.state())

    def test_a_check_that_never_gets_its_answer_ends_with_no_progress(self):
        agent_loop.PENDING_CHECK_POLL_S = 0.01
        self.write_done([milestone("M1", "not_started", ["open"], check="exit 75"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop(no_progress_hours=0.00001)
        self.assertEqual(result["result"], "NO_PROGRESS_FOR_HOURS", result)
        self.assertEqual(len(self.calls()), 1)
        self.assertIn("main-branch check", result["next"]["why"] + command(result))


class ReplannedWhileBuilding(Repo):
    """A planner re-plans the milestone a run is building. The run kept the definitions it started with, so every
    DONE failed as "not the authorised ones" and the builder was told to fix what it couldn't."""

    def replan_on_origin(self):
        """A planner's change to M1 lands on the main branch, with the record authorising it."""
        other = Path(tempfile.mkdtemp(dir=self.root))
        self.sh("git", "clone", "-q", str(self.origin), str(other / "c"))
        where = other / "c"
        path = where / "docs/plans/WATER/DONE.json"
        doc = json.loads(path.read_text())
        doc["milestones"][0]["items"][0]["statement"] = "a smaller first step"
        path.write_text(json.dumps(doc))
        rec_path = where / "docs/plans/WATER/RECORD.json"
        rec = json.loads(rec_path.read_text())
        rec["milestones"]["M1"]["definitions"] = agent_loop.definitions(doc["milestones"][0])
        rec_path.write_text(json.dumps(rec))
        self.git("commit", "-qam", f"orchestrate: authorise the plan\n\n{agent_loop.TRAILER}", where=where)
        self.git("push", "-q", "origin", "main", where=where)

    def test_a_run_stops_after_the_turn_in_which_its_milestone_was_replanned(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working on it")
        original = agent_loop.wait_for_merges
        landed = []

        def during_turn(worktree):
            if not landed:
                landed.append(self.replan_on_origin())
            return original(worktree)
        with mock.patch.object(agent_loop, "wait_for_merges", during_turn):
            result = self.run_loop()
        self.assertEqual(result["result"], "INVALID", result)
        self.assertIn("a planner changed M1's definitions", result["problems"][0])
        self.assertIn(" run ", command(result))
        self.assertEqual(len(self.calls()), 1)

    def test_merge_refuses_a_branch_built_to_the_old_items(self):
        path = self.wt / "docs/plans/WATER/DONE.json"
        doc = json.loads(path.read_text())
        doc["milestones"][0]["status"] = "in_progress"
        path.write_text(json.dumps(doc))
        put(self.wt / "src/water.txt", "work")
        self.git("add", "-A")
        self.git("commit", "-qm", "the builder's work")
        self.replan_on_origin()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_merge(argparse.Namespace(worktree=str(self.wt), no_check=False))
        release()
        self.assertEqual(stop.exception.code, 1)
        result = json.loads(out.getvalue().splitlines()[-1])
        self.assertEqual(result["result"], "FAILED")
        self.assertIn("WATER M1", result["detail"])
        self.assertIn("a planner has changed", result["detail"])


class PlannerEndings(Repo):
    """A planner turn that didn't merge used to end with no `next`, or, when its landing failed, as PLANNED."""

    def test_a_plan_that_couldnt_merge_has_its_own_result_and_a_next(self):
        with mock.patch.object(agent_loop, "land", return_value=(False, "rebase onto origin/main failed: conflict")):
            result = self.plan()
        self.assertEqual(result["result"], "PLAN_NOT_MERGED", result)
        self.assertFalse(result["merged"])
        self.assertIn(" plan ", command(result))
        self.assertIn("plan PAY", command(result))
        self.assertIn("couldn't merge", command(result))
        self.assertIn("stash", result)  # the planner's files are set aside, not lost

    def test_a_blocked_planner_gets_the_task_again_with_a_place_for_the_answer(self):
        os.environ.update(FAKE_PLAN="blocked")
        result = self.plan()
        self.assertEqual(result["result"], "BLOCKED")
        self.assertIn("plan PAY", command(result))
        self.assertIn("the user must choose the payment provider", command(result))
        self.assertIn("<the answer", command(result))

    def test_an_unfinished_planner_gets_the_task_again(self):
        os.environ.update(FAKE_PLAN="progress")
        result = self.plan()
        self.assertEqual(result["result"], "UNFINISHED")
        self.assertIn("plan PAY", command(result))

    def test_the_planners_task_names_keep(self):
        self.assertIn("`KEEP` line your task gives", agent_loop.PLAN_TEMPLATE)
        self.assertNotIn("If nothing should change", agent_loop.PLAN_TEMPLATE)

    def block_on_dependency(self):
        m1 = milestone("M1", "blocked", ["open"])
        m1["blocked"] = {"reason": "needs_dependency", "what": "PAY's payment API"}
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.git("add", "-A")
        self.git("commit", "-qm", "orchestrate: WATER M1 blocked: needs_dependency")
        self.git("push", "-q", "origin", "main")

    def blocked_next(self):
        prof = agent_loop.profile(self.wt)
        _, proj = agent_loop.read_project(self.wt, prof)
        return agent_loop.next_for(agent_loop.next_step("WATER", proj), self.wt, prof, proj)

    def test_unblock_comes_first_once_a_plan_has_merged_after_a_needs_dependency(self):
        self.block_on_dependency()
        before = self.blocked_next()
        self.assertIn(" plan ", before["command"])
        self.assertIn("KEEP WATER M1: builder:", before["command"])
        self.assertEqual(self.plan()["result"], "PLANNED")  # a planner adds the missing part to PAY
        after = self.blocked_next()
        self.assertIn(" unblock ", after["command"])
        self.assertIn("Plan: plan PAY", after["why"])
        self.assertIn(" plan ", after["alternative"])

    def test_keep_on_a_block_the_plan_answers_lifts_it(self):
        self.block_on_dependency()
        os.environ.update(FAKE_PLAN="keep_builder")
        result = self.plan(task="WATER M1 needs PAY's payment API")
        self.assertEqual((result["result"], result.get("unblocked")), ("KEPT", True), result)
        self.assertIn(" run ", command(result))
        m1 = self.read_done()["milestones"][0]
        self.assertEqual(m1["status"], "in_progress")
        self.assertNotIn("blocked", m1)
        self.assertEqual(m1["diagnoses"], 0)  # an answered block isn't a diagnosis


class HumanDecisionsBesideAPlanner(Repo):
    """`human` was refused while any planner held the repository's planner lock, so with planners queued the user's
    answers couldn't be recorded for hours."""

    def test_a_human_decision_is_recorded_while_a_planner_works_on_another_module(self):
        m1 = milestone("M1", "blocked", ["open", "open"], inspect="frames")
        m1["items"][1]["needs"] = {"type": "human_feedback", "what": "the user picks a direction"}
        m1["blocked"] = {"reason": "needs_human_feedback", "items": ["M1.2"], "what": "M1.2 needs the user"}
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop\n"
                f"from pathlib import Path; wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, '_plan')\n"
                "agent_loop.loop_register(wt, 'plan', task='plan PAY', host='codex', model='m', effort='high'); "
                "print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            result = self.human("feedback", "M1", "Direction B.", item="M1.2")
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
        self.assertEqual(result["result"], "DONE", result)


class BrokenMainBranch(Repo):
    """The script lands its own commits without the test command, so the main branch can break with no builder to
    blame. A branch that then failed alone in a batch was told the test command "passed without it"."""

    def use_test_command(self, test):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", f"`{test}`"))
        self.git("commit", "-qam", "test command")
        self.git("push", "-q", "origin", "main")

    def break_main(self):
        """A planner's commit adds a test the main branch fails, and lands without the test command."""
        put(self.wt / "docs/plans/PAY/PLAN.md", "# Pay plan")
        put(self.wt / "broken", "a test that fails")
        self.git("add", "-A")
        self.git("commit", "-qm", "Plan: plan PAY")
        self.git("push", "-q", "origin", "main")
        return agent_loop.head_commit(self.wt)

    def builder(self, name):
        where = self.root / f"builder-{name}"
        self.git("worktree", "add", "-q", "-b", f"build/{name}", str(where), "origin/main")
        put(where / f"{name}.txt", name)
        self.git("add", "-A", where=where)
        self.git("commit", "-qm", f"{name}'s work", where=where)
        return where

    def merge(self, *trees):
        queue = agent_loop.loop_dir(self.wt) / agent_loop.MERGE_QUEUE
        queue.mkdir(parents=True, exist_ok=True)
        lock = agent_loop.take_file_lock(agent_loop.loop_dir(self.wt) / f"{agent_loop.MERGE_QUEUE}.lock")
        procs = []
        try:
            for n, where in enumerate(trees, 1):
                procs.append(subprocess.Popen([sys.executable, str(SCRIPTS / "agent_loop.py"), "merge", "--worktree",
                                               str(where)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
                deadline = time.time() + 30
                while len(list(queue.glob("*.json"))) < n:
                    self.assertLess(time.time(), deadline)
                    time.sleep(0.05)
        finally:
            lock.close()
        out = []
        for p in procs:
            stdout, stderr = p.communicate(timeout=120)
            self.assertTrue(stdout.strip(), stderr)
            out.append(json.loads(stdout.splitlines()[-1]))
        return out

    def assert_main_broken(self, result, culprit):
        self.assertEqual(result["result"], "FAILED", result)
        self.assertNotIn("passed without it", result["detail"])
        self.assertIn("fails on the main branch", result["detail"])
        self.assertEqual(result["main_broken"]["culprit"]["commit"], culprit)
        self.assertEqual(result["main_broken"]["culprit"]["modules"], ["PAY"])
        self.assertIn(" plan ", command(result))
        self.assertIn("PAY", command(result))

    def test_branches_in_a_batch_on_a_broken_main_branch_are_told_so(self):
        self.use_test_command("test ! -f broken")
        culprit = self.break_main()
        a, b = self.merge(self.builder("a"), self.builder("b"))
        self.assert_main_broken(a, culprit)
        self.assert_main_broken(b, culprit)

    def test_a_branch_merging_alone_on_a_broken_main_branch_is_told_so(self):
        self.use_test_command("test ! -f broken")
        culprit = self.break_main()
        [a] = self.merge(self.builder("a"))
        self.assert_main_broken(a, culprit)

    def test_a_branch_that_breaks_the_test_command_itself_still_is_blamed(self):
        self.use_test_command("test ! -f b.txt")
        a, b = self.merge(self.builder("a"), self.builder("b"))
        self.assertEqual((a["result"], b["result"]), ("MERGED", "FAILED"), (a, b))
        self.assertIn("passed without it", b["detail"])
        self.assertNotIn("main_broken", b)


class FindingsForAPlanner(Repo):
    """Every Could Not Judge finding went back to the builder, even one only a planner can settle, such as an item
    its named proof can't prove."""

    def test_a_finding_for_a_planner_sends_the_review_to_the_diagnosis(self):
        work = self.ready_for_review()
        os.environ.update(FAKE_REVIEW="fail", FAKE_FOR_PLANNER="a frame sequence can't show the latency the item asks")
        result = self.review("M1", commit=work)
        self.assertEqual((result["verdict"], result["escalation"]), ("FAIL", "diagnosis"), result)
        self.assertEqual(result["next"]["by"], "planner")
        self.assertIn("only a planner can settle", command(result))
        self.assertIn("can't show the latency", command(result))
        os.environ.pop("FAKE_FOR_PLANNER")
        self.assertEqual(self.run_loop()["result"], "WAITING")  # no builder starts on it until the planner has acted

    def test_keep_after_a_planner_finding_lets_the_builder_carry_on(self):
        work = self.ready_for_review()
        os.environ.update(FAKE_REVIEW="fail", FAKE_FOR_PLANNER="the items contradict each other")
        self.review("M1", commit=work)
        os.environ.pop("FAKE_FOR_PLANNER")
        os.environ.update(FAKE_PLAN="keep_builder")
        self.assertEqual(self.plan(task="Diagnose WATER M1")["result"], "KEPT")
        m1 = self.read_done()["milestones"][0]
        self.assertFalse(agent_loop.planner_findings(m1))
        self.assertEqual(agent_loop.escalation_of(m1), "none")

    def test_old_findings_without_the_field_escalate_as_before(self):
        self.assertEqual(agent_loop.escalation_of({"failed_reviews": 1, "findings": [{"name": "x", "item": "M1.1"}]}),
                         "same_builder")
        self.assertEqual(agent_loop.findings_problems({"findings": [{"name": "x", "planner": ""}]}, "M1", []),
                         ["M1: finding 'x': planner should say why only a planner can settle it"])
