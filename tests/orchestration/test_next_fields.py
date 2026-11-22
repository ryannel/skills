"""The script's own bookkeeping and `next` commands that took the place of steps the skills used to describe."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import agent_loop  # noqa: E402


class SplitOffMilestones(unittest.TestCase):
    def test_a_milestone_split_off_in_a_diagnosis_carries_the_diagnosed_count(self):
        before = {"milestones": [{"id": "M2", "diagnoses": 1, "failed_reviews": 3}]}
        after = {"milestones": [{"id": "M2", "diagnoses": 2, "failed_reviews": 0}, {"id": "M3", "diagnoses": 0}]}
        agent_loop.keep_counts(before, after, ["CORE M2"], "CORE", diagnosed="M2")
        self.assertEqual(after["milestones"][1]["diagnoses"], 2)

    def test_a_new_milestone_outside_a_diagnosis_keeps_what_the_planner_wrote(self):
        after = {"milestones": [{"id": "M3"}]}
        agent_loop.keep_counts({"milestones": []}, after, [], "CORE")
        self.assertNotIn("diagnoses", after["milestones"][0])


class MainCheckFix(unittest.TestCase):
    def test_a_failing_check_traced_to_a_module_gives_a_fix_task_with_a_revert_as_the_alternative(self):
        got = agent_loop.main_check_fix_next(Path("/repo"), "e2e", {"commit": "a" * 40, "subject": "add pay",
                                                                   "modules": ["PAY"]}, "it fails")
        self.assertIn(" plan --worktree /repo --module PAY --kind fix --task ", got["command"])
        self.assertIn("git revert --no-edit aaaaaaaaaaaa", got["alternative"])

    def test_a_failing_check_no_module_owns_goes_to_the_lead(self):
        got = agent_loop.main_check_fix_next(Path("/repo"), "e2e", {"commit": "b" * 40}, "it fails")
        self.assertIsNone(got["command"])
        self.assertIn("revert", got["why"])


class Migrated(unittest.TestCase):
    def test_definitions_naming_the_old_evidence_path_go_to_a_planner(self):
        got = agent_loop.migrated_next(Path("/repo"), {"evidence": {"from": "docs/evidence", "to": ".orchestrate/evidence",
                                                                    "definitions_naming_it": ["CORE M1", "CORE M2"]}})
        self.assertIn(" --module CORE --kind fix ", got["command"])
        self.assertIn("CORE M1, CORE M2", got["command"])

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
