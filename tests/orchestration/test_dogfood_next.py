"""`next` fields the wordfreq dogfood run of 23 November 2026 found wrong, missing or meant for the wrong actor.

A lead follows each result's `next` as it is printed, so each test checks that the command is the right one,
complete with the flags the lead gave, and run by the lead."""

import json
import os
import shlex
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import BASE_PROFILE, PROFILE, Repo, agent_loop, milestone, put  # noqa: E402


def words(result, key="command"):
    then = result.get("next") or {}
    text = then.get(key) if isinstance(then.get(key), str) else ""
    return shlex.split(text) if text else []


class PlanFlags(Repo):
    """Finding 3: a `next` that gave a planner the task again dropped `--one-step`, so following it ran the design
    reviews before the user had seen the plan."""

    def unmerged_brief(self):
        put(self.wt / "docs/plans/BRIEF.md", "# Brief\n\nA small tool.\n")

    def test_a_refused_one_step_plan_keeps_its_flags_in_then_and_in_adopts_then(self):
        self.unmerged_brief()
        result = self.plan(one_step=True, model="m-1", effort="low")
        self.assertEqual(result["result"], "REFUSED", result)
        then = shlex.split(result["next"]["then"]["command"])
        for flag in ("--one-step", "--model", "--effort"):
            self.assertIn(flag, then)
        adopt = words(result)
        self.assertEqual(adopt[2], "adopt")
        self.assertEqual(adopt[adopt.index("--then") + 1], result["next"]["then"]["command"])

    def test_adopt_gives_back_the_command_it_was_run_for(self):
        self.unmerged_brief()
        refused = self.plan(one_step=True)
        adopt = words(refused)
        result = self.call(agent_loop.cmd_adopt, worktree=str(self.wt), paths=[],
                           then=adopt[adopt.index("--then") + 1])
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertEqual(result["next"]["command"], refused["next"]["then"]["command"])
        self.assertEqual(result["next"]["by"], "lead")

    def test_adopt_without_then_still_points_at_ready(self):
        self.unmerged_brief()
        result = self.call(agent_loop.cmd_adopt, worktree=str(self.wt), paths=[])
        self.assertIn("ready", words(result))

    def test_the_retry_after_an_invalid_plan_keeps_one_step(self):
        os.environ.update(FAKE_PLAN="forge")
        result = self.plan(one_step=True)
        self.assertEqual(result["result"], "INVALID", result)
        self.assertIn("--one-step", words(result))

    def test_a_step_of_a_longer_plan_leaves_one_step_to_the_command_that_runs_the_steps(self):
        args = agent_loop.argparse.Namespace(kind="change", host="claude", model=None, effort=None,
                                             turn_timeout_hours=2.0, one_step=True)
        self.assertEqual(agent_loop.plan_flags(args), ["--kind", "change", "--host", "claude", "--one-step"])
        with mock.patch.object(agent_loop, "STEPS_PARENT", "1"):
            self.assertNotIn("--one-step", agent_loop.plan_flags(args))
        self.assertNotIn("--model", agent_loop.plan_flags(
            agent_loop.argparse.Namespace(host="codex", model="m", one_step=False), on="claude"))


class FirstPlanAndReady(Repo):
    """Finding 5: the first plan's PLANNED and `ready` with milestones that can start had no command in `next`."""

    def test_the_first_plan_asks_for_the_builders_line_then_runs_the_first_module(self):
        (self.wt / "ORCHESTRATE.md").write_text(BASE_PROFILE)
        self.commit_all()
        result = self.plan(one_step=True)
        self.assertEqual((result["result"], result.get("first_plan")), ("PLANNED", True), result)
        got = words(result)
        self.assertEqual(got[2:4], ["settings", "--worktree"])
        self.assertIn("Builders", got)
        self.assertEqual(result["next"]["decides"], "human")
        self.assertTrue(result["next"]["ask"])
        then = shlex.split(result["next"]["then"])
        self.assertEqual(then[2], "run")
        self.assertEqual(then[then.index("--module") + 1], "PAY")

    def test_ready_gives_each_milestone_that_can_start_its_run(self):
        ready = self.ready()
        self.assertEqual([s["module"] for s in ready["can_start"]], ["WATER"])
        self.assertIn("run", words(ready["can_start"][0]))
        self.assertEqual(ready["next"]["command"], ready["can_start"][0]["next"]["command"])
        self.assertIn("--module", words(ready))


class BuildWorktreePlanFiles(Repo):
    """Finding 6: after a pause, the builder's committed check script in the plans folder made `run` send the lead
    to `adopt` in the build worktree, which would merge an unreviewed part of the builder's work to main."""

    def worktree_profile(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Worktrees:** .orchestrate/worktrees\n")
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        prof = agent_loop.profile(self.wt)
        built, _ = agent_loop.module_worktree(self.wt, prof, "WATER")
        put(built / "docs/plans/WATER/checks/suite_guard.py", "print('guard')\n")
        self.git("add", "-A", where=built)
        self.git("commit", "-qm", "WATER M1: tests and a guard", where=built)
        return prof, built

    def test_plan_files_a_builder_committed_in_its_worktree_go_with_its_work(self):
        prof, built = self.worktree_profile()
        drift = agent_loop.plan_drift(built, prof, agent_loop.tip(built, prof))
        self.assertEqual((drift["unmerged"], drift["uncommitted"]), ([], []))
        self.assertIn("docs/plans/WATER/checks/suite_guard.py", drift["with_work"])

    def test_a_design_not_approved_after_a_pause_sends_the_lead_to_the_planner_not_to_adopt(self):
        self.worktree_profile()
        os.environ.update(FAKE_REVIEW="design_changes")
        result = self.run_loop(one_step=True)
        self.assertEqual(result["result"], "DESIGN_NOT_APPROVED", result)
        self.assertNotIn("unmerged_plans", result)
        got = words(result)
        self.assertEqual(got[2], "plan")
        self.assertEqual(got[got.index("--kind") + 1], "revise")
        self.assertEqual(result["next"]["by"], "lead")

    def test_every_planner_command_is_the_leads_to_run(self):
        prof = agent_loop.profile(self.wt)
        then = agent_loop.design_review_next({"verdict": "DESIGN CHANGES", "review": "r.md"}, "WATER", self.wt, prof)
        self.assertEqual(then["by"], "lead")
        counts = {"failed_reviews": 3, "failed_reviews_with_repeat": 2}
        self.assertEqual(agent_loop.escalation_next("diagnosis", "WATER", "M1", counts, self.wt, prof)["by"], "lead")


class SettingsTemplate(Repo):
    """Finding 7: the template's Setup command was `npm ci`, which fails in a project that isn't Node."""

    def test_the_setup_command_is_none_with_examples_in_the_note(self):
        out = self.printed(agent_loop.cmd_settings, worktree=str(self.wt), template=True)
        line = next(l for l in out.splitlines() if l.startswith("- **Setup command:**"))
        self.assertTrue(line.startswith("- **Setup command:** none  *("), line)
        self.assertIn("npm ci", line)


class DropAModule(Repo):
    """Finding 1: a planner asked to drop a module had its turn refused for deleting the record, and `next` gave the
    same task again, which failed the same way."""

    def second_module(self, started=False):
        doc = {"module": "ACC", "milestones": [milestone("M1", "in_progress" if started else "not_started",
                                                         ["pass" if started else "open"])]}
        put(self.wt / "docs/plans/ACC/DONE.json", json.dumps(doc))
        put(self.wt / "docs/plans/ACC/RECORD.json", json.dumps(agent_loop.adopt(doc, agent_loop.text_hash(None))))
        put(self.wt / "docs/plans/ARCHITECTURE.md",
            "| # | Module | What it's for | Needs |\n|---|---|---|---|\n| 1 | WATER | water | |\n| 2 | ACC | tests | WATER |\n")
        self.commit_all()

    def drop(self, row=True):
        cmd = "rm -rf docs/plans/ACC"
        if row:
            cmd += " && grep -v ' ACC ' docs/plans/ARCHITECTURE.md > a.tmp && mv a.tmp docs/plans/ARCHITECTURE.md"
        os.environ.update(FAKE_DURING=cmd)

    def test_a_module_nothing_was_built_in_is_dropped_whole(self):
        self.second_module()
        self.drop()
        result = self.plan(task="Drop ACC", kind="change", one_step=True)
        self.assertEqual(result["result"], "PLANNED", result)
        self.assertEqual(result["removed"], ["ACC"])
        self.git("fetch", "-q", "origin")
        listed = self.git("ls-tree", "-r", "--name-only", "origin/main", "docs/plans/ACC").stdout
        self.assertEqual(listed, "")

    def test_its_row_in_the_module_table_has_to_go_too(self):
        self.second_module()
        self.drop(row=False)
        result = self.plan(task="Drop ACC", kind="change", one_step=True)
        self.assertEqual(result["result"], "INVALID", result)
        self.assertTrue(any("module table" in p for p in result["problems"]), result["problems"])

    def test_a_started_module_keeps_its_record_and_the_retry_says_what_to_do_instead(self):
        self.second_module(started=True)
        self.drop()
        result = self.plan(task="Drop ACC", kind="change", one_step=True)
        self.assertEqual(result["result"], "INVALID", result)
        self.assertTrue(any("ACC M1 has started" in p for p in result["problems"]), result["problems"])
        task = words(result)[words(result).index("--task") + 1]
        self.assertIn("keep its folder and record", task)
        self.assertIn("--one-step", words(result))


if __name__ == "__main__":
    import unittest
    unittest.main()
