"""The script's own bookkeeping and `next` commands that took the place of steps the skills used to describe."""
import shlex
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import agent_loop  # noqa: E402


class SplitOffWorkPackages(unittest.TestCase):
    def test_a_work_package_split_off_in_a_diagnosis_carries_the_diagnosed_count(self):
        before = {"work_packages": [{"id": "WP2", "diagnoses": 1, "failed_reviews": 3}]}
        after = {"work_packages": [{"id": "WP2", "diagnoses": 2, "failed_reviews": 0}, {"id": "WP3", "diagnoses": 0}]}
        agent_loop.keep_counts(before, after, ["CORE WP2"], "CORE", diagnosed="WP2")
        self.assertEqual(after["work_packages"][1]["diagnoses"], 2)

    def test_a_new_work_package_outside_a_diagnosis_keeps_what_the_planner_wrote(self):
        after = {"work_packages": [{"id": "WP3"}]}
        agent_loop.keep_counts({"work_packages": []}, after, [], "CORE")
        self.assertNotIn("diagnoses", after["work_packages"][0])


class MainCheckFix(unittest.TestCase):
    def test_a_failing_check_traced_to_a_module_gives_a_fix_task_with_a_revert_as_the_alternative(self):
        got = agent_loop.main_check_fix_next(Path("/repo"), "e2e", {"commit": "a" * 40, "subject": "add pay",
                                                                   "modules": ["PAY"]}, "it fails")
        self.assertIn(" plan --worktree /repo --module PAY --kind fix --task ", got["command"])
        self.assertEqual(got["alternative"], "git -C /repo revert --no-edit aaaaaaaaaaaa")
        self.assertIn("human rereview", got["why"])

    def test_a_failing_check_no_module_owns_goes_to_a_planner_for_the_whole_project(self):
        got = agent_loop.main_check_fix_next(Path("/repo"), "e2e", {"commit": "b" * 40}, "it fails")
        self.assertIn(" plan --worktree /repo --kind fix --task ", got["command"])
        self.assertNotIn("--module", got["command"])
        self.assertIn("bbbbbbbbbbbb, which no module's merge made", shlex.split(got["command"])[-1])
        self.assertEqual(got["alternative"], "git -C /repo revert --no-edit bbbbbbbbbbbb")

    def test_a_failing_check_with_no_commit_found_yet_still_gives_a_command(self):
        got = agent_loop.main_check_fix_next(Path("/repo"), "e2e", {}, "it fails")
        self.assertIn("couldn't tell which commit broke it", shlex.split(got["command"])[-1])
        self.assertNotIn("alternative", got)


class Migrated(unittest.TestCase):
    def test_definitions_naming_the_old_evidence_path_go_to_a_planner(self):
        got = agent_loop.migrated_next(Path("/repo"), {"evidence": {"from": "docs/evidence", "to": ".orchestrate/evidence",
                                                                    "definitions_naming_it": ["CORE WP1", "CORE WP2"]}})
        self.assertIn(" --module CORE --kind fix ", got["command"])
        self.assertIn("CORE WP1, CORE WP2", got["command"])

    def test_nothing_to_fix_points_at_status(self):
        self.assertIn(" status ", agent_loop.migrated_next(Path("/repo"), {})["command"])


class FlowSigns(unittest.TestCase):
    def test_slow_merges_and_a_slow_test_command_are_named(self):
        f = {"merges": {**agent_loop.spread([5, 6, 40, 45, 50, 60, 70, 80, 90, 95]), "failed": 0, "conflicts": 0,
                        "main_broken": 0},
             "checks": {"test_command": {**agent_loop.spread([31, 33, 35]), "failed": 0}, "slowest_other": []},
             "locks": {}, "reviews": {"count": 0, "passed": 0, "first_reviews": 0, "first_review_passes": 0},
             "background_jobs": {"started": 0, "errors": 0}, "build_sessions": 2, "ready_for_review": 2}
        signs = agent_loop.flow_signs(f)
        self.assertTrue(any(s.startswith("merges are slow") for s in signs), signs)
        self.assertTrue(any(s.startswith("the test command is slow") for s in signs), signs)

    def test_a_quiet_build_has_no_signs(self):
        f = {"merges": {"count": 0}, "checks": {"test_command": {"count": 0}}, "locks": {},
             "reviews": {"count": 0, "passed": 0, "first_reviews": 0, "first_review_passes": 0},
             "background_jobs": {"started": 0, "errors": 0}, "build_sessions": 0, "ready_for_review": 0}
        self.assertEqual(agent_loop.flow_signs(f), [])


if __name__ == "__main__":
    unittest.main()
