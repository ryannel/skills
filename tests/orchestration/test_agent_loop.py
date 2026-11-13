"""Checks for agent_loop's mechanical decisions: the acceptance record, the queue, claims, reviews, plans, owner
commands, profile, pins, locks and report lines. Hosts are fake executables; no model is launched.

Tests named after a review finding (astra_1, fable_3, ...) reproduce that finding from
workbench/review-2026-11-08 and check it no longer happens."""

import argparse
import contextlib
import io
import json
import os
import re
import shutil
import signal
import sqlite3
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import (PROFILE, SCRIPTS, Clean, Repo, agent_loop, done, item, milestone,  # noqa: E402
                     proved, put, release, shares)


def too_many(mid, statuses, **kw):
    """A milestone blocked after too many failed reviews, waiting for the human to decide."""
    return dict(milestone(mid, "blocked", statuses, **kw),
                blocked={"reason": "too_many_failed_reviews", "what": "the human decides"})


def needs(kind, what):
    """An item's `needs` field."""
    return {"type": kind, "what": what}


def failed_before(m):
    """A milestone whose last review failed every item, as a done-when file kept from before rounds kept their
    findings leaves it."""
    for i in m["items"]:
        i["verdict"] = "fail"
    return m


def entry_for(doc, design_ok=True):
    """A project entry as agent_loop.project builds it in a repository taking up the loop (finished milestones taken
    as they stand), with the design agreed unless told otherwise."""
    rec = agent_loop.adopt(doc, agent_loop.text_hash(None), as_it_stands=True)
    if design_ok:
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)}
    return {"stem": doc["module"], "doc": doc, "record": rec, "design": agent_loop.text_hash(None),
            "problems": agent_loop.validate(doc, doc["module"])}


class ProfileOnly(Clean):
    """A folder holding only the project settings, ORCHESTRATE.md, in a git repository with no commits."""

    def setUp(self):
        super().setUp()
        self.wt = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE)
        subprocess.run(["git", "init", "-q", str(self.wt)], check=True)


class Decisions(Clean):
    def test_what_the_counts_call_for(self):
        # failed reviews that repeat a finding: a new builder session at three, a diagnosis at four
        self.assertEqual([agent_loop.escalation(n, with_repeat=n) for n in range(6)],
                         ["none", "same_builder", "same_builder", "new_builder_session", "diagnosis", "diagnosis"])
        # every failed review counts: three start a new session even with nothing repeated, and six a diagnosis
        self.assertEqual([agent_loop.escalation(n) for n in range(1, 8)],
                         ["same_builder", "same_builder", "new_builder_session", "same_builder", "same_builder",
                          "diagnosis", "diagnosis"])
        # a milestone gets one diagnosis, so the same counts after it block the milestone
        self.assertEqual(agent_loop.escalation(4, with_repeat=4, diagnoses=1), "too_many_failed_reviews")
        self.assertEqual(agent_loop.escalation(6, with_repeat=1, diagnoses=1), "too_many_failed_reviews")
        self.assertEqual(agent_loop.escalation(2, with_repeat=2, diagnoses=1), "same_builder")

    def test_the_counts_from_before_2_2_become_one_diagnosis(self):
        for old, new in (
                ({"fails": 0, "replans": 0}, (0, 0, 0)),
                ({"fails": 2, "rounds": 3, "replans": 0}, (3, 2, 0)),
                ({"fails": 1, "replans": 1}, (1, 1, 1)),  # written before `rounds`, when only repeats were counted
                ({"fails": 0, "rounds": 2, "replans": 1, "diagnoses": 1}, (2, 0, 1)),  # a re-plan and a diagnosis are one
                # owed a re-plan or a diagnosis when it was migrated: still owed its diagnosis
                ({"fails": 4, "rounds": 4, "replans": 0, "diagnoses": 1}, (4, 4, 0)),
                ({"fails": 1, "rounds": 6, "replans": 1, "diagnoses": 0}, (6, 1, 0)),
                # it had used both, so it stays as stuck as it was
                ({"fails": 4, "rounds": 6, "replans": 1, "diagnoses": 1}, (6, 4, 1))):
            with self.subTest(old=old):
                m = {k: v for k, v in milestone("M1", "in_progress", ["open"]).items() if k not in agent_loop.COUNTS}
                doc = done(dict(m, **old))
                self.assertTrue(agent_loop.old_names_in_doc(doc))
                up = agent_loop.upgrade_doc(doc)
                self.assertEqual(tuple(up["milestones"][0][k] for k in agent_loop.COUNTS), new)
                self.assertEqual((agent_loop.old_names_in_doc(up), agent_loop.validate(up, "WATER")), ([], []))
        self.assertEqual(agent_loop.escalation_of({"failed_reviews": 6, "failed_reviews_with_repeat": 1}), "diagnosis")

    def test_a_finding_repeats_by_name_or_by_item_unless_it_says_how_it_differs(self):
        found = [{"name": "seams show", "item": "M1.1"}, {"name": "crash on load"},
                 {"name": "foam is grey", "item": "M1.2", "different": "M1.2 failed on speed before, colour now"},
                 {"name": "slow", "item": "M1.2"}]
        self.assertEqual(agent_loop.repeats(found, {"seams show", "crash on load"}, {"M1.2"}),
                         ["seams show", "crash on load", "slow"])
        self.assertEqual(agent_loop.repeats(found, set(), set()), [])

    def test_findings_are_checked(self):
        items = [{"id": "M1.1"}]
        ok = {"findings": [{"name": "seams show", "item": "M1.1"}, {"name": "crash", "different": "new"}]}
        self.assertEqual(agent_loop.findings_problems(ok, "M1", items), [])
        for bad, says in (({"findings": {"name": "x"}}, "should be a list"),
                          ({"findings": [{"item": "M1.1"}]}, "needs a short name"),
                          ({"findings": [{"name": "x"}, {"name": "x"}]}, "two findings are named"),
                          ({"findings": [{"name": "x", "item": "M9.9"}]}, "isn't one of M1's"),
                          ({"findings": [{"name": "x", "different": True}]}, "should be text")):
            self.assertTrue(any(says in p for p in agent_loop.findings_problems(bad, "M1", items)), bad)

    def test_plan_forecast_lasts_when_the_open_work_fits(self):
        acc = {"used_percent": 50.0, "hours_left": 100.0}
        history = [{"state": "done", "reviews": 3, "pct": [1.0, 1.2, 1.5]},
                   {"state": "done", "reviews": 1, "pct": [2.0, 2.4, 3.0]}]
        open_ms = [{"state": "not_started", "reviews": 1}] * 4
        recent = {"hours": 12.0, "loop": [1.0, 1.0, 1.0], "other": [0.6, 1.2, 1.8]}
        f = agent_loop.plan_forecast(acc, history, open_ms, recent)
        self.assertEqual(f["per_milestone"], [1.0, 1.8, 3.0])
        self.assertEqual(f["reviews_per_milestone"], 2.0)
        self.assertEqual(f["plan_pct"], [4.0, 7.2, 12.0])
        self.assertEqual(f["other_use_before_reset"], [5.0, 10.0, 15.0])  # at the last 12 h's rate, not the week's
        self.assertFalse(f["warn"])
        self.assertTrue(f["verdict"].startswith("Quota lasts"), f["verdict"])
        self.assertNotIn("runs_out", f)

    def test_plan_forecast_warns_only_when_it_wont_last(self):
        history = [{"state": "done", "reviews": 1, "pct": [4.0, 5.0, 6.0], "builder_hours": 2.0}] * 2
        recent = {"hours": 10.0, "loop": [1.0, 1.0, 1.0], "other": [0.0, 0.0, 0.0]}
        short = agent_loop.plan_forecast({"used_percent": 90.0, "hours_left": 100.0}, history,
                                         [{"state": "not_started"}] * 4, recent)  # 16-24 % against 10 % left
        self.assertTrue(short["warn"])
        self.assertTrue(short["verdict"].startswith("Quota runs short"), short["verdict"])
        self.assertEqual(short["plan_hours_one_builder"], 8.0)
        self.assertIn("runs_out", short)  # 2.5 %/h uses the 10 % up in four hours
        maybe = agent_loop.plan_forecast({"used_percent": 95.0, "hours_left": 100.0}, history,
                                         [{"state": "not_started"}], recent)  # 4-6 % against 5 % left
        self.assertTrue(maybe["warn"])
        self.assertTrue(maybe["verdict"].startswith("Quota may run short"), maybe["verdict"])

    def test_plan_forecast_says_too_little_data_without_history(self):
        acc = {"used_percent": 20.0, "hours_left": 100.0}
        recent = {"hours": 12.0, "loop": [0.0] * 3, "other": [0.0] * 3}
        f = agent_loop.plan_forecast(acc, [{"state": "not_started", "pct": [1, 1, 1]}], [{"state": "not_started"}] * 2, recent)
        self.assertIsNone(f["plan_pct"])
        self.assertFalse(f["warn"])
        self.assertIn("Too little data", f["verdict"])

    def test_quota_never_fails_the_result_line(self):
        with mock.patch.object(agent_loop.codex_quota, "read", side_effect=OSError("disk gone")):
            self.assertEqual(agent_loop.quota_now(), {"unavailable": "OSError: disk gone"})


    def test_report_word_reads_only_the_last_line(self):
        self.assertEqual(agent_loop.report_word("work\nevidence\nBLOCKED: no Metal device"), "BLOCKED")
        self.assertEqual(agent_loop.report_word("`DONE`"), "DONE")
        self.assertIsNone(agent_loop.report_word("DONE\nActually the milestone is not complete yet."))
        self.assertIsNone(agent_loop.report_word("still working"))

    def test_pin_mismatch_lists_wrong_turns_and_skips_partial_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            rollout = Path(tmp) / "rollout.jsonl"
            rollout.write_text("\n".join([
                json.dumps({"type": "turn_context", "payload": {"turn_id": "a", "model": "gpt-6.1-sol", "effort": "medium"}}),
                json.dumps({"type": "turn_context", "payload": {"turn_id": "b", "model": "gpt-6.1-sol", "effort": "xhigh"}}),
                '{"type": "turn_context", "payload": {"turn_id": "c", "mod']))
            self.assertEqual(agent_loop.pin_mismatches(rollout), ["b: gpt-6.1-sol/xhigh"])

    def test_definitions_ignore_claims_but_not_checks_or_needs(self):
        m = milestone("M1", "not_started", ["open"])
        before = agent_loop.definitions(m)
        m["items"][0].update(status="pass", evidence="log", verdict="pass")
        self.assertEqual(agent_loop.definitions(m), before)
        m["items"][0]["needs"] = needs("hardware", "plug in the phone")
        self.assertNotEqual(agent_loop.definitions(m), before)

    def test_last_milestone_and_inspected_milestones_need_review(self):
        d = done(milestone("M1", "not_started", ["pass"]), milestone("M2", "not_started", ["open"]))
        self.assertFalse(agent_loop.needs_review(d["milestones"][0], d))
        self.assertTrue(agent_loop.needs_review(d["milestones"][1], d))

    def test_validate_rejects_missing_proof_and_empty_milestones(self):
        bare = milestone("M1", "not_started", ["open"])
        del bare["items"][0]["check"]
        self.assertTrue(any("nothing proves it" in p for p in agent_loop.validate(done(bare))))
        self.assertTrue(any("no items" in p for p in agent_loop.validate(done(milestone("M1", "not_started", [])))))
        dup = done(milestone("M1", "not_started", ["open"]), milestone("M1", "not_started", ["open"]))
        self.assertTrue(any("duplicate" in p for p in agent_loop.validate(dup)))
        self.assertEqual(agent_loop.validate(done(milestone("M1", "not_started", ["open"]))), [])

    def test_astra_14_malformed_shapes_are_problems_not_crashes(self):
        for bad in ({"milestones": "bad"}, {"milestones": ["x"]}, [], {"milestones": [{"id": 3, "items": "no"}]},
                    done(dict(milestone("M1", "not_started", ["open"]), failed_reviews_with_repeat=-1)),
                    done(dict(milestone("M1", "not_started", ["open"]), items=[{"id": "a", "statement": "s", "check": 3}]))):
            self.assertTrue(agent_loop.validate(bad), bad)

    def test_fable_8_forward_and_self_needs_in_a_module_are_errors(self):
        d = done(dict(milestone("M1", "not_started", ["open"]), depends_on=["M2"]), milestone("M2", "not_started", ["open"]))
        self.assertTrue(any("comes at or after it" in p for p in agent_loop.validate(d, "WATER")))
        d = done(milestone("M1", "not_started", ["open"]), dict(milestone("M2", "not_started", ["open"]), depends_on=["M9"]))
        self.assertTrue(any("isn't in this module" in p for p in agent_loop.validate(d, "WATER")))
        ok = done(milestone("M1", "not_started", ["open"]), dict(milestone("M2", "not_started", ["open"]), depends_on=["M1", "CORE:M3"]))
        self.assertEqual(agent_loop.validate(ok, "WATER"), [])


class Queue(Clean):
    """next_step is the one readiness predicate behind ready, status and run."""

    def test_astra_2_a_done_state_without_accepted_review_doesnt_release_dependents(self):
        core = done(milestone("M1", "done", ["pass"], inspect="captures"), module="CORE")
        water = done(dict(milestone("M1", "not_started", ["open"]), depends_on=["CORE:M1"]))
        proj = {"CORE": entry_for(core), "WATER": entry_for(water)}
        self.assertEqual(agent_loop.next_step("CORE", proj)["status"], "review_owed")
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual((step["status"], step["depends_on"]), ("waiting", ["CORE:M1"]))

    def test_astra_2_a_forged_done_without_a_record_acceptance_isnt_accepted(self):
        water = done(milestone("M1", "not_started", ["open"]), milestone("M2", "not_started", ["open"]))
        e = entry_for(water)
        water["milestones"][0].update(state="done")  # written into the file, never accepted by the loop
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["milestone"], "M1")

    def test_astra_2_and_fable_17_open_milestone_with_passing_items_is_still_next(self):
        water = done(milestone("M1", "not_started", ["pass"]), milestone("M2", "not_started", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water)})["milestone"], "M1")
        water = done(milestone("M1", "in_progress", ["pass"]), milestone("M2", "not_started", ["open"]))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)})
        self.assertEqual((step["milestone"], step["status"]), ("M1", "ready"))

    def test_milestones_run_in_file_order_not_in_progress_first(self):
        water = done(milestone("M1", "done", ["pass"]), milestone("M2", "not_started", ["open"]),
                     milestone("M3", "in_progress", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water)})["milestone"], "M2")

    def test_fable_8_dependencies_on_too_many_failed_reviews_and_cycles_are_reported_not_waited_on(self):
        prk = done(too_many("M1", ["open"]), module="PRK")
        water = done(dict(milestone("M1", "not_started", ["open"]), depends_on=["PRK:M1"]))
        proj = {"PRK": entry_for(prk), "WATER": entry_for(water)}
        self.assertEqual(agent_loop.next_step("PRK", proj)["reason"], "too_many_failed_reviews")
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual(step["status"], "invalid")
        self.assertIn("Blocked: Too Many Failed Reviews", step["problems"][0])
        a = done(dict(milestone("M1", "not_started", ["open"]), depends_on=["B:M1"]), module="A")
        b = done(dict(milestone("M1", "not_started", ["open"]), depends_on=["A:M1"]), module="B")
        cycles = agent_loop.need_cycles({"A": entry_for(a), "B": entry_for(b)})
        self.assertEqual(set(cycles), {"A", "B"})

    def test_unplanned_module_is_waiting_and_missing_milestone_is_invalid(self):
        core = done(milestone("M1", "not_started", ["open"]), module="CORE")
        water = done(dict(milestone("M1", "not_started", ["open"]), depends_on=["PAY:M1"]))
        proj = {"WATER": entry_for(water), "CORE": entry_for(core)}
        self.assertEqual(agent_loop.next_step("WATER", proj)["depends_on"], ["PAY:M1 (not planned)"])
        water["milestones"][0]["depends_on"] = ["CORE:M7"]
        proj["WATER"] = entry_for(water)
        self.assertEqual(agent_loop.next_step("WATER", proj)["status"], "invalid")

    def test_design_review_gates_a_module(self):
        water = done(milestone("M1", "not_started", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water, design_ok=False)})["status"],
                         "design_not_approved")

    def test_blocked_and_taken(self):
        blocked = {"reason": "needs_hardware", "items": ["M1.1"], "what": "needs the iPhone"}
        water = done(dict(milestone("M1", "blocked", ["open"]), blocked=blocked))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)})
        self.assertEqual((step["status"], step["reason"], step["blocked"]), ("blocked", "needs_hardware", blocked))
        water["milestones"][0]["blocked"] = "needs the iPhone"  # text from before 2.0 is for migrate to convert
        self.assertTrue(any("migrate" in p or "blocked" in p for p in agent_loop.validate(water, "WATER")))
        water = done(milestone("M1", "not_started", ["open"]))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)}, {("WATER", "M1"): "other"}, "me")
        self.assertEqual((step["status"], step["by"]), ("taken", "other"))

    def test_unauthorised_definitions_are_invalid(self):
        water = done(milestone("M1", "not_started", ["open"]))
        e = entry_for(water)
        water["milestones"][0]["items"][0]["check"] = "true # weakened"
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["status"], "invalid")


class Deltas(Clean):
    def setUp(self):
        self.before = done(milestone("M1", "in_progress", ["open"]), milestone("M2", "not_started", ["open"]))

    def after(self):
        return json.loads(json.dumps(self.before))

    def test_builder_may_change_only_its_fields_on_its_milestone(self):
        a = self.after()
        a["milestones"][0]["state"] = "ready_for_review"
        a["milestones"][0]["items"][0].update(status="pass", evidence="log")
        self.assertEqual(agent_loop.delta_problems(self.before, a, "build", "M1"), [])
        a["milestones"][0]["diagnoses"] = 1
        self.assertTrue(agent_loop.delta_problems(self.before, a, "build", "M1"))

    def test_astra_1_builder_forging_another_milestone_is_caught(self):
        a = self.after()
        a["milestones"][1]["state"] = "done"
        a["milestones"][1]["items"][0].update(verdict="pass", status="pass")
        self.assertTrue(any("M2" in p for p in agent_loop.delta_problems(self.before, a, "build", "M1")))

    def test_rebased_upstream_changes_are_allowed(self):
        upstream = self.after()
        upstream["milestones"][1]["bar"] = "planner's new bar"
        a = json.loads(json.dumps(upstream))
        self.assertEqual(agent_loop.delta_problems(self.before, a, "build", "M1", upstream), [])

    def test_astra_4_reviewer_deleting_a_milestone_is_caught(self):
        before = done(milestone("M1", "ready_for_review", ["pass"]), milestone("M2", "not_started", ["open"]))
        a = done(milestone("M1", "done", ["pass"]))
        self.assertTrue(agent_loop.delta_problems(before, a, "review", "M1"))

    def test_a_reviewer_cant_set_the_counts(self):
        before = done(milestone("M1", "ready_for_review", ["pass"]))
        for field in ("failed_reviews", "failed_reviews_with_repeat", "diagnoses"):
            a = json.loads(json.dumps(before))
            a["milestones"][0].update(state="in_progress", **{field: 2})
            self.assertTrue(agent_loop.delta_problems(before, a, "review", "M1"), field)

    def test_planner_cant_grant_passes(self):
        a = self.after()
        a["milestones"][1]["state"] = "done"
        self.assertTrue(agent_loop.delta_problems(self.before, a, "plan"))


class Profiles(Clean):
    def test_profile_reads_labelled_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                "- **Plans:** [docs/design/modules](docs/design/modules/)  *(read by the loop)*\n"
                "- **Evidence:** docs/my evidence  *(loop)*\n"
                "- **Test command:** `npm run check < /dev/null`  *(loop)*\n"
                "- **Merge:** local  *(loop)*\n"
                "- **Branch:** trunk  *(loop: integrate here)*\n"
                "- **Codex sandbox:** danger-full-access  *(loop)*\n"
                "- **Codex generator:** gpt-6.1-sol, high\n- **Writable roots:** ~/.cargo, ~/.npm\n")
            p = agent_loop.profile(Path(tmp), strict=True)
            self.assertEqual((p["plans"], p["branch"], p["model"], p["effort"], p["evidence"], p["test_command"], p["sandbox"]),
                             ("docs/design/modules", "trunk", "gpt-6.1-sol", "high", "docs/my evidence",
                              "npm run check < /dev/null", "danger-full-access"))
            self.assertEqual(p["roots"], ["~/.cargo", "~/.npm"])
            self.assertEqual(p["graded_examples"], "docs/my evidence/graded-examples.md")

    def test_astra_7_and_fable_1_missing_integrate_or_check_fails_strict_and_never_defaults_to_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            for text in ("# profile\n", "- **Test command:** none\n", "- **Merge:** push\n"):
                Path(tmp, "ORCHESTRATE.md").write_text(text)
                with self.assertRaises(SystemExit, msg=text):
                    agent_loop.profile(Path(tmp), strict=True)
            Path(tmp, "ORCHESTRATE.md").write_text("# profile\n")
            with contextlib.redirect_stderr(io.StringIO()):
                loose = agent_loop.profile(Path(tmp))
            self.assertEqual((loose["merge"], loose["test_command"]), ("local", ""))
            Path(tmp, "ORCHESTRATE.md").write_text("- **Merge:** push\n- **Test command:** none\n")
            self.assertEqual(agent_loop.profile(Path(tmp), strict=True)["test_command"], "")

    def test_profile_strict_rejects_missing_unfilled_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                agent_loop.profile(Path(tmp), strict=True)
            good = "- **Merge:** push\n- **Test command:** none\n"
            for bad in ("- **Evidence:** <where review files go>\n", "- **Codex sandbox:** open\n",
                        "- **Codex generator:** gpt-6.1-sol turbo\n", "- **Merge:** pull-request\n- **Test command:** none\n"):
                Path(tmp, "ORCHESTRATE.md").write_text(good + bad if "Merge" not in bad else bad)
                with self.assertRaises(SystemExit, msg=bad):
                    agent_loop.profile(Path(tmp), strict=True)

    def test_profile_reads_hosts_models_and_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                "- **Claude model:** claude-opus-5-5\n- **Effort:** high\n- **Gemini model:** g-2\n"
                "- **Host gemini:** `gemini -p {prompt} -m {model}`\n- **Host bad:** gemini\n")
            with contextlib.redirect_stderr(io.StringIO()):
                p = agent_loop.profile(Path(tmp))
            self.assertEqual((p["models"]["codex"], p["models"]["claude"], p["models"]["gemini"], p["effort"]),
                             ("gpt-6.1-sol", "claude-opus-5-5", "g-2", "high"))
            self.assertEqual(p["hosts"], {"gemini": "gemini -p {prompt} -m {model}"})
            args, env = agent_loop.host_command("gemini", p, "g-2", "medium", Path(tmp), "do it now", None)
            self.assertEqual(args, ["gemini", "-p", "do it now", "-m", "g-2"])
            self.assertEqual(env["ORCHESTRATE_ROLE"], "build")
            with mock.patch.object(agent_loop, "claude_supports", lambda flag: True):
                new = agent_loop.host_command("claude", p, "m", "high", Path(tmp), "go", None, new_id="abc",
                                              title="thrum · WATER · M1 build")[0]
                resumed = agent_loop.host_command("claude", p, "m", "high", Path(tmp), "go", "abc",
                                                  title="thrum · WATER · M1 build")[0]
            self.assertEqual(new[new.index("--name") + 1], "thrum · WATER · M1 build")
            self.assertNotIn("--name", resumed)  # a resumed session keeps the name it started with

    def test_planner_host_sends_planners_to_that_host_unless_the_lead_names_one(self):
        base = "- **Merge:** local\n- **Test command:** none\n- **Default host:** codex\n"
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                base + "- **Planner host:** claude\n- **Claude planner:** claude-fable-5-2 high\n")
            p = agent_loop.profile(Path(tmp), strict=True)
        ns = lambda host=None: argparse.Namespace(host=host, model=None, effort=None)
        self.assertEqual(agent_loop.resolve(ns(), p, "plan"), ("claude", "claude-fable-5-2", "high"))
        self.assertEqual(agent_loop.resolve(ns(), p, "build")[0], "codex", "only planners move")
        self.assertEqual(agent_loop.resolve(ns("codex"), p, "plan"), ("codex", "gpt-6.1-sol", "high"))
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(base + "- **Planner host:** other\n")
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                agent_loop.profile(Path(tmp), strict=True)

    def test_profile_sets_model_and_effort_for_one_kind_of_agent(self):
        base = "- **Merge:** local\n- **Test command:** none\n"
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                base + "- **Claude model:** claude-opus-5-5\n- **Effort:** low\n"
                "- **Claude planner:** `claude-fable-5-2` xhigh  *(script)*\n- **Codex planner:** gpt-6-astra\n"
                "- **Codex reviewer:** high\n- **Claude design reviewer:** claude-fable-5-2\n"
                "- **Builder:** medium\n- **Claude builder:** <model>\n"
                "- **Host gemini:** gemini -p {prompt} -m {model}\n- **Gemini model:** g-3\n"
                "- **Gemini reviewer:** g-3-ultra, max\n")
            p = agent_loop.profile(Path(tmp), strict=True)
        json.dumps(p)  # the `profile` command prints the settings as JSON

        def launch(role, host, **flags):
            ns = argparse.Namespace(**{"host": host, "model": None, "effort": None, **flags})
            return agent_loop.resolve(ns, p, role)[1:]
        # a line with a host gives that host's model, effort or both; a planner's effort is high unless a line says
        self.assertEqual(launch("plan", "claude"), ("claude-fable-5-2", "xhigh"))
        self.assertEqual(launch("plan", "codex"), ("gpt-6-astra", "high"))
        self.assertEqual(launch("plan", "gemini"), ("g-3", "high"), "another host's model never crosses over")
        # a line with no host gives an effort on every host
        self.assertEqual(launch("build", "claude"), ("claude-opus-5-5", "medium"))
        self.assertEqual(launch("build", "codex"), ("gpt-6.1-sol", "medium"))
        # an effort alone keeps the host's model
        self.assertEqual(launch("review", "codex"), ("gpt-6.1-sol", "high"))
        self.assertEqual(launch("review", "claude"), ("claude-opus-5-5", "low"))
        self.assertEqual(launch("review", "gemini"), ("g-3-ultra", "max"))
        # a design review uses its own line, then the reviewer's
        self.assertEqual(launch("design", "claude"), ("claude-fable-5-2", "low"))
        self.assertEqual(launch("design", "codex"), ("gpt-6.1-sol", "high"))
        # what the lead passes still wins
        self.assertEqual(launch("plan", "claude", model="claude-haiku-5-5", effort="low"), ("claude-haiku-5-5", "low"))
        for bad in ("- **Planner:** claude-fable-5-2\n",          # a model with no host
                    "- **Antigravity planner:** gemini-3 high\n",  # a host this profile can't start
                    "- **Claude planner:** a b\n", "- **Reviewer:** high max\n"):
            with tempfile.TemporaryDirectory() as tmp:
                Path(tmp, "ORCHESTRATE.md").write_text(base + bad)
                with self.assertRaises(SystemExit, msg=bad), contextlib.redirect_stderr(io.StringIO()):
                    agent_loop.profile(Path(tmp), strict=True)

    def test_fable_10_default_host_follows_the_profile_then_the_running_host(self):
        prof = {"default_host": ""}
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            self.assertEqual(agent_loop.default_host(prof), "claude")
            self.assertEqual(agent_loop.default_host({"default_host": "gemini"}), "gemini")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        with mock.patch.dict(os.environ, {**env, "CODEX_THREAD_ID": "x"}, clear=True):
            self.assertEqual(agent_loop.default_host(prof), "codex")

    def test_fable_15_codex_reviewers_and_planners_cant_spawn_agents(self):
        prof = {"model": "m", "effort": "medium", "sandbox": "workspace-write", "roots": []}
        self.assertIn("features.multi_agent=false", agent_loop.codex_flags(prof, "review"))
        self.assertIn("features.multi_agent=false", agent_loop.codex_flags(prof, "plan"))
        self.assertNotIn("features.multi_agent=false", agent_loop.codex_flags(prof, "build"))

    def test_holistic_5_no_prompt_template_names_a_model_or_effort(self):
        values = dict(goal=agent_loop.GOAL_LINE, milestone="M1", module="W", done="d", loop="l", skill="s", commit="c",
                      review="r", task="t", evidence="e", captures="r-captures", answers="", changed="", briefs="",
                      lead="", feedback="", needs="", rules="", resources="", session="", handoff="h", earlier="", checks="")
        for name in ("BUILD_TEMPLATE", "REVIEW_TEMPLATE", "DESIGN_REVIEW_TEMPLATE", "PLAN_TEMPLATE",
                     "FINDINGS_TEMPLATE"):
            template = getattr(agent_loop, name)
            self.assertNotIn("{model}", template, name)
            self.assertNotIn("{effort}", template, name)
            text = template.format(**values).lower()
            for word in ("effort", "gpt-6", "opus", "launched on"):
                self.assertNotIn(word, text, f"{name} mentions {word}")
        self.assertTrue(agent_loop.BUILD_TEMPLATE.format(**values).startswith(agent_loop.GOAL_LINE + "Build milestone M1 of module W,"))

    def test_fable_16_prompts_carry_the_skill_path_for_hosts_without_skills(self):
        self.assertIn(str(SCRIPTS.parents[1] / "build-milestone" / "SKILL.md"), agent_loop.skill_note("build-milestone"))

    def test_claude_environment_drops_keys_but_keeps_config_dir(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x", "CLAUDE_CONFIG_DIR": "/c", "CLAUDECODE": "1",
                                          "CLAUDE_CODE_OAUTH_TOKEN": "plan"}):
            env = agent_loop.clean_env("review")
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual(env["CLAUDE_CODE_OAUTH_TOKEN"], "plan")
        self.assertEqual((env["CLAUDE_CONFIG_DIR"], env["ORCHESTRATE_ROLE"]), ("/c", "review"))

    def test_claude_stream_parsing(self):
        out = "\n".join(json.dumps(e) for e in [
            {"type": "system", "subtype": "init", "session_id": "s9", "model": "claude-opus-5-5"},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "working"}]}},
            {"type": "result", "result": "BLOCKED: no device", "is_error": False}])
        self.assertEqual(agent_loop.parse_output("claude", out), ("s9", "BLOCKED: no device", "claude-opus-5-5", False))

    def test_usage_is_read_from_each_hosts_own_output(self):
        claude = "\n".join(json.dumps(e) for e in [
            {"type": "assistant", "message": {"content": [], "usage": {"input_tokens": 999}}},
            {"type": "result", "result": "DONE", "total_cost_usd": 0.25, "usage": {
                "input_tokens": 100, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 4000,
                "output_tokens": 30}}])
        self.assertEqual(agent_loop.usage_of("claude", claude),
                         {"input": 150, "cached": 4000, "output": 30, "cost_usd": 0.25, "turns": 1})
        codex = "\n".join(json.dumps(e) for e in [
            {"type": "thread.started", "thread_id": "t1"},
            {"type": "turn.completed", "usage": {"input_tokens": 5000, "cached_input_tokens": 4200,
                                                 "output_tokens": 70}}])
        self.assertEqual(agent_loop.usage_of("codex", codex), {"input": 800, "cached": 4200, "output": 70, "turns": 1})

    def test_missing_usage_stays_missing(self):
        self.assertEqual(agent_loop.usage_of("gemini", '{"type": "result", "usage": {"input_tokens": 5}}'), {})
        self.assertEqual(agent_loop.usage_of("claude", 'not json\n{"type": "result", "result": "DONE"}'), {})
        self.assertEqual(agent_loop.add_usage({"input": 1, "turns": 2}, {}), {"input": 1, "turns": 2})

    def test_usage_adds_up_across_turns(self):
        total = agent_loop.add_usage(None, {"input": 10, "cached": 5, "output": 2, "cost_usd": 0.1, "turns": 1})
        total = agent_loop.add_usage(total, {"input": 1, "cached": 0, "output": 3, "cost_usd": 0.2, "turns": 1})
        self.assertEqual(total, {"input": 11, "cached": 5, "output": 5, "cost_usd": 0.3, "turns": 2})


class Processes(Clean):
    def test_fable_6_a_pause_stops_the_whole_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "child"
            threading.Timer(0.1, lambda: setattr(agent_loop, "_STOP", True)).start()
            started = time.time()
            code, _, _ = agent_loop.run_proc(["sh", "-c", f"sleep 30 & echo $! > {pidfile}; wait"], None, 60)
            self.assertEqual(code, 130)
            self.assertLess(time.time() - started, 15)
            pid = int(pidfile.read_text())
            time.sleep(0.2)
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_a_host_that_ignores_sigterm_is_killed_at_the_turn_limit(self):
        pidfile = Path(self.enterContext(tempfile.TemporaryDirectory())) / "host"
        agent_loop.KILL_GRACE_S = (0.2, 0.2)
        started = time.time()
        code, _, _ = agent_loop.run_proc(["sh", "-c", f"trap '' TERM; echo $$ > {pidfile}; sleep 30 & wait"], None, 0.3)
        self.assertEqual(code, 124)
        self.assertLess(time.time() - started, 8)  # SIGKILL after the grace, not the 10 s a real run waits
        time.sleep(0.2)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(pidfile.read_text()), 0)

    def test_astra_13_a_missing_cli_is_a_controlled_result(self):
        self.assertEqual(agent_loop.run_proc(["/no/such/host"], None, 5)[0], 127)

    def test_a_background_process_holding_the_output_does_not_hold_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "child"
            started = time.time()
            code, out, _ = agent_loop.run_proc(["sh", "-c", f"sleep 30 & echo $! > {pidfile}; echo hi"], None, 60)
            self.assertEqual((code, out.strip()), (0, "hi"))
            self.assertLess(time.time() - started, 10)
            time.sleep(0.2)
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pidfile.read_text()), 0)

    def test_a_watch_ends_a_run_whose_turn_is_over(self):
        seen = []
        watch = lambda new: (seen.append(new), "turn over" if "x" in "".join(seen) else None)[1]  # noqa: E731
        started = time.time()
        code, out, err = agent_loop.run_proc(["sh", "-c", "echo x; sleep 30"], None, 60, watch=watch)
        self.assertEqual((code, out.strip()), (0, "x"))
        self.assertIn("(turn over)", err)
        self.assertLess(time.time() - started, 15)

    def test_a_codex_turn_that_completed_ends_without_its_process_exiting(self):
        with tempfile.TemporaryDirectory() as tmp:
            thread = "01a1c92f-78db-75d1-9c22-4905c9aafe72"
            day = Path(tmp) / "sessions" / "2026" / "11" / "11"
            day.mkdir(parents=True)
            rollout = day / f"rollout-2026-11-11T06-58-13-{thread}.jsonl"
            events = [{"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t1"}},
                      {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": "t1",
                                                        "last_agent_message": "DONE: M1 is claimed"}}]
            with mock.patch.object(agent_loop, "CODEX_HOME", Path(tmp)), \
                    mock.patch.object(agent_loop, "SETTLE_S", 0.0):
                watch = agent_loop.HeadlessWatch("codex", None)
                self.assertIsNone(watch('{"type":"thread.started","thread_id":"%s"}\n' % thread))
                self.assertEqual(watch.session, thread)
                rollout.write_text(json.dumps(events[0]) + "\n")
                self.assertIsNone(watch(""))
                with open(rollout, "a") as f:
                    f.write(json.dumps(events[1]) + "\n")
                self.assertIn("hadn't exited", watch("") or "")
                self.assertEqual(watch.message, "DONE: M1 is claimed")

    def test_a_resumed_codex_thread_does_not_end_on_its_earlier_turns(self):
        with tempfile.TemporaryDirectory() as tmp:
            thread = "01a1c92f-78db-75d1-9c22-4905c9aafe73"
            day = Path(tmp) / "sessions" / "2026" / "11" / "11"
            day.mkdir(parents=True)
            (day / f"rollout-x-{thread}.jsonl").write_text(json.dumps(
                {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": "old"}}) + "\n")
            with mock.patch.object(agent_loop, "CODEX_HOME", Path(tmp)), \
                    mock.patch.object(agent_loop, "SETTLE_S", 0.0):
                self.assertIsNone(agent_loop.HeadlessWatch("codex", thread)(""))

    def test_a_codex_call_open_in_the_rollout_stops_the_turn_and_a_shell_command_doesnt(self):
        thread = "01a1c92f-78db-75d1-9c22-4905c9aafe74"
        home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        agent_loop.CODEX_HOME = home
        day = home / "sessions" / "2026" / "11" / "12"
        day.mkdir(parents=True)
        rollout = day / f"rollout-2026-11-12T09-00-00-{thread}.jsonl"
        rollout.write_text("")

        def add(payload):
            with open(rollout, "a") as f:
                f.write(json.dumps({"type": "response_item", "payload": payload}) + "\n")
        with mock.patch.object(agent_loop, "TOOL_CALL_LIMIT_S", 0.0):
            watch = agent_loop.HeadlessWatch("codex", thread)
            add({"type": "custom_tool_call", "name": "exec", "call_id": "c1",
                 "input": 'text(await tools.exec_command({cmd:"./dev check"}))'})
            add({"type": "function_call", "name": "sleep", "namespace": "clock", "call_id": "c0",
                 "arguments": '{"duration_ms":45000}'})
            self.assertIsNone(watch(""))
            time.sleep(0.05)
            self.assertIsNone(watch(""))  # a shell command and a sleep can rightly run long
            add({"type": "function_call", "namespace": "mcp__cua_repl", "name": "js", "call_id": "c2",
                 "arguments": '{"code":"await cua.getApp(\'Thrum\')","title":"Finding the game window"}'})
            said = watch("") or (time.sleep(0.05) or watch(""))
        self.assertIn("the tool call mcp__cua_repl.js had been open for", said)
        stop = agent_loop.stopped_turn(watch, 0, 7200)
        self.assertEqual((stop["tool_call"]["name"], stop["tool_call"]["open"]), ("mcp__cua_repl.js", True))
        self.assertIn("cua.getApp", stop["tool_call"]["input"])
        self.assertIn("15-minute limit", stop["why"])

    def test_a_turn_stopped_at_the_turn_limit_names_the_last_open_tool_call(self):
        watch = agent_loop.HeadlessWatch("claude", "s1")
        self.assertIsNone(watch(json.dumps({"type": "assistant", "session_id": "s1", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "./dev capture --realtime"}}]}})
                                + "\n"))
        stop = agent_loop.stopped_turn(watch, 124, 7200)
        self.assertEqual(stop["why"], "the turn reached the 2-hour turn limit")
        self.assertEqual((stop["tool_call"]["name"], stop["tool_call"]["open"]), ("Bash", True))
        self.assertIn("./dev capture --realtime", stop["tool_call"]["input"])
        facts = agent_loop.resume_facts(Path(self.enterContext(tempfile.TemporaryDirectory())), None, 124, 2.0,
                                       stop=stop)
        self.assertIn("reached the 2-hour turn limit and was stopped, while the tool call Bash was open", facts)
        self.assertEqual(agent_loop.stopped_turn(watch, 0, 7200), {})  # a turn the script didn't stop


class Building(Repo):
    def test_quota_costs_the_loops_milestones_and_counts_other_threads_apart(self):
        import test_codex_quota as fixtures
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")  # M1, in the fake host's thread t1
        ledger = (self.wt / ".git/orchestrate/threads.jsonl").read_text()
        self.assertIn('"thread": "t1"', ledger)
        now = fixtures.NOW
        builder = fixtures.Rollout(self.home, "t1", now - 10 * 3600, cwd=str(self.wt), origin="codex_exec",
                                   source="exec")
        builder.turn("b1", now - 10 * 3600, now - 6 * 3600,
                     [(now - 10 * 3600 + i * 600, 2_000_000, i) for i in range(1, 21)])  # about 20 % at 0.5 %/M
        mine = fixtures.Rollout(self.home, "owner", now - 5 * 3600, name="Clouds")
        mine.turn("o1", now - 5 * 3600, now - 3 * 3600, [(now - 5 * 3600 + i * 600, 2_000_000, 20 + i)
                                                         for i in range(1, 11)])
        guard = fixtures.Rollout(self.home, "g", now - 9 * 3600, cwd=str(self.wt), origin="codex_exec",
                                 source={"subagent": {"other": "guardian"}})
        guard.turn("g1", now - 9 * 3600, now - 9 * 3600 + 60, [(now - 9 * 3600 + 30, 10_000, None)],
                   model="codex-auto-review", effort="low")
        reading = agent_loop.codex_quota.read(budget_s=10, home=self.home, cache=False, now=now)
        own = agent_loop.loop_threads(self.wt, reading)
        self.assertEqual(own["t1"]["milestone"], "M1")
        self.assertEqual(own["g"]["milestone"], "M1")  # the auto-review served the builder
        self.assertNotIn("owner", own)
        acc = agent_loop.quota_report(self.wt, reading=reading)
        m1 = next(m for m in acc["milestones"] if m["milestone"] == "M1")
        self.assertTrue(m1["pct"][0] <= 20 <= m1["pct"][2], m1)
        self.assertEqual(acc["forecast"]["open_milestones"], 1)
        use = acc["use_this_window"]
        self.assertTrue(use["other_local_pct"][0] <= 10 <= use["other_local_pct"][2], use)
        self.assertEqual(use["other_local_threads"][0]["name"], "Clouds")
        summary = agent_loop.quota_summary(acc)
        self.assertEqual(set(summary) - {"runs_out", "note"}, {"rate", "used_percent", "resets_at", "burn", "verdict",
                                                                "warn", "detail"})
        rate = acc["rate"]
        self.assertEqual(rate["left_pct"], round(100 - acc["used_percent"], 1))
        self.assertTrue(rate["left_at_reset_pct"][0] <= rate["left_at_reset_pct"][2], rate)
        self.assertTrue(summary["rate"].startswith(f"{rate['left_pct']:.0f}% left and "), summary["rate"])
        self.assertTrue(agent_loop.quota_text(acc).startswith(summary["rate"]))
        bare = Path(self.enterContext(tempfile.TemporaryDirectory()))  # a checkout with no settings or plans
        subprocess.run(["git", "init", "-q", str(bare)], check=True)
        subprocess.run(["git", "-C", str(bare), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "start"], check=True)
        blind = agent_loop.quota_report(bare, reading=reading)["forecast"]
        self.assertIsNone(blind["open_milestones"])
        self.assertIn("No milestone forecast: no plans found", blind["verdict"])

    def test_a_script_checkout_whose_git_entry_is_gone_is_made_again(self):
        tree = agent_loop.verify_tree(self.wt, "WATER", "origin/main")
        shutil.rmtree(self.wt / ".git/worktrees" / tree.name)  # as a crash or a prune elsewhere can leave it
        put(self.wt / "later.txt", "later")
        self.commit_all()
        again = agent_loop.verify_tree(self.wt, "WATER", "origin/main")
        self.assertEqual(again, tree)
        self.assertEqual(agent_loop.head_commit(again), self.git("rev-parse", "origin/main").stdout.strip())
        self.assertTrue((again / "later.txt").exists())
        self.assertEqual(self.git("status", "--porcelain", where=again).stdout, "")

    def ready_problems(self, m1, test_command="none", leave=None):
        """Why the script won't set M1 to Ready for Review, once a builder has merged it as given. `leave` changes
        the worktree after the merge."""
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", test_command))
        self.write_done([proved(m1), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        prof = agent_loop.profile(self.wt, strict=True)
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        authorised = json.loads((self.wt / "docs/plans/WATER/ACCEPTED.json").read_text())["milestones"]["M1"]
        if leave:
            leave()
        return "; ".join(agent_loop.ready_problems(self.wt, prof, "WATER", doc["milestones"][0], doc,
                                                   authorised["definitions"], agent_loop.head_commit(self.wt))[0])

    def test_the_script_sets_ready_for_review_only_on_a_clean_merged_tree_whose_checks_pass(self):
        passed = lambda **proof: milestone("M1", "in_progress", ["pass"], **proof)  # noqa: E731
        cases = [
            ("an uncommitted change", dict(leave=lambda: put(self.wt / "ORCHESTRATE.md", "changed")),
             "uncommitted"),
            ("an untracked file", dict(leave=lambda: (self.wt / "helper.sh").write_text("echo hi\n")), "untracked"),
            ("a failing test command", dict(test_command="`sh -c 'exit 4'`"), "Test command `sh -c 'exit 4'` exited 4"),
            ("a check that leaves files", dict(), "left changes")]
        for name, kw, reason in cases:
            with self.subTest(name):
                self.setUp()
                m1 = passed(check="touch new-helper") if name == "a check that leaves files" else passed()
                self.assertIn(reason, self.ready_problems(m1, **kw))
        with self.subTest("all clear"):
            self.setUp()
            self.assertEqual(self.ready_problems(passed()), "")

    def test_claims_check_only_milestone_and_accepts_it_in_the_record(self):
        """The one plain headless Codex builder turn through to Ready for Review, and what it records."""
        (self.wt / "AGENTS.md").write_text("rules")
        self.commit_all()
        # a Claude version on the binary: the profile's default host is codex, so the Claude CLI isn't checked
        os.environ.update(FAKE_VERSION="2.1.239 (Claude Code)")
        result = self.run_loop(effort="high")  # the fake codex prints no turn.completed
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", False))
        self.assertEqual((result["path"], self.calls()[0]["argv"][0]), ("headless", "exec"))  # no Codex app here
        self.assertTrue(result["path_reason"])
        self.assertIn("quota", result)
        self.assertFalse([w for w in result.get("warnings", []) if "AGENTS.md" in w])  # codex reads AGENTS.md
        record = self.read_record()["milestones"]["M1"]
        self.assertEqual(record["accepted"]["by"], "checks")
        claim = record["ready_for_review"]  # no rollout, so nothing observed
        self.assertEqual((claim["effort"], claim["observed"], claim["cli"], claim["path"]),
                         ("high", {}, "2.1.239 (Claude Code)", "headless"))
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M2")
        agent_loop.sync_holds(self.wt, agent_loop.profile(self.wt, strict=True))
        self.assertNotIn(("WATER", "M1"), agent_loop.holds(self.wt))  # the claim is released once accepted
        self.assertEqual(agent_loop.ledger_rows(self.wt)[0]["usage"], {"incomplete_turns": 1})
        self.assertIn("showed no tokens or only some",
                      agent_loop.cost_line(agent_loop.cost_of(agent_loop.ledger_rows(self.wt))["total"]))

    def test_astra_1_weakening_a_check_and_bumping_replans_is_invalid_and_stays_invalid(self):
        self.write_done([milestone("M1", "not_started", ["open"], check="test -f real-proof"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_WEAKEN="1")
        result = self.run_loop()
        self.assertEqual(result["result"], "INVALID")
        # The weakened file reached the tip, but the authorised hash is in the record, so a fresh session or a
        # different host can't pick the weakened definitions up as new ones.
        os.environ.pop("FAKE_WEAKEN")
        again = self.run_loop(fresh=True)
        self.assertEqual(again["result"], "INVALID")
        self.assertIn("aren't the ones last authorised", again["problems"][0])

    def test_astra_1_forging_a_later_milestone_while_building_is_invalid(self):
        os.environ.update(FAKE_FORGE="1")
        result = self.run_loop()
        self.assertEqual(result["result"], "INVALID")
        self.assertTrue(any("M2" in p for p in result["problems"]))

    def test_astra_2_milestone_flag_doesnt_skip_an_earlier_milestone(self):
        result = self.run_loop(milestone="M2")
        self.assertEqual((result["result"], result["milestone"]), ("WAITING", "M2"))
        self.assertFalse(self.log.exists())

    def test_astra_5_checks_run_on_the_integrated_tip_not_an_older_ancestor(self):
        self.write_done([milestone("M1", "not_started", ["open"], check="test ! -f broken"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_UPSTREAM_BREAK="1")
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "NO_PROGRESS_FOR_HOURS")
        self.assertIn("M1.1 `test ! -f broken` exited 1", self.state()["not_ready_reasons"])

    def test_invalid_file_stops_before_any_turn(self):
        bare = milestone("M1", "not_started", ["open"])
        del bare["items"][0]["check"]
        self.write_done([bare], authorise=False)
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "INVALID")
        self.assertFalse(self.log.exists())

    def test_astra_14_unparseable_done_when_file_is_invalid_not_a_crash(self):
        put(self.wt / "docs/plans/WATER/DONE.json", "{not json")
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "INVALID")

    def test_done_without_a_claim_never_finishes_as_done(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "CHECKS_FAILED")
        self.assertIn("items not yet pass", result["reasons"][0])
        self.assertEqual(len(self.calls()), 3)

    def test_builder_done_on_reviewed_milestone_is_not_a_claim(self):
        os.environ.update(FAKE_STATE="done")
        self.write_done([milestone("M1", "not_started", ["open"], inspect="captures"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop(budget_hours=0.0)
        # the builder's done counts for nothing: the script checks the work and sets the state, so it still gets reviewed
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True), result)
        self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")

    def test_a_milestone_ready_for_review_holds_the_next_until_reviewed(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="captures"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        result = self.run_loop()
        self.assertEqual((result["result"], result["milestone"]), ("REVIEW_OWED", "M1"))

    def test_design_owed_holds_the_module(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        self.assertEqual(self.run_loop(no_design_review=True)["result"], "DESIGN_NOT_APPROVED")
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design")["verdict"], "DESIGN OK")
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")

    def test_a_design_review_runs_from_a_worktree_behind_the_plan(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()  # a planner's merge
        behind = Path(self.enterContext(tempfile.TemporaryDirectory())) / "behind"
        self.git("worktree", "add", "-q", "--detach", str(behind), "HEAD~1")
        shutil.rmtree(behind / "docs/plans/WATER", ignore_errors=True)  # as before WATER was planned
        os.environ.update(FAKE_REVIEW="design")
        result = self.review("design", worktree=str(behind))
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(result.get("verdict"), "DESIGN OK", result)

    def test_a_plan_revised_before_its_design_review_is_authorised_by_that_review(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        self.review("design")  # the record adopts the first definitions here
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.write_done([milestone("M1", "not_started", ["open"], check="test -n revised")], authorise=False)
        (self.wt / "docs/evidence/WATER/design-review.md").unlink()  # the fake reviewer rewrites the same text
        self.commit_all()
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "INVALID")  # revised outside a planner turn
        os.environ.update(FAKE_REVIEW="design")
        second = self.review("design")
        self.assertEqual(second.get("verdict"), "DESIGN OK", second)
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        self.assertEqual(self.read_record()["milestones"]["M1"]["authorised"]["by"], "design review")

    def test_blocked_report_records_blocked_state_and_unblock_requeues(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device attached")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        m1 = self.read_done()["milestones"][0]
        m1["blocked"].pop("work", None)
        self.assertEqual((m1["state"], m1["blocked"]), ("blocked", {"reason": "needs_context",
                                                                    "what": "no device attached"}))
        self.assertEqual(self.ready()["blocked"][0]["blocked"]["what"], "no device attached")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_unblock(argparse.Namespace(module="WATER", milestone="M1", worktree=str(self.wt)))
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M1")

    def test_items_that_need_someone_are_batched_into_the_blocked_reason(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"]), items=[
            item("M1.1"), item("M1.2", inspect="on the phone", needs=needs("hardware", "plug in the iPhone"))]),
            milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_REPLY="BLOCKED: the iPhone item needs a person")
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "needs_hardware"), result)
        self.assertEqual(self.read_done()["milestones"][0]["blocked"]["items"], ["M1.2"])
        self.assertTrue(result["next"]["command"].startswith("ORCHESTRATE_VISIBLE=1 "), result["next"])

    def test_a_headless_run_does_the_other_items_then_blocks_on_an_access_item(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"]), items=[
            item("M1.1"), item("M1.2", inspect="the app", needs=needs("access", "approve Computer Use for IINA"))]),
            milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_STATE="in_progress")
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "needs_access"), result)
        m1 = self.read_done()["milestones"][0]
        self.assertEqual([i["status"] for i in m1["items"]], ["pass", "open"])
        self.assertEqual((m1["blocked"]["reason"], m1["blocked"]["items"]), ("needs_access", ["M1.2"]))
        self.assertIn("approve Computer Use for IINA", m1["blocked"]["what"])
        self.assertEqual(len(self.calls()), 1)  # nobody is asked to confirm anything; the visible run is next
        self.assertTrue(result["next"]["command"].startswith("ORCHESTRATE_VISIBLE=1 "), result["next"])
        refused = self.refused_feedback("M1", ["M1.2"])  # access is done at the machine, so no reply is recorded
        self.assertIn("ORCHESTRATE_VISIBLE=1", refused)
        os.environ.pop("FAKE_STATE")

    def test_second_blocked_report_with_an_active_goal_finishes(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        self.assertEqual(len(self.calls()), 2)

    def test_a_block_with_a_reason_finishes_at_once_and_pauses_the_goal(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED needs_dependency: CORE has no save API yet")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.goal_changes, ["paused"])

    def test_a_block_merges_the_builders_handoff_and_the_next_session_is_told(self):
        os.environ.update(FAKE_PASS="0", FAKE_HANDOFF="Tried the CORE save path; it isn't there.",
                          FAKE_REPLY="NEEDS_CONTEXT: which CORE call saves a game; see the handoff")
        result = self.run_loop()
        self.assertEqual(result["result"], "BLOCKED")
        self.assertEqual(result["blocked"]["handoff"], "docs/evidence/WATER/M1-handoff.md")
        self.assertEqual(self.git("show", "origin/main:docs/evidence/WATER/M1-handoff.md").stdout,
                         "Tried the CORE save path; it isn't there.")
        self.assertIn("docs/evidence/WATER/M1-handoff.md", result["next"]["alternative"])
        self.assertIn("docs/evidence/WATER/M1-handoff.md", result["next"]["why"])
        self.git("checkout", "-q", "--", ".")
        self.git("clean", "-qfd")
        os.environ.pop("FAKE_HANDOFF")
        os.environ.update(FAKE_REPLY="BLOCKED: still stuck")
        self.run_loop(fresh=True, message="CORE has the API now")
        self.assertIn("left a handoff at docs/evidence/WATER/M1-handoff.md", self.prompt(self.calls()[-1]))

    def test_paused_goal_stops_before_dispatching_another_turn(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'paused')")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        self.assertEqual(len(self.calls()), 1)

    def test_a_changed_pin_starts_a_fresh_session(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop()
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Codex generator:** gpt-6.1-sol high\n")
        self.commit_all()
        self.run_loop()
        self.assertNotIn("resume", self.calls()[-1]["argv"])

    def test_astra_13_missing_host_cli_is_floor_with_the_reason(self):
        agent_loop.CODEX = "/no/such/codex"
        result = self.run_loop()
        self.assertEqual(result["result"], "HOST_FAILED")
        self.assertIn("couldn't start", result["reason"])

    def test_claude_builder_claims_with_a_clean_environment(self):
        """The one plain headless Claude builder turn through to Ready for Review, and what it records."""
        (self.wt / "AGENTS.md").write_text("rules")
        self.commit_all()
        os.environ.update(FAKE_VERSION="2.1.239 (Claude Code)")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret"}):
            result = self.run_loop(host="claude", effort="high")
        self.assertEqual(result["result"], "READY_FOR_REVIEW", "an AGENTS.md warning, not a failure")
        self.assertNotIn("quota", result)  # quota is Codex's
        call = self.calls()[0]
        self.assertFalse(call["api_key"])
        self.assertEqual(call["argv"][call["argv"].index("--model") + 1], "claude-opus-5-5")
        self.assertEqual(call["argv"][call["argv"].index("--effort") + 1], "high")
        self.assertNotIn("high", self.prompt(call))  # model and effort are in the launch record, never the prompt
        claim = self.read_record()["milestones"]["M1"]["ready_for_review"]
        self.assertEqual({k: claim[k] for k in ("host", "model", "effort", "cli", "observed")},
                         {"host": "claude", "model": "claude-opus-5-5", "effort": "high",
                          "cli": "2.1.239 (Claude Code)", "observed": {"model": "claude-opus-5-5"}})
        # this Claude CLI doesn't read AGENTS.md, and the warning names the binary the launch used
        agents = [w for w in result["warnings"] if "AGENTS.md" in w]
        self.assertEqual(len(agents), 1)
        self.assertIn("2.1.239", agents[0])
        self.assertIn("`@AGENTS.md`", agents[0])
        self.assertIn(agent_loop.CLAUDE, agents[0])

    def test_waiting_when_needs_are_unmet(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"]), depends_on=["CORE:M1"])])
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "WAITING")

    def test_fable_23_rebased_upstream_commits_are_not_the_builders_progress(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        (other / "src").mkdir()
        (other / "src/water.rs").write_text("someone else's work")
        self.git("add", "-A", where=other)
        self.git("-c", "user.name=o", "-c", "user.email=o@o", "commit", "-qm", "other module", where=other)
        self.git("push", "-q", "origin", "main", where=other)
        _, seen = agent_loop.own_progress(self.wt, 10 ** 9, "docs/plans")
        self.git("pull", "-q", "--rebase", "origin", "main")
        moved, seen = agent_loop.own_progress(self.wt, seen, "docs/plans")
        self.assertFalse(moved)
        (self.wt / "mine.txt").write_text("mine")
        self.git("add", "-A")
        self.git("commit", "-qm", "mine")
        self.assertTrue(agent_loop.own_progress(self.wt, seen, "docs/plans")[0])


class Reviewing(Repo):
    def setUp(self):
        super().setUp()
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frame sequence"), milestone("M2", "not_started", ["open"])])
        self.commit_all()

    def claim(self):
        """M1 Ready for Review, written as the script leaves it after its checks pass."""
        return self.ready_for_review()

    def test_a_passing_review_lands_and_accepts(self):
        result = self.run_loop()  # the one review test that starts from a builder's real turn
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True))
        commit = result["commit"]
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"]), ("REVIEWED", "PASS"))
        rec = self.read_record()["milestones"]["M1"]
        # the reviewer judged the script's commit that set Ready for Review, which follows the builder's work
        reviewed = rec["accepted"]["commit"]
        self.assertEqual(rec["accepted"]["by"], "review")
        self.assertEqual(self.git("merge-base", "--is-ancestor", commit, reviewed).returncode, 0)
        self.assertEqual(agent_loop.state_at(self.wt, reviewed, "docs/plans/WATER/DONE.json", "M1"), "ready_for_review")
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M2")

    def test_fable_3_a_failed_review_resets_the_items_that_failed(self):
        commit = self.run_loop()["commit"]  # a builder's real turn, whose session t1 the findings resume
        os.environ.update(FAKE_REVIEW="fail")
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"], result["failed_reviews_with_repeat"], result["failed_reviews"], result["escalation"]),
                         ("REVIEWED", "FAIL", 0, 1, "same_builder"))
        self.assertEqual(result["next"]["escalation"], "same_builder")
        self.assertIn(" run --module WATER ", result["next"]["command"])
        self.assertIn("--message", result["next"]["command"])
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["items"][0]["status"], m1["items"][0]["evidence"]), ("in_progress", "open", ""))
        self.assertEqual(m1["items"][0]["verdict"], "fail")
        # The builder resumes its session with the findings, in its worktree.
        os.environ.pop("FAKE_REVIEW")
        self.run_loop(message="FINDINGS")
        last = self.calls()[-1]
        self.assertEqual(last["argv"][last["argv"].index("resume") + 1], "t1")
        self.assertIn("--add-dir", last["argv"][:last["argv"].index("resume")])
        self.assertTrue(last["argv"][-1].startswith("FINDINGS"), last["argv"][-1][:300])

    def test_the_script_blocks_a_milestone_that_keeps_failing_after_its_diagnosis(self):
        commit = self.ready_for_review(failed_before(dict(milestone("M1", "not_started", ["open"], inspect="frames"),
                                                          failed_reviews_with_repeat=3, diagnoses=1, failed_reviews=3)))
        os.environ.update(FAKE_REVIEW="fail")
        stuck = self.review(commit=commit)
        self.assertEqual((stuck["failed_reviews_with_repeat"], stuck["repeated"]), (4, ["the water is flat (M1.1)"]))
        self.assertEqual((stuck["escalation"], stuck["next"]["escalation"], stuck["next"]["decides"]),
                         ("too_many_failed_reviews", "too_many_failed_reviews", "human"))
        self.assertIn(" human reopen --module WATER --milestone M1 ", stuck["next"]["command"])
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["blocked"]["reason"]), ("blocked", "too_many_failed_reviews"))

    def test_astra_3_review_of_a_missing_commit_is_invalid(self):
        self.claim()
        result = self.review(commit="does-not-exist")
        self.assertEqual(result["result"], "INVALID")
        self.assertIn("doesn't exist", result["problems"][0])

    def test_astra_3_a_reviewer_that_writes_nothing_is_invalid_and_nothing_lands(self):
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="nothing")
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["merged"]), ("INVALID", False))
        self.assertTrue(any("M999" in p for p in result["problems"]))
        self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")

    def test_astra_4_reviewer_source_edits_are_caught_and_not_landed(self):
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="overreach")
        result = self.review(commit=commit)
        self.assertEqual(result["result"], "INVALID")
        self.assertTrue(any("src.txt" in p for p in result["problems"]))
        self.git("fetch", "-q", "origin")
        self.assertNotIn("src.txt", self.git("ls-tree", "--name-only", "origin/main").stdout)

    def test_fable_2_upstream_work_landed_during_review_isnt_the_reviewers(self):
        commit = self.claim()
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        (other / "src").mkdir()
        (other / "src/water.rs").write_text("another module's work")
        self.git("add", "-A", where=other)
        self.git("-c", "user.name=o", "-c", "user.email=o@o", "commit", "-qm", "other module", where=other)
        self.git("push", "-q", "origin", "main", where=other)
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"]), ("REVIEWED", "PASS"))
        self.git("fetch", "-q", "origin")
        self.assertIn("src/water.rs", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)

    def test_astra_13_host_failure_in_review_is_floor_for_the_fallback(self):
        commit = self.claim()
        os.environ.update(FAKE_EXIT="1")
        self.assertEqual(self.review(commit=commit)["result"], "HOST_FAILED")

    def test_human_accept_skips_review_and_rereview_keeps_the_old_review(self):
        self.claim()
        result = self.human("accept", "M1", reason="typo fix")
        self.assertEqual(result["result"], "DONE")
        accepted = self.read_record()["milestones"]["M1"]["accepted"]
        self.assertEqual((accepted["by"], accepted["words"]), ("human decision", "typo fix"))
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M2")
        # Now a reviewed acceptance, then a re-review.
        self.human("rereview", "M1")
        self.git("pull", "-q", "--rebase", "origin", "main")
        result = self.review(commit=self.read_record()["milestones"]["M1"]["ready_for_review"]["commit"])
        self.assertEqual(result["verdict"], "PASS")
        again = self.human("rereview", "M1", reason="too lenient")
        self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")
        self.git("fetch", "-q", "origin")
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout
        self.assertIn("docs/evidence/WATER/M1-review-1.md", files)
        self.assertTrue(again["commit"])

    def test_human_commands_are_refused_inside_a_loop_session(self):
        for verb in ("accept", "rereview", "reopen", "scope", "release", "feedback"):
            with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit) as stop:
                agent_loop.cmd_human(argparse.Namespace(action=verb, module="WATER", milestone="M1", item=None,
                                                        text="yes", said="yes", asked="ok?", worktree=str(self.wt)))
            self.assertIn(f"human {verb} can't run inside a session the script started", str(stop.exception))

    def test_astra_1_a_record_edited_outside_the_loop_blocks_the_claim(self):
        start = agent_loop.head_commit(self.wt)
        rec = json.loads((self.wt / "docs/plans/WATER/ACCEPTED.json").read_text())
        rec["milestones"]["M1"]["accepted"] = {"by": "review"}
        put(self.wt / "docs/plans/WATER/ACCEPTED.json", json.dumps(rec))
        self.commit_all()
        prof = agent_loop.profile(self.wt, strict=True)
        self.assertEqual(len(agent_loop.record_tampering(self.wt, prof, start, agent_loop.head_commit(self.wt))), 1)


class HumanAndPlanner(Repo):
    def test_fable_7_human_scope_change_authorises_without_spending_the_diagnosis(self):
        d = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        d["milestones"][0]["items"][0]["statement"] = "M1.1 works, and faster"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(d))
        self.assertEqual(self.human("scope", "M1")["result"], "DONE")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["diagnoses"], m1["failed_reviews_with_repeat"], m1["items"][0]["statement"]), (0, 0, "M1.1 works, and faster"))
        self.assertEqual(self.read_record()["milestones"]["M1"]["authorised"]["by"], "human decision")
        self.git("checkout", "-q", "--", ".")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")

    def test_human_reopen(self):
        self.write_done([dict(too_many("M1", ["open"]), failed_reviews_with_repeat=4), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "too_many_failed_reviews"), result)
        self.human("reopen", "M1")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["failed_reviews_with_repeat"], "blocked" in m1), ("in_progress", 0, False))

    def test_fable_9_a_planned_module_is_committed_landed_and_queued(self):
        result = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="plan PAY", host=None, model=None,
                           effort=None, turn_timeout_hours=0.1)
        self.assertEqual((result["result"], result["merged"]), ("PLANNED", True))
        self.assertEqual(result["design_review_owed"], ["PAY"])
        self.assertIn("features.multi_agent=false", self.calls()[0]["argv"])
        self.assertIn({"module": "PAY"}, self.ready()["design_not_approved"])
        rec = json.loads(self.git("show", "origin/main:docs/plans/PAY/ACCEPTED.json").stdout)
        self.assertEqual(rec["milestones"]["M1"]["authorised"]["by"], "plan")

    def test_planner_editing_a_record_is_invalid(self):
        os.environ.update(FAKE_PLAN="forge")
        result = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="x", host=None, model=None,
                           effort=None, turn_timeout_hours=0.1)
        self.assertEqual(result["result"], "INVALID")


class Leads(Repo):
    def second_clone(self):
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.git("config", "user.name", "t2", where=other)
        self.git("config", "user.email", "t2@t", where=other)
        return other

    def test_fable_4_two_leads_never_start_the_same_milestone(self):
        prof = agent_loop.profile(self.wt, strict=True)
        self.assertTrue(agent_loop.take_hold(self.wt, prof, "WATER", "M1")[0])
        other = self.second_clone()
        ok, holder = agent_loop.take_hold(other, prof, "WATER", "M1")
        self.assertFalse(ok)
        self.assertEqual(holder, agent_loop.me(self.wt))
        self.assertEqual(self.ready(other)["taken"][0]["milestone"], "M1")
        self.assertEqual(self.run_loop(worktree=str(other))["result"], "TAKEN")

    def test_fable_6_pause_signals_the_running_loop(self):
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER'); agent_loop.install_stop(); print('up', flush=True)\n"
                "while not agent_loop._STOP: time.sleep(0.05)\nprint('paused', flush=True)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.stdout.readline().strip(), "up")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_pause(argparse.Namespace(module=None, worktree=str(self.wt)))
        self.assertEqual(json.loads(out.getvalue())["paused"][0]["run"], "WATER")
        self.assertEqual(proc.stdout.readline().strip(), "paused")
        proc.wait(timeout=5)

    def test_astra_14_ready_fails_closed_when_the_tip_cant_be_fetched(self):
        self.git("remote", "set-url", "origin", str(self.root / "gone.git"))
        with self.assertRaises(SystemExit):
            self.ready()

    def test_fable_8_ready_names_cycles(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"]), depends_on=["CORE:M1"])])
        self.write_done([dict(milestone("M1", "not_started", ["open"]), depends_on=["WATER:M1"])], module="CORE")
        self.commit_all()
        invalid = self.ready()["invalid"]
        self.assertEqual({i["module"] for i in invalid}, {"WATER", "CORE"})
        self.assertTrue(all("cycle" in i["problems"][-1] for i in invalid))

    def test_ready_and_project_status(self):
        put(self.wt / "docs/plans/CORE/DONE.json", json.dumps(done(milestone("M1", "not_started", ["open"]),
                                                                            module="CORE")))
        self.commit_all()
        r = self.ready()
        self.assertEqual(r["ready"][0]["milestone"], "M1")
        self.assertEqual(r["design_not_approved"], [{"module": "CORE"}])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_status(argparse.Namespace(module=None, worktree=str(self.wt)))
        self.assertIn("CORE: design_not_approved", out.getvalue())
        self.assertIn("WATER: ready (M1)", out.getvalue())

    def test_ready_names_the_modules_to_plan_next(self):
        put(self.wt / "docs/plans/ARCHITECTURE.md", ARCH.replace(
            "| WATER |\n", "| WATER M1 |\n| 3 | HARBOUR | Boats dock | modules 1 to 2 |\n"
                           "| 4 | GULLS | Birds | the human's call |\n| 5 | FISH | Fish swim | none |\n"
                           "| 6 | TIDE | Tides | WATER M1; the human's port timing |\n"))
        self.commit_all()
        ahead = self.ready()["plan_ahead"]
        self.assertEqual([(a["module"], a["needs"]) for a in ahead], [("SHIPS", ["WATER"]), ("FISH", [])])
        self.assertIn("--task 'Plan module SHIPS. It needs: WATER M1'", ahead[0]["next"]["command"])


class Loops(Repo):
    """`loops` lists every live loop on the machine from the records loops keep, or from the process table for those
    that keep none; a dead loop never shows, and what it left is cleared. `status` names the modules with a live run."""

    def repo(self):
        return agent_loop.repository_of(agent_loop.git_common_dir(self.wt))

    def listed(self):
        return [r for r in agent_loop.live_loops(self.repo())[0]]

    def status(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_status(argparse.Namespace(module=None, worktree=str(self.wt)))
        return out.getvalue()

    def holder(self):
        """A loop in another process, holding the module's run lock with a record, until killed."""
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER', milestone='M1', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.stdout.readline().strip(), "up")
        return proc

    def test_a_running_build_is_listed_with_its_record_and_leaves_nothing_when_it_ends(self):
        seen = self.root / "seen"
        os.environ.update(FAKE_LOOPS=str(seen), FAKE_LOOPS_SCRIPT=str(SCRIPTS / "agent_loop.py"))
        steps = []
        real = agent_loop.loop_note
        with mock.patch.object(agent_loop, "loop_note", lambda **f: (steps.append(f["step"]) if "step" in f else None,
                                                                      real(**f))):
            result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW")
        self.assertFalse({"pid", "runs", "turns", "registered"} & set(result))  # the result contract is unchanged
        self.assertEqual(steps, ["builder turn 1", "checking M1: M1.1", "merging the Ready for Review record"])
        during = json.loads(seen.read_text().splitlines()[0])["runs"]
        self.assertEqual(len(during), 1, during)
        v = during[0]
        self.assertEqual(v["step"], "builder turn 1")
        self.assertIn("now: builder turn 1", agent_loop.loop_line(v))
        self.assertEqual((v["role"], v["module"], v["milestone"], v["host"], v["model"], v["effort"], v["path"]),
                         ("build", "WATER", "M1", "codex", agent_loop.DEFAULT_MODEL, "medium", "headless"))
        self.assertEqual((v["pid"], v["turns"], v["registered"], v["repository"]), (os.getpid(), 0, True, self.repo()))
        self.assertLess(v["idle_s"], 60)
        self.assertTrue(v["started"])
        self.assertEqual(list(self.loops.glob("*")), [])
        # the run lock's file stays (an older copy may hold it open); it names a pid that no longer runs it
        self.assertIsNone(agent_loop.run_holder(self.wt / ".git/orchestrate", "WATER"))
        self.assertEqual(self.listed(), [])

    def test_each_turn_counts_with_its_session_and_tokens(self):
        os.environ.update(FAKE_PASS="0", FAKE_USAGE="1")
        prof = agent_loop.profile(self.wt, strict=True)
        agent_loop.loop_register(self.wt, "build", module="WATER", milestone="M1")
        for _ in range(2):
            agent_loop.run_turn("codex", prof, "m", "medium", self.wt, "go", None, 30)
        rec = json.loads((self.loops / f"{os.getpid()}.json").read_text())
        self.assertEqual((rec["turns"], rec["session"], rec["path"]), (2, "t1", "headless"))
        self.assertEqual(rec["usage"], {"input": 120, "cached": 80, "output": 14, "turns": 2})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_loops(argparse.Namespace(repo=str(self.wt), json=False))
        self.assertIn("WATER M1  build  codex m medium, headless", out.getvalue())
        self.assertIn("2 turns", out.getvalue())
        self.assertIn("tokens 120 in, 80 cached, 14 out", out.getvalue())

    def test_a_dead_loop_never_shows_and_what_it_left_is_cleared(self):
        proc = self.holder()
        try:
            self.assertEqual([(r["pid"], r["registered"]) for r in self.listed()], [(proc.pid, True)])
            self.assertIn("WATER: ready (M1); running: build M1 codex, pid", self.status())
        finally:
            proc.kill()
            proc.wait(timeout=5)
        self.assertNotIn("running", self.status())  # status reads only; it never shows the dead loop
        loops, removed = agent_loop.live_loops(self.repo())
        self.assertEqual(loops, [])
        self.assertNotIn((self.wt / ".git/orchestrate/run-WATER.lock").resolve(), [Path(p).resolve() for p in removed])
        self.assertEqual(list(self.loops.glob("*")), [])
        self.assertIsNone(agent_loop.run_holder(self.wt / ".git/orchestrate", "WATER"))
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")  # and the module runs again

    def test_bookkeeping_that_cant_be_written_never_stops_a_loop(self):
        blocker = self.root / "not-a-folder"
        blocker.write_text("")
        agent_loop.LOOPS_DIR = blocker / "loops"
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        self.assertEqual(agent_loop.LIVE, {})

    def test_a_loop_without_a_record_is_found_in_the_process_table(self):
        self.assertEqual((agent_loop.etime_s("1-02:03:04"), agent_loop.etime_s("05:06")), (93784.0, 306.0))
        script = self.root / "old" / "agent_loop.py"  # an older copy, which keeps no record
        script.parent.mkdir()
        script.write_text("import time\ntime.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, str(script), "run", "--module", "WATER", "--worktree", str(self.wt),
                                 "--host", "claude"])
        try:
            (self.wt / ".git/orchestrate").mkdir(exist_ok=True)
            state = self.wt / ".git/orchestrate/WATER.json"
            state.write_text(json.dumps({"milestone": "M2", "path": "visible"}))
            # its run state, written after it started: ps gives the start in whole seconds
            os.utime(state, (time.time() + 2, time.time() + 2))
            found = [r for r in self.listed() if r["pid"] == proc.pid]
            self.assertEqual(len(found), 1, self.listed())
            v = agent_loop.loop_view(found[0])
            self.assertEqual((v["role"], v["module"], v["milestone"], v["host"], v["path"], v["registered"]),
                             ("build", "WATER", "M2", "claude", "visible", False))
            self.assertEqual(v["script"], str(script))
        finally:
            proc.kill()
            proc.wait(timeout=5)
        self.assertEqual([r for r in self.listed() if r["pid"] == proc.pid], [])


class Guidance(Repo):
    """The four things a lead had to work out by hand before a milestone could run: plans left uncommitted, a
    sandbox refusing writes under .git, an owed design review, and what to run after any stop short of building."""

    def plan_core(self):
        put(self.wt / "docs/plans/CORE/DONE.json", json.dumps(done(milestone("M1", "not_started", ["open"]),
                                                                            module="CORE")))
        put(self.wt / "docs/plans/CORE/DESIGN.md", "# Core design")

    def main(self, *argv):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["agent_loop.py", *argv]), contextlib.redirect_stdout(out), \
                self.assertRaises(SystemExit) as stop:
            agent_loop.main()
        release()
        return stop.exception.code, json.loads(out.getvalue().strip().splitlines()[-1])

    # 1. Uncommitted plans

    def test_fix1_ready_and_run_name_plan_files_the_tip_doesnt_have(self):
        self.plan_core()
        r = self.ready()
        self.assertEqual(r["unmerged_plans"]["uncommitted"], ["docs/plans/CORE/DESIGN.md", "docs/plans/CORE/DONE.json"])
        self.assertIn(" adopt --worktree ", r["next"]["command"])
        result = self.run_loop(module="CORE")
        self.assertEqual(result["result"], "INVALID")
        self.assertIn("no done-when file at the main branch's tip", result["problems"][0])
        self.assertIn("CORE/DONE.json", result["next"]["why"])
        self.assertIn(" adopt ", result["next"]["command"])
        self.assertFalse(self.log.exists())
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# Water design")  # committed here, never integrated
        self.git("add", "docs/plans/WATER/DESIGN.md")
        self.git("commit", "-qm", "water design")
        self.assertEqual(self.ready()["unmerged_plans"]["unmerged"], ["docs/plans/WATER/DESIGN.md"])

    def test_fix1_adopt_lands_only_the_plan_files_and_refuses_anything_else(self):
        self.plan_core()
        (self.wt / "src").mkdir()
        (self.wt / "src/engine.rs").write_text("unfinished work")
        refused = self.adopt("src/engine.rs")
        self.assertEqual(refused["result"], "REFUSED")
        self.assertIn("isn't a plan file under docs/plans/", refused["problems"][0])
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertEqual(result["files"], ["docs/plans/CORE/DESIGN.md", "docs/plans/CORE/DONE.json"])
        self.git("fetch", "-q", "origin")
        landed = self.git("show", "--name-only", "--format=", "origin/main").stdout.split()
        self.assertEqual(sorted(landed), ["docs/plans/CORE/DESIGN.md", "docs/plans/CORE/DONE.json"])
        self.assertEqual((self.wt / "src/engine.rs").read_text(), "unfinished work")  # left alone, not swept in
        self.assertNotIn(agent_loop.TRAILER, self.git("log", "-1", "--format=%B", "origin/main").stdout)
        r = self.ready()
        self.assertNotIn("unmerged_plans", r)
        self.assertEqual(r["design_not_approved"], [{"module": "CORE"}])
        self.assertTrue(result["worktree"].startswith("fast-forwarded"), result["worktree"])

    def test_fix1_adopt_refuses_a_plan_that_grants_what_a_planner_cant(self):
        forged = milestone("M1", "done", ["pass"])
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(done(forged, milestone("M2", "not_started", ["open"]))))
        put(self.wt / "docs/plans/WATER/ACCEPTED.json", "{}")
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED")
        self.assertTrue(any("only the script writes" in p for p in result["problems"]), result)
        self.assertTrue(any("a planner can't set" in p for p in result["problems"]), result)
        with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_adopt(argparse.Namespace(worktree=str(self.wt), message=None, paths=[]))
        self.assertIn("inside a session", str(stop.exception))

    # 2. A sandbox refusing writes under .git

    def test_fix2_refused_writes_and_held_locks_are_named_not_mistaken(self):
        here = Path("/repo")
        e = agent_loop.blocked_write("error: cannot open '.git/FETCH_HEAD': Permission denied", here)
        self.assertEqual((e.path, e.held), ("/repo/.git/FETCH_HEAD", False))
        e = agent_loop.blocked_write("fatal: cannot lock ref 'HEAD': Unable to create '/repo/.git/refs/heads/main.lock'"
                                     ": Operation not permitted")
        self.assertEqual(e.path, "/repo/.git/refs/heads/main.lock")
        self.assertIn("outside the sandbox", e.reason())
        e = agent_loop.blocked_write("fatal: Unable to create '/repo/.git/index.lock': File exists.")
        self.assertTrue(e.held)
        self.assertIn("doesn't delete lock files", e.reason())
        self.assertIsNone(agent_loop.blocked_write("git@github.com: Permission denied (publickey).\n"
                                                   "fatal: Could not read from remote repository."))

    def test_fix2_a_read_only_git_dir_stops_with_the_path_and_the_fix(self):
        if os.geteuid() == 0:
            self.skipTest("root ignores directory permissions")
        (self.wt / ".git/FETCH_HEAD").unlink(missing_ok=True)
        os.chmod(self.wt / ".git", 0o555)
        try:
            code, ready = self.main("ready", "--worktree", str(self.wt))
            code_land, land = self.main("merge", "--worktree", str(self.wt))
        finally:
            os.chmod(self.wt / ".git", 0o755)
        self.assertEqual((code, ready["result"]), (1, "SCRIPT_FAILED"))
        self.assertEqual(ready["blocked_write"]["path"], str(self.wt.resolve() / ".git/FETCH_HEAD"))
        self.assertIn("outside the sandbox, or with escalation", ready["reason"])
        self.assertIn(" ready --worktree ", ready["next"]["command"])
        self.assertEqual((code_land, land["result"]), (1, "FAILED"))
        self.assertIn(str(self.wt.resolve() / ".git"), land["blocked_write"]["path"])
        self.assertIn("outside the sandbox", land["detail"])

    # 3. An owed design review

    def test_fix3_run_does_the_owed_design_review_then_builds_on_design_ok(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertEqual([c["role"] for c in self.calls()], ["review", "build"])
        self.assertEqual(self.read_record()["design"]["verdict"], "ok")

    def test_fix3_any_other_design_verdict_stops_the_run_and_says_what_next(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        result = self.run_loop()
        self.assertEqual(result["result"], "DESIGN_NOT_APPROVED")
        self.assertEqual(result["design_review"]["verdict"], "DESIGN CHANGES")
        self.assertIn(" plan --worktree ", result["next"]["command"])
        self.assertEqual([c["role"] for c in self.calls()], ["review"])

    def test_fix3_no_design_review_opts_out(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        result = self.run_loop(no_design_review=True)
        self.assertEqual(result["result"], "DESIGN_NOT_APPROVED")
        self.assertIn(" review --module WATER --milestone design ", result["next"]["command"])
        self.assertFalse(self.log.exists())

    # 4. The next command

    def test_fix4_waiting_follows_the_need_to_the_command_that_moves_it(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"]), depends_on=["CORE:M1"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual(result["result"], "WAITING")
        self.assertIn(" plan --worktree ", result["next"]["command"])
        self.assertIn("Plan module CORE", result["next"]["command"])
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False, module="CORE")
        self.commit_all()
        result = self.run_loop()
        self.assertIn(" review --module CORE --milestone design ", result["next"]["command"])
        r = self.ready()  # nothing ready: the lead still gets a command
        self.assertEqual(r["ready"], [])
        self.assertIn(" review --module CORE --milestone design ", r["next"]["command"])

    def test_fix4_review_blocked_invalid_and_floor_carry_the_next_command(self):
        self.write_done([milestone("M1", "ready_for_review", ["pass"], inspect="captures"), milestone("M2", "not_started", ["open"])],
                        ready=["M1"])
        self.commit_all()
        owed = self.run_loop()
        self.assertEqual(owed["result"], "REVIEW_OWED")
        self.assertIn(" review --module WATER --milestone M1 --commit ", owed["next"]["command"])
        self.write_done([milestone("M1", "not_started", ["open"]), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device attached")
        blocked = self.run_loop()
        self.assertEqual(blocked["result"], "BLOCKED")
        self.assertIn(" run --module WATER ", blocked["next"]["command"])
        self.assertIn(" --message '<the missing fact>'", blocked["next"]["command"])
        self.assertIn("no device attached", blocked["next"]["why"])
        again = self.run_loop()  # without the fact, it stays blocked
        self.assertEqual((again["result"], again["reason"]), ("BLOCKED", "needs_context"), again)
        self.assertIn(" --message ", again["next"]["command"])
        agent_loop.CODEX = "/no/such/codex"
        with contextlib.redirect_stdout(io.StringIO()):
            agent_loop.cmd_unblock(argparse.Namespace(module="WATER", milestone="M1", worktree=str(self.wt)))
        floor = self.run_loop()
        self.assertEqual(floor["result"], "HOST_FAILED")
        self.assertIn("--host claude", floor["next"]["alternative"])
        put(self.wt / "docs/plans/WATER/DONE.json", "{not json")
        self.commit_all()
        invalid = self.run_loop()
        self.assertEqual(invalid["result"], "INVALID")
        self.assertIn(" plan --worktree ", invalid["next"]["command"])

    def test_fix4_human_decisions_are_commands_for_the_human_never_run(self):
        self.write_done([too_many("M1", ["open"], inspect="captures"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "too_many_failed_reviews"), result)
        self.assertEqual(result["next"]["decides"], "human")
        self.assertIn(" human reopen --module WATER --milestone M1 ", result["next"]["command"])
        self.write_done([milestone("M1", "done", ["pass"], inspect="captures"), milestone("M2", "not_started", ["open"])],
                        authorise=False)  # done in the file, never accepted by the loop
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["next"]["decides"]), ("REVIEW_OWED", "human"))
        self.assertIn(" human accept ", result["next"]["command"])
        self.assertFalse(self.log.exists())
        self.assertEqual(self.read_done()["milestones"][0]["state"], "done")
        self.assertNotIn("accepted", self.read_record()["milestones"]["M1"])

    def test_fix4_taken_points_at_other_work(self):
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.assertTrue(agent_loop.take_hold(other, prof, "WATER", "M1")[0])
        result = self.run_loop()
        self.assertEqual(result["result"], "TAKEN")
        self.assertIn(" ready --worktree ", result["next"]["command"])
        self.assertIn(" human release ", result["next"]["human"])


class ReviewerAccess(Repo):
    """Release 4 of the 2026-11-12 improvement plan. A reviewer who can't reach the product ends Blocked: Needs
    Access and costs no round (F1), and the script stops waiting on a tool call that has hung, naming it (N5, C5)."""

    def setUp(self):
        super().setUp()
        self.commit = self.ready_for_review()

    def tip(self):
        self.git("fetch", "-q", "origin")
        return self.git("rev-parse", "origin/main").stdout.strip()

    def test_a_reviewer_that_cant_reach_the_product_ends_blocked_and_costs_no_review(self):
        before = self.tip()
        os.environ.update(FAKE_REVIEW="needs_access")
        result = self.review(commit=self.commit)
        self.assertEqual((result["result"], result["reason"], result["merged"]), ("BLOCKED", "needs_access", False),
                         result)
        self.assertEqual(result["what"], "unlock the Mac's console and approve Computer Use")
        then = result["next"]
        self.assertTrue(then["command"].startswith("ORCHESTRATE_VISIBLE=1 "), then)
        self.assertIn(f" review --module WATER --milestone M1 --commit {self.commit} ", then["command"])
        self.assertIn("no review was counted", then["why"])
        self.assertIn("Are you there now?", then["ask"])
        self.assertEqual(self.tip(), before)  # nothing merged, so no round and no review file
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1.get("failed_reviews", 0), m1["failed_reviews_with_repeat"]), ("ready_for_review", 0, 0))
        self.assertFalse(self.read_record()["milestones"]["M1"].get("reviews"))
        # the same review, once the human is at the machine, judges it as usual
        os.environ.update(FAKE_REVIEW="pass")
        self.assertEqual(self.review(commit=self.commit)["verdict"], "PASS")

    def test_a_tool_call_open_too_long_stops_the_turn_and_the_next_prompt_names_it(self):
        os.environ.update(FAKE_TOOL_HANG="60", FAKE_REVIEW="needs_access")
        started = time.time()
        with mock.patch.object(agent_loop, "TOOL_CALL_LIMIT_S", 0.1):
            result = self.review(commit=self.commit, host="claude")
        self.assertLess(time.time() - started, 40)
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "needs_access"), result)
        reviews = [c for c in self.calls() if c["role"] == "review"]
        self.assertEqual(len(reviews), 2)
        nudge = self.prompt(reviews[1])
        self.assertIn("the tool call mcp__computer-use__screenshot had been open for", nudge)
        self.assertIn("BLOCKED needs_access", nudge)
        self.assertNotIn("Bash had been open", nudge)  # the shell command had finished, and is never stopped

class WhatTheLeadSees(Repo):
    """Release 5 of the 2026-11-12 improvement plan: what the lead and the human see (N5, L5, N8, F3, P5 and the
    smaller issues)."""

    def builders_line(self, line):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + f"- **Builders:** {line}\n")
        self.commit_all()


    def test_run_refuses_a_builder_past_the_builders_count_without_the_humans_words(self):
        self.builders_line("one Codex builder")
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'CORE')\n"
                "agent_loop.loop_register(wt, 'build', module='CORE', milestone='M4', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        other = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(other.stdout.readline().strip(), "up")
            refused = self.run_loop()
            self.assertEqual(refused["result"], "REFUSED", refused)
            self.assertEqual(refused["running"], [{"module": "CORE", "milestone": "M4", "pid": other.pid}])
            self.assertIn("Builders line allows 1", refused["problems"][0])
            self.assertEqual(refused["next"]["decides"], "human")
            self.assertIn("--more-builders", refused["next"]["command"])
            self.assertEqual(self.calls() if self.log.exists() else [], [])  # no builder started
            words = "Yes, run one more while I'm at the Mac"
            more = self.run_loop(more_builders=words)
            self.assertEqual(more["result"], "READY_FOR_REVIEW", more)
            self.assertEqual((more["more_builders"]["said"], more["more_builders"]["running"]), (words, 1))
        finally:
            other.kill()
            other.wait()
        self.builders_line("two Codex builders")
        self.assertNotEqual(self.run_loop()["result"], "REFUSED")  # under the count, nothing to ask

    def test_the_first_result_after_a_version_change_says_what_changed(self):
        self.assertIsNone(agent_loop.version_change(self.wt))  # a new project: nothing changed for it
        note = Path(agent_loop.git_common_dir(self.wt)) / "orchestrate" / "version.json"
        self.assertEqual(json.loads(note.read_text())["version"], agent_loop.VERSION)
        note.unlink()
        old = agent_loop.loop_dir(self.wt) / "usage.jsonl"  # left by 2.0.0, which kept no note of its version
        old.write_text('{"at": "2026-11-11T09:00:00Z"}\n')
        os.utime(old, (time.time() - 3600, time.time() - 3600))
        agent_loop.new_command()
        with mock.patch.object(agent_loop, "QUOTA_WORKTREE", [self.wt]):
            first = self.call(lambda a: agent_loop.emit("NOTHING"))
            second = self.call(lambda a: agent_loop.emit("NOTHING"))
        lines = first["changed"]["2.1.0"]
        for words in ("Only the script sets a milestone to Ready for Review", "over 60% full", "HOST_FAILED",
                      "`runs`", "--more-builders", "BLOCKED needs_access"):
            self.assertTrue(any(words in l for l in lines), words)
        self.assertNotIn("changed", second)
        note.write_text('{"version": "2.0.0"}')
        self.assertEqual(list(agent_loop.version_change(self.wt)), ["2.1.0"])

    def test_a_blocked_message_gives_paths_in_the_repository_and_names_who_acts(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY=f"BLOCKED: the seam shows in {self.wt}/docs/evidence/WATER/f.png "
                                                    "and I don't know which constant sets it")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
        what = self.read_done()["milestones"][0]["blocked"]["what"]
        self.assertEqual(what, "the seam shows in docs/evidence/WATER/f.png and I don't know which constant sets it")
        self.assertIn("The lead finds the missing fact, or asks the human", blocked["next"]["why"])
        self.git("fetch", "-q", "origin")
        page = agent_loop.status_page(self.wt, agent_loop.profile(self.wt), "origin/main")
        now_next = page.split("### Now and next")[1].split("###")[0]
        self.assertIn("Blocked: Needs Context: the seam shows in docs/evidence/WATER/f.png", now_next)
        self.assertIn("The lead finds the missing fact, or asks you for it", now_next)
        self.assertNotIn(str(self.wt), page)


class WhatTheLeadSeesAlone(ProfileOnly):
    """Tests from WhatTheLeadSees that need no repository, only the project settings."""

    def test_runs_prints_the_step_a_review_is_on_and_the_tool_call_it_waits_on(self):
        # a build's step, seen live during its turn, is checked in Loops
        rec = {"pid": 1, "role": "review", "module": "WATER", "milestone": "M1", "host": "claude", "turns": 0,
               "started_at": time.time() - 600, "activity_at": time.time() - 500, "turn_started_at": time.time() - 590,
               "usage": {}, "registered": True, "worktree": str(self.wt), "step": "reviewer turn 1",
               "open_tool_call": {"name": "mcp__computer-use__screenshot", "opened_at": time.time() - 480}}
        line = agent_loop.loop_line(agent_loop.loop_view(rec))
        self.assertIn("now: reviewer turn 1, waiting on the tool call mcp__computer-use__screenshot for 8m", line)

    def test_profile_reads_the_builders_count_as_a_digit_or_a_word(self):
        for line, count in (("two Codex builders", 2), ("3 on Codex, one on Claude", 3), ("usually one", 1),
                            ("as many as can start", None), ("<how many builders>", None)):
            (self.wt / "ORCHESTRATE.md").write_text(PROFILE + f"- **Builders:** {line}\n")
            self.assertEqual(agent_loop.profile(self.wt)["builders"], count, line)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE)
        self.assertIsNone(agent_loop.profile(self.wt)["builders"])


class Landing(Clean):
    def test_astra_10_local_integration_with_no_remote_fast_forwards_the_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, wt = Path(tmp, "repo"), Path(tmp, "repo-build")
            run = lambda *a, where=main: subprocess.run(["git", "-C", str(where), *a], check=True, capture_output=True)
            run("init", "-q", "-b", "main", str(main), where=tmp)
            run("config", "user.name", "t")
            run("config", "user.email", "t@t")
            (main / "ORCHESTRATE.md").write_text("- **Merge:** local\n- **Test command:** test -f feature\n")
            run("add", "-A")
            run("commit", "-qm", "init")
            run("worktree", "add", "-q", "-b", "build/x", str(wt), "main")
            (wt / "feature").write_text("x")
            run("add", "-A", where=wt)
            run("commit", "-qm", "feature", where=wt)
            prof = agent_loop.profile(wt, strict=True)
            ok, landed = agent_loop.land(wt, prof, check=True)
            self.assertTrue(ok, landed)
            self.assertEqual(agent_loop.head_commit(main), agent_loop.head_commit(wt))
            self.assertTrue((main / "feature").exists())


class PausingARun(Repo):
    def test_pause_stops_a_running_run_and_its_host(self):
        """The whole path: `run` started as the lead starts it, `pause` sent from another process, and the turn's
        host stopped before the run prints PAUSED."""
        env = dict(os.environ, ORCHESTRATE_CODEX=agent_loop.CODEX, CODEX_HOME=str(self.home), FAKE_PASS="0",
                   FAKE_SLEEP="30")
        run = subprocess.Popen([sys.executable, str(agent_loop.LOOP), "run", "--module", "WATER", "--worktree",
                                str(self.wt)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
        self.addCleanup(lambda: (run.kill(), run.wait(), run.stdout.close()))
        deadline = time.time() + 30
        while time.time() < deadline and not (self.log.exists() and self.log.read_text().strip()):
            time.sleep(0.05)
        host = self.calls()[0]["pid"]
        paused = subprocess.run([sys.executable, str(agent_loop.LOOP), "pause", "--module", "WATER", "--worktree",
                                 str(self.wt)], capture_output=True, text=True, env=env, check=True)
        self.assertEqual(json.loads(paused.stdout)["paused"], [{"run": "WATER", "pid": run.pid}])
        out, _ = run.communicate(timeout=60)
        result = json.loads(out.splitlines()[-1])
        self.assertEqual(result["result"], "PAUSED", result)
        with self.assertRaises(ProcessLookupError):
            os.kill(host, 0)


class LandingOnGit(Repo):
    """`land` when real git pushes back. Losing a builder's work here, or leaving a rebase half done in its tree,
    would go unseen, so each case is made to happen with git rather than mocked."""

    def commit(self, name, text, where=None):
        put((where or self.wt) / name, text)
        self.git("add", "-A", where=where)
        self.git("commit", "-qm", name, where=where)
        return agent_loop.head_commit(where or self.wt)

    def reject_pushes(self, times):
        """Makes the origin refuse the next `times` pushes, then accept."""
        hook = self.origin / "hooks/pre-receive"
        hook.write_text(f"#!/bin/sh\nn=$(cat rejected 2>/dev/null || echo 0)\n"
                        f"if [ $n -lt {times} ]; then echo $((n + 1)) > rejected; echo not now >&2; exit 1; fi\n")
        hook.chmod(0o755)

    def test_a_rejected_push_is_retried_and_lands(self):
        mine = self.commit("mine.txt", "mine")
        self.reject_pushes(1)
        ok, landed = agent_loop.land(self.wt, agent_loop.profile(self.wt, strict=True))
        self.assertTrue(ok, landed)
        self.assertEqual((self.origin / "rejected").read_text().strip(), "1")  # the first push was refused
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("rev-parse", "origin/main").stdout.strip(), landed)
        self.assertEqual(landed, mine)

    def test_a_push_rejected_twice_fails_and_says_so(self):
        self.commit("mine.txt", "mine")
        self.reject_pushes(2)
        ok, detail = agent_loop.land(self.wt, agent_loop.profile(self.wt, strict=True))
        self.assertFalse(ok)
        self.assertIn("push rejected", detail)
        self.assertIn("pre-receive hook declined", detail)
        self.assertEqual((self.origin / "rejected").read_text().strip(), "2")  # it tried twice, no more

    def test_a_rebase_that_conflicts_is_aborted_and_the_work_kept(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.commit("shared.txt", "theirs\n", where=other)
        self.git("push", "-q", "origin", "main", where=other)
        mine = self.commit("shared.txt", "mine\n")
        ok, detail = agent_loop.land(self.wt, agent_loop.profile(self.wt, strict=True))
        self.assertFalse(ok)
        self.assertIn("rebase onto origin/main failed", detail)
        self.assertFalse((self.wt / ".git/rebase-merge").exists() or (self.wt / ".git/rebase-apply").exists())
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertEqual(agent_loop.head_commit(self.wt), mine)
        self.assertEqual((self.wt / "shared.txt").read_text(), "mine\n")

    def test_a_local_main_branch_that_cant_fast_forward_is_left_as_it_was(self):
        before = self.commit("ORCHESTRATE.md", PROFILE.replace("push", "local"))
        build = self.root / "build"
        self.git("worktree", "add", "-q", "-b", "build/x", str(build), "main")
        self.commit("water.txt", "built\n", where=build)
        (self.wt / "water.txt").write_text("the human's edit, not committed\n")  # main, checked out here, is dirty
        ok, detail = agent_loop.land(build, agent_loop.profile(build, strict=True))
        self.assertFalse(ok)
        self.assertIn(f"couldn't fast-forward main in {self.wt.resolve()}", detail)
        self.assertEqual(agent_loop.head_commit(self.wt), before)
        self.assertEqual((self.wt / "water.txt").read_text(), "the human's edit, not committed\n")


class FakeCodexApp:
    """Stands in for the Codex desktop app. A thread is a rollout file under the fake CODEX_HOME; a wake link runs the
    fake host as the app's turn would (in the thread's folder, with its role) and appends the turn's events."""

    def __init__(self, case, behaviour="run", effort_seen=None):
        self.case, self.behaviour, self.effort_seen = case, behaviour, effort_seen
        self.threads, self.queued, self.links, self.interrupts, self.activated = {}, {}, [], [], []
        self.sent, self.unqueued, self.ignored_wakes = [], [], 0

    def write(self, t, *events):
        with open(self.threads[t]["path"], "a") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")

    def create(self, prof, model, effort, worktree, role, title):
        t = f"019a0000-0000-7000-8000-{len(self.threads):012d}"
        path = self.case.home / "sessions/2026/11/09" / f"rollout-2026-11-09T00-00-00-{t}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.threads[t] = dict(path=path, model=model, effort=effort, cwd=Path(worktree), role=role, title=title)
        self.write(t, {"type": "session_meta", "payload": {"id": t, "cwd": str(worktree)}},
                   {"type": "turn_context", "payload": {"turn_id": "boot", "model": model, "effort": effort}})
        return t

    def owner(self, t):
        info = self.threads.get(t)
        return {"model": info["model"], "reasoningEffort": info["effort"]} if info else None

    def queue(self, t, text):
        self.queued[t] = text
        self.sent.append(text)

    def link(self, url):
        self.links.append(url)
        if "/wake/" in url:
            self.wake(url.rsplit("/", 1)[1])
        return True

    def unqueue(self, t):
        self.unqueued.append(t)
        self.queued.pop(t, None)
        return True

    def wake(self, t):
        if self.behaviour == "never" or (self.behaviour == "late" and self.ignored_wakes < 3):
            self.ignored_wakes += 1
            return
        text = self.queued.pop(t, None)
        if text is None:
            return
        info, turn = self.threads[t], f"turn-{len(self.links)}"
        self.write(t, {"type": "event_msg", "payload": {"type": "task_started", "turn_id": turn}},
                   {"type": "turn_context", "payload": {"turn_id": turn, "model": info["model"],
                                                        "effort": self.effort_seen or info["effort"]}})
        if self.behaviour == "hang" or (self.behaviour == "hung_call" and not self.interrupts):
            info["running"] = turn
            if self.behaviour == "hung_call":  # a Computer Use call that never answers, as in Thrum
                self.write(t, {"type": "response_item", "payload": {
                    "type": "function_call", "namespace": "mcp__cua_repl", "name": "js", "call_id": "c1",
                    "arguments": '{"code":"await cua.getApp(\'ThrumReview.app\')"}'}})
            return
        if self.behaviour == "owner_stop":
            self.write(t, {"type": "event_msg", "payload": {"type": "turn_aborted", "turn_id": turn}})
            return
        out = subprocess.run([agent_loop.CODEX], cwd=info["cwd"], capture_output=True, text=True,
                             env={**os.environ, "ORCHESTRATE_ROLE": info["role"]})
        message = agent_loop.parse_output("codex", out.stdout)[1]
        self.write(t, {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": turn,
                                                        "last_agent_message": message}})

    def interrupt(self, t):
        self.interrupts.append(t)
        if running := self.threads[t].pop("running", None):
            self.write(t, {"type": "event_msg", "payload": {"type": "turn_aborted", "turn_id": running}})
        return True

    @contextlib.contextmanager
    def installed(self, claude=False):
        patches = [mock.patch.object(agent_loop, name, value) for name, value in dict(
            visible_unavailable=lambda host: None if host == "codex" or claude else "no app",
            codex_thread_create=self.create, codex_owner=self.owner, codex_queue=self.queue, open_link=self.link,
            codex_interrupt=self.interrupt, codex_queued=lambda t: int(t in self.queued), codex_unqueue=self.unqueue,
            codex_goal_activate=lambda t, status="active": self.activated.append(t) or True,
            SETTLE_S=0.0, POLL_S=0.01, START_S=0.05, STALL_START_S=0.3, CLAUDE_IMPORT_WAIT_S=0.0,
            CODEX_APP_CLI=agent_loop.CODEX).items()]
        for p in patches:
            p.start()
        try:
            yield self
        finally:
            for p in patches:
                p.stop()


class VisibleCodex(Repo):
    """Decision 8: the loop's Codex sessions are threads the Codex app lists and runs."""

    def test_decision_8_a_build_runs_in_a_thread_the_app_shows_and_the_loop_still_claims(self):
        with FakeCodexApp(self).installed() as app:
            result = self.run_loop()
        self.assertEqual((result["result"], result["path"], result["app_settings"]),
                         ("READY_FOR_REVIEW", "visible", "gpt-6.1-sol medium"))
        (t, info), = app.threads.items()
        self.assertEqual((info["model"], info["effort"], info["role"], info["title"], info["cwd"]),
                         ("gpt-6.1-sol", "medium", "build", agent_loop.session_title(self.wt, "WATER", "M1 build"),
                          self.wt.resolve()))
        self.assertIn(f"codex://threads/wake/{t}", app.links)
        self.assertEqual((self.state()["thread"], self.state()["path"]), (t, "visible"))
        self.assertTrue(self.calls(), "the app ran the turn")
        self.assertEqual(self.read_record()["milestones"]["M1"]["accepted"]["by"], "checks")

    def test_decision_8_a_resumed_turn_goes_to_the_same_thread_with_the_message(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        with FakeCodexApp(self).installed() as app:
            blocked = self.run_loop()
            self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
            self.run_loop(message="Use the simulator.")
        self.assertEqual(len(app.threads), 1)
        self.assertIn('the paragraph that starts "The goal:" as the objective, word for word', app.sent[0])
        self.assertTrue(app.sent[0].startswith(agent_loop.GOAL_LINE + "Build milestone M1 of module WATER,"))
        self.assertNotIn("gpt-6.1-sol", app.sent[0])
        self.assertTrue(app.sent[-1].startswith("Use the simulator.\n\nStill binding: the goal is every item of M1 pass with evidence"))

    def test_decision_8_a_turn_on_another_effort_in_the_app_is_PIN(self):
        with FakeCodexApp(self, effort_seen="xhigh").installed():
            result = self.run_loop()
        self.assertEqual(result["result"], "WRONG_MODEL_OR_EFFORT")
        self.assertIn("gpt-6.1-sol/xhigh", result["mismatches"][0])

    def test_decision_8_the_human_pressing_stop_in_the_app_is_PAUSED_not_a_failure(self):
        with FakeCodexApp(self, behaviour="owner_stop").installed() as app:
            result = self.run_loop()
        self.assertEqual(result["result"], "PAUSED")
        self.assertIn("stopped in the Codex app", result["reason"])
        self.assertEqual(app.interrupts, [])

    def test_decision_8_pause_stops_the_turn_running_in_the_app(self):
        with FakeCodexApp(self, behaviour="hang").installed() as app:
            def stop_once_a_turn_is_running():  # a fixed delay raced the loop's start-up on a busy machine
                deadline = time.time() + 30
                while time.time() < deadline and not any(t.get("running") for t in app.threads.values()):
                    time.sleep(0.01)
                agent_loop._STOP = True
            threading.Thread(target=stop_once_a_turn_is_running, daemon=True).start()
            result = self.run_loop()
        self.assertEqual(result["result"], "PAUSED")
        self.assertEqual(len(app.interrupts), 1)

    def test_decision_8_a_timeout_interrupts_the_apps_turn_and_keeps_an_active_goal(self):
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('019a0000-0000-7000-8000-000000000000', 'active')")
        with FakeCodexApp(self, behaviour="hang").installed() as app:
            result = self.run_loop(turn_timeout_hours=0.1 / 3600)
        # A turn stopped at the turn limit isn't a host failure, so the run ends on the stall check, not HOST_FAILED.
        self.assertEqual(result["result"], "STALLED")
        self.assertEqual(len(app.interrupts), agent_loop.STALL_TURNS)
        self.assertEqual(len(app.activated), agent_loop.STALL_TURNS)

    def test_decision_8_run_again_reactivates_a_goal_paused_or_blocked_in_the_app(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        with FakeCodexApp(self).installed() as app:
            self.run_loop()
            t = self.state()["thread"]
            with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
                conn.execute("create table thread_goals (thread_id text, status text)")
                conn.execute("insert into thread_goals values (?, 'paused')", (t,))
            for n, status in enumerate(("paused", "blocked"), 1):  # paused in the app, or blocked until unblocked
                with self.subTest(status=status):
                    with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
                        conn.execute("update thread_goals set status = ?", (status,))
                    self.run_loop(message="x is 3")
                    self.assertEqual(app.activated, [t] * n)

    def test_decision_8_a_review_runs_in_its_own_visible_thread_in_the_verify_tree(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        with FakeCodexApp(self).installed() as app:
            commit = self.run_loop()["commit"]
            result = self.review(commit=commit, effort="high")
        self.assertEqual((result["result"], result["verdict"], result["path"]), ("REVIEWED", "PASS", "visible"))
        review = [i for i in app.threads.values() if i["role"] == "review"][0]
        self.assertEqual((review["title"], review["effort"]), (agent_loop.session_title(self.wt, "WATER", "M1 review"), "high"))
        self.assertIn("orchestrate/verify", str(review["cwd"]))

    def test_decision_8_a_turn_the_app_starts_late_is_waited_for_not_given_up_on(self):
        with FakeCodexApp(self, behaviour="late").installed() as app:
            result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW")
        self.assertEqual(app.unqueued, [])

    def test_decision_8_a_turn_the_app_never_starts_is_unqueued_so_it_cant_run_unwatched(self):
        with FakeCodexApp(self, behaviour="never").installed() as app:
            result = self.run_loop()
        self.assertEqual(result["result"], "HOST_FAILED")
        self.assertIn("queued message was removed", result["stderr"])
        self.assertEqual(app.queued, {})
        self.assertTrue(app.unqueued)

class VisibleClaude(Repo):
    """Decision 8: Claude turns run in the loop's own signed-in CLI, imported into the Code tab."""

    def setUp(self):
        super().setUp()
        self.records = set()

    def link(self, url):
        self.links.append(url)
        self.records.add(url.split("session=")[1])
        return True

    @contextlib.contextmanager
    def app(self, owner_pid=None):
        self.links = []
        with FakeCodexApp(self).installed(claude=True), \
                mock.patch.object(agent_loop, "open_link", self.link), \
                mock.patch.object(agent_loop, "claude_transcript", lambda s: Path("/t") / s), \
                mock.patch.object(agent_loop, "claude_app_record", lambda s: s in self.records and Path("/r")), \
                mock.patch.object(agent_loop, "claude_app_process", lambda s: owner_pid):
            yield

    def test_decision_8_a_claude_build_names_its_session_and_imports_it_into_the_app(self):
        with self.app():
            result = self.run_loop(host="claude")
        self.assertEqual((result["result"], result["path"]), ("READY_FOR_REVIEW", "visible"))
        argv = self.calls()[0]["argv"]
        sid = argv[argv.index("--session-id") + 1]
        self.assertEqual(self.links, [f"claude://resume?session={sid}"])
        self.assertEqual(self.state()["thread"], sid)

    def test_decision_8_the_loop_wont_write_to_a_session_the_human_has_open_in_the_app(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        with self.app():
            self.run_loop(host="claude")
        with self.app(owner_pid=4242):
            result = self.run_loop(host="claude", message="x is 3")
        self.assertEqual(result["result"], "PAUSED")
        self.assertIn("pid 4242", result["reason"])
        self.assertEqual(len(self.calls()), 1)


class VisibleChoice(Clean):
    def test_decision_8_each_reason_to_fall_back_is_named(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(agent_loop, "CODEX_HOME", Path(tmp)), \
                mock.patch.object(agent_loop, "CODEX_APP_CLI", sys.executable), \
                mock.patch.object(agent_loop, "CLAUDE_APP_STORE", Path(tmp)), \
                mock.patch.object(agent_loop.sys, "platform", "darwin"):
            for off in ("", "0"):
                with mock.patch.dict(os.environ, {"ORCHESTRATE_VISIBLE": off}):
                    self.assertIn("headless is the default", agent_loop.visible_unavailable("codex"))
                    self.assertIn("headless is the default", agent_loop.visible_unavailable("claude"))
            with mock.patch.dict(os.environ, {"ORCHESTRATE_VISIBLE": "1"}):
                self.assertIn("isn't running", agent_loop.visible_unavailable("codex"))
                with mock.patch.object(agent_loop, "CODEX_APP_CLI", "/no/such/app"):
                    self.assertIn("isn't installed", agent_loop.visible_unavailable("codex"))
                with mock.patch.object(agent_loop, "claude_app_running", lambda: False):
                    self.assertIn("isn't running", agent_loop.visible_unavailable("claude"))
                with mock.patch.object(agent_loop, "claude_app_running", lambda: True), \
                        mock.patch.object(agent_loop, "claude_signed_in", lambda: False):
                    self.assertIn("signed out", agent_loop.visible_unavailable("claude"))
                with mock.patch.object(agent_loop, "claude_app_running", lambda: True), \
                        mock.patch.object(agent_loop, "claude_signed_in", lambda: True):
                    self.assertIsNone(agent_loop.visible_unavailable("claude"))
                with mock.patch.object(agent_loop, "CLAUDE_APP_STORE", Path(tmp) / "none"):
                    self.assertIn("isn't installed", agent_loop.visible_unavailable("claude"))
                with mock.patch.object(agent_loop.sys, "platform", "linux"):
                    self.assertIn("macOS", agent_loop.visible_unavailable("codex"))

    def test_decision_8_other_hosts_are_unaffected(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof = {"hosts": {"gemini": "echo {prompt}"}}
            code, _, message, _, _ = agent_loop.run_turn("gemini", prof, "g", "medium", Path(tmp), "hi", None, 10)
        self.assertEqual((code, message, agent_loop.SESSION_PATH), (0, "hi", {}))

    def test_decision_8_codex_events_read_only_whole_new_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "r.jsonl"
            f.write_text('{"a": 1}\n{"b": 2}\n{"c"')
            events, offset = agent_loop.new_events(f, 0)
            self.assertEqual(events, [{"a": 1}, {"b": 2}])
            with open(f, "a") as h:
                h.write(': 3}\n')
            self.assertEqual(agent_loop.new_events(f, offset)[0], [{"c": 3}])


BOUNDS_PROFILE = PROFILE + ("- **Licences and paths not to touch:** no GPL code; never modify ../other-repo\n"
                            "- **Human decides:** spending and publishing\n")
ECHO_HOST = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "role": "build"}) + "\\n")
print("NEEDS_CONTEXT: which device?")
"""


class Fold(Repo):
    """Fold-learnings part B (workbench/fold-learnings-2026-11-09/PLAN.md items 5-8)."""

    def bounds(self):
        (self.wt / "ORCHESTRATE.md").write_text(BOUNDS_PROFILE)
        self.commit_all()

    # Item 5: constraints that survive a resumed turn.

    def test_item5_a_resumed_claude_turn_restates_the_binding_constraints(self):
        self.bounds()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        self.run_loop(host="claude")
        result = self.run_loop(host="claude", message="Use the simulator.")
        first, resumed = (self.prompt(c) for c in self.calls())
        self.assertNotIn("Still binding", first)
        message, _, restated = resumed.partition("\n\n")
        self.assertEqual(message, "Use the simulator.")
        for part in ("In docs/plans/WATER/DONE.json, change only M1's items' status and evidence, and its state only to in_progress.",
                     f"`python3 {agent_loop.LOOP} merge --worktree .`",
                     "The project's rules are in ORCHESTRATE.md; re-read them"):
            self.assertIn(part, restated)
        self.assertNotIn("no GPL code", restated, "the rules are pointed to, not copied")
        self.assertTrue(restated.startswith("Still binding: the goal is every item of M1 pass with evidence"))
        self.assertLessEqual(len(restated.split()), 90, "the restatement stays terse")
        self.assertNotIn("constraints_missing", result)

    def test_item5_a_turn_resumed_inside_a_run_restates_too(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        self.assertEqual(self.run_loop(host="claude")["result"], "CHECKS_FAILED")
        later = [self.prompt(c) for c in self.calls()[1:]]
        self.assertEqual(len(later), 2)
        for p in later:
            self.assertTrue(p.startswith("The script can't set the milestone to Ready for Review yet"), p[:200])
            self.assertIn("Still binding: the goal is every item of M1 pass with evidence", p)

    def test_item5_codex_restates_only_when_no_goal_is_active_and_records_the_goal(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        self.assertEqual(self.run_loop()["goal"], "none")
        self.run_loop(message="Use the simulator.")
        self.assertIn("\n\nStill binding: the goal is every item of M1 pass with evidence", self.prompt(self.calls()[-1]))
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        before = len(self.calls())
        os.environ.update(FAKE_REPLY="BLOCKED: no device")  # a plain block keeps one more turn while the goal is active
        result = self.run_loop(message="Use the simulator.")
        self.assertEqual(result["goal"], "active")
        prompts = [self.prompt(c) for c in self.calls()[before:]]
        self.assertEqual(prompts, ["Use the simulator.", "Continue the objective. Still open: M1.1."])

    def test_item5_a_generic_host_continuation_restates(self):
        host = self.root / "echo-host"
        host.write_text(ECHO_HOST)
        host.chmod(0o755)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + f"- **Host echo:** {host} {{prompt}}\n- **Echo model:** m\n")
        self.commit_all()
        self.run_loop(host="echo")
        self.run_loop(host="echo", message="Use the simulator.")  # the missing fact lifts the block
        first, second = (c["argv"][-1] for c in self.calls())
        self.assertNotIn("Still binding", first)
        self.assertTrue(second.startswith("Build milestone M1 of module WATER,"), second[:200])  # the whole task again
        self.assertIn("From the lead:\nUse the simulator.", second)
        self.assertTrue(second.endswith("`NEEDS_CONTEXT: <the fact you need>`."), second[-200:])

    def test_item5_a_missing_out_of_bounds_line_is_reported_not_guessed(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop(host="claude")
        result = self.run_loop(host="claude", message="go on")
        self.assertEqual(result["constraints_missing"], list(agent_loop.BOUNDS))
        restated = self.prompt(self.calls()[-1])
        self.assertNotIn("ORCHESTRATE.md", restated, "no rules to point to")
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Human decides:** <e.g. spending>\n")
        self.assertIsNone(agent_loop.profile(self.wt)["bounds"]["Human decides"], "a placeholder isn't a rule")


    # Item 6: launch records.

    def test_item6_a_visible_review_records_what_the_rollout_showed(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_VERSION="codex-cli 0.167.0")
        with FakeCodexApp(self).installed():
            commit = self.run_loop()["commit"]
            self.assertEqual(self.review(commit=commit, effort="high")["verdict"], "PASS")
        rec = self.read_record()["milestones"]["M1"]
        self.assertEqual(rec["ready_for_review"]["observed"], {"model": "gpt-6.1-sol", "effort": "medium"})
        review = rec["reviews"][-1]
        self.assertEqual({k: review[k] for k in ("model", "effort", "observed", "cli", "path")},
                         {"model": "gpt-6.1-sol", "effort": "high", "cli": "codex-cli 0.167.0", "path": "visible",
                          "observed": {"model": "gpt-6.1-sol", "effort": "high"}})


    def test_a_visible_review_stops_a_hung_tool_call_and_a_timeout_is_named(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        with FakeCodexApp(self).installed():
            commit = self.run_loop()["commit"]
        with FakeCodexApp(self, behaviour="hang").installed():
            result = self.review(commit=commit, host="codex", turn_timeout_hours=0.1 / 3600)
        self.assertEqual(result["result"], "HOST_FAILED")
        self.assertIn("the review turn on codex was stopped: the turn reached the", result["reason"])
        self.assertNotIn("quota", result["reason"])
        with FakeCodexApp(self, behaviour="hung_call").installed() as app, \
                mock.patch.object(agent_loop, "TOOL_CALL_LIMIT_S", 0.05):
            result = self.review(commit=commit, host="codex")
        self.assertEqual(result["verdict"], "PASS")  # resumed after the stop, and told which call hung
        self.assertEqual(len(app.interrupts), 1)
        self.assertIn("the tool call mcp__cua_repl.js had been open for", app.sent[-1])

    # Item 7: the loader check runs on the resolved launch.


    def test_item7_a_skill_missing_where_the_host_loads_it_is_a_warning(self):
        warn = agent_loop.skill_warnings
        self.assertIn("review-milestone isn't installed where claude", warn("claude", self.wt, "review")[0])
        self.assertIn("plan-module isn't installed where codex", warn("codex", self.wt, "plan")[0])
        self.assertEqual(warn("echo", self.wt, "build"), [])
        for folder in (agent_loop.CLAUDE_HOME / "skills/review-milestone",
                       agent_loop.AGENTS_HOME / "skills/plan-module", self.home / "skills/build-milestone"):
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("x")
        self.assertEqual(warn("claude", self.wt, "review"), [])
        self.assertEqual(warn("codex", self.wt, "plan"), [])
        self.assertIn("docs don't list", warn("codex", self.wt, "build")[0])
        plugin = agent_loop.CLAUDE_HOME / "plugins/cache/m/orchestrate/1.0/skills/plan-module"
        plugin.mkdir(parents=True)
        (plugin / "SKILL.md").write_text("x")
        self.assertEqual(warn("claude", self.wt, "plan"), [])

    # Item 8: reviewers and planners start with no inherited context.

    def fresh_review_and_plan(self, host, resume_flag):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        commit = self.run_loop(host=host)["commit"]
        builder = self.calls()[-1]
        self.assertEqual(self.review(commit=commit, host=host)["verdict"], "PASS")
        self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="plan PAY", host=host, model=None, effort=None,
                  turn_timeout_hours=0.1)
        for role in ("review", "plan"):
            call = next(c for c in self.calls() if c["role"] == role)
            self.assertNotIn(resume_flag, call["argv"], f"{host} {role} resumes nothing")
            first = "Review milestone M1 of module WATER, using the review-milestone skill" if role == "review" \
                else "plan PAY"
            self.assertTrue(self.prompt(call).startswith(first), f"{host} {role} gets only its own task")
            if role == "plan":
                self.assertIn("plan-module skill", self.prompt(call))
            if role == "review":
                self.assertNotEqual(call["cwd"], builder["cwd"], "a clean checkout, not the builder's tree")

    def test_item8_codex_reviewers_and_planners_start_a_new_session(self):
        self.fresh_review_and_plan("codex", "resume")

    def test_item8_claude_reviewers_and_planners_start_a_new_session(self):
        self.fresh_review_and_plan("claude", "--resume")


class FoldAlone(ProfileOnly):
    """Tests from Fold that need no repository, only the project settings."""

    def test_item5_a_rule_that_runs_over_several_lines_is_restated_whole(self):
        (self.wt / "ORCHESTRATE.md").write_text(
            PROFILE + "- **Licences and paths not to touch:** no GPL code.\n"
            "  Never modify Broadsides.\n"
            "  - Gate order and tuning is the agents' call.\n"
            "- **Human decides:** spending\n  and publishing.\n\n## Targets\n")
        prof = agent_loop.profile(self.wt)
        self.assertEqual(prof["bounds"]["Licences and paths not to touch"],
                         "no GPL code. Never modify Broadsides; Gate order and tuning is the agents' call.")
        self.assertEqual(prof["bounds"]["Human decides"], "spending and publishing.")
        text, missing = agent_loop.binding(prof, "build", "M1", None, "d.json")
        self.assertIn("The project's rules are in ORCHESTRATE.md", text)
        self.assertEqual(missing, [])

    def test_item6_one_unverified_turn_drops_a_field_for_good(self):
        self.assertEqual(agent_loop.still_observed(None, {"model": "m"}), {"model": "m"})
        self.assertEqual(agent_loop.still_observed({"model": "m"}, {}), {})
        self.assertEqual(agent_loop.still_observed({}, {"model": "m"}), {})

    def test_item7_which_instruction_files_stop_claude_reading_agents_md(self):
        wt = self.wt
        (wt / "AGENTS.md").write_text("rules")
        check = agent_loop.instruction_warnings
        self.assertEqual(check(wt, "2.1.300 (Claude Code)"), [])
        self.assertIn("unknown", check(wt, None)[0])
        (wt / "CLAUDE.local.md").write_text("mine")
        self.assertIn("stops Claude reading", check(wt, "2.1.300 (Claude Code)")[0])
        (wt / "CLAUDE.md").write_text("@AGENTS.md\nmore\n")
        self.assertEqual(check(wt, "2.1.100"), [], "an import works on any version")
        (wt / "CLAUDE.md").write_text("Read AGENTS.md first.\n")
        self.assertIn("CLAUDE.md", check(wt, "2.1.300")[0])
        (wt / "CLAUDE.md").unlink()
        (wt / "CLAUDE.local.md").unlink()
        (wt / "AGENTS.md").unlink()
        self.assertEqual(check(wt, "2.1.100"), [], "no AGENTS.md, nothing to load")


class Holistic(Repo):
    """Decisions 1-9 of workbench/holistic-review-2026-11-09/SYNTHESIS.md."""

    prompt = Fold.prompt

    def plan_calls(self):
        return [c for c in self.calls() if c["role"] == "plan"]

    # 1. A planner's progress report isn't a plan.

    def test_holistic_1_a_progress_report_from_the_planner_lands_nothing(self):
        os.environ.update(FAKE_PLAN="progress")
        result = self.plan()
        self.assertEqual((result["result"], result["merged"]), ("UNFINISHED", False))
        self.assertIn("wasn't `PLANNED", result["owed"])
        self.assertEqual(len(self.plan_calls()), 3, "the first turn and two nudges, no more")
        self.git("fetch", "-q", "origin")
        self.assertNotIn("PAY", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)

    def test_holistic_1_a_planner_nudged_after_a_progress_report_lands_its_plan(self):
        os.environ.update(FAKE_PLAN="late")
        result = self.plan()
        self.assertEqual((result["result"], result["merged"], result["modules"]), ("PLANNED", True, ["PAY"]))
        nudge = self.prompt(self.plan_calls()[1])
        self.assertTrue(nudge.startswith("Your last line wasn't `PLANNED`"))

    def test_a_planner_ends_with_planned_alone_and_the_script_lists_the_files(self):
        os.environ.update(FAKE_PLAN_BARE="1")
        result = self.plan()
        self.assertEqual((result["result"], result["merged"]), ("PLANNED", True))
        self.assertIn("docs/plans/PAY/DONE.json", result["files"])
        self.assertIn("docs/plans/PAY/DESIGN.md", result["files"])
        self.assertIn("end with `PLANNED` once the files are written", self.prompt(self.plan_calls()[0]))

    def test_holistic_1_a_plan_missing_its_design_is_nudged_with_the_gap_and_never_lands(self):
        os.environ.update(FAKE_PLAN="nodesign")
        result = self.plan()
        self.assertEqual((result["result"], result["merged"]), ("UNFINISHED", False))
        self.assertIn("docs/plans/PAY/DONE.json has no design at docs/plans/PAY/DESIGN.md", result["owed"])
        self.assertIn("docs/plans/PAY/DONE.json", result["set_aside"])
        self.assertIn("planner", result["stash"])

    def test_holistic_1_a_blocked_planner_lands_nothing_and_says_what_it_left(self):
        os.environ.update(FAKE_PLAN="blocked")
        result = self.plan()
        self.assertEqual((result["result"], result["merged"]), ("BLOCKED", False))
        self.assertEqual(result["set_aside"], ["docs/plans/PAY/DESIGN.md"])
        stashed = self.git("stash", "show", "--include-untracked", "--name-only", "stash@{0}").stdout.split()
        self.assertEqual(stashed, ["docs/plans/PAY/DESIGN.md"])  # kept where the lead's worktree sees it
        self.assertEqual(len(self.plan_calls()), 1)

    def test_holistic_1_named_files_must_exist_and_be_changed(self):
        owed = agent_loop.plan_owed(self.wt, agent_loop.head_commit(self.wt), "PLANNED: docs/plans/NOPE/DESIGN.md, "
                                    "docs/plans/WATER/DONE.json")
        self.assertIn("docs/plans/NOPE/DESIGN.md doesn't exist", owed)
        self.assertIn("docs/plans/WATER/DONE.json isn't changed", owed)
        self.assertIsNone(agent_loop.plan_owed(self.wt, "HEAD", "NEEDS_CONTEXT: which provider?"))

    # 2. Owner rules survive fresh sessions.

    def test_holistic_2_an_human_rule_survives_fresh_sessions_and_milestones_until_cleared(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        rule = "never edit the schema"
        self.run_loop(host="claude", human_rule=[rule])
        self.run_loop(host="claude", fresh=True, message="Findings: see the review.")
        self.run_loop(host="claude", message="go on")
        first, fresh, resumed = (self.prompt(c) for c in self.calls())
        self.assertIn("The human's rule: never edit the schema.", first)
        self.assertIn("The human's rule: never edit the schema.", fresh, "a fresh session keeps the rule")
        self.assertIn("Findings: see the review.", fresh)
        self.assertIn("The human's rule: never edit the schema.", resumed)
        self.assertEqual(self.state()["human_rules"], [rule])
        self.run_loop(host="claude", fresh=True, clear_human_rules=True, message="x is 3")
        self.assertNotIn("The human's rule:", self.prompt(self.calls()[-1]))
        self.assertEqual(self.state()["human_rules"], [])

    def test_holistic_2_an_active_codex_goal_still_gets_human_rules_added_after_it(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop()
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.run_loop(message="go on", human_rule=["keep the public API"])
        resumed = self.prompt(self.calls()[1])
        self.assertEqual(resumed, "go on\n\nThe human's rule: keep the public API.")

    # 3. Progress-only turns are capped.

    def test_holistic_3_progress_updates_stop_as_stalled_after_two_continuations_naming_open_items(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="Read the code; next I'll write the parser.")
        result = self.run_loop()
        self.assertEqual((result["result"], result["open"]), ("STALLED", ["M1.1"]))
        prompts = [self.prompt(c) for c in self.calls()]
        self.assertEqual(len(prompts), agent_loop.STALL_TURNS)
        for p in prompts[1:]:
            self.assertTrue(p.startswith("Continue the objective. Still open: M1.1."))

    def test_holistic_3_uncommitted_work_is_progress_not_a_stall(self):
        marks = agent_loop.work_marks(self.wt, None)
        (self.wt / "parser.py").write_text("x = 1")
        self.assertNotEqual(agent_loop.work_marks(self.wt, None), marks)

    # 4. No model or effort frontmatter overrides the launch.


    # 6. A resumed Claude turn restates the objective (covered with item 5 above), terse.

    # 7. Plugin installs: skills, namespaced names and agents.

    def install_plugin(self, home):
        ver = home / "plugins/cache/ryannel-skills/orchestrate/1.3.0"
        for name in ("review-milestone", "plan-module", "build-milestone"):
            (ver / "skills/orchestration" / name).mkdir(parents=True)
            (ver / "skills/orchestration" / name / "SKILL.md").write_text("x")
        (ver / "skills/orchestration/build/agents/claude").mkdir(parents=True)
        (ver / "skills/orchestration/build/agents/claude/orchestrate-reviewer.md").write_text("x")
        (ver / ".claude-plugin").mkdir()
        (ver / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": [
            {"name": "orchestrate", "skills": ["./skills/orchestration/review-milestone",
                                               "./skills/orchestration/plan-module",
                                               "./skills/orchestration/build-milestone"],
             "agents": ["./skills/orchestration/build/agents/claude/orchestrate-reviewer.md"]},
            {"name": "skill-creator", "skills": ["./skills/skill-creator"]}]}))
        # the same repository copied for another plugin doesn't provide orchestrate's skills
        other = home / "plugins/cache/ryannel-skills/skill-creator/1.0.0/skills/orchestration/build"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("x")

    def test_holistic_7_plugin_installed_skills_are_found_on_both_hosts_in_this_repos_layout(self):
        warn = agent_loop.skill_warnings
        self.install_plugin(agent_loop.CLAUDE_HOME)
        self.install_plugin(self.home)
        self.assertEqual(warn("claude", self.wt, "review"), [])
        self.assertEqual(warn("codex", self.wt, "plan"), [])
        self.assertEqual(agent_loop.plugin_components(self.home, "skills").get("build"), None)
        note = agent_loop.skill_note("review-milestone", "codex")
        self.assertTrue(note.startswith("`orchestrate:review-milestone` in Codex; the file is "), note)
        self.assertTrue(agent_loop.skill_note("review-milestone", "claude").startswith("the file is "))

    def test_holistic_7_a_plugin_agent_is_used_for_claude_reviews(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        commit = self.run_loop(host="claude")["commit"]
        self.install_plugin(agent_loop.CLAUDE_HOME)
        self.assertEqual(self.review(commit=commit, host="claude")["verdict"], "PASS")
        argv = next(c for c in self.calls() if c["role"] == "review")["argv"]
        self.assertEqual(argv[argv.index("--agent") + 1], "orchestrate-reviewer")

    # 8. The reviewer fails only on blocking defects.


class HolisticAlone(ProfileOnly):
    """Tests from Holistic that need no repository, only the project settings."""

    def test_holistic_4_no_skill_or_claude_agent_file_sets_model_or_effort(self):
        root = agent_loop.SKILLS
        files = [root / n / "SKILL.md" for n in ("build", "build-milestone", "review-milestone", "plan-module")]
        files += sorted((root / "build/agents/claude").glob("*.md"))
        for f in files:
            front = f.read_text().split("\n---\n")[0]
            self.assertNotRegex(front, r"(?m)^(model|effort):", str(f))

    def test_holistic_8_review_skill_and_findings_message_separate_blocking_from_advisory(self):
        review = (agent_loop.SKILLS / "review-milestone/SKILL.md").read_text()
        self.assertIn("A Suggestion never changes the\n`state`.", review)
        self.assertIn("Count Must Fix findings only.", review)
        self.assertNotIn("If you think the defect doesn't matter, say so in the finding", review)
        self.assertIn("finished when every item is true as it is written", agent_loop.FINDINGS_TEMPLATE)
        self.assertNotIn("Fix every", agent_loop.FINDINGS_TEMPLATE)
        self.assertIn("yours to take or leave", agent_loop.FINDINGS_TEMPLATE)


class Locks(Clean):
    def test_lock_takes_worktree_after_the_name_and_runs_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            marker = Path(tmp) / "where"
            with self.assertRaises(SystemExit) as exit_:
                agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=None, command_args=[
                    "--worktree", tmp, "--", "sh", "-c", f"pwd > {marker}"]))
            self.assertEqual(exit_.exception.code, 0)
            self.assertEqual(Path(marker.read_text().strip()).resolve(), Path(tmp).resolve())

    def test_a_held_lock_is_waited_for_only_as_long_as_the_patience(self):
        path = Path(self.enterContext(tempfile.TemporaryDirectory())) / "WATER.lock"
        hold = (f"import fcntl, sys, time; h = open({str(path)!r}, 'a+'); fcntl.flock(h, fcntl.LOCK_EX); "
                "print('up', flush=True); time.sleep(float(sys.argv[1]))")
        for held_s, patience_s, taken in ((0.3, 2.0, True), (30, 0.2, False)):
            with self.subTest(held_s=held_s, patience_s=patience_s):
                proc = subprocess.Popen([sys.executable, "-c", hold, str(held_s)], stdout=subprocess.PIPE, text=True)
                self.addCleanup(lambda p=proc: (p.kill(), p.wait(), p.stdout.close()))
                self.assertEqual(proc.stdout.readline().strip(), "up")
                started = time.time()
                handle = agent_loop.take_file_lock(path, patience_s)
                self.assertEqual(handle is not None, taken)
                self.assertGreater(time.time() - started, 0.15)  # it waited rather than giving up at once
                self.assertLess(time.time() - started, patience_s + 5)
                if handle:
                    handle.close()

    def test_lock_refuses_outside_a_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=tmp, command_args=["--", "true"]))


class CodexProject(Clean):
    PROJECTS = [{"id": "thrum", "roots": [{"path": "/w/thrum"}]},
                {"id": "sub", "roots": [{"path": "/w/thrum/tools"}]},
                {"id": "thrumbo", "roots": [{"path": "/w/thrumbo"}]}]

    def test_a_worktree_inside_the_repository_gets_its_project(self):
        self.assertEqual(agent_loop.codex_project_for(self.PROJECTS, ["/w/thrum/.claude/worktrees/x", "/w/thrum"]),
                         "thrum")

    def test_a_worktree_elsewhere_falls_back_to_the_repository(self):
        self.assertEqual(agent_loop.codex_project_for(self.PROJECTS, ["/tmp/wt/x", "/w/thrum"]), "thrum")

    def test_the_deepest_root_wins_and_names_need_a_path_boundary(self):
        self.assertEqual(agent_loop.codex_project_for(self.PROJECTS, ["/w/thrum/tools/a"]), "sub")
        self.assertIsNone(agent_loop.codex_project_for(self.PROJECTS, ["/w/thru", "/w/other"]))


class FirstRuns(Repo):
    """What the first end-to-end runs turned up (workbench e2e s1, s2, s4): the one-chat path, a first plan with its
    profile, an unplanned repository, running a milestone's checks, cost, quota's readout, stops that say what's next
    and who holds what, the review host, and the pause race. Each test is named after its item."""

    def revise_design(self):
        """What a planner does after DESIGN CHANGES: the script won't review an unchanged design again."""
        self.git("pull", "-q", "--rebase", "origin", "main")
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# Water design, revised")
        self.assertEqual(self.adopt("docs/plans/WATER/DESIGN.md")["result"], "ADOPTED")

    def edit_m2(self, check="test -n changed"):
        doc = self.read_done("HEAD")
        doc["milestones"][1]["items"][0]["check"] = check
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))

    # 1. The one-chat path

    def draft(self):
        """WATER as a draft: planned, nothing built, its design review still owed."""
        self.write_done([milestone("M1", "not_started", ["open"]), milestone("M2", "not_started", ["open"])], design_ok=False)
        self.commit_all()

    def test_item1_adopt_authorises_a_drafts_revisions_for_the_owed_design_review(self):
        self.draft()
        self.edit_m2()
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertEqual(result["authorised"], ["WATER"])
        r = self.ready()
        self.assertEqual(r.get("invalid", []), [])
        self.assertEqual(r["design_not_approved"], [{"module": "WATER"}])
        stamp = self.read_record()["milestones"]["M2"]["authorised"]
        self.assertEqual(stamp["by"], "adopt")
        self.assertIn("before the module's design review passed", stamp["why"])
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("## Definitions changed through adopt", report)
        self.assertIn("WATER M2: definitions authorised by adopt", report)
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")  # after the design review judged them

    def test_item1_a_lead_cant_weaken_checks_once_the_design_review_passed(self):
        """The reviewer's probe: design agreed, nothing built, a check rewritten to `true`."""
        m1 = milestone("M1", "not_started", ["open", "open"], inspect="the frames match the spec")
        m1["items"][0]["check"] = "cargo test --test physics -- --exact solver_converges"
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["check"] = "true"
        doc["milestones"][0]["items"][1].pop("inspect", None)
        doc["milestones"][0]["items"][1]["check"] = "true"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED", result)
        self.assertIn("a design review of it has passed", result["problems"][0])
        self.assertIn(" human scope --module WATER --milestone M1 ", result["next"]["human"])
        self.assertEqual(self.read_done()["milestones"][0]["items"][0]["check"],
                         "cargo test --test physics -- --exact solver_converges")
        self.assertEqual(self.run_loop()["result"], "INVALID")  # the edit here still isn't authorised

    def test_item1_a_claim_alone_closes_the_draft(self):
        self.draft()
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.assertTrue(agent_loop.take_hold(other, prof, "WATER", "M1")[0])  # taken, nothing accepted
        self.edit_m2()
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED", result)
        self.assertIn("building on it has begun", result["problems"][0])
        self.assertIn(" plan --worktree ", result["next"]["command"])

    def test_item1_a_run_holding_the_module_closes_the_draft(self):
        self.draft()
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER', milestone='M1', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            self.edit_m2()
            result = self.adopt()
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
        self.assertEqual(result["result"], "REFUSED", result)
        self.assertIn("a run holds it", result["problems"][0])

    def test_item1_a_claim_made_while_adopt_lands_stops_the_authorising(self):
        self.draft()
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        real_land, calls = agent_loop.land, []

        def land(tree, prof_, check=True):
            calls.append(tree)
            if len(calls) == 1:  # while the plan files land (the Check can take minutes), another clone claims
                self.assertTrue(agent_loop.take_hold(other, prof, "WATER", "M1")[0])
            return real_land(tree, prof_, check=check)
        self.edit_m2()
        with mock.patch.object(agent_loop, "land", land):
            result = self.adopt()
        self.assertEqual(result["result"], "FAILED", result)
        self.assertIn("weren't authorised", result["detail"])
        self.assertNotEqual((self.read_record()["milestones"]["M2"].get("authorised") or {}).get("by"), "adopt")
        self.assertEqual(len(calls), 1)  # the authorising commit never went

    # 2. A first plan lands whole

    def test_item2_adopt_lands_a_first_profile_and_only_names_a_changed_one(self):
        self.git("rm", "-q", "ORCHESTRATE.md")
        self.commit_all()
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE)
        self.assertIn("ORCHESTRATE.md", self.ready()["unmerged_plans"]["uncommitted"])
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertIn("ORCHESTRATE.md", result["files"])
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("show", "origin/main:ORCHESTRATE.md").stdout, PROFILE)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** high\n")
        self.assertIn("differs from the one at origin/main", self.ready()["settings_differ"])
        self.assertIn("differs from the one at origin/main", self.printed(agent_loop.cmd_status, module=None,
                                                                           worktree=str(self.wt)))
        refused = self.adopt("ORCHESTRATE.md")
        self.assertEqual(refused["result"], "REFUSED")
        self.assertIn("the lead commits and merges it with git once the human has agreed", refused["problems"][0])
        self.assertIn("once the human has agreed to it", self.ready()["settings_differ"])
        nothing = self.adopt()
        self.assertEqual(nothing["result"], "NOTHING")
        self.assertIn("settings_differ", nothing)

    def test_item2_adopt_lands_build_reports(self):
        (self.wt / "docs/evidence/build-reports").mkdir(parents=True)
        (self.wt / "docs/evidence/build-reports/2026-11-10.md").write_text("# Build report")
        result = self.adopt()
        self.assertEqual((result["result"], result["files"]),
                         ("ADOPTED", ["docs/evidence/build-reports/2026-11-10.md"]))

    # 3. An unplanned repository

    def test_item3_an_unplanned_repository_says_so_and_names_plan(self):
        self.git("rm", "-q", "-r", "ORCHESTRATE.md", "docs")
        self.commit_all()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            r = self.ready()
            status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
            prof = json.loads(self.printed(agent_loop.cmd_settings, code=1, worktree=str(self.wt), host=None))
            run = self.run_loop()
        self.assertIn("isn't planned yet", r["unplanned"])
        self.assertIn(" plan --worktree ", r["next"]["command"])
        self.assertTrue(status.startswith("The project isn't planned yet"), status)
        self.assertIn(" plan --worktree ", status)
        self.assertEqual((prof["planned"], " plan --worktree " in prof["next"]["command"]), (False, True))
        self.assertEqual(run["result"], "INVALID")
        self.assertIn(" plan --worktree ", run["next"]["command"])
        self.assertNotIn("no ORCHESTRATE.md", err.getvalue())
        self.assertFalse(self.log.exists())

    # 4. A milestone's checks against a tree

    def test_item4_check_tells_not_built_from_broken(self):
        self.write_done([milestone("M1", "not_started", ["open", "open", "open"]), milestone("M2", "not_started", ["open"])])
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        checks = ["true", "test -f built.txt", "if then"]
        # not built yet, a failing test whose output looks like shell trouble, and one that doesn't parse
        for i, check in zip(doc["milestones"][0]["items"], checks):
            i["check"] = check
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        out = json.loads(self.printed(agent_loop.cmd_check, code=1, module="WATER", milestone="M1",
                                      worktree=str(self.wt), plans_from=None, timeout=60.0, json=True))
        self.assertEqual([i["result"] for i in out["items"]], ["pass", "fail", "error"])
        self.assertEqual((out["pass"], out["fail"], out["error"]), (1, 1, 1))
        self.assertIn("doesn't parse as shell", out["items"][2]["why"])
        self.assertIn("without changing what it tests", out["items"][2]["why"])
        cases = {"./bin/newtool --version": "fail", "echo 'unexpected EOF, unmatched quote' >&2; exit 1": "fail",
                 # a syntax error is never certain to be the check's: exec'd files report themselves as inline code
                 "python3 -c 'import sys; sys.exit(1'": "fail", "if then": "error", "python3 -m no_such_mod": "fail",
                 # a tool that isn't installed yet is not built, not broken
                 "no-such-command-here --flag": "fail"}
        # a syntax error in a file the inline code imports is the work, not the check
        (self.wt / "brokenmod.py").write_text("def f(:\n")
        cases["python3 -c 'import brokenmod'"] = "fail"
        cases["python3 -c \"exec(open('brokenmod.py').read())\""] = "fail"
        for command, expected in cases.items():
            self.assertEqual(agent_loop.try_check(self.wt, command, None, 30)["result"], expected, command)
        (self.wt / "built.txt").write_text("x")
        doc["milestones"][0]["items"][2]["check"] = "true"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        out = json.loads(self.printed(agent_loop.cmd_check, code=0, module="WATER", milestone="M1",
                                      worktree=str(self.wt), plans_from=None, timeout=60.0, json=True))
        self.assertEqual(out["pass"], 3)

    def test_a_planner_tries_its_item_checks_without_the_test_command(self):
        self.write_done([milestone("M1", "not_started", ["open"])])
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("**Test command:** none", "**Test command:** false"))
        kw = dict(module="WATER", milestone="M1", worktree=str(self.wt), plans_from=None, timeout=60.0, json=True)
        everything = json.loads(self.printed(agent_loop.cmd_check, code=1, **kw))
        self.assertEqual(everything["items"][-1]["id"], "Test command")
        items = json.loads(self.printed(agent_loop.cmd_check, code=0, items_only=True, **kw))
        self.assertEqual([i["id"] for i in items["items"]], ["M1.1"])

    # 5. Cost in one place


    def test_item5_every_turn_lands_in_the_ledger_and_cost_adds_it_up(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_USAGE="1", FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertEqual(result["design_review"]["verdict"], "DESIGN OK")
        self.assertEqual(result["design_review"]["usage"]["output"], 7)
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=result["commit"])
        rows = agent_loop.ledger_rows(self.wt)
        self.assertEqual([(r["role"], r["milestone"]) for r in rows],
                         [("review", "design"), ("build", "M1"), ("review", "M1")])
        c = json.loads(self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=True))
        self.assertEqual(c["modules"]["WATER"]["M1"]["build"]["output"], 7)
        self.assertEqual(c["modules"]["WATER"]["design"]["review"]["runs"], 1)
        self.assertEqual(c["total"]["output"], 21)
        text = self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=False)
        self.assertIn("WATER M1: build 1 turn, tokens 60 in, 40 cached, 7 out on codex; review 1 turn", text)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=True)
        written = json.loads(report)["written"]
        self.assertTrue(written.startswith("docs/evidence/build-reports/"))
        body = (self.wt / written).read_text()
        self.assertIn("- WATER M1: accepted by review", body)
        self.assertIn("fewer than about ten, so spot-check every one", body)
        self.assertEqual(self.adopt()["result"], "ADOPTED")

    # 6. quota


    def test_item6_quota_reads_out_the_rate_and_verdict_first_and_json_behind_a_flag(self):
        acc = {"used_percent": 30.0, "resets_at": "2026-11-12T00:00:00Z", "hours_left": 40.0, "complete": True,
               "recent": {"hours": 12, "burn": {}}, "outside": {"pct": 0.5},
               "use_this_window": {"runs_pct": [1.0, 1.2, 1.4], "other_local_pct": [0.0, 0.0, 0.0],
                                   "elsewhere_pct": 0.5},
               "forecast": {"verdict": "Quota lasts: x.", "warn": False}}
        with mock.patch.object(agent_loop, "quota_report", lambda *a, **k: acc):
            text = self.printed(agent_loop.cmd_quota, worktree=None, budget=1.0, json=False)
            raw = json.loads(self.printed(agent_loop.cmd_quota, worktree=None, budget=1.0, json=True))
        self.assertTrue(text.startswith("70% left and 40 h to the reset.\nQuota lasts: x."), text)
        self.assertIn("1.2% by orchestrate runs on this machine (any repository)", text)
        self.assertIn("from elsewhere", text)
        self.assertEqual(raw["used_percent"], 30.0)

    # 7. Stops that say what's next and who holds what

    def test_item7_reviewed_and_planned_name_what_comes_next(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        changes = self.review("design", commit=None)
        self.assertEqual((changes["verdict"], changes["next"]["by"]), ("DESIGN CHANGES", "planner"))
        self.assertIn(" plan --worktree ", changes["next"]["command"])
        self.assertEqual(changes["next"]["findings"], "docs/evidence/WATER/design-review.md")
        self.revise_design()
        os.environ.update(FAKE_REVIEW="design")
        ok = self.review("design", commit=None)
        self.assertEqual(ok["verdict"], "DESIGN OK")
        self.assertIn(" run --module WATER ", ok["next"]["command"])
        # a second design review keeps the first
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("show", "origin/main:docs/evidence/WATER/design-review-1.md").stdout,
                         "the design needs a second pass")
        os.environ.update(FAKE_REVIEW="pass")
        claim = self.run_loop()
        passed = self.review(commit=claim["commit"])
        self.assertEqual(passed["verdict"], "PASS")
        self.assertIn(" run --module WATER ", passed["next"]["command"])
        os.environ.pop("FAKE_PLAN", None)
        planned = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Plan PAY", host=None, model=None,
                            effort=None, turn_timeout_hours=0.1)
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertIn(" review --module PAY --milestone design ", planned["next"]["command"])

    def test_item7_the_last_pass_says_the_module_is_finished(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames")])
        self.commit_all()
        claim = self.run_loop()
        passed = self.review(commit=claim["commit"])
        self.assertIsNone(passed["next"]["command"])
        self.assertIn("finished", passed["next"]["why"])
        self.assertIn("git worktree remove", passed["next"]["why"])
        # the loop's own checkout of a finished module is gone, and `ready` clears one left from before
        verify = agent_loop.loop_dir(self.wt) / "verify" / "WATER"
        self.assertFalse(verify.exists())
        agent_loop.verify_tree(self.wt, "WATER", "HEAD")
        self.assertTrue(verify.exists())
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.ready()
        self.assertFalse(verify.exists())

    def test_item7_taken_says_who_holds_it(self):
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER', milestone='M1', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            result = self.run_loop()
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
        self.assertEqual(result["result"], "TAKEN")
        self.assertEqual(result["holder"]["pid"], proc.pid)
        self.assertEqual(result["holder"]["worktree"], str(self.wt))
        self.assertIn(f"pid {proc.pid}", result["by"])

    def test_item7_status_marks_an_unchecked_claim_and_profile_hides_the_codex_model(self):
        self.write_done([milestone("M1", "done", ["pass"]), milestone("M2", "not_started", ["open"])], authorise=False)
        self.commit_all()  # the builder's file says done; the loop has checked nothing
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        line = next(l for l in status.splitlines() if l.strip().startswith("M1"))
        self.assertIn("done, unchecked", line)
        self.assertIn("the script hasn't checked this yet; `run` checks it", line)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("codex", "claude") + "- **Codex model:** gpt-x\n")
        prof = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host=None))
        self.assertNotIn("model", prof)

    # 8. Reviews on the right host

    def test_item8_the_profile_sends_reviews_to_the_other_host(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames")], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertEqual(result["design_review"]["host"], "claude")
        os.environ.update(FAKE_REVIEW="pass")
        review = self.review(commit=result["commit"])
        self.assertEqual((review["verdict"], review["host"]), ("PASS", "claude"))
        builds = [c for c in self.calls() if c["role"] == "build"]
        self.assertEqual(builds[0]["argv"][0], "exec")  # codex built it

    def test_item8_review_host_flag_wins(self):
        self.write_done([milestone("M1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        result = self.run_loop(review_host="claude")
        self.assertEqual(result["design_review"]["host"], "claude")
        self.assertEqual(agent_loop.review_host({"review_host": ""}, "codex"), "codex")
        self.assertEqual(agent_loop.review_host({"review_host": "other"}, "claude"), "codex")
        self.assertEqual(agent_loop.review_host({"review_host": "other"}, "codex", "codex"), "codex")

    # 9. The pause race

    def test_item9_pause_and_status_never_lock_a_run_lock(self):
        """An older copy of the script takes the run lock without waiting, so nothing but a run may lock it, even for
        a moment: `pause`, `status`, `loops` and the TAKEN holder find liveness without it."""
        self.assertTrue(agent_loop.run_lock(self.wt, "WATER"))
        release()
        import fcntl
        real, touched = fcntl.flock, []

        def flock(handle, op):
            name = getattr(handle, "name", "")
            if isinstance(name, str) and Path(name).name.startswith("run-"):
                touched.append((name, op))
            return real(handle, op)
        with mock.patch.object(fcntl, "flock", flock):
            self.printed(agent_loop.cmd_pause, module=None, worktree=str(self.wt))
            self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
            self.printed(agent_loop.cmd_loops, repo=str(self.wt), json=True)
            agent_loop.run_holder_info(self.wt, "WATER")
        self.assertEqual(touched, [])

    def test_item9_a_run_lock_file_outlives_its_process_and_counts_for_nothing(self):
        code = (f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); assert agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER', host='codex', model='m', effort='medium')\n")
        subprocess.run([sys.executable, "-c", code], check=True)  # a real process, ending normally
        path = agent_loop.loop_dir(self.wt) / "run-WATER.lock"
        self.assertTrue(path.exists())  # left in place: an older copy may have it open
        self.assertIsNone(agent_loop.run_holder(path.parent, "WATER"))
        self.assertNotIn("running", self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt)))
        import fcntl
        with open(path, "a+") as old_copy:  # how an older copy takes it
            fcntl.flock(old_copy, fcntl.LOCK_EX | fcntl.LOCK_NB)

    # 5 and 7. Claims count what they spent; Claude's cost per turn

    def test_item5_each_claim_records_what_it_spent_since_the_last(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_USAGE="1")
        first = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        self.review(commit=first["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        second = self.run_loop(message="FINDINGS")
        self.assertEqual(second["result"], "READY_FOR_REVIEW", second)
        claim = self.read_record()["milestones"]["M1"]["ready_for_review"]
        self.assertEqual(claim["usage"]["output"], 7)  # this round only
        self.assertEqual(claim["session_usage"]["output"], 14)  # the session so far
        self.assertEqual(second["usage"]["output"], 14)  # the result line's meaning is unchanged

    def test_item7_a_resumed_claude_turn_costs_only_the_rise_in_its_sessions_total(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which colour?", FAKE_COST="0.5")
        self.assertEqual(self.run_loop(host="claude")["reason"], "needs_context")
        os.environ.update(FAKE_PASS="1", FAKE_REPLY="DONE", FAKE_COST="0.8")
        self.assertEqual(self.run_loop(host="claude", message="blue")["result"], "READY_FOR_REVIEW")
        rows = agent_loop.ledger_rows(self.wt)
        self.assertEqual([r["usage"]["cost_usd"] for r in rows], [0.5, 0.3])
        self.assertEqual(rows[1]["session"], rows[0]["session"])
        self.assertEqual(self.read_record()["milestones"]["M1"]["ready_for_review"]["usage"]["cost_usd"], 0.8)

    # 8. Human Feedback on items a builder can't judge

    def test_item8_human_feedback_goes_through_the_record_and_into_the_prompts(self):
        m1 = milestone("M1", "not_started", ["open", "open", "open"], inspect="frames")
        m1["items"][1]["needs"] = needs("human_feedback", "the human picks a direction")
        m1["items"][2]["needs"] = needs("human_feedback", "the human judges the ink")
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_STATE="in_progress", FAKE_REPLY="BLOCKED: M1.2 needs the human")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_human_feedback"), blocked)
        self.assertEqual(blocked["next"]["decides"], "human")
        self.assertIn(" human feedback --module WATER --milestone M1 --item M1.2 --item M1.3 ",
                      blocked["next"]["command"])
        self.assertIn("--asked '", blocked["next"]["command"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        given = self.human("feedback", "M1", "Direction B, the ink one.", item=["M1.2", "M1.3"],
                           asked="Which direction do you want, A or B?")
        self.assertEqual((given["result"], given["unblocked"]), ("DONE", True))
        [entry] = self.read_record()["milestones"]["M1"]["human_feedback"]
        self.assertEqual((entry["asked"], entry["said"], entry["items"]),
                         ("Which direction do you want, A or B?", "Direction B, the ink one.", ["M1.2", "M1.3"]))
        self.assertTrue(entry["at"])
        self.assertEqual(self.read_done()["milestones"][0]["state"], "in_progress")
        for key in ("FAKE_SKIP_NEEDS", "FAKE_STATE"):
            os.environ.pop(key)
        os.environ.update(FAKE_REPLY="DONE")
        claim = self.run_loop(fresh=True, message="Show the ink direction first.")
        self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
        prompt = self.calls()[-1]["argv"][-1]
        order = [prompt.find(part) for part in (
            "Build milestone M1 of module WATER,", "The goal: ", "Human Feedback on M1", "\nAbout this session:\n",
            "\nFrom the lead:\nShow the ink direction first.", "\nTo finish: ")]
        self.assertTrue(all(i >= 0 for i in order) and order == sorted(order), (order, prompt))
        self.assertIn('on M1.2, M1.3: asked "Which direction do you want, A or B?"; '
                      'the human said "Direction B, the ink one."', prompt)
        self.assertEqual(prompt.count(f"python3 {agent_loop.LOOP}"), 1, "the script's path is given once")
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        self.assertIn("milestones.M1.human_feedback", self.calls()[-1]["argv"][-1])

    def test_item8_feedback_needs_the_question_and_only_covers_items_that_need_human_feedback(self):
        m1 = milestone("M1", "not_started", ["open", "open", "open"])
        m1["items"][1]["needs"] = needs("hardware", "plug in the iPhone")
        m1["items"][2]["needs"] = needs("human_feedback", "the human judges the ink")
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.assertIn("ORCHESTRATE_VISIBLE=1", self.refused_feedback("M1", ["M1.2"]))
        self.assertIn("isn't marked as needing human feedback", self.refused_feedback("M1", ["M1.1"]))
        try:
            with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
                agent_loop.cmd_human(argparse.Namespace(action="feedback", module="WATER", milestone="M1",
                                                        item=["M1.3"], text=None, said="fine", asked=None,
                                                        worktree=str(self.wt)))
        finally:
            release()
        self.assertIn("needs --asked", str(stop.exception))
        self.assertNotIn("human_feedback", self.read_record()["milestones"]["M1"])
        self.assertEqual(self.human("feedback", "M1", "The ink reads well.", item="M1.3")["result"], "DONE")

    # 9. Captures beside the review

    def test_item9_a_reviewers_captures_land_beside_the_review(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="pass", FAKE_CAPTURE="1")
        result = self.review(commit=claim["commit"])
        self.assertEqual(result["verdict"], "PASS", result)
        self.git("fetch", "-q", "origin")
        self.assertIn("PNG", self.git("show", "origin/main:docs/evidence/WATER/M1-review/shot.png").stdout)

    # 10. Owner commands

    def test_item10_an_human_command_needs_the_humans_words(self):
        with self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_human(argparse.Namespace(action="accept", module="WATER", milestone="M1", item=None,
                                                    text="  ", worktree=str(self.wt)))
        self.assertIn("human accept needs --text, the human's words", str(stop.exception))

    def test_item10_human_scope_leaves_the_worktree_clean(self):
        self.edit_m2()
        result = self.human("scope", "M2")
        self.assertEqual(result["result"], "DONE", result)
        self.assertTrue(result["worktree"].startswith("fast-forwarded"), result)
        self.assertEqual(self.git("status", "--porcelain").stdout.strip(), "")
        self.assertEqual(self.read_done("HEAD")["milestones"][1]["items"][0]["check"], "test -n changed")

    # 11. A planner's report keeps its end


    # Round four: the commands tried on finished projects

    def test_r4_cost_falls_back_to_the_committed_record_when_the_ledger_has_nothing(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_USAGE="1", FAKE_REVIEW="design")
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        ledger = Path(self.git("rev-parse", "--git-common-dir").stdout.strip())
        ledger = (ledger if ledger.is_absolute() else self.wt / ledger) / "orchestrate" / "usage.jsonl"
        ledger.unlink()  # a clone, or a project built before the ledger existed
        self.assertEqual(agent_loop.ledger_rows(self.wt), [])
        c = json.loads(self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=True))
        self.assertTrue(c["from_records"])
        self.assertEqual(c["modules"]["WATER"]["M1"]["source"], "records")
        self.assertEqual(c["modules"]["WATER"]["M1"]["build"]["output"], 7)
        self.assertEqual(c["modules"]["WATER"]["design"]["review"]["runs"], 1)
        text = self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=False)
        self.assertNotIn("no turns recorded", text)
        self.assertIn("WATER M1: build 1 turn", text)
        self.assertIn("[from the committed record]", text)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("[from the committed record]", report)
        # where the ledger has a milestone, it wins and isn't marked
        ledger.write_text(json.dumps({"at": agent_loop.now(), "role": "build", "module": "WATER", "milestone": "M2",
                                      "host": "codex", "usage": {"input": 1, "cached": 0, "output": 1}}) + "\n")
        c = json.loads(self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=True))
        self.assertEqual(c["modules"]["WATER"]["M2"]["source"], "ledger")
        self.assertEqual(c["modules"]["WATER"]["M1"]["source"], "records")

    def test_r4_check_reads_out_per_item_and_json_behind_a_flag(self):
        self.write_done([milestone("M1", "not_started", ["open", "open"]), milestone("M2", "not_started", ["open"])])
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        doc["milestones"][0]["items"][0]["check"] = "true"
        doc["milestones"][0]["items"][1]["check"] = "echo nope-not-built; exit 3"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        kw = dict(module="WATER", milestone="M1", worktree=str(self.wt), plans_from=None, timeout=60.0)
        text = self.printed(agent_loop.cmd_check, code=1, json=False, **kw)
        self.assertRaises(json.JSONDecodeError, json.loads, text)
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("WATER M1 in "), text)
        self.assertIn("1 pass, 1 fail", lines[0])
        self.assertIn("  M1.1  pass  true", text)
        self.assertIn("  M1.2  fail (exit 3)  echo nope-not-built; exit 3", text)
        self.assertIn("| nope-not-built", text)
        self.assertIn("--json", lines[-1])
        out = json.loads(self.printed(agent_loop.cmd_check, code=1, json=True, **kw))
        self.assertEqual([i["result"] for i in out["items"]], ["pass", "fail"])

    def test_r4_adopt_leaves_a_record_so_a_turned_away_run_names_it(self):
        self.draft()
        self.edit_m2()
        seen, real = [], agent_loop.land

        def land(*a, **k):
            seen.append(agent_loop.run_holder_info(self.wt, "WATER"))
            return real(*a, **k)

        with mock.patch.object(agent_loop, "land", land):
            self.assertEqual(self.adopt()["result"], "ADOPTED")
        self.assertTrue(seen)
        self.assertEqual(seen[0]["role"], "adopt", seen)
        self.assertEqual(seen[0]["pid"], os.getpid())
        self.assertIn("adopt", agent_loop.holder_text(seen[0]))

    def test_r4_a_repository_with_no_commits_says_what_to_do(self):
        empty, origin = self.root / "empty", self.root / "empty-origin.git"
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(origin))
        self.sh("git", "init", "-q", "-b", "main", str(empty))
        self.git("remote", "add", "origin", str(origin), where=empty)
        (empty / "ORCHESTRATE.md").write_text(PROFILE)  # the human's profile, waiting for adopt to land it
        adopted = self.call(agent_loop.cmd_adopt, worktree=str(empty), message=None, paths=[])
        self.assertEqual(adopted["result"], "FAILED", adopted)
        self.assertIn("no commits yet", adopted["detail"])
        self.assertNotIn("fatal:", adopted["detail"])
        self.assertIn("commit --allow-empty", adopted["next"]["command"])
        self.assertIn("push -u origin main", adopted["next"]["command"])
        before = self.log.read_text() if self.log.exists() else ""
        planned = self.call(agent_loop.cmd_plan, worktree=str(empty), task="Plan the project", host=None, model=None,
                            effort=None, turn_timeout_hours=0.1)
        self.assertEqual(planned["result"], "SCRIPT_FAILED", planned)
        self.assertIn("no commits yet", planned["reason"])
        self.assertIn("commit --allow-empty", planned["next"]["command"])
        self.assertEqual(self.log.read_text() if self.log.exists() else "", before)  # no planner turn spent
        # a local commit with origin still empty: push it
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "Initial commit",
                 where=empty)
        adopted = self.call(agent_loop.cmd_adopt, worktree=str(empty), message=None, paths=[])
        self.assertEqual(adopted["result"], "FAILED", adopted)
        self.assertIn("push -u origin main", adopted["next"]["command"])
        self.assertNotIn("allow-empty", adopted["next"]["command"])

    def test_r4_a_design_re_review_is_told_which_items_changed(self):
        self.draft()
        os.environ.update(FAKE_REVIEW="design_changes")
        self.assertEqual(self.review("design", commit=None)["verdict"], "DESIGN CHANGES")
        first = self.calls()[-1]["argv"][-1]
        self.assertNotIn("Since the last design review", first)
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.edit_m2()
        self.assertEqual(self.adopt()["result"], "ADOPTED")
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design", commit=None)["verdict"], "DESIGN OK")
        second = self.calls()[-1]["argv"][-1]
        self.assertIn("Since the last design review (docs/evidence/WATER/design-review.md, at ", second)
        self.assertIn("these changed: M2.1 changed.", second)
        before = {"milestones": [milestone("M1", "not_started", ["open", "open"]), milestone("M2", "not_started", ["open"])]}
        after = {"milestones": [milestone("M1", "not_started", ["open"]), milestone("M3", "not_started", ["open"])]}
        after["milestones"][0]["bar"] = "higher"
        self.assertEqual(agent_loop.changed_items(before, after),
                         ["M1's bar or depends_on changed", "M1.2 removed", "M3 added", "M2 removed"])


    # Round five: the ladder's re-plan rung

    def test_r5_four_failed_reviews_hand_every_surface_the_planners_command(self):
        self.write_done([failed_before(dict(milestone("M1", "not_started", ["open"], inspect="frames"), failed_reviews_with_repeat=3, failed_reviews=3)),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
        os.environ.update(FAKE_REVIEW="fail")
        failed = self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual((failed["failed_reviews_with_repeat"], failed["escalation"]), (4, "diagnosis"))
        self.assertEqual((failed["next"]["escalation"], failed["next"]["by"]), ("diagnosis", "planner"))
        self.assertIn(" plan --worktree ", failed["next"]["command"])
        self.assertIn("Diagnose WATER M1", failed["next"]["command"])
        self.assertIn("docs/evidence/WATER/M1-review.md", failed["next"]["command"])
        self.assertEqual(failed["next"]["findings"], "docs/evidence/WATER/M1-review.md")
        # ready: not ready, owed a diagnosis, with the command
        r = self.ready()
        self.assertEqual(r["ready"], [])
        self.assertEqual([(s["milestone"], s["reason"]) for s in r["waiting"]], [("M1", "for_diagnosis")])
        self.assertEqual(r["waiting"][0]["next"]["command"], failed["next"]["command"])
        self.assertEqual(r["next"]["command"], failed["next"]["command"])
        # next: the planner's task, not the builder's findings
        nxt = json.loads(self.printed(agent_loop.cmd_next, module="WATER", milestone="M1", worktree=str(self.wt)))
        self.assertEqual(nxt["action"], "diagnosis")
        self.assertTrue(nxt["message"].startswith("Diagnose WATER M1"), nxt["message"])
        self.assertNotIn("set the state back to ready_for_review", nxt["message"])
        self.assertEqual(nxt["next"]["command"], failed["next"]["command"])
        # status says so, with the command
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        self.assertIn("WATER: waiting: for_diagnosis (M1)", status)
        self.assertIn("a planner looks at it before any more building", status)
        self.assertIn("Diagnose WATER M1", status)
        # run starts no builder
        before = len(self.calls())
        stopped = self.run_loop()
        self.assertEqual((stopped["result"], stopped["reason"]), ("WAITING", "for_diagnosis"), stopped)
        self.assertEqual(stopped["next"]["command"], failed["next"]["command"])
        self.assertEqual(len(self.calls()), before)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("WATER M1: waiting: for diagnosis", report)
        # once the planner has re-planned (its counts at 0, diagnoses 1), it's the builder's again
        doc = self.read_done()
        m1 = doc["milestones"][0]
        m1.update(failed_reviews_with_repeat=0, failed_reviews=0, diagnoses=1, state="not_started")
        m1["items"][0]["statement"] = "a smaller first step"
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(doc)})["status"], "ready")


    # Round six: the taste-led rerun

    # Round eighteen: the human decides in chat, and the lead records it

    def test_r18_a_block_on_human_feedback_tells_the_lead_what_to_ask_and_what_to_run(self):
        m1 = milestone("M1", "not_started", ["open", "open"], inspect="frames")
        m1["items"][1]["needs"] = needs("human_feedback", "the human picks a direction")
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_STATE="in_progress", FAKE_REPLY="BLOCKED: M1.2 needs the human")
        blocked = self.run_loop()
        nxt = blocked["next"]
        self.assertEqual((blocked["result"], nxt["decides"]), ("BLOCKED", "human"), blocked)
        self.assertTrue(nxt["ask"].startswith("M1.2: M1.2 works (the human picks a direction). Evidence to show "
                                              "them: docs/evidence/WATER/"), nxt["ask"])
        self.assertIn("The builder's note: M1.2 needs the human", nxt["ask"])
        self.assertIn(" human feedback --module WATER --milestone M1 --item M1.2 ", nxt["command"])
        self.assertIn("--said '<what the human said, in their words>'", nxt["command"])
        self.assertIn("Ask the human in chat", nxt["why"])
        self.assertNotIn("alternative", nxt)
        for text in (json.dumps(blocked), json.dumps(self.ready())):
            self.assertNotIn("terminal", text)
            self.assertNotIn("relay", text)
        self.git("pull", "-q", "--rebase", "origin", "main")
        answered = self.human("feedback", "M1", "Direction B, the ink one.", item="M1.2")
        self.assertEqual((answered["result"], answered["unblocked"]), ("DONE", True))
        rec = self.read_record()
        [d] = rec["decisions"]
        self.assertEqual((d["action"], d["milestone"], d["items"], d["words"]), ("feedback", "M1", ["M1.2"],
                                                                                "Direction B, the ink one."))
        self.assertNotIn("by", d)
        self.assertNotIn("by", rec["milestones"]["M1"]["human_feedback"][0])
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Decisions recorded in your name (check each is one you made)")[1]
        self.assertIn('- WATER M1 M1.2: feedback, ', section.split("\n## ")[0])
        self.assertIn('"Direction B, the ink one."', section.split("\n## ")[0])
        for key in ("FAKE_SKIP_NEEDS", "FAKE_STATE"):
            os.environ.pop(key)
        os.environ.update(FAKE_REPLY="DONE")
        claim = self.run_loop()
        self.assertIn("Direction B, the ink one.", self.calls()[-1]["argv"][-1])
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        self.assertIn("Human Feedback on M1", self.calls()[-1]["argv"][-1])

    def test_r18_every_verb_keeps_the_humans_words_and_report_lists_them(self):
        self.write_done([dict(too_many("M1", ["open"]), failed_reviews_with_repeat=4), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(self.human("reopen", "M1", "give it one more go")["result"], "DONE")
        self.assertEqual(self.human("accept", "design", "the design is fine")["result"], "DONE")
        released = self.human("release", "M2", "that lead's machine is gone")
        self.assertEqual(released["result"], "RELEASED", released)
        rec = self.read_record()
        self.assertEqual([(d["action"], d["milestone"], d["words"]) for d in rec["decisions"]],
                         [("reopen", "M1", "give it one more go"), ("accept", "design", "the design is fine"),
                          ("release", "M2", "that lead's machine is gone")])
        self.assertEqual(rec["design"]["by"], "human decision")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Decisions recorded in your name")[1].split("\n## ")[0]
        for line in ('- WATER M1: reopen, ', '"give it one more go"', '- WATER design: accept, ',
                     '- WATER M2: release, '):
            self.assertIn(line, section)

    def test_r19_scope_with_nothing_changed_says_so(self):
        with self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_human(argparse.Namespace(action="scope", module="WATER", milestone="M1", item=None,
                                                    text="keep it as it is", worktree=str(self.wt)))
        release()
        self.assertIn("nothing changed: docs/plans/WATER/DONE.json here has the same definitions as the tip",
                      str(stop.exception))
        self.assertNotIn("decisions", self.read_record())

    def test_r19_report_lists_planner_turns_with_their_tasks(self):
        self.plan(task="Plan PAY. The human said: \"card payments only, no PayPal\"")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Planner turns (with the task each was given)")[1].split("\n## ")[0]
        self.assertIn(', PAY: Plan PAY. The human said: "card payments only, no PayPal"', section)

    def test_r18_older_records_read_as_they_were_written_once_migrated(self):
        rec = json.loads((self.wt / "docs/plans/WATER/ACCEPTED.json").read_text())
        at = agent_loop.now()
        m1 = rec["milestones"]["M1"]
        m1["owner"] = [{"by": "owner", "reason": "typo fix", "at": at, "action": "accept"}]
        m1["owner_answers"] = [{"by": "owner", "text": "Direction A", "at": at, "item": "M1.1"},
                               {"by": "lead", "text": "Direction B", "at": at, "item": "M1.1", "relayed": True}]
        rec["design"] = {"by": "owner", "reason": "fine as it is", "at": at, "verdict": "ok",
                         "hash": rec["design"]["hash"]}
        put(self.wt / "docs/plans/WATER/ACCEPTED.json", json.dumps(rec))
        self.commit_all()
        self.assertEqual(self.migrate()["result"], "MIGRATED")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Decisions recorded in your name")[1].split("\n## ")[0]
        self.assertIn('- WATER M1: accept, ', section)
        self.assertIn('"typo fix"', section)
        self.assertIn('- WATER M1 M1.1: feedback, ', section)
        self.assertIn('"Direction B"', section)
        self.assertIn('- WATER design: accept, ', section)
        feedback = self.read_record()["milestones"]["M1"]["human_feedback"]
        note = agent_loop.feedback_note(feedback, "M1", "docs/plans/WATER/ACCEPTED.json")
        self.assertLess(note.index("Direction A"), note.index("Direction B"), "oldest first")


    def test_r6_quota_counts_only_this_repositorys_milestones(self):
        import test_codex_quota as fixtures
        now = fixtures.NOW
        elsewhere = self.root / "other-repo"
        elsewhere.mkdir()
        other = fixtures.Rollout(self.home, "o1", now - 10 * 3600, cwd=str(elsewhere), origin="codex_exec",
                                 source="exec", name="build WATER M1")
        other.turn("t", now - 10 * 3600, now - 9 * 3600, [(now - 10 * 3600 + i * 600, 2_000_000, i) for i in range(1, 5)])
        mine = fixtures.Rollout(self.home, "h1", now - 8 * 3600, cwd=str(self.wt / "sub"), origin="codex_exec",
                                source="exec", name="thrum · WATER · M2 build")
        mine.turn("t", now - 8 * 3600, now - 7 * 3600, [(now - 8 * 3600 + i * 600, 2_000_000, 10 + i)
                                                        for i in range(1, 5)])
        reading = agent_loop.codex_quota.read(budget_s=10, home=self.home, cache=False, now=now)
        own = agent_loop.loop_threads(self.wt, reading)
        self.assertEqual((own["o1"]["here"], own["h1"]["here"]), (False, True))
        acc = agent_loop.quota_report(self.wt, reading=reading)
        self.assertEqual([m["milestone"] for m in acc["milestones"]], ["M2"])

    def test_r6_report_lists_every_design_review_in_the_window(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        self.review("design", commit=None)
        self.revise_design()
        os.environ.update(FAKE_REVIEW="design")
        self.review("design", commit=None)
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        lines = [line for line in report.split("## Verdicts")[1].split("##")[0].splitlines()
                 if line.startswith("- WATER design:")]
        self.assertEqual(len(lines), 2, report)
        self.assertIn("changes", lines[0])
        self.assertIn("docs/evidence/WATER/design-review-1.md", lines[0])
        self.assertIn("ok", lines[1])
        self.assertIn("docs/evidence/WATER/design-review.md)", lines[1])
        # a record from before the history was kept still shows the kept review, from its file
        rec = json.loads(self.git("show", "origin/main:docs/plans/WATER/ACCEPTED.json").stdout)
        rec.pop("design_history")
        prof = agent_loop.profile(self.wt)
        ref = self.git("rev-parse", "origin/main").stdout.strip()
        older = agent_loop.design_reviews(self.wt, prof, ref, "WATER", rec)
        self.assertEqual([d["review"] for d in older],
                         ["docs/evidence/WATER/design-review-1.md", "docs/evidence/WATER/design-review.md"])

    # Round seven: the browser-game run

    def test_r7_a_block_with_another_cause_leads_and_the_report_still_lists_the_feedback_item(self):
        m1 = milestone("M1", "not_started", ["open", "open"], inspect="frames")
        m1["items"][1]["needs"] = needs("human_feedback", "the human plays both and picks a direction")
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no browser starts here; M1.2 needs the human's pick")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
        self.assertIn(" --message '<the missing fact>'", blocked["next"]["command"])  # the builder's cause leads
        r = self.ready()
        self.assertEqual(r["blocked"][0]["blocked"]["reason"], "needs_context")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Items that need human feedback, access or hardware")[1].split("\n## ")[0]
        self.assertIn("- WATER M1 M1.2 (needs human feedback: the human plays both and picks a direction)", section)
        self.assertIn("Ask the human in chat; their reply goes in `", section)
        self.assertIn(" human feedback --module WATER --milestone M1 --item M1.2 ", section)

    def test_r7_a_builder_names_the_reason_it_is_blocked(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="Tried it.\nBLOCKED needs_dependency: CORE has no save API yet")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_dependency"), blocked)
        recorded = self.read_done()["milestones"][0]["blocked"]
        self.assertEqual(recorded.pop("work")["branch"], "main")
        self.assertEqual(recorded, {"reason": "needs_dependency", "what": "CORE has no save API yet"})
        self.assertIn(" plan --worktree ", blocked["next"]["command"])
        os.environ.update(FAKE_REPLY="NEEDS_CONTEXT: which save slot?")
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.printed(agent_loop.cmd_unblock, module="WATER", milestone="M1", worktree=str(self.wt))
        again = self.run_loop()
        self.assertEqual((again["result"], again["reason"]), ("BLOCKED", "needs_context"), again)

    def test_r7_codex_in_workspace_write_is_warned_off_browser_work(self):
        self.assertEqual(agent_loop.browser_warnings(self.wt), [])
        profile = PROFILE + ("\n## Targets\n\n| Target | What it is | Run | Capture | Edge conditions |\n"
                             "|---|---|---|---|---|\n| web | Chromium, desktop | `npm run dev` | Playwright screenshots | resize |\n"
                             "| cli | the binary | `cargo run` | transcript | bad args |\n")
        (self.wt / "ORCHESTRATE.md").write_text(profile)
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["target"] = "web"
        doc["milestones"][1]["items"][0]["check"] = "npx playwright test"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        [warning] = agent_loop.browser_warnings(self.wt)
        self.assertIn("target web, WATER M1.1, WATER M2.1 need a browser", warning)
        self.assertNotIn("target cli", warning)
        self.assertNotIn("--host claude", warning)  # round eleven: never steer a lead off the human's host
        self.assertIn("has to ask to run it outside the sandbox", warning)
        self.assertIn("Codex sandbox: danger-full-access", warning)
        # N8: a run's warning names only the milestone it builds, not 18 items from other modules
        [m1] = agent_loop.browser_warnings(self.wt, "WATER", "M1")
        self.assertTrue(m1.startswith("WATER M1.1 need a browser"), m1)
        self.assertIn(m1, agent_loop.preflight("codex", self.wt, "build", "WATER", "M1"))
        self.assertEqual(agent_loop.browser_warnings(self.wt, "WATER", "M3"), [])
        self.assertNotIn(m1, agent_loop.preflight("codex", self.wt, "plan"))
        prof = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host="codex"))
        self.assertIn(warning, prof["preflight"]["warnings"])
        (self.wt / "ORCHESTRATE.md").write_text(profile.replace("**Default host:** codex",
                                                                "**Default host:** codex\n- **Codex sandbox:** danger-full-access"))
        self.assertEqual(agent_loop.browser_warnings(self.wt), [])

    # Round eight: the re-plan's bookkeeping, scope as a re-plan, and every review round kept

    def four_fails(self):
        """WATER M1 after its fourth failed review, owed a diagnosis, with each review kept. Built once per
        process and copied back after that."""
        return self.restore("four-fails", self.build_four_fails)

    def build_four_fails(self):
        # three failed reviews so far, two of them repeats; both rounds below repeat what failed before
        self.write_done([failed_before(dict(milestone("M1", "not_started", ["open"], inspect="frames"), failed_reviews_with_repeat=2, failed_reviews=3)),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        for n in range(2):
            os.environ.pop("FAKE_REVIEW", None)
            claim = self.run_loop(**({"message": "FINDINGS"} if n else {}))
            self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
            os.environ.update(FAKE_REVIEW="fail")
            failed = self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        return failed

    @shares("four-fails")
    def test_r8_every_review_is_kept_and_named(self):
        failed = self.four_fails()
        self.assertEqual((failed["escalation"], failed["next"]["cause"]), ("diagnosis", "a finding keeps coming back"))
        kept = [r.get("review") for r in self.read_record()["milestones"]["M1"]["reviews"]]
        self.assertEqual(kept, ["docs/evidence/WATER/M1-review-1.md", "docs/evidence/WATER/M1-review.md"])
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout
        self.assertIn("docs/evidence/WATER/M1-review-1.md", files)
        task = failed["next"]["command"]
        self.assertIn("Its reviews, oldest first: docs/evidence/WATER/M1-review-1.md, "
                      "docs/evidence/WATER/M1-review.md", task)
        self.assertNotIn("git log", task)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("[docs/evidence/WATER/M1-review-1.md]", report)

    @shares("four-fails")
    def test_r8_the_loop_does_the_replans_bookkeeping_once(self):
        for mode in ("replan", "replan_counted"):
            with self.subTest(mode=mode):
                self.setUp()
                self.four_fails()
                os.environ.update(FAKE_PLAN=mode)
                planned = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Diagnose WATER M1", host=None,
                                    model=None, effort=None, turn_timeout_hours=0.1)
                self.assertEqual((planned["result"], planned["replanned"]), ("PLANNED", ["WATER M1"]), planned)
                m1 = self.read_done()["milestones"][0]
                self.assertEqual((m1["failed_reviews_with_repeat"], m1["failed_reviews"], m1["diagnoses"], m1["state"]),
                                 (0, 0, 1, "not_started"))
                self.assertNotEqual(agent_loop.next_step("WATER", agent_loop.read_project(
                    self.wt, agent_loop.profile(self.wt))[1]).get("reason"), "for_diagnosis")


    # A milestone that keeps failing on something new: the round-six diagnosis

    def six_rounds(self, diagnoses=0):
        """WATER M1 after its sixth failed review, only one of which repeated an earlier round's finding. Built once
        per process and copied back after that."""
        return self.restore(f"six-rounds-{diagnoses}", lambda: self.build_six_rounds(diagnoses))

    def build_six_rounds(self, diagnoses):
        self.write_done([dict(milestone("M1", "not_started", ["open"], inspect="frames"), failed_reviews_with_repeat=1, failed_reviews=5,
                              diagnoses=diagnoses), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
        os.environ.update(FAKE_REVIEW="fail")
        failed = self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        return failed

    def diagnose(self, mode):
        os.environ.update(FAKE_PLAN=mode)
        out = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Diagnose WATER M1", host=None, model=None,
                        effort=None, turn_timeout_hours=0.1)
        os.environ.pop("FAKE_PLAN")
        self.git("pull", "-q", "--rebase", "origin", "main")
        return out

    @shares("six-rounds-0")
    def test_six_failed_reviews_on_new_findings_owe_a_diagnosis(self):
        failed = self.six_rounds()
        self.assertEqual((failed["failed_reviews_with_repeat"], failed["failed_reviews"], failed["repeated"], failed["escalation"]),
                         (1, 6, [], "diagnosis"), failed)
        self.assertEqual((failed["next"]["escalation"], failed["next"]["by"], failed["next"]["cause"]),
                         ("diagnosis", "planner", "reviews keep finding something new"))
        self.assertIn(" plan --worktree ", failed["next"]["command"])
        self.assertIn("Diagnose WATER M1", failed["next"]["command"])
        self.assertIn("KEEP WATER M1: builder", failed["next"]["command"])
        waiting = self.run_loop()
        self.assertEqual((waiting["result"], waiting["reason"]), ("WAITING", "for_diagnosis"), waiting)
        m1 = self.read_done()["milestones"][0]
        self.assertEqual(m1["findings"], [{"name": "the water is flat (M1.1)", "item": "M1.1", "repeat": False}])
        rnd = self.read_record()["milestones"]["M1"]["reviews"][-1]
        self.assertEqual((rnd["items"], rnd["findings"][0]["name"]), ({"M1.1": "fail"}, "the water is flat (M1.1)"))

    @shares("six-rounds-0")
    def test_a_diagnosis_that_changes_the_plan_is_a_replan(self):
        self.six_rounds()
        planned = self.diagnose("replan")
        self.assertEqual((planned["result"], planned["replanned"]), ("PLANNED", ["WATER M1"]), planned)
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["failed_reviews_with_repeat"], m1["failed_reviews"], m1["diagnoses"], m1["state"]),
                         (0, 0, 1, "not_started"))
        self.assertNotIn("findings", m1)

    @shares("six-rounds-0")
    def test_a_diagnosis_that_keeps_the_plan_names_who_acts(self):
        for who, by, has in (("builder", "lead", "--fresh"), ("reviewer", "lead", "--fresh"),
                             ("human", "human", " human reopen ")):
            with self.subTest(who=who):
                self.setUp()
                self.six_rounds()
                kept = self.diagnose(f"keep_{who}")
                self.assertEqual((kept["result"], kept["who"], kept["next"].get("decides") or kept["next"]["by"]),
                                 ("KEPT", who, by), kept)
                self.assertIn(has, kept["next"]["command"])
                self.assertIn(f"the {who} has to act", json.dumps(kept["next"]))
                m1 = self.read_done()["milestones"][0]
                self.assertEqual((m1["failed_reviews_with_repeat"], m1["failed_reviews"], m1["diagnoses"]), (0, 0, 1))
                self.assertEqual(m1["state"], "blocked" if who == "human" else "in_progress")
                e = self.read_record()["milestones"]["M1"]
                self.assertEqual(e["diagnoses"][-1]["who"], who)
                self.assertEqual(e["counted_from"], e["diagnoses"][-1]["at"])
                if who == "human":
                    self.assertTrue(kept["next"]["ask"])
                    self.assertTrue(kept["next"]["history"])
                    # every later readout gives the planner's reason and the rounds it read
                    later = agent_loop.next_for({"module": "WATER", "milestone": "M1", "status": "blocked",
                                                 "reason": "too_many_failed_reviews"}, self.wt,
                                                agent_loop.profile(self.wt))
                    self.assertIn(f"the {who} has to act", later["ask"])
                    self.assertEqual(later["history"], kept["next"]["history"])
                    nxt = json.loads(self.printed(agent_loop.cmd_next, module="WATER", milestone="M1",
                                                  worktree=str(self.wt)))
                    self.assertEqual(nxt["action"], "too_many_failed_reviews")
                    continue
                self.assertEqual(self.run_loop(fresh=True, message="FINDINGS")["result"], "READY_FOR_REVIEW")
                os.environ.update(FAKE_REVIEW="fail")
                again = self.review()
                os.environ.pop("FAKE_REVIEW")
                prompt = self.calls()[-1]["argv"][-1]
                told = "diagnosis on" in prompt and "kept M1's items as written" in prompt
                self.assertEqual(told, who == "reviewer")
                # the rounds before the diagnosis no longer count: the same finding isn't a repeat
                self.assertEqual((again["failed_reviews_with_repeat"], again["failed_reviews"], again["repeated"]), (0, 1, []), again)

    @shares("four-fails")
    def test_a_kept_plan_after_repeated_findings_counts_as_the_diagnosis(self):
        failed = self.four_fails()
        self.assertIn("KEEP WATER M1: builder", failed["next"]["command"])
        self.assertNotIn("the plan is wrong", failed["next"]["command"])
        kept = self.diagnose("keep_builder")
        self.assertEqual((kept["result"], kept["who"], kept["next"]["by"]), ("KEPT", "builder", "lead"), kept)
        self.assertIn("--fresh", kept["next"]["command"])
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["failed_reviews_with_repeat"], m1["failed_reviews"], m1["diagnoses"], m1["state"]),
                         (0, 0, 1, "in_progress"))
        # a second run of four repeated failures goes to the human, as it does after a re-plan
        self.assertEqual(agent_loop.escalation_of(dict(m1, failed_reviews=4, failed_reviews_with_repeat=4)),
                         "too_many_failed_reviews")

    def test_keep_is_refused_when_no_diagnosis_is_owed(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        refused = self.diagnose("keep_builder")
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("isn't owed one", refused["problems"][0])

    @shares("six-rounds-1")
    def test_the_same_counts_after_a_diagnosis_block_it_with_each_reviews_failures(self):
        stuck = self.six_rounds(diagnoses=1)
        self.assertEqual((stuck["escalation"], stuck["next"]["decides"]), ("too_many_failed_reviews", "human"), stuck)
        self.assertEqual(self.read_done()["milestones"][0]["blocked"]["reason"], "too_many_failed_reviews")
        self.assertTrue(any("the water is flat (M1.1)" in h for h in stuck["next"]["history"]), stuck["next"])
        for verb in ("Accept it", "change its scope", "reopen it"):
            self.assertIn(verb, stuck["next"]["ask"])
        # the human reopens it: the counts start again, and the earlier rounds no longer count as repeats
        self.assertEqual(self.human("reopen", "M1", "one more go")["result"], "DONE")
        self.git("pull", "-q", "--rebase", "origin", "main")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["failed_reviews_with_repeat"], m1["failed_reviews"], m1["diagnoses"]), ("in_progress", 0, 0, 0))
        self.assertTrue(self.read_record()["milestones"]["M1"]["counted_from"])
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        again = self.review(commit=claim["commit"])
        self.assertEqual((again["failed_reviews_with_repeat"], again["failed_reviews"], again["escalation"]), (0, 1, "same_builder"), again)

    def test_a_failure_says_how_it_differs_or_counts_as_a_repeat(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"], inspect="frames")), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_REVIEW="fail")
        results = []
        for n, (name, different) in enumerate((("flat", ""), ("seams", ""), ("foam", "seams fixed; foam is new"))):
            os.environ.update(FAKE_FINDING=name, FAKE_DIFFERENT=different)
            os.environ.pop("FAKE_REVIEW")
            claim = self.run_loop(**({"message": "FINDINGS"} if n else {}))
            os.environ.update(FAKE_REVIEW="fail")
            results.append(self.review(commit=claim["commit"]))
        # round 2 fails the same item with a new name and no `different`: a repeat; round 3 says how it differs
        self.assertEqual([(r["failed_reviews_with_repeat"], r["failed_reviews"]) for r in results], [(0, 1), (1, 2), (1, 3)])
        self.assertEqual(results[2]["escalation"], "new_builder_session")

    def test_a_pass_after_a_failed_review_clears_the_findings(self):
        self.write_done([dict(milestone("M1", "not_started", ["open"], inspect="frames")), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        claim = self.run_loop(message="FINDINGS")
        prompt_before = len(self.calls())
        passed = self.review(commit=claim["commit"])
        self.assertEqual((passed["result"], passed["verdict"]), ("REVIEWED", "PASS"), passed)
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertNotIn("findings", self.read_done()["milestones"][0])
        # the second reviewer is told where the first round is kept, and not what it found, so it judges the items first
        prompt = self.calls()[prompt_before]["argv"][-1]
        self.assertIn("M1 has failed review 1 time since its counts last started", prompt)
        self.assertIn("docs/evidence/WATER/M1-review.md", prompt)
        self.assertIn("docs/plans/WATER/ACCEPTED.json under milestones.M1.reviews", prompt)
        self.assertNotIn("the water is flat", prompt)


    @shares("six-rounds-1")
    def test_human_scope_restarts_the_counts_and_unblocks_it(self):
        self.six_rounds(diagnoses=1)
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["statement"] = "what the human wants now"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        self.assertEqual(self.human("scope", "M1")["result"], "DONE")
        self.git("pull", "-q", "--rebase", "origin", "main")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["failed_reviews_with_repeat"], m1["failed_reviews"], m1["diagnoses"]), ("not_started", 0, 0, 0))
        self.assertNotIn("findings", m1)

    def test_a_review_must_list_its_findings_on_a_fail_and_none_on_a_pass(self):
        with self.subTest("a fail with no findings is refused"):
            commit = self.ready_for_review()
            os.environ.update(FAKE_NO_FINDINGS="1", FAKE_REVIEW="fail")
            bad = self.review(commit=commit)
            self.assertEqual(bad["result"], "INVALID", bad)
            self.assertIn("the last line says FAIL, but findings is empty; list each Must Fix with a short name",
                          bad["problems"])
            self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")
        with self.subTest("a pass merges with no findings, whatever the reviewer listed"):
            self.setUp()
            commit = self.ready_for_review()
            os.environ.update(FAKE_PASS_FINDINGS="1", FAKE_REVIEW="pass")
            passed = self.review(commit=commit)
            self.assertEqual((passed["result"], passed["verdict"]), ("REVIEWED", "PASS"), passed)
            m1 = self.read_done()["milestones"][0]
            self.assertEqual(m1["state"], "done")
            self.assertNotIn("findings", m1)

    @shares("four-fails")
    def test_r8_human_scope_on_an_owed_milestone_leaves_nothing_to_diagnose(self):
        self.four_fails()
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["statement"] = "what the human wants now"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        scoped = self.human("scope", "M1")
        self.assertEqual((scoped["result"], scoped["replanned"]), ("DONE", ["M1"]), scoped)
        self.assertIn("nothing is left to diagnose", scoped["replanned_why"])
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["failed_reviews_with_repeat"], m1["diagnoses"], m1["state"]), (0, 0, "not_started"))


    # Round nine: the second whole-change review

    def feedback_m1(self, state="blocked", status="open"):
        m1 = milestone("M1", state, ["open", status], inspect="frames")
        m1["items"][1]["needs"] = needs("human_feedback", "the human picks a direction")
        if state == "blocked":
            m1["blocked"] = {"reason": "needs_human_feedback", "items": ["M1.2"], "what": "M1.2 needs the human"}
        self.write_done([m1, milestone("M2", "not_started", ["open"])])
        self.commit_all()

    def test_r9_human_decisions_are_refused_while_the_module_is_held(self):
        self.feedback_m1()
        for name, role, says in (("WATER", "review", "a run, review or design review holds WATER"),
                                 ("_plan", "plan", "a planner is running")):
            code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop\n"
                    f"from pathlib import Path; wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, {name!r})\n"
                    f"agent_loop.loop_register(wt, {role!r}, module='WATER', milestone='M1', host='codex', "
                    "model='m', effort='medium'); print('up', flush=True); time.sleep(60)\n")
            proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(proc.stdout.readline().strip(), "up")
                messages = []
                for verb in ("feedback", "accept", "release"):
                    with self.assertRaises(SystemExit) as stop:
                        agent_loop.cmd_human(argparse.Namespace(
                            action=verb, module="WATER", milestone="M1", item=["M1.2"] if verb == "feedback" else None,
                            text="B", said="B", asked="A or B?", worktree=str(self.wt)))
                    release()
                    messages.append(str(stop.exception))
            finally:
                proc.kill()
                proc.wait()
                proc.stdout.close()
            for message in messages:
                self.assertIn(says, message)
                self.assertIn(f"pid {proc.pid}", message)
        self.assertEqual(self.human("feedback", "M1", "Direction B.", item="M1.2")["result"], "DONE")  # once free

    def test_r9_a_draft_stays_closed_after_ok_then_changes(self):
        self.draft()
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design", commit=None)["verdict"], "DESIGN OK")
        os.environ.update(FAKE_REVIEW="design_changes")
        self.assertEqual(self.review("design", commit=None)["verdict"], "DESIGN CHANGES")
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        rec = self.read_record()
        self.assertTrue(agent_loop.design_passed(rec))
        self.edit_m2()
        refused = self.adopt()
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("a design review of it has passed, so they're no longer a draft", refused["problems"][0])

    def test_r9_a_design_review_counts_only_for_what_it_read(self):
        self.draft()
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        os.environ.update(FAKE_REVIEW="design", FAKE_DURING=(
            f"cd {other} && echo '# Water, revised' > docs/plans/WATER/DESIGN.md && git add -A && "
            "git -c user.name=t -c user.email=t@t commit -qm revise && git push -q origin main"))
        stale = self.review("design", commit=None)
        self.assertEqual((stale["verdict"], stale["counted"]), ("DESIGN OK", False), stale)
        self.assertIn("the design document", stale["not_counted"])
        self.assertIn(" review --module WATER --milestone design ", stale["next"]["command"])
        rec = self.read_record()
        self.assertFalse(agent_loop.design_passed(rec))
        self.assertIn("not_counted", rec["design_history"][-1])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertEqual(self.ready()["design_not_approved"], [{"module": "WATER"}])

    def test_r9_each_kept_round_keeps_its_captures(self):
        os.environ.update(FAKE_CAPTURE="1")
        self.four_fails()
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertIn("docs/evidence/WATER/M1-review-1/shot.png", files)
        self.assertIn("docs/evidence/WATER/M1-review/shot.png", files)
        self.assertEqual(self.git("show", "origin/main:docs/evidence/WATER/M1-review-1/shot.png").stdout, "PNG 4")
        self.assertEqual(self.git("show", "origin/main:docs/evidence/WATER/M1-review/shot.png").stdout, "PNG 5")
        kept = self.git("show", "origin/main:docs/evidence/WATER/M1-review-1.md").stdout
        self.assertIn("(M1-review-1/shot.png)", kept)
        self.assertIn("(M1-review/shot.png)", self.git("show", "origin/main:docs/evidence/WATER/M1-review.md").stdout)

    def test_r9_a_worktree_merely_behind_a_planned_tip_is_told_so(self):
        origin, first = self.root / "o2.git", self.root / "first"
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(origin))
        self.sh("git", "clone", "-q", str(origin), str(first))
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "start", where=first)
        self.git("push", "-q", "origin", "main", where=first)
        behind = self.root / "behind"
        self.sh("git", "clone", "-q", str(origin), str(behind))
        (first / "ORCHESTRATE.md").write_text(PROFILE)
        self.git("add", "-A", where=first)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "plan", where=first)
        self.git("push", "-q", "origin", "main", where=first)
        r = self.ready(where=behind)
        self.assertNotIn("unplanned", r)
        self.assertIn("behind origin/main", r["behind"])
        self.assertIn(f"merge --ff-only origin/main", r["next"]["command"])
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(behind))
        self.assertIn("Bring it up with", status)
        self.assertIn("merge --ff-only origin/main", r["next"]["command"])
        diverged = self.root / "diverged"
        self.sh("git", "clone", "-q", str(origin), str(diverged))
        self.git("reset", "-q", "--hard", "HEAD~1", where=diverged)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "mine",
                 where=diverged)
        split = agent_loop.unplanned(diverged)
        self.assertIsNone(split["next"]["command"])  # only a fast-forward is the lead's to run
        self.assertIn("has commits origin/main doesn't", split["reason"])
        self.git("merge", "-q", "--ff-only", "origin/main", where=behind)
        self.assertIsNone(agent_loop.unplanned(behind))
        fresh = self.root / "fresh"
        self.sh("git", "init", "-q", "-b", "main", str(fresh))
        self.assertIn("isn't planned yet", agent_loop.unplanned(fresh)["reason"])

    def test_r9_a_profile_merely_behind_the_tip_isnt_told_to_commit(self):
        behind = self.root / "behind"
        self.sh("git", "clone", "-q", str(self.origin), str(behind))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** high\n")
        self.commit_all()
        self.git("fetch", "-q", "origin", where=behind)
        prof = agent_loop.profile(behind)
        self.assertFalse(agent_loop.plan_drift(behind, prof, "origin/main")["settings_differ"])
        (behind / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** low\n")
        self.assertTrue(agent_loop.plan_drift(behind, prof, "origin/main")["settings_differ"])


    # Round ten: two modules built at once

    def test_r15_a_planner_that_catches_up_with_loop_commits_still_lands(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        # another module's claim (with the loop's trailer) lands mid-turn, and the planner fast-forwards to it: that
        # commit is on the tip and isn't the planner's work, so the turn lands what it left uncommitted
        os.environ.update(FAKE_PLAN="catch_up", FAKE_DURING=(
            f"cd {other} && echo '{{}}' > docs/plans/WATER/ACCEPTED.json && git add -A && "
            f"git -c user.name=t -c user.email=t@t commit -qm 'orchestrate: claim WATER M1' -m '{agent_loop.TRAILER}' "
            "&& git push -q origin main"))
        planned = self.plan()
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertIn("acceptance/test_pay.py", files)
        self.assertIn("docs/plans/PAY/DONE.json", files)

    def forge_on_tip(self):
        """A FAKE_DURING command: a commit without the loop's trailer changes WATER's acceptance record on the tip."""
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        return (f"cd {other} && echo '{{\"forged\": true}}' > docs/plans/WATER/ACCEPTED.json && git add -A && "
                "git -c user.name=t -c user.email=t@t commit -qm 'tidy records' && git push -q origin main")

    def test_r15_a_record_forged_elsewhere_during_a_planner_turn_refuses_it(self):
        os.environ.update(FAKE_DURING=self.forge_on_tip())
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("without the script's trailer changed", refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"], refused["next"]["decides"]),
                         (None, "lead", "human"))
        self.assertNotIn("docs/plans/PAY/DONE.json",
                         self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split())
        self.assertIn("docs/plans/PAY/DONE.json", refused["set_aside"])  # kept in a stash, for the human

    def test_r15_a_record_forged_during_a_review_refuses_it(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claimed = self.run_loop()
        self.assertEqual((claimed["result"], claimed["review"]), ("READY_FOR_REVIEW", True), claimed)
        os.environ.update(FAKE_DURING=self.forge_on_tip())
        refused = self.review(commit=claimed["commit"])
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("without the script's trailer changed", refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["decides"]), (None, "human"))
        self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")  # no verdict was recorded

    def test_r15_a_local_landing_during_a_planner_turn_doesnt_refuse_it(self):
        main, side = self.root / "local", self.root / "local-side"
        self.sh("git", "init", "-q", "-b", "main", str(main))
        (main / "docs/plans").mkdir(parents=True)
        (main / "ORCHESTRATE.md").write_text(PROFILE.replace("Merge:** push", "Merge:** local"))
        self.git("add", "-A", where=main)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init", where=main)
        self.git("worktree", "add", "-q", "-b", "side", str(side), "main", where=main)
        script = Path(agent_loop.__file__).resolve()
        # mid-turn, another worktree lands, which fast-forwards main in the checkout the planner is working in
        os.environ.update(FAKE_DURING=(
            f"cd {side} && echo x > feature && git add -A && git -c user.name=t -c user.email=t@t commit -qm feature "
            f"&& env -u ORCHESTRATE_ROLE {sys.executable} {script} merge --worktree {side} --no-check"))
        planned = self.plan(worktree=str(main))
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "main", where=main).stdout.split()
        self.assertIn("feature", files)
        self.assertIn("docs/plans/PAY/DONE.json", files)
        self.assertIn("docs/plans/PAY/ACCEPTED.json", files)

    # Round sixteen: a module the loop has no record for is new once any record exists; planner commits are refused

    SHIP = ("import json, os, sys\n"
            "d = sys.argv[1]\n"
            "os.makedirs(d + '/docs/plans/SHIP', exist_ok=True)\n"
            "json.dump({'module': 'SHIP', 'milestones': [{'id': 'M1', 'name': 'ship', 'state': 'done', 'failed_reviews': 0,"
            " 'diagnoses': 0, 'items': [{'id': 'M1.1', 'statement': 'ships', 'check': 'true', 'status': 'pass',"
            " 'evidence': 'x', 'verdict': 'pass', 'review': 'x'"
            + "}]}]}, open(d + '/docs/plans/SHIP/DONE.json', 'w'))\n"
            "open(d + '/docs/plans/SHIP/DESIGN.md', 'w').write('# Ship')\n")

    def ship(self, where, then=""):
        """A shell command that writes a finished-looking SHIP module in `where` and commits it there."""
        script = self.root / "ship.py"
        script.write_text(self.SHIP)
        g = f"git -C {where} -c user.name=t -c user.email=t@t"
        return f"{sys.executable} {script} {where} && {g} add -A && {g} commit -qm 'plan SHIP' {then}"

    def local_repo(self):
        """A repository integrating locally, with a second worktree; the planner works in the checkout of main."""
        main, side = self.root / "local", self.root / "local-side"
        self.sh("git", "init", "-q", "-b", "main", str(main))
        (main / "docs/plans").mkdir(parents=True)
        (main / "ORCHESTRATE.md").write_text(PROFILE.replace("Merge:** push", "Merge:** local"))
        self.write_done([milestone("M1", "not_started", ["open"])], where=main)  # a record: the loop is in use here
        self.git("add", "-A", where=main)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init", where=main)
        self.git("worktree", "add", "-q", "-b", "side", str(side), "main", where=main)
        return main, side

    def assert_ship_is_new(self, where):
        r = self.ready(where=where)
        self.assertNotIn("SHIP", [x["module"] for x in r["finished"]], r)
        self.assertIn({"module": "SHIP"}, r["design_not_approved"], r)

    def test_r16_a_planner_that_commits_and_pushes_a_finished_module_is_refused_and_accepts_nothing(self):
        # the planner works in the loop's checkout, which is its current directory
        os.environ.update(FAKE_DURING=self.ship(".", "&& git push -q origin HEAD:main"))
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("the planner committed (1 commit in its checkout's reflog during the turn",
                      refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "lead"))
        self.git("reset", "-q", "--hard", "origin/main")
        self.git("clean", "-qfd")
        self.assert_ship_is_new(self.wt)  # it reached the tip, but as a new module

    def test_r16_a_planner_that_commits_in_the_local_checkout_is_refused_and_accepts_nothing(self):
        main, _ = self.local_repo()
        os.environ.update(FAKE_DURING=self.ship("."))
        refused = self.plan(worktree=str(main))
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("in its checkout's reflog during the turn", refused["problems"][0])
        # its commit is kept on a branch, and nothing of it reached main
        self.assertIn("SHIP", self.git("show", "--name-only", "--format=", refused["branch"], where=main).stdout)
        self.assertNotIn("docs/plans/SHIP/DONE.json",
                         self.git("ls-tree", "-r", "--name-only", "main", where=main).stdout.split())

    def test_r16_a_module_landed_from_elsewhere_and_edited_by_the_planner_is_new_push(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        # landed deliberately from another clone (no reflog entry here), fast-forwarded into, then edited uncommitted
        os.environ.update(FAKE_DURING=(
            self.ship(other, "&& git -C " + str(other) + " push -q origin main") +
            " && git fetch -q origin && git merge -q --ff-only origin/main && "
            "echo '# Ship, revised' > docs/plans/SHIP/DESIGN.md && "
            "sed -i.bak s/ships/ships\\ fast/ docs/plans/SHIP/DONE.json && "
            "rm docs/plans/SHIP/DONE.json.bak"))
        planned = self.plan()
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        self.assertIn("SHIP", planned["modules"])
        self.assertIn("SHIP", planned["design_review_owed"])
        rec = json.loads(self.git("show", "origin/main:docs/plans/SHIP/ACCEPTED.json").stdout)
        self.assertNotIn("accepted", rec["milestones"]["M1"])
        self.assertIsNone(rec["design"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assert_ship_is_new(self.wt)

    def test_r16_a_module_landed_from_elsewhere_and_edited_by_the_planner_is_new_local(self):
        main, side = self.local_repo()
        script = Path(agent_loop.__file__).resolve()
        os.environ.update(FAKE_DURING=(
            self.ship(side) + f" && env -u ORCHESTRATE_ROLE {sys.executable} {script} merge --worktree {side} "
            "--no-check && git merge -q --ff-only main && echo '# Ship, revised' > docs/plans/SHIP/DESIGN.md && "
            "sed -i.bak s/ships/ships\\ fast/ docs/plans/SHIP/DONE.json && "
            "rm docs/plans/SHIP/DONE.json.bak"))
        planned = self.plan(worktree=str(main))
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        self.assertIn("SHIP", planned["modules"])  # through the plan's own record-keeping
        self.assertIn("SHIP", planned["design_review_owed"])
        rec = json.loads(self.git("show", "main:docs/plans/SHIP/ACCEPTED.json", where=main).stdout)
        self.assertNotIn("accepted", rec["milestones"]["M1"])
        self.assert_ship_is_new(main)

    def test_r16_a_reviewer_that_commits_is_refused(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claimed = self.run_loop()
        self.assertEqual((claimed["result"], claimed["review"]), ("READY_FOR_REVIEW", True), claimed)
        os.environ.update(FAKE_DURING="git -c user.name=t -c user.email=t@t commit -q --allow-empty -m habit")
        refused = self.review(commit=claimed["commit"])
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("the reviewer committed in its checkout", refused["problems"][0])
        self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")

    def test_r16_a_repository_with_no_records_still_adopts_modules_as_they_stand(self):
        origin, wt = self.root / "legacy.git", self.root / "legacy"
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(origin))
        self.sh("git", "init", "-q", "-b", "main", str(wt))
        (wt / "docs/plans").mkdir(parents=True)
        (wt / "ORCHESTRATE.md").write_text(PROFILE)
        self.write_done([milestone("M1", "done", ["pass"]), milestone("M2", "not_started", ["open"])], authorise=False,
                        where=wt)
        self.git("add", "-A", where=wt)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "work already done", where=wt)
        self.git("remote", "add", "origin", str(origin), where=wt)
        self.git("push", "-q", "origin", "main", where=wt)
        prof = agent_loop.profile(wt)
        self.assertTrue(agent_loop.unrecorded(wt, prof, "origin/main"))
        r = self.ready(where=wt)
        self.assertEqual([(x["module"], x["milestone"]) for x in r["ready"]], [("WATER", "M2")], r)
        # the loop's first record-keeping commit (here, a plan's) writes WATER's record as it was taken
        planned = self.plan(worktree=str(wt))
        self.assertEqual(planned["result"], "PLANNED", planned)
        rec = json.loads(self.git("show", "origin/main:docs/plans/WATER/ACCEPTED.json", where=wt).stdout)
        self.assertEqual(rec["milestones"]["M1"]["accepted"], {"by": "adopted"})
        self.assertFalse(agent_loop.unrecorded(wt, prof, "origin/main"))
        self.git("pull", "-q", "--rebase", "origin", "main", where=wt)
        r = self.ready(where=wt)
        self.assertEqual([(x["module"], x["milestone"]) for x in r["ready"]], [("WATER", "M2")], r)
        self.assertIn({"module": "PAY"}, r["design_not_approved"])
        # once a record has existed, deleting every record doesn't bring adoption as it stands back
        self.git("rm", "-q", "docs/plans/WATER/ACCEPTED.json", "docs/plans/PAY/ACCEPTED.json", where=wt)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "drop records", where=wt)
        self.assertFalse(agent_loop.unrecorded(wt, prof, "HEAD"))

    # Round seventeen: a design review goes to the host that didn't plan it, decided once; planners get the loop path

    def test_r17_a_design_review_goes_to_the_host_that_didnt_plan_it_everywhere(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([too_many("M1", ["open"])])  # nothing of WATER's is ready
        self.commit_all()
        planned = self.plan(host="claude")
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertTrue(planned["next"]["command"].endswith("--host codex"), planned["next"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        rec = json.loads(self.git("show", "origin/main:docs/plans/PAY/ACCEPTED.json").stdout)
        self.assertEqual(rec["planner"]["host"], "claude")
        r = self.ready()
        self.assertIn(" review --module PAY --milestone design ", r["next"]["command"])
        self.assertTrue(r["next"]["command"].endswith("--host codex"), r["next"])
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        self.assertNotIn("--host claude", status)
        os.environ.update(FAKE_REVIEW="design")
        # built on claude, the planner's own host: the owed design review still goes to codex
        built = self.run_loop(module="PAY", host="claude")
        self.assertEqual(built["design_review"]["host"], "codex", built)
        self.assertEqual(self.review("design", module="PAY", commit=None)["host"], "codex")
        # a host the lead names wins
        self.assertEqual(self.review("design", module="PAY", commit=None, host="claude")["host"], "claude")
        named = self.run_loop(module="PAY", host="codex", review_host="claude")
        self.assertEqual(named["design_review"]["host"], "claude", named)

    def test_r17_without_a_known_planner_or_other_nothing_changes(self):
        prof = {"review_host": "other"}
        self.assertEqual(agent_loop.design_review_host(prof, {}, "claude"), "codex")  # as before: the fallback
        self.assertEqual(agent_loop.design_review_host(prof, {"planner": {"host": "claude"}}, "claude"), "codex")
        self.assertEqual(agent_loop.design_review_host(prof, {"planner": {"host": "codex"}}, "codex"), "claude")
        self.assertEqual(agent_loop.design_review_host(prof, {"planner": {"host": "claude"}}, "x", "codex"), "codex")
        for wanted in ("", "same", "pi"):  # no Review host, same, or a named host: the planner isn't consulted
            prof = {"review_host": wanted}
            self.assertEqual(agent_loop.design_review_host(prof, {"planner": {"host": "claude"}}, "codex"),
                             agent_loop.review_host(prof, "codex"))
        # a profile with no Review host (Thrum's): PLANNED names the planner's host, as it did
        self.write_done([too_many("M1", ["open"])])
        self.commit_all()
        planned = self.plan(host="claude")
        self.assertTrue(planned["next"]["command"].endswith("--host claude"), planned["next"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertNotIn("--host", self.ready()["next"]["command"])

    def test_r17_planners_get_the_loop_path_and_dont_hunt_for_host_clis(self):
        self.plan()
        prompt = [c for c in self.calls() if c["role"] == "plan"][0]["argv"][-1]
        self.assertIn(f"The script is `python3 {agent_loop.LOOP}`. Its `check --module <M> --milestone <id> "
                      "--worktree . --items-only` command", prompt)
        self.assertNotIn("PATH", prompt, "the note about host programs on PATH was cut: no planner ever met it")

    def test_r10_everything_a_planner_writes_lands_with_its_plan(self):
        os.environ.update(FAKE_PLAN="catch_up")  # nothing new on the tip, so the fast-forward moves nothing
        planned = self.plan()
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertIn("acceptance/test_pay.py", files)

    def test_r13_a_planner_that_lands_a_forged_record_itself_is_refused(self):
        os.environ.update(FAKE_PLAN_SIDE="push")
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("without the script's trailer changed", refused["problems"][0])
        # no revert handed out: the human decides what happens to a commit already on the tip
        self.assertEqual((refused["next"]["command"], refused["next"]["by"], refused["next"]["decides"]),
                         (None, "lead", "human"))

    def test_r13_a_planner_that_fakes_the_tracking_ref_is_refused(self):
        os.environ.update(FAKE_PLAN_SIDE="ref")
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("the planner committed (", refused["problems"][0])
        self.assertIn("tidy", refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "lead"))
        self.assertTrue(refused["branch"].startswith("orchestrate/planner-"))  # its commit is kept, not landed
        self.assertNotIn("forged", self.git("show", "origin/main:docs/plans/WATER/ACCEPTED.json").stdout)
        # the next plan lands nothing of it
        os.environ.pop("FAKE_PLAN_SIDE")
        planned = self.plan()
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertNotIn("forged", self.git("show", "origin/main:docs/plans/WATER/ACCEPTED.json").stdout)

    def test_r15_a_second_refusal_from_the_same_start_is_refused_the_same_way(self):
        os.environ.update(FAKE_PLAN_SIDE="ref")
        first = self.plan()
        self.git("reset", "-q", "--hard", "origin/main")
        self.git("clean", "-qfd")
        second = self.plan()
        self.assertEqual((first["result"], second["result"]), ("INVALID", "INVALID"), second)
        self.assertEqual((first["next"]["command"], first["next"]["by"]), (second["next"]["command"], "lead"))
        for kept in (first, second):  # each turn's commit is kept; identical commits share a sha and so a branch
            self.assertEqual(self.git("rev-parse", "--verify", "-q", f"refs/heads/{kept['branch']}").returncode, 0, kept)

    def test_r13_a_plan_from_a_worktree_with_its_own_work_leaves_that_work_alone(self):
        (self.wt / "notes.txt").write_text("x")
        self.git("add", "-A")
        self.git("commit", "-qm", "side work")
        (self.wt / "draft.txt").write_text("uncommitted")
        planned = self.plan()
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertNotIn("notes.txt", files)  # the planner plans from the tip, in the loop's own checkout
        self.assertNotIn("draft.txt", files)
        self.assertIn("side work", self.git("log", "-1", "--format=%s").stdout)  # this worktree is left alone
        self.assertTrue((self.wt / "draft.txt").exists())

    def test_r13_merge_refuses_plan_and_review_sessions(self):
        for role in ("plan", "review"):
            with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": role}), self.assertRaises(SystemExit) as stop:
                agent_loop.cmd_merge(argparse.Namespace(worktree=str(self.wt), no_check=False))
            self.assertIn(f"merge isn't for a {role} session", str(stop.exception))

    def test_r10_a_refused_plan_says_what_to_do(self):
        os.environ.update(FAKE_PLAN="forge")
        refused = self.plan(task="x")
        self.assertEqual(refused["result"], "INVALID")
        self.assertIn("planner", refused["stash"])  # the loop set the turn's files aside itself
        self.assertIn("docs/plans/WATER/ACCEPTED.json",
                      self.git("stash", "show", "--include-untracked", "--name-only", "stash@{0}").stdout.split())
        self.assertNotIn("stash push", refused["next"]["command"])
        self.assertIn(" plan --worktree ", refused["next"]["command"])
        self.assertIn("only the script writes record files", refused["next"]["command"])

    def test_r10_a_second_planner_waits_for_the_first(self):
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop\n"
                f"from pathlib import Path; wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, '_plan')\n"
                "agent_loop.loop_register(wt, 'plan', task='Revise CORE', host='claude', model='m', effort='high')\n"
                "print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            threading.Timer(0.5, proc.kill).start()  # the first planner finishes a moment later
            started = time.time()
            planned = self.plan(task="Revise REPORT", host="codex")
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
        self.assertEqual(planned["result"], "PLANNED", planned)  # it waited, then planned, with nothing to retry
        self.assertGreater(time.time() - started, 0.4)

    def test_r10_a_claim_for_review_names_the_review_command(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames"), milestone("M2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual((claim["result"], claim["review"]), ("READY_FOR_REVIEW", True), claim)
        self.assertIn(f" review --module WATER --milestone M1 --commit {claim['commit']} ", claim["next"]["command"])
        self.assertTrue(claim["next"]["command"].endswith("--host claude"), claim["next"]["command"])


    def test_r10_the_build_row_doesnt_carry_the_design_reviews_tokens(self):
        self.draft()
        script = self.root / "loops-script.py"
        script.write_text(f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; agent_loop.main()\n")
        seen = self.root / "seen.jsonl"
        os.environ.update(FAKE_REVIEW="design", FAKE_USAGE="1", FAKE_LOOPS=str(seen), FAKE_LOOPS_SCRIPT=str(script))
        claim = self.run_loop()
        self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
        rows = [json.loads(l) for l in seen.read_text().splitlines()]
        build = [r for snap in rows for r in snap.get("runs", snap) if isinstance(r, dict) and r.get("role") == "build"]
        self.assertTrue(build, rows)
        self.assertEqual((build[-1]["turns"], build[-1]["tokens"]), (0, None))
        self.assertIsNotNone(build[-1]["turn_running_s"])

    # Round eleven: the icon project carried on

    def test_r11_next_keeps_its_own_worktree_and_reuses_the_modules_hosts(self):
        wt2 = self.root / "wt-water"
        self.git("worktree", "add", "-q", "--detach", str(wt2))
        agent_loop.note_run(wt2, "WATER", "claude", "codex")
        agent_loop.RUN_HERE.clear()  # as another process would see it
        run = agent_loop.fit_command(agent_loop.loop_cmd("run", "--module", "WATER", "--worktree", str(self.wt)))
        self.assertIn(f"--worktree {self.wt} --host claude --review-host codex", run)  # the worktree it was given
        review = agent_loop.loop_cmd("review", "--module", "WATER", "--milestone", "M1", "--commit", "abc",
                                     "--worktree", str(self.wt))
        self.assertEqual(agent_loop.fit_command(review), review)  # `review` takes the builder from the claim
        design = agent_loop.fit_command(agent_loop.loop_cmd("review", "--module", "WATER", "--milestone", "design",
                                                            "--worktree", str(self.wt)))
        self.assertTrue(design.endswith(f"--worktree {self.wt} --host codex"), design)
        cut = agent_loop.loop_cmd("run", "--worktree", str(self.wt), "--module")
        self.assertEqual(agent_loop.fit_command(cut), cut)
        named = agent_loop.loop_cmd("run", "--module", "WATER", "--worktree", str(self.wt), "--host", "codex")
        self.assertIn("--host codex", agent_loop.fit_command(named))
        self.assertNotIn("--host claude", agent_loop.fit_command(named))
        other = agent_loop.loop_cmd("run", "--module", "PAY", "--worktree", str(self.wt))
        self.assertEqual(agent_loop.fit_command(other), other)
        out = io.StringIO()  # every result line's `next` goes through it
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            agent_loop.emit("DONE", next=agent_loop.next_cmd(None, "lead", "x", then=agent_loop.loop_cmd(
                "run", "--module", "WATER", "--worktree", str(self.wt))))
        self.assertIn("--host claude --review-host codex", json.loads(out.getvalue())["next"]["then"])

    def test_r11_the_browser_warning_is_for_builds_and_says_the_true_thing(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Targets:** web-chrome\n")
        self.write_done([milestone("M1", "not_started", ["open"], inspect="drive it in a browser"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual([w for w in agent_loop.preflight("codex", self.wt, "review") if "browser" in w], [])
            build = [w for w in agent_loop.preflight("codex", self.wt, "build", "WATER", "M1") if "browser" in w]
        self.assertEqual(len(build), 1, build)
        self.assertIn("has to ask to run it outside the sandbox, and auto-review may refuse", build[0])
        self.assertNotIn("--host claude", build[0])

    def test_r11_an_archived_design_review_keeps_its_own_time_in_utc(self):
        ev = self.wt / "docs/evidence/WATER"
        ev.mkdir(parents=True)
        (ev / "design-review.md").write_text("first\nDESIGN CHANGES: no LOD plan")
        self.git("add", "-A")
        subprocess.run(["git", "-C", str(self.wt), "commit", "-qm", "first review"], check=True, capture_output=True,
                       env={**os.environ, "GIT_COMMITTER_DATE": "2026-11-10T02:53:50+0100"})
        (ev / "design-review-1.md").write_text((ev / "design-review.md").read_text())
        (ev / "design-review.md").write_text("second\nDESIGN OK")
        self.git("add", "-A")
        subprocess.run(["git", "-C", str(self.wt), "commit", "-qm", "second review"], check=True, capture_output=True,
                       env={**os.environ, "GIT_COMMITTER_DATE": "2026-11-10T02:58:51+0100"})
        prof = agent_loop.profile(self.wt)
        rec = {"design": {"verdict": "ok", "review": "docs/evidence/WATER/design-review.md",
                          "at": "2026-11-10T01:58:51Z"}}
        rows = agent_loop.design_reviews(self.wt, prof, "HEAD", "WATER", rec)
        self.assertEqual([(d["verdict"], d["at"]) for d in rows],
                         [("changes", "2026-11-10T01:53:50Z"), ("ok", "2026-11-10T01:58:51Z")])

    def test_r11_adopt_names_a_build_report_in_its_subject(self):
        reports = self.wt / "docs/evidence/build-reports"
        reports.mkdir(parents=True)
        (reports / "2026-11-10.md").write_text("# Report\n")
        self.assertEqual(self.adopt()["result"], "ADOPTED")
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("log", "-1", "--format=%s", "origin/main").stdout.strip(),
                         "Adopt build report: 2026-11-10.md")

    # Round twelve: the confirmation run

    def test_r12_the_whole_ask_reaches_the_record_the_commit_and_the_design_reviewer(self):
        ask = "Plan the project: " + "a slug tool that handles accents, " * 12 + "and when the input is empty, says so"
        planned = self.plan(task=ask)
        self.assertEqual(planned["result"], "PLANNED", planned)
        rec = json.loads(self.git("show", "origin/main:docs/plans/PAY/ACCEPTED.json").stdout)
        self.assertEqual(rec["briefs"][-1]["task"], ask)
        self.assertEqual(rec["milestones"]["M1"]["authorised"]["task"], ask[:120])  # the whole ask is kept once
        self.assertIn("and when the input is empty, says so", self.git("log", "--format=%B", "origin/main").stdout)
        self.git("pull", "-q", "--rebase", "origin", "main")
        os.environ.update(FAKE_REVIEW="design")
        self.review("design", module="PAY", commit=None)
        self.assertIn("docs/plans/PAY/ACCEPTED.json under `briefs`", self.calls()[-1]["argv"][-1])

    def test_r12_a_planners_assumptions_are_counted_and_reported(self):
        os.environ.update(FAKE_ASSUME="\n\n## Open for the human\n\n- Assumption: accents means any letter with a Latin base\n"
                                       "Assumption: the size limit is in bytes\nNot an assumption: this line\n")
        planned = self.plan()
        self.assertEqual(planned["assumptions"], {"PAY": 2}, planned)
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Assumptions the planners made (for you to overturn)")[1].split("\n## ")[0]
        self.assertIn("- PAY ([plan](docs/plans/PAY/PLAN.md)):", section)
        self.assertIn("  - accents means any letter with a Latin base", section)
        self.assertIn("  - the size limit is in bytes", section)
        self.assertNotIn("this line", section)

    def test_r12_a_written_report_links_from_where_it_lives(self):
        quoted = "a reviewer wrote [see](docs/x.md) and [u](https://x.test/a)"  # not the report's own links
        text = (agent_loop.md_link("r", "docs/evidence/WATER/M1-review.md") + " "
                + agent_loop.md_link("p", "docs/plans/PAY/PLAN.md") + " " + quoted)
        self.assertEqual(agent_loop.relink(text, "docs/evidence/build-reports"),
                         "[r](../WATER/M1-review.md) [p](../../plans/PAY/PLAN.md) " + quoted)
        self.assertEqual(agent_loop.relink(text, None),
                         "[r](docs/evidence/WATER/M1-review.md) [p](docs/plans/PAY/PLAN.md) " + quoted)
        os.environ.update(FAKE_ASSUME="\n- Assumption: one\n")
        self.plan()
        self.git("pull", "-q", "--rebase", "origin", "main")
        written = json.loads(self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=True))
        body = (self.wt / written["written"]).read_text()
        self.assertIn("([plan](../../plans/PAY/PLAN.md))", body)

    def test_r13_a_run_that_builds_nothing_isnt_recorded_as_the_modules_run(self):
        self.write_done([milestone("M1", "ready_for_review", ["pass"], inspect="frames"), milestone("M2", "not_started", ["open"])],
                        ready=["M1"])
        self.commit_all()
        owed = self.run_loop(host="claude")
        self.assertEqual(owed["result"], "REVIEW_OWED", owed)
        agent_loop.RUN_HERE.clear()
        self.assertEqual(agent_loop.known_run(str(self.wt), "WATER"), {})


    def test_session_titles_group_by_repository_then_module(self):
        title = agent_loop.session_title(self.wt, "WATER", "M1 build")
        self.assertEqual(title, f"{agent_loop.repository_name(self.wt)} · WATER · M1 build")
        self.assertEqual(agent_loop.title_parts(title), ("build", "WATER", "M1"))
        self.assertEqual(agent_loop.title_parts("review WATER M1"), ("review", "WATER", "M1"))  # before 1.7.0
        self.assertIsNone(agent_loop.title_parts("Thrum: Delivery Lead"))
        prof = agent_loop.profile(self.wt)
        self.assertEqual(agent_loop.plan_title(self.wt, self.wt, prof, "Re-plan water M2 after review"),
                         agent_loop.session_title(self.wt, "WATER", "plan: Re-plan water M2 after review"))
        self.assertEqual(agent_loop.plan_title(self.wt, self.wt, prof, "Plan the project"),
                         agent_loop.session_title(self.wt, "plan", "plan: Plan the project"))


class FirstRunsAlone(ProfileOnly):
    """Tests from FirstRuns that need no repository, only the project settings."""

    def test_item5_a_paused_claude_turn_counts_the_tokens_it_showed(self):
        partial = "\n".join(json.dumps(e) for e in [
            {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 10, "output_tokens": 1}}},
            {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 10, "output_tokens": 3}}},
            {"type": "assistant", "message": {"id": "b", "usage": {"input_tokens": 5, "cache_read_input_tokens": 100,
                                                                   "output_tokens": 2}}}])
        self.assertEqual(agent_loop.usage_of("claude", partial),
                         {"input": 15, "cached": 100, "output": 5, "incomplete_turns": 1, "turns": 1})

    def test_item6_quota_rounds_small_costs_and_counts_in_words(self):
        self.assertEqual([agent_loop.pct(x) for x in (0, 0.04, 0.42, 3.25, 41.6)],
                         ["0%", "under 0.1%", "0.4%", "3.2%", "42%"])
        acc = {"used_percent": 30.0, "hours_left": 50.0}
        recent = {"hours": 12.0, "loop": [0.1, 0.2, 0.3], "other": [0.01, 0.02, 0.03]}
        done_ms = [{"module": "W", "milestone": "M1", "state": "done", "pct": [0.1, 0.2, 0.3], "reviews": 1}]
        open_one = [{"module": "W", "milestone": "M2", "state": "not_started", "reviews": 1}]
        verdict = agent_loop.plan_forecast(acc, done_ms, open_one, recent)["verdict"]
        self.assertTrue(verdict.startswith("Quota lasts: the 1 open milestone and other use need about 0.3%"), verdict)
        verdict = agent_loop.plan_forecast(acc, done_ms, [], recent)["verdict"]
        self.assertTrue(verdict.startswith("Quota lasts: other use needs about"), verdict)

    def test_item11_a_long_report_keeps_its_end(self):
        report = "x" * 9000 + "\nHuman decides: pick a licence.\nPLANNED: a, b"
        kept = agent_loop.tail(report, 6000)
        self.assertTrue(kept.startswith("[earlier text cut] "))
        prose = "Planned PAY files. " * 400 + "Human decides: pick a licence."
        cut = agent_loop.tail(prose, 1500)
        self.assertTrue(cut.startswith("[earlier text cut] Planned PAY files."), cut[:60])
        lines = "\n".join(f"line {n} of the planner's notes" for n in range(400))
        self.assertTrue(agent_loop.tail(lines, 1500).startswith("[earlier text cut] line "))
        self.assertTrue(kept.endswith("Human decides: pick a licence.\nPLANNED: a, b"))
        self.assertEqual(agent_loop.tail("short", 6000), "short")

    def test_r5_next_gives_a_command_on_every_rung(self):
        prof = agent_loop.profile(self.wt)
        for with_repeat, failed, diagnoses, word, by, has in (
                (0, 1, 0, "same_builder", "lead", "--message"),
                (1, 2, 0, "same_builder", "lead", "--message"),
                (0, 3, 0, "new_builder_session", "lead", "--fresh"),
                (3, 4, 0, "new_builder_session", "lead", "--fresh"),
                (4, 4, 0, "diagnosis", "planner", " plan "),
                (4, 5, 1, "too_many_failed_reviews", "human", " human reopen "),  # the lead runs it once the human decides
                (1, 6, 0, "diagnosis", "planner", " plan "),
                (1, 6, 1, "too_many_failed_reviews", "human", " human reopen ")):
            word_now = agent_loop.escalation(failed, with_repeat, diagnoses)
            counts = {"failed_reviews": failed, "failed_reviews_with_repeat": with_repeat, "diagnoses": diagnoses}
            then = agent_loop.escalation_next(word_now, "WATER", "M1", counts, self.wt, prof)
            self.assertEqual((word_now, then["escalation"], then.get("decides") or then["by"]), (word, word, by))
            self.assertIn(has, then["command"])

    def test_r18_human_stops_ask_in_chat_and_never_send_anyone_to_a_terminal(self):
        prof = agent_loop.profile(self.wt)
        for word in ("too_many_failed_reviews",):
            then = agent_loop.escalation_next(word, "WATER", "M1", {"failed_reviews": 4, "failed_reviews_with_repeat": 4, "diagnoses": 1}, self.wt, prof)
            self.assertEqual(then["decides"], "human")
            self.assertTrue(then["ask"])
            self.assertIn("--text '<what the human said", then["command"])
        for step in ({"module": "WATER", "milestone": "M1", "status": "blocked", "reason": "too_many_failed_reviews"},
                     {"module": "WATER", "milestone": "M1", "status": "review_owed", "state": "done"},
                     {"module": "WATER", "milestone": "M1", "status": "taken", "by": "elsewhere"}):
            n = agent_loop.next_for(step, self.wt, prof)
            text = json.dumps(n)
            self.assertNotIn("terminal", text)
            self.assertNotIn("--reason", text)
            self.assertIn("--text '<what the human said", text)
            if n["by"] == "human":
                self.assertTrue(n["ask"])


    def test_r8_a_plan_that_leaves_an_owed_milestone_alone_settles_nothing(self):
        before = {"milestones": [dict(milestone("M1", "in_progress", ["open"]), failed_reviews_with_repeat=4)]}
        after = json.loads(json.dumps(before))
        self.assertEqual(agent_loop.settle_replanned(before, after, "WATER"), [])
        self.assertEqual(after["milestones"][0]["failed_reviews_with_repeat"], 4)
        after["milestones"][0]["items"][0]["check"] = "test -f smaller"
        self.assertEqual(agent_loop.settle_replanned(before, after, "WATER"), ["WATER M1"])
        self.assertEqual((after["milestones"][0]["failed_reviews_with_repeat"], after["milestones"][0]["diagnoses"]), (0, 1))

    def test_a_planner_cant_change_the_counts(self):
        before = {"milestones": [dict(too_many("M1", ["open"]), failed_reviews_with_repeat=3, failed_reviews=5, diagnoses=1,
                                      findings=[{"name": "x"}])]}
        after = json.loads(json.dumps(before))
        m = after["milestones"][0]
        m.update(failed_reviews_with_repeat=0, failed_reviews=0, diagnoses=0, state="not_started")
        m.pop("findings")
        after["milestones"].append(dict(milestone("M1b", "not_started", ["open"]), failed_reviews_with_repeat=2, diagnoses=1))
        settled = agent_loop.settle_replanned(before, after, "WATER")
        agent_loop.keep_counts(before, after, settled, "WATER")
        m, split = after["milestones"]
        self.assertEqual((m["failed_reviews_with_repeat"], m["failed_reviews"], m["diagnoses"], m["state"], m["findings"]),
                         (3, 5, 1, "blocked", [{"name": "x"}]))
        self.assertEqual((split["failed_reviews_with_repeat"], split["failed_reviews"], split["diagnoses"]), (0, 0, 1))

    def test_r9_a_review_host_the_profile_cant_resolve_is_a_problem(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** codx\n")
        with self.assertRaises(SystemExit) as stop:
            agent_loop.profile(self.wt, strict=True)
        self.assertIn("review host: 'codx'", str(stop.exception))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Host pi:** pi run {prompt}\n- **Review host:** pi\n")
        self.assertEqual(agent_loop.profile(self.wt, strict=True)["review_host"], "pi")

    def test_r9_loop_started_codex_shells_carry_the_role(self):
        prof = agent_loop.profile(self.wt)
        flags = agent_loop.codex_flags(prof, "review")
        self.assertIn('shell_environment_policy.set.ORCHESTRATE_ROLE="review"', flags)

    def test_r10_live_turns_and_dollars_say_what_they_are(self):
        rec = {"pid": 1, "role": "build", "module": "WATER", "milestone": "M1", "host": "codex", "turns": 0,
               "started_at": time.time() - 600, "activity_at": time.time() - 5, "turn_started_at": time.time() - 590,
               "usage": {}, "registered": True, "worktree": str(self.wt)}
        v = agent_loop.loop_view(rec)
        self.assertGreaterEqual(v["turn_running_s"], 589)
        line = agent_loop.loop_line(v)
        self.assertIn("0 turns done, turn 1 running for 9m", line)
        self.assertIn("they count when a turn ends", line)
        both = agent_loop.cost_line({"runs": 3, "turns": 3, "input": 10, "cached": 0, "output": 1, "cost_usd": 8.99,
                                     "hosts": ["claude", "codex"]})
        self.assertIn("$8.99 at list price, for the Claude turns only; codex reports tokens, not a price", both)


ARCH = ("# Architecture\n\nSome words first.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
        "| # | Module | What it’s for (plain words) | Needs |\n|---|---|---|---|\n"
        "| 1 | [WATER](WATER/DESIGN.md) | The sea moves | none |\n"
        "| 2 | `SHIPS` | Boats float on it | WATER |\n\nInterfaces follow.\n")


class PlanFiles(Repo):
    """One folder per module under docs/plans, the human's STATUS.md, `migrate` from the flat layout, the module
    table, and the checks a plan has to pass where it lands."""

    def prof(self):
        return agent_loop.profile(self.wt)

    def flatten(self, root="docs/plans", log=True):
        """Puts WATER back in the old flat layout, with M1 accepted, a design, a plan with a log and a brief."""
        rec = json.loads((self.wt / "docs/plans/WATER/ACCEPTED.json").read_text())
        design = "# Water design\n"
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(design)}
        doc = done(milestone("M1", "done", ["pass"]), milestone("M2", "not_started", ["open"]))
        rec["milestones"]["M1"]["accepted"] = {"by": "checks", "at": "2026-11-10T10:00:00Z"}
        self.git("rm", "-rq", "docs/plans")
        flat = self.wt / root
        flat.mkdir(parents=True, exist_ok=True)
        (flat / "WATER-DONE.json").write_text(json.dumps(doc))
        (flat / "WATER-ACCEPTED.json").write_text(json.dumps(rec))
        (flat / "WATER.md").write_text(design)
        (flat / "WATER-PLAN.md").write_text("# Water plan\n\n## M2 waves\n- [ ] waves\n" +
                                            ("\n## Log\n- 2026-11-01 started\n- 2026-11-02 M1 done\n" if log else ""))
        (flat / "WATER-BRIEF.md").write_text("# Water brief\n")
        (flat / "GLOSSARY.md").write_text("# Glossary\n")
        if root != "docs/plans":
            (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("docs/plans", root))
        self.git("add", "-A")
        self.git("commit", "-qm", "flat", "-m", agent_loop.TRAILER)  # the loop wrote these records
        self.git("push", "-q", "origin", "main")

    def test_modules_are_folders_holding_a_done_when_file(self):
        prof = self.prof()
        put(self.wt / "docs/plans/NOTES/README.md", "not a module")
        self.assertEqual(agent_loop.modules_here(self.wt, prof), ["WATER"])
        self.assertEqual(agent_loop.modules_at(self.wt, prof, "HEAD"), ["WATER"])
        self.assertEqual(agent_loop.module_stem(self.wt, prof, "water"), "WATER")
        self.assertEqual(agent_loop.done_rel(prof, "WATER"), "docs/plans/WATER/DONE.json")
        self.assertEqual(agent_loop.design_rel(prof, "WATER"), "docs/plans/WATER/DESIGN.md")
        self.assertEqual(agent_loop.module_of(prof, "docs/plans/WATER/LOG.md"), ("WATER", "log"))
        self.assertIsNone(agent_loop.module_of(prof, "docs/plans/BRIEF.md"))  # the project's brief, not a module's
        self.assertIsNone(agent_loop.module_of(prof, "docs/plans/WATER/notes.md"))
        self.assertEqual(self.ready()["ready"][0]["module"], "WATER")

    def test_a_project_without_a_plans_line_keeps_docs_modules(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("- **Plans:** docs/plans\n", ""))
        self.git("mv", "docs/plans", "docs/modules")
        self.assertEqual(self.prof()["plans"], "docs/modules")
        (self.wt / "docs/plans").mkdir()
        self.assertEqual(self.prof()["plans"], "docs/plans")  # once docs/plans exists, it is the default again

    def test_the_flat_layout_stops_commands_and_names_migrate(self):
        self.flatten()
        with self.assertRaises(SystemExit) as stop:
            self.ready()
        self.assertIn("migrate --worktree", str(stop.exception))
        self.assertIn("WATER-DONE.json", str(stop.exception))
        profile = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host="codex"))
        self.assertIn("migrate", profile["flat_layout"])

    def test_migrate_moves_each_module_into_its_folder_and_keeps_acceptance(self):
        self.flatten()
        moved = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to=None)
        self.assertEqual(moved["result"], "MIGRATED", moved)
        self.assertEqual((moved["modules"], moved["logs_split"]), (["WATER"], ["WATER"]))
        self.assertTrue(moved["worktree"].startswith("fast-forwarded"), moved)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main", "docs/plans").stdout.split()
        self.assertEqual(sorted(files), ["docs/plans/GLOSSARY.md", "docs/plans/STATUS.md", "docs/plans/WATER/ACCEPTED.json",
                                         "docs/plans/WATER/BRIEF.md", "docs/plans/WATER/DESIGN.md",
                                         "docs/plans/WATER/DONE.json", "docs/plans/WATER/LOG.md",
                                         "docs/plans/WATER/PLAN.md"])
        plan = self.git("show", "origin/main:docs/plans/WATER/PLAN.md").stdout
        self.assertNotIn("## Log", plan)
        self.assertIn("## M2 waves", plan)
        log = self.git("show", "origin/main:docs/plans/WATER/LOG.md").stdout
        self.assertIn("- 2026-11-02 M1 done", log)
        self.assertIn(agent_loop.TRAILER, self.git("log", "--format=%B", "origin/main").stdout)
        r = self.ready()  # M1 stays accepted and the design agreed: the move changed no hash
        self.assertEqual([x["milestone"] for x in r["ready"]], ["M2"])
        self.assertEqual(r["design_not_approved"], [])
        again = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to=None)
        self.assertEqual(again["result"], "NOTHING", again)

    def old_names(self):
        """Puts WATER back in the names from before 2.0: old states, `needs` lists, `attended` items, a parked
        milestone, `owner_answers` and the old settings labels, with every hash stamped by the old formula."""
        at = "2026-11-09T10:00:00Z"
        m2 = dict(milestone("M2", "open", ["open", "open"]), needs=["M1"])
        m2["items"][1].update(inspect="on the phone", attended="plug in the iPhone")
        m4 = milestone("M4", "open", ["open"])
        m4["items"][0]["attended"] = "the human picks a direction"
        doc = done(milestone("M1", "done", ["pass"]), m2, dict(milestone("M3", "parked", ["open"]), failed_reviews_with_repeat=4), m4)
        rec = json.loads((self.wt / "docs/plans/WATER/ACCEPTED.json").read_text())
        rec["milestones"] = {m["id"]: {"definitions": agent_loop.old_definitions(m), "authorised": {"by": "plan"},
                                       "reviews": []} for m in doc["milestones"]}
        rec["milestones"]["M1"].update(accepted={"by": "checks", "at": at},
                                       reviews=[{"verdict": "PASS", "items": {"M1.1": "cant_tell"}, "at": at}])
        rec["milestones"]["M2"]["owner_answers"] = [{"by": "owner", "text": "Direction B", "at": at, "item": "M2.2"}]
        rec["milestones"]["M3"]["parked"] = {"why": "it kept failing", "after": 4, "at": at}
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        put(self.wt / "docs/plans/WATER/ACCEPTED.json", json.dumps(rec))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("**Merge:**", "**Integrate:**")
                                                .replace("**Test command:**", "**Check:**"))
        self.git("add", "-A")
        self.git("commit", "-qm", "old names", "-m", "Orchestrate-Loop: yes")  # the old trailer still counts
        self.git("push", "-q", "origin", "main")
        return doc

    def test_an_unmigrated_project_is_refused_by_every_other_command(self):
        self.old_names()
        for func, kw in ((agent_loop.cmd_ready, dict()),
                         (agent_loop.cmd_status, dict(module=None)),
                         (agent_loop.cmd_run, dict(module="WATER", milestone=None, fresh=False, message=None,
                                                   budget_hours=1.0, turn_timeout_hours=0.1, host=None, model=None,
                                                   effort=None, human_rule=None, clear_human_rules=False,
                                                   no_design_review=False)),
                         (agent_loop.cmd_human, dict(action="accept", module="WATER", milestone="M2", item=None,
                                                     text="fine", said=None, asked=None))):
            with self.subTest(command=func.__name__):
                try:
                    with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
                        func(argparse.Namespace(worktree=str(self.wt), **kw))
                finally:
                    release()
                self.assertIn("names from before orchestrate 2.0", str(stop.exception))
                self.assertIn("migrate --worktree", str(stop.exception))
        settings = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host="codex"))
        self.assertTrue(settings["old_names"], settings)

    def test_migrate_renames_an_old_project_in_one_commit_and_restamps_its_hashes(self):
        old = self.old_names()
        before = self.git("rev-parse", "origin/main").stdout.strip()
        moved = self.migrate()
        self.assertEqual(moved["result"], "MIGRATED", moved)
        self.assertTrue(moved["renamed"], moved)
        self.git("pull", "-q", "--rebase", "origin", "main")
        subjects = self.git("log", "--format=%s", f"{before}..origin/main").stdout.splitlines()
        self.assertEqual([s for s in subjects if "STATUS.md" not in s],
                         ["orchestrate: migrate the plans to a folder per module and the names of 2.0"])
        settings = self.git("show", "origin/main:ORCHESTRATE.md").stdout
        self.assertIn("- **Merge:** push", settings)
        self.assertIn("- **Test command:** none", settings)
        self.assertNotIn("Integrate", settings)
        doc = self.read_done()
        m1, m2, m3, m4 = doc["milestones"]
        self.assertEqual([m["state"] for m in doc["milestones"]], ["done", "not_started", "blocked", "not_started"])
        self.assertEqual((m2["depends_on"], "attended" in m2["items"][1]), (["M1"], False))
        self.assertEqual(m2["items"][1]["needs"], {"type": "hardware", "what": "plug in the iPhone"})
        self.assertEqual(m4["items"][0]["needs"], {"type": "human_feedback", "what": "the human picks a direction"})
        self.assertEqual(m3["blocked"]["reason"], "too_many_failed_reviews")
        rec = self.read_record()["milestones"]
        self.assertEqual(rec["M2"]["human_feedback"], [{"asked": None, "said": "Direction B", "items": ["M2.2"],
                                                        "at": "2026-11-09T10:00:00Z", "by": "owner"}])
        self.assertNotIn("owner_answers", rec["M2"])
        self.assertEqual(rec["M3"]["too_many_failed_reviews"]["why"], "it kept failing")
        self.assertEqual(rec["M1"]["reviews"][0]["items"], {"M1.1": "could_not_judge"})
        for m in doc["milestones"]:  # each hash re-stamped with today's formula, so nothing reads as re-planned
            self.assertEqual(rec[m["id"]]["definitions"], agent_loop.definitions(m), m["id"])
        self.assertEqual(rec["M1"]["definitions"], agent_loop.old_definitions(old["milestones"][0]),
                         "a milestone with no renamed field keeps its hash")
        r = self.ready()
        self.assertEqual(([x["milestone"] for x in r["ready"]], r["invalid"]), (["M2"], []), r)
        self.assertEqual(self.migrate()["result"], "NOTHING")

    def test_migrate_to_moves_the_whole_plans_folder_and_the_plans_line(self):
        self.flatten(root="docs/modules", log=False)
        moved = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to="docs/plans")
        self.assertEqual((moved["result"], moved["plans"]), ("MIGRATED", "docs/plans"), moved)
        self.assertNotIn("logs_split", moved)
        self.assertIn("- **Plans:** docs/plans", self.git("show", "origin/main:ORCHESTRATE.md").stdout)
        self.assertEqual(self.git("show", "origin/main:docs/plans/GLOSSARY.md").stdout, "# Glossary\n")
        self.assertEqual(self.git("ls-tree", "--name-only", "origin/main", "docs/modules").stdout, "")
        self.assertEqual([x["milestone"] for x in self.ready()["ready"]], ["M2"])

    def test_a_milestone_ready_for_review_before_migrate_is_reviewed_at_the_move(self):
        self.flatten()
        doc = done(milestone("M1", "done", ["pass"]), milestone("M2", "ready_for_review", ["pass"]))
        (self.wt / "docs/plans/WATER-DONE.json").write_text(json.dumps(doc))
        rec = json.loads((self.wt / "docs/plans/WATER-ACCEPTED.json").read_text())
        rec["milestones"]["M2"]["claim"] = {"at": "2026-11-11T10:00:00Z", "checks": []}  # as a 2.0.0 script wrote it
        (self.wt / "docs/plans/WATER-ACCEPTED.json").write_text(json.dumps(rec))
        self.git("commit", "-qam", "claim M2", "-m", agent_loop.TRAILER)
        self.git("push", "-q", "origin", "main")
        claimed = self.git("rev-parse", "HEAD").stdout.strip()
        moved = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to=None)
        self.assertEqual(moved["result"], "MIGRATED", moved)
        reviewed = self.review("M2", commit=claimed)
        self.assertEqual(reviewed["result"], "REVIEWED", reviewed)
        self.assertIn("before `migrate` brought", " ".join(reviewed.get("warnings") or []))

    def builder_branched_before_migrate(self):
        """A builder's worktree for WATER, branched before `migrate`, with two commits of its own on the old names:
        one moving M2 to in_progress in the done-when file, and one adding code."""
        tree = self.root / "wt-water"
        self.git("worktree", "add", "-q", "-b", "water-m2", str(tree), "origin/main")
        doc = json.loads((tree / "docs/plans/WATER/DONE.json").read_text())
        doc["milestones"][1]["state"] = "in_progress"
        doc["milestones"][1]["items"][0]["status"] = "pass"
        (tree / "docs/plans/WATER/DONE.json").write_text(json.dumps(doc))
        self.git("commit", "-qam", "M2: first wave", where=tree)
        put(tree / "src/waves.py", "WAVES = 3\n")
        self.git("add", "-A", where=tree)
        self.git("commit", "-qm", "M2: waves", where=tree)
        return tree

    def test_r6_migrate_branch_brings_a_worktree_over_while_another_module_runs(self):
        """Thrum: a builder's worktree branched before `migrate`, with commits of its own on the old names. Once the
        main branch was migrated, `run` refused it, `migrate` was refused because other modules were running, and
        a hand merge left the builder deleting conflict markers."""
        self.old_names()
        tree = self.builder_branched_before_migrate().resolve()
        moved = self.migrate()
        self.assertEqual(moved["result"], "MIGRATED", moved)
        self.assertEqual([w["worktree"] for w in moved["worktrees_on_old_names"]], [str(tree)], moved)
        self.assertIn("migrate --branch", moved["next"]["command"])
        put(self.wt / "README.md", "# the sea\n")  # the main branch moves on after the migration
        self.commit_all()

        with self.assertRaises(SystemExit) as stop:  # what `run` met in Thrum
            agent_loop.profile(tree, strict=True)
        self.assertIn("migrate --branch --worktree", str(stop.exception))
        naive = subprocess.run(["git", "-C", str(tree), "rebase", "origin/main"], capture_output=True, text=True)
        self.assertNotEqual(naive.returncode, 0, "a plain rebase should conflict, or this test shows nothing")
        self.assertIn("docs/plans/WATER/DONE.json", self.git("diff", "--name-only", "--diff-filter=U", where=tree).stdout)
        self.git("rebase", "--abort", where=tree)

        # SHIPS's run holds its own lock throughout, as another module building would.
        ships = agent_loop.take_file_lock(agent_loop.loop_dir(self.wt) / "run-SHIPS.lock")
        self.addCleanup(ships.close)
        holder = lambda folder, name: 4242 if name == "SHIPS" else None
        with mock.patch.object(agent_loop, "run_holder", holder):
            listed = self.call(agent_loop.cmd_migrate, worktree=str(tree))  # needs no run stopped any more
            self.assertEqual(listed["result"], "NOTHING", listed)
            self.assertIn("migrate --branch", listed["worktree"])
            water = agent_loop.take_file_lock(agent_loop.loop_dir(self.wt) / "run-WATER.lock")
            taken = self.call(agent_loop.cmd_migrate, worktree=str(tree), branch=True)
            water.close()
            self.assertEqual(taken["result"], "REFUSED", taken)
            self.assertIn("a run holds WATER", taken["problems"][0])
            was = agent_loop.head_commit(tree)
            self.assertEqual(self.git("rev-parse", "HEAD", where=tree).stdout.strip(), was)
            brought = self.call(agent_loop.cmd_migrate, worktree=str(tree), branch=True)
        self.assertEqual(brought["result"], "MIGRATED", brought)
        self.assertEqual((brought["module"], brought["commits"], brought["was"]), ("WATER", 2, was))
        self.assertIn("docs/plans/WATER/DONE.json", brought["renamed"])
        self.assertIn("README.md", brought["upstream_files"])
        self.assertEqual(self.git("log", "--format=%s", "origin/main..HEAD", where=tree).stdout.splitlines(),
                         ["M2: waves", "M2: first wave"])
        rebased = subprocess.run(["git", "-C", str(tree), "rebase", "origin/main"], capture_output=True, text=True)
        self.assertEqual(rebased.returncode, 0, rebased.stderr)  # nothing left to conflict
        doc = json.loads((tree / "docs/plans/WATER/DONE.json").read_text())
        m2 = doc["milestones"][1]
        self.assertEqual((m2["state"], m2["items"][0]["status"], m2["depends_on"]), ("in_progress", "pass", ["M1"]))
        self.assertEqual(m2["items"][1]["needs"]["type"], "hardware")
        self.assertEqual((tree / "src/waves.py").read_text(), "WAVES = 3\n")
        self.assertEqual(agent_loop.old_names_in_tree(tree)[0], [])
        self.assertNotIn("<<<<<<<", (tree / "docs/plans/WATER/DONE.json").read_text())
        self.assertNotIn(str(tree), json.dumps(self.migrate().get("worktrees_on_old_names") or []))
        ran = self.run_loop(worktree=str(tree))
        # `run` accepts it and starts M2's builder; the fake builder never merges, so its checks fail
        self.assertEqual((ran["result"], ran["milestone"]), ("CHECKS_FAILED", "M2"), ran)

    def test_r6_migrate_branch_leaves_later_conflicts_to_the_builders_next_merge(self):
        self.old_names()
        tree = self.builder_branched_before_migrate().resolve()
        self.migrate()
        migration = self.git("rev-parse", "origin/main~1").stdout.strip()  # STATUS.md follows the migration
        put(self.wt / "src/waves.py", "WAVES = 5\n")  # the main branch wrote the same new file differently
        self.commit_all()
        brought = self.call(agent_loop.cmd_migrate, worktree=str(tree), branch=True)
        self.assertEqual(brought["result"], "MIGRATED", brought)
        self.assertEqual(brought["conflicts"], ["src/waves.py"])
        self.assertIn(f"onto {migration[:12]}, the migration commit", brought["worktree"])
        self.assertEqual(self.git("rev-parse", "HEAD~2", where=tree).stdout.strip(), migration)
        self.assertEqual(agent_loop.old_names_in_tree(tree)[0], [])

    def test_r6_migrate_branch_refuses_earlier_conflicts_and_names_the_commit_to_resolve_them_on(self):
        self.old_names()
        tree = self.builder_branched_before_migrate().resolve()
        put(self.wt / "src/waves.py", "WAVES = 5\n")  # before the migration, the main branch wrote it differently
        self.commit_all()
        before = self.git("rev-parse", "HEAD").stdout.strip()
        self.migrate()
        was = agent_loop.head_commit(tree)
        refused = self.call(agent_loop.cmd_migrate, worktree=str(tree), branch=True)
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertEqual(refused["conflicts"], ["src/waves.py"])
        self.assertEqual((agent_loop.head_commit(tree), self.git("status", "--porcelain", where=tree).stdout),
                         (was, ""))
        self.assertEqual(refused["next"]["command"], f"git -C {tree} rebase {before[:12]}")
        self.assertIn("migrate --branch", refused["next"]["then"])
        # The builder resolves it there, where both sides use the old names, and then nothing conflicts.
        resolve = subprocess.run(["git", "-C", str(tree), "rebase", before], capture_output=True, text=True)
        self.assertNotEqual(resolve.returncode, 0)
        put(tree / "src/waves.py", "WAVES = 5\n")
        self.git("add", "src/waves.py", where=tree)
        self.git("-c", "core.editor=true", "rebase", "--continue", where=tree)
        self.assertEqual(self.call(agent_loop.cmd_migrate, worktree=str(tree), branch=True)["result"], "MIGRATED")

    def test_a_refused_review_keeps_the_profiles_review_host(self):
        refused = self.review("M1", commit="0" * 40)
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertNotIn("--host", refused["next"]["command"])  # another host would refuse it the same way

    def test_migrate_waits_for_running_loops(self):
        self.flatten()
        (agent_loop.loop_dir(self.wt) / "run-WATER.lock").write_text("1")  # a run elsewhere holds WATER
        with mock.patch.object(agent_loop, "run_holder", lambda folder, name: 1 if name == "WATER" else None):
            refused = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to=None)
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("WATER", refused["problems"][0])
        self.assertTrue((self.wt / "docs/plans/WATER-DONE.json").exists())

    def test_the_module_table_is_read_and_a_folder_without_a_row_is_named(self):
        rows = agent_loop.module_table(ARCH)
        self.assertEqual([(r["n"], r["module"], r["needs"]) for r in rows], [("1", "WATER", "none"), ("2", "SHIPS", "WATER")])
        self.assertIsNone(agent_loop.module_table("| # | Name | Needs |\n|---|---|---|\n| 1 | x | y |\n"))
        put(self.wt / "docs/plans/ARCHITECTURE.md", ARCH.replace("[WATER](WATER/DESIGN.md)", "SEA"))
        self.commit_all()
        r = self.ready()
        self.assertEqual(len(r["module_table"]), 1)
        self.assertIn("WATER has a folder under docs/plans but no row", r["module_table"][0])
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        self.assertIn("warning: WATER has a folder", status)  # SHIPS has a row and no folder: just not planned yet
        self.assertNotIn("SHIPS", status)

    def test_status_md_has_the_overview_then_every_module_in_build_order(self):
        doc = done(milestone("M1", "done", ["pass"]), milestone("M2", "not_started", ["open"], check="true",
                                                                  needs=needs("human_feedback", "the human")),
                   milestone("M3", "not_started", ["open"]))
        doc["milestones"][1]["state"], doc["milestones"][1]["blocked"] = "blocked", {
            "reason": "needs_human_feedback", "items": ["M2.1"], "what": "needs the human"}
        doc["milestones"][0]["name"] = "The sea moves on screen"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)}
        rec["milestones"]["M1"]["accepted"] = {"by": "review", "at": agent_loop.now(),
                                                "review": "docs/evidence/WATER/M1-review.md"}
        put(self.wt / "docs/plans/WATER/ACCEPTED.json", json.dumps(rec))
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water\n\n## Open for the human\n- Assumption: waves are blue\n")
        self.write_done([milestone("M1", "not_started", ["open"])], module="EXTRA")
        put(self.wt / "docs/plans/ARCHITECTURE.md", ARCH)
        put(self.wt / "docs/plans/GLOSSARY.md", "**Swell**\nA long wave.\nProposed: by a builder.\n")
        self.commit_all()
        page = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt), format="md")
        overview, modules = page.split("## All modules")
        self.assertLess(overview.index("## Overview"), overview.index("### Needs you now"))
        self.assertLess(overview.index("### Needs you now"), overview.index("### Choices made for you"))
        self.assertLess(overview.index("### Choices made for you"), overview.index("### Now and next"))
        self.assertLess(overview.index("### Now and next"), overview.index("### Recently done"))
        self.assertIn("0 of 3 modules done · 1 in progress · 2 to come", overview)
        # L5: what needs the human is apart from the choices a planner made for them
        needs_you, chosen = overview.split("### Choices made for you")
        chosen = chosen.split("### Now and next")[0]
        self.assertIn("- WATER assumes: waves are blue ([plan](WATER/PLAN.md))", chosen)
        self.assertIn("Swell (by a builder)", chosen)
        self.assertIn("Blocked: Needs Human Feedback, M2.1: M2.1 works (the human). You judge it", needs_you)
        self.assertNotIn("assumes", needs_you)
        self.assertIn("- M1 (EXTRA M1): Not Started · [plan](EXTRA/PLAN.md)", overview)
        self.assertIn("- The sea moves on screen (WATER M1), ", overview)
        self.assertIn("[review](../evidence/WATER/M1-review.md)", overview)
        lines = [line for line in modules.splitlines() if line.startswith("| ") and "---" not in line][1:]
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("| 1 | WATER |") and lines[0].endswith("| M2 of 3 · Blocked: Needs Human Feedback |"),
                        lines[0])
        self.assertTrue(lines[1].endswith("| Not planned yet |"), lines[1])
        self.assertTrue(lines[2].startswith("|  | EXTRA | (no row in the module table)"), lines[2])

    def test_a_record_write_lands_status_md_in_its_own_commit(self):
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("log", "-1", "--format=%s", "origin/main").stdout.strip(),
                         "orchestrate: update STATUS.md")
        self.assertNotIn(agent_loop.TRAILER, self.git("log", "-1", "--format=%B", "origin/main").stdout)
        page = self.git("show", "origin/main:docs/plans/STATUS.md").stdout
        self.assertIn("## Overview", page)
        before = self.git("rev-parse", "origin/main").stdout
        agent_loop.land_status(self.wt, self.prof(), "WATER")  # the same page again makes no commit
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("rev-parse", "origin/main").stdout, before)

    def test_status_md_that_cant_land_never_fails_the_record(self):
        real = agent_loop.land
        calls = []

        def flaky(tree, prof, check=False):
            calls.append(tree)
            if len(calls) > 1:  # every STATUS.md landing loses, as a rebase conflict would
                return False, "rebase onto origin/main failed: conflict in docs/plans/STATUS.md"
            return real(tree, prof, check)

        prof = self.prof()
        err = io.StringIO()
        with mock.patch.object(agent_loop, "land", flaky), contextlib.redirect_stderr(err):
            ok, landed = agent_loop.loop_write(self.wt, prof, "WATER", lambda t: (
                put(t / "docs/plans/WATER/NOTE.json", "{}"), ["docs/plans/WATER/NOTE.json"])[1], "orchestrate: note")
        self.assertTrue(ok, landed)
        self.assertEqual(len(calls), 3)  # the record, then STATUS.md twice: once regenerated from the newer tip
        self.assertIn("STATUS.md wasn't updated", err.getvalue())
        with mock.patch.object(agent_loop, "status_page", side_effect=RuntimeError("boom")), \
                contextlib.redirect_stderr(io.StringIO()):
            ok, _ = agent_loop.loop_write(self.wt, prof, "WATER", lambda t: (
                put(t / "docs/plans/WATER/NOTE.json", "[]"), ["docs/plans/WATER/NOTE.json"])[1], "orchestrate: note")
        self.assertTrue(ok)

    def test_status_md_is_never_unlanded_and_never_adopted_by_hand(self):
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        (self.wt / "docs/plans/STATUS.md").write_text("# my own notes\n")
        self.assertNotIn("unmerged_plans", self.ready())
        refused = self.adopt("docs/plans/STATUS.md")
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("written by the script", " ".join(refused["problems"]))


    def test_a_planner_turn_with_a_status_line_is_refused_with_why(self):
        os.environ.update(FAKE_ASSUME="\nNow: building M1\n")
        refused = self.plan()
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertTrue(any("`Now:` line" in p for p in refused["problems"]), refused["problems"])
        self.assertIn("`Now:` line", refused["next"]["command"])  # the planner is told why, to fix it

    def test_adopt_refuses_a_plan_that_fails_the_checks_and_land_only_warns(self):
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water\n## M1\n### Notes\n")
        refused = self.adopt()
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("`###` heading", " ".join(refused["problems"]))
        self.git("add", "-A")
        self.git("commit", "-qm", "builder ticks a box")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            agent_loop.cmd_merge(argparse.Namespace(worktree=str(self.wt), no_check=True))
        landed = json.loads(out.getvalue())
        self.assertEqual(landed["result"], "MERGED", landed)
        self.assertIn("`###` heading", landed["plan_warnings"][0])

    def test_status_warns_about_plan_files_outside_the_plans_folder(self):
        put(self.wt / "notes/BUILD-PLAN.md", "# old plan")
        self.commit_all()
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        self.assertIn("warning: notes/BUILD-PLAN.md is a plan file outside docs/plans", status)


class PlanFilesAlone(ProfileOnly):
    """Tests from PlanFiles that need no repository, only the project settings."""

    def test_plan_checks(self):
        p = "docs/plans/W/PLAN.md"
        self.assertEqual(agent_loop.plan_text_problems(p, "# W\n\n## M1 sea: done\n[review](x.md)\n\n## M2 waves\n"
                                                          "- [ ] a\n\n## Open for the human\n- Assumption: x\n"), [])
        cases = {"long": "word " * 1600, "Now:": "# W\nNow: building M2\n", "###": "# W\n## M2\n### Notes\n",
                 "## Log": "# W\n## Log\n- 2026-11-01 x\n", "under": "## M1 sea: done\n[review](x.md)\nsome notes\n"}
        for say, text in cases.items():
            found = agent_loop.plan_text_problems(p, text)
            self.assertEqual(len(found), 1, (say, found))
            self.assertIn({"long": "1,500", "under": "keeps one line"}.get(say, say), found[0])
        self.assertEqual(agent_loop.plan_text_problems(p, "# W\n```\n### an example\nNow: x\n```\n"), [])
        log = "# Log\n- 2026-11-01 short\n  and a second line\n- 2026-11-02 long\n" + "  more\n" * 8
        found = agent_loop.log_text_problems("docs/plans/W/LOG.md", log)
        self.assertEqual(len(found), 1)
        self.assertIn("1 entry longer than 8 lines", found[0])
        self.assertIn("2026-11-02 long", found[0])


class OnlyTheScriptSetsReadyForReview(Repo):
    """Release 3 of the 2026-11-12 plan: a builder merges with its milestone in progress, and the script sets Ready for
    Review only after its own checks pass (N2, P3, N3, N4)."""

    def merge(self):
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                agent_loop.cmd_merge(argparse.Namespace(worktree=str(self.wt), no_check=False))
        finally:
            release()
        return json.loads(out.getvalue().splitlines()[-1])

    def set_m1(self, state, status="pass", where=None):
        """Edits M1 in the worktree's done-when file and commits it, without merging."""
        where = where or self.wt
        path = where / "docs/plans/WATER/DONE.json"
        doc = json.loads(path.read_text())
        doc["milestones"][0]["state"] = state
        for i in doc["milestones"][0]["items"]:
            i["status"], i["evidence"] = status, "docs/evidence/WATER/run.log" if status == "pass" else ""
        path.write_text(json.dumps(doc))
        self.git("commit", "-qam", f"M1 {state}", where=where)

    def test_the_builder_merges_in_progress_and_the_script_sets_ready_for_review(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="captures"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True), result)
        self.assertEqual(self.calls()[0]["argv"][-1].count("with M1's state left as in_progress"), 1)
        self.assertEqual(self.read_done()["milestones"][0]["state"], "ready_for_review")
        self.assertEqual(self.read_record()["milestones"]["M1"]["ready_for_review"]["commit"], result["commit"])
        # the builder's commit says in_progress; the reviewer works on the script's commit, where it says Ready
        self.assertEqual(agent_loop.state_at(self.wt, result["commit"], "docs/plans/WATER/DONE.json", "M1"),
                         "in_progress")
        self.assertEqual(self.review(commit=result["commit"])["verdict"], "PASS")

    def test_a_failing_item_check_leaves_the_main_branch_without_ready_for_review(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="captures",
                                   check="echo building; echo 'thread main panicked at tile.rs:88' >&2; exit 3"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "NO_PROGRESS_FOR_HOURS")
        self.assertEqual(self.read_done()["milestones"][0]["state"], "in_progress")
        self.assertNotIn("ready_for_review", self.read_record()["milestones"]["M1"])
        why = self.state()["not_ready_reasons"]
        self.assertIn("exited 3", why)
        # stdout and stderr are shown apart, and both are saved whole (N3)
        self.assertIn("The end of its stdout:\nbuilding\nThe end of its stderr:\nthread main panicked", why)
        saved = re.search(r"and (\S+\.stderr) \(stderr\)", why).group(1)
        self.assertIn("panicked at tile.rs:88", Path(saved).read_text())
        self.assertEqual(Path(saved).parent, (self.wt / ".git/orchestrate/checks").resolve())

    def test_a_second_check_of_the_same_files_runs_no_command(self):
        count = self.root / "count"
        command = f"echo x >> {count}"
        first = agent_loop.try_check(self.wt, command, None, 30, "docs/plans")
        second = agent_loop.try_check(self.wt, command, None, 30, "docs/plans")
        self.assertEqual((first["result"], second["result"]), ("pass", "pass"))
        self.assertFalse(first.get("reused"))
        self.assertTrue(second["reused"])
        self.assertEqual(count.read_text(), "x\n")
        # a builder ticking items in the plans folder doesn't change what a check tests
        put(self.wt / "docs/plans/WATER/LOG.md", "- M1: done")
        self.assertTrue(agent_loop.try_check(self.wt, command, None, 30, "docs/plans")["reused"])
        # a change anywhere else does
        (self.wt / "src.txt").write_text("changed")
        self.assertFalse(agent_loop.try_check(self.wt, command, None, 30, "docs/plans").get("reused"))
        self.assertEqual(count.read_text(), "x\nx\n")
        # a failure is never reused
        (self.wt / "src.txt").unlink()
        failing = f"echo y >> {count}; exit 1"
        for _ in range(2):
            self.assertEqual(agent_loop.try_check(self.wt, failing, None, 30, "docs/plans")["result"], "fail")
        self.assertEqual(count.read_text().count("y"), 2)

    def test_the_test_command_merge_ran_isnt_run_again_by_the_script(self):
        count = self.root / "count"
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", f"`echo x >> {count}`"))
        self.write_done([milestone("M1", "in_progress", ["open"], inspect="captures"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.set_m1("in_progress")
        self.assertEqual(self.merge()["result"], "MERGED")
        self.assertEqual(count.read_text(), "x\n")
        os.environ.update(FAKE_PASS="0")
        result = self.run_loop(checks_only=True)
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertEqual(result["reused_checks"], ["Test command"])
        self.assertEqual(count.read_text(), "x\n")
        self.assertFalse(self.log.exists())  # no agent started

    def test_merge_refuses_a_builders_ready_for_review(self):
        self.write_done([milestone("M1", "in_progress", ["open"], inspect="captures"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.set_m1("ready_for_review")
        refused = self.merge()
        self.assertEqual(refused["result"], "FAILED")
        self.assertIn("Your commits set M1 to ready_for_review", refused["detail"])
        self.assertIn("Set the state back to in_progress in docs/plans/WATER/DONE.json", refused["detail"])
        self.assertEqual(self.read_done()["milestones"][0]["state"], "in_progress")
        self.set_m1("in_progress")  # what the message says to do
        self.assertEqual(self.merge()["result"], "MERGED")
        # the script's own Ready for Review, already on the main branch, isn't the next builder's change
        os.environ.update(FAKE_PASS="0")
        self.assertEqual(self.run_loop(checks_only=True)["result"], "READY_FOR_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        (self.wt / "more.txt").write_text("next milestone")
        self.git("add", "more.txt")
        self.git("commit", "-qm", "M2 work")
        self.assertEqual(self.merge()["result"], "MERGED")

    def test_an_upgraded_branch_that_set_ready_for_review_is_told_what_to_do(self):
        """A builder before 2.1.0 committed Ready for Review on its branch and stopped before merging."""
        self.write_done([milestone("M1", "in_progress", ["open"], inspect="captures"),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        self.set_m1("ready_for_review")
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "CHECKS_FAILED", result)
        self.assertIn("Your commits set M1 to ready_for_review", result["reasons"][0])
        first = self.prompt(self.calls()[0])
        self.assertIn("From the script:\nCommits in this worktree that haven't merged yet set M1 to "
                      "ready_for_review, as builders did before 2.1.0.", first)
        self.assertIn("Set the state back to in_progress", self.prompt(self.calls()[1]))
        self.assertEqual(self.read_done()["milestones"][0]["state"], "in_progress")
        self.set_m1("in_progress")
        self.assertEqual(self.merge()["result"], "MERGED")
        done = self.run_loop(checks_only=True)
        self.assertEqual((done["result"], done["review"]), ("READY_FOR_REVIEW", True), done)

    def test_ready_for_review_on_the_main_branch_without_a_record_is_checked_not_reviewed(self):
        """Thrum's main branch can hold a milestone a builder set Ready for Review before 2.1.0, with no record."""
        self.write_done([proved(milestone("M1", "ready_for_review", ["pass"], inspect="captures")),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        refused = self.review()
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("no record that its checks passed", refused["problems"][0])
        self.assertIn(" run --module WATER ", refused["next"]["command"])
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M1")
        os.environ.update(FAKE_PASS="0")
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True), result)
        self.assertFalse(self.log.exists())  # checked before any builder turn
        self.assertEqual(self.review(commit=result["commit"])["verdict"], "PASS")

    def test_ready_for_review_without_a_record_goes_back_to_in_progress_when_its_checks_fail(self):
        self.write_done([proved(milestone("M1", "ready_for_review", ["pass"], inspect="captures", check="test -f proof")),
                         milestone("M2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="Working on it.")
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "NO_PROGRESS_FOR_HOURS")
        self.assertEqual(self.read_done()["milestones"][0]["state"], "in_progress")
        self.assertIn("From the script:\nThe script can't set the milestone to Ready for Review yet: M1.1 "
                      "`test -f proof` exited 1", self.prompt(self.calls()[0]))


    def test_the_run_waits_for_a_merge_left_running_in_the_background(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_background(argparse.Namespace(
                worktree=str(self.wt), log=None, command_args=["sh", "-c", "sleep 0.3", "agent_loop.py", "merge"]))
            agent_loop.cmd_background(argparse.Namespace(
                worktree=str(self.wt), log=None, command_args=["sleep", "30"]))
        started = time.time()
        waited = agent_loop.wait_for_merges(self.wt)
        self.assertEqual(len(waited), 1)
        self.assertTrue(waited[0].endswith("exited 0"), waited)
        self.assertTrue(0.2 < time.time() - started < 20)  # it waited for the merge, not the other job
        for job in agent_loop.worktree_jobs(self.wt, running_only=True):
            os.killpg(int(job["pid"]), signal.SIGTERM)


class OnlyTheScriptSetsReadyForReviewAlone(ProfileOnly):
    """Tests from OnlyTheScriptSetsReadyForReview that need no repository, only the project settings."""

    def test_a_record_older_than_a_failed_review_is_not_current(self):
        ready = {"commit": "abc", "at": "2026-11-12T10:00:00Z"}
        self.assertTrue(agent_loop.ready_current({"ready_for_review": ready}))
        self.assertFalse(agent_loop.ready_current({"ready_for_review": ready, "reviews": [
            {"verdict": "fail", "at": "2026-11-12T11:00:00Z"}]}))
        self.assertTrue(agent_loop.ready_current({"ready_for_review": ready, "reviews": [
            {"verdict": "pass", "at": "2026-11-12T11:00:00Z"}]}))
        self.assertTrue(agent_loop.ready_current({"ready_for_review": {**ready, "at": "2026-11-12T12:00:00Z"},
                                                  "reviews": [{"verdict": "fail", "at": "2026-11-12T11:00:00Z"}]}))
        self.assertFalse(agent_loop.ready_current({}))


class OldNeedsTest(Clean):
    def test_an_old_attended_note_becomes_the_matching_needs_type(self):
        cases = {"Screen Recording permission already granted; approve Computer Use for IINA": "access",
                 "plug in the iPhone": "hardware",
                 "the human judges whether the animation is smooth": "human_feedback"}
        for text, kind in cases.items():
            self.assertEqual(agent_loop.old_needs({"attended": text})["type"], kind, text)


class ScriptFactsTest(Clean):
    """When the script can't establish a fact, it names where the fact lives rather than stating or dropping it."""

    def test_a_round_without_recorded_findings_names_its_review(self):
        e = {"reviews": [{"verdict": "fail", "at": "2026-11-11T03:14:00Z", "review": "docs/evidence/C/M1-review-1.md"}]}
        with mock.patch.object(agent_loop, "counted_reviews", lambda e, after=None: e["reviews"]):
            line = agent_loop.history_lines(e)[0]
        self.assertNotIn("no findings recorded", line)
        self.assertIn("read docs/evidence/C/M1-review-1.md", line)

    def test_a_design_re_review_that_cant_compare_says_so(self):
        rec = {"design": {"commit": "a" * 40, "review": "docs/evidence/C/design-review.md", "verdict": "changes"}}
        with mock.patch.object(agent_loop, "path_at", lambda *args: None):
            text, changed = agent_loop.design_changes(Path("."), rec, "docs/plans/C/DONE.json", {"milestones": []})
        self.assertIsNone(changed)
        self.assertIn("couldn't compare", text)
        self.assertIn("docs/evidence/C/design-review.md", text)

    def test_a_changed_design_document_is_named(self):
        doc = {"milestones": []}
        rec = {"design": {"commit": "a" * 40, "review": "r.md", "hash": agent_loop.text_hash("old design")}}
        with mock.patch.object(agent_loop, "path_at", lambda w, c, path: path), \
                mock.patch.object(agent_loop, "show", lambda w, c, path: json.dumps(doc)):
            text, changed = agent_loop.design_changes(Path("."), rec, "D.json", doc, "DESIGN.md", "new design")
        self.assertTrue(changed)
        self.assertIn("the design document (DESIGN.md)", text)

    def test_the_planner_task_after_design_changes_counts_must_fix_and_frees_suggestions(self):
        out = {"verdict": "DESIGN CHANGES", "review": "docs/evidence/C/design-review.md",
               "line": "DESIGN CHANGES: 2 must_fix findings"}
        task = agent_loop.design_review_next(out, "C", Path("/tmp/x"), {"default_host": "codex"})["command"]
        self.assertIn("Resolve its 2 Must Fix findings", task)
        self.assertIn("Suggestions are yours to take or leave", task)

    def test_a_block_records_where_the_builders_work_is(self):
        note = agent_loop.work_note({"work": {"branch": "build/atmosphere", "commit": "7911c75b" + "0" * 32}})
        self.assertIn("branch build/atmosphere at 7911c75b0000", note)
        self.assertIn("git show", note)

    def test_the_session_and_resource_rules(self):
        self.assertIn("can't appear", agent_loop.session_rule(True, "codex"))
        self.assertIn("visible in the Codex app", agent_loop.session_rule(False, "codex"))
        rule = agent_loop.resources_rule({"exclusive resources": "gpu"})
        self.assertIn("exclusive resources are: gpu", rule)
        self.assertIn("waits its turn", rule)


class DesignReReview(Repo):
    def test_an_unchanged_design_after_changes_is_not_reviewed_again(self):
        self.write_done([milestone("M1", "not_started", ["open"], inspect="frames")], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        self.review("design", commit=None)
        again = self.review("design", commit=None)
        self.assertEqual(again["result"], "INVALID", again)
        self.assertIn("the planner hasn't acted yet", again["problems"][0])
        self.assertIn(" plan --worktree ", again["next"]["command"])


class BackgroundJobs(Clean):
    """`background`, `jobs` and `wait`: in Thrum builders waited on long captures with sleep and tail, and each check
    re-read the whole conversation."""

    def script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "agent_loop.py"), *args], capture_output=True,
                              text=True, timeout=60)

    def test_wait_returns_the_exit_code_and_the_end_of_the_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            started = json.loads(self.script("background", "--worktree", tmp, "--", "echo hi; exit 3").stdout)
            waited = self.script("wait", started["job"], "--worktree", tmp, "--timeout", "30").stdout
            self.assertIn("exited 3", waited)
            self.assertIn("hi", waited)
            jobs = json.loads(self.script("jobs", "--worktree", tmp, "--json").stdout)
            self.assertEqual([(j["state"], j.get("exit")) for j in jobs], [("exited", 3)])
            self.assertTrue(started["log"].startswith(str(Path(tmp).resolve() / ".git")))

    def test_wait_stops_on_a_match_and_on_its_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            started = json.loads(self.script("background", "--worktree", tmp, "--",
                                             "echo ready; sleep 30").stdout)
            self.assertIn("matched", self.script("wait", started["job"], "--worktree", tmp, "--until", "ready",
                                                 "--timeout", "20").stdout)
            self.assertIn("still running after 1 s", self.script("wait", started["job"], "--worktree", tmp,
                                                                 "--timeout", "1").stdout)
            os.killpg(started["pid"], signal.SIGTERM)

    def test_a_resumed_builder_is_told_about_its_running_jobs_and_the_turn_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            started = json.loads(self.script("background", "--worktree", tmp, "--", "sleep 30").stdout)
            facts = agent_loop.resume_facts(Path(tmp), milestone("M1", "in_progress", ["pass", "open"]), 124, 2.0)
            self.assertIn("2-hour turn limit", facts)
            self.assertIn(started["job"], facts)
            self.assertIn("Passed: M1.1.", facts)
            os.killpg(started["pid"], signal.SIGTERM)
            self.assertNotIn("turn limit", agent_loop.resume_facts(Path(tmp), None, 0, 2.0))


class MergeUpstream(Clean):
    def test_merge_lists_the_files_the_rebase_brought_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, wt = Path(tmp, "repo"), Path(tmp, "repo-build")
            run = lambda *a, where=main: subprocess.run(["git", "-C", str(where), *a], check=True, capture_output=True)
            run("init", "-q", "-b", "main", str(main), where=tmp)
            run("config", "user.name", "t")
            run("config", "user.email", "t@t")
            (main / "ORCHESTRATE.md").write_text("- **Merge:** local\n- **Test command:** none\n")
            run("add", "-A")
            run("commit", "-qm", "init")
            run("worktree", "add", "-q", "-b", "build/x", str(wt), "main")
            (wt / "feature").write_text("x")
            run("add", "-A", where=wt)
            run("commit", "-qm", "feature", where=wt)
            (main / "camera.rs").write_text("moved")
            run("add", "-A")
            run("commit", "-qm", "another module")
            out = subprocess.run([sys.executable, str(SCRIPTS / "agent_loop.py"), "merge", "--worktree", str(wt)],
                                 capture_output=True, text=True)
            result = json.loads(out.stdout)
            self.assertEqual(result["result"], "MERGED", out.stderr)
            self.assertEqual(result["upstream_files"], ["camera.rs"])


class Versions(Clean):
    def test_the_script_version_matches_the_marketplace(self):
        market = json.loads((SCRIPTS.parents[3] / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(next(p["version"] for p in market["plugins"] if p["name"] == "orchestrate"),
                         agent_loop.VERSION)

    def test_a_newer_installed_copy_is_found_beside_a_cached_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            rest = Path("skills/orchestration/build/scripts/agent_loop.py")
            for version in ("1.7.1", "2.0.0", "2.1.0"):
                put(Path(tmp, "orchestrate", version) / rest, "")
            with mock.patch.object(agent_loop, "LOOP", Path(tmp, "orchestrate", "1.7.1") / rest):
                self.assertEqual(agent_loop.newer_install(), str(Path(tmp, "orchestrate", "2.1.0") / rest))
            with mock.patch.object(agent_loop, "LOOP", Path(tmp, "orchestrate", "2.1.0") / rest):
                self.assertIsNone(agent_loop.newer_install())

    def test_the_review_prompt_names_the_checks_the_script_already_ran(self):
        prof = {"test_command": "./dev check"}
        note = agent_loop.checks_note(prof, milestone("M1", "ready_for_review", ["pass", "pass"]), "abc123def4567")
        self.assertIn("`./dev check`", note)
        self.assertIn("M1.1, M1.2", note)
        self.assertEqual(agent_loop.checks_note(prof, milestone("M1", "ready_for_review", ["pass"]), None), "")


def token_count(total_in, cached, out, context, window=475000):
    """A rollout file's token_count line, in the shape Codex writes (read from a real rollout, 2026-11-11):
    input_tokens includes the cached ones."""
    usage = {"input_tokens": total_in, "cached_input_tokens": cached, "cache_write_input_tokens": 0,
             "output_tokens": out, "reasoning_output_tokens": 0, "total_tokens": total_in + out}
    return {"timestamp": "2026-11-11T22:46:59.202Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
        "total_token_usage": usage, "last_token_usage": {"input_tokens": context - 100, "cached_input_tokens": 0,
                                                         "output_tokens": 100, "total_tokens": context},
        "last_usage_includes_reasoning": True, "model_context_window": window},
        "rate_limits": {"limit_id": "codex", "primary": {"used_percent": 72.0}}}}


class SessionTokens(Clean):
    """Release 1 of the 2026-11-12 plan: tokens and how full a session is, read from the host's own records."""

    def test_codex_figures_come_from_the_rollout_files_last_token_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            thread = "01a1ccb6-a70b-7430-85c0-4d446614d3da"
            day = Path(tmp) / "sessions" / "2026" / "11" / "11"
            day.mkdir(parents=True)
            lines = [token_count(19933, 7168, 5, 19938), {"type": "event_msg", "payload": {"type": "agent_message"}},
                     token_count(91234, 57856, 294, 300000),
                     {"type": "event_msg", "payload": {"type": "token_count", "info": None}}]  # a rate-limit update
            path = day / f"rollout-2026-11-11T23-24-44-{thread}.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in lines) + '\n{"type": "event_msg", "payload": {"type": "tok')
            with mock.patch.object(agent_loop, "CODEX_HOME", Path(tmp)):
                self.assertEqual(agent_loop.session_tokens("codex", thread), {
                    "total": {"input": 91234 - 57856, "cached": 57856, "output": 294}, "context": 300000,
                    "window": 475000})
            # read from the end in blocks far smaller than a line, the line is still found whole
            found = agent_loop.last_event(path, '"token_count"', lambda e: e["payload"]["info"], block=64)
            self.assertEqual(found["payload"]["info"]["total_token_usage"]["input_tokens"], 91234)
            with mock.patch.object(agent_loop, "CODEX_HOME", Path(tmp)):
                self.assertEqual(agent_loop.session_tokens("codex", "no-such-thread"), {})

    def test_claude_context_is_its_last_messages_usage_and_window_its_results(self):
        out = "\n".join(json.dumps(e) for e in [
            {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 5, "cache_read_input_tokens": 9000,
                                                                   "output_tokens": 20}}},
            {"type": "assistant", "parent_tool_use_id": "tool1", "message": {"id": "s", "usage": {"input_tokens": 1}}},
            {"type": "assistant", "message": {"id": "b", "usage": {"input_tokens": 10, "cache_creation_input_tokens": 400,
                                                                   "cache_read_input_tokens": 120000,
                                                                   "output_tokens": 90}}},
            {"type": "result", "result": "DONE", "modelUsage": {"claude-opus-5-5": {"contextWindow": 200000},
                                                                "claude-haiku": {"contextWindow": 200000}}}])
        self.assertEqual(agent_loop.session_tokens("claude", "s1", out), {"context": 120500, "window": 200000})

    def test_cost_says_from_when_codex_figures_are_per_turn(self):
        rows = [{"at": "2026-11-10T09:00:00Z", "host": "codex"},
                {"at": "2026-11-12T09:00:00Z", "host": "codex", "version": "2.1.0"}]
        self.assertEqual(agent_loop.per_turn_from(rows), "2026-11-12T09:00:00Z")
        self.assertIsNone(agent_loop.per_turn_from(rows[:1]))


class StaleSessions(Clean):
    """Release 2: when the script stops resuming a session."""

    def test_a_session_over_60_percent_full_is_not_resumed(self):
        state = {"version": agent_loop.VERSION, "context": 285000, "window": 475000}
        self.assertIsNone(agent_loop.stale_session(state))
        state["context"] = 300000
        self.assertEqual(agent_loop.stale_session(state), "the session was 63% full (300,000 of 475,000 tokens)")
        self.assertIsNone(agent_loop.stale_session({"version": agent_loop.VERSION, "context": 300000}))

    def test_a_session_another_version_started_is_not_resumed(self):
        self.assertIn("a version before 2.1.0", agent_loop.stale_session({"thread": "t1", "turns": 4}))
        self.assertIn("version 2.0.9 of the script", agent_loop.stale_session({"version": "2.0.9"}))


class TokensAndSessions(Repo):
    """Releases 1 and 2 end to end: rows from the rollout file, and new sessions in place of full or old ones."""

    def rollout(self, thread="t1"):
        day = self.home / "sessions" / "2026" / "11" / "12"
        day.mkdir(parents=True, exist_ok=True)
        return day / f"rollout-2026-11-12T09-00-00-{thread}.jsonl"

    def final_total(self, path):
        info = [json.loads(l)["payload"]["info"] for l in path.read_text().splitlines()]
        total = [i for i in info if i][-1]["total_token_usage"]
        return {"input": total["input_tokens"] - total["cached_input_tokens"],
                "cached": total["cached_input_tokens"], "output": total["output_tokens"]}

    def test_a_two_turn_rollout_and_its_rows_add_up_to_its_final_total(self):
        path = self.rollout()
        os.environ.update(FAKE_PASS="0", FAKE_ROLLOUT=str(path), FAKE_USAGE="1")  # stdout's own figures too
        prof = agent_loop.profile(self.wt, strict=True)
        for session in (None, "t1"):  # a new session, then that session resumed
            agent_loop.run_turn("codex", prof, "m", "medium", self.wt, "go", session, 30)
        rows = agent_loop.ledger_rows(self.wt)
        summed = agent_loop.add_usage({}, {})
        for r in rows:
            summed = agent_loop.add_usage(summed, r["usage"])
        self.assertEqual({k: summed[k] for k in agent_loop.TOKEN_KEYS}, self.final_total(path))
        self.assertEqual([(r["context"], r["window"], r["version"]) for r in rows],
                         [(40000, 475000, agent_loop.VERSION)] * 2)
        self.assertNotIn("incomplete_turns", summed)

    def test_a_turn_stopped_at_the_turn_limit_gets_a_row_with_its_tokens(self):
        path = self.rollout()
        path.write_text(json.dumps(token_count(500000, 400000, 9000, 120000)) + "\n")  # the session's earlier turns
        os.environ.update(FAKE_PASS="0", FAKE_ROLLOUT=str(path), FAKE_SLEEP="30")
        prof = agent_loop.profile(self.wt, strict=True)
        code = agent_loop.run_turn("codex", prof, "m", "medium", self.wt, "go", "t1", 0.5)[0]
        self.assertEqual(code, 124)
        row = agent_loop.ledger_rows(self.wt)[-1]
        self.assertEqual((row["exit"], row["usage"]), (124, {"input": 2000, "cached": 8000, "output": 300, "turns": 1}))
        self.assertNotIn("stderr", row)  # a turn stopped at the limit isn't a failure

    def test_a_failed_turn_keeps_the_end_of_the_hosts_stderr(self):
        os.environ.update(FAKE_PASS="0", FAKE_FAIL_RESUME="t9")
        prof = agent_loop.profile(self.wt, strict=True)
        agent_loop.run_turn("codex", prof, "m", "medium", self.wt, "go", "t9", 30)
        row = agent_loop.ledger_rows(self.wt)[-1]
        self.assertEqual((row["exit"], row["usage"]), (1, {"incomplete_turns": 1}))
        self.assertIn("no rollout found for thread id t9", row["stderr"])

    def stalled_run(self, contexts="40000"):
        """A run whose builder reports nothing, so it stops STALLED after three turns, on thread t1."""
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working", FAKE_ROLLOUT=str(self.rollout()),
                          FAKE_CONTEXTS=contexts)
        return self.restore("stalled-run", self.run_loop)

    def resumed(self, calls):
        return ["resume" in c["argv"] for c in calls]

    def test_a_session_that_crosses_60_percent_mid_run_is_replaced_before_the_next_turn(self):
        result = self.stalled_run("100000,300000,50000")
        self.assertEqual(result["result"], "STALLED")
        self.assertEqual(self.resumed(self.calls()), [False, True, False])
        self.assertEqual(result["fresh_because"], ["the session was 63% full (300,000 of 475,000 tokens)"])
        new = self.prompt(self.calls()[2])
        self.assertIn("This is a new session. An earlier session worked on M1", new)
        self.assertIn("create_goal", new)  # the new Codex session gets its own goal
        self.assertEqual((self.state()["context"], self.state()["version"]), (50000, agent_loop.VERSION))

    @shares("stalled-run")
    def test_a_session_from_a_state_file_2_0_0_wrote_is_not_resumed(self):
        self.assertEqual(self.stalled_run()["result"], "STALLED")
        state = self.state()
        for key in ("version", "context", "window"):  # 2.0.0 wrote none of these
            state.pop(key)
        (self.wt / ".git/orchestrate/WATER.json").write_text(json.dumps(state))
        result = self.run_loop()
        self.assertEqual(self.resumed(self.calls()[3:]), [False, True, True])
        self.assertEqual(result["fresh_because"], [
            f"the session was started by a version before 2.1.0 of the script, and this is {agent_loop.VERSION}"])
        self.assertEqual(self.state()["version"], agent_loop.VERSION)
        self.assertEqual(self.run_loop().get("fresh_because"), None)  # the new session is resumed as usual

    @shares("stalled-run")
    def test_a_resume_that_fails_before_its_turn_starts_gets_one_new_session(self):
        os.environ.update(FAKE_THREAD="old")
        self.assertEqual(self.stalled_run()["result"], "STALLED")
        os.environ.update(FAKE_THREAD="new", FAKE_FAIL_RESUME="old")
        result = self.run_loop(message="The console is unlocked now.")
        calls = self.calls()[3:]
        self.assertEqual(self.resumed(calls), [True, False, True, True])
        self.assertEqual(result["result"], "STALLED")
        self.assertEqual(result["fresh_because"], ["resuming session old failed before its turn started: "
                                                   "ERROR: no rollout found for thread id old"])
        self.assertIn("From the lead:\nThe console is unlocked now.", self.prompt(calls[1]))
        self.assertEqual(self.state()["thread"], "new")

    @shares("stalled-run")
    def test_a_resume_that_fails_again_in_its_new_session_is_host_failed(self):
        self.assertEqual(self.stalled_run()["result"], "STALLED")
        os.environ.update(FAKE_EXIT="1")
        result = self.run_loop()
        self.assertEqual(result["result"], "HOST_FAILED")
        self.assertEqual(self.resumed(self.calls()[3:]), [True, False])


if __name__ == "__main__":
    unittest.main()
