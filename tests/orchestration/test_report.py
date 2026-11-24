"""Checks for `report`, the facts the lead sends when the user asks how the build is going: the window it covers,
the four questions it answers (what needs the user, what is done, what is moving, what has slowed down), the file
`--write` puts it in, and that no result asks the lead for a report a day any more."""

import contextlib
import io
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import COMMANDS, Repo, agent_loop, work_package, parse_argv  # noqa: E402

HEADINGS = ["## Needs you now", "## Done", "## Verdicts", "## Now and next", "## What has slowed down", "## Flow",
            "## Cost"]


def section(report, heading):
    return report.split(heading + "\n")[1].split("\n## ")[0]


class Report(Repo):

    def report(self, **kw):
        return self.printed(agent_loop.cmd_report, worktree=str(self.wt), **kw)

    def times(self):
        return agent_loop.loop_dir(self.wt) / agent_loop.REPORT_TIMES

    def test_it_answers_the_four_questions_in_order(self):
        w1 = work_package("WP1", "in_progress", ["pass", "open"])
        w1["items"][1]["needs"] = {"type": "human_feedback", "what": "the user picks a colour"}
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        report = self.report(since=24.0)
        self.assertEqual([h for h in HEADINGS if h in report], HEADINGS)
        self.assertLess(report.index("## Needs you now"), report.index("## Done"))
        self.assertIn("# Build report, the last 24 hours", report)
        self.assertIn("0 of 1 module Done", report)
        needs = section(report, "## Needs you now")
        self.assertIn("- WATER WP1 WP1.2 (needs user feedback: the user picks a colour)", needs)
        self.assertIn(" human feedback --module WATER --work-package WP1 --item WP1.2 ", needs)
        moving = section(report, "## Now and next")
        self.assertIn("- WATER WP1 (work package 1 of 2): In Progress, 1 of 2 items passing", moving)
        self.assertIn("[done-when file](docs/plans/WATER/DONE.json)", moving)
        self.assertIn("- Nothing became Done in this window.", section(report, "## Done"))

    def test_slowed_down_names_the_cause_the_records_show(self):
        w1 = work_package("WP1", "in_progress", ["open"])
        w1.update(failed_reviews=3, failed_reviews_with_repeat=2)
        w2 = dict(work_package("WP2", "blocked", ["open"]),
                  blocked={"reason": "too_many_failed_reviews", "what": "the user decides"})
        self.write_done([w1, w2])
        self.commit_all()
        results = agent_loop.loop_dir(self.wt) / "results"
        results.mkdir(parents=True, exist_ok=True)
        (results / "WATER-WP1-run.json").write_text(json.dumps(
            {"result": "STALLED", "module": "WATER", "work_package": "WP1", "open": ["WP1.1"]}) + "\n")
        (results / "WATER-WP1-review.json").write_text(json.dumps({"result": "FAILED", "module": "WATER"}) + "\n")
        old = results / "WATER-WP2-run.json"
        old.write_text(json.dumps({"result": "HOST_FAILED", "module": "WATER", "work_package": "WP2"}) + "\n")
        os.utime(old, (time.time() - 3 * 86400,) * 2)  # before the window
        stamp = time.time()
        live = {"pid": 1, "role": "build", "repository": None, "module": "WATER", "work_package": "WP1",
                "host": "codex", "model": "gpt-6.2-sol", "effort": "medium", "path": "headless",
                "started_at": stamp - 7200, "turns": 2, "activity_at": stamp - 2400, "registered": True,
                "turn_started_at": stamp - 2400, "step": "builder turn 3"}
        with mock.patch.object(agent_loop, "live_loops", lambda *a, **k: ([live], [])):
            report = self.report(since=24.0)
        slowed = section(report, "## What has slowed down")
        self.assertIn("- WATER WP1 has failed review 3 times since its definitions last changed, 2 of them on an "
                      "item or a finding an earlier review had failed", slowed)
        self.assertIn("- WATER WP1: `run` ended STALLED at ", slowed)
        self.assertIn("open items: WP1.1", slowed)
        self.assertNotIn("review` ended", slowed)  # a failed review is counted above, not as a slowed run
        self.assertNotIn("HOST_FAILED", slowed)  # older than the window
        self.assertIn("- WATER WP1 (build): no sign of activity for 40m", slowed)
        moving = section(report, "## Now and next")
        self.assertIn("- Running now: WATER WP1, build on codex gpt-6.2-sol medium, started 2h 0m ago, 2 turns done, "
                      "one running for 40m; now builder turn 3", moving)
        needs = section(report, "## Needs you now")
        self.assertIn("- WATER WP2: Blocked: Too Many Failed Reviews, because the user decides. You decide:", needs)

    def test_the_default_window_runs_from_the_last_report_at_least_an_hour_old(self):
        first = self.report()
        self.assertIn("# Build report, the last 24 hours (no earlier report)", first)
        self.assertEqual(len(json.loads(self.times().read_text())["at"]), 1)
        again = self.report()  # printed, then written a minute later: the same window
        self.assertIn("(no earlier report)", again)
        earlier = time.time() - 3 * 3600
        self.times().write_text(json.dumps({"at": [time.time() - 30 * 3600, earlier, time.time() - 60]}))
        later = self.report()
        self.assertIn(f"# Build report, since the last report, at {agent_loop.local_time(earlier)}", later)

    def test_since_takes_hours_or_a_time(self):
        self.assertIn("# Build report, the last 6 hours", self.report(since="6"))
        day = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
        start = time.mktime(time.strptime(day, "%Y-%m-%d"))
        self.assertIn(f"# Build report, since {agent_loop.local_time(start)}", self.report(since=day))
        with self.assertRaises(SystemExit) as bad:
            agent_loop.report_window(self.wt, "last tuesday")
        self.assertIn("--since takes hours, such as 24, or a time", str(bad.exception))
        with self.assertRaises(SystemExit):
            agent_loop.report_window(self.wt, "2999-01-01")

    def test_done_and_ready_for_review_and_verdicts_are_listed(self):
        commit = self.ready_for_review()
        self.git("pull", "-q", "--rebase", "origin", "main")
        ready = self.report(since=24.0)
        self.assertIn("Reached Ready for Review, and waiting for a review:", ready)
        self.assertIn("- WATER WP1: Ready for Review, ", ready)
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=commit)
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.report(since=24.0)
        self.assertIn("- WATER WP1: Done, by review", section(report, "## Done"))
        self.assertIn("- WATER WP1: pass (", section(report, "## Verdicts"))

    def test_write_puts_it_where_the_human_can_open_it_with_links_that_resolve(self):
        w1 = work_package("WP1", "in_progress", ["open"])
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        out = io.StringIO()  # a bare --write, which the test helpers' keyword form can't give
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_report(parse_argv(COMMANDS[agent_loop.cmd_report],
                                             ["--worktree", str(self.wt), "--since", "24", "--write"]))
        out = json.loads(out.getvalue())
        path = Path(out["written"])
        self.assertEqual(path.parent, agent_loop.loop_dir(self.wt) / "reports")
        body = path.read_text()
        link = body.split("[done-when file](")[1].split(")")[0]
        self.assertTrue((path.parent / link).resolve().samefile(self.wt / "docs/plans/WATER/DONE.json"), link)
        elsewhere = self.root / "for-the-human" / "report.md"
        out = json.loads(self.report(since=24.0, write=str(elsewhere)))
        self.assertTrue(Path(out["written"]).samefile(elsewhere))
        link = elsewhere.read_text().split("[done-when file](")[1].split(")")[0]
        self.assertEqual(link, "../wt/docs/plans/WATER/DONE.json")
        self.assertFalse(self.git("status", "--porcelain").stdout.strip(), "nothing lands in the checkout")

    def test_no_result_asks_for_a_report_a_day(self):
        result = self.run_loop()
        self.assertNotIn("report_due", result)
        self.assertFalse(hasattr(agent_loop, "report_due"))
        self.assertNotIn("build report", agent_loop.status_page(self.wt, agent_loop.profile(self.wt), "HEAD"))


if __name__ == "__main__":
    unittest.main()
