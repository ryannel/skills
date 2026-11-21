"""The smaller fixes from the whole-set review of 2026-11-18: the setup command, the Builders line read as a person
would, builder sessions kept across a script fix, a result line from `pause`, a CHANGES entry for every version, the
review's bookkeeping worked out by the script, and graded examples from the user's overturned reviews."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Clean, Repo, agent_loop  # noqa: E402  (first: points the script's homes at this process's folder)


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
        failed = agent_loop.check_failures(tree, prof, {"id": "M1", "items": []})
        self.assertEqual(len(failed), 1)
        self.assertIn("Setup command `echo no registry >&2; exit 3` exited 3", failed[0])
        self.assertIn("no registry", failed[0])
        prof["setup_command"] = "true"
        self.assertEqual(agent_loop.check_failures(tree, prof, {"id": "M1", "items": []}), [])

    def test_a_merge_tests_the_work_after_setup_installs_what_the_test_needs(self):
        # The test command needs a file only the setup makes, in a folder git ignores, as node_modules is.
        self.settings("mkdir -p deps && touch deps/installed", test="test -f deps/installed")
        out = self.run_loop()
        self.assertEqual(out["result"], "READY_FOR_REVIEW", out)

    def test_without_setup_the_same_merge_fails_its_checks(self):
        self.settings("none", test="test -f deps/installed")
        out = self.run_loop()
        self.assertNotEqual(out["result"], "READY_FOR_REVIEW", out)


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
