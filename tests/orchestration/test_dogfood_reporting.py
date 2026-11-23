"""What a dogfood run found in reporting and escalation: a milestone that fails review again on the same item counts as
a repeat even with a new finding, a plan that changes a milestone's items starts its counts again, `flow` names a low
review pass rate and planning churn and counts every Ready for Review, `report` reads the state `status` reads, and
`watch` and `runs` treat a `run` going through its steps as one builder."""

import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import PROCESS, Clean, Repo, agent_loop, milestone  # noqa: E402


def section(report, heading):
    return report.split(heading + "\n")[1].split("\n## ")[0]


def flow(**over):
    f = {"merges": {"count": 0}, "checks": {"test_command": {"count": 0}}, "locks": {},
         "reviews": {"count": 0, "passed": 0, "first_reviews": 0, "first_review_passes": 0},
         "background_jobs": {"started": 0, "errors": 0}, "build_sessions": 0, "ready_for_review": 0}
    f.update(over)
    return f


class Escalation(Clean):
    def test_an_item_that_fails_again_is_a_repeat_whatever_its_finding_says(self):
        found = [{"name": "ties at the limit", "item": "M1.7", "different": "the earlier one capped the lines"}]
        # the finding is new, by its name and its `different`, so it isn't a repeated finding
        self.assertEqual(agent_loop.repeats(found, {"ten-line cap"}, {"M1.7"}), [])
        # but M1.7 failed before and fails again, so the review counts as a repeat
        self.assertEqual(agent_loop.items_failed_again({"M1.1": "pass", "M1.7": "fail"}, found, {"M1.7"}), ["M1.7"])
        self.assertEqual(agent_loop.items_failed_again({"M1.5": "fail", "M1.7": "pass"},
                                                       [{"name": "x", "item": "M1.5"}], {"M1.7"}), [])

    def test_a_plan_that_changes_a_milestones_items_starts_its_counts_again(self):
        before = {"milestones": [dict(milestone("M1", "in_progress", ["open"]), failed_reviews=3,
                                      failed_reviews_with_repeat=2, diagnoses=1, findings=[{"name": "x"}]),
                                 dict(milestone("M2", "not_started", ["open"]), failed_reviews=2)]}
        after = json.loads(json.dumps(before))
        after["milestones"][0]["items"][0]["check"] = "test -f closed-to-the-listed-variants"
        for m in after["milestones"]:  # a planner can't change the counts by writing them
            m.update(failed_reviews=0, failed_reviews_with_repeat=0, diagnoses=0)
        agent_loop.keep_counts(before, after, [], "WATER")
        m1, m2 = after["milestones"]
        self.assertEqual((m1["failed_reviews"], m1["failed_reviews_with_repeat"], m1["diagnoses"], "findings" in m1),
                         (0, 0, 1, False))
        self.assertEqual(m2["failed_reviews"], 2, "a milestone whose items didn't change keeps its counts")

    def test_the_help_names_the_item_and_the_restart(self):
        text = agent_loop.COMMAND_HELP["next"]
        self.assertIn(f"{agent_loop.REPEATS_TO_DIAGNOSE} reviews with a repeat", text)
        # a new builder session comes one repeat before the diagnosis, as `escalation` decides
        self.assertIn(f"or {agent_loop.REPEATS_TO_DIAGNOSE - 1} with a repeat: a builder in a new session", text)
        self.assertIn("An item that fails again counts even when its finding is new", text)
        self.assertIn("after any plan that changes the milestone's items", text)
        self.assertIn("(`repeated_items` names", agent_loop.COMMAND_HELP["review"])


class Flow(Clean):
    def test_a_low_review_pass_rate_is_a_sign_that_names_the_items(self):
        reviews = {"count": 8, "passed": 1, "first_reviews": 2, "first_review_passes": 0,
                   "most_failed": [{"item": "WORDFREQ M1.7", "failed": 5}]}
        signs = agent_loop.flow_signs(flow(reviews=reviews))
        self.assertTrue(any(s.startswith("only 1 of 8 reviews passed, and most failures were on WORDFREQ M1.7 "
                                         "(5 failed reviews)") and "How it will be judged" in s for s in signs), signs)
        reviews.update(count=3, passed=0)  # too few to say anything
        self.assertFalse(any("reviews passed" in s for s in agent_loop.flow_signs(flow(reviews=reviews))))

    def test_planning_turns_matching_build_turns_is_a_sign(self):
        signs = agent_loop.flow_signs(flow(turns={"plan": 9, "design_review": 4, "build": 10, "review": 8}))
        self.assertTrue(any(s.startswith("planning is churning: 9 planner turns and 4 design review turns beside 10 "
                                         "builder turns") for s in signs), signs)
        self.assertEqual(agent_loop.flow_signs(flow(turns={"plan": 9, "design_review": 4, "build": 20})), [])
        self.assertEqual(agent_loop.flow_signs(flow(turns={"plan": 3, "design_review": 1, "build": 1})), [])

    def test_ready_for_review_counts_each_time_not_each_milestone(self):
        since = "2026-11-22T00:00:00Z"
        came_back = {"ready_for_review": {"at": "2026-11-22T09:00:00Z"},
                     "reviews": [{"verdict": "fail", "at": "2026-11-22T07:00:00Z"},
                                 {"verdict": "fail", "at": "2026-11-22T08:00:00Z"},
                                 {"verdict": "pass", "at": "2026-11-22T09:05:00Z"}]}
        self.assertEqual(agent_loop.ready_events(came_back, since), 3)
        waiting = {"ready_for_review": {"at": "2026-11-22T10:00:00Z"},
                   "reviews": [{"verdict": "fail", "at": "2026-11-22T09:00:00Z"}]}
        self.assertEqual(agent_loop.ready_events(waiting, since), 2, "the one no review has answered counts too")
        self.assertEqual(agent_loop.ready_events(waiting, "2026-11-23T00:00:00Z"), 0)


class DesignReviewList(Clean):
    def test_a_copy_made_as_a_review_starts_is_listed_once(self):
        root = PROCESS / "design-reviews"
        folder = root / "ev/WATER"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "design-review.md").write_text("review two\nDESIGN CHANGES\n")
        (folder / "design-review-1.md").write_text("review one\nDESIGN CHANGES\n")
        (folder / "design-review-2.md").write_text("review two\nDESIGN CHANGES\n")  # copied as review three starts
        rec = {"design_history": [{"verdict": "changes", "review": "ev/WATER/design-review-1.md",
                                   "at": "2026-11-22T22:47:52Z"}],
               "design": {"verdict": "changes", "review": "ev/WATER/design-review.md", "at": "2026-11-22T22:56:53Z"}}
        with mock.patch.object(agent_loop, "evidence_file", lambda wt, prof, rel: root / rel):
            rows = agent_loop.design_reviews(root, {"evidence": "ev"}, "HEAD", "WATER", rec)
        self.assertEqual([r["review"] for r in rows], ["ev/WATER/design-review-1.md", "ev/WATER/design-review.md"])


class ReportReadsStatus(Repo):
    def test_a_failed_review_after_ready_for_review_and_a_paused_run(self):
        m1 = dict(milestone("M1", "in_progress", ["pass", "open"]), failed_reviews=1)
        self.write_done([m1, milestone("M2", "not_started", ["open"])], ready=("M1",))
        record = self.wt / "docs/plans/WATER/RECORD.json"
        rec = json.loads(record.read_text())
        rec["milestones"]["M1"]["reviews"] = [{"verdict": "fail", "at": agent_loop.now(), "items": {"M1.2": "fail"}}]
        record.write_text(json.dumps(rec))
        self.commit_all()
        results = agent_loop.loop_dir(self.wt) / "results"
        results.mkdir(parents=True, exist_ok=True)
        (results / "WATER-M1-run.json").write_text(json.dumps({"result": "PAUSED", "module": "WATER",
                                                               "milestone": "M1"}) + "\n")
        with mock.patch.object(agent_loop, "live_loops", lambda *a, **k: ([], [])):
            report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertNotIn("waiting for a review", report)  # `status` has it In Progress with a failed review
        needs = section(report, "## Needs you now")
        self.assertIn("- WATER M1: its run was paused at ", needs)
        self.assertIn(" run --module WATER ", needs)
        live = [{"role": "steps", "module": "WATER"}]
        with mock.patch.object(agent_loop, "live_loops", lambda *a, **k: (live, [])):
            self.assertEqual(agent_loop.paused_runs(self.wt, live), [], "a run going again isn't paused")


class StepsAreOneBuilder(Clean):
    def test_a_step_seen_before_its_record_belongs_to_its_parent(self):
        loops = [{"pid": 1, "role": "steps", "module": "WATER", "origin": "run", "registered": True,
                  "activity_at": 100.0, "turns": 0},
                 {"pid": 2, "role": "build", "module": "WATER", "ppid": 1, "started_at": 2000.0}]
        agent_loop.join_steps(loops)
        self.assertEqual([r["pid"] for r in agent_loop.builder_runs(loops)], [1])

    def test_a_plans_steps_hold_no_builder_slot(self):
        loops = [{"pid": 1, "role": "steps", "module": "WATER", "origin": "plan"},
                 {"pid": 2, "role": "review", "milestone": "design", "steps_parent": 1},
                 {"pid": 3, "role": "steps", "module": "SKY", "task": "re-plan SKY"},  # before `origin`
                 {"pid": 4, "role": "steps", "module": "SAND", "origin": "run"},
                 {"pid": 5, "role": "build", "module": "SAND", "steps_parent": 4}]
        self.assertEqual([r["pid"] for r in agent_loop.builder_runs(loops)], [4])

    def test_runs_shows_the_parent_working_while_its_step_works(self):
        stamp = time.time()
        loops = [{"pid": 1, "role": "steps", "module": "WATER", "registered": True, "activity_at": stamp - 1620,
                  "turns": 0, "started_at": stamp - 3600},
                 {"pid": 2, "role": "build", "module": "WATER", "milestone": "M2", "steps_parent": 1,
                  "registered": True, "host": "claude", "model": "claude-sonnet-5-5", "effort": "medium",
                  "turns": 2, "activity_at": stamp - 30, "started_at": stamp - 600}]
        agent_loop.join_steps(loops)
        view = agent_loop.loop_view(loops[0])
        self.assertEqual((view["host"], view["milestone"], view["turns"]), ("claude", "M2", 2))
        self.assertLess(view["idle_s"], 60)


class Watch(Clean):
    def test_a_new_watch_counts_its_check_in_from_its_own_start(self):
        folder = PROCESS / "watch-loop"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / agent_loop.WATCH_FILE).write_text(json.dumps({"woke_at": time.time() - 5 * 3600, "signs": {}}))

        class Slept(Exception):
            pass

        def sleep(_):
            raise Slept

        look = {"stamp": time.time()}
        with mock.patch.object(agent_loop, "unplanned", lambda wt: None), \
                mock.patch.object(agent_loop, "profile", lambda wt: {"check_in_s": 3 * 3600.0}), \
                mock.patch.object(agent_loop, "loop_dir", lambda wt: folder), \
                mock.patch.object(agent_loop, "watch_look", lambda *a: look), \
                mock.patch.object(agent_loop, "watch_signs", lambda l: {}), \
                mock.patch.object(agent_loop.time, "sleep", sleep):
            # a watch started 5 hours after the last one woke the lead waits rather than waking it at once
            with self.assertRaises(Slept):
                agent_loop.cmd_watch(agent_loop.argparse.Namespace(worktree=str(folder), runs=False))

    def test_the_sign_and_the_counts_say_item_or_finding(self):
        rec = {"milestones": {"M1": {"reviews": [
            {"verdict": "fail", "at": "2026-11-22T23:07:05Z", "items": {"M1.7": "fail"},
             "findings": [{"name": "ten-line cap", "item": "M1.7"}]},
            {"verdict": "fail", "at": "2026-11-22T23:12:07Z", "items": {"M1.7": "fail"},
             "findings": [{"name": "ties at the limit", "item": "M1.7", "different": "new"}]}]}}}
        m1 = dict(milestone("M1", "in_progress", ["open"]), failed_reviews=2, failed_reviews_with_repeat=1)
        look = {"stamp": time.time(), "builds": [], "progress": {}, "loops": [], "since": {}, "disk": None,
                "broken": [], "proj": {"WATER": {"stem": "WATER", "problems": [], "record": rec,
                                                 "doc": {"milestones": [m1]}}}}
        text = agent_loop.watch_signs(look)["same_items WATER M1"]["text"]
        self.assertEqual(text, "WATER M1 failed the same items in its last two reviews (M1.7), whether or not the "
                               "findings were new")
        self.assertEqual(agent_loop.repeat_words(1), "1 of them on an item or a finding an earlier review had failed")


if __name__ == "__main__":
    unittest.main()
