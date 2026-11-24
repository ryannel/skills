"""The smaller fixes from the whole-set review of 2026-11-18: the setup command, the Builders line read as a person
would, builder sessions kept across a script fix, a result line from `pause`, a CHANGES entry for every version, the
review's bookkeeping worked out by the script, and graded examples from the user's overturned reviews."""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Clean, Repo, agent_loop, put, release  # noqa: E402  (first: points the script's homes at this process's folder)


class SetupCommand(Repo):
    def settings(self, setup, test="none"):
        (self.wt / "ORCHESTRATE.md").write_text(
            f"- **Plans:** docs/plans\n- **Merge:** push\n- **Test command:** {test}\n- **Default host:** codex\n"
            f"- **Setup command:** {setup}\n- **Builders:** 20 builders\n")
        (self.wt / ".gitignore").write_text("deps/\n")
        self.commit_all()

    def test_the_settings_read_the_setup_command_and_none_means_no_command(self):
        self.settings("npm ci")
        self.assertEqual(agent_loop.profile(self.wt)["setup_command"], "npm ci")
        self.settings("none")
        self.assertEqual(agent_loop.profile(self.wt)["setup_command"], "")

    def test_setup_runs_in_a_new_checkout_and_again_only_when_a_lockfile_changes(self):
        runs = self.root / "setup-runs"
        prof = {"setup_command": f"echo x >> {runs}"}
        tree = agent_loop.verify_tree(self.wt, "WATER", "HEAD")
        self.assertIsNone(agent_loop.run_setup(tree, prof))
        self.assertIsNone(agent_loop.run_setup(tree, prof))
        self.assertEqual(runs.read_text().count("x"), 1, "a checkout set up from the same files isn't set up again")
        (self.wt / "src.txt").write_text("code")
        self.commit_all()
        tree = agent_loop.verify_tree(self.wt, "WATER", agent_loop.head_commit(self.wt))
        agent_loop.run_setup(tree, prof)
        self.assertEqual(runs.read_text().count("x"), 1, "a change to code alone needs no new setup")
        (self.wt / "package-lock.json").write_text("{}")
        self.commit_all()
        tree = agent_loop.verify_tree(self.wt, "WATER", agent_loop.head_commit(self.wt))
        agent_loop.run_setup(tree, prof)
        self.assertEqual(runs.read_text().count("x"), 2, "a new lockfile sets the checkout up again")

    def test_a_failed_setup_is_the_checks_failure_and_is_tried_again(self):
        tree = agent_loop.verify_tree(self.wt, "WATER", "HEAD")
        prof = {"setup_command": "echo no registry >&2; exit 3", "test_command": "true", "plans": "docs/plans"}
        m = {"id": "M1", "items": [{"id": "M1.1", "check": "true"}]}
        self.assertEqual(agent_loop.check_failures(tree, prof, {"id": "M1", "items": []}), [],
                         "with no item check to run there is nothing to set up for")
        failed = agent_loop.check_failures(tree, prof, m)
        self.assertEqual(len(failed), 1)
        self.assertIn("Setup command `echo no registry >&2; exit 3` exited 3", failed[0])
        self.assertIn("no registry", failed[0])
        prof["setup_command"] = "true"
        self.assertEqual(agent_loop.check_failures(tree, prof, m), [])

    def merge(self):
        put(self.wt / "src.txt", "code\n")
        self.commit_all()
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                agent_loop.cmd_merge(argparse.Namespace(worktree=str(self.wt), no_check=False))
        finally:
            release()
        return json.loads(out.getvalue().splitlines()[-1])

    def test_a_merge_tests_the_work_after_setup_installs_what_the_test_needs(self):
        # The test command needs a file only the setup makes, in a folder git ignores, as node_modules is.
        self.settings("mkdir -p deps && touch deps/installed", test="`test -f deps/installed`")
        out = self.merge()
        self.assertEqual(out["result"], "MERGED", out)

    def test_without_setup_the_same_merge_fails_its_test_command(self):
        self.settings("none", test="`test -f deps/installed`")
        out = self.merge()
        self.assertNotEqual(out["result"], "MERGED", out)


class BuildersLine(Clean):
    def count(self, line):
        return agent_loop.builders_count(f"- **Builders:** {line}\n")

    def test_the_counts_on_the_line_add_up(self):
        self.assertEqual(self.count("two Claude builders and one Codex builder"), 3)
        self.assertEqual(self.count("2 builders on codex, 1 builder on claude"), 3)

    def test_a_total_with_its_breakdown_counts_once(self):
        self.assertEqual(self.count("three builders: two Codex and one Claude"), 3)
        self.assertEqual(self.count("two builders (one on each host)"), 2)

    def test_one_count_and_lines_without_builder_still_read_as_before(self):
        self.assertEqual(self.count("one Codex builder"), 1)
        self.assertEqual(self.count("two Codex builders, one at a time"), 2)
        self.assertEqual(self.count("3"), 3)
        self.assertIsNone(self.count("as many as are ready"))
        self.assertIsNone(self.count("<how many builders>"))


class BuilderSessions(Clean):
    def test_a_session_given_the_same_prompts_and_skill_carries_on_across_versions(self):
        state = {"version": "2.0.0", "basis": agent_loop.session_basis()}
        self.assertIsNone(agent_loop.stale_session(state))

    def test_a_session_given_other_prompts_or_another_skill_starts_again(self):
        why = agent_loop.stale_session({"version": agent_loop.VERSION, "basis": "0" * 16})
        self.assertIn("build prompt or the builder skill has changed", why)
        state = {"version": agent_loop.VERSION, "basis": agent_loop.session_basis()}
        agent_loop.BUILD_TEMPLATE = agent_loop.BUILD_TEMPLATE + " Something new."
        self.assertIsNotNone(agent_loop.stale_session(state))

    def test_a_state_file_without_a_basis_goes_by_its_version(self):
        self.assertIsNone(agent_loop.stale_session({"version": agent_loop.VERSION}))
        self.assertIn("version 2.2.0", agent_loop.stale_session({"version": "2.2.0"}))


class PauseResult(Repo):
    def test_pause_with_nothing_running_ends_with_a_result(self):
        out = self.call(agent_loop.cmd_pause, module=None, worktree=str(self.wt))
        self.assertEqual(out["result"], "NOTHING")
        self.assertEqual(out["paused"], [])
        self.assertEqual(out["version"], agent_loop.VERSION)


class Changes(Clean):
    def test_this_version_says_what_changed(self):
        self.assertIn(agent_loop.VERSION, agent_loop.CHANGES,
                      f"CHANGES has no entry for {agent_loop.VERSION}: add what behaves differently in it, for the "
                      "lead of a project that has just moved to it")
        self.assertTrue(all(isinstance(line, str) and line for line in agent_loop.CHANGES[agent_loop.VERSION]))


# A reviewer that writes only what it judged: each item's verdict, the findings and the review file. It leaves the
# milestone's status and the items' `review` fields as the builder left them, and gives no counts.
BARE_REVIEWER = """#!/usr/bin/env python3
import json, os
from pathlib import Path
cwd = Path(os.getcwd())
path = cwd / "docs/plans/WATER/DONE.json"
d = json.loads(path.read_text())
m = next(m for m in d["milestones"] if m["status"] == "ready_for_review")
verdict = os.environ.get("BARE_VERDICT", "fail")
for i in m["items"]:
    i["verdict"] = verdict
if verdict == "fail":
    m["findings"] = [{"name": "the water is flat", "item": i["id"]} for i in m["items"]]
path.write_text(json.dumps(d))
(cwd / ".orchestrate/evidence/WATER").mkdir(parents=True, exist_ok=True)
(cwd / f".orchestrate/evidence/WATER/{m['id']}-review.md").write_text("judged")
reply = f"PASS {m['id']}" if verdict == "pass" else f"FAIL {m['id']}"
print(json.dumps({"type": "thread.started", "thread_id": "t1"}))
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": reply}}))
"""


class ReviewBookkeeping(Repo):
    def bare_reviewer(self):
        host = self.root / "bare-codex"
        host.write_text(BARE_REVIEWER)
        host.chmod(0o755)
        agent_loop.CODEX = str(host)

    def test_a_failed_review_with_only_verdicts_and_findings_is_saved(self):
        self.ready_for_review()
        self.bare_reviewer()
        out = self.review()
        self.assertEqual(out["result"], "REVIEWED", out)
        self.assertEqual(out["verdict"], "FAIL")
        self.assertEqual(out["found"], {"fail": 1, "could_not_judge": 0, "outside_the_items": 0})
        self.assertIn("status in_progress", out["filled"])
        m1 = self.read_done()["milestones"][0]
        self.assertEqual(m1["status"], "in_progress")
        self.assertEqual({i["review"] for i in m1["items"]}, {".orchestrate/evidence/WATER/M1-review.md"})

    def test_a_passed_review_with_only_verdicts_is_saved_as_done(self):
        self.ready_for_review()
        self.bare_reviewer()
        os.environ["BARE_VERDICT"] = "pass"
        out = self.review()
        self.assertEqual(out["result"], "REVIEWED", out)
        self.assertEqual(self.read_done()["milestones"][0]["status"], "done")

    def test_a_review_written_the_old_way_is_saved_as_before(self):
        self.ready_for_review()
        os.environ["FAKE_REVIEW"] = "fail"
        out = self.review()
        self.assertEqual(out["result"], "REVIEWED", out)
        self.assertNotIn("filled", out)
        self.assertEqual(self.read_done()["milestones"][0]["status"], "in_progress")


class GradedExamples(Repo):
    def name_the_file(self):
        with open(self.wt / "ORCHESTRATE.md", "a") as f:
            f.write("- **Graded examples:** .orchestrate/evidence/graded-examples.md\n")
        self.commit_all()

    def failed_review(self):
        self.ready_for_review()
        os.environ["FAKE_REVIEW"] = "fail"
        self.assertEqual(self.review()["result"], "REVIEWED")

    def examples(self):
        """The graded examples, which are kept in the working folder and never committed."""
        path = self.evidence("graded-examples.md")
        self.git("fetch", "-q", "origin")
        self.assertNotIn("graded-examples.md", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)
        return path.read_text() if path.exists() else None

    def test_accepting_a_failed_milestone_adds_the_case_with_the_humans_words(self):
        self.name_the_file()
        self.failed_review()
        out = self.human("accept", "M1", reason="The flat water is the style I asked for.")
        self.assertEqual(out["result"], "DONE", out)
        self.assertEqual(out["graded_example"], ".orchestrate/evidence/graded-examples.md")
        text = self.examples()
        self.assertIn("## WATER M1: the user overturned a review", text)
        self.assertIn("- M1.1 (Fail): M1.1 works", text)
        self.assertIn("the water is flat (M1.1)", text)
        self.assertIn("> The flat water is the style I asked for.", text)
        self.assertIn("Why it is here:", text)

    def test_re_reviewing_a_passed_milestone_adds_the_case(self):
        self.name_the_file()
        self.ready_for_review()
        self.assertEqual(self.review()["result"], "REVIEWED")
        out = self.human("rereview", "M1", reason="The foam doesn't move; that's not done.")
        self.assertEqual(out["result"], "DONE", out)
        text = self.examples()
        self.assertIn("passed it", text)
        self.assertIn("> The foam doesn't move; that's not done.", text)

    def test_no_file_is_written_when_the_settings_name_none(self):
        self.failed_review()
        out = self.human("accept", "M1")
        self.assertEqual(out["result"], "DONE", out)
        self.assertNotIn("graded_example", out)
        self.assertIsNone(self.examples())


class SecondReviewScript(Repo):
    """The script side of the second whole-set review (2026-11-22): prompts that name what only the script knows,
    and `next` and `why` strings that point at the right command and leave the lead skill's judgement to it."""

    def test_the_codex_note_follows_the_sandbox_setting_and_keeps_only_the_window_rule(self):
        note = agent_loop.session_rule(True, "codex", {"sandbox": "workspace-write"})
        self.assertIn("outside Codex's sandbox", note)
        for gone in ("yield_time_ms", "apply_patch", "`ps`", "NEEDS_CONTEXT"):
            self.assertNotIn(gone, note)
        self.assertNotIn("sandbox", agent_loop.session_rule(True, "codex", {"sandbox": "danger-full-access"}))
        self.assertNotIn("sandbox", agent_loop.session_rule(False, "claude", {"sandbox": "workspace-write"}))

    def test_review_prompts_carry_the_session_note_and_the_design_review_names_the_brief(self):
        prof = agent_loop.profile(self.wt)
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        rec = json.loads((self.wt / "docs/plans/WATER/RECORD.json").read_text())
        common = dict(host="codex", prof=prof, stem="WATER", mid="M1", commit="abc", done="docs/plans/WATER/DONE.json",
                      review=".orchestrate/evidence/WATER/M1-review.md", milestone=doc["milestones"][0],
                      entry=rec["milestones"]["M1"], feedback=None, judged=[], tree=self.wt)
        review = agent_loop.review_prompt(**common)
        design = agent_loop.review_prompt(**{**common, "mid": "design", "design": True})
        for text in (review, design):
            self.assertIn("This session runs in the background", text)
            self.assertNotIn("the skill describes", text)
        self.assertIn(f"The project brief is {self.wt / 'docs/plans/BRIEF.md'}", design)
        self.assertIn(str(self.wt / "docs/plans/ARCHITECTURE.md"), design)

    def test_plan_refuses_unmerged_plan_files_with_adopt_and_the_plan_command_after_it(self):
        (self.wt / "docs/plans/BRIEF.md").write_text("# Brief\n")
        refused = self.plan()
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("docs/plans/BRIEF.md", refused["unmerged_plans"]["uncommitted"])
        self.assertIn(" adopt ", refused["next"]["command"])
        self.assertIn(" plan ", refused["next"]["then"]["command"])

    def test_settings_prints_the_default_paths_before_the_project_has_settings(self):
        (self.wt / "ORCHESTRATE.md").unlink()
        out = json.loads(self.printed(agent_loop.cmd_settings, code=1, worktree=str(self.wt)).splitlines()[-1])
        self.assertFalse(out["planned"])
        self.assertEqual(out["paths"]["brief"], str(self.wt.resolve() / "docs/plans/BRIEF.md"))

    def test_messages_that_change_a_setting_name_settings_set(self):
        self.assertIn("settings --set", agent_loop.adoptable(agent_loop.profile(self.wt), self.wt, "HEAD",
                                                             "ORCHESTRATE.md"))
        self.assertNotIn("ask the planner", agent_loop.hold_limit_note("gpu", 60, "make"))
        (self.wt / "ORCHESTRATE.md").write_text(
            (self.wt / "ORCHESTRATE.md").read_text().replace("- **Builders:**", "- **Old builders:**"))
        self.commit_all()
        refused = self.run_loop()
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("settings", refused["next"]["argv"])
        self.assertIn("Builders", refused["next"]["argv"])
        self.assertEqual(refused["next"]["decides"], "human")
        self.assertIn(" run ", refused["next"]["then"])

    def test_planner_tasks_give_facts_and_leave_the_instructions_to_the_task_file(self):
        prof = agent_loop.profile(self.wt)
        task = agent_loop.diagnosis_task("WATER", "M1", {"failed_reviews": 6}, prof)
        self.assertNotIn("Read every review", task)
        self.assertIn("KEEP WATER M1", task)
        self.assertNotIn("change no file", agent_loop.answered_line("WATER", "M1"))

    def test_the_build_prompt_names_the_commit_subject_and_promises_no_reviewer(self):
        prof = agent_loop.profile(self.wt)
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        text = agent_loop.build_prompt("claude", True, prof, "WATER", "M1", doc["milestones"][0])
        self.assertIn("`WATER M1: `", text)
        self.assertIn("Done, or Ready for Review when the milestone needs a reviewer", text)
        self.assertNotIn("starts a reviewer", text)

    def test_the_pick_between_options_is_reviewed(self):
        pick = {"id": "M2", "items": [{"id": "M2.1", "needs": {"type": "human_feedback"}, "check": "true"}]}
        doc = {"milestones": [{"id": "M1", "items": [{"id": "M1.1", "check": "true"}]}, pick]}
        self.assertTrue(agent_loop.needs_review(pick, doc, {"ends_stretch": True}))
        self.assertNotIn("closes without a reviewer", agent_loop.needs_review.__doc__)

    def test_the_settings_template_carries_what_the_planner_files_no_longer_say(self):
        t = agent_loop.SETTINGS_TEMPLATE
        self.assertIn("- **Test command:** none", t)
        self.assertIn("must pass before any test exists", t)
        self.assertIn("into ignored folders, leaving tracked files as they were", t)
        self.assertIn("gates no milestone", t)
        self.assertIn("else the only one installed, else codex", t)
        self.assertEqual(t.count("Keep it on a new project"), 2)
        self.assertIn("{prompt}, {model} and {effort}", t)
