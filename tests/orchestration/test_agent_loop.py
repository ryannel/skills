"""Checks for agent_loop's mechanical decisions: the acceptance record, the queue, claims, reviews, plans, owner
commands, profile, pins, locks and report lines. Hosts are fake executables; no model is launched.

Tests named after a review finding (astra_1, fable_3, ...) reproduce that finding from
workbench/review-2026-11-08 and check it no longer happens."""

import argparse
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
import os
import re
import shlex
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
from support import (BASE_PROFILE, PROFILE, SCRIPTS, Clean, Repo, agent_loop, check_next_commands, done, item,  # noqa: E402
                     work_package, parse, proved, put, release, shares, COMMANDS, parse_argv)


def too_many(mid, statuses, **kw):
    """A work package blocked after too many failed reviews, waiting for the user to decide."""
    return dict(work_package(mid, "blocked", statuses, **kw),
                blocked={"reason": "too_many_failed_reviews", "what": "the user decides"})


def needs(kind, what):
    """An item's `needs` field."""
    return {"type": kind, "what": what}


def failed_before(m):
    """A work package whose last review failed every item, as a done-when file kept from before rounds kept their
    findings leaves it."""
    for i in m["items"]:
        i["verdict"] = "fail"
    return m


def entry_for(doc, design_ok=True):
    """A project entry as agent_loop.project builds it in a repository taking up the loop (finished work packages taken
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


# The counts the escalation ladder climbs by. Tests build their scenarios from these, so the user's choice of
# count can change without breaking them.
REPEATS = agent_loop.REPEATS_TO_DIAGNOSE
NEW_SESSION = agent_loop.NEW_SESSION_AFTER_FAILED_REVIEWS


class Decisions(Clean):
    def test_what_the_counts_call_for(self):
        # failed reviews that repeat a finding: a new builder session one short of the diagnosis, the diagnosis at
        # REPEATS (or at the new-session count of every failed review, if that comes first)
        self.assertEqual([agent_loop.escalation(n, with_repeat=n) for n in range(REPEATS + 2)],
                         ["none"] + ["diagnosis" if n >= REPEATS else
                                     "new_builder_session" if n in (REPEATS - 1, NEW_SESSION) else
                                     "same_builder" for n in range(1, REPEATS + 2)])
        self.assertEqual(agent_loop.escalation(REPEATS - 1, with_repeat=REPEATS - 1), "new_builder_session")
        self.assertEqual(agent_loop.escalation(REPEATS, with_repeat=REPEATS), "diagnosis")
        # every failed review counts: three start a new session even with nothing repeated, and six a diagnosis
        self.assertEqual([agent_loop.escalation(n) for n in range(1, 8)],
                         ["same_builder", "same_builder", "new_builder_session", "same_builder", "same_builder",
                          "diagnosis", "diagnosis"])
        # a work package gets one diagnosis, so the same counts after it block the work package
        self.assertEqual(agent_loop.escalation(REPEATS, with_repeat=REPEATS, diagnoses=1), "too_many_failed_reviews")
        self.assertEqual(agent_loop.escalation(6, with_repeat=1, diagnoses=1), "too_many_failed_reviews")
        self.assertEqual(agent_loop.escalation(1, with_repeat=1, diagnoses=1), "same_builder")

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
                m = {k: v for k, v in work_package("WP1", "in_progress", ["open"]).items() if k not in agent_loop.COUNTS}
                doc = done(dict(m, **old))
                self.assertTrue(agent_loop.old_names_in_doc(doc))
                up = agent_loop.upgrade_doc(doc)
                self.assertEqual(tuple(up["work_packages"][0][k] for k in agent_loop.COUNTS), new)
                self.assertEqual((agent_loop.old_names_in_doc(up), agent_loop.validate(up, "WATER")), ([], []))
        self.assertEqual(agent_loop.escalation_of({"failed_reviews": 6, "failed_reviews_with_repeat": 1}), "diagnosis")

    def test_a_finding_repeats_by_name_or_by_item_unless_it_says_how_it_differs(self):
        found = [{"name": "seams show", "item": "WP1.1"}, {"name": "crash on load"},
                 {"name": "foam is grey", "item": "WP1.2", "different": "WP1.2 failed on speed before, colour now"},
                 {"name": "slow", "item": "WP1.2"}]
        self.assertEqual(agent_loop.repeats(found, {"seams show", "crash on load"}, {"WP1.2"}),
                         ["seams show", "crash on load", "slow"])
        self.assertEqual(agent_loop.repeats(found, set(), set()), [])

    def test_findings_are_checked(self):
        items = [{"id": "WP1.1"}]
        ok = {"findings": [{"name": "seams show", "item": "WP1.1"}, {"name": "crash", "different": "new"}]}
        self.assertEqual(agent_loop.findings_problems(ok, "WP1", items), [])
        for bad, says in (({"findings": {"name": "x"}}, "should be a list"),
                          ({"findings": [{"item": "WP1.1"}]}, "needs a short name"),
                          ({"findings": [{"name": "x"}, {"name": "x"}]}, "two findings are named"),
                          ({"findings": [{"name": "x", "item": "WP9.9"}]}, "isn't one of WP1's"),
                          ({"findings": [{"name": "x", "different": True}]}, "should be text")):
            self.assertTrue(any(says in p for p in agent_loop.findings_problems(bad, "WP1", items)), bad)

    def test_plan_forecast_lasts_when_the_open_work_fits(self):
        acc = {"used_percent": 50.0, "hours_left": 100.0}
        history = [{"status": "done", "reviews": 3, "pct": [1.0, 1.2, 1.5]},
                   {"status": "done", "reviews": 1, "pct": [2.0, 2.4, 3.0]}]
        open_ms = [{"status": "not_started", "reviews": 1}] * 4
        recent = {"hours": 12.0, "loop": [1.0, 1.0, 1.0], "other": [0.6, 1.2, 1.8]}
        f = agent_loop.plan_forecast(acc, history, open_ms, recent)
        self.assertEqual(f["per_work_package"], [1.0, 1.8, 3.0])
        self.assertEqual(f["reviews_per_work_package"], 2.0)
        self.assertEqual(f["plan_pct"], [4.0, 7.2, 12.0])
        self.assertEqual(f["other_use_before_reset"], [5.0, 10.0, 15.0])  # at the last 12 h's rate, not the week's
        self.assertFalse(f["warn"])
        self.assertTrue(f["verdict"].startswith("Quota lasts"), f["verdict"])
        self.assertNotIn("runs_out", f)

    def test_plan_forecast_warns_only_when_it_wont_last(self):
        history = [{"status": "done", "reviews": 1, "pct": [4.0, 5.0, 6.0], "builder_hours": 2.0}] * 2
        recent = {"hours": 10.0, "loop": [1.0, 1.0, 1.0], "other": [0.0, 0.0, 0.0]}
        short = agent_loop.plan_forecast({"used_percent": 90.0, "hours_left": 100.0}, history,
                                         [{"status": "not_started"}] * 4, recent)  # 16-24 % against 10 % left
        self.assertTrue(short["warn"])
        self.assertTrue(short["verdict"].startswith("Quota runs short"), short["verdict"])
        self.assertEqual(short["plan_hours_one_builder"], 8.0)
        self.assertIn("runs_out", short)  # 2.5 %/h uses the 10 % up in four hours
        maybe = agent_loop.plan_forecast({"used_percent": 95.0, "hours_left": 100.0}, history,
                                         [{"status": "not_started"}], recent)  # 4-6 % against 5 % left
        self.assertTrue(maybe["warn"])
        self.assertTrue(maybe["verdict"].startswith("Quota may run short"), maybe["verdict"])

    def test_plan_forecast_says_too_little_data_without_history(self):
        acc = {"used_percent": 20.0, "hours_left": 100.0}
        recent = {"hours": 12.0, "loop": [0.0] * 3, "other": [0.0] * 3}
        f = agent_loop.plan_forecast(acc, [{"status": "not_started", "pct": [1, 1, 1]}], [{"status": "not_started"}] * 2, recent)
        self.assertIsNone(f["plan_pct"])
        self.assertFalse(f["warn"])
        self.assertIn("Too little data", f["verdict"])

    def test_quota_never_fails_the_result_line(self):
        with mock.patch.object(agent_loop.codex_quota, "read", side_effect=OSError("disk gone")):
            self.assertEqual(agent_loop.quota_now(), {"unavailable": "OSError: disk gone"})


    def test_report_word_reads_only_the_last_line(self):
        self.assertEqual(agent_loop.report_word("work\nevidence\nBLOCKED: no Metal device"), "BLOCKED")
        self.assertEqual(agent_loop.report_word("`DONE`"), "DONE")
        self.assertIsNone(agent_loop.report_word("DONE\nActually the work package is not complete yet."))
        self.assertIsNone(agent_loop.report_word("still working"))

    def test_pin_mismatch_lists_wrong_turns_and_skips_partial_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            rollout = Path(tmp) / "rollout.jsonl"
            rollout.write_text("\n".join([
                json.dumps({"type": "turn_context", "payload": {"turn_id": "a", "model": "gpt-6.2-sol", "effort": "medium"}}),
                json.dumps({"type": "turn_context", "payload": {"turn_id": "b", "model": "gpt-6.2-sol", "effort": "xhigh"}}),
                '{"type": "turn_context", "payload": {"turn_id": "c", "mod']))
            self.assertEqual(agent_loop.pin_mismatches(rollout), ["b: gpt-6.2-sol/xhigh"])

    def test_definitions_ignore_claims_but_not_checks_or_needs(self):
        m = work_package("WP1", "not_started", ["open"])
        before = agent_loop.definitions(m)
        m["items"][0].update(builder_result="pass", evidence="log", verdict="pass")
        self.assertEqual(agent_loop.definitions(m), before)
        m["items"][0]["needs"] = needs("hardware", "plug in the phone")
        self.assertNotEqual(agent_loop.definitions(m), before)

    def test_last_work_package_and_inspected_work_packages_need_review(self):
        d = done(work_package("WP1", "not_started", ["pass"]), work_package("WP2", "not_started", ["open"]))
        self.assertFalse(agent_loop.needs_review(d["work_packages"][0], d))
        self.assertTrue(agent_loop.needs_review(d["work_packages"][1], d))

    def test_validate_rejects_missing_proof_and_empty_work_packages(self):
        bare = work_package("WP1", "not_started", ["open"])
        del bare["items"][0]["check"]
        self.assertTrue(any("nothing proves it" in p for p in agent_loop.validate(done(bare))))
        self.assertTrue(any("no items" in p for p in agent_loop.validate(done(work_package("WP1", "not_started", [])))))
        dup = done(work_package("WP1", "not_started", ["open"]), work_package("WP1", "not_started", ["open"]))
        self.assertTrue(any("duplicate" in p for p in agent_loop.validate(dup)))
        self.assertEqual(agent_loop.validate(done(work_package("WP1", "not_started", ["open"]))), [])

    def test_astra_14_malformed_shapes_are_problems_not_crashes(self):
        for bad in ({"work_packages": "bad"}, {"work_packages": ["x"]}, [], {"work_packages": [{"id": 3, "items": "no"}]},
                    done(dict(work_package("WP1", "not_started", ["open"]), failed_reviews_with_repeat=-1)),
                    done(dict(work_package("WP1", "not_started", ["open"]), items=[{"id": "a", "statement": "s", "check": 3}]))):
            self.assertTrue(agent_loop.validate(bad), bad)

    def test_reads_must_be_a_list_of_relative_pathspecs_on_an_item_with_a_check(self):
        def problems(**fields):
            m = work_package("WP1", "not_started", ["open"])
            m["items"][0].update(fields)
            return agent_loop.validate(done(m), "WATER")
        self.assertEqual(problems(reads=["src/", "models/*.json", ":(exclude)src/vendor"]), [])
        for bad in ("src/", [], [""], ["src/", 3], {"src": True}):
            self.assertTrue(any("non-empty list of git pathspecs" in p for p in problems(reads=bad)), bad)
        self.assertTrue(any("relative to the repository's top" in p for p in problems(reads=["/etc/passwd"])))
        self.assertTrue(any("relative to the repository's top" in p for p in problems(reads=["src/../../x"])))
        self.assertTrue(any("has no check" in p for p in problems(reads=["src/"], check="", inspect="captures")))

    def test_fable_8_forward_and_self_needs_in_a_module_are_errors(self):
        d = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["WP2"]), work_package("WP2", "not_started", ["open"]))
        self.assertTrue(any("comes at or after it" in p for p in agent_loop.validate(d, "WATER")))
        d = done(work_package("WP1", "not_started", ["open"]), dict(work_package("WP2", "not_started", ["open"]), depends_on=["WP9"]))
        self.assertTrue(any("isn't in this module" in p for p in agent_loop.validate(d, "WATER")))
        ok = done(work_package("WP1", "not_started", ["open"]), dict(work_package("WP2", "not_started", ["open"]), depends_on=["WP1", "CORE:WP3"]))
        self.assertEqual(agent_loop.validate(ok, "WATER"), [])


class Queue(Clean):
    """next_step is the one readiness predicate behind ready, status and run."""

    def test_astra_2_a_done_state_without_accepted_review_doesnt_release_dependents(self):
        core = done(work_package("WP1", "done", ["pass"], inspect="captures"), module="CORE")
        water = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["CORE:WP1"]))
        proj = {"CORE": entry_for(core), "WATER": entry_for(water)}
        self.assertEqual(agent_loop.next_step("CORE", proj)["status"], "ready_for_review")
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual((step["status"], step["depends_on"]), ("waiting", ["CORE:WP1"]))

    def test_astra_2_a_forged_done_without_a_record_acceptance_isnt_accepted(self):
        water = done(work_package("WP1", "not_started", ["open"]), work_package("WP2", "not_started", ["open"]))
        e = entry_for(water)
        water["work_packages"][0].update(status="done")  # written into the file, never accepted by the loop
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["work_package"], "WP1")

    def test_astra_2_and_fable_17_open_work_package_with_passing_items_is_still_next(self):
        water = done(work_package("WP1", "not_started", ["pass"]), work_package("WP2", "not_started", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water)})["work_package"], "WP1")
        water = done(work_package("WP1", "in_progress", ["pass"]), work_package("WP2", "not_started", ["open"]))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)})
        self.assertEqual((step["work_package"], step["status"]), ("WP1", "can_start"))

    def test_work_packages_run_in_file_order_not_in_progress_first(self):
        water = done(work_package("WP1", "done", ["pass"]), work_package("WP2", "not_started", ["open"]),
                     work_package("WP3", "in_progress", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water)})["work_package"], "WP2")

    def test_fable_8_dependencies_on_too_many_failed_reviews_and_cycles_are_reported_not_waited_on(self):
        prk = done(too_many("WP1", ["open"]), module="PRK")
        water = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["PRK:WP1"]))
        proj = {"PRK": entry_for(prk), "WATER": entry_for(water)}
        self.assertEqual(agent_loop.next_step("PRK", proj)["reason"], "too_many_failed_reviews")
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual(step["status"], "invalid")
        self.assertIn("Blocked: Too Many Failed Reviews", step["problems"][0])
        a = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["B:WP1"]), module="A")
        b = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["A:WP1"]), module="B")
        cycles = agent_loop.need_cycles({"A": entry_for(a), "B": entry_for(b)})
        self.assertEqual(set(cycles), {"A", "B"})

    def test_unplanned_module_is_waiting_and_missing_work_package_is_invalid(self):
        core = done(work_package("WP1", "not_started", ["open"]), module="CORE")
        water = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["PAY:WP1"]))
        proj = {"WATER": entry_for(water), "CORE": entry_for(core)}
        self.assertEqual(agent_loop.next_step("WATER", proj)["depends_on"], ["PAY:WP1 (not planned)"])
        water["work_packages"][0]["depends_on"] = ["CORE:WP7"]
        proj["WATER"] = entry_for(water)
        self.assertEqual(agent_loop.next_step("WATER", proj)["status"], "invalid")

    def test_work_packages_the_plan_names_without_items_are_planned_before_the_module_finishes(self):
        plan = ("# Water plan\n\n## Open for the user\n- Assumption: tides\n\n## WP1 Water flows: done\n[review](x)\n\n"
                "## WP2 Waves break on the shore\n\n## WP3 Boats float\n")
        self.assertEqual(agent_loop.later_work_packages(plan, {"WP1"}),
                         [{"id": "WP2", "name": "Waves break on the shore"}, {"id": "WP3", "name": "Boats float"}])
        water = done(work_package("WP1", "done", ["pass"]))
        water["work_packages"][0]["items"][0]["verdict"] = "pass"
        proj = {"WATER": dict(entry_for(water), later=agent_loop.later_work_packages(plan, {"WP1"}))}
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual((step["status"], step["reason"], step["later"]), ("waiting", "for_planning", ["WP2", "WP3"]))
        nxt = agent_loop.next_for(step, Path("/r"), {"plans": "docs/plans"}, proj)
        self.assertIn("Plan the next work packages of module WATER, up to WP3", nxt["command"])
        ships = done(dict(work_package("WP1", "not_started", ["open"]), depends_on=["WATER:WP3"]), module="SHIPS")
        proj["SHIPS"] = entry_for(ships)
        self.assertEqual(agent_loop.next_step("SHIPS", proj)["depends_on"], ["WATER:WP3 (not planned)"])
        self.assertIn("up to WP3", agent_loop.next_for(agent_loop.next_step("SHIPS", proj), Path("/r"),
                                                      {"plans": "docs/plans"}, proj)["command"])

    def test_a_new_stretch_waits_for_a_design_review_and_the_last_stretch_ending_keeps_its_review(self):
        water = done(work_package("WP1", "in_progress", ["open"]), work_package("WP2", "not_started", ["open"]))
        e = entry_for(water)
        e["record"]["design"]["items_owed"] = ["WP2"]
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["status"], "can_start")  # WP1 builds on
        water["work_packages"][0] = work_package("WP1", "done", ["pass"])
        e = entry_for(water)
        e["record"]["work_packages"]["WP1"]["done"] = {"by": "checks"}
        e["record"]["design"]["items_owed"] = ["WP2"]
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["status"], "design_not_approved")
        w1 = work_package("WP1", "in_progress", ["open"])
        self.assertFalse(agent_loop.needs_review(w1, water))
        self.assertTrue(agent_loop.needs_review(w1, water, {"ends_stretch": True}))

    def test_design_review_gates_a_module(self):
        water = done(work_package("WP1", "not_started", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water, design_ok=False)})["status"],
                         "design_not_approved")

    def test_blocked_and_taken(self):
        blocked = {"reason": "needs_hardware", "items": ["WP1.1"], "what": "needs the iPhone"}
        water = done(dict(work_package("WP1", "blocked", ["open"]), blocked=blocked))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)})
        self.assertEqual((step["status"], step["reason"], step["blocked"]), ("blocked", "needs_hardware", blocked))
        water["work_packages"][0]["blocked"] = "needs the iPhone"  # text from before 2.0 is for migrate to convert
        self.assertTrue(any("migrate" in p or "blocked" in p for p in agent_loop.validate(water, "WATER")))
        water = done(work_package("WP1", "not_started", ["open"]))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)}, {("WATER", "WP1"): "other"}, "me")
        self.assertEqual((step["status"], step["by"]), ("in_progress_elsewhere", "other"))

    def test_unauthorised_definitions_are_invalid(self):
        water = done(work_package("WP1", "not_started", ["open"]))
        e = entry_for(water)
        water["work_packages"][0]["items"][0]["check"] = "true # weakened"
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["status"], "invalid")


class Deltas(Clean):
    def setUp(self):
        self.before = done(work_package("WP1", "in_progress", ["open"]), work_package("WP2", "not_started", ["open"]))

    def after(self):
        return json.loads(json.dumps(self.before))

    def test_builder_may_change_only_its_fields_on_its_work_package(self):
        a = self.after()
        a["work_packages"][0]["status"] = "ready_for_review"
        a["work_packages"][0]["items"][0].update(builder_result="pass", evidence="log")
        self.assertEqual(agent_loop.delta_problems(self.before, a, "build", "WP1"), [])
        a["work_packages"][0]["diagnoses"] = 1
        self.assertTrue(agent_loop.delta_problems(self.before, a, "build", "WP1"))

    def test_astra_1_builder_forging_another_work_package_is_caught(self):
        a = self.after()
        a["work_packages"][1]["status"] = "done"
        a["work_packages"][1]["items"][0].update(verdict="pass", builder_result="pass")
        self.assertTrue(any("WP2" in p for p in agent_loop.delta_problems(self.before, a, "build", "WP1")))

    def test_rebased_upstream_changes_are_allowed(self):
        upstream = self.after()
        upstream["work_packages"][1]["quality_bar"] = "planner's new bar"
        a = json.loads(json.dumps(upstream))
        self.assertEqual(agent_loop.delta_problems(self.before, a, "build", "WP1", upstream), [])

    def test_astra_4_reviewer_deleting_a_work_package_is_caught(self):
        before = done(work_package("WP1", "ready_for_review", ["pass"]), work_package("WP2", "not_started", ["open"]))
        a = done(work_package("WP1", "done", ["pass"]))
        self.assertTrue(agent_loop.delta_problems(before, a, "review", "WP1"))

    def test_a_reviewer_cant_set_the_counts(self):
        before = done(work_package("WP1", "ready_for_review", ["pass"]))
        for field in ("failed_reviews", "failed_reviews_with_repeat", "diagnoses"):
            a = json.loads(json.dumps(before))
            a["work_packages"][0].update(status="in_progress", **{field: 2})
            self.assertTrue(agent_loop.delta_problems(before, a, "review", "WP1"), field)

    def test_planner_cant_grant_passes(self):
        a = self.after()
        a["work_packages"][1]["status"] = "done"
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
                "- **Codex generator:** gpt-6.2-sol, high\n- **Writable roots:** ~/.cargo, ~/.npm\n")
            p = agent_loop.profile(Path(tmp), strict=True)
            self.assertEqual((p["plans"], p["branch"], p["model"], p["effort"], p["evidence"], p["test_command"], p["sandbox"]),
                             ("docs/design/modules", "trunk", "gpt-6.2-sol", "high", "docs/my evidence",
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
                        "- **Codex generator:** gpt-6.2-sol turbo\n", "- **Merge:** pull-request\n- **Test command:** none\n"):
                Path(tmp, "ORCHESTRATE.md").write_text(good + bad if "Merge" not in bad else bad)
                with self.assertRaises(SystemExit, msg=bad):
                    agent_loop.profile(Path(tmp), strict=True)

    def test_profile_reads_hosts_models_and_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                "- **Claude model:** claude-opus-5-5\n- **Effort:** high\n- **Gemini model:** g-2\n"
                "- **Host gemini:** `gemini -p {prompt} -m {model} -e {effort}`\n- **Host bad:** gemini\n")
            with contextlib.redirect_stderr(io.StringIO()):
                p = agent_loop.profile(Path(tmp))
            self.assertEqual((p["models"]["codex"], p["models"]["claude"], p["models"]["gemini"], p["effort"]),
                             ("gpt-6.2-sol", "claude-opus-5-5", "g-2", "high"))
            self.assertEqual(p["hosts"], {"gemini": "gemini -p {prompt} -m {model} -e {effort}"})
            args, env = agent_loop.host_command("gemini", p, "g-2", "medium", Path(tmp), "do it now", None)
            self.assertEqual(args, ["gemini", "-p", "do it now", "-m", "g-2", "-e", "medium"])
            self.assertEqual(env["ORCHESTRATE_ROLE"], "build")
            with mock.patch.object(agent_loop, "claude_supports", lambda flag: True):
                new = agent_loop.host_command("claude", p, "m", "high", Path(tmp), "go", None, new_id="abc",
                                              title="thrum · WATER · WP1 build")[0]
                resumed = agent_loop.host_command("claude", p, "m", "high", Path(tmp), "go", "abc",
                                                  title="thrum · WATER · WP1 build")[0]
            self.assertEqual(new[new.index("--name") + 1], "thrum · WATER · WP1 build")
            self.assertNotIn("--name", resumed)  # a resumed session keeps the name it started with

    def test_a_host_line_needs_model_and_effort_placeholders_and_a_model(self):
        base = "- **Merge:** local\n- **Test command:** none\n"
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(base + "- **Host gemini:** gemini -p {prompt} -m {model}\n")
            with self.assertRaises(SystemExit) as stop, contextlib.redirect_stderr(io.StringIO()):
                agent_loop.profile(Path(tmp), strict=True)
            self.assertIn("{effort}", str(stop.exception))
            Path(tmp, "ORCHESTRATE.md").write_text(base + "- **Host gemini:** gemini -p {prompt} -m {model} -e {effort}\n")
            p = agent_loop.profile(Path(tmp), strict=True)
        ns = argparse.Namespace(host="gemini", model=None, effort=None)
        with self.assertRaises(SystemExit) as stop:
            agent_loop.resolve(ns, p, "build")
        self.assertIn("Gemini model", str(stop.exception), "a launch never leaves the model to the host's default")
        ns.model = "g-3"
        self.assertEqual(agent_loop.resolve(ns, p, "build"), ("gemini", "g-3", "medium"))

    def test_planner_host_sends_planners_to_that_host_unless_the_lead_names_one(self):
        base = "- **Merge:** local\n- **Test command:** none\n- **Default host:** codex\n"
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                base + "- **Planner host:** claude\n- **Claude planner:** claude-fable-5-2 high\n")
            p = agent_loop.profile(Path(tmp), strict=True)
        ns = lambda host=None: argparse.Namespace(host=host, model=None, effort=None)
        self.assertEqual(agent_loop.resolve(ns(), p, "plan"), ("claude", "claude-fable-5-2", "high"))
        self.assertEqual(agent_loop.resolve(ns(), p, "build")[0], "codex", "only planners move")
        self.assertEqual(agent_loop.resolve(ns("codex"), p, "plan"), ("codex", "gpt-6.2-sol", "high"))
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(base + "- **Planner host:** other\n")
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                agent_loop.profile(Path(tmp), strict=True)

    def test_profile_sets_model_and_effort_for_one_kind_of_agent(self):
        base = "- **Merge:** local\n- **Test command:** none\n"
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                base + "- **Claude model:** claude-opus-5-5\n- **Effort:** low\n"
                "- **Claude planner:** `claude-fable-5-2` xhigh  *(script)*\n- **Codex planner:** gpt-6.2-astra\n"
                "- **Codex reviewer:** high\n- **Claude design reviewer:** claude-fable-5-2\n"
                "- **Builder:** medium\n- **Claude builder:** <model>\n"
                "- **Host gemini:** gemini -p {prompt} -m {model} -e {effort}\n- **Gemini model:** g-3\n"
                "- **Gemini reviewer:** g-3-ultra, max\n")
            p = agent_loop.profile(Path(tmp), strict=True)
        json.dumps(p)  # the `profile` command prints the settings as JSON

        def launch(role, host, **flags):
            ns = argparse.Namespace(**{"host": host, "model": None, "effort": None, **flags})
            return agent_loop.resolve(ns, p, role)[1:]
        # a line with a host gives that host's model, effort or both; a planner's effort is high unless a line says
        self.assertEqual(launch("plan", "claude"), ("claude-fable-5-2", "xhigh"))
        self.assertEqual(launch("plan", "codex"), ("gpt-6.2-astra", "high"))
        self.assertEqual(launch("plan", "gemini"), ("g-3", "high"), "another host's model never crosses over")
        # a line with no host gives an effort on every host
        self.assertEqual(launch("build", "claude"), ("claude-opus-5-5", "medium"))
        self.assertEqual(launch("build", "codex"), ("gpt-6.2-sol", "medium"))
        # an effort alone keeps the host's model
        self.assertEqual(launch("review", "codex"), ("gpt-6.2-sol", "high"))
        self.assertEqual(launch("review", "claude"), ("claude-opus-5-5", "low"))
        self.assertEqual(launch("review", "gemini"), ("g-3-ultra", "max"))
        # a design review uses its own line, then the reviewer's
        self.assertEqual(launch("design", "claude"), ("claude-fable-5-2", "low"))
        self.assertEqual(launch("design", "codex"), ("gpt-6.2-sol", "high"))
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

    def test_the_status_page_finds_proposed_names_in_the_domain_language_format_and_the_old_one(self):
        text = ("### Hold\n\nA book kept for a patron.\n\n- **Proposed:** by a planner, 2026-11-22. Not yet agreed by "
                "the user.\n\n### Loan\n\nA book that has left the library.\n\n**Recall**\nAsks for a loan back.\n"
                "Proposed: by a builder, 2026-11-21.\n")
        self.assertEqual([n.split(" (")[0] for n in agent_loop.proposed_names(text)], ["Hold", "Recall"])

    def test_each_kind_of_planner_task_gives_its_instructions_with_links_that_work(self):
        for kind in agent_loop.PLAN_KINDS:
            text = agent_loop.kind_text(kind)
            self.assertTrue(text.startswith("# "), kind)
            for target in re.findall(r"\]\(([^)#]+)", text):
                self.assertTrue(target.startswith("http") or Path(target).exists(), f"{kind}: {target}")
        self.assertIn("# Planning a module", agent_loop.kind_text("project"))

    def test_a_plan_with_no_kind_plans_the_project_until_there_is_a_module_list(self):
        with tempfile.TemporaryDirectory() as d:
            tree, prof = Path(d), {"plans": "docs/plans"}
            self.assertEqual(agent_loop.default_kind(tree, prof), "project")
            path = tree / agent_loop.project_file(prof, "architecture")
            path.parent.mkdir(parents=True)
            path.write_text("| # | Module | What it's for | Needs |\n|---|---|---|---|\n| 1 | CORE | It works | |\n")
            self.assertEqual(agent_loop.default_kind(tree, prof), "module")

    def test_holistic_5_no_prompt_template_names_a_model_or_effort(self):
        values = dict(goal=agent_loop.GOAL_LINE, work_package="WP1", module="W", done="d", loop="l", skill="s", commit="c", glossary="g",
                      review="r", task="t", evidence="e", captures="r-captures", answers="", changed="", module_dir="m", graded="gr",
                      lead="", feedback="", needs="", rules="", resources="", session="", handoff="h", earlier="", checks="", kind="", kind_name="", scope="",
                      vision="b", architecture="a", plans="p")
        for name in ("BUILD_TEMPLATE", "REVIEW_TEMPLATE", "DESIGN_REVIEW_TEMPLATE", "PLAN_TEMPLATE",
                     "FINDINGS_TEMPLATE"):
            template = getattr(agent_loop, name)
            self.assertNotIn("{model}", template, name)
            self.assertNotIn("{effort}", template, name)
            text = template.format(**values).lower()
            for word in ("effort", "gpt-6", "opus", "launched on"):
                self.assertNotIn(word, text, f"{name} mentions {word}")
        self.assertTrue(agent_loop.BUILD_TEMPLATE.format(**values).startswith(agent_loop.GOAL_LINE + "Build work package WP1 of module W,"))

    def test_fable_16_prompts_carry_the_skill_path_for_hosts_without_skills(self):
        self.assertIn(str(SCRIPTS.parents[1] / "builder" / "SKILL.md"), agent_loop.skill_note("builder"))

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
                                                        "last_agent_message": "DONE: WP1 is claimed"}}]
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
                self.assertEqual(watch.message, "DONE: WP1 is claimed")

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
    def test_quota_costs_the_loops_work_packages_and_counts_other_threads_apart(self):
        import test_codex_quota as fixtures
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")  # WP1, in the fake host's thread t1
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
        self.assertEqual(own["t1"]["work_package"], "WP1")
        self.assertEqual(own["g"]["work_package"], "WP1")  # the auto-review served the builder
        self.assertNotIn("owner", own)
        acc = agent_loop.quota_report(self.wt, reading=reading)
        w1 = next(m for m in acc["work_packages"] if m["work_package"] == "WP1")
        self.assertTrue(w1["pct"][0] <= 20 <= w1["pct"][2], w1)
        self.assertEqual(acc["forecast"]["open_work_packages"], 1)
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
        self.assertIsNone(blind["open_work_packages"])
        self.assertIn("No work package forecast: no plans found", blind["verdict"])

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

    def test_an_idle_script_checkout_is_removed_and_one_in_use_is_kept(self):
        old = agent_loop.verify_tree(self.wt, "WATER", "origin/main")
        busy = agent_loop.verify_tree(self.wt, "SKY", "origin/main")
        for path in (old, busy):  # as if this process had exited after using them, two days ago
            agent_loop._TREE_HOLDS.pop(str(path)).close()
            stamp = time.time() - 2 * 86400
            os.utime(agent_loop.tree_marks(path)[1], (stamp, stamp))
        holder = subprocess.Popen([sys.executable, "-c", (
            "import fcntl, sys, time; h = open(sys.argv[1], 'a'); fcntl.flock(h, fcntl.LOCK_SH); "
            "print('held', flush=True); time.sleep(60)"), str(agent_loop.tree_marks(busy)[0])],
            stdout=subprocess.PIPE, text=True)
        self.addCleanup(holder.kill)
        self.assertEqual(holder.stdout.readline().strip(), "held")  # another live process is using SKY
        fresh = agent_loop.verify_tree(self.wt, "RAIN", "origin/main")
        self.assertFalse(old.exists())
        self.assertTrue((busy / ".git").exists())
        self.assertTrue((fresh / ".git").exists())
        self.assertNotIn(str(old), self.git("worktree", "list").stdout)
        again = agent_loop.verify_tree(self.wt, "WATER", "origin/main")  # made again when next needed
        self.assertEqual(agent_loop.head_commit(again), self.git("rev-parse", "origin/main").stdout.strip())
        # A checkout from an older version has no mark of the script's; a hand-cleared build folder makes its own
        # time fresh, so only the mark counts
        unmarked = agent_loop.verify_tree(self.wt, "SNOW", "origin/main")
        agent_loop._TREE_HOLDS.pop(str(unmarked)).close()
        agent_loop.tree_marks(unmarked)[1].unlink()
        (unmarked / "target").mkdir()
        shutil.rmtree(unmarked / "target")
        self.assertEqual(agent_loop.prune_idle_trees(self.wt), ["SNOW"])

    def ready_problems(self, w1, test_command="none", leave=None):
        """Why the script won't set WP1 to Ready for Review, once a builder has merged it as given. `leave` changes
        the worktree after the merge."""
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", test_command))
        self.write_done([proved(w1), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        prof = agent_loop.profile(self.wt, strict=True)
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        authorised = json.loads((self.wt / "docs/plans/WATER/RECORD.json").read_text())["work_packages"]["WP1"]
        if leave:
            leave()
        return "; ".join(agent_loop.ready_problems(self.wt, prof, "WATER", doc["work_packages"][0], doc,
                                                   authorised["definitions"], agent_loop.head_commit(self.wt))[0])

    def test_the_script_sets_ready_for_review_only_on_a_clean_merged_tree_whose_checks_pass(self):
        passed = lambda **proof: work_package("WP1", "in_progress", ["pass"], **proof)  # noqa: E731
        cases = [
            ("an uncommitted change", dict(leave=lambda: put(self.wt / "ORCHESTRATE.md", "changed")),
             "uncommitted"),
            ("an untracked file", dict(leave=lambda: (self.wt / "helper.sh").write_text("echo hi\n")), "untracked"),
            ("a check that leaves files", dict(), "left changes")]
        for name, kw, reason in cases:
            with self.subTest(name):
                self.setUp()
                w1 = passed(check="touch new-helper") if name == "a check that leaves files" else passed()
                self.assertIn(reason, self.ready_problems(w1, **kw))
        with self.subTest("all clear"):
            self.setUp()
            self.assertEqual(self.ready_problems(passed()), "")
        with self.subTest("the test command is the merge's to run, not run again here"):
            self.setUp()
            self.assertEqual(self.ready_problems(passed(), test_command="`sh -c 'exit 4'`"), "")

    def test_claims_check_only_work_package_and_accepts_it_in_the_record(self):
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
        record = self.read_record()["work_packages"]["WP1"]
        self.assertEqual(record["done"]["by"], "checks")
        claim = record["ready_for_review"]  # no rollout, so nothing observed
        self.assertEqual((claim["effort"], claim["observed"], claim["cli"], claim["path"]),
                         ("high", {}, "2.1.239 (Claude Code)", "headless"))
        self.assertEqual(self.ready()["can_start"][0]["work_package"], "WP2")
        agent_loop.sync_holds(self.wt, agent_loop.profile(self.wt, strict=True))
        self.assertNotIn(("WATER", "WP1"), agent_loop.holds(self.wt))  # the claim is released once accepted
        self.assertEqual(agent_loop.ledger_rows(self.wt)[0]["usage"], {"incomplete_turns": 1})
        self.assertIn("showed no tokens or only some",
                      agent_loop.cost_line(agent_loop.cost_of(agent_loop.ledger_rows(self.wt))["total"]))

    def test_astra_1_weakening_a_check_and_bumping_replans_is_invalid_and_stays_invalid(self):
        self.write_done([work_package("WP1", "not_started", ["open"], check="test -f real-proof"),
                         work_package("WP2", "not_started", ["open"])])
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

    def test_astra_1_forging_a_later_work_package_while_building_is_invalid(self):
        os.environ.update(FAKE_FORGE="1")
        result = self.run_loop()
        self.assertEqual(result["result"], "INVALID")
        self.assertTrue(any("WP2" in p for p in result["problems"]))

    def test_astra_2_work_package_flag_doesnt_skip_an_earlier_work_package(self):
        result = self.run_loop(work_package="WP2")
        self.assertEqual((result["result"], result["work_package"]), ("WAITING", "WP2"))
        self.assertFalse(self.log.exists())

    def test_astra_5_checks_run_on_the_integrated_tip_not_an_older_ancestor(self):
        self.write_done([work_package("WP1", "not_started", ["open"], check="test ! -f broken"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_UPSTREAM_BREAK="1")
        self.assertEqual(self.run_loop(no_progress_hours=0.0)["result"], "NO_PROGRESS_FOR_HOURS")
        self.assertIn("WP1.1 `test ! -f broken` exited 1", self.state()["not_ready_reasons"])

    def test_invalid_file_stops_before_any_turn(self):
        bare = work_package("WP1", "not_started", ["open"])
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

    def test_builder_done_on_reviewed_work_package_is_not_a_claim(self):
        os.environ.update(FAKE_STATE="done")
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="captures"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop(no_progress_hours=0.0)
        # the builder's done counts for nothing: the script checks the work and sets the state, so it still gets reviewed
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True), result)
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")

    def test_a_work_package_ready_for_review_holds_the_next_until_reviewed(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="captures"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        result = self.run_loop()
        self.assertEqual((result["result"], result["work_package"]), ("NEEDS_REVIEW", "WP1"))

    def test_design_owed_holds_the_module(self):
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        self.assertEqual(self.run_loop(no_design_review=True)["result"], "DESIGN_NOT_APPROVED")
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design")["verdict"], "DESIGN OK")
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")

    def test_a_design_review_runs_from_a_worktree_behind_the_plan(self):
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
        self.commit_all()  # a planner's merge
        behind = Path(self.enterContext(tempfile.TemporaryDirectory())) / "behind"
        self.git("worktree", "add", "-q", "--detach", str(behind), "HEAD~1")
        shutil.rmtree(behind / "docs/plans/WATER", ignore_errors=True)  # as before WATER was planned
        os.environ.update(FAKE_REVIEW="design")
        result = self.review("design", worktree=str(behind))
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(result.get("verdict"), "DESIGN OK", result)

    def test_a_plan_revised_before_its_design_review_is_authorised_by_that_review(self):
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        self.review("design")  # the record adopts the first definitions here
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.write_done([work_package("WP1", "not_started", ["open"], check="test -n revised")], authorise=False)
        self.evidence("WATER/design-review.md").unlink()  # the fake reviewer rewrites the same text
        self.commit_all()
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "INVALID")  # revised outside a planner turn
        os.environ.update(FAKE_REVIEW="design")
        second = self.review("design")
        self.assertEqual(second.get("verdict"), "DESIGN OK", second)
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["authorised"]["by"], "design review")

    def test_blocked_report_records_blocked_state_and_unblock_requeues(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device attached")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        w1 = self.read_done()["work_packages"][0]
        w1["blocked"].pop("work", None)
        self.assertEqual((w1["status"], w1["blocked"]), ("blocked", {"reason": "needs_context",
                                                                    "what": "no device attached"}))
        self.assertEqual(self.ready()["blocked"][0]["blocked"]["what"], "no device attached")
        # with no --work-package, unblock takes the module's one blocked work package, and says to run the module next
        unblocked = self.call(agent_loop.cmd_unblock, module="WATER", worktree=str(self.wt))
        self.assertEqual((unblocked["result"], unblocked["work_package"]), ("UNBLOCKED", "WP1"), unblocked)
        self.assertIn(" run --module WATER ", unblocked["next"]["command"])
        self.assertEqual(unblocked["next"]["argv"], shlex.split(unblocked["next"]["command"]))
        self.assertEqual(self.ready()["can_start"][0]["work_package"], "WP1")

    def test_items_that_need_someone_are_batched_into_the_blocked_reason(self):
        self.write_done([dict(work_package("WP1", "not_started", ["open"]), items=[
            item("WP1.1"), item("WP1.2", inspect="on the phone", needs=needs("hardware", "plug in the iPhone"))]),
            work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_REPLY="BLOCKED: the iPhone item needs a person")
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "needs_hardware"), result)
        self.assertEqual(self.read_done()["work_packages"][0]["blocked"]["items"], ["WP1.2"])
        self.assertTrue(result["next"]["command"].startswith("ORCHESTRATE_VISIBLE=1 "), result["next"])

    def test_a_headless_run_does_the_other_items_then_blocks_on_an_access_item(self):
        self.write_done([dict(work_package("WP1", "not_started", ["open"]), items=[
            item("WP1.1"), item("WP1.2", inspect="the app", needs=needs("access", "approve Computer Use for IINA"))]),
            work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_STATE="in_progress")
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "needs_access"), result)
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual([i["builder_result"] for i in w1["items"]], ["pass", "open"])
        self.assertEqual((w1["blocked"]["reason"], w1["blocked"]["items"]), ("needs_access", ["WP1.2"]))
        self.assertIn("approve Computer Use for IINA", w1["blocked"]["what"])
        self.assertEqual(len(self.calls()), 1)  # nobody is asked to confirm anything; the visible run is next
        self.assertTrue(result["next"]["command"].startswith("ORCHESTRATE_VISIBLE=1 "), result["next"])
        refused = self.refused_feedback("WP1", ["WP1.2"])  # access is done at the machine, so no reply is recorded
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
        self.assertEqual(result["blocked"]["handoff"], ".orchestrate/evidence/WATER/WP1-handoff.md")
        self.assertEqual(self.evidence("WATER/WP1-handoff.md").read_text(), "Tried the CORE save path; it isn't there.")
        self.git("fetch", "-q", "origin")
        self.assertNotIn("WP1-handoff.md", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)
        self.assertIn(".orchestrate/evidence/WATER/WP1-handoff.md", result["next"]["alternative"])
        self.assertIn(".orchestrate/evidence/WATER/WP1-handoff.md", result["next"]["why"])
        self.git("checkout", "-q", "--", ".")
        self.git("clean", "-qfd")
        os.environ.pop("FAKE_HANDOFF")
        os.environ.update(FAKE_REPLY="BLOCKED: still stuck")
        self.run_loop(fresh=True, message="CORE has the API now")
        self.assertIn("left a handoff at .orchestrate/evidence/WATER/WP1-handoff.md", self.prompt(self.calls()[-1]))

    def test_paused_goal_stops_before_dispatching_another_turn(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'paused')")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        self.assertEqual(len(self.calls()), 1)

    def set_goal(self, status):
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table if not exists thread_goals (thread_id text, status text)")
            conn.execute("delete from thread_goals")
            conn.execute("insert into thread_goals values ('t1', ?)", (status,))

    def test_a_headless_run_sets_a_paused_goal_active_again_and_resumes(self):
        """A block or `pause` leaves the goal paused; `run` again must resume the session, not report PAUSED."""
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working")
        self.set_goal("paused")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        with mock.patch.object(agent_loop, "codex_goal_activate",
                               lambda t, status="active": self.set_goal(status) or True):
            os.environ.update(FAKE_REPLY="NEEDS_CONTEXT: which device?")
            result = self.run_loop()
        self.assertEqual(result["result"], "BLOCKED", result)
        self.assertEqual(result["goal"], "paused")  # read when the run ended, after the block paused it
        self.assertEqual(len(self.calls()), 2)
        self.assertIn("resume", self.calls()[-1]["argv"])

    def test_a_goal_that_cant_be_set_active_again_gets_a_new_session(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="working")
        self.set_goal("paused")
        self.assertEqual(self.run_loop()["result"], "PAUSED")
        os.environ.update(FAKE_REPLY="NEEDS_CONTEXT: which device?", FAKE_THREAD="t2")
        self.addCleanup(os.environ.pop, "FAKE_THREAD")
        with mock.patch.object(agent_loop, "codex_goal_activate", lambda t, status="active": False):
            result = self.run_loop()
        self.assertEqual(result["result"], "BLOCKED", result)
        self.assertIn("couldn't be set active again", result["fresh_because"][0])
        self.assertNotIn("resume", self.calls()[-1]["argv"])

    def test_a_changed_pin_starts_a_fresh_session(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop()
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Codex generator:** gpt-6.2-sol high\n")
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
        claim = self.read_record()["work_packages"]["WP1"]["ready_for_review"]
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
        self.write_done([dict(work_package("WP1", "not_started", ["open"]), depends_on=["CORE:WP1"])])
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
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frame sequence"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()

    def claim(self):
        """WP1 Ready for Review, written as the script leaves it after its checks pass."""
        return self.ready_for_review()

    def test_a_passing_review_lands_and_accepts(self):
        result = self.run_loop()  # the one review test that starts from a builder's real turn
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True))
        commit = result["commit"]
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"]), ("REVIEWED", "PASS"))
        rec = self.read_record()["work_packages"]["WP1"]
        # the reviewer judged the script's commit that set Ready for Review, which follows the builder's work
        reviewed = rec["done"]["commit"]
        self.assertEqual(rec["done"]["by"], "review")
        self.assertEqual(self.git("merge-base", "--is-ancestor", commit, reviewed).returncode, 0)
        self.assertEqual(agent_loop.state_at(self.wt, reviewed, "docs/plans/WATER/DONE.json", "WP1"), "ready_for_review")
        self.assertEqual(self.ready()["can_start"][0]["work_package"], "WP2")

    def test_fable_3_a_failed_review_resets_the_items_that_failed(self):
        commit = self.run_loop()["commit"]  # a builder's real turn, whose session t1 the findings resume
        os.environ.update(FAKE_REVIEW="fail")
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"], result["failed_reviews_with_repeat"], result["failed_reviews"], result["escalation"]),
                         ("REVIEWED", "FAIL", 0, 1, "same_builder"))
        self.assertEqual(result["next"]["escalation"], "same_builder")
        self.assertIn(" run --module WATER ", result["next"]["command"])
        self.assertIn("--message", result["next"]["command"])
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["status"], w1["items"][0]["builder_result"], w1["items"][0]["evidence"]), ("in_progress", "open", ""))
        self.assertEqual(w1["items"][0]["verdict"], "fail")
        # The builder resumes its session with the findings, in its worktree.
        os.environ.pop("FAKE_REVIEW")
        self.run_loop(message="FINDINGS")
        last = self.calls()[-1]
        self.assertEqual(last["argv"][last["argv"].index("resume") + 1], "t1")
        self.assertIn("--add-dir", last["argv"][:last["argv"].index("resume")])
        self.assertTrue(last["argv"][-1].startswith("FINDINGS"), last["argv"][-1][:300])

    def test_the_script_blocks_a_work_package_that_keeps_failing_after_its_diagnosis(self):
        commit = self.ready_for_review(failed_before(dict(work_package("WP1", "not_started", ["open"], inspect="frames"),
                                                          failed_reviews_with_repeat=REPEATS - 1, diagnoses=1,
                                                          failed_reviews=REPEATS - 1)))
        os.environ.update(FAKE_REVIEW="fail")
        stuck = self.review(commit=commit)
        self.assertEqual((stuck["failed_reviews_with_repeat"], stuck["repeated"]), (REPEATS, ["the water is flat (WP1.1)"]))
        self.assertEqual((stuck["escalation"], stuck["next"]["escalation"], stuck["next"]["decides"]),
                         ("too_many_failed_reviews", "too_many_failed_reviews", "human"))
        self.assertIn(" human reopen --module WATER --work-package WP1 ", stuck["next"]["command"])
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["status"], w1["blocked"]["reason"]), ("blocked", "too_many_failed_reviews"))

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
        self.assertTrue(any("WP999" in p for p in result["problems"]))
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")

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
        result = self.human("accept", "WP1", reason="typo fix")
        self.assertEqual(result["result"], "DONE")
        accepted = self.read_record()["work_packages"]["WP1"]["done"]
        self.assertEqual((accepted["by"], accepted["words"]), ("human decision", "typo fix"))
        self.assertEqual(self.ready()["can_start"][0]["work_package"], "WP2")
        # Now a reviewed acceptance, then a re-review.
        self.human("rereview", "WP1")
        self.git("pull", "-q", "--rebase", "origin", "main")
        result = self.review(commit=self.read_record()["work_packages"]["WP1"]["ready_for_review"]["commit"])
        self.assertEqual(result["verdict"], "PASS")
        again = self.human("rereview", "WP1", reason="too lenient")
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")
        self.assertTrue(self.evidence("WATER/WP1-review-1.md").exists())
        self.assertTrue(again["commit"])

    def test_human_commands_are_refused_inside_a_loop_session(self):
        for verb in ("accept", "rereview", "reopen", "scope", "release", "feedback"):
            with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit) as stop:
                agent_loop.cmd_human(argparse.Namespace(action=verb, module="WATER", work_package="WP1", item=None,
                                                        text="yes", said="yes", asked="ok?", worktree=str(self.wt)))
            self.assertIn(f"human {verb} can't run inside a session the script started", str(stop.exception))

    def test_astra_1_a_record_edited_outside_the_loop_blocks_the_claim(self):
        start = agent_loop.head_commit(self.wt)
        rec = json.loads((self.wt / "docs/plans/WATER/RECORD.json").read_text())
        rec["work_packages"]["WP1"]["done"] = {"by": "review"}
        put(self.wt / "docs/plans/WATER/RECORD.json", json.dumps(rec))
        self.commit_all()
        prof = agent_loop.profile(self.wt, strict=True)
        self.assertEqual(len(agent_loop.record_tampering(self.wt, prof, start, agent_loop.head_commit(self.wt))), 1)


class HumanAndPlanner(Repo):
    def test_fable_7_human_scope_change_authorises_without_spending_the_diagnosis(self):
        d = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        d["work_packages"][0]["items"][0]["statement"] = "WP1.1 works, and faster"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(d))
        self.assertEqual(self.human("scope", "WP1")["result"], "DONE")
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["diagnoses"], w1["failed_reviews_with_repeat"], w1["items"][0]["statement"]), (0, 0, "WP1.1 works, and faster"))
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["authorised"]["by"], "human decision")
        self.git("checkout", "-q", "--", ".")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")

    def test_human_reopen(self):
        self.write_done([dict(too_many("WP1", ["open"]), failed_reviews_with_repeat=4), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "too_many_failed_reviews"), result)
        self.human("reopen", "WP1")
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["status"], w1["failed_reviews_with_repeat"], "blocked" in w1), ("in_progress", 0, False))

    def test_fable_9_a_planned_module_is_committed_landed_and_queued(self):
        result = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="plan PAY", host=None, model=None,
                           effort=None, turn_timeout_hours=0.1)
        self.assertEqual((result["result"], result["merged"]), ("PLANNED", True))
        self.assertEqual(result["design_review_owed"], ["PAY"])
        self.assertIn("features.multi_agent=false", self.calls()[0]["argv"])
        self.assertIn({"module": "PAY"}, self.ready()["design_not_approved"])
        rec = json.loads(self.git("show", "origin/main:docs/plans/PAY/RECORD.json").stdout)
        self.assertEqual(rec["work_packages"]["WP1"]["authorised"]["by"], "plan")

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

    def test_fable_4_two_leads_never_start_the_same_work_package(self):
        prof = agent_loop.profile(self.wt, strict=True)
        self.assertTrue(agent_loop.take_hold(self.wt, prof, "WATER", "WP1")[0])
        other = self.second_clone()
        ok, holder = agent_loop.take_hold(other, prof, "WATER", "WP1")
        self.assertFalse(ok)
        self.assertEqual(holder, agent_loop.me(self.wt))
        self.assertEqual(self.ready(other)["in_progress_elsewhere"][0]["work_package"], "WP1")
        self.assertEqual(self.run_loop(worktree=str(other))["result"], "IN_PROGRESS_ELSEWHERE")

    def test_fable_6_pause_signals_the_running_loop(self):
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER'); agent_loop.install_stop(); print('up', flush=True)\n"
                "while not agent_loop._STOP: time.sleep(0.05)\nprint('paused', flush=True)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.stdout.readline().strip(), "up")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            agent_loop.cmd_pause(argparse.Namespace(module=None, worktree=str(self.wt)))
        self.assertEqual(json.loads(out.getvalue())["paused"][0]["run"], "WATER")
        self.assertEqual(proc.stdout.readline().strip(), "paused")
        proc.wait(timeout=5)

    def test_astra_14_ready_fails_closed_when_the_tip_cant_be_fetched(self):
        self.git("remote", "set-url", "origin", str(self.root / "gone.git"))
        with self.assertRaises(SystemExit):
            self.ready()

    def test_fable_8_ready_names_cycles(self):
        self.write_done([dict(work_package("WP1", "not_started", ["open"]), depends_on=["CORE:WP1"])])
        self.write_done([dict(work_package("WP1", "not_started", ["open"]), depends_on=["WATER:WP1"])], module="CORE")
        self.commit_all()
        invalid = self.ready()["invalid"]
        self.assertEqual({i["module"] for i in invalid}, {"WATER", "CORE"})
        self.assertTrue(all("cycle" in i["problems"][-1] for i in invalid))

    def test_ready_and_project_status(self):
        put(self.wt / "docs/plans/CORE/DONE.json", json.dumps(done(work_package("WP1", "not_started", ["open"]),
                                                                            module="CORE")))
        self.commit_all()
        r = self.ready()
        self.assertEqual(r["can_start"][0]["work_package"], "WP1")
        self.assertEqual(r["design_not_approved"], [{"module": "CORE"}])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_status(argparse.Namespace(module=None, worktree=str(self.wt)))
        self.assertIn("CORE: design_not_approved", out.getvalue())
        self.assertIn("WATER: can_start (WP1)", out.getvalue())

    def test_ready_names_the_modules_to_plan_next(self):
        put(self.wt / "docs/plans/ARCHITECTURE.md", ARCH.replace(
            "| WATER |\n", "| WATER WP1 |\n| 3 | HARBOUR | Boats dock | modules 1 to 2 |\n"
                           "| 4 | GULLS | Birds | the user's call |\n| 5 | FISH | Fish swim | none |\n"
                           "| 6 | TIDE | Tides | WATER WP1; the user's port timing |\n"))
        self.commit_all()
        ahead = self.ready()["plan_ahead"]
        self.assertEqual([(a["module"], a["needs"]) for a in ahead], [("SHIPS", ["WATER"]), ("FISH", [])])
        self.assertIn("--task 'Plan module SHIPS. It needs: WATER WP1'", ahead[0]["next"]["command"])


    def test_planning_from_a_pick_waits_until_the_user_has_chosen(self):
        put(self.wt / "docs/plans/ARCHITECTURE.md", ARCH.replace("| WATER |\n", "| WATER |\n| 3 | FISH | Fish | WATER WP1 |\n"))
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water plan\n\n## WP1 Pick a sea\n\n## WP2 Waves break\n")
        pick = work_package("WP1", "not_started", ["open"])
        pick["items"][0]["needs"] = {"type": "human_feedback", "what": "pick one option"}
        self.write_done([pick])
        ships = work_package("WP1", "not_started", ["open"])
        ships["depends_on"] = ["WATER:WP1"]
        self.write_done([ships], module="SHIPS")
        self.commit_all()
        self.assertNotIn("plan_ahead", self.ready())  # WATER WP2, FISH and SHIPS WP1 are all written from the pick
        self.assertFalse(agent_loop.needs_review(pick, {"work_packages": [pick, {"id": "WP2"}]}, {"ends_stretch": True}),
                         "the user judged the pick, so no reviewer reads it")
        pick.update(status="done")
        pick["items"][0]["builder_result"] = "pass"
        self.write_done([pick])
        record = self.wt / "docs/plans/WATER/RECORD.json"
        rec = json.loads(record.read_text())
        rec["work_packages"]["WP1"]["done"] = {"by": "checks", "at": agent_loop.now()}
        record.write_text(json.dumps(rec))
        self.commit_all()
        ahead = {a["module"]: a["next"]["command"] for a in self.ready()["plan_ahead"]}
        self.assertEqual(sorted(ahead), ["FISH", "SHIPS", "WATER"])
        self.assertIn("--kind change", ahead["SHIPS"])
        self.assertIn("SHIPS WP1", ahead["SHIPS"])
        self.assertIn("References", ahead["WATER"])

    def test_ready_plans_a_modules_next_work_packages_while_its_last_planned_one_builds(self):
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water plan\n\n## WP1 Water flows\n\n## WP2 Waves break\n\n"
                                                  "## WP3 Boats float\n")
        self.commit_all()
        self.assertNotIn("plan_ahead", self.ready())  # WP1 and WP2 are both still to build
        self.write_done([work_package("WP1", "not_started", ["open"])])
        self.commit_all()
        ahead = self.ready()["plan_ahead"]
        self.assertEqual(ahead[0]["module"], "WATER")
        self.assertIn("next work packages of module WATER, up to WP3", ahead[0]["next"]["command"])


class Loops(Repo):
    """`loops` lists every live loop on the machine from the records loops keep, or from the process table for those
    that keep none; a dead loop never shows, and what it left is cleared. `status` names the modules with a live run."""


    def test_watch_warns_when_a_module_has_one_planned_work_package_left(self):
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water plan\n\n## WP1 Water flows\n\n## WP2 Waves break\n")
        self.write_done([work_package("WP1", "not_started", ["open"])])
        self.commit_all()
        prof = agent_loop.profile(self.wt)
        signs = agent_loop.watch_signs(agent_loop.watch_look(self.wt, prof, {}, fetch=False))
        self.assertIn("one planned work package", signs["plan_ahead WATER"]["text"])

    def test_an_items_check_is_told_it_runs_as_an_items_check(self):
        m = work_package("WP1", "in_progress", ["pass"])
        m["items"][0]["check"] = 'test "$ORCHESTRATE_ITEM_CHECK" = WP1.1'
        prof = agent_loop.profile(self.wt)
        self.assertEqual(agent_loop.check_failures(self.wt, prof, m), [])

    def test_a_broken_test_command_is_seen_from_every_worktree_until_a_merge_lands(self):
        broken = {"main_broken": {"commit": agent_loop.head_commit(self.wt), "exit": 1,
                                  "culprit": {"commit": "b" * 40, "subject": "sky: clouds", "modules": ["SKY"]}},
                  "next": {"command": None}, "at": 1.0}
        agent_loop.write_json(agent_loop.loop_dir(self.wt) / agent_loop.MAIN_BROKEN_FILE, broken)
        seen = agent_loop.main_broken(self.wt)
        self.assertEqual((seen[0]["check"], seen[0]["modules"]), ("test command", ["SKY"]))
        self.assertIn("no builder can merge", seen[0]["text"])
        look = agent_loop.watch_look(self.wt, agent_loop.profile(self.wt), {}, fetch=False)
        self.assertNotIn("ready_waiting", look["since"])  # only SKY can merge, so ready work isn't idle
        put(self.wt / "fix.txt", "a revert made by hand\n")
        self.commit_all()
        self.assertEqual(agent_loop.main_broken(self.wt), [], "a commit outside the plans may be the fix")

    def test_a_commit_with_no_plan_files_is_the_module_its_subject_names(self):
        put(self.wt / "src.txt", "code\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "water WP1: the river flows")
        prof = agent_loop.profile(self.wt)
        self.assertEqual(agent_loop.commit_modules(self.wt, prof, "HEAD")[0], ["WATER"])
        put(self.wt / "src.txt", "code 2\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "WATER fix round: the river again")
        self.assertEqual(agent_loop.commit_modules(self.wt, prof, "HEAD")[0], ["WATER"])

    def test_a_quiet_window_holds_other_work_back_until_it_ends(self):
        prof = agent_loop.profile(self.wt)
        agent_loop.quiet_wait(self.wt, prof, "WATER WP3")  # nothing else works, so the window starts at once
        claim = agent_loop.read_json_file(agent_loop.loop_dir(self.wt) / agent_loop.QUIET_FILE)
        self.assertEqual((claim["pid"], claim["work_package"]), (os.getpid(), "WATER WP3"))
        self.assertIsNone(agent_loop.quiet_claim(self.wt), "a process's own window doesn't hold it back")
        agent_loop.quiet_release(self.wt)
        other = subprocess.Popen(["sleep", "30"])
        self.addCleanup(lambda: other.poll() is None and (other.kill(), other.wait()))
        agent_loop.write_atomically(agent_loop.loop_dir(self.wt) / agent_loop.QUIET_FILE,
                                    {"pid": other.pid, "work_package": "SHIPS WP2"})
        waited = threading.Thread(target=agent_loop.quiet_wait, args=(self.wt, prof), kwargs={"what": "review"})
        with mock.patch.object(agent_loop, "SLOT_POLL_S", 0.05):
            waited.start()
            time.sleep(0.3)
            self.assertTrue(waited.is_alive(), "another process's window holds new work back")
            other.kill()
            other.wait()
            waited.join(5)
        self.assertFalse(waited.is_alive(), "a window whose process has gone holds nothing back")

    def test_a_landed_commit_is_the_module_whose_merge_landed_it(self):
        put(self.wt / "src.txt", "code\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "tidy the river")
        prof = agent_loop.profile(self.wt)
        self.assertEqual(agent_loop.commit_modules(self.wt, prof, "HEAD")[0], [])
        agent_loop.note_landed(self.wt, [agent_loop.head_commit(self.wt)], "WATER")
        self.assertEqual(agent_loop.commit_modules(self.wt, prof, "HEAD")[0], ["WATER"])

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
                "agent_loop.loop_register(wt, 'build', module='WATER', work_package='WP1', host='codex', model='m', "
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
        self.assertEqual(steps, ["builder turn 1", "checking WP1: WP1.1", "merging the Ready for Review record"])
        during = json.loads(seen.read_text().splitlines()[0])["runs"]
        self.assertEqual(len(during), 1, during)
        v = during[0]
        self.assertEqual(v["step"], "builder turn 1")
        self.assertIn("now: builder turn 1", agent_loop.loop_line(v))
        self.assertEqual((v["role"], v["module"], v["work_package"], v["host"], v["model"], v["effort"], v["path"]),
                         ("build", "WATER", "WP1", "codex", agent_loop.DEFAULT_MODEL, "medium", "headless"))
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
        agent_loop.loop_register(self.wt, "build", module="WATER", work_package="WP1")
        for _ in range(2):
            agent_loop.run_turn("codex", prof, "m", "medium", self.wt, "go", None, 30)
        rec = json.loads((self.loops / f"{os.getpid()}.json").read_text())
        self.assertEqual((rec["turns"], rec["session"], rec["path"]), (2, "t1", "headless"))
        self.assertEqual(rec["usage"], {"input": 120, "cached": 80, "output": 14, "turns": 2})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_loops(argparse.Namespace(repo=str(self.wt), json=False))
        self.assertIn("WATER WP1  build  codex m medium, headless", out.getvalue())
        self.assertIn("2 turns", out.getvalue())
        self.assertIn("tokens 120 in, 80 cached, 14 out", out.getvalue())

    def test_a_dead_loop_never_shows_and_what_it_left_is_cleared(self):
        proc = self.holder()
        try:
            self.assertEqual([(r["pid"], r["registered"]) for r in self.listed()], [(proc.pid, True)])
            self.assertIn("WATER: can_start (WP1); running: build WP1 codex, pid", self.status())
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
            state.write_text(json.dumps({"work_package": "WP2", "path": "visible"}))
            # its run state, written after it started: ps gives the start in whole seconds
            os.utime(state, (time.time() + 2, time.time() + 2))
            found = [r for r in self.listed() if r["pid"] == proc.pid]
            self.assertEqual(len(found), 1, self.listed())
            v = agent_loop.loop_view(found[0])
            self.assertEqual((v["role"], v["module"], v["work_package"], v["host"], v["path"], v["registered"]),
                             ("build", "WATER", "WP2", "claude", "visible", False))
            self.assertEqual(v["script"], str(script))
        finally:
            proc.kill()
            proc.wait(timeout=5)
        self.assertEqual([r for r in self.listed() if r["pid"] == proc.pid], [])


class Guidance(Repo):
    """The four things a lead had to work out by hand before a work package could run: plans left uncommitted, a
    sandbox refusing writes under .git, an owed design review, and what to run after any stop short of building."""

    def plan_core(self):
        put(self.wt / "docs/plans/CORE/DONE.json", json.dumps(done(work_package("WP1", "not_started", ["open"]),
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
        forged = work_package("WP1", "done", ["pass"])
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(done(forged, work_package("WP2", "not_started", ["open"]))))
        put(self.wt / "docs/plans/WATER/RECORD.json", "{}")
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
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertEqual([c["role"] for c in self.calls()], ["review", "build"])
        self.assertEqual(self.read_record()["design"]["verdict"], "ok")

    def test_fix3_any_other_design_verdict_stops_the_run_and_says_what_next(self):
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        result = self.run_loop()
        self.assertEqual(result["result"], "DESIGN_NOT_APPROVED")
        self.assertEqual(result["design_review"]["verdict"], "DESIGN CHANGES")
        self.assertIn(" plan --worktree ", result["next"]["command"])
        self.assertEqual([c["role"] for c in self.calls()], ["review"])

    def test_fix3_no_design_review_opts_out(self):
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
        self.commit_all()
        result = self.run_loop(no_design_review=True)
        self.assertEqual(result["result"], "DESIGN_NOT_APPROVED")
        self.assertIn(" review --module WATER --work-package design ", result["next"]["command"])
        self.assertFalse(self.log.exists())

    # 4. The next command

    def test_fix4_waiting_follows_the_need_to_the_command_that_moves_it(self):
        self.write_done([dict(work_package("WP1", "not_started", ["open"]), depends_on=["CORE:WP1"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual(result["result"], "WAITING")
        self.assertIn(" plan --worktree ", result["next"]["command"])
        self.assertIn("Plan module CORE", result["next"]["command"])
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False, module="CORE")
        self.commit_all()
        result = self.run_loop()
        self.assertIn(" review --module CORE --work-package design ", result["next"]["command"])
        r = self.ready()  # nothing ready: the lead still gets a command
        self.assertEqual(r["can_start"], [])
        self.assertIn(" review --module CORE --work-package design ", r["next"]["command"])

    def test_fix4_review_blocked_invalid_and_floor_carry_the_next_command(self):
        self.write_done([work_package("WP1", "ready_for_review", ["pass"], inspect="captures"), work_package("WP2", "not_started", ["open"])],
                        ready=["WP1"])
        self.commit_all()
        owed = self.run_loop()
        self.assertEqual(owed["result"], "NEEDS_REVIEW")
        self.assertIn(" review --module WATER --work-package WP1 --commit ", owed["next"]["command"])
        self.write_done([work_package("WP1", "not_started", ["open"]), work_package("WP2", "not_started", ["open"])])
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
        self.call(agent_loop.cmd_unblock, module="WATER", work_package="WP1", worktree=str(self.wt))
        floor = self.run_loop()
        self.assertEqual(floor["result"], "HOST_FAILED")
        self.assertIn("--host claude", floor["next"]["alternative"])
        put(self.wt / "docs/plans/WATER/DONE.json", "{not json")
        self.commit_all()
        invalid = self.run_loop()
        self.assertEqual(invalid["result"], "INVALID")
        self.assertIn(" plan --worktree ", invalid["next"]["command"])

    def test_fix4_human_decisions_are_commands_for_the_human_never_run(self):
        self.write_done([too_many("WP1", ["open"], inspect="captures"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["reason"]), ("BLOCKED", "too_many_failed_reviews"), result)
        self.assertEqual(result["next"]["decides"], "human")
        self.assertIn(" human reopen --module WATER --work-package WP1 ", result["next"]["command"])
        self.write_done([work_package("WP1", "done", ["pass"], inspect="captures"), work_package("WP2", "not_started", ["open"])],
                        authorise=False)  # done in the file, never accepted by the loop
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["next"]["decides"]), ("NEEDS_REVIEW", "human"))
        self.assertIn(" human accept ", result["next"]["command"])
        self.assertFalse(self.log.exists())
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "done")
        self.assertNotIn("done", self.read_record()["work_packages"]["WP1"])

    def test_fix4_taken_points_at_other_work(self):
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.assertTrue(agent_loop.take_hold(other, prof, "WATER", "WP1")[0])
        result = self.run_loop()
        self.assertEqual(result["result"], "IN_PROGRESS_ELSEWHERE")
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
        self.assertIn(f" review --module WATER --work-package WP1 --commit {self.commit} ", then["command"])
        self.assertIn("no review was counted", then["why"])
        self.assertIn("Are you there now?", then["ask"])
        self.assertEqual(self.tip(), before)  # nothing merged, so no round and no review file
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["status"], w1.get("failed_reviews", 0), w1["failed_reviews_with_repeat"]), ("ready_for_review", 0, 0))
        self.assertFalse(self.read_record()["work_packages"]["WP1"].get("reviews"))
        # the same review, once the user is at the machine, judges it as usual
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
    """Release 5 of the 2026-11-12 improvement plan: what the lead and the user see (N5, L5, N8, F3, P5 and the
    smaller issues)."""

    def builders_line(self, line):
        (self.wt / "ORCHESTRATE.md").write_text(BASE_PROFILE + f"- **Builders:** {line}\n")
        self.commit_all()

    def test_run_starts_no_builder_until_the_user_has_said_how_the_agents_work(self):
        # The planner leaves the Builders line out; the lead asks the user before the first build.
        (self.wt / "ORCHESTRATE.md").write_text(BASE_PROFILE)
        self.commit_all()
        refused = self.run_loop()
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("no Builders line", refused["problems"][0])
        self.assertEqual(refused["next"]["decides"], "human")
        self.assertIn("Before the first build", refused["next"]["ask"])

    def test_run_refuses_a_builder_past_the_users_most_and_past_the_leads_working_number(self):
        self.builders_line("one Codex builder")
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'CORE')\n"
                "agent_loop.loop_register(wt, 'build', module='CORE', work_package='WP4', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        other = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(other.stdout.readline().strip(), "up")
            refused = self.run_loop()
            self.assertEqual(refused["result"], "REFUSED", refused)
            self.assertEqual(refused["running"], [{"module": "CORE", "work_package": "WP4", "pid": other.pid}])
            self.assertIn("the most the project settings' Builders line allows", refused["problems"][0])
            self.assertEqual(refused["next"]["decides"], "human")
            self.assertIn(" settings ", refused["next"]["command"])
            self.assertIn("Builders", refused["next"]["command"])
            self.assertEqual(self.calls() if self.log.exists() else [], [])  # no builder started
            self.builders_line("three Codex builders")
            self.call(agent_loop.cmd_builders, worktree=str(self.wt), set=1, why="the machine is loaded")
            refused = self.run_loop()  # the lead's own number holds it now, and is the lead's to raise
            self.assertEqual(refused["result"], "REFUSED", refused)
            self.assertIn("the working number you set with `builders`", refused["problems"][0])
            self.assertNotEqual(refused["next"].get("decides"), "human")
            self.assertIn(" builders ", refused["next"]["command"])
            self.assertIn("--set 2", refused["next"]["command"])
            self.call(agent_loop.cmd_builders, worktree=str(self.wt), clear=True)
            self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")
        finally:
            other.kill()
            other.wait()

    def test_builders_sets_the_working_number_within_the_users_most(self):
        self.builders_line("three Codex builders")
        prof = agent_loop.profile(self.wt)
        self.assertEqual((prof["builders"], prof["builders_set"], agent_loop.builder_limit(self.wt, prof)),
                         (3, True, 3))
        refused = self.call(agent_loop.cmd_builders, worktree=str(self.wt), set=2)
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("--why", refused["problems"][0])
        got = self.call(agent_loop.cmd_builders, worktree=str(self.wt), set=2, why="the GPU is shared")
        self.assertEqual((got["result"], got["most"], got["working"]["count"], got["limit"], got["changed"]),
                         ("BUILDERS", 3, 2, 2, "set"), got)
        got = self.call(agent_loop.cmd_builders, worktree=str(self.wt), set=5, why="the machine has room")
        self.assertEqual(got["limit"], 3)  # the user's most caps it
        self.assertIn("capped", got)
        got = self.call(agent_loop.cmd_builders, worktree=str(self.wt), clear=True)
        self.assertEqual((got["working"], got["limit"], got["changed"]), (None, 3, "cleared"))
        self.builders_line("Codex, no limit")
        prof = agent_loop.profile(self.wt)
        self.assertEqual((prof["builders"], prof["builders_set"], agent_loop.builder_limit(self.wt, prof)),
                         (None, True, None))

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
        self.assertEqual(sorted(first["changed"]), ["2.10.0", "2.10.1", "2.11.0", "2.11.1", "2.11.2", "2.11.3", "2.11.4", "2.12.0", "2.12.1", "2.12.2", "2.12.3", "2.12.4", "2.13.0", "2.14.0", "2.5.0", "2.6.0", "2.7.0", "2.7.1", "2.8.0", "2.9.0", "3.0.0", "3.0.1", "3.0.2", "3.0.3"])
        self.assertIn("From before 2.6.0", first["changed"]["2.5.0"][0])
        self.assertNotIn("changed", second)
        note.write_text('{"version": "2.0.0"}')
        self.assertIn("2.5.0", agent_loop.version_change(self.wt))
        note.write_text('{"version": "2.5.0"}')
        self.assertEqual(sorted(agent_loop.version_change(self.wt)), ["2.10.0", "2.10.1", "2.11.0", "2.11.1", "2.11.2", "2.11.3", "2.11.4", "2.12.0", "2.12.1", "2.12.2", "2.12.3", "2.12.4", "2.13.0", "2.14.0", "2.6.0", "2.7.0", "2.7.1", "2.8.0", "2.9.0", "3.0.0", "3.0.1", "3.0.2", "3.0.3"])
        note.write_text('{"version": "2.9.0"}')
        (line, *_) = agent_loop.version_change(self.wt)["2.10.0"]
        self.assertIn("Read the lead skill again", line)

    def test_a_blocked_message_gives_paths_in_the_repository_and_names_who_acts(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY=f"BLOCKED: the seam shows in {self.wt}/.orchestrate/evidence/WATER/f.png "
                                                    "and I don't know which constant sets it")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
        what = self.read_done()["work_packages"][0]["blocked"]["what"]
        self.assertEqual(what, "the seam shows in .orchestrate/evidence/WATER/f.png and I don't know which constant sets it")
        self.assertIn("Answer it with `run --message`", blocked["next"]["why"])
        self.git("fetch", "-q", "origin")
        page = agent_loop.status_page(self.wt, agent_loop.profile(self.wt), "origin/main")
        now_next = page.split("### Now and next")[1].split("###")[0]
        self.assertIn("Blocked: Needs Context: the seam shows in .orchestrate/evidence/WATER/f.png", now_next)
        self.assertIn("The lead finds the missing fact, or asks you for it", now_next)
        self.assertNotIn(str(self.wt), page)


class WhatTheLeadSeesAlone(ProfileOnly):
    """Tests from WhatTheLeadSees that need no repository, only the project settings."""

    def test_runs_prints_the_step_a_review_is_on_and_the_tool_call_it_waits_on(self):
        # a build's step, seen live during its turn, is checked in Loops
        rec = {"pid": 1, "role": "review", "module": "WATER", "work_package": "WP1", "host": "claude", "turns": 0,
               "started_at": time.time() - 600, "activity_at": time.time() - 500, "turn_started_at": time.time() - 590,
               "usage": {}, "registered": True, "worktree": str(self.wt), "step": "reviewer turn 1",
               "open_tool_call": {"name": "mcp__computer-use__screenshot", "opened_at": time.time() - 480}}
        line = agent_loop.loop_line(agent_loop.loop_view(rec))
        self.assertIn("now: reviewer turn 1, waiting on the tool call mcp__computer-use__screenshot for 8m", line)

    def test_profile_reads_the_builders_count_as_a_digit_or_a_word(self):
        for line, count in (("two Codex builders", 2), ("3 on Codex, one on Claude", 4), ("usually one", 1),
                            ("as many as can start", None), ("<how many builders>", None)):
            (self.wt / "ORCHESTRATE.md").write_text(BASE_PROFILE + f"- **Builders:** {line}\n")
            self.assertEqual(agent_loop.profile(self.wt)["builders"], count, line)
        (self.wt / "ORCHESTRATE.md").write_text(BASE_PROFILE)
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
                                str(self.wt), "--one-step"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, env=env)
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

    def test_a_push_rejected_every_time_fails_and_says_so(self):
        self.commit("mine.txt", "mine")
        self.reject_pushes(agent_loop.LAND_TRIES)
        ok, detail = agent_loop.land(self.wt, agent_loop.profile(self.wt, strict=True))
        self.assertFalse(ok)
        self.assertIn("push rejected", detail)
        self.assertIn("pre-receive hook declined", detail)
        self.assertEqual((self.origin / "rejected").read_text().strip(), str(agent_loop.LAND_TRIES))  # no more

    def test_a_record_lands_while_a_builder_merge_holds_the_merge_lock(self):
        self.commit("docs/plans/WATER/STATUS.md", "unblocked\n")
        done = []
        with agent_loop.held("merge", self.wt):  # a builder's merge, running its test command
            t = threading.Thread(target=lambda: done.append(agent_loop.land(self.wt, agent_loop.profile(self.wt))))
            t.start()
            t.join(30)
            self.assertTrue(done, "the record waited for the merge lock")
        self.assertTrue(done[0][0], done[0])

    def test_a_builder_merge_that_loses_its_push_to_a_record_lands_without_testing_again(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        for key, value in (("user.name", "t"), ("user.email", "t@t")):
            self.git("config", key, value, where=other)
        count = self.root / "runs"
        script = self.root / "test.sh"
        script.write_text(  # the first run lands a record from elsewhere while the builder's test runs
            f'echo run >> "{count}"\n'
            f'if [ "$(wc -l < "{count}")" -eq 1 ]; then\n'
            f'  cd "{other}" && git pull -q origin main && mkdir -p docs/plans && echo blocked > docs/plans/STATUS.md && git add -A && '
            f'git commit -qm record && git push -q origin main\nfi\n')
        self.commit("ORCHESTRATE.md", PROFILE.replace("**Test command:** none", f"**Test command:** sh {script}"))
        self.git("push", "-q", "origin", "HEAD:main")
        mine = self.commit("water.txt", "built\n")
        ok, landed = agent_loop.land(self.wt, agent_loop.profile(self.wt, strict=True), check=True)
        self.assertTrue(ok, landed)
        self.assertEqual(count.read_text().count("run"), 1)  # the pass was reused over the record
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("rev-parse", "origin/main").stdout.strip(), landed)
        self.assertNotEqual(landed, mine)  # rebased onto the record
        self.assertEqual(self.git("show", f"{landed}:docs/plans/STATUS.md").stdout, "blocked\n")

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

    def test_a_local_merge_rebases_over_a_record_that_landed_during_its_test(self):
        count = self.root / "runs"
        script = self.root / "test.sh"
        script.write_text(
            f'echo run >> "{count}"\n'
            f'if [ "$(wc -l < "{count}")" -eq 1 ]; then\n'
            f'  cd "{self.wt}" && mkdir -p docs/plans && echo blocked > docs/plans/STATUS.md && git add -A && '
            f'git commit -qm record\nfi\n')
        self.commit("ORCHESTRATE.md", PROFILE.replace("push", "local").replace(
            "**Test command:** none", f"**Test command:** sh {script}"))
        build = self.root / "build"
        self.git("worktree", "add", "-q", "-b", "build/x", str(build), "main")
        self.commit("water.txt", "built\n", where=build)
        ok, landed = agent_loop.land(build, agent_loop.profile(build, strict=True), check=True)
        self.assertTrue(ok, landed)
        self.assertEqual(agent_loop.head_commit(self.wt), landed)
        self.assertEqual(((self.wt / "water.txt").read_text(), (self.wt / "docs/plans/STATUS.md").read_text()),
                         ("built\n", "blocked\n"))  # neither the record nor the build was lost
        self.assertEqual(count.read_text().count("run"), 1)

    def test_a_local_main_branch_that_cant_fast_forward_is_left_as_it_was(self):
        before = self.commit("ORCHESTRATE.md", PROFILE.replace("push", "local"))
        build = self.root / "build"
        self.git("worktree", "add", "-q", "-b", "build/x", str(build), "main")
        self.commit("water.txt", "built\n", where=build)
        (self.wt / "water.txt").write_text("the user's edit, not committed\n")  # main, checked out here, is dirty
        ok, detail = agent_loop.land(build, agent_loop.profile(build, strict=True))
        self.assertFalse(ok)
        self.assertIn(f"couldn't fast-forward main in {self.wt.resolve()}", detail)
        self.assertEqual(agent_loop.head_commit(self.wt), before)
        self.assertEqual((self.wt / "water.txt").read_text(), "the user's edit, not committed\n")


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
        if self.behaviour == "never" or (self.behaviour == "late" and self.ignored_wakes < 3) or \
                (self.behaviour == "hung_call_held" and self.interrupts):  # the app holds the resume, as in Thrum
            self.ignored_wakes += 1
            return
        text = self.queued.pop(t, None)
        if text is None:
            return
        info, turn = self.threads[t], f"turn-{len(self.links)}"
        self.write(t, {"type": "event_msg", "payload": {"type": "task_started", "turn_id": turn}},
                   {"type": "turn_context", "payload": {"turn_id": turn, "model": info["model"],
                                                        "effort": self.effort_seen or info["effort"]}})
        if self.behaviour == "hang" or (self.behaviour.startswith("hung_call") and not self.interrupts):
            info["running"] = turn
            if self.behaviour.startswith("hung_call"):  # a Computer Use call that never answers, as in Thrum
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


def pause_once_a_turn_is_running(app) -> None:
    """Sets the script's stop flag, as `pause` does, once the fake app has a turn running. A fixed delay raced the
    loop's start-up on a busy machine."""
    def wait_then_stop():
        deadline = time.time() + 30
        while time.time() < deadline and not any(t.get("running") for t in app.threads.values()):
            time.sleep(0.01)
        agent_loop._STOP = True
    threading.Thread(target=wait_then_stop, daemon=True).start()


class VisibleCodex(Repo):
    """Decision 8: the loop's Codex sessions are threads the Codex app lists and runs."""

    def test_decision_8_a_build_runs_in_a_thread_the_app_shows_and_the_loop_still_claims(self):
        with FakeCodexApp(self).installed() as app:
            result = self.run_loop()
        self.assertEqual((result["result"], result["path"], result["app_settings"]),
                         ("READY_FOR_REVIEW", "visible", "gpt-6.2-sol medium"))
        (t, info), = app.threads.items()
        self.assertEqual((info["model"], info["effort"], info["role"], info["title"], info["cwd"]),
                         ("gpt-6.2-sol", "medium", "build", agent_loop.session_title(self.wt, "WATER", "WP1 build"),
                          self.wt.resolve()))
        self.assertIn(f"codex://threads/wake/{t}", app.links)
        self.assertEqual((self.state()["thread"], self.state()["path"]), (t, "visible"))
        self.assertTrue(self.calls(), "the app ran the turn")
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["done"]["by"], "checks")

    def test_decision_8_a_resumed_turn_goes_to_the_same_thread_with_the_message(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        with FakeCodexApp(self).installed() as app:
            blocked = self.run_loop()
            self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
            self.run_loop(message="Use the simulator.")
        self.assertEqual(len(app.threads), 1)
        self.assertIn('the paragraph that starts "Finish the work package" as the objective, word for word', app.sent[0])
        self.assertTrue(app.sent[0].startswith(agent_loop.GOAL_LINE + "Build work package WP1 of module WATER,"))
        self.assertNotIn("gpt-6.2-sol", app.sent[0])
        self.assertTrue(app.sent[-1].startswith("Use the simulator.\n\nEvery item of WP1 has to pass with evidence"))

    def test_decision_8_a_turn_on_another_effort_in_the_app_is_PIN(self):
        with FakeCodexApp(self, effort_seen="xhigh").installed():
            result = self.run_loop()
        self.assertEqual(result["result"], "WRONG_MODEL_OR_EFFORT")
        self.assertIn("gpt-6.2-sol/xhigh", result["mismatches"][0])

    def test_a_wrong_model_reruns_as_set_and_asks_the_user_only_when_it_repeats(self):
        os.environ.update(FAKE_PASS="0")  # the work package stays open, so the rerun takes a turn of its own
        with FakeCodexApp(self, effort_seen="xhigh").installed():
            first = self.run_loop()
            second = self.run_loop()
        self.assertEqual((first["result"], second["result"]), ("WRONG_MODEL_OR_EFFORT", "WRONG_MODEL_OR_EFFORT"))
        self.assertNotIn("decides", first["next"], "a rerun as set is the lead's call")
        self.assertIn("mention it to the user", first["next"]["why"])
        self.assertEqual(second["next"]["decides"], "human", "the same mismatch twice needs the user")
        self.assertIn("twice", second["next"]["ask"])

    def test_decision_8_the_human_pressing_stop_in_the_app_is_PAUSED_not_a_failure(self):
        with FakeCodexApp(self, behaviour="owner_stop").installed() as app:
            result = self.run_loop()
        self.assertEqual(result["result"], "PAUSED")
        self.assertIn("stopped in the Codex app", result["reason"])
        self.assertEqual(app.interrupts, [])

    def test_decision_8_pause_stops_the_turn_running_in_the_app(self):
        with FakeCodexApp(self, behaviour="hang").installed() as app:
            pause_once_a_turn_is_running(app)
            result = self.run_loop()
        self.assertEqual(result["result"], "PAUSED")
        self.assertEqual(len(app.interrupts), 1)
        self.assertNotIn("turn_not_stopped", result)

    def test_a_pause_the_app_doesnt_take_names_the_thread_whose_turn_may_still_be_running(self):
        with FakeCodexApp(self, behaviour="hang").installed() as app, \
                mock.patch.object(agent_loop, "codex_interrupt", lambda thread: False):
            pause_once_a_turn_is_running(app)
            result = self.run_loop()
        self.assertEqual(result["result"], "PAUSED")
        (thread,) = app.threads
        self.assertIn(f"the Codex app didn't take the stop for thread {thread}", result["turn_not_stopped"])

    def test_a_stop_refused_because_the_window_left_the_thread_opens_it_and_is_sent_again(self):
        asked, links = [], []

        def request(thread):  # the app stops a thread only while one of its windows holds it
            asked.append(thread)
            return "" if links else "RuntimeError: thread-follower-interrupt-turn: no-client-found"
        with mock.patch.object(agent_loop, "codex_interrupt_request", request), \
                mock.patch.object(agent_loop, "open_link", lambda url: links.append(url) or True), \
                mock.patch.object(agent_loop, "codex_owner", lambda thread: {} if links else None), \
                mock.patch.object(agent_loop, "POLL_S", 0.0):
            self.assertTrue(agent_loop.codex_interrupt("t1"))
        self.assertEqual((asked, links), (["t1", "t1"], ["codex://threads/t1"]))

    def test_a_stop_gives_up_when_no_window_takes_the_thread_and_opens_nothing_for_another_failure(self):
        links = []
        with mock.patch.object(agent_loop, "open_link", lambda url: links.append(url) or True), \
                mock.patch.object(agent_loop, "codex_owner", lambda thread: None), \
                mock.patch.object(agent_loop, "POLL_S", 0.0), mock.patch.object(agent_loop, "REOPEN_TRIES", 3):
            with mock.patch.object(agent_loop, "codex_interrupt_request",
                                   lambda thread: "RuntimeError: thread-follower-interrupt-turn: no-client-found"):
                self.assertFalse(agent_loop.codex_interrupt("t1"))
            self.assertEqual(links, ["codex://threads/t1"])
            with mock.patch.object(agent_loop, "codex_interrupt_request", lambda thread: "OSError: no socket"):
                self.assertFalse(agent_loop.codex_interrupt("t2"))  # the app isn't running, so no turn is either
            self.assertEqual(links, ["codex://threads/t1"])

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
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        with FakeCodexApp(self).installed() as app:
            commit = self.run_loop()["commit"]
            result = self.review(commit=commit, effort="high")
        self.assertEqual((result["result"], result["verdict"], result["path"]), ("REVIEWED", "PASS", "visible"))
        review = [i for i in app.threads.values() if i["role"] == "review"][0]
        self.assertEqual((review["title"], review["effort"]), (agent_loop.session_title(self.wt, "WATER", "WP1 review"), "high"))
        self.assertIn("orchestrate/verify", str(review["cwd"]))

    def test_decision_8_a_turn_the_app_starts_late_is_waited_for_not_given_up_on(self):
        steps, note = [], agent_loop.loop_note
        with FakeCodexApp(self, behaviour="late").installed() as app, mock.patch.object(
                agent_loop, "loop_note", lambda **f: (steps.append(f["step"]) if "step" in f else None, note(**f))):
            result = self.run_loop()
        self.assertEqual(result["result"], "READY_FOR_REVIEW")
        self.assertEqual(app.unqueued, [])
        waiting = [s for s in steps if s and "hasn't started it" in s]
        self.assertTrue(waiting)  # `runs` shows the wait while it lasts, with what to do if the thread is stuck
        self.assertIn("--fresh", waiting[0])
        last = max(i for i, s in enumerate(steps) if s and "hasn't started it" in s)
        self.assertNotIn("hasn't started it", steps[last + 1] or "")  # and drops it once the turn starts

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
        self.assertNotIn("Every item of WP1 has to pass with evidence", first)
        message, _, restated = resumed.partition("\n\n")
        self.assertEqual(message, "Use the simulator.")
        for part in ("In docs/plans/WATER/DONE.json, change only WP1's items' `builder_result` and `evidence`; the script sets the status.",
                     f"`python3 {agent_loop.LOOP} merge --worktree .`",
                     "The project's rules are in ORCHESTRATE.md; re-read them"):
            self.assertIn(part, restated)
        self.assertNotIn("no GPL code", restated, "the rules are pointed to, not copied")
        self.assertTrue(restated.startswith("Every item of WP1 has to pass with evidence"))
        self.assertLessEqual(len(restated.split()), 90, "the restatement stays terse")
        self.assertNotIn("constraints_missing", result)

    def test_item5_a_turn_resumed_inside_a_run_restates_too(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        self.assertEqual(self.run_loop(host="claude")["result"], "CHECKS_FAILED")
        later = [self.prompt(c) for c in self.calls()[1:]]
        self.assertEqual(len(later), 2)
        for p in later:
            self.assertTrue(p.startswith("The script can't set the work package to Ready for Review yet"), p[:200])
            self.assertIn("Every item of WP1 has to pass with evidence", p)

    def test_item5_codex_restates_only_when_no_goal_is_active_and_records_the_goal(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        self.assertEqual(self.run_loop()["goal"], "none")
        self.run_loop(message="Use the simulator.")
        self.assertIn("\n\nEvery item of WP1 has to pass with evidence", self.prompt(self.calls()[-1]))
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        before = len(self.calls())
        os.environ.update(FAKE_REPLY="BLOCKED: no device")  # a plain block keeps one more turn while the goal is active
        result = self.run_loop(message="Use the simulator.")
        self.assertEqual(result["goal"], "active")
        prompts = [self.prompt(c) for c in self.calls()[before:]]
        self.assertEqual(prompts, ["Use the simulator.", "Carry on with WP1. WP1.1 hasn't passed yet."])

    def test_item5_a_generic_host_continuation_restates(self):
        host = self.root / "echo-host"
        host.write_text(ECHO_HOST)
        host.chmod(0o755)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + f"- **Host echo:** {host} {{model}} {{effort}} {{prompt}}\n- **Echo model:** m\n")
        self.commit_all()
        self.run_loop(host="echo")
        self.run_loop(host="echo", message="Use the simulator.")  # the missing fact lifts the block
        first, second = (c["argv"][-1] for c in self.calls())
        self.assertNotIn("Every item of WP1 has to pass with evidence", first)
        self.assertTrue(second.startswith("Build work package WP1 of module WATER,"), second[:200])  # the whole task again
        self.assertIn("From the lead:\nUse the simulator.", second)
        self.assertTrue(second.endswith("The skill lists the reasons."), second[-200:])

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
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_VERSION="codex-cli 0.167.0")
        with FakeCodexApp(self).installed():
            commit = self.run_loop()["commit"]
            self.assertEqual(self.review(commit=commit, effort="high")["verdict"], "PASS")
        rec = self.read_record()["work_packages"]["WP1"]
        self.assertEqual(rec["ready_for_review"]["observed"], {"model": "gpt-6.2-sol", "effort": "medium"})
        review = rec["reviews"][-1]
        self.assertEqual({k: review[k] for k in ("model", "effort", "observed", "cli", "path")},
                         {"model": "gpt-6.2-sol", "effort": "high", "cli": "codex-cli 0.167.0", "path": "visible",
                          "observed": {"model": "gpt-6.2-sol", "effort": "high"}})


    def test_a_visible_review_stops_a_hung_tool_call_and_a_timeout_is_named(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
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

    def test_a_paused_visible_review_the_app_doesnt_stop_says_so(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        with FakeCodexApp(self).installed():
            commit = self.run_loop()["commit"]
        with FakeCodexApp(self, behaviour="hang").installed() as app, \
                mock.patch.object(agent_loop, "codex_interrupt", lambda thread: False):
            pause_once_a_turn_is_running(app)
            result = self.review(commit=commit, host="codex")
        self.assertEqual(result["result"], "PAUSED")
        self.assertIn("so its turn may still be running", result["turn_not_stopped"])

    def test_a_resume_the_codex_app_holds_after_a_hung_call_fails_in_minutes_and_names_the_call(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        with FakeCodexApp(self).installed():
            commit = self.run_loop()["commit"]
        with FakeCodexApp(self, behaviour="hung_call_held").installed() as app, \
                mock.patch.object(agent_loop, "TOOL_CALL_LIMIT_S", 0.05):
            result = self.review(commit=commit, host="codex")  # a 6-minute turn limit; it should end long before
        self.assertEqual(result["result"], "HOST_FAILED")
        self.assertIn("didn't start the turn that resumes the thread after the script stopped its tool call "
                      "mcp__cua_repl.js", result["reason"])
        self.assertEqual(result["stopped_turn"]["tool_call"]["name"], "mcp__cua_repl.js")
        self.assertEqual(app.queued, {})

    # Item 7: the loader check runs on the resolved launch.


    def test_item7_a_skill_missing_where_the_host_loads_it_is_a_warning(self):
        warn = agent_loop.skill_warnings
        self.assertIn("reviewer isn't installed where claude", warn("claude", self.wt, "review")[0])
        self.assertIn("planner isn't installed where codex", warn("codex", self.wt, "plan")[0])
        self.assertEqual(warn("echo", self.wt, "build"), [])
        for folder in (agent_loop.CLAUDE_HOME / "skills/reviewer",
                       agent_loop.AGENTS_HOME / "skills/planner", self.home / "skills/builder"):
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("x")
        self.assertEqual(warn("claude", self.wt, "review"), [])
        self.assertEqual(warn("codex", self.wt, "plan"), [])
        self.assertIn("docs don't list", warn("codex", self.wt, "build")[0])
        plugin = agent_loop.CLAUDE_HOME / "plugins/cache/m/orchestrate/1.0/skills/planner"
        plugin.mkdir(parents=True)
        (plugin / "SKILL.md").write_text("x")
        self.assertEqual(warn("claude", self.wt, "plan"), [])

    # Item 8: reviewers and planners start with no inherited context.

    def fresh_review_and_plan(self, host, resume_flag):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        commit = self.run_loop(host=host)["commit"]
        builder = self.calls()[-1]
        self.assertEqual(self.review(commit=commit, host=host)["verdict"], "PASS")
        self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="plan PAY", host=host, model=None, effort=None,
                  turn_timeout_hours=0.1)
        for role in ("review", "plan"):
            call = next(c for c in self.calls() if c["role"] == role)
            self.assertNotIn(resume_flag, call["argv"], f"{host} {role} resumes nothing")
            first = "Review work package WP1 of module WATER, using the reviewer skill" if role == "review" \
                else "plan PAY"
            self.assertTrue(self.prompt(call).startswith(first), f"{host} {role} gets only its own task")
            if role == "plan":
                self.assertIn("planner skill", self.prompt(call))
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
        text, missing = agent_loop.binding(prof, "build", "WP1", None, "d.json")
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

    def test_holistic_2_an_human_rule_survives_fresh_sessions_and_work_packages_until_cleared(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        rule = "never edit the schema"
        self.run_loop(host="claude", human_rule=[rule])
        self.run_loop(host="claude", fresh=True, message="Findings: see the review.")
        self.run_loop(host="claude", message="go on")
        first, fresh, resumed = (self.prompt(c) for c in self.calls())
        self.assertIn("The user's rule: never edit the schema.", first)
        self.assertIn("The user's rule: never edit the schema.", fresh, "a fresh session keeps the rule")
        self.assertIn("Findings: see the review.", fresh)
        self.assertIn("The user's rule: never edit the schema.", resumed)
        self.assertEqual(self.state()["human_rules"], [rule])
        self.run_loop(host="claude", fresh=True, clear_human_rules=True, message="x is 3")
        self.assertNotIn("The user's rule:", self.prompt(self.calls()[-1]))
        self.assertEqual(self.state()["human_rules"], [])

    def test_holistic_2_an_active_codex_goal_still_gets_human_rules_added_after_it(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop()
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.run_loop(message="go on", human_rule=["keep the public API"])
        resumed = self.prompt(self.calls()[1])
        self.assertEqual(resumed, "go on\n\nThe user's rule: keep the public API.")

    # 3. Progress-only turns are capped.

    def test_holistic_3_progress_updates_stop_as_stalled_after_two_continuations_naming_open_items(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="Read the code; next I'll write the parser.")
        result = self.run_loop()
        self.assertEqual((result["result"], result["open"]), ("STALLED", ["WP1.1"]))
        prompts = [self.prompt(c) for c in self.calls()]
        self.assertEqual(len(prompts), agent_loop.STALL_TURNS)
        for p in prompts[1:]:
            self.assertTrue(p.startswith("Carry on with WP1. WP1.1 hasn't passed yet."))

    def test_holistic_3_uncommitted_work_is_progress_not_a_stall(self):
        marks = agent_loop.work_marks(self.wt, None)
        (self.wt / "parser.py").write_text("x = 1")
        self.assertNotEqual(agent_loop.work_marks(self.wt, None), marks)

    # 4. No model or effort frontmatter overrides the launch.


    # 6. A resumed Claude turn restates the objective (covered with item 5 above), terse.

    # 7. Plugin installs: skills and namespaced names.

    def install_plugin(self, home):
        ver = home / "plugins/cache/ryannel-skills/orchestrate/1.3.0"
        for name in ("reviewer", "planner", "builder"):
            (ver / "skills/orchestration" / name).mkdir(parents=True)
            (ver / "skills/orchestration" / name / "SKILL.md").write_text("x")
        (ver / ".claude-plugin").mkdir()
        (ver / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": [
            {"name": "orchestrate", "skills": ["./skills/orchestration/reviewer",
                                               "./skills/orchestration/planner",
                                               "./skills/orchestration/builder"]},
            {"name": "skill-creator", "skills": ["./skills/skill-creator"]}]}))
        # the same repository copied for another plugin doesn't provide orchestrate's skills
        other = home / "plugins/cache/ryannel-skills/skill-creator/1.0.0/skills/orchestration/lead"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("x")

    def test_holistic_7_plugin_installed_skills_are_found_on_both_hosts_in_this_repos_layout(self):
        warn = agent_loop.skill_warnings
        self.install_plugin(agent_loop.CLAUDE_HOME)
        self.install_plugin(self.home)
        self.assertEqual(warn("claude", self.wt, "review"), [])
        self.assertEqual(warn("codex", self.wt, "plan"), [])
        self.assertEqual(agent_loop.plugin_components(self.home, "skills").get("lead"), None)
        note = agent_loop.skill_note("reviewer", "codex")
        self.assertTrue(note.startswith("`orchestrate:reviewer` in Codex; the file is "), note)
        self.assertTrue(agent_loop.skill_note("reviewer", "claude").startswith("the file is "))

    def test_holistic_7_claude_reviews_start_from_the_skill_without_an_agent_file(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        commit = self.run_loop(host="claude")["commit"]
        self.install_plugin(agent_loop.CLAUDE_HOME)
        self.assertEqual(self.review(commit=commit, host="claude")["verdict"], "PASS")
        argv = next(c for c in self.calls() if c["role"] == "review")["argv"]
        self.assertNotIn("--agent", argv)
        self.assertEqual(argv[argv.index("--disallowedTools") + 1], "Agent")

    # 8. The reviewer fails only on blocking defects.


class HolisticAlone(ProfileOnly):
    """Tests from Holistic that need no repository, only the project settings."""

    def test_holistic_4_no_skill_sets_model_or_effort(self):
        root = agent_loop.SKILLS
        files = [root / n / "SKILL.md" for n in ("lead", "builder", "reviewer", "planner")]
        self.assertEqual(sorted(root.glob("*/agents")), [])
        for f in files:
            front = f.read_text().split("\n---\n")[0]
            self.assertNotRegex(front, r"(?m)^(model|effort):", str(f))

    def test_holistic_8_review_skill_and_findings_message_separate_blocking_from_advisory(self):
        review = (agent_loop.SKILLS / "reviewer/tasks/work-package.md").read_text()
        self.assertIn("is a Suggestion", review)
        self.assertIn("list every Must Fix in the work package's `findings`", review)
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


HOLD = ("import sys, time; sys.path.insert(0, {scripts!r}); import agent_loop; from pathlib import Path\n"
        "wt, name, gate = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])\n"
        "with agent_loop.held(name, wt, what='hold ' + gate.name):\n"
        "    print('got', flush=True)\n"
        "    while not gate.exists(): time.sleep(0.05)\n")


class LockClasses(Clean):
    """Shared resources with a capacity, sole use that drains them, the hold limit and the `locks` command. Each
    holder is a separate process, as builders are, holding its lock until the test opens its gate."""

    def repo(self, settings=""):
        self.wt = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        subprocess.run(["git", "init", "-q", str(self.wt)], check=True)
        if settings:
            (self.wt / "ORCHESTRATE.md").write_text(settings)

    def holder(self, name, tag):
        gate = self.wt / f"release-{tag}"
        proc = subprocess.Popen([sys.executable, "-c", HOLD.format(scripts=str(SCRIPTS)), str(self.wt), name,
                                 str(gate)], stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: (proc.kill(), proc.wait(), proc.stdout.close()))
        return proc, gate

    def got(self, proc, within):
        import select
        ready, _, _ = select.select([proc.stdout], [], [], within)
        return bool(ready) and proc.stdout.readline().strip() == "got"

    def queued(self, count):
        """Waits until `count` requests are queued, so the next one is surely behind them."""
        for _ in range(200):
            if sum(len(r["queued"]) for r in agent_loop.lock_report(self.wt)["locks"]) >= count:
                return
            time.sleep(0.05)
        self.fail(f"{count} requests never queued")

    def rows(self):
        path = Path(agent_loop.git_common_dir(self.wt)) / "orchestrate" / agent_loop.LOCKS_FILE
        return [json.loads(line) for line in path.read_text().splitlines()]

    def test_settings_lines_parse_and_bad_ones_are_named(self):
        parse = agent_loop.lock_settings_from
        self.assertEqual(parse(""), {"shared": {}, "hold_limit_s": agent_loop.DEFAULT_HOLD_LIMIT_S, "problems": []})
        got = parse("- **Shared resources:** `gpu: 3`, chrome 1 runs\n- **Lock hold limit:** 45 minutes\n")
        self.assertEqual((got["shared"], got["hold_limit_s"]), ({"gpu": 3, "chrome": 1}, 2700))
        self.assertEqual(parse("- **Lock hold limit:** 2h\n")["hold_limit_s"], 7200)
        self.assertIsNone(parse("- **Lock hold limit:** none\n")["hold_limit_s"])
        self.assertEqual(parse("- **Shared resources:** none\n")["shared"], {})
        self.assertEqual(parse("- **Shared resources:** <resources several runs may use at once>\n")["shared"], {})
        bad = parse("- **Shared resources:** gpu, sim.alone: 2\n- **Lock hold limit:** soon\n")
        self.assertEqual(bad["shared"], {})
        self.assertEqual(len(bad["problems"]), 3, bad["problems"])
        self.repo("- **Merge:** local\n- **Test command:** none\n- **Shared resources:** gpu: 2\n")
        prof = agent_loop.profile(self.wt, strict=True)
        self.assertEqual((prof["shared_resources"], prof["lock_hold_limit_s"]),
                         ({"gpu": 2}, agent_loop.DEFAULT_HOLD_LIMIT_S))
        rule = agent_loop.resources_rule(prof)
        self.assertIn("gpu (up to 2 runs at once)", rule)
        self.assertIn("`lock <name>.alone -- <command>`", rule)
        self.assertIn("longer than 30 minutes", rule)
        self.assertEqual(agent_loop.resources_rule({**prof, "shared_resources": {}}), "")

    def test_a_shared_resource_lets_that_many_runs_hold_it_at_once(self):
        self.repo("- **Shared resources:** gpu: 2\n")
        a, gate_a = self.holder("gpu", "a")
        b, _ = self.holder("gpu", "b")
        self.assertTrue(self.got(a, 15) and self.got(b, 15))
        c, _ = self.holder("gpu", "c")
        self.assertFalse(self.got(c, 1.0))  # both places are taken
        gate_a.touch()
        self.assertTrue(self.got(c, 15))

    def test_sole_use_drains_the_shared_holders_and_new_shared_requests_queue_behind_it(self):
        self.repo("- **Shared resources:** gpu: 3\n")
        a, gate_a = self.holder("gpu", "a")
        b, gate_b = self.holder("gpu", "b")
        self.assertTrue(self.got(a, 15) and self.got(b, 15))
        alone, gate_alone = self.holder("gpu.alone", "alone")
        self.queued(1)
        late, _ = self.holder("gpu", "late")  # a place is free, but a sole use is waiting
        self.queued(2)
        self.assertFalse(self.got(alone, 0.5) or self.got(late, 0.5))
        gate_a.touch()
        self.assertFalse(self.got(alone, 0.5) or self.got(late, 0.5))  # b still shares it
        gate_b.touch()
        self.assertTrue(self.got(alone, 15))
        self.assertFalse(self.got(late, 1.0))  # it waits out the sole use too
        gate_alone.touch()
        self.assertTrue(self.got(late, 15))
        uses = [(r["lock"], r.get("use")) for r in self.rows()]
        self.assertEqual(uses, [("gpu", "shared"), ("gpu", "shared"), ("gpu", "alone")])

    def test_an_undeclared_resource_is_one_run_at_a_time_as_before(self):
        self.repo()
        a, gate_a = self.holder("gpu", "a")
        self.assertTrue(self.got(a, 15))
        b, _ = self.holder("gpu", "b")
        self.assertFalse(self.got(b, 1.0))
        common = Path(agent_loop.git_common_dir(self.wt))
        with open(common / "orchestrate-gpu.lock") as raw:  # an older copy of the script locks this file exclusively
            with self.assertRaises(BlockingIOError):
                fcntl_ex(raw)
        gate_a.touch()
        self.assertTrue(self.got(b, 15))
        a.wait(10)
        self.assertEqual({k for k in self.rows()[0]}, {"lock", "worktree", "pid", "asked_s", "got_s", "released_s"})
        self.assertEqual(self.rows()[0]["lock"], "gpu")

    def test_flow_counts_overlapping_shared_holds_once_in_busy(self):
        self.repo("- **Shared resources:** gpu: 2\n")
        subprocess.run(["git", "-C", str(self.wt), "checkout", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(self.wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "start"], check=True)
        now = time.time()
        for got, released in ((now - 600, now - 300), (now - 500, now - 200)):
            agent_loop.record_lock_use(self.wt, "gpu", got, got, released, 0, "shared")
        with contextlib.redirect_stderr(io.StringIO()):
            gpu = agent_loop.flow_numbers(self.wt, 1)["locks"]["gpu"]
        self.assertEqual((gpu["holds"], gpu["held_h"], gpu["busy"]), (2, 0.2, 0.11))  # 400 s of 3600, not 600

    def test_flow_splits_failed_jobs_into_stopped_answers_and_errors(self):
        self.repo()
        subprocess.run(["git", "-C", str(self.wt), "checkout", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(self.wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "start"], check=True)
        folder = agent_loop.loop_dir(self.wt)
        rows = []
        for n, (command, code) in enumerate((("python3 /x/agent_loop.py check --module A --worktree .", "1"),
                                             ("python3 /x/agent_loop.py merge --worktree .", "1"),
                                             ("./dev check", "143"), ("python3 tools/broken.py", "1"),
                                             ("./dev check", "0"))):
            log = folder / f"job{n}.log"
            log.write_text("")
            Path(str(log) + ".exit").write_text(code)
            rows.append({"id": f"j{n}", "pid": 1, "command": command, "log": str(log), "started_s": time.time()})
        (folder / agent_loop.JOBS_FILE).write_text("".join(json.dumps(r) + "\n" for r in rows))
        with contextlib.redirect_stderr(io.StringIO()):
            jobs = agent_loop.flow_numbers(self.wt, 1)["background_jobs"]
        self.assertEqual({k: jobs[k] for k in ("started", "failed", "stopped", "script_said_no", "errors")},
                         {"started": 5, "failed": 4, "stopped": 1, "script_said_no": 2, "errors": 1})

    def test_lock_refuses_to_wrap_the_scripts_own_commands(self):
        self.repo()
        out = subprocess.run([sys.executable, str(SCRIPTS / "agent_loop.py"), "lock", "gpu", "--", "python3",
                              str(SCRIPTS / "agent_loop.py"), "merge", "--worktree", "."], cwd=self.wt,
                             capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("merge queue", out.stderr)

    def test_an_older_copys_exclusive_hold_keeps_shared_requests_out(self):
        self.repo("- **Shared resources:** gpu: 2\n")
        common = Path(agent_loop.git_common_dir(self.wt))
        with open(common / "orchestrate-gpu.lock", "a") as raw:
            fcntl_ex(raw)
            a, _ = self.holder("gpu", "a")
            self.assertFalse(self.got(a, 1.0))
            self.assertTrue(agent_loop.lock_report(self.wt)["locks"][0]["held_by_unknown"])
        self.assertTrue(self.got(a, 15))

    def test_a_holder_that_dies_lets_go_and_its_ticket_is_cleared(self):
        self.repo("- **Shared resources:** gpu: 1\n")
        a, _ = self.holder("gpu", "a")
        self.assertTrue(self.got(a, 15))
        b, _ = self.holder("gpu.alone", "b")
        self.assertFalse(self.got(b, 0.5))
        a.kill()
        a.wait()
        self.assertTrue(self.got(b, 15))
        (gpu,) = agent_loop.lock_report(self.wt)["locks"]
        self.assertEqual([h["pid"] for h in gpu["holders"]], [b.pid])

    def test_the_hold_limit_stops_a_command_under_lock_and_says_so(self):
        self.repo("- **Lock hold limit:** 1 second\n")
        err = io.StringIO()
        started = time.time()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=None, command_args=[
                "--worktree", str(self.wt), "--", "sleep", "30"]))
        self.assertEqual(stop.exception.code, 124)
        self.assertLess(time.time() - started, 15)
        self.assertIn("held the gpu lock for 1 second, which is this project's hold limit", err.getvalue())
        self.assertEqual((self.rows()[-1]["exit"], self.rows()[-1]["stopped"]), (124, "hold limit"))
        r = agent_loop.run_check(self.wt, "sleep 30", "gpu", 3600, save=False)
        self.assertEqual(r["exit"], 124)
        self.assertIn("this project's hold limit", r["err"])

    def test_the_hold_limit_leaves_the_merge_lock_alone(self):
        self.repo("- **Lock hold limit:** 1 second\n")
        with agent_loop.held("merge", self.wt) as use:
            self.assertIsNone(use["limit_s"])

    def test_locks_shows_who_holds_each_resource_and_who_is_queued(self):
        self.repo("- **Shared resources:** gpu: 1\n- **Lock hold limit:** 20 minutes\n")
        a, _ = self.holder("gpu", "a")
        self.assertTrue(self.got(a, 15))
        b, _ = self.holder("gpu.alone", "b")
        self.queued(1)
        text = self.printed(agent_loop.cmd_locks, worktree=str(self.wt), json=False)
        self.assertIn("stopped once it has held a lock for 20 minutes", text)
        self.assertIn("gpu (shared by up to 1 runs at once, or held alone as gpu.alone): 1 holding, 1 queued.", text)
        self.assertRegex(text, rf"holding shared for \d+s: pid {a.pid} in {re.escape(str(self.wt))}: hold release-a")
        self.assertRegex(text, rf"queued alone for \d+s: pid {b.pid} in .*: hold release-b")
        report = json.loads(self.printed(agent_loop.cmd_locks, worktree=str(self.wt), json=True))
        (gpu,) = report["locks"]
        self.assertEqual(([h["pid"] for h in gpu["holders"]], [q["pid"] for q in gpu["queued"]]), ([a.pid], [b.pid]))

    def printed(self, func, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            func(argparse.Namespace(**kw))
        return out.getvalue()


def fcntl_ex(handle):
    import fcntl
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)


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
    profile, an unplanned repository, running a work package's checks, cost, quota's readout, stops that say what's next
    and who holds what, the review host, and the pause race. Each test is named after its item."""

    def revise_design(self):
        """What a planner does after DESIGN CHANGES: the script won't review an unchanged design again."""
        self.git("pull", "-q", "--rebase", "origin", "main")
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# Water design, revised")
        self.assertEqual(self.adopt("docs/plans/WATER/DESIGN.md")["result"], "ADOPTED")

    def edit_w2(self, check="test -n changed"):
        doc = self.read_done("HEAD")
        doc["work_packages"][1]["items"][0]["check"] = check
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))

    # 1. The one-chat path

    def draft(self):
        """WATER as a draft: planned, nothing built, its design review still owed."""
        self.write_done([work_package("WP1", "not_started", ["open"]), work_package("WP2", "not_started", ["open"])], design_ok=False)
        self.commit_all()

    def test_item1_adopt_authorises_a_drafts_revisions_for_the_owed_design_review(self):
        self.draft()
        self.edit_w2()
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertEqual(result["authorised"], ["WATER"])
        r = self.ready()
        self.assertEqual(r.get("invalid", []), [])
        self.assertEqual(r["design_not_approved"], [{"module": "WATER"}])
        stamp = self.read_record()["work_packages"]["WP2"]["authorised"]
        self.assertEqual(stamp["by"], "adopt")
        self.assertIn("before the module's design review passed", stamp["why"])
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertIn("## Definitions changed through adopt", report)
        self.assertIn("WATER WP2: definitions authorised by adopt", report)
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.run_loop()["result"], "READY_FOR_REVIEW")  # after the design review judged them

    def test_item1_a_lead_cant_weaken_checks_once_the_design_review_passed(self):
        """The reviewer's probe: design agreed, nothing built, a check rewritten to `true`."""
        w1 = work_package("WP1", "not_started", ["open", "open"], inspect="the frames match the spec")
        w1["items"][0]["check"] = "cargo test --test physics -- --exact solver_converges"
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        doc = self.read_done("HEAD")
        doc["work_packages"][0]["items"][0]["check"] = "true"
        doc["work_packages"][0]["items"][1].pop("inspect", None)
        doc["work_packages"][0]["items"][1]["check"] = "true"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED", result)
        self.assertIn("a design review of it has passed", result["problems"][0])
        self.assertIn(" human scope --module WATER --work-package WP1 ", result["next"]["human"])
        self.assertEqual(self.read_done()["work_packages"][0]["items"][0]["check"],
                         "cargo test --test physics -- --exact solver_converges")
        self.assertEqual(self.run_loop()["result"], "INVALID")  # the edit here still isn't authorised

    def test_item1_a_claim_alone_closes_the_draft(self):
        self.draft()
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.assertTrue(agent_loop.take_hold(other, prof, "WATER", "WP1")[0])  # taken, nothing accepted
        self.edit_w2()
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED", result)
        self.assertIn("building on it has begun", result["problems"][0])
        self.assertIn(" plan --worktree ", result["next"]["command"])

    def test_item1_a_run_holding_the_module_closes_the_draft(self):
        self.draft()
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; from pathlib import Path\n"
                f"wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, 'WATER')\n"
                "agent_loop.loop_register(wt, 'build', module='WATER', work_package='WP1', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            self.edit_w2()
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
                self.assertTrue(agent_loop.take_hold(other, prof, "WATER", "WP1")[0])
            return real_land(tree, prof_, check=check)
        self.edit_w2()
        with mock.patch.object(agent_loop, "land", land):
            result = self.adopt()
        self.assertEqual(result["result"], "FAILED", result)
        self.assertIn("weren't authorised", result["detail"])
        self.assertNotEqual((self.read_record()["work_packages"]["WP2"].get("authorised") or {}).get("by"), "adopt")
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
        self.assertIn("settings --set LABEL VALUE --said", refused["problems"][0])
        self.assertIn("lead changes each line with `settings --set`", self.ready()["settings_differ"])
        nothing = self.adopt()
        self.assertEqual(nothing["result"], "NOTHING")
        self.assertIn("settings_differ", nothing)

    def test_item2_adopt_leaves_evidence_uncommitted(self):
        self.ready()  # links the working folder into the worktree
        (self.wt / ".orchestrate/evidence/build-reports").mkdir(parents=True)
        (self.wt / ".orchestrate/evidence/build-reports/2026-11-10.md").write_text("# Build report")
        self.assertEqual(self.adopt()["result"], "NOTHING")
        self.assertTrue(self.evidence("build-reports/2026-11-10.md").exists())

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

    # 4. A work package's checks against a tree

    def test_item4_check_tells_not_built_from_broken(self):
        self.write_done([work_package("WP1", "not_started", ["open", "open", "open"]), work_package("WP2", "not_started", ["open"])])
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        checks = ["true", "test -f built.txt", "if then"]
        # not built yet, a failing test whose output looks like shell trouble, and one that doesn't parse
        for i, check in zip(doc["work_packages"][0]["items"], checks):
            i["check"] = check
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        out = json.loads(self.printed(agent_loop.cmd_check, code=1, module="WATER", work_package="WP1",
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
        doc["work_packages"][0]["items"][2]["check"] = "true"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        out = json.loads(self.printed(agent_loop.cmd_check, code=0, module="WATER", work_package="WP1",
                                      worktree=str(self.wt), plans_from=None, timeout=60.0, json=True))
        self.assertEqual(out["pass"], 3)

    def test_a_planner_tries_its_item_checks_without_the_test_command(self):
        self.write_done([work_package("WP1", "not_started", ["open"])])
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("**Test command:** none", "**Test command:** false"))
        kw = dict(module="WATER", work_package="WP1", worktree=str(self.wt), plans_from=None, timeout=60.0, json=True)
        everything = json.loads(self.printed(agent_loop.cmd_check, code=1, **kw))
        self.assertEqual(everything["items"][-1]["id"], "Test command")
        items = json.loads(self.printed(agent_loop.cmd_check, code=0, items_only=True, **kw))
        self.assertEqual([i["id"] for i in items["items"]], ["WP1.1"])

    # 5. Cost in one place


    def test_item5_every_turn_lands_in_the_ledger_and_cost_adds_it_up(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])],
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
        self.assertEqual([(r["role"], r["work_package"]) for r in rows],
                         [("review", "design"), ("build", "WP1"), ("review", "WP1")])
        c = json.loads(self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=True))
        self.assertEqual(c["modules"]["WATER"]["WP1"]["build"]["output"], 7)
        self.assertEqual(c["modules"]["WATER"]["design"]["review"]["runs"], 1)
        self.assertEqual(c["total"]["output"], 21)
        text = self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=False)
        self.assertIn("WATER WP1: build 1 turn, tokens 60 in, 40 cached, 7 out on codex; review 1 turn", text)
        body = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertIn("- WATER WP1: Done, by review", body)
        self.assertIn("fewer than about ten, so spot-check every one", body)
        self.assertIn("## Flow", body)
        self.assertIn("times a work package reached Ready for Review: 1; work packages that became Done: 1", body)
        with self.assertRaises(SystemExit) as exit_:  # a hold of an exclusive resource whose command fails
            agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=None, command_args=[
                "--worktree", str(self.wt), "--", "sh", "-c", "exit 4"]))
        self.assertEqual(exit_.exception.code, 4)
        f = json.loads(self.printed(agent_loop.cmd_flow, worktree=str(self.wt), since=24.0))["flow"]
        self.assertEqual((f["ready_for_review"], f["done"]), (1, 1))
        self.assertEqual((f["locks"]["gpu"]["holds"], f["locks"]["gpu"]["failed"]), (1, 1))
        self.assertIn("records", f["locks"])  # with no test command to run, the builder's merge took the short lock
        self.assertGreaterEqual(f["commits"], f["code_commits"])

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
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        changes = self.review("design", commit=None)
        self.assertEqual((changes["verdict"], changes["next"]["by"]), ("DESIGN CHANGES", "lead"))
        self.assertIn(" plan --worktree ", changes["next"]["command"])
        self.assertEqual(changes["next"]["findings"], ".orchestrate/evidence/WATER/design-review.md")
        self.revise_design()
        os.environ.update(FAKE_REVIEW="design")
        ok = self.review("design", commit=None)
        self.assertEqual(ok["verdict"], "DESIGN OK")
        self.assertIn(" run --module WATER ", ok["next"]["command"])
        # a second design review keeps the first
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.evidence("WATER/design-review-1.md").read_text(), "the design needs a second pass")
        os.environ.update(FAKE_REVIEW="pass")
        claim = self.run_loop()
        passed = self.review(commit=claim["commit"])
        self.assertEqual(passed["verdict"], "PASS")
        self.assertIn(" run --module WATER ", passed["next"]["command"])
        os.environ.pop("FAKE_PLAN", None)
        planned = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Plan PAY", host=None, model=None,
                            effort=None, turn_timeout_hours=0.1)
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertIn(" review --module PAY --work-package design ", planned["next"]["command"])

    def test_item7_the_last_pass_says_the_module_is_finished(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames")])
        self.commit_all()
        claim = self.run_loop()
        passed = self.review(commit=claim["commit"])
        self.assertIn(" ready --worktree ", passed["next"]["command"])
        self.assertIn("finished", passed["next"]["why"])
        self.assertIn("remove the worktree it was built in", passed["next"]["why"])
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
                "agent_loop.loop_register(wt, 'build', module='WATER', work_package='WP1', host='codex', model='m', "
                "effort='medium'); print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            result = self.run_loop()
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
        self.assertEqual(result["result"], "IN_PROGRESS_ELSEWHERE")
        self.assertEqual(result["holder"]["pid"], proc.pid)
        self.assertEqual(result["holder"]["worktree"], str(self.wt))
        self.assertIn(f"pid {proc.pid}", result["by"])

    def test_item7_status_marks_an_unchecked_claim_and_profile_hides_the_codex_model(self):
        self.write_done([work_package("WP1", "done", ["pass"]), work_package("WP2", "not_started", ["open"])], authorise=False)
        self.commit_all()  # the builder's file says done; the loop has checked nothing
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        line = next(l for l in status.splitlines() if l.strip().startswith("WP1"))
        self.assertIn("done, unchecked", line)
        self.assertIn("the script hasn't checked this yet; `run` checks it", line)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("codex", "claude") + "- **Codex model:** gpt-x\n")
        prof = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host=None))
        self.assertNotIn("model", prof)

    def test_settings_reports_paths_agents_and_what_is_defaulted(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Claude planner:** claude-fable-5-2 high\n")
        self.write_done([work_package("WP1", "not_started", ["open"])])
        self.commit_all()
        prof = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host=None).splitlines()[-1])
        self.assertEqual(prof["result"], "SETTINGS")
        self.assertEqual(prof["paths"]["modules"], {"WATER": str(self.wt.resolve() / "docs/plans/WATER")})
        self.assertTrue(prof["paths"]["working_folder"].endswith("/orchestrate/evidence"))
        self.assertEqual(prof["agents"]["claude"]["planner"],
                         {"model": "claude-fable-5-2", "model_from": "a line for this kind of agent",
                          "effort": "high", "effort_from": "a line for this kind of agent"})
        self.assertEqual(prof["agents"]["codex"]["planner"]["effort_from"], "the planners' default")
        self.assertIn("lead check-in", prof["defaulted"])

    def test_a_run_on_the_main_checkout_builds_in_the_modules_own_worktree(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Worktrees:** .orchestrate/worktrees\n")
        self.write_done([work_package("WP1", "not_started", ["open"])])
        self.commit_all()
        self.git("push", "-q", "origin", "HEAD:main")
        prof = agent_loop.profile(self.wt)
        made, how = agent_loop.module_worktree(self.wt, prof, "WATER")
        self.assertEqual((made, how), (self.wt.resolve() / ".orchestrate/worktrees/water", "made"))
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD", where=made).stdout.strip(), "build/water")
        self.assertIn(".orchestrate/worktrees", (Path(agent_loop.git_common_dir(self.wt)) / "info/exclude").read_text())
        self.assertEqual(agent_loop.module_worktree(self.wt, prof, "WATER"), (made, "found"))
        self.assertEqual(agent_loop.module_worktree(made, prof, "WATER"), (made, None))  # not the main branch
        self.assertEqual(agent_loop.finished_worktrees(self.wt, prof, ["WATER"]), [str(made)])
        self.assertFalse(made.exists())

    def test_settings_template_is_a_file_the_script_reads(self):
        out = self.printed(agent_loop.cmd_settings, worktree=str(self.wt), template=True)
        self.assertIn("- **Test command:**", out)
        self.assertIn("## Targets", out)

    def test_settings_set_merges_one_line_with_the_users_words(self):
        self.write_done([work_package("WP1", "not_started", ["open"])])
        self.commit_all()
        args = parse_argv(COMMANDS[agent_loop.cmd_settings], ["--worktree", str(self.wt), "--set", "Builders",
                                                              "two Claude builders", "--said", "use two Claude ones"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_settings(args)
        line = json.loads(out.getvalue().splitlines()[-1])
        self.assertEqual((stop.exception.code, line["result"]), (0, "SAVED"), line)
        body = subprocess.run(["git", "-C", str(self.wt), "log", "-1", "--format=%B", "origin/main"],
                              capture_output=True, text=True).stdout + subprocess.run(
            ["git", "-C", str(self.wt), "log", "-1", "--format=%B", "main"], capture_output=True, text=True).stdout
        self.assertIn("The user said: use two Claude ones", body)
        prof = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host=None).splitlines()[-1])
        self.assertEqual(prof["builders"], 2)
        with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit):
            agent_loop.cmd_settings(args)

    # 8. Reviews on the right host

    def test_item8_the_profile_sends_reviews_to_the_other_host(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames")], design_ok=False)
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
        self.write_done([work_package("WP1", "not_started", ["open"])], design_ok=False)
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
        a moment: `pause`, `status`, `loops` and the IN_PROGRESS_ELSEWHERE holder find liveness without it."""
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
            self.printed(agent_loop.cmd_pause, code=0, module=None, worktree=str(self.wt))
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
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_USAGE="1")
        first = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        self.review(commit=first["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        second = self.run_loop(message="FINDINGS")
        self.assertEqual(second["result"], "READY_FOR_REVIEW", second)
        claim = self.read_record()["work_packages"]["WP1"]["ready_for_review"]
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
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["ready_for_review"]["usage"]["cost_usd"], 0.8)

    # 8. User Feedback on items a builder can't judge

    def test_item8_human_feedback_goes_through_the_record_and_into_the_prompts(self):
        w1 = work_package("WP1", "not_started", ["open", "open", "open"], inspect="frames")
        w1["items"][1]["needs"] = needs("human_feedback", "the user picks a direction")
        w1["items"][2]["needs"] = needs("human_feedback", "the user judges the ink")
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_STATE="in_progress", FAKE_REPLY="BLOCKED: WP1.2 needs the user")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_human_feedback"), blocked)
        self.assertEqual(blocked["next"]["decides"], "human")
        self.assertIn(" human feedback --module WATER --work-package WP1 --item WP1.2 --item WP1.3 ",
                      blocked["next"]["command"])
        self.assertIn("--asked '", blocked["next"]["command"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        given = self.human("feedback", "WP1", "Direction B, the ink one.", item=["WP1.2", "WP1.3"],
                           asked="Which direction do you want, A or B?")
        self.assertEqual((given["result"], given["unblocked"]), ("DONE", True))
        [entry] = self.read_record()["work_packages"]["WP1"]["human_feedback"]
        self.assertEqual((entry["asked"], entry["said"], entry["items"]),
                         ("Which direction do you want, A or B?", "Direction B, the ink one.", ["WP1.2", "WP1.3"]))
        self.assertTrue(entry["at"])
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "in_progress")
        for key in ("FAKE_SKIP_NEEDS", "FAKE_STATE"):
            os.environ.pop(key)
        os.environ.update(FAKE_REPLY="DONE")
        claim = self.run_loop(fresh=True, message="Show the ink direction first.")
        self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
        prompt = self.calls()[-1]["argv"][-1]
        order = [prompt.find(part) for part in (
            "Build work package WP1 of module WATER,", "\nFinish the work package by merging", "User Feedback on WP1", "\nAbout this session:\n",
            "\nFrom the lead:\nShow the ink direction first.", "\nWhen the work is merged and proved, end with DONE")]
        self.assertTrue(all(i >= 0 for i in order) and order == sorted(order), (order, prompt))
        self.assertIn('on WP1.2, WP1.3: asked "Which direction do you want, A or B?"; '
                      'the user said "Direction B, the ink one."', prompt)
        self.assertEqual(prompt.count(f"python3 {agent_loop.LOOP}"), 1, "the script's path is given once")
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        self.assertIn("work_packages.WP1.human_feedback", self.calls()[-1]["argv"][-1])

    def test_a_builder_asking_for_an_approval_gets_the_users_words_recorded(self):
        w1 = work_package("WP1", "blocked", ["open"])
        w1["blocked"] = {"reason": "needs_human_feedback", "items": [], "what": "approve publishing to the store"}
        self.write_done([w1])
        self.commit_all()
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertIn("the builder asks for the user's decision: approve publishing", report)
        self.call(agent_loop.cmd_human, action="feedback", module="WATER", work_package="WP1", item=[], text=None,
                  said="Yes, publish it.", asked="May it publish to the store?", worktree=str(self.wt))
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["human_feedback"][0]["said"], "Yes, publish it.")
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "in_progress")

    def test_item8_feedback_needs_the_question_and_only_covers_items_that_need_human_feedback(self):
        w1 = work_package("WP1", "not_started", ["open", "open", "open"])
        w1["items"][2]["needs"] = needs("human_feedback", "the user judges the ink")
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.assertIn("hasn't started", self.refused_feedback("WP1", ["WP1.3"]))  # nothing built to judge yet
        w1 = work_package("WP1", "in_progress", ["open", "open", "open"])
        w1["items"][1]["needs"] = needs("hardware", "plug in the iPhone")
        w1["items"][2]["needs"] = needs("human_feedback", "the user judges the ink")
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.assertIn("ORCHESTRATE_VISIBLE=1", self.refused_feedback("WP1", ["WP1.2"]))
        self.assertIn("isn't marked as needing user feedback", self.refused_feedback("WP1", ["WP1.1"]))
        try:
            with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
                agent_loop.cmd_human(argparse.Namespace(action="feedback", module="WATER", work_package="WP1",
                                                        item=["WP1.3"], text=None, said="fine", asked=None,
                                                        worktree=str(self.wt)))
        finally:
            release()
        self.assertIn("needs --asked", str(stop.exception))
        self.assertNotIn("human_feedback", self.read_record()["work_packages"]["WP1"])
        self.assertEqual(self.human("feedback", "WP1", "The ink reads well.", item="WP1.3")["result"], "DONE")

    # 9. Captures beside the review

    def test_item9_a_reviewers_captures_land_beside_the_review(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="pass", FAKE_CAPTURE="1")
        result = self.review(commit=claim["commit"])
        self.assertEqual(result["verdict"], "PASS", result)
        self.git("fetch", "-q", "origin")
        self.assertIn("PNG", self.evidence("WATER/WP1-review/shot.png").read_text())
        self.git("fetch", "-q", "origin")
        self.assertNotIn("shot.png", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)

    # 10. Owner commands

    def test_item10_an_human_command_needs_the_humans_words(self):
        with self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_human(argparse.Namespace(action="accept", module="WATER", work_package="WP1", item=None,
                                                    text="  ", worktree=str(self.wt)))
        self.assertIn("human accept needs --text, the user's words", str(stop.exception))

    def test_item10_human_scope_leaves_the_worktree_clean(self):
        self.edit_w2()
        result = self.human("scope", "WP2")
        self.assertEqual(result["result"], "DONE", result)
        self.assertTrue(result["worktree"].startswith("fast-forwarded"), result)
        self.assertEqual(self.git("status", "--porcelain").stdout.strip(), "")
        self.assertEqual(self.read_done("HEAD")["work_packages"][1]["items"][0]["check"], "test -n changed")

    # 11. A planner's report keeps its end


    # Round four: the commands tried on finished projects

    def test_r4_cost_falls_back_to_the_committed_record_when_the_ledger_has_nothing(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])],
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
        self.assertEqual(c["modules"]["WATER"]["WP1"]["source"], "records")
        self.assertEqual(c["modules"]["WATER"]["WP1"]["build"]["output"], 7)
        self.assertEqual(c["modules"]["WATER"]["design"]["review"]["runs"], 1)
        text = self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=False)
        self.assertNotIn("no turns recorded", text)
        self.assertIn("WATER WP1: build 1 turn", text)
        self.assertIn("[from the committed record]", text)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertIn("[from the committed record]", report)
        # where the ledger has a work package, it wins and isn't marked
        ledger.write_text(json.dumps({"at": agent_loop.now(), "role": "build", "module": "WATER", "work_package": "WP2",
                                      "host": "codex", "usage": {"input": 1, "cached": 0, "output": 1}}) + "\n")
        c = json.loads(self.printed(agent_loop.cmd_cost, worktree=str(self.wt), module=None, since=None, json=True))
        self.assertEqual(c["modules"]["WATER"]["WP2"]["source"], "ledger")
        self.assertEqual(c["modules"]["WATER"]["WP1"]["source"], "records")

    def test_r4_check_reads_out_per_item_and_json_behind_a_flag(self):
        self.write_done([work_package("WP1", "not_started", ["open", "open"]), work_package("WP2", "not_started", ["open"])])
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        doc["work_packages"][0]["items"][0]["check"] = "true"
        doc["work_packages"][0]["items"][1]["check"] = "echo nope-not-built; exit 3"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        kw = dict(module="WATER", work_package="WP1", worktree=str(self.wt), plans_from=None, timeout=60.0)
        text = self.printed(agent_loop.cmd_check, code=1, json=False, **kw)
        self.assertRaises(json.JSONDecodeError, json.loads, text)
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("WATER WP1 in "), text)
        self.assertIn("1 pass, 1 fail", lines[0])
        self.assertIn("  WP1.1  pass  true", text)
        self.assertIn("  WP1.2  fail (exit 3)  echo nope-not-built; exit 3", text)
        self.assertIn("| nope-not-built", text)
        self.assertIn("--json", lines[-1])
        out = json.loads(self.printed(agent_loop.cmd_check, code=1, json=True, **kw))
        self.assertEqual([i["result"] for i in out["items"]], ["pass", "fail"])

    def test_r4_adopt_leaves_a_record_so_a_turned_away_run_names_it(self):
        self.draft()
        self.edit_w2()
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
        (empty / "ORCHESTRATE.md").write_text(PROFILE)  # the user's profile, waiting for adopt to land it
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
        self.edit_w2()
        self.assertEqual(self.adopt()["result"], "ADOPTED")
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design", commit=None)["verdict"], "DESIGN OK")
        second = self.calls()[-1]["argv"][-1]
        self.assertIn("Since the last design review (.orchestrate/evidence/WATER/design-review.md, at ", second)
        self.assertIn("these changed: WP2.1 changed.", second)
        before = {"work_packages": [work_package("WP1", "not_started", ["open", "open"]), work_package("WP2", "not_started", ["open"])]}
        after = {"work_packages": [work_package("WP1", "not_started", ["open"]), work_package("WP3", "not_started", ["open"])]}
        after["work_packages"][0]["quality_bar"] = "higher"
        self.assertEqual(agent_loop.changed_items(before, after),
                         ["WP1's quality_bar or depends_on changed", "WP1.2 removed", "WP3 added", "WP2 removed"])


    # Round five: the ladder's re-plan rung

    def test_r5_the_failed_review_that_owes_a_diagnosis_hands_every_surface_the_planners_command(self):
        self.write_done([failed_before(dict(work_package("WP1", "not_started", ["open"], inspect="frames"),
                                            failed_reviews_with_repeat=REPEATS - 1, failed_reviews=REPEATS - 1)),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual(claim["result"], "READY_FOR_REVIEW", claim)
        os.environ.update(FAKE_REVIEW="fail")
        failed = self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual((failed["failed_reviews_with_repeat"], failed["escalation"]), (REPEATS, "diagnosis"))
        self.assertEqual((failed["next"]["escalation"], failed["next"]["by"]), ("diagnosis", "lead"))
        self.assertIn(" plan --worktree ", failed["next"]["command"])
        self.assertIn("Diagnose WATER WP1", failed["next"]["command"])
        self.assertIn(".orchestrate/evidence/WATER/WP1-review.md", failed["next"]["command"])
        self.assertEqual(failed["next"]["findings"], ".orchestrate/evidence/WATER/WP1-review.md")
        # ready: not ready, owed a diagnosis, with the command
        r = self.ready()
        self.assertEqual(r["can_start"], [])
        self.assertEqual([(s["work_package"], s["reason"]) for s in r["waiting"]], [("WP1", "for_diagnosis")])
        self.assertEqual(r["waiting"][0]["next"]["command"], failed["next"]["command"])
        self.assertEqual(r["next"]["command"], failed["next"]["command"])
        # next: the planner's task, not the builder's findings
        nxt = json.loads(self.printed(agent_loop.cmd_next, module="WATER", work_package="WP1", worktree=str(self.wt)))
        self.assertEqual(nxt["action"], "diagnosis")
        self.assertTrue(nxt["message"].startswith("Diagnose WATER WP1"), nxt["message"])
        self.assertNotIn("set the state back to ready_for_review", nxt["message"])
        self.assertEqual(nxt["next"]["command"], failed["next"]["command"])
        # status says so, with the command
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        self.assertIn("WATER: waiting: for_diagnosis (WP1)", status)
        self.assertIn("a planner looks at it before any more building", status)
        self.assertIn("Diagnose WATER WP1", status)
        # run starts no builder
        before = len(self.calls())
        stopped = self.run_loop()
        self.assertEqual((stopped["result"], stopped["reason"]), ("WAITING", "for_diagnosis"), stopped)
        self.assertEqual(stopped["next"]["command"], failed["next"]["command"])
        self.assertEqual(len(self.calls()), before)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertIn("WATER WP1: waiting: for diagnosis", report)
        # once the planner has re-planned (its counts at 0, diagnoses 1), it's the builder's again
        doc = self.read_done()
        w1 = doc["work_packages"][0]
        w1.update(failed_reviews_with_repeat=0, failed_reviews=0, diagnoses=1, status="not_started")
        w1["items"][0]["statement"] = "a smaller first step"
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(doc)})["status"], "can_start")


    # Round six: the taste-led rerun

    # Round eighteen: the user decides in chat, and the lead records it

    def test_r18_a_block_on_human_feedback_tells_the_lead_what_to_ask_and_what_to_run(self):
        w1 = work_package("WP1", "not_started", ["open", "open"], inspect="frames")
        w1["items"][1]["needs"] = needs("human_feedback", "the user picks a direction")
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_NEEDS="1", FAKE_STATE="in_progress", FAKE_REPLY="BLOCKED: WP1.2 needs the user")
        blocked = self.run_loop()
        nxt = blocked["next"]
        self.assertEqual((blocked["result"], nxt["decides"]), ("BLOCKED", "human"), blocked)
        self.assertTrue(nxt["ask"].startswith("WP1.2: WP1.2 works (the user picks a direction). Evidence to show "
                                              "them: .orchestrate/evidence/WATER/"), nxt["ask"])
        self.assertIn("The builder's note: WP1.2 needs the user", nxt["ask"])
        self.assertIn(" human feedback --module WATER --work-package WP1 --item WP1.2 ", nxt["command"])
        self.assertIn("--said '<what the user said, in their words>'", nxt["command"])
        self.assertIn("Run it with the user's reply in --said", nxt["why"])
        self.assertNotIn("alternative", nxt)
        for text in (json.dumps(blocked), json.dumps(self.ready())):
            self.assertNotIn("terminal", text)
            self.assertNotIn("relay", text)
        self.git("pull", "-q", "--rebase", "origin", "main")
        answered = self.human("feedback", "WP1", "Direction B, the ink one.", item="WP1.2")
        self.assertEqual((answered["result"], answered["unblocked"]), ("DONE", True))
        rec = self.read_record()
        [d] = rec["decisions"]
        self.assertEqual((d["action"], d["work_package"], d["items"], d["words"]), ("feedback", "WP1", ["WP1.2"],
                                                                                "Direction B, the ink one."))
        self.assertNotIn("by", d)
        self.assertNotIn("by", rec["work_packages"]["WP1"]["human_feedback"][0])
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        section = report.split("## Decisions recorded in your name (check each is one you made)")[1]
        self.assertIn('- WATER WP1 WP1.2: feedback, ', section.split("\n## ")[0])
        self.assertIn('"Direction B, the ink one."', section.split("\n## ")[0])
        for key in ("FAKE_SKIP_NEEDS", "FAKE_STATE"):
            os.environ.pop(key)
        os.environ.update(FAKE_REPLY="DONE")
        claim = self.run_loop()
        self.assertIn("Direction B, the ink one.", self.calls()[-1]["argv"][-1])
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        self.assertIn("User Feedback on WP1", self.calls()[-1]["argv"][-1])

    def test_r18_every_verb_keeps_the_humans_words_and_report_lists_them(self):
        self.write_done([dict(too_many("WP1", ["open"]), failed_reviews_with_repeat=4), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(self.human("reopen", "WP1", "give it one more go")["result"], "DONE")
        self.assertEqual(self.human("accept", "design", "the design is fine")["result"], "DONE")
        released = self.human("release", "WP2", "that lead's machine is gone")
        self.assertEqual(released["result"], "RELEASED", released)
        rec = self.read_record()
        self.assertEqual([(d["action"], d["work_package"], d["words"]) for d in rec["decisions"]],
                         [("reopen", "WP1", "give it one more go"), ("accept", "design", "the design is fine"),
                          ("release", "WP2", "that lead's machine is gone")])
        self.assertEqual(rec["design"]["by"], "human decision")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        section = report.split("## Decisions recorded in your name")[1].split("\n## ")[0]
        for line in ('- WATER WP1: reopen, ', '"give it one more go"', '- WATER design: accept, ',
                     '- WATER WP2: release, '):
            self.assertIn(line, section)

    def test_r19_scope_with_nothing_changed_says_so(self):
        with self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_human(argparse.Namespace(action="scope", module="WATER", work_package="WP1", item=None,
                                                    text="keep it as it is", worktree=str(self.wt)))
        release()
        self.assertIn("nothing changed: docs/plans/WATER/DONE.json here has the same definitions as the tip",
                      str(stop.exception))
        self.assertNotIn("decisions", self.read_record())

    def test_r19_report_lists_planner_turns_with_their_tasks(self):
        self.plan(task="Plan PAY. The user said: \"card payments only, no PayPal\"")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        section = report.split("## Planner turns (with the task each was given)")[1].split("\n## ")[0]
        self.assertIn(', PAY: Plan PAY. The user said: "card payments only, no PayPal"', section)

    def test_r18_older_records_read_as_they_were_written_once_migrated(self):
        rec = json.loads((self.wt / "docs/plans/WATER/RECORD.json").read_text())
        at = agent_loop.now()
        w1 = rec["work_packages"]["WP1"]
        w1["owner"] = [{"by": "owner", "reason": "typo fix", "at": at, "action": "accept"}]
        w1["owner_answers"] = [{"by": "owner", "text": "Direction A", "at": at, "item": "WP1.1"},
                               {"by": "lead", "text": "Direction B", "at": at, "item": "WP1.1", "relayed": True}]
        rec["design"] = {"by": "owner", "reason": "fine as it is", "at": at, "verdict": "ok",
                         "hash": rec["design"]["hash"]}
        put(self.wt / "docs/plans/WATER/RECORD.json", json.dumps(rec))
        self.commit_all()
        self.assertEqual(self.migrate()["result"], "MIGRATED")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        section = report.split("## Decisions recorded in your name")[1].split("\n## ")[0]
        self.assertIn('- WATER WP1: accept, ', section)
        self.assertIn('"typo fix"', section)
        self.assertIn('- WATER WP1 WP1.1: feedback, ', section)
        self.assertIn('"Direction B"', section)
        self.assertIn('- WATER design: accept, ', section)
        feedback = self.read_record()["work_packages"]["WP1"]["human_feedback"]
        note = agent_loop.feedback_note(feedback, "WP1", "docs/plans/WATER/RECORD.json")
        self.assertLess(note.index("Direction A"), note.index("Direction B"), "oldest first")


    def test_r6_quota_counts_only_this_repositorys_work_packages(self):
        import test_codex_quota as fixtures
        now = fixtures.NOW
        elsewhere = self.root / "other-repo"
        elsewhere.mkdir()
        other = fixtures.Rollout(self.home, "o1", now - 10 * 3600, cwd=str(elsewhere), origin="codex_exec",
                                 source="exec", name="build WATER WP1")
        other.turn("t", now - 10 * 3600, now - 9 * 3600, [(now - 10 * 3600 + i * 600, 2_000_000, i) for i in range(1, 5)])
        mine = fixtures.Rollout(self.home, "h1", now - 8 * 3600, cwd=str(self.wt / "sub"), origin="codex_exec",
                                source="exec", name="thrum · WATER · WP2 build")
        mine.turn("t", now - 8 * 3600, now - 7 * 3600, [(now - 8 * 3600 + i * 600, 2_000_000, 10 + i)
                                                        for i in range(1, 5)])
        reading = agent_loop.codex_quota.read(budget_s=10, home=self.home, cache=False, now=now)
        own = agent_loop.loop_threads(self.wt, reading)
        self.assertEqual((own["o1"]["here"], own["h1"]["here"]), (False, True))
        acc = agent_loop.quota_report(self.wt, reading=reading)
        self.assertEqual([m["work_package"] for m in acc["work_packages"]], ["WP2"])

    def test_r6_report_lists_every_design_review_in_the_window(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        self.review("design", commit=None)
        self.revise_design()
        os.environ.update(FAKE_REVIEW="design")
        self.review("design", commit=None)
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        lines = [line for line in report.split("## Verdicts")[1].split("##")[0].splitlines()
                 if line.startswith("- WATER design:")]
        self.assertEqual(len(lines), 2, report)
        self.assertIn("changes", lines[0])
        self.assertIn(".orchestrate/evidence/WATER/design-review-1.md", lines[0])
        self.assertIn("ok", lines[1])
        self.assertIn(".orchestrate/evidence/WATER/design-review.md)", lines[1])
        # a record from before the history was kept still shows the kept review, from its file
        rec = json.loads(self.git("show", "origin/main:docs/plans/WATER/RECORD.json").stdout)
        rec.pop("design_history")
        prof = agent_loop.profile(self.wt)
        ref = self.git("rev-parse", "origin/main").stdout.strip()
        older = agent_loop.design_reviews(self.wt, prof, ref, "WATER", rec)
        self.assertEqual([d["review"] for d in older],
                         [".orchestrate/evidence/WATER/design-review-1.md", ".orchestrate/evidence/WATER/design-review.md"])

    # Round seven: the browser-game run

    def test_r7_a_block_with_another_cause_leads_and_the_report_still_lists_the_feedback_item(self):
        w1 = work_package("WP1", "not_started", ["open", "open"], inspect="frames")
        w1["items"][1]["needs"] = needs("human_feedback", "the user plays both and picks a direction")
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no browser starts here; WP1.2 needs the user's pick")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
        self.assertIn(" --message '<the missing fact>'", blocked["next"]["command"])  # the builder's cause leads
        r = self.ready()
        self.assertEqual(r["blocked"][0]["blocked"]["reason"], "needs_context")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        section = report.split("## Needs you now")[1].split("\n## ")[0]
        self.assertIn("- WATER WP1 WP1.2 (needs user feedback: the user plays both and picks a direction)", section)
        self.assertIn("Ask the user in chat; their reply goes in `", section)
        self.assertIn(" human feedback --module WATER --work-package WP1 --item WP1.2 ", section)

    def test_a_question_a_planner_answered_in_the_plan_resumes_the_builder_with_a_pointer(self):
        self.write_done([work_package("WP1", "not_started", ["open", "open"]), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED needs_context: which currency does the import use?")
        blocked = self.run_loop()
        self.assertEqual(blocked["reason"], "needs_context", blocked)
        self.git("pull", "-q", "--rebase", "origin", "main")
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# Water\n\nImports are in euros.\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "Plan: Unblock WATER WP1")
        self.git("push", "-q", "origin", "HEAD:main")
        step = next(b for b in self.ready()["blocked"] if b["module"] == "WATER")
        then = agent_loop.next_for(dict(step, status="blocked"), self.wt, agent_loop.profile(self.wt))
        self.assertIn("answered in the plan (Plan: Unblock WATER WP1)", then["command"])
        self.assertIn("--message", then["command"])

    def test_r7_a_builder_names_the_reason_it_is_blocked(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="Tried it.\nBLOCKED needs_dependency: CORE has no save API yet")
        blocked = self.run_loop()
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_dependency"), blocked)
        recorded = self.read_done()["work_packages"][0]["blocked"]
        self.assertEqual(recorded.pop("work")["branch"], "main")
        self.assertEqual(recorded, {"reason": "needs_dependency", "what": "CORE has no save API yet"})
        self.assertIn(" plan --worktree ", blocked["next"]["command"])
        os.environ.update(FAKE_REPLY="NEEDS_CONTEXT: which save slot?")
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.call(agent_loop.cmd_unblock, module="WATER", work_package="WP1", worktree=str(self.wt))
        again = self.run_loop()
        self.assertEqual((again["result"], again["reason"]), ("BLOCKED", "needs_context"), again)

    def test_r7_codex_in_workspace_write_is_warned_off_browser_work(self):
        self.assertEqual(agent_loop.browser_warnings(self.wt), [])
        profile = PROFILE + ("\n## Targets\n\n| Target | What it is | Run | Capture | Edge conditions |\n"
                             "|---|---|---|---|---|\n| web | Chromium, desktop | `npm run dev` | Playwright screenshots | resize |\n"
                             "| cli | the binary | `cargo run` | transcript | bad args |\n")
        (self.wt / "ORCHESTRATE.md").write_text(profile)
        doc = self.read_done("HEAD")
        doc["work_packages"][0]["items"][0]["target"] = "web"
        doc["work_packages"][1]["items"][0]["check"] = "npx playwright test"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        [warning] = agent_loop.browser_warnings(self.wt)
        self.assertIn("target web, WATER WP1.1, WATER WP2.1 need a browser", warning)
        self.assertNotIn("target cli", warning)
        self.assertNotIn("--host claude", warning)  # round eleven: never steer a lead off the user's host
        self.assertIn("has to ask to run it there", warning)
        self.assertNotIn("danger-full-access", warning)  # the lead grants the permission rather than widening the sandbox
        # N8: a run's warning names only the work package it builds, not 18 items from other modules
        [w1] = agent_loop.browser_warnings(self.wt, "WATER", "WP1")
        self.assertTrue(w1.startswith("WATER WP1.1 need a browser"), w1)
        self.assertIn(w1, agent_loop.preflight("codex", self.wt, "build", "WATER", "WP1"))
        self.assertEqual(agent_loop.browser_warnings(self.wt, "WATER", "WP3"), [])
        self.assertNotIn(w1, agent_loop.preflight("codex", self.wt, "plan"))
        prof = json.loads(self.printed(agent_loop.cmd_settings, worktree=str(self.wt), host="codex"))
        self.assertIn(warning, prof["preflight"]["warnings"])
        (self.wt / "ORCHESTRATE.md").write_text(profile.replace("**Default host:** codex",
                                                                "**Default host:** codex\n- **Codex sandbox:** danger-full-access"))
        self.assertEqual(agent_loop.browser_warnings(self.wt), [])

    # Round eight: the re-plan's bookkeeping, scope as a re-plan, and every review round kept

    def repeated_fails(self):
        """WATER WP1 after the failed review that makes REPEATS_TO_DIAGNOSE repeats, owed a diagnosis, with the last
        two reviews kept. Built once per process and copied back after that."""
        return self.restore("repeated-fails", self.build_repeated_fails)

    def build_repeated_fails(self):
        # three failed reviews so far, two short of the diagnosis in repeats; both rounds below repeat what failed
        # before
        self.write_done([failed_before(dict(work_package("WP1", "not_started", ["open"], inspect="frames"),
                                            failed_reviews_with_repeat=REPEATS - 2, failed_reviews=3)),
                         work_package("WP2", "not_started", ["open"])])
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

    @shares("repeated-fails")
    def test_r8_every_review_is_kept_and_named(self):
        failed = self.repeated_fails()
        self.assertEqual((failed["escalation"], failed["next"]["cause"]), ("diagnosis", "the same items or findings keep failing"))
        kept = [r.get("review") for r in self.read_record()["work_packages"]["WP1"]["reviews"]]
        self.assertEqual(kept, [".orchestrate/evidence/WATER/WP1-review-1.md", ".orchestrate/evidence/WATER/WP1-review.md"])
        self.assertTrue(self.evidence("WATER/WP1-review-1.md").exists())
        task = failed["next"]["command"]
        self.assertIn("Its reviews, oldest first: .orchestrate/evidence/WATER/WP1-review-1.md, "
                      ".orchestrate/evidence/WATER/WP1-review.md", task)
        self.assertNotIn("git log", task)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        self.assertIn("[.orchestrate/evidence/WATER/WP1-review-1.md]", report)

    @shares("repeated-fails")
    def test_r8_the_loop_does_the_replans_bookkeeping_once(self):
        for mode in ("replan", "replan_counted"):
            with self.subTest(mode=mode):
                self.setUp()
                self.repeated_fails()
                os.environ.update(FAKE_PLAN=mode)
                planned = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Diagnose WATER WP1", host=None,
                                    model=None, effort=None, turn_timeout_hours=0.1)
                self.assertEqual((planned["result"], planned["replanned"]), ("PLANNED", ["WATER WP1"]), planned)
                w1 = self.read_done()["work_packages"][0]
                self.assertEqual((w1["failed_reviews_with_repeat"], w1["failed_reviews"], w1["diagnoses"], w1["status"]),
                                 (0, 0, 1, "not_started"))
                self.assertNotEqual(agent_loop.next_step("WATER", agent_loop.read_project(
                    self.wt, agent_loop.profile(self.wt))[1]).get("reason"), "for_diagnosis")


    # A work package that keeps failing on something new: the round-six diagnosis

    def six_rounds(self, diagnoses=0):
        """WATER WP1 after its sixth failed review, only one of which repeated an earlier round's finding. Built once
        per process and copied back after that."""
        return self.restore(f"six-rounds-{diagnoses}", lambda: self.build_six_rounds(diagnoses))

    def build_six_rounds(self, diagnoses):
        self.write_done([dict(work_package("WP1", "not_started", ["open"], inspect="frames"), failed_reviews_with_repeat=1, failed_reviews=5,
                              diagnoses=diagnoses), work_package("WP2", "not_started", ["open"])])
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
        out = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Diagnose WATER WP1", host=None, model=None,
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
                         ("diagnosis", "lead", "reviews keep finding something new"))
        self.assertIn(" plan --worktree ", failed["next"]["command"])
        self.assertIn("Diagnose WATER WP1", failed["next"]["command"])
        self.assertIn("KEEP WATER WP1:", failed["next"]["command"])
        waiting = self.run_loop()
        self.assertEqual((waiting["result"], waiting["reason"]), ("WAITING", "for_diagnosis"), waiting)
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual(w1["findings"], [{"name": "the water is flat (WP1.1)", "item": "WP1.1", "repeat": False}])
        rnd = self.read_record()["work_packages"]["WP1"]["reviews"][-1]
        self.assertEqual((rnd["items"], rnd["findings"][0]["name"]), ({"WP1.1": "fail"}, "the water is flat (WP1.1)"))

    @shares("six-rounds-0")
    def test_a_diagnosis_that_changes_the_plan_is_a_replan(self):
        self.six_rounds()
        planned = self.diagnose("replan")
        self.assertEqual((planned["result"], planned["replanned"]), ("PLANNED", ["WATER WP1"]), planned)
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["failed_reviews_with_repeat"], w1["failed_reviews"], w1["diagnoses"], w1["status"]),
                         (0, 0, 1, "not_started"))
        self.assertNotIn("findings", w1)

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
                w1 = self.read_done()["work_packages"][0]
                self.assertEqual((w1["failed_reviews_with_repeat"], w1["failed_reviews"], w1["diagnoses"]), (0, 0, 1))
                self.assertEqual(w1["status"], "blocked" if who == "human" else "in_progress")
                e = self.read_record()["work_packages"]["WP1"]
                self.assertEqual(e["diagnoses"][-1]["who"], who)
                self.assertEqual(e["counted_from"], e["diagnoses"][-1]["at"])
                if who == "human":
                    self.assertTrue(kept["next"]["ask"])
                    self.assertTrue(kept["next"]["history"])
                    # every later readout gives the planner's reason and the rounds it read
                    later = agent_loop.next_for({"module": "WATER", "work_package": "WP1", "status": "blocked",
                                                 "reason": "too_many_failed_reviews"}, self.wt,
                                                agent_loop.profile(self.wt))
                    self.assertIn(f"the {who} has to act", later["ask"])
                    self.assertEqual(later["history"], kept["next"]["history"])
                    nxt = json.loads(self.printed(agent_loop.cmd_next, module="WATER", work_package="WP1",
                                                  worktree=str(self.wt)))
                    self.assertEqual(nxt["action"], "too_many_failed_reviews")
                    continue
                self.assertEqual(self.run_loop(fresh=True, message="FINDINGS")["result"], "READY_FOR_REVIEW")
                os.environ.update(FAKE_REVIEW="fail")
                again = self.review()
                os.environ.pop("FAKE_REVIEW")
                prompt = self.calls()[-1]["argv"][-1]
                told = "diagnosis on" in prompt and "kept WP1's items as written" in prompt
                self.assertEqual(told, who == "reviewer")
                # the rounds before the diagnosis no longer count: the same finding isn't a repeat
                self.assertEqual((again["failed_reviews_with_repeat"], again["failed_reviews"], again["repeated"]), (0, 1, []), again)

    @shares("repeated-fails")
    def test_a_kept_plan_after_repeated_findings_counts_as_the_diagnosis(self):
        failed = self.repeated_fails()
        self.assertIn("KEEP WATER WP1:", failed["next"]["command"])
        self.assertNotIn("the plan is wrong", failed["next"]["command"])
        kept = self.diagnose("keep_builder")
        self.assertEqual((kept["result"], kept["who"], kept["next"]["by"]), ("KEPT", "builder", "lead"), kept)
        self.assertIn("--fresh", kept["next"]["command"])
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["failed_reviews_with_repeat"], w1["failed_reviews"], w1["diagnoses"], w1["status"]),
                         (0, 0, 1, "in_progress"))
        # the same repeated failures a second time go to the user, as they do after a re-plan
        self.assertEqual(agent_loop.escalation_of(dict(w1, failed_reviews=REPEATS, failed_reviews_with_repeat=REPEATS)),
                         "too_many_failed_reviews")

    def test_keep_is_refused_when_no_diagnosis_is_owed(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        refused = self.diagnose("keep_reviewer")  # a KEEP for the builder is the answer to a run that stopped
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("isn't owed a diagnosis", refused["problems"][0])

    @shares("six-rounds-1")
    def test_the_same_counts_after_a_diagnosis_block_it_with_each_reviews_failures(self):
        stuck = self.six_rounds(diagnoses=1)
        self.assertEqual((stuck["escalation"], stuck["next"]["decides"]), ("too_many_failed_reviews", "human"), stuck)
        self.assertEqual(self.read_done()["work_packages"][0]["blocked"]["reason"], "too_many_failed_reviews")
        self.assertTrue(any("the water is flat (WP1.1)" in h for h in stuck["next"]["history"]), stuck["next"])
        for verb in ("Accept it", "change its scope", "reopen it"):
            self.assertIn(verb, stuck["next"]["ask"])
        # the user reopens it: the counts start again, and the earlier rounds no longer count as repeats
        self.assertEqual(self.human("reopen", "WP1", "one more go")["result"], "DONE")
        self.git("pull", "-q", "--rebase", "origin", "main")
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["status"], w1["failed_reviews_with_repeat"], w1["failed_reviews"], w1["diagnoses"]), ("in_progress", 0, 0, 0))
        self.assertTrue(self.read_record()["work_packages"]["WP1"]["counted_from"])
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        again = self.review(commit=claim["commit"])
        self.assertEqual((again["failed_reviews_with_repeat"], again["failed_reviews"], again["escalation"]), (0, 1, "same_builder"), again)

    def test_a_failure_says_how_it_differs_or_counts_as_a_repeat(self):
        self.write_done([dict(work_package("WP1", "not_started", ["open"], inspect="frames")), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_REVIEW="fail")
        results = []
        for n, (name, different) in enumerate((("flat", ""), ("seams", ""), ("foam", "seams fixed; foam is new"))):
            os.environ.update(FAKE_FINDING=name, FAKE_DIFFERENT=different)
            os.environ.pop("FAKE_REVIEW")
            claim = self.run_loop(**({"message": "FINDINGS"} if n else {}))
            os.environ.update(FAKE_REVIEW="fail")
            results.append(self.review(commit=claim["commit"]))
        # round 2 fails the same item with a new name and no `different`: a repeat; round 3 says how the finding
        # differs, which keeps the finding new, but the same item failed again, so the review still counts as a repeat
        self.assertEqual([(r["failed_reviews_with_repeat"], r["failed_reviews"]) for r in results], [(0, 1), (1, 2), (2, 3)])
        self.assertEqual((results[2]["repeated"], results[2]["repeated_items"]), ([], ["WP1.1"]))
        self.assertEqual(results[2]["escalation"], "new_builder_session")

    def test_a_pass_after_a_failed_review_clears_the_findings(self):
        self.write_done([dict(work_package("WP1", "not_started", ["open"], inspect="frames")), work_package("WP2", "not_started", ["open"])])
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
        self.assertNotIn("findings", self.read_done()["work_packages"][0])
        # the second reviewer is told where the first round is kept, and not what it found, so it judges the items first
        prompt = self.calls()[prompt_before]["argv"][-1]
        self.assertIn("WP1 has failed review 1 time since the script last started counting", prompt)
        self.assertIn(".orchestrate/evidence/WATER/WP1-review.md", prompt)
        self.assertIn("docs/plans/WATER/RECORD.json under work_packages.WP1.reviews", prompt)
        self.assertNotIn("the water is flat", prompt)


    @shares("six-rounds-1")
    def test_human_scope_restarts_the_counts_and_unblocks_it(self):
        self.six_rounds(diagnoses=1)
        doc = self.read_done("HEAD")
        doc["work_packages"][0]["items"][0]["statement"] = "what the user wants now"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        self.assertEqual(self.human("scope", "WP1")["result"], "DONE")
        self.git("pull", "-q", "--rebase", "origin", "main")
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["status"], w1["failed_reviews_with_repeat"], w1["failed_reviews"], w1["diagnoses"]), ("not_started", 0, 0, 0))
        self.assertNotIn("findings", w1)

    def test_a_review_must_list_its_findings_on_a_fail_and_none_on_a_pass(self):
        with self.subTest("a fail with no findings is refused"):
            commit = self.ready_for_review()
            os.environ.update(FAKE_NO_FINDINGS="1", FAKE_REVIEW="fail")
            bad = self.review(commit=commit)
            self.assertEqual(bad["result"], "INVALID", bad)
            self.assertIn("the last line says FAIL, but findings is empty; list each Must Fix with a short name",
                          bad["problems"])
            self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")
        with self.subTest("a pass merges with no findings, whatever the reviewer listed"):
            self.setUp()
            commit = self.ready_for_review()
            os.environ.update(FAKE_PASS_FINDINGS="1", FAKE_REVIEW="pass")
            passed = self.review(commit=commit)
            self.assertEqual((passed["result"], passed["verdict"]), ("REVIEWED", "PASS"), passed)
            w1 = self.read_done()["work_packages"][0]
            self.assertEqual(w1["status"], "done")
            self.assertNotIn("findings", w1)

    @shares("repeated-fails")
    def test_r8_human_scope_on_an_owed_work_package_leaves_nothing_to_diagnose(self):
        self.repeated_fails()
        doc = self.read_done("HEAD")
        doc["work_packages"][0]["items"][0]["statement"] = "what the user wants now"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        scoped = self.human("scope", "WP1")
        self.assertEqual((scoped["result"], scoped["replanned"]), ("DONE", ["WP1"]), scoped)
        self.assertIn("nothing is left to diagnose", scoped["replanned_why"])
        w1 = self.read_done()["work_packages"][0]
        self.assertEqual((w1["failed_reviews_with_repeat"], w1["diagnoses"], w1["status"]), (0, 0, "not_started"))


    # Round nine: the second whole-change review

    def feedback_w1(self, state="blocked", result="open"):
        w1 = work_package("WP1", state, ["open", result], inspect="frames")
        w1["items"][1]["needs"] = needs("human_feedback", "the user picks a direction")
        if state == "blocked":
            w1["blocked"] = {"reason": "needs_human_feedback", "items": ["WP1.2"], "what": "WP1.2 needs the user"}
        self.write_done([w1, work_package("WP2", "not_started", ["open"])])
        self.commit_all()

    def test_r9_human_decisions_are_refused_while_the_module_is_held(self):
        self.feedback_w1()
        for name, role, says in (("WATER", "review", "a run, review or design review holds WATER"),):
            code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop\n"
                    f"from pathlib import Path; wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, {name!r})\n"
                    f"agent_loop.loop_register(wt, {role!r}, module='WATER', work_package='WP1', host='codex', "
                    "model='m', effort='medium'); print('up', flush=True); time.sleep(60)\n")
            proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(proc.stdout.readline().strip(), "up")
                messages = []
                for verb in ("feedback", "accept", "release"):
                    with self.assertRaises(SystemExit) as stop:
                        agent_loop.cmd_human(argparse.Namespace(
                            action=verb, module="WATER", work_package="WP1", item=["WP1.2"] if verb == "feedback" else None,
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
        self.assertEqual(self.human("feedback", "WP1", "Direction B.", item="WP1.2")["result"], "DONE")  # once free

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
        self.edit_w2()
        refused = self.adopt()
        self.assertEqual(refused["result"], "REFUSED", refused)
        self.assertIn("a design review of it has passed, so they're no longer a draft", refused["problems"][0])

    def test_a_lock_change_keeps_progress_and_owes_no_design_review(self):
        self.write_done([work_package("WP1", "in_progress", ["pass", "open"]), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        rec = self.read_record()
        self.assertTrue(agent_loop.design_passed(rec))
        doc = self.read_done("HEAD")
        doc["work_packages"][0]["items"][0]["lock"] = "gpu"
        doc["work_packages"][0]["items"][1]["reads"] = ["src/"]
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        after, rec = self.read_done(), self.read_record()
        w1 = after["work_packages"][0]
        self.assertEqual((w1["status"], w1["items"][0]["builder_result"]), ("in_progress", "pass"))
        self.assertEqual(rec["work_packages"]["WP1"]["definitions"], agent_loop.definitions(w1))
        self.assertEqual(rec["work_packages"]["WP1"]["run_changes"][0]["by"], "adopt")
        self.assertEqual(agent_loop.changed_items(self.read_done("HEAD~1"), after), [])
        # a change to what an item proves is still refused once the design has passed
        self.edit_w2()
        self.assertEqual(self.adopt()["result"], "REFUSED")

    def test_a_replan_that_changes_a_blocked_work_package_lifts_a_block_a_planner_answers(self):
        stamp = {"by": "plan"}
        for reason, lifted in (("needs_dependency", True), ("needs_context", True), ("needs_access", False)):
            m = work_package("WP1", "blocked", ["open"])
            m["blocked"] = {"reason": reason, "what": "the cooker publishes edits"}
            record = {"work_packages": {"WP1": {"definitions": agent_loop.definitions(m), "reviews": []}}}
            before = {"work_packages": [json.loads(json.dumps(m))]}
            m["depends_on"] = ["CONTENT-LOOP:WP2"]  # the planner put the missing part where it belongs
            agent_loop.authorise_doc({"work_packages": [m]}, record, stamp, before=before)
            self.assertEqual((m["status"], "blocked" in m), ("not_started", False) if lifted else ("blocked", True),
                             reason)
            self.assertEqual(record["work_packages"]["WP1"]["definitions"], agent_loop.definitions(m))

    def test_reads_leaves_older_definition_hashes_unchanged(self):
        m = work_package("WP1", "not_started", ["open"])
        before = agent_loop.definitions(m)
        self.assertEqual(agent_loop.definitions(json.loads(json.dumps(m))), before)
        m["items"][0]["reads"] = ["src/"]
        self.assertNotEqual(agent_loop.definitions(m), before)
        self.assertEqual(agent_loop.run_free_definitions(m),
                         agent_loop.run_free_definitions(work_package("WP1", "not_started", ["open"])))

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
        self.assertIn(" review --module WATER --work-package design ", stale["next"]["command"])
        rec = self.read_record()
        self.assertFalse(agent_loop.design_passed(rec))
        self.assertIn("not_counted", rec["design_history"][-1])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertEqual(self.ready()["design_not_approved"], [{"module": "WATER"}])

    def test_r9_each_kept_round_keeps_its_captures(self):
        os.environ.update(FAKE_CAPTURE="1")
        self.repeated_fails()
        self.git("fetch", "-q", "origin")
        self.assertNotIn("shot.png", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)
        self.assertEqual(self.evidence("WATER/WP1-review-1/shot.png").read_text(), "PNG 4")
        self.assertEqual(self.evidence("WATER/WP1-review/shot.png").read_text(), "PNG 5")
        kept = self.evidence("WATER/WP1-review-1.md").read_text()
        self.assertIn("(WP1-review-1/shot.png)", kept)
        self.assertIn("(WP1-review/shot.png)", self.evidence("WATER/WP1-review.md").read_text())

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
        # only a fast-forward is the lead's to run alone; a rebase of the branch's own commits waits for the user
        self.assertEqual((split["next"]["decides"], shlex.split(split["next"]["command"])[3:]),
                         ("human", ["rebase", "origin/main"]))
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

    def test_r9_waiting_planners_go_in_the_order_they_were_started(self):
        common = agent_loop.git_common_dir(self.wt)
        self.loops.mkdir(parents=True, exist_ok=True)
        held = []
        for pid, started, task in ((90002, 200.0, "Plan the later module"), (90001, 100.0, "Plan the first module"),
                                   (90003, 50.0, None)):
            held.append(agent_loop.take_file_lock(self.loops / f"{pid}.lock"))
            record = {"pid": pid, "role": "plan", "git_dir": common, "started_at": started, "task": task,
                      "waiting_for": "another planner" if task else None}  # 90003 holds the lock, it isn't waiting
            (self.loops / f"{pid}.json").write_text(json.dumps(record))
        self.addCleanup(lambda: [h.close() for h in held])
        self.assertEqual([r["pid"] for r in agent_loop.planners_waiting(self.wt)], [90001, 90002])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_status(argparse.Namespace(module=None, worktree=str(self.wt)))
        status = out.getvalue()
        self.assertLess(status.index("1 in line: Plan the first module"), status.index("2 in line: Plan the later module"))

    def test_r9_settings_merely_behind_the_tip_are_read_from_the_tip(self):
        behind = self.root / "behind"
        self.sh("git", "clone", "-q", str(self.origin), str(behind))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** high\n")
        self.commit_all()
        self.git("fetch", "-q", "origin", where=behind)
        agent_loop.EMIT_EXTRA.clear()
        self.assertEqual(agent_loop.profile(behind)["effort"], "high")  # the tip's, though this copy is older
        self.assertIn("origin/main", agent_loop.EMIT_EXTRA["settings_read_from"])
        self.assertNotIn("high", (behind / "ORCHESTRATE.md").read_text())  # nothing here is rewritten
        (behind / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** low\n")
        self.assertEqual(agent_loop.profile(behind)["effort"], "low")  # an edit of its own is read as it is
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "mine", where=behind)
        self.assertEqual(agent_loop.profile(behind)["effort"], "low")  # and so is a commit of its own


    # Round ten: two modules built at once

    def test_r15_a_planner_that_catches_up_with_loop_commits_still_lands(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        # another module's claim (with the loop's trailer) lands mid-turn, and the planner fast-forwards to it: that
        # commit is on the tip and isn't the planner's work, so the turn lands what it left uncommitted
        os.environ.update(FAKE_PLAN="catch_up", FAKE_DURING=(
            f"cd {other} && echo '{{}}' > docs/plans/WATER/RECORD.json && git add -A && "
            f"git -c user.name=t -c user.email=t@t commit -qm 'orchestrate: claim WATER WP1' -m '{agent_loop.TRAILER}' "
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
        return (f"cd {other} && echo '{{\"forged\": true}}' > docs/plans/WATER/RECORD.json && git add -A && "
                "git -c user.name=t -c user.email=t@t commit -qm 'tidy records' && git push -q origin main")

    def test_r15_a_record_forged_elsewhere_during_a_planner_turn_refuses_it(self):
        os.environ.update(FAKE_DURING=self.forge_on_tip())
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("without the script's trailer changed", refused["problems"][0])
        self.assertEqual((shlex.split(refused["next"]["command"])[3:5], refused["next"]["by"],
                          refused["next"]["decides"]), (["revert", "--no-edit"], "lead", "human"))
        self.assertNotIn("docs/plans/PAY/DONE.json",
                         self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split())
        self.assertIn("docs/plans/PAY/DONE.json", refused["set_aside"])  # kept in a stash, for the user

    def test_r15_a_record_forged_during_a_review_refuses_it(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        claimed = self.run_loop()
        self.assertEqual((claimed["result"], claimed["review"]), ("READY_FOR_REVIEW", True), claimed)
        os.environ.update(FAKE_DURING=self.forge_on_tip())
        refused = self.review(commit=claimed["commit"])
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("without the script's trailer changed", refused["problems"][0])
        # the revert is the user's to approve, since the commits are already on the tip
        self.assertEqual((shlex.split(refused["next"]["command"])[3:5], refused["next"]["decides"]),
                         (["revert", "--no-edit"], "human"))
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")  # no verdict was recorded

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
        self.assertIn("docs/plans/PAY/RECORD.json", files)

    # Round sixteen: a module the loop has no record for is new once any record exists; planner commits are refused

    SHIP = ("import json, os, sys\n"
            "d = sys.argv[1]\n"
            "os.makedirs(d + '/docs/plans/SHIP', exist_ok=True)\n"
            "json.dump({'module': 'SHIP', 'work_packages': [{'id': 'WP1', 'name': 'ship', 'status': 'done', 'failed_reviews': 0,"
            " 'diagnoses': 0, 'items': [{'id': 'WP1.1', 'statement': 'ships', 'check': 'true', 'builder_result': 'pass',"
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
        self.write_done([work_package("WP1", "not_started", ["open"])], where=main)  # a record: the loop is in use here
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
        self.assertIn("refused because you committed", shlex.split(refused["next"]["command"])[-1])  # plan again
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
        rec = json.loads(self.git("show", "origin/main:docs/plans/SHIP/RECORD.json").stdout)
        self.assertNotIn("done", rec["work_packages"]["WP1"])
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
        rec = json.loads(self.git("show", "main:docs/plans/SHIP/RECORD.json", where=main).stdout)
        self.assertNotIn("done", rec["work_packages"]["WP1"])
        self.assert_ship_is_new(main)

    def test_r16_a_reviewer_that_commits_is_refused(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        claimed = self.run_loop()
        self.assertEqual((claimed["result"], claimed["review"]), ("READY_FOR_REVIEW", True), claimed)
        os.environ.update(FAKE_DURING="git -c user.name=t -c user.email=t@t commit -q --allow-empty -m habit")
        refused = self.review(commit=claimed["commit"])
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("the reviewer committed in its checkout", refused["problems"][0])
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")

    def test_r16_a_repository_with_no_records_still_adopts_modules_as_they_stand(self):
        origin, wt = self.root / "legacy.git", self.root / "legacy"
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(origin))
        self.sh("git", "init", "-q", "-b", "main", str(wt))
        (wt / "docs/plans").mkdir(parents=True)
        (wt / "ORCHESTRATE.md").write_text(PROFILE)
        self.write_done([work_package("WP1", "done", ["pass"]), work_package("WP2", "not_started", ["open"])], authorise=False,
                        where=wt)
        self.git("add", "-A", where=wt)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "work already done", where=wt)
        self.git("remote", "add", "origin", str(origin), where=wt)
        self.git("push", "-q", "origin", "main", where=wt)
        prof = agent_loop.profile(wt)
        self.assertTrue(agent_loop.unrecorded(wt, prof, "origin/main"))
        r = self.ready(where=wt)
        self.assertEqual([(x["module"], x["work_package"]) for x in r["can_start"]], [("WATER", "WP2")], r)
        # the loop's first record-keeping commit (here, a plan's) writes WATER's record as it was taken
        planned = self.plan(worktree=str(wt))
        self.assertEqual(planned["result"], "PLANNED", planned)
        rec = json.loads(self.git("show", "origin/main:docs/plans/WATER/RECORD.json", where=wt).stdout)
        self.assertEqual(rec["work_packages"]["WP1"]["done"], {"by": "adopted"})
        self.assertFalse(agent_loop.unrecorded(wt, prof, "origin/main"))
        self.git("pull", "-q", "--rebase", "origin", "main", where=wt)
        r = self.ready(where=wt)
        self.assertEqual([(x["module"], x["work_package"]) for x in r["can_start"]], [("WATER", "WP2")], r)
        self.assertIn({"module": "PAY"}, r["design_not_approved"])
        # once a record has existed, deleting every record doesn't bring adoption as it stands back
        self.git("rm", "-q", "docs/plans/WATER/RECORD.json", "docs/plans/PAY/RECORD.json", where=wt)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "drop records", where=wt)
        self.assertFalse(agent_loop.unrecorded(wt, prof, "HEAD"))

    # Round seventeen: a design review goes to the host that didn't plan it, decided once; planners get the loop path

    def test_r17_a_design_review_goes_to_the_host_that_didnt_plan_it_everywhere(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([too_many("WP1", ["open"])])  # nothing of WATER's is ready
        self.commit_all()
        planned = self.plan(host="claude")
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertTrue(planned["next"]["command"].endswith("--host codex"), planned["next"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        rec = json.loads(self.git("show", "origin/main:docs/plans/PAY/RECORD.json").stdout)
        self.assertEqual(rec["planner"]["host"], "claude")
        r = self.ready()
        self.assertIn(" review --module PAY --work-package design ", r["next"]["command"])
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
        self.write_done([too_many("WP1", ["open"])])
        self.commit_all()
        planned = self.plan(host="claude")
        self.assertTrue(planned["next"]["command"].endswith("--host claude"), planned["next"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertNotIn("--host", self.ready()["next"]["command"])

    def test_r17_planners_get_the_loop_path_and_dont_hunt_for_host_clis(self):
        self.plan()
        prompt = [c for c in self.calls() if c["role"] == "plan"][0]["argv"][-1]
        self.assertIn(f"The script is `python3 {agent_loop.LOOP}`. Its `check --module <M> --work-package <id> "
                      "--worktree . --items-only` command", prompt)
        self.assertNotIn("PATH", prompt, "the note about host programs on PATH was cut: no planner ever met it")

    def test_r10_everything_a_planner_writes_lands_with_its_plan(self):
        os.environ.update(FAKE_PLAN="catch_up")  # nothing new on the tip, so the fast-forward moves nothing
        planned = self.plan()
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertIn("acceptance/test_pay.py", files)


    def test_a_plan_that_changes_files_outside_the_plans_merges_only_when_the_test_command_passes(self):
        profile = (self.wt / "ORCHESTRATE.md").read_text()
        (self.wt / "ORCHESTRATE.md").write_text(profile.replace("- **Test command:** none", "- **Test command:** test ! -d acceptance"))
        self.commit_all()
        os.environ.update(FAKE_PLAN="catch_up")  # it writes acceptance/test_pay.py, which the test command fails on
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("PLAN_NOT_MERGED", False), refused)
        self.assertIn("test ! -d acceptance", refused["problems"][0])
        os.environ.pop("FAKE_PLAN")
        planned = self.plan()  # plan files alone run nothing
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)

    def test_a_plan_on_a_main_branch_broken_on_its_own_is_kept_and_lands_later_without_a_planner(self):
        profile = (self.wt / "ORCHESTRATE.md").read_text()
        (self.wt / "ORCHESTRATE.md").write_text(profile.replace("- **Test command:** none", "- **Test command:** test ! -f broken"))
        put(self.wt / "broken", "a test that fails\n")
        self.commit_all()
        os.environ.update(FAKE_PLAN="catch_up")  # it writes acceptance/test_pay.py, outside the plans
        waiting = self.plan()
        self.assertEqual((waiting["result"], waiting["merged"]), ("PLAN_NOT_MERGED", False), waiting)
        self.assertIn("main_broken", waiting)
        self.assertIn("--merge-kept orchestrate/planner-", waiting["merge_kept_later"])
        self.assertEqual(agent_loop.main_broken(self.wt)[0]["check"], "test command")
        os.environ.pop("FAKE_PLAN")
        self.git("rm", "-q", "broken")
        self.commit_all()
        calls = len(self.calls())
        planned = self.plan(merge_kept=waiting["branch"])
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        self.assertEqual(len(self.calls()), calls, "no planner turn")
        self.assertIn("acceptance/test_pay.py", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)

    def test_the_main_branch_fails_on_its_own_only_when_a_retry_fails_too_and_never_by_a_settings_commit(self):
        flag = self.root / "flaked"
        prof = {**agent_loop.profile(self.wt), "test_command": f"test -f {flag} || {{ touch {flag}; exit 1; }}"}
        base = agent_loop.head_commit(self.wt)
        self.assertIsNone(agent_loop.broken_base(agent_loop.verify_tree(self.wt, agent_loop.BATCH_TREE, base), prof,
                                                 base), "a failure that passes on its retry is a flake")
        put(self.wt / "broken", "x\n")
        self.commit_all()
        breaking = agent_loop.head_commit(self.wt)
        (self.wt / "ORCHESTRATE.md").write_text((self.wt / "ORCHESTRATE.md").read_text() + "\n")
        self.commit_all()
        base = agent_loop.head_commit(self.wt)
        prof = {**agent_loop.profile(self.wt), "test_command": "test ! -f broken"}
        broken = agent_loop.broken_base(agent_loop.verify_tree(self.wt, agent_loop.BATCH_TREE, base), prof, base)
        self.assertEqual(broken["culprit"]["commit"], breaking, broken)
        self.assertFalse(agent_loop.changes_code(prof, ["ORCHESTRATE.md", "docs/plans/STATUS.md"]))
        self.assertTrue(agent_loop.changes_code(prof, ["ORCHESTRATE.md", "src/a.txt"]))

    def test_a_planner_limited_to_a_module_merges_only_that_modules_files(self):
        planned = self.plan(module="PAY")
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        os.environ.update(FAKE_PLAN="replan")  # it re-plans WATER, which a PAY planner leaves to WATER's planners
        refused = self.plan(module="PAY", task="re-plan PAY")
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("limited to PAY", refused["problems"][-1])
        self.assertNotIn("--module", refused["next"]["command"])  # the task goes to a planner for the whole project

    def test_a_plan_that_conflicts_with_a_builders_results_in_the_same_file_still_merges(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        # the builder ticks an item and writes its log entry, while the planner re-plans and logs too
        tick = ("import json; p = 'docs/plans/WATER/DONE.json'; d = json.load(open(p)); "
                "d['work_packages'][0]['items'][0]['evidence'] = 'ev/log.txt'; json.dump(d, open(p, 'w')); "
                "open('docs/plans/WATER/LOG.md', 'a').write('builder entry\\n')")
        os.environ.update(FAKE_PLAN="replan", FAKE_DURING=(
            f"cd {other} && python3 -c \"{tick}\" && git add -A && "
            "git -c user.name=t -c user.email=t@t commit -qm 'WATER WP1: tick' && git push -q origin main"))
        os.environ.update(FAKE_PLAN_LOG="planner entry\n")
        planned = self.plan(task="re-plan WATER WP1")
        self.assertEqual((planned["result"], planned["merged"]), ("PLANNED", True), planned)
        log = self.git("show", "origin/main:docs/plans/WATER/LOG.md").stdout
        self.assertIn("builder entry", log)
        self.assertIn("planner entry", log)

    def test_a_run_keeps_its_builder_slot_through_a_review(self):
        loops = [{"pid": 1, "role": "steps", "module": "WATER"}, {"pid": 2, "role": "review", "steps_parent": 1},
                 {"pid": 3, "role": "steps", "module": "SKY"}, {"pid": 4, "role": "build", "steps_parent": 3},
                 {"pid": 7, "role": "build", "module": "ROCK"}, {"pid": 8, "role": "build", "checks_only": True}]
        # the run under review keeps its slot, for the fix half of reviews need; a checks-only run needs none
        self.assertEqual([r["pid"] for r in agent_loop.builder_runs(loops)], [1, 3, 7])
        loops.append({"pid": 9, "role": "build", "step": agent_loop.WAITING_FOR_SLOT, "waiting_since": 2.0})
        loops.append({"pid": 10, "role": "build", "step": agent_loop.WAITING_FOR_SLOT, "waiting_since": 1.0})
        self.assertEqual([r["pid"] for r in agent_loop.slot_waiters(loops)], [10, 9])

    def test_design_reviews_after_a_plan_go_past_a_module_whose_run_is_going(self):
        steps = {"origin": "plan", "worktree": "w", "owed": ["SKY"], "changes": {}, "last_run": None}
        words, _ = agent_loop.routine_next({"result": "IN_PROGRESS_ELSEWHERE", "module": "WATER",
                                            "work_package": "design"}, steps)
        self.assertEqual(words[:3], ["review", "--module", "SKY"])
        words, why = agent_loop.routine_next({"result": "REVIEWED", "verdict": "DESIGN OK", "module": "SKY",
                                              "work_package": "design"}, steps)
        self.assertIsNone(words)
        self.assertIn("WATER had a run going", why)

    def test_a_field_merge_keeps_what_each_side_changed(self):
        base = {"work_packages": [{"id": "WP1", "name": "a", "items": [{"id": "WP1.1", "statement": "s", "evidence": ""}]}]}
        ours = {"work_packages": [{"id": "WP1", "name": "b", "items": [{"id": "WP1.1", "statement": "s", "evidence": ""}]},
                               {"id": "WP2", "name": "new", "items": []}]}
        theirs = {"work_packages": [{"id": "WP1", "name": "a", "items": [{"id": "WP1.1", "statement": "s",
                                                                      "evidence": "log"}]}]}
        merged = agent_loop.merge_fields(base, ours, theirs)
        self.assertEqual([m["name"] for m in merged["work_packages"]], ["b", "new"])
        self.assertEqual(merged["work_packages"][0]["items"][0]["evidence"], "log")

    def test_planners_of_different_modules_run_side_by_side_and_a_whole_project_planner_waits(self):
        folder = agent_loop.loop_dir(self.wt)
        (folder / "run-_plan.SKY.lock").write_text("12345")
        real = agent_loop.run_holder
        agent_loop.run_holder = lambda f, name: 12345 if name == "_plan.SKY" else real(f, name)
        try:
            self.assertTrue(agent_loop.take_plan_lock(self.wt, "WATER"))
            agent_loop.release_run_lock(self.wt, "_plan.WATER")
            self.assertEqual(agent_loop.module_planners(self.wt), ["SKY"])
            self.assertFalse(agent_loop.take_plan_lock(self.wt, None), "a whole-project planner waits for SKY's")
        finally:
            agent_loop.run_holder = real
            agent_loop.release_run_lock(self.wt, "_plan")
        self.assertTrue(agent_loop.plans_clash("SKY", "sky") and agent_loop.plans_clash(None, "SKY"))
        self.assertFalse(agent_loop.plans_clash("SKY", "WATER"))

    def test_r13_a_planner_that_lands_a_forged_record_itself_is_refused(self):
        os.environ.update(FAKE_PLAN_SIDE="push")
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("without the script's trailer changed", refused["problems"][0])
        # the user decides what happens to a commit already on the tip: the revert runs only on their yes
        self.assertEqual((shlex.split(refused["next"]["command"])[3:5], refused["next"]["by"],
                          refused["next"]["decides"]), (["revert", "--no-edit"], "lead", "human"))
        self.assertTrue(refused["next"]["ask"])

    def test_r13_a_planner_that_fakes_the_tracking_ref_is_refused(self):
        os.environ.update(FAKE_PLAN_SIDE="ref")
        refused = self.plan()
        self.assertEqual((refused["result"], refused["merged"]), ("INVALID", False), refused)
        self.assertIn("the planner committed (", refused["problems"][0])
        self.assertIn("tidy", refused["problems"][0])
        self.assertEqual((shlex.split(refused["next"]["command"])[2], refused["next"]["by"]), ("plan", "lead"))
        self.assertTrue(refused["branch"].startswith("orchestrate/planner-"))  # its commit is kept, not landed
        self.assertNotIn("forged", self.git("show", "origin/main:docs/plans/WATER/RECORD.json").stdout)
        # the next plan lands nothing of it
        os.environ.pop("FAKE_PLAN_SIDE")
        planned = self.plan()
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertNotIn("forged", self.git("show", "origin/main:docs/plans/WATER/RECORD.json").stdout)

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
        self.assertIn("docs/plans/WATER/RECORD.json",
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
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames"), work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual((claim["result"], claim["review"]), ("READY_FOR_REVIEW", True), claim)
        self.assertIn(f" review --module WATER --work-package WP1 --commit {claim['commit']} ", claim["next"]["command"])
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
        review = agent_loop.loop_cmd("review", "--module", "WATER", "--work-package", "WP1", "--commit", "abc",
                                     "--worktree", str(self.wt))
        self.assertEqual(agent_loop.fit_command(review), review)  # `review` takes the builder from the claim
        design = agent_loop.fit_command(agent_loop.loop_cmd("review", "--module", "WATER", "--work-package", "design",
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
            agent_loop.emit("DONE", next=agent_loop.next_cmd(agent_loop.loop_cmd("ready", "--worktree", str(self.wt)),
                                                             "lead", "x", then=agent_loop.loop_cmd(
                "run", "--module", "WATER", "--worktree", str(self.wt))))
        self.assertIn("--host claude --review-host codex", json.loads(out.getvalue())["next"]["then"])

    def test_r11_the_browser_warning_is_for_builds_and_says_the_true_thing(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Targets:** web-chrome\n")
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="drive it in a browser"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual([w for w in agent_loop.preflight("codex", self.wt, "review") if "browser" in w], [])
            build = [w for w in agent_loop.preflight("codex", self.wt, "build", "WATER", "WP1") if "browser" in w]
        self.assertEqual(len(build), 1, build)
        self.assertIn("has to ask to run it there", build[0])
        self.assertIn("tell the agent with `run --message` that it may", build[0])
        self.assertNotIn("--host claude", build[0])

    def test_r11_an_archived_design_review_keeps_its_own_time_in_utc(self):
        ev = self.evidence("WATER")
        ev.mkdir(parents=True)
        (ev / "design-review-1.md").write_text("first\nDESIGN CHANGES: no LOD plan")
        when = datetime(2026, 11, 10, 2, 53, 50, tzinfo=timezone(timedelta(hours=1))).timestamp()
        os.utime(ev / "design-review-1.md", (when, when))  # kept as the second review started
        (ev / "design-review.md").write_text("second\nDESIGN OK")
        prof = agent_loop.profile(self.wt)
        rec = {"design": {"verdict": "ok", "review": ".orchestrate/evidence/WATER/design-review.md",
                          "at": "2026-11-10T01:58:51Z"}}
        rows = agent_loop.design_reviews(self.wt, prof, "HEAD", "WATER", rec)
        self.assertEqual([(d["verdict"], d["at"]) for d in rows],
                         [("changes", "2026-11-10T01:53:50Z"), ("ok", "2026-11-10T01:58:51Z")])

    # Round twelve: the confirmation run

    def test_r12_the_whole_ask_reaches_the_record_the_commit_and_the_design_reviewer(self):
        ask = "Plan the project: " + "a slug tool that handles accents, " * 12 + "and when the input is empty, says so"
        planned = self.plan(task=ask)
        self.assertEqual(planned["result"], "PLANNED", planned)
        rec = json.loads(self.git("show", "origin/main:docs/plans/PAY/RECORD.json").stdout)
        self.assertEqual(rec["tasks"][-1]["task"], ask)
        self.assertEqual(rec["work_packages"]["WP1"]["authorised"]["task"], ask[:120])  # the whole ask is kept once
        self.assertIn("and when the input is empty, says so", self.git("log", "--format=%B", "origin/main").stdout)
        self.git("pull", "-q", "--rebase", "origin", "main")
        os.environ.update(FAKE_REVIEW="design")
        self.review("design", module="PAY", commit=None)
        self.assertIn("docs/plans/PAY/RECORD.json under `tasks`", self.calls()[-1]["argv"][-1])

    def test_r12_a_planners_assumptions_are_counted_and_reported(self):
        os.environ.update(FAKE_ASSUME="\n\n## Open for the user\n\n- Assumption: accents means any letter with a Latin base\n"
                                       "Assumption: the size limit is in bytes\nNot an assumption: this line\n")
        planned = self.plan()
        self.assertEqual(planned["assumptions"], {"PAY": 2}, planned)
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0)
        section = report.split("## Choices made for you")[1].split("\n## ")[0]
        self.assertIn("- PAY ([plan](docs/plans/PAY/PLAN.md)) assumes:", section)
        self.assertIn("  - accents means any letter with a Latin base", section)
        self.assertIn("  - the size limit is in bytes", section)
        self.assertNotIn("this line", section)

    def test_r12_a_written_report_links_from_where_it_lives(self):
        quoted = "a reviewer wrote [see](docs/x.md) and [u](https://x.test/a)"  # not the report's own links
        text = (agent_loop.md_link("r", ".orchestrate/evidence/WATER/WP1-review.md") + " "
                + agent_loop.md_link("p", "docs/plans/PAY/PLAN.md") + " " + quoted)
        self.assertEqual(agent_loop.relink(text, ".orchestrate/evidence/build-reports"),
                         "[r](../WATER/WP1-review.md) [p](../../../docs/plans/PAY/PLAN.md) " + quoted)
        self.assertEqual(agent_loop.relink(text, None),
                         "[r](.orchestrate/evidence/WATER/WP1-review.md) [p](docs/plans/PAY/PLAN.md) " + quoted)

    def test_r13_a_run_that_builds_nothing_isnt_recorded_as_the_modules_run(self):
        self.write_done([work_package("WP1", "ready_for_review", ["pass"], inspect="frames"), work_package("WP2", "not_started", ["open"])],
                        ready=["WP1"])
        self.commit_all()
        owed = self.run_loop(host="claude")
        self.assertEqual(owed["result"], "NEEDS_REVIEW", owed)
        agent_loop.RUN_HERE.clear()
        self.assertEqual(agent_loop.known_run(str(self.wt), "WATER"), {})


    def test_session_titles_group_by_repository_then_module(self):
        title = agent_loop.session_title(self.wt, "WATER", "WP1 build")
        self.assertEqual(title, f"{agent_loop.repository_name(self.wt)} · WATER · WP1 build")
        self.assertEqual(agent_loop.title_parts(title), ("build", "WATER", "WP1"))
        self.assertEqual(agent_loop.title_parts("review WATER WP1"), ("review", "WATER", "WP1"))  # before 1.7.0
        self.assertIsNone(agent_loop.title_parts("Thrum: Delivery Lead"))
        prof = agent_loop.profile(self.wt)
        self.assertEqual(agent_loop.plan_title(self.wt, self.wt, prof, "Re-plan water WP2 after review"),
                         agent_loop.session_title(self.wt, "WATER", "plan: Re-plan water WP2 after review"))
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
        done_ms = [{"module": "W", "work_package": "WP1", "status": "done", "pct": [0.1, 0.2, 0.3], "reviews": 1}]
        open_one = [{"module": "W", "work_package": "WP2", "status": "not_started", "reviews": 1}]
        verdict = agent_loop.plan_forecast(acc, done_ms, open_one, recent)["verdict"]
        self.assertTrue(verdict.startswith("Quota lasts: the 1 open work package and other use need about 0.3%"), verdict)
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
                (REPEATS - 1, 4, 0, "new_builder_session", "lead", "--fresh"),
                (REPEATS, REPEATS, 0, "diagnosis", "lead", " plan "),
                (REPEATS, 5, 1, "too_many_failed_reviews", "human", " human reopen "),  # the lead runs it once the user decides
                (1, 6, 0, "diagnosis", "lead", " plan "),
                (1, 6, 1, "too_many_failed_reviews", "human", " human reopen ")):
            word_now = agent_loop.escalation(failed, with_repeat, diagnoses)
            counts = {"failed_reviews": failed, "failed_reviews_with_repeat": with_repeat, "diagnoses": diagnoses}
            then = agent_loop.escalation_next(word_now, "WATER", "WP1", counts, self.wt, prof)
            self.assertEqual((word_now, then["escalation"], then.get("decides") or then["by"]), (word, word, by))
            self.assertIn(has, then["command"])

    def test_r18_human_stops_ask_in_chat_and_never_send_anyone_to_a_terminal(self):
        prof = agent_loop.profile(self.wt)
        for word in ("too_many_failed_reviews",):
            then = agent_loop.escalation_next(word, "WATER", "WP1", {"failed_reviews": 4, "failed_reviews_with_repeat": 4, "diagnoses": 1}, self.wt, prof)
            self.assertEqual(then["decides"], "human")
            self.assertTrue(then["ask"])
            self.assertIn("--text '<what the user said", then["command"])
        for step in ({"module": "WATER", "work_package": "WP1", "status": "blocked", "reason": "too_many_failed_reviews"},
                     {"module": "WATER", "work_package": "WP1", "status": "ready_for_review", "stored_status": "done"},
                     {"module": "WATER", "work_package": "WP1", "status": "in_progress_elsewhere", "by": "elsewhere"}):
            n = agent_loop.next_for(step, self.wt, prof)
            text = json.dumps(n)
            self.assertNotIn("terminal", text)
            self.assertNotIn("--reason", text)
            self.assertIn("--text '<what the user said", text)
            if n["by"] == "human":
                self.assertTrue(n["ask"])


    def test_r8_a_plan_that_leaves_an_owed_work_package_alone_settles_nothing(self):
        before = {"work_packages": [dict(work_package("WP1", "in_progress", ["open"]), failed_reviews_with_repeat=4)]}
        after = json.loads(json.dumps(before))
        self.assertEqual(agent_loop.settle_replanned(before, after, "WATER"), [])
        self.assertEqual(after["work_packages"][0]["failed_reviews_with_repeat"], 4)
        after["work_packages"][0]["items"][0]["check"] = "test -f smaller"
        self.assertEqual(agent_loop.settle_replanned(before, after, "WATER"), ["WATER WP1"])
        self.assertEqual((after["work_packages"][0]["failed_reviews_with_repeat"], after["work_packages"][0]["diagnoses"]), (0, 1))

    def test_a_planner_cant_change_the_counts(self):
        before = {"work_packages": [dict(too_many("WP1", ["open"]), failed_reviews_with_repeat=3, failed_reviews=5, diagnoses=1,
                                      findings=[{"name": "x"}])]}
        after = json.loads(json.dumps(before))
        m = after["work_packages"][0]
        m.update(failed_reviews_with_repeat=0, failed_reviews=0, diagnoses=0, status="not_started")
        m.pop("findings")
        after["work_packages"].append(dict(work_package("WP1b", "not_started", ["open"]), failed_reviews_with_repeat=2, diagnoses=1))
        settled = agent_loop.settle_replanned(before, after, "WATER")
        agent_loop.keep_counts(before, after, settled, "WATER")
        m, split = after["work_packages"]
        self.assertEqual((m["failed_reviews_with_repeat"], m["failed_reviews"], m["diagnoses"], m["status"], m["findings"]),
                         (3, 5, 1, "blocked", [{"name": "x"}]))
        self.assertEqual((split["failed_reviews_with_repeat"], split["failed_reviews"], split["diagnoses"]), (0, 0, 1))

    def test_a_plan_that_changes_a_work_package_blocked_for_failed_reviews_starts_it_again(self):
        before = {"work_packages": [dict(too_many("WP1", ["open"]), failed_reviews_with_repeat=4, failed_reviews=6, diagnoses=1,
                                      findings=[{"name": "x"}])]}
        after = json.loads(json.dumps(before))
        after["work_packages"][0]["items"][0]["check"] = "test -f what-the-user-asked-for"
        other = json.loads(json.dumps(after))
        kept = agent_loop.settle_replanned(before, other, "WATER")
        agent_loop.keep_counts(before, other, kept, "WATER")
        self.assertEqual(other["work_packages"][0]["status"], "blocked", "only a change task carries out the user's call")
        settled = agent_loop.settle_replanned(before, after, "WATER")
        agent_loop.keep_counts(before, after, settled, "WATER", restart=True)
        m = after["work_packages"][0]
        self.assertEqual(settled, ["WATER WP1"])
        self.assertEqual((m["status"], "blocked" in m, "findings" in m, m["failed_reviews"], m["diagnoses"]),
                         ("not_started", False, False, 0, 0))


    def test_r9_a_review_host_the_profile_cant_resolve_is_a_problem(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** codx\n")
        with self.assertRaises(SystemExit) as stop:
            agent_loop.profile(self.wt, strict=True)
        self.assertIn("review host: 'codx'", str(stop.exception))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Host pi:** pi run {prompt} -m {model} -e {effort}\n- **Pi model:** p-1\n- **Review host:** pi\n")
        self.assertEqual(agent_loop.profile(self.wt, strict=True)["review_host"], "pi")

    def test_r9_loop_started_codex_shells_carry_the_role(self):
        prof = agent_loop.profile(self.wt)
        flags = agent_loop.codex_flags(prof, "review")
        self.assertIn('shell_environment_policy.set.ORCHESTRATE_ROLE="review"', flags)

    def test_r10_live_turns_and_dollars_say_what_they_are(self):
        rec = {"pid": 1, "role": "build", "module": "WATER", "work_package": "WP1", "host": "codex", "turns": 0,
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
    """One folder per module under docs/plans, the user's STATUS.md, `migrate` from the flat layout, the module
    table, and the checks a plan has to pass where it lands."""

    def prof(self):
        return agent_loop.profile(self.wt)

    def old_module(self, *entries):
        doc = done(*entries)
        rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)}
        doc["milestones"] = doc.pop("work_packages")
        rec["milestones"] = rec.pop("work_packages")
        return doc, rec

    def flatten(self, root="docs/plans", log=True):
        """Puts WATER back in the old flat layout, with M1 accepted, a design, a plan with a log and a brief."""
        design = "# Water design\n"
        doc, rec = self.old_module(work_package("M1", "done", ["pass"]), work_package("M2", "not_started", ["open"]))
        rec["milestones"]["M1"]["done"] = {"by": "checks", "at": "2026-11-10T10:00:00Z"}
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(design)}
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
        self.assertIsNone(agent_loop.module_of(prof, "docs/plans/VISION.md"))  # the project's vision and scope document, not a module's
        self.assertIsNone(agent_loop.module_of(prof, "docs/plans/WATER/notes.md"))
        self.assertEqual(self.ready()["can_start"][0]["module"], "WATER")

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
        self.assertEqual(sorted(files), ["docs/plans/GLOSSARY.md", "docs/plans/STATUS.md",
                                         "docs/plans/WATER/BRIEF.md", "docs/plans/WATER/DESIGN.md",
                                         "docs/plans/WATER/DONE.json", "docs/plans/WATER/LOG.md",
                                         "docs/plans/WATER/PLAN.md", "docs/plans/WATER/RECORD.json"])
        plan = self.git("show", "origin/main:docs/plans/WATER/PLAN.md").stdout
        self.assertNotIn("## Log", plan)
        self.assertIn("## WP2 waves", plan)
        log = self.git("show", "origin/main:docs/plans/WATER/LOG.md").stdout
        self.assertIn("- 2026-11-02 M1 done", log)
        self.assertIn(agent_loop.TRAILER, self.git("log", "--format=%B", "origin/main").stdout)
        r = self.ready()  # WP1 stays accepted and the design agreed: the move changed no hash
        self.assertEqual([x["work_package"] for x in r["can_start"]], ["WP2"])
        self.assertEqual(r["design_not_approved"], [])
        again = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to=None)
        self.assertEqual(again["result"], "NOTHING", again)

    def old_names(self):
        """Puts WATER back in the names from before 2.0: old states, `needs` lists, `attended` items, a parked
        work package, `owner_answers` and the old settings labels, with every hash stamped by the old formula."""
        at = "2026-11-09T10:00:00Z"
        w2 = dict(work_package("M2", "open", ["open", "open"]), needs=["M1"])
        w2["items"][1].update(inspect="on the phone", attended="plug in the iPhone")
        w4 = work_package("M4", "open", ["open"])
        w4["items"][0]["attended"] = "the user picks a direction"
        doc, rec = self.old_module(work_package("M1", "done", ["pass"]), w2, dict(work_package("M3", "parked", ["open"]), failed_reviews_with_repeat=4), w4)
        rec["milestones"] = {m["id"]: {"definitions": agent_loop.old_definitions(m), "authorised": {"by": "plan"},
                                       "reviews": []} for m in doc["milestones"]}
        rec["milestones"]["M1"].update(accepted={"by": "checks", "at": at},
                                       reviews=[{"verdict": "PASS", "items": {"M1.1": "cant_tell"}, "at": at}])
        rec["milestones"]["M2"]["owner_answers"] = [{"by": "owner", "text": "Direction B", "at": at, "item": "M2.2"}]
        rec["milestones"]["M3"]["parked"] = {"why": "it kept failing", "after": 4, "at": at}
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        put(self.wt / "docs/plans/WATER/RECORD.json", json.dumps(rec))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("**Merge:**", "**Integrate:**")
                                                .replace("**Test command:**", "**Check:**"))
        self.git("add", "-A")
        self.git("commit", "-qm", "old names", "-m", "Orchestrate-Loop: yes")  # the old trailer still counts
        self.git("push", "-q", "origin", "main")
        return doc

    def names_of_2_1(self):
        """Puts WATER back in the names of 2.1: a work package's `state`, `bar` and its counts `fails`, `rounds` and
        `replans`, an item's `status`, ACCEPTED.json with `accepted` and an `owner decision`, and the settings line
        `Owner decides`."""
        at = "2026-11-12T10:00:00Z"
        doc, rec = self.old_module(dict(work_package("M1", "done", ["pass"]), quality_bar="as calm as a pond"),
                   dict(work_package("M2", "in_progress", ["open"]), failed_reviews=5, failed_reviews_with_repeat=2))
        rec["milestones"] = {m["id"]: {"definitions": agent_loop.definitions(m), "reviews": [],
                                       "authorised": {"by": "owner decision", "words": "as planned", "at": at}}
                             for m in doc["milestones"]}
        rec["milestones"]["M1"]["accepted"] = {"by": "checks", "at": at}
        rec["milestones"]["M2"]["diagnoses"] = [{"who": "owner", "why": "the user decides", "at": at}]
        for m in doc["milestones"]:
            m["state"], m["fails"], m["rounds"] = m.pop("status"), m.pop("failed_reviews_with_repeat"), m.pop("failed_reviews", 0)
            m["replans"] = 1 if m["id"] == "M2" else 0  # M2 has had its re-plan
            m.pop("diagnoses")
            if "quality_bar" in m:
                m["bar"] = m.pop("quality_bar")
            for i in m["items"]:
                i["status"] = i.pop("builder_result")
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        (self.wt / "docs/plans/WATER/RECORD.json").unlink()
        put(self.wt / "docs/plans/WATER/ACCEPTED.json", json.dumps(rec))
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Owner decides:** spending and publishing\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "the names of 2.1", "-m", agent_loop.TRAILER)
        self.git("push", "-q", "origin", "main")
        return doc

    def test_migrate_brings_a_project_from_the_names_of_2_1_to_3_0(self):
        self.names_of_2_1()
        with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
            agent_loop.cmd_ready(argparse.Namespace(worktree=str(self.wt)))
        release()
        for old in ("names from before orchestrate 3.0", "ACCEPTED.json (now RECORD.json)", "`state` (now `status`)",
                    "`Owner decides:` line (now `Human decides:`)", "migrate --worktree"):
            self.assertIn(old, str(stop.exception))
        moved = self.migrate()
        self.assertEqual(moved["result"], "MIGRATED", moved)
        self.git("pull", "-q", "--rebase", "origin", "main")
        files = self.git("ls-tree", "-r", "--name-only", "origin/main", "docs/plans/WATER").stdout.split()
        self.assertIn("docs/plans/WATER/RECORD.json", files)
        self.assertNotIn("docs/plans/WATER/ACCEPTED.json", files)
        self.assertIn("- **Human decides:** spending and publishing", self.git("show", "origin/main:ORCHESTRATE.md").stdout)
        w1, w2 = self.read_done()["work_packages"]
        self.assertEqual((w1["status"], w1["quality_bar"], w1["items"][0]["builder_result"]),
                         ("done", "as calm as a pond", "pass"))
        self.assertEqual((w2["status"], w2["failed_reviews"], w2["failed_reviews_with_repeat"], w2["diagnoses"]),
                         ("in_progress", 5, 2, 1))
        for gone in ("state", "bar", "fails", "rounds", "replans"):
            self.assertNotIn(gone, w1)
            self.assertNotIn(gone, w2)
        self.assertNotIn("status", w1["items"][0])
        rec = self.read_record()["work_packages"]
        self.assertEqual((rec["WP1"]["done"]["by"], "accepted" in rec["WP1"], rec["WP1"]["authorised"]["by"]),
                         ("checks", False, "human decision"))
        self.assertEqual(rec["WP2"]["diagnoses"][0]["who"], "human")
        # no hash changed: WP1 is still Done in the record, and WP2 is the next to build
        self.assertEqual(rec["WP1"]["definitions"], agent_loop.definitions(w1))
        ready = self.ready()
        self.assertEqual([x["work_package"] for x in ready["can_start"]], ["WP2"], ready)
        self.assertEqual(self.migrate()["result"], "NOTHING")

    def test_an_unmigrated_project_is_refused_by_every_other_command(self):
        self.old_names()
        for func, kw in ((agent_loop.cmd_ready, dict()),
                         (agent_loop.cmd_status, dict(module=None)),
                         (agent_loop.cmd_run, dict(module="WATER", work_package=None, fresh=False, message=None,
                                                   no_progress_hours=1.0, turn_timeout_hours=0.1, host=None, model=None,
                                                   effort=None, human_rule=None, clear_human_rules=False,
                                                   no_design_review=False)),
                         (agent_loop.cmd_human, dict(action="accept", module="WATER", work_package="WP2", item=None,
                                                     text="fine", said=None, asked=None))):
            with self.subTest(command=func.__name__):
                try:
                    with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
                        func(argparse.Namespace(worktree=str(self.wt), **kw))
                finally:
                    release()
                self.assertIn("names from before orchestrate 3.0", str(stop.exception))
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
                         ["orchestrate: migrate the plans to a folder per module and the names of 3.0.3"])
        settings = self.git("show", "origin/main:ORCHESTRATE.md").stdout
        self.assertIn("- **Merge:** push", settings)
        self.assertIn("- **Test command:** none", settings)
        self.assertNotIn("Integrate", settings)
        doc = self.read_done()
        w1, w2, w3, w4 = doc["work_packages"]
        self.assertEqual([m["status"] for m in doc["work_packages"]], ["done", "not_started", "blocked", "not_started"])
        self.assertEqual((w2["depends_on"], "attended" in w2["items"][1]), (["WP1"], False))
        self.assertEqual(w2["items"][1]["needs"], {"type": "hardware", "what": "plug in the iPhone"})
        self.assertEqual(w4["items"][0]["needs"], {"type": "human_feedback", "what": "the user picks a direction"})
        self.assertEqual(w3["blocked"]["reason"], "too_many_failed_reviews")
        rec = self.read_record()["work_packages"]
        self.assertEqual(rec["WP2"]["human_feedback"], [{"asked": None, "said": "Direction B", "items": ["WP2.2"],
                                                        "at": "2026-11-09T10:00:00Z", "by": "owner"}])
        self.assertNotIn("owner_answers", rec["WP2"])
        self.assertEqual(rec["WP3"]["too_many_failed_reviews"]["why"], "it kept failing")
        self.assertEqual(rec["WP1"]["reviews"][0]["items"], {"WP1.1": "could_not_judge"})
        for m in doc["work_packages"]:  # each hash re-stamped with today's formula, so nothing reads as re-planned
            self.assertEqual(rec[m["id"]]["definitions"], agent_loop.definitions(m), m["id"])
        r = self.ready()
        self.assertEqual(([x["work_package"] for x in r["can_start"]], r["invalid"]), (["WP2"], []), r)
        self.assertEqual(self.migrate()["result"], "NOTHING")

    def test_migrate_to_moves_the_whole_plans_folder_and_the_plans_line(self):
        self.flatten(root="docs/modules", log=False)
        moved = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to="docs/plans")
        self.assertEqual((moved["result"], moved["plans"]), ("MIGRATED", "docs/plans"), moved)
        self.assertNotIn("logs_split", moved)
        self.assertIn("- **Plans:** docs/plans", self.git("show", "origin/main:ORCHESTRATE.md").stdout)
        self.assertEqual(self.git("show", "origin/main:docs/plans/GLOSSARY.md").stdout, "# Glossary\n")
        self.assertEqual(self.git("ls-tree", "--name-only", "origin/main", "docs/modules").stdout, "")
        self.assertEqual([x["work_package"] for x in self.ready()["can_start"]], ["WP2"])

    def test_a_work_package_ready_for_review_before_migrate_is_reviewed_at_the_move(self):
        self.flatten()
        doc, _ = self.old_module(work_package("M1", "done", ["pass"]), work_package("M2", "ready_for_review", ["pass"]))
        (self.wt / "docs/plans/WATER-DONE.json").write_text(json.dumps(doc))
        rec = json.loads((self.wt / "docs/plans/WATER-ACCEPTED.json").read_text())
        rec["milestones"]["M2"]["claim"] = {"at": "2026-11-11T10:00:00Z", "checks": []}  # as a 2.0.0 script wrote it
        (self.wt / "docs/plans/WATER-ACCEPTED.json").write_text(json.dumps(rec))
        self.git("commit", "-qam", "claim M2", "-m", agent_loop.TRAILER)
        self.git("push", "-q", "origin", "main")
        claimed = self.git("rev-parse", "HEAD").stdout.strip()
        moved = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), to=None)
        self.assertEqual(moved["result"], "MIGRATED", moved)
        reviewed = self.review("WP2", commit=claimed)
        self.assertEqual(reviewed["result"], "REVIEWED", reviewed)
        self.assertIn("before `migrate` brought", " ".join(reviewed.get("warnings") or []))

    def builder_branched_before_migrate(self):
        """A builder's worktree for WATER, branched before `migrate`, with two commits of its own on the old names:
        one moving M2 to in_progress in the done-when file, and one adding code."""
        tree = self.root / "wt-water"
        self.git("worktree", "add", "-q", "-b", "water-w2", str(tree), "origin/main")
        doc = json.loads((tree / "docs/plans/WATER/DONE.json").read_text())
        doc["milestones"][1]["status"] = "in_progress"
        doc["milestones"][1]["items"][0]["builder_result"] = "pass"
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
        w2 = doc["work_packages"][1]
        self.assertEqual((w2["status"], w2["items"][0]["builder_result"], w2["depends_on"]), ("in_progress", "pass", ["WP1"]))
        self.assertEqual(w2["items"][1]["needs"]["type"], "hardware")
        self.assertEqual((tree / "src/waves.py").read_text(), "WAVES = 3\n")
        self.assertEqual(agent_loop.old_names_in_tree(tree)[0], [])
        self.assertNotIn("<<<<<<<", (tree / "docs/plans/WATER/DONE.json").read_text())
        self.assertNotIn(str(tree), json.dumps(self.migrate().get("worktrees_on_old_names") or []))
        ran = self.run_loop(worktree=str(tree))
        # `run` accepts it, and WP2's builder merges from the worktree and reaches Ready for Review
        self.assertEqual((ran["result"], ran["work_package"]), ("READY_FOR_REVIEW", "WP2"), ran)

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
        refused = self.review("WP1", commit="0" * 40)
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
        doc = done(work_package("WP1", "done", ["pass"]), work_package("WP2", "not_started", ["open"], check="true",
                                                                  needs=needs("human_feedback", "the user")),
                   work_package("WP3", "not_started", ["open"]))
        doc["work_packages"][1]["status"], doc["work_packages"][1]["blocked"] = "blocked", {
            "reason": "needs_human_feedback", "items": ["WP2.1"], "what": "needs the user"}
        doc["work_packages"][0]["name"] = "The sea moves on screen"
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)}
        rec["work_packages"]["WP1"]["done"] = {"by": "review", "at": agent_loop.now(),
                                                "review": ".orchestrate/evidence/WATER/WP1-review.md"}
        put(self.wt / "docs/plans/WATER/RECORD.json", json.dumps(rec))
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water\n\n## Open for the user\n- Assumption: waves are blue\n")
        self.write_done([work_package("WP1", "not_started", ["open"])], module="EXTRA")
        put(self.wt / "docs/plans/ARCHITECTURE.md", ARCH)
        put(self.wt / "docs/plans/GLOSSARY.md", "**Swell**\nA long wave.\nProposed: by a builder.\n")
        self.commit_all()
        put(self.evidence("WATER/WP1-review.md"), "PASS WP1")
        page = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt), format="md")
        overview, modules = page.split("## All modules")
        self.assertLess(overview.index("## Overview"), overview.index("### Needs you now"))
        self.assertLess(overview.index("### Needs you now"), overview.index("### Choices made for you"))
        self.assertLess(overview.index("### Choices made for you"), overview.index("### Now and next"))
        self.assertLess(overview.index("### Now and next"), overview.index("### Recently done"))
        self.assertIn("0 of 3 modules done · 1 in progress · 2 to come", overview)
        # L5: what needs the user is apart from the choices a planner made for them
        needs_you, chosen = overview.split("### Choices made for you")
        chosen = chosen.split("### Now and next")[0]
        self.assertIn("- WATER assumes: waves are blue ([plan](WATER/PLAN.md))", chosen)
        self.assertIn("Swell (by a builder)", chosen)
        self.assertIn("Blocked: Needs User Feedback, WP2.1: WP2.1 works (the user). You judge it", needs_you)
        self.assertNotIn("assumes", needs_you)
        self.assertIn("- WP1 (EXTRA WP1): Not Started · [plan](EXTRA/PLAN.md)", overview)
        self.assertIn("- The sea moves on screen (WATER WP1), ", overview)
        self.assertIn("[review](../../.orchestrate/evidence/WATER/WP1-review.md)", overview)
        lines = [line for line in modules.splitlines() if line.startswith("| ") and "---" not in line][1:]
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("| 1 | WATER |") and lines[0].endswith("| WP2 of 3 · Blocked: Needs User Feedback |"),
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
        os.environ.update(FAKE_ASSUME="\nNow: building WP1\n")
        refused = self.plan()
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertTrue(any("`Now:` line" in p for p in refused["problems"]), refused["problems"])
        self.assertIn("`Now:` line", refused["next"]["command"])  # the planner is told why, to fix it

    def test_adopt_refuses_a_plan_that_fails_the_checks_and_land_only_warns(self):
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water\n## WP1\n### Notes\n")
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
        self.assertEqual(agent_loop.plan_text_problems(p, "# W\n\n## WP1 sea: done\n[review](x.md)\n\n## WP2 waves\n"
                                                          "- [ ] a\n\n## Open for the user\n- Assumption: x\n"), [])
        cases = {"long": "word " * 1600, "Now:": "# W\nNow: building WP2\n", "###": "# W\n## WP2\n### Notes\n",
                 "## Log": "# W\n## Log\n- 2026-11-01 x\n", "under": "## WP1 sea: done\n[review](x.md)\nsome notes\n"}
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
    """Release 3 of the 2026-11-12 plan: a builder merges with its work package in progress, and the script sets Ready for
    Review only after its own checks pass (N2, P3, N3, N4)."""

    def merge(self):
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                agent_loop.cmd_merge(argparse.Namespace(worktree=str(self.wt), no_check=False))
        finally:
            release()
        return json.loads(out.getvalue().splitlines()[-1])

    def set_w1(self, state, status="pass", where=None):
        """Edits WP1 in the worktree's done-when file and commits it, without merging."""
        where = where or self.wt
        path = where / "docs/plans/WATER/DONE.json"
        doc = json.loads(path.read_text())
        doc["work_packages"][0]["status"] = state
        for i in doc["work_packages"][0]["items"]:
            i["builder_result"], i["evidence"] = status, ".orchestrate/evidence/WATER/run.log" if status == "pass" else ""
        path.write_text(json.dumps(doc))
        self.git("commit", "-qam", f"WP1 {state}", where=where)

    def test_the_builder_merges_in_progress_and_the_script_sets_ready_for_review(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="captures"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True), result)
        self.assertEqual(self.calls()[0]["argv"][-1].count("with WP1's status left as in_progress"), 1)
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "ready_for_review")
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["ready_for_review"]["commit"], result["commit"])
        # the builder's commit says in_progress; the reviewer works on the script's commit, where it says Ready
        self.assertEqual(agent_loop.state_at(self.wt, result["commit"], "docs/plans/WATER/DONE.json", "WP1"),
                         "in_progress")
        self.assertEqual(self.review(commit=result["commit"])["verdict"], "PASS")

    def test_a_failing_item_check_leaves_the_main_branch_without_ready_for_review(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="captures",
                                   check="echo building; echo 'thread main panicked at tile.rs:88' >&2; exit 3"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop(no_progress_hours=0.0)["result"], "NO_PROGRESS_FOR_HOURS")
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "in_progress")
        self.assertNotIn("ready_for_review", self.read_record()["work_packages"]["WP1"])
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
        put(self.wt / "docs/plans/WATER/LOG.md", "- WP1: done")
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

    def test_a_check_that_names_its_inputs_is_reused_until_one_of_them_changes(self):
        count = self.root / "count"
        command = f"echo x >> {count}"
        put(self.wt / "render/shader.txt", "v1")
        put(self.wt / "other/notes.txt", "a")
        self.commit_all()
        reads = ["render/"]
        check = lambda: agent_loop.try_check(self.wt, command, None, 30, "docs/plans", reads)
        self.assertFalse(check().get("reused"))
        # a commit touching other files moves the tree, but not what this check reads
        put(self.wt / "other/notes.txt", "b")
        self.commit_all()
        self.assertTrue(check()["reused"])
        # uncommitted work elsewhere doesn't matter either
        (self.wt / "other/notes.txt").write_text("c")
        self.assertTrue(check()["reused"])
        self.assertEqual(count.read_text(), "x\n")
        # the same command without `reads` keys on the whole tree, which has moved
        self.git("checkout", "-q", "--", "other/notes.txt")
        self.assertFalse(agent_loop.try_check(self.wt, command, None, 30, "docs/plans").get("reused"))
        self.assertEqual(count.read_text(), "x\nx\n")
        # a commit touching a named path runs it again
        put(self.wt / "render/shader.txt", "v2")
        self.commit_all()
        self.assertFalse(check().get("reused"))
        self.assertTrue(check()["reused"])
        self.assertEqual(count.read_text(), "x\nx\nx\n")
        # the memo is in the git common directory, shared by every worktree
        self.assertTrue(list((self.wt / ".git/orchestrate/checks").glob("*.json")))

    def test_the_scripts_checks_reuse_an_items_pass_and_leave_the_test_command_to_the_merge(self):
        count = self.root / "count"
        put(self.wt / "render/shader.txt", "v1")
        self.commit_all()
        m = work_package("WP1", "in_progress", ["pass"], check=f"echo item >> {count}", reads=["render/"])
        prof = {"plans": "docs/plans", "test_command": f"echo tests >> {count}"}
        for n in range(2):
            reused = []
            self.assertEqual(agent_loop.check_failures(self.wt, prof, m, 30, reused), [])
            put(self.wt / "other.txt", str(n))  # another builder's merge moves the tip
            self.commit_all()
        self.assertEqual(reused, ["WP1.1"])
        self.assertEqual(count.read_text().split(), ["item"])

    def test_a_check_whose_named_inputs_cant_be_accounted_for_runs(self):
        count = self.root / "count"
        command = f"echo x >> {count}"
        put(self.wt / "render/shader.txt", "v1")
        self.commit_all()
        runs = lambda reads: agent_loop.try_check(self.wt, command, None, 30, "docs/plans", reads).get("reused")
        self.assertFalse(runs(["render/"]))
        self.assertTrue(runs(["render/"]))
        # an uncommitted change, or an untracked file, inside a named path
        (self.wt / "render/shader.txt").write_text("v2")
        self.assertFalse(runs(["render/"]))
        self.assertFalse(runs(["render/"]))
        self.git("checkout", "-q", "--", "render/shader.txt")
        (self.wt / "render/new.txt").write_text("new")
        self.assertFalse(runs(["render/"]))
        (self.wt / "render/new.txt").unlink()
        self.assertTrue(runs(["render/"]))
        # a named path that matches no file, even beside one that does
        self.assertFalse(runs(["render/", "models/"]))
        self.assertFalse(runs(["render/", "models/"]))
        self.assertEqual(count.read_text(), "x\n" * 6)
        # a check that changes files outside the named paths isn't remembered
        writes = f"echo x >> {count}; echo out > {self.wt / 'stray.txt'}"
        self.assertFalse(agent_loop.try_check(self.wt, writes, None, 30, "docs/plans", ["render/"]).get("reused"))
        (self.wt / "stray.txt").unlink()
        self.assertFalse(agent_loop.try_check(self.wt, writes, None, 30, "docs/plans", ["render/"]).get("reused"))

    def test_the_test_command_merge_ran_isnt_run_again_by_the_script(self):
        count = self.root / "count"
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", f"`echo x >> {count}`"))
        self.write_done([work_package("WP1", "in_progress", ["open"], inspect="captures"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.set_w1("in_progress")
        self.assertEqual(self.merge()["result"], "MERGED")
        self.assertEqual(count.read_text(), "x\n")
        os.environ.update(FAKE_PASS="0")
        result = self.run_loop(checks_only=True)
        self.assertEqual(result["result"], "READY_FOR_REVIEW", result)
        self.assertNotIn("Test command", result.get("reused_checks") or [])
        self.assertEqual(count.read_text(), "x\n")
        self.assertFalse(self.log.exists())  # no agent started

    def test_merge_refuses_a_builders_ready_for_review(self):
        self.write_done([work_package("WP1", "in_progress", ["open"], inspect="captures"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.set_w1("ready_for_review")
        refused = self.merge()
        self.assertEqual(refused["result"], "FAILED")
        self.assertIn("Your commits set WP1 to ready_for_review", refused["detail"])
        self.assertIn("Put the status back to in_progress in docs/plans/WATER/DONE.json", refused["detail"])
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "in_progress")
        self.set_w1("in_progress")  # what the message says to do
        self.assertEqual(self.merge()["result"], "MERGED")
        # the script's own Ready for Review, already on the main branch, isn't the next builder's change
        os.environ.update(FAKE_PASS="0")
        self.assertEqual(self.run_loop(checks_only=True)["result"], "READY_FOR_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        (self.wt / "more.txt").write_text("next work package")
        self.git("add", "more.txt")
        self.git("commit", "-qm", "WP2 work")
        self.assertEqual(self.merge()["result"], "MERGED")

    def test_an_upgraded_branch_that_set_ready_for_review_is_told_what_to_do(self):
        """A builder before 2.1.0 committed Ready for Review on its branch and stopped before merging."""
        self.write_done([work_package("WP1", "in_progress", ["open"], inspect="captures"),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        self.set_w1("ready_for_review")
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "CHECKS_FAILED", result)
        self.assertIn("Your commits set WP1 to ready_for_review", result["reasons"][0])
        first = self.prompt(self.calls()[0])
        self.assertIn("From the script:\nCommits in this worktree that haven't merged yet set WP1 to "
                      "ready_for_review.", first)
        self.assertIn("Put the status back to in_progress", self.prompt(self.calls()[1]))
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "in_progress")
        self.set_w1("in_progress")
        self.assertEqual(self.merge()["result"], "MERGED")
        done = self.run_loop(checks_only=True)
        self.assertEqual((done["result"], done["review"]), ("READY_FOR_REVIEW", True), done)

    def test_ready_for_review_on_the_main_branch_without_a_record_is_checked_not_reviewed(self):
        """Thrum's main branch can hold a work package a builder set Ready for Review before 2.1.0, with no record."""
        self.write_done([proved(work_package("WP1", "ready_for_review", ["pass"], inspect="captures")),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        refused = self.review()
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("no record that its checks passed", refused["problems"][0])
        self.assertIn(" run --module WATER ", refused["next"]["command"])
        self.assertEqual(self.ready()["can_start"][0]["work_package"], "WP1")
        os.environ.update(FAKE_PASS="0")
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("READY_FOR_REVIEW", True), result)
        self.assertFalse(self.log.exists())  # checked before any builder turn
        self.assertEqual(self.review(commit=result["commit"])["verdict"], "PASS")

    def test_ready_for_review_without_a_record_goes_back_to_in_progress_when_its_checks_fail(self):
        self.write_done([proved(work_package("WP1", "ready_for_review", ["pass"], inspect="captures", check="test -f proof")),
                         work_package("WP2", "not_started", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="Working on it.")
        self.assertEqual(self.run_loop(no_progress_hours=0.0)["result"], "NO_PROGRESS_FOR_HOURS")
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "in_progress")
        self.assertIn("From the script:\nThe script can't set the work package to Ready for Review yet: WP1.1 "
                      "`test -f proof` exited 1", self.prompt(self.calls()[0]))


    def test_the_run_waits_for_a_merge_left_running_in_the_background(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_background(argparse.Namespace(
                worktree=str(self.wt), log=None, command_args=["sh", "-c", "sleep 1.5", "agent_loop.py", "merge"]))
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
                 "the user judges whether the animation is smooth": "human_feedback"}
        for text, kind in cases.items():
            self.assertEqual(agent_loop.old_needs({"attended": text})["type"], kind, text)


class ScriptFactsTest(Clean):
    """When the script can't establish a fact, it names where the fact lives rather than stating or dropping it."""

    def test_a_round_without_recorded_findings_names_its_review(self):
        e = {"reviews": [{"verdict": "fail", "at": "2026-11-11T03:14:00Z", "review": ".orchestrate/evidence/C/WP1-review-1.md"}]}
        with mock.patch.object(agent_loop, "counted_reviews", lambda e, after=None: e["reviews"]):
            line = agent_loop.history_lines(e)[0]
        self.assertNotIn("no findings recorded", line)
        self.assertIn("read .orchestrate/evidence/C/WP1-review-1.md", line)

    def test_a_design_re_review_that_cant_compare_says_so(self):
        rec = {"design": {"commit": "a" * 40, "review": ".orchestrate/evidence/C/design-review.md", "verdict": "changes"}}
        with mock.patch.object(agent_loop, "path_at", lambda *args: None):
            text, changed = agent_loop.design_changes(Path("."), rec, "docs/plans/C/DONE.json", {"work_packages": []})
        self.assertIsNone(changed)
        self.assertIn("couldn't compare", text)
        self.assertIn(".orchestrate/evidence/C/design-review.md", text)

    def test_a_changed_design_document_is_named(self):
        doc = {"work_packages": []}
        rec = {"design": {"commit": "a" * 40, "review": "r.md", "hash": agent_loop.text_hash("old design")}}
        with mock.patch.object(agent_loop, "path_at", lambda w, c, path: path), \
                mock.patch.object(agent_loop, "show", lambda w, c, path: json.dumps(doc)):
            text, changed = agent_loop.design_changes(Path("."), rec, "D.json", doc, "DESIGN.md", "new design")
        self.assertTrue(changed)
        self.assertIn("the design document (DESIGN.md)", text)

    def test_the_planner_task_after_design_changes_counts_must_fix(self):
        out = {"verdict": "DESIGN CHANGES", "review": ".orchestrate/evidence/C/design-review.md",
               "line": "DESIGN CHANGES: 2 must_fix findings"}
        task = agent_loop.design_review_next(out, "C", Path("/tmp/x"), {"default_host": "codex"})["command"]
        self.assertIn("asked for changes, with its 2 Must Fix findings", task)
        self.assertNotIn("Suggestions", task, "revise.md says what to do with them")

    def test_a_block_records_where_the_builders_work_is(self):
        note = agent_loop.work_note({"work": {"branch": "build/atmosphere", "commit": "7911c75b" + "0" * 32}})
        self.assertIn("branch build/atmosphere at 7911c75b0000", note)
        self.assertIn("git show", note)

    def test_the_session_and_resource_rules(self):
        self.assertIn("no approval prompt", agent_loop.session_rule(True, "codex"))
        self.assertIn("visible in the Codex app", agent_loop.session_rule(False, "codex"))
        rule = agent_loop.resources_rule({"exclusive resources": "gpu"})
        self.assertIn("exclusive resources are: gpu", rule)
        self.assertIn("waits its turn", rule)


class DesignReReview(Repo):
    def test_an_unchanged_design_after_changes_is_not_reviewed_again(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames")], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        self.review("design", commit=None)
        again = self.review("design", commit=None)
        self.assertEqual(again["result"], "INVALID", again)
        self.assertIn("the planner hasn't acted yet", again["problems"][0])
        self.assertIn(" plan --worktree ", again["next"]["command"])

    def test_the_planners_answer_to_the_second_design_changes_is_approved_without_another_review(self):
        self.write_done([work_package("WP1", "not_started", ["open"], inspect="frames")], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        first = self.review("design", commit=None)
        self.assertIn("review the design again", first["next"]["why"])
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# Water design, revised once")
        self.commit_all()
        second = self.review("design", commit=None)
        self.assertEqual(second["result"], "REVIEWED", second)
        self.assertIn("without another review", second["next"]["command"])
        self.assertIn("approves its revision", second["next"]["why"])
        os.environ.update(FAKE_PLAN="replan")
        planned = self.plan(task="resolve the findings")
        self.assertEqual(planned["design_approved_at_limit"], ["WATER"], planned)
        self.assertNotIn("WATER", planned["design_review_owed"])
        design = self.read_record()["design"]
        self.assertEqual((design["verdict"], design["by"], len(design["after"])), ("ok", "review_limit", 2))
        self.assertNotIn({"module": "WATER"}, self.ready()["design_not_approved"])

    def test_only_design_changes_since_the_last_approval_count_towards_the_limit(self):
        rec = {"design_history": [{"verdict": "changes", "at": "1"}, {"verdict": "ok", "at": "2"},
                                  {"verdict": "changes", "at": "3", "not_counted": "the plan changed"}],
               "design": {"verdict": "changes", "at": "4"}}
        self.assertEqual([d["at"] for d in agent_loop.design_changes_in_a_row(rec)], ["4"])


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
            facts = agent_loop.resume_facts(Path(tmp), work_package("WP1", "in_progress", ["pass", "open"]), 124, 2.0)
            self.assertIn("2-hour turn limit", facts)
            self.assertIn(started["job"], facts)
            self.assertIn("WP1.1 has passed.", facts)
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


class MergeQueue(Repo):
    """`merge` as a queue: branches waiting together land as one batch with one run of the test command. The merges
    run as builders run them, each in its own process; the test holds the queue's lock until every request is in, so
    the batch is the one it means to build."""

    def use_test_command(self, command):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", f"`{command}`"))
        self.git("commit", "-qam", "test command")
        self.git("push", "-q", "origin", "main")

    def builder(self, name, files, subject=None):
        """A builder's worktree on its own branch from the main branch's tip, with one commit of `files`."""
        where = self.root / f"builder-{name}"
        self.git("worktree", "add", "-q", "-b", f"build/{name}", str(where), "origin/main")
        for path, text in files.items():
            put(where / path, text)
        self.git("add", "-A", where=where)
        self.git("commit", "-qm", subject or f"{name}'s work", where=where)
        return where

    def queue(self):
        return agent_loop.loop_dir(self.wt) / agent_loop.MERGE_QUEUE

    def start(self, where, **popen):
        proc = subprocess.Popen([sys.executable, str(SCRIPTS / "agent_loop.py"), "merge", "--worktree", str(where)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **popen)
        self.addCleanup(lambda: proc.poll() is None and (proc.kill(), proc.wait()))
        return proc

    def wait_for(self, test, what):
        deadline = time.time() + 30
        while not test():
            self.assertLess(time.time(), deadline, f"timed out waiting for {what}")
            time.sleep(0.05)

    def batch_of(self, *trees):
        """Starts a merge in each tree, in order, while the queue's lock is held, then lets them run. Returns each
        merge's result."""
        lock = agent_loop.take_file_lock(agent_loop.loop_dir(self.wt) / f"{agent_loop.MERGE_QUEUE}.lock")
        procs = []
        try:
            for n, where in enumerate(trees, 1):
                procs.append(self.start(where))
                self.wait_for(lambda: len(list(self.queue().glob("*.json"))) == n, f"request {n}")
        finally:
            lock.close()
        results = []
        for p in procs:
            out, err = p.communicate(timeout=120)
            self.assertTrue(out.strip(), err)
            results.append(json.loads(out.splitlines()[-1]))
        return results

    def landed(self, path):
        self.git("fetch", "-q", "origin")
        return subprocess.run(["git", "-C", str(self.wt), "cat-file", "-e", f"origin/main:{path}"],
                              capture_output=True).returncode == 0

    def test_three_waiting_branches_land_as_one_batch_with_one_test_run(self):
        count = self.root / "count"
        self.use_test_command(f"echo x >> {count}")
        trees = [self.builder(n, {f"{n}.txt": n}) for n in ("a", "b", "c")]
        results = self.batch_of(*trees)
        self.assertEqual([r["result"] for r in results], ["MERGED"] * 3, results)
        self.assertEqual(count.read_text(), "x\n")  # the test command ran once, for the batch
        batches = {r["batch"]["id"] for r in results}
        self.assertEqual(len(batches), 1)
        self.assertEqual(results[0]["batch"]["landed"], ["build/a", "build/b", "build/c"])  # in arrival order
        self.assertEqual([r["batch"]["your_place"] for r in results], [1, 2, 3])
        self.assertEqual(results[0]["batch"]["test_runs"], 1)
        self.assertIn("number 1 of 3", results[0]["batch"]["note"])
        tip = self.git("ls-remote", "origin", "refs/heads/main").stdout.split()[0]
        for r, where in zip(results, trees):
            self.assertEqual((r["detail"], r["commit"], agent_loop.head_commit(where)), (tip, tip, tip))
        self.assertTrue(all(self.landed(f"{n}.txt") for n in "abc"))
        # each builder is told what came in with its merge: the branches before its own and after it
        self.assertEqual(results[0]["upstream_files"], ["b.txt", "c.txt"])
        self.assertEqual(results[1]["upstream_files"], ["a.txt", "c.txt"])
        self.assertEqual(results[2]["upstream_files"], ["a.txt", "b.txt"])
        self.assertEqual(list(self.queue().iterdir()), [])  # nothing left in the queue

    def test_the_merge_queue_notes_whose_each_landed_commit_is(self):
        self.use_test_command("true")
        trees = [self.builder("a", {"a.txt": "a"}, "Water w1: a"), self.builder("b", {"b.txt": "b"})]
        self.assertEqual([r["result"] for r in self.batch_of(*trees)], ["MERGED"] * 2)
        noted = json.loads((agent_loop.loop_dir(self.wt) / agent_loop.LANDED_FILE).read_text())
        self.git("fetch", "-q", "origin")
        a = self.git("log", "-1", "--format=%H", "origin/main~1").stdout.strip()
        self.assertEqual(noted, {a: "WATER"})  # b's subject names no module, so nothing is known of it

    def test_a_branch_that_conflicts_is_left_out_with_its_files_named(self):
        count = self.root / "count"
        self.use_test_command(f"echo x >> {count}")
        trees = [self.builder("a", {"shared.txt": "a\n"}), self.builder("b", {"shared.txt": "b\n", "b.txt": "b"}),
                 self.builder("c", {"c.txt": "c"})]
        before_b = agent_loop.head_commit(trees[1])
        a, b, c = self.batch_of(*trees)
        self.assertEqual((a["result"], b["result"], c["result"]), ("MERGED", "FAILED", "MERGED"), (a, b, c))
        self.assertEqual(b["conflicts"], ["shared.txt"])
        self.assertIn("conflicts in shared.txt", b["detail"])
        self.assertEqual(a["batch"]["landed"], ["build/a", "build/c"])
        self.assertEqual(count.read_text(), "x\n")
        self.assertEqual(agent_loop.head_commit(trees[1]), before_b)  # b's worktree is as it was
        self.assertFalse(self.landed("b.txt"))
        self.assertTrue(self.landed("c.txt"))

    def test_a_branch_that_fails_the_test_command_is_found_by_splitting_and_the_rest_land(self):
        self.use_test_command("if [ -f broken ]; then echo 'thread main panicked' >&2; exit 3; fi")
        trees = [self.builder("a", {"a.txt": "a"}), self.builder("b", {"broken": "x"}),
                 self.builder("c", {"c.txt": "c"})]
        a, b, c = self.batch_of(*trees)
        self.assertEqual((a["result"], b["result"], c["result"]), ("MERGED", "FAILED", "MERGED"), (a, b, c))
        self.assertIn("exited 3", b["detail"])
        self.assertIn("thread main panicked", b["detail"])
        self.assertNotIn("conflicts", b)
        self.assertEqual(a["batch"]["landed"], ["build/a", "build/c"])
        self.assertEqual(a["batch"]["test_runs"], 4)  # all three, a alone, b on a, c on a
        self.assertTrue(self.landed("a.txt") and self.landed("c.txt"))
        self.assertFalse(self.landed("broken"))

    def test_one_waiting_branch_lands_from_its_own_worktree_as_before(self):
        count = self.root / "count"
        self.use_test_command(f"pwd >> {count}")
        where = self.builder("a", {"a.txt": "a"})
        put(self.wt / "camera.rs", "moved")
        self.git("add", "-A")
        self.git("commit", "-qm", "another module")
        self.git("push", "-q", "origin", "main")
        out, err = self.start(where).communicate(timeout=120)
        result = json.loads(out.splitlines()[-1])
        self.assertEqual(result["result"], "MERGED", err)
        self.assertNotIn("batch", result)
        self.assertEqual(Path(count.read_text().strip()).resolve(), where.resolve())  # tested in its own worktree
        self.assertEqual(result["upstream_files"], ["camera.rs"])
        self.assertEqual(result["commit"], agent_loop.head_commit(where))
        self.assertTrue(self.landed("a.txt"))

    def test_the_queue_outlives_a_merge_that_dies_while_running_it(self):
        started = self.root / "started"
        self.use_test_command(f"if [ -f a.txt ]; then touch {started}; sleep 60; fi")
        a, b, c = (self.builder(n, {f"{n}.txt": n}) for n in "abc")
        runner = self.start(a, start_new_session=True)
        self.wait_for(started.exists, "a's test command")  # a runs the queue, and holds it while its test runs
        waiting = [self.start(b), self.start(c)]
        self.wait_for(lambda: len(list(self.queue().glob("*.json"))) == 3, "b's and c's requests")
        os.killpg(runner.pid, signal.SIGKILL)
        runner.wait()
        results = [json.loads(p.communicate(timeout=120)[0].splitlines()[-1]) for p in waiting]
        self.assertEqual([r["result"] for r in results], ["MERGED", "MERGED"], results)
        # b and c start a moment apart, so either may queue first
        self.assertEqual(sorted(results[0]["batch"]["landed"]), ["build/b", "build/c"])
        self.assertFalse(self.landed("a.txt"))  # a's merge died, so its request went with it
        self.assertEqual(list(self.queue().iterdir()), [])


class Versions(Clean):
    def test_the_script_version_matches_the_marketplace(self):
        market = json.loads((SCRIPTS.parents[3] / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(next(p["version"] for p in market["plugins"] if p["name"] == "orchestrate"),
                         agent_loop.VERSION)

    def test_a_newer_installed_copy_is_found_beside_a_cached_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            rest = Path("skills/orchestration/lead/scripts/agent_loop.py")
            for version in ("1.7.1", "2.0.0", "2.1.0"):
                put(Path(tmp, "orchestrate", version) / rest, "")
            with mock.patch.object(agent_loop, "LOOP", Path(tmp, "orchestrate", "1.7.1") / rest):
                self.assertEqual(agent_loop.newer_install(), str(Path(tmp, "orchestrate", "2.1.0") / rest))
            with mock.patch.object(agent_loop, "LOOP", Path(tmp, "orchestrate", "2.1.0") / rest):
                self.assertIsNone(agent_loop.newer_install())

    def test_the_review_prompt_names_the_checks_the_script_already_ran(self):
        prof = {"test_command": "./dev check"}
        note = agent_loop.checks_note(prof, work_package("WP1", "ready_for_review", ["pass", "pass"]), "abc123def4567")
        self.assertIn("`./dev check`", note)
        self.assertIn("WP1.1, WP1.2", note)
        self.assertEqual(agent_loop.checks_note(prof, work_package("WP1", "ready_for_review", ["pass"]), None), "")


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
        code = agent_loop.run_turn("codex", prof, "m", "medium", self.wt, "go", "t1", 3)[0]
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
        self.assertIn("This is a new session. An earlier session worked on WP1", new)
        self.assertIn("create_goal", new)  # the new Codex session gets its own goal
        self.assertEqual((self.state()["context"], self.state()["version"]), (50000, agent_loop.VERSION))

    @shares("stalled-run")
    def test_a_session_from_a_state_file_2_0_0_wrote_is_not_resumed(self):
        self.assertEqual(self.stalled_run()["result"], "STALLED")
        state = self.state()
        for key in ("version", "context", "window", "basis"):  # 2.0.0 wrote none of these
            state.pop(key, None)
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


class CommandLine(Repo):
    """How the script behaves as a command line: every ending is a JSON result with an exit status, a result file is
    never left holding an earlier attempt's result, and a printed `next` can be run and added to safely."""

    def main(self, *argv):
        """Runs the script's own entry point as the shell would, and returns (exit status, result line)."""
        out, err = io.StringIO(), io.StringIO()
        saved = list(agent_loop.QUOTA_WORKTREE)
        try:
            with mock.patch.object(sys, "argv", ["agent_loop.py", *argv]), contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as stop:
                agent_loop.main()
        finally:
            agent_loop.QUOTA_WORKTREE[:] = saved
            agent_loop.MARKED.clear()
            release()
        return stop.exception.code, json.loads(out.getvalue().splitlines()[-1])

    def results(self):
        return Path(agent_loop.git_common_dir(self.wt)) / "orchestrate" / "results"

    def test_review_kinds_select_the_work_package_or_the_design(self):
        self.ready_for_review()
        cmd = ("review", "--module", "WATER", "--worktree", str(self.wt))
        code, line = self.main(*cmd, "--kind", "work-package", "--work-package", "WP1")
        self.assertEqual((code, line["result"], line.get("verdict")), (0, "REVIEWED", "PASS"), line)
        os.environ["FAKE_REVIEW"] = "design"
        code, line = self.main(*cmd, "--kind", "design")
        self.assertEqual((code, line["result"], line.get("verdict")), (0, "REVIEWED", "DESIGN OK"), line)
        for flags in ((), ("--kind", "work-package"), ("--kind", "work-package", "--work-package", "design"),
                      ("--kind", "design", "--work-package", "WP1")):
            with self.subTest(flags=flags):
                code, line = self.main(*cmd, *flags)
                self.assertEqual((code, line["result"]), (2, "ERROR"))
                self.assertIn("--work-package", line["error"])

    def test_a_refused_command_line_replaces_the_result_file_a_lead_would_read(self):
        old = self.results() / "WATER-WP1-run.json"
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text(json.dumps({"result": "READY_FOR_REVIEW", "module": "WATER", "work_package": "WP1"}) + "\n")
        code, line = self.main("run", "--module", "WATER", "--worktree", str(self.wt), "--mesage", "hi")
        self.assertEqual((code, line["result"]), (2, "ERROR"), line)
        self.assertIn("maybe you meant --message for --mesage", line["error"])
        self.assertIn("usage: agent_loop.py run", line["usage"])
        self.assertEqual(line["next"]["argv"][-2:], ["run", "--help"])
        self.assertEqual(json.loads(old.read_text())["result"], "ERROR")

    def test_a_misspelt_required_flag_gets_a_suggestion(self):
        code, line = self.main("plan", "--worktree", str(self.wt), "--tsk", "x")
        self.assertEqual((code, line["result"]), (2, "ERROR"))
        self.assertIn("maybe you meant --task for --tsk", line["error"])

    def test_a_misspelt_command_gets_a_suggestion(self):
        code, line = self.main("unblok", "--module", "WATER")
        self.assertEqual((code, line["result"]), (2, "ERROR"))
        self.assertIn("unblock", line["error"])

    def test_a_check_that_stops_a_command_is_an_error_result_with_status_1(self):
        code, line = self.main("unblock", "--module", "WATER", "--worktree", str(self.wt))
        self.assertEqual((code, line["result"]), (1, "ERROR"), line)
        self.assertEqual(line["error"], "WATER has no blocked work package at the main branch's tip")
        self.assertEqual(json.loads(Path(line["result_file"]).read_text())["result"], "ERROR")

    def test_a_crash_is_script_failed_with_its_traceback(self):
        with mock.patch.object(agent_loop, "cmd_ready", side_effect=KeyError("boom")):
            parser = agent_loop.build_parser
            with mock.patch.object(agent_loop, "build_parser", lambda: _with_func(parser(), "ready",
                                                                                  agent_loop.cmd_ready)):
                code, line = self.main("ready", "--worktree", str(self.wt))
        self.assertEqual((code, line["result"]), (1, "SCRIPT_FAILED"), line)
        self.assertIn("KeyError", line["error"])
        self.assertTrue(line["traceback"])

    def test_a_running_command_marks_its_files_and_puts_back_the_ones_it_did_not_write(self):
        folder = self.results()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "WATER-WP1-run.json").write_text('{"result": "FINISHED"}\n')
        (folder / "WATER-TILE-WP1-run.json").write_text('{"result": "FINISHED"}\n')  # another module, untouched
        agent_loop.mark_running(["run", "--module", "WATER", "--worktree", str(self.wt)], str(self.wt))
        try:
            running = json.loads((folder / "WATER-WP1-run.json").read_text())
            self.assertEqual((running["result"], running["pid"]), ("RUNNING", os.getpid()))
            self.assertEqual(json.loads((folder / "WATER-run.json").read_text())["result"], "RUNNING")
            self.assertEqual(json.loads((folder / "WATER-TILE-WP1-run.json").read_text())["result"], "FINISHED")
            agent_loop.unmark(folder / "WATER-WP2-run.json")  # the run built WP2, so WP1's file goes back
            self.assertEqual(json.loads((folder / "WATER-WP1-run.json").read_text())["result"], "FINISHED")
            self.assertFalse((folder / "WATER-run.json").exists())
        finally:
            agent_loop.MARKED.clear()

    def test_another_live_commands_marker_is_left_alone(self):
        folder = self.results()
        folder.mkdir(parents=True, exist_ok=True)
        other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            live = json.dumps({"result": "RUNNING", "module": "WATER", "work_package": "WP1", "pid": other.pid}) + "\n"
            (folder / "WATER-WP1-run.json").write_text(live)
            code, line = self.main("run", "--module", "WATER", "--work-package", "WP1", "--worktree", str(self.wt),
                                   "--bogus")
            self.assertEqual(line["result"], "ERROR")
            self.assertEqual((folder / "WATER-WP1-run.json").read_text(), live)
        finally:
            other.kill()
            other.wait()

    def test_a_flag_given_twice_adds_the_leads_words(self):
        plan = agent_loop.build_parser().parse_args(
            ["plan", "--worktree", ".", "--task", "Fix CULLING's design (Metal triangle-merging)", "--task", "Do not split modules."])
        self.assertEqual(plan.task, "Fix CULLING's design (Metal triangle-merging)\n\nDo not split modules.")
        run = agent_loop.build_parser().parse_args(["run", "--module", "M", "--worktree", ".", "--message", "a",
                                                    "--message", "b"])
        self.assertEqual(run.message, "a\n\nb")

    def test_next_points_at_the_newest_installed_copy(self):
        newer = "/plugins/orchestrate/9.9.9/skills/orchestration/lead/scripts/agent_loop.py"
        command = agent_loop.loop_cmd("run", "--module", "WATER", "--worktree", "/w")
        with mock.patch.object(agent_loop, "newer_install", return_value=newer):
            fitted = agent_loop.fit_next(agent_loop.next_cmd(command, "lead", "why"))
        self.assertEqual(fitted["argv"][:3], ["python3", newer, "run"])
        self.assertTrue(fitted["command"].startswith(f"python3 {newer} run "))
        with mock.patch.object(agent_loop, "newer_install", return_value=newer):
            visible = agent_loop.fit_next(agent_loop.next_cmd("ORCHESTRATE_VISIBLE=1 " + command, "lead", "why"))
        self.assertTrue(visible["command"].startswith(f"ORCHESTRATE_VISIBLE=1 python3 {newer} run "))
        self.assertEqual(visible["argv"][:4], ["env", "ORCHESTRATE_VISIBLE=1", "python3", newer])  # runs without a shell

    def test_an_assumptions_links_resolve_where_it_is_copied(self):
        plan = "Assumption: waves follow [the sea study](../../research/sea.md#swell), as [noted](#w2) at [site](https://x.y)\n"
        line, = agent_loop.assumptions(plan, "docs/plans/WATER/PLAN.md")
        on_status = agent_loop.relink(f"- WATER assumes: {line}", "docs/plans")
        self.assertIn("[the sea study](../research/sea.md#swell)", on_status)
        self.assertIn("[noted](#w2)", on_status)  # an anchor or a web link is left alone
        self.assertIn("[site](https://x.y)", on_status)


class PlannerNudges(Repo):
    def test_a_planner_is_asked_to_shorten_a_long_log_entry_before_its_turn_ends(self):
        start = agent_loop.head_commit(self.wt)
        (self.wt / "docs/plans/WATER/LOG.md").write_text(
            "# WATER log\n\n- 2026-11-15 Planner: a long entry\n" + "  more detail\n" * 9)
        owed = agent_loop.plan_owed(self.wt, start, "Done.\n\nPLANNED")
        self.assertIn("longer than 8 lines", owed)
        self.assertTrue(owed.endswith("end with `PLANNED`."))
        (self.wt / "docs/plans/WATER/LOG.md").write_text("# WATER log\n\n- 2026-11-15 Planner: short.\n")
        self.assertIsNone(agent_loop.plan_owed(self.wt, start, "Done.\n\nPLANNED"))


def _with_func(parser, command, func):
    """`parser` with `command` set to call `func`, for a test that swaps a command's function."""
    parser._subparsers._group_actions[0].choices[command].set_defaults(func=func)
    return parser


class CatchUp(Repo):
    """`run` brings a builder's branch up to the main branch's tip when a planner has changed the plan files."""

    def test_a_builder_branch_is_rebased_onto_new_plan_files_keeping_its_proof(self):
        log = self.wt / "docs/plans/WATER/LOG.md"
        log.write_text("# WATER log\n\n- 2026-11-14 Planned.\n")
        self.commit_all()
        builder = self.root / "builder"
        self.git("worktree", "add", "-q", "-b", "build/water", str(builder), "origin/main")
        mine = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())
        mine["work_packages"][0]["status"] = "in_progress"
        mine["work_packages"][0]["items"][0].update(builder_result="pass", evidence=".orchestrate/evidence/WATER/WP1.log")
        (builder / "docs/plans/WATER/DONE.json").write_text(json.dumps(mine, indent=2) + "\n")
        with (builder / "docs/plans/WATER/LOG.md").open("a") as f:
            f.write("- 2026-11-15 Builder: WP1.1 passes.\n")
        (builder / "src.txt").write_text("the builder's work\n")
        self.git("add", "-A", where=builder)
        self.git("commit", "-q", "-m", "build: WP1.1", where=builder)
        theirs = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        theirs["work_packages"][0]["name"] = "WP1, renamed by the planner"
        (self.wt / "docs/plans/WATER/DONE.json").write_text(json.dumps(theirs, indent=2) + "\n")
        with log.open("a") as f:
            f.write("- 2026-11-15 Planner: renamed WP1.\n")
        self.commit_all()
        prof = agent_loop.profile(builder)
        caught = agent_loop.catch_up(builder, prof, agent_loop.tip(builder, prof))
        self.assertEqual(caught["result"], "rebased", caught)
        self.assertTrue(agent_loop.is_ancestor(builder, "origin/main", "HEAD"))
        merged = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())["work_packages"][0]
        self.assertEqual((merged["name"], merged["status"]), ("WP1, renamed by the planner", "in_progress"))
        self.assertEqual((merged["items"][0]["builder_result"], merged["items"][0]["evidence"]),
                         ("pass", ".orchestrate/evidence/WATER/WP1.log"))
        text = (builder / "docs/plans/WATER/LOG.md").read_text()
        self.assertIn("Builder: WP1.1 passes", text)
        self.assertIn("Planner: renamed WP1", text)
        self.assertEqual((builder / "src.txt").read_text(), "the builder's work\n")
        self.assertEqual(agent_loop.catch_up(builder, prof, agent_loop.tip(builder, prof)), {})  # nothing more to do

    def test_a_conflict_outside_the_plans_folder_is_left_for_the_builder(self):
        (self.wt / "src.txt").write_text("main\n")
        self.commit_all()
        builder = self.root / "builder"
        self.git("worktree", "add", "-q", "-b", "build/water", str(builder), "origin/main")
        (builder / "src.txt").write_text("builder\n")
        self.git("commit", "-qam", "builder's change", where=builder)
        before = agent_loop.head_commit(builder)
        (self.wt / "src.txt").write_text("main again\n")
        theirs = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        theirs["work_packages"][0]["name"] = "renamed"
        (self.wt / "docs/plans/WATER/DONE.json").write_text(json.dumps(theirs, indent=2) + "\n")
        self.commit_all()
        prof = agent_loop.profile(builder)
        caught = agent_loop.catch_up(builder, prof, agent_loop.tip(builder, prof))
        self.assertEqual((caught["result"], caught["conflicts"]), ("left", ["src.txt"]), caught)
        self.assertEqual(agent_loop.head_commit(builder), before)
        self.assertFalse(agent_loop.rebasing(builder))

    def branch_with_proof(self):
        """A builder worktree whose own commit passes WP1.1, and a tip that redefines WP1.1 without a textual conflict."""
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        doc["work_packages"][0]["items"][0]["note"] = "\n".join(["padding"] * 3)  # keeps the two edits apart
        (self.wt / "docs/plans/WATER/DONE.json").write_text(json.dumps(doc, indent=2) + "\n")
        self.commit_all()
        builder = self.root / "builder"
        self.git("worktree", "add", "-q", "-b", "build/water", str(builder), "origin/main")
        mine = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())
        mine["work_packages"][0]["items"][0].update(builder_result="pass", evidence=".orchestrate/evidence/WATER/WP1.log")
        (builder / "docs/plans/WATER/DONE.json").write_text(json.dumps(mine, indent=2) + "\n")
        self.git("commit", "-qam", "build: WP1.1", where=builder)
        theirs = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        theirs["work_packages"][0]["items"][0]["statement"] = "WP1.1 works, redefined"
        (self.wt / "docs/plans/WATER/DONE.json").write_text(json.dumps(theirs, indent=2) + "\n")
        self.commit_all()
        return builder

    def test_proof_on_an_item_the_tip_redefined_is_dropped_even_without_a_conflict(self):
        builder = self.branch_with_proof()
        prof = agent_loop.profile(builder)
        caught = agent_loop.catch_up(builder, prof, agent_loop.tip(builder, prof))
        self.assertEqual(caught["result"], "rebased", caught)
        item1 = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())["work_packages"][0]["items"][0]
        self.assertEqual((item1["statement"], item1["builder_result"]), ("WP1.1 works, redefined", "open"))
        self.assertEqual(self.git("status", "--porcelain", where=builder).stdout.strip(), "")

    def test_a_rebase_the_script_cannot_settle_is_undone(self):
        builder = self.branch_with_proof()
        prof = agent_loop.profile(builder)
        before = agent_loop.head_commit(builder)
        with mock.patch.object(agent_loop, "settle_rebase", side_effect=lambda w, *a: (
                agent_loop.git(w, *agent_loop.ident(w), "rebase", "--exec", "false", a[1]),  # stops part-way
                (_ for _ in ()).throw(UnicodeDecodeError("utf-8", b"", 0, 1, "x")))):
            caught = agent_loop.catch_up(builder, prof, agent_loop.tip(builder, prof))
        self.assertEqual(caught["result"], "left", caught)
        self.assertFalse(agent_loop.rebasing(builder))
        self.assertEqual(agent_loop.head_commit(builder), before)

    def test_merged_done_keeps_proof_only_where_the_definitions_held(self):
        tip_doc = done(work_package("WP1", "not_started", ["open", "open"]))
        tip_doc["work_packages"][0]["items"][1]["statement"] = "WP1.2 works, redefined"
        mine = done(work_package("WP1", "in_progress", ["pass", "pass"], check="true", evidence="e.log"))
        out = json.loads(agent_loop.merged_done(json.dumps(tip_doc), json.dumps(mine)))["work_packages"][0]
        self.assertEqual(out["status"], "in_progress")
        self.assertEqual([i["builder_result"] for i in out["items"]], ["pass", "open"])
        self.assertEqual(agent_loop.merged_done("{bad", json.dumps(mine)), "{bad")


class Recovery(Repo):
    """After a failed merge or a block, the command a result prints moves the work on: no hand rebase, no `unblock`
    the script could have done, and no `adopt` of a builder's own progress or of stale plan files."""

    def blocked_builder(self):
        """A builder worktree whose own commit passes WP1.1, adds a log entry, does work and carries a copy of another
        module's plan, stopped Blocked by a run; then the main branch changes that other plan file."""
        put(self.wt / "docs/plans/PAY/PLAN.md", "# Pay plan v1\n")
        (self.wt / "docs/plans/WATER/LOG.md").write_text("# WATER log\n")
        self.commit_all()
        builder = self.root / "builder"
        self.git("worktree", "add", "-q", "-b", "build/water", str(builder), "origin/main")
        mine = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())
        mine["work_packages"][0]["status"] = "in_progress"
        mine["work_packages"][0]["items"][0].update(builder_result="pass", evidence="run log")
        (builder / "docs/plans/WATER/DONE.json").write_text(json.dumps(mine, indent=2) + "\n")
        with (builder / "docs/plans/WATER/LOG.md").open("a") as f:
            f.write("- Builder: WP1.1 passes; merge failed on main's tests.\n")
        (builder / "docs/plans/PAY/PLAN.md").write_text("# Pay plan v2\n")
        (builder / "src.txt").write_text("the builder's work\n")
        self.git("add", "-A", where=builder)
        self.git("commit", "-qm", "build: WP1.1", where=builder)
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: merge failed: main's test command fails")
        blocked = self.run_loop(worktree=str(builder))
        self.assertEqual((blocked["result"], blocked["reason"]), ("BLOCKED", "needs_context"), blocked)
        put(self.wt / "docs/plans/PAY/PLAN.md", "# Pay plan v3\n")
        self.commit_all()
        return builder

    def test_a_blocked_builders_own_plan_files_and_stale_copies_never_send_the_lead_to_adopt(self):
        builder = self.blocked_builder()
        again = self.run_loop(worktree=str(builder))
        self.assertEqual(again["result"], "BLOCKED", again)
        self.assertNotIn("unmerged_plans", again)
        self.assertIn(" run --module WATER ", again["next"]["command"])
        self.assertIn("--message", again["next"]["command"])
        nothing = self.call(agent_loop.cmd_adopt, worktree=str(builder), paths=[])
        self.assertEqual(nothing["result"], "NOTHING", nothing)
        self.assertEqual(self.git("show", "origin/main:docs/plans/PAY/PLAN.md").stdout, "# Pay plan v3\n")
        drift = agent_loop.plan_drift(builder, agent_loop.profile(builder), "origin/main")
        self.assertEqual((drift["uncommitted"], drift["unmerged"]), ([], []))
        # a plan file the branch changed and the tip didn't is still the lead's to adopt, with its log entry
        put(builder / "docs/plans/WATER/DESIGN.md", "# Water design, revised in chat\n")
        self.git("add", "-A", where=builder)
        self.git("commit", "-qm", "design", where=builder)
        drift = agent_loop.plan_drift(builder, agent_loop.profile(builder), "origin/main")
        self.assertEqual(drift["unmerged"], ["docs/plans/WATER/DESIGN.md", "docs/plans/WATER/LOG.md"])

    def test_a_run_lifts_a_block_once_the_builders_work_has_merged_by_hand(self):
        builder = self.blocked_builder()
        # the lead merges the work by hand: the branch, rebased, is now on the main branch with its proof
        self.git("reset", "-q", "--hard", "origin/main", where=builder)
        doc = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())
        doc["work_packages"][0]["items"][0].update(builder_result="pass", evidence="run log")
        (builder / "docs/plans/WATER/DONE.json").write_text(json.dumps(doc, indent=2) + "\n")
        (builder / "src.txt").write_text("the builder's work\n")
        self.git("add", "-A", where=builder)
        self.git("commit", "-qm", "build: WP1.1, merged by hand", where=builder)
        self.git("push", "-q", "origin", "HEAD:main", where=builder)
        told = self.ready()["next"]
        self.assertIn(" run --module WATER ", told["command"])
        self.assertNotIn("--message", told["command"])
        self.assertIn("has merged since it stopped", told["why"])
        calls = len(self.calls())
        ran = self.run_loop(worktree=str(builder))
        self.assertEqual(ran["result"], "READY_FOR_REVIEW", ran)
        self.assertEqual(len(self.calls()), calls)  # no builder turn: the work had merged with every item passing
        self.assertEqual(self.read_done()["work_packages"][0]["status"], "done")  # a check item needs no reviewer

    def test_a_block_whose_work_never_left_the_main_branch_stays(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device attached")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        again = self.run_loop()
        self.assertEqual(again["result"], "BLOCKED", again)

    def test_a_builder_whose_code_conflicts_with_a_replanned_tip_is_started_to_rebase(self):
        (self.wt / "src.txt").write_text("main\n")
        self.commit_all()
        builder = self.root / "builder"
        self.git("worktree", "add", "-q", "-b", "build/water", str(builder), "origin/main")
        mine = json.loads((builder / "docs/plans/WATER/DONE.json").read_text())
        mine["work_packages"][0]["status"] = "in_progress"
        (builder / "docs/plans/WATER/DONE.json").write_text(json.dumps(mine, indent=2) + "\n")
        (builder / "src.txt").write_text("builder\n")
        self.git("commit", "-qam", "builder's change", where=builder)
        (self.wt / "src.txt").write_text("main again\n")
        self.write_done([work_package("WP1", "not_started", ["open"]), work_package("WP2", "not_started", ["open"])])
        doc = json.loads((self.wt / "docs/plans/WATER/DONE.json").read_text())
        doc["work_packages"][0]["items"][0]["statement"] = "WP1.1 works, re-planned"
        self.write_done(doc["work_packages"])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        ran = self.run_loop(worktree=str(builder))
        self.assertIn("src.txt", ran["caught_up"]["conflicts"], ran)
        self.assertEqual(len(self.calls()), 1)
        prompt = self.prompt(self.calls()[-1])
        self.assertIn("conflicts with the main branch in src.txt", prompt)
        self.assertIn("`git rebase origin/main`", prompt)
        # the fake builder didn't rebase, so the run stops and its next starts the builder again
        self.assertEqual(ran["result"], "INVALID", ran)
        self.assertNotIn("unmerged_plans", ran)
        self.assertIn(" run --module WATER ", ran["next"]["command"])


class MainBranchCheckSettings(Clean):
    def test_the_settings_declare_main_branch_checks_one_line_each(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(PROFILE + (
                "- **Main-branch check exact-images:** `./dev verify --exact; echo done`; every 30m; gap 2h; lock gpu, "
                "chrome; timeout 40m  *(script)*\n"
                "- **Main-branch check lint:** cargo clippy --all\n"
                "- **Main-branch check <name>:** `<command>`; every <30m>\n"))
            checks = agent_loop.profile(Path(tmp), strict=True)["main_checks"]
        self.assertEqual(checks, {
            "exact-images": {"command": "./dev verify --exact; echo done", "every_s": 1800.0, "gap_s": 7200.0,
                             "locks": ["chrome", "gpu"], "timeout_s": 2400.0},
            "lint": {"command": "cargo clippy --all", "every_s": 0.0, "gap_s": 0.0, "locks": [],
                     "timeout_s": agent_loop.MAIN_CHECK_TIMEOUT_S}})

    def test_a_main_branch_check_that_cant_be_read_is_named(self):
        problems = []
        checks = agent_loop.main_check_lines("- **Main-branch check slow:** `x`; every soon\n"
                                             "- **Main-branch check two words:** `y`\n"
                                             "- **Main-branch check slow:** `z`\n", problems)
        self.assertEqual(checks, {"slow": {"command": "x", "every_s": 0.0, "gap_s": 0.0, "locks": [],
                                           "timeout_s": agent_loop.MAIN_CHECK_TIMEOUT_S}})
        self.assertEqual(len(problems), 3, problems)
        self.assertIn("every 'soon'", problems[0])


class MainBranchChecks(Repo):
    """`main-check`: a slow check run once on the main branch's tip for every commit merged since its last run. In
    Thrum the exact-image verifier took 16 minutes while the main branch moved every 20, and required before each
    merge it stalled the build."""

    def setUp(self):
        super().setUp()
        agent_loop.MAIN_CHECK_POLL_S = 0.1
        self.count = self.root / "count"
        self.addCleanup(self.settle)

    def declare(self, command, extra=""):
        path = self.wt / "ORCHESTRATE.md"
        path.write_text(path.read_text() + f"- **Main-branch check images:** `{command}`{extra}\n")
        self.commit_all()

    def ask(self, **kw):
        """The command's exit status and result line."""
        args = parse(agent_loop.cmd_main_check, worktree=str(self.wt), **kw)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as stop:
                agent_loop.cmd_main_check(args)
        finally:
            release()
        line = json.loads(out.getvalue().splitlines()[-1])
        check_next_commands(line)
        return stop.exception.code, line

    def folder(self):
        return agent_loop.main_check_dir(self.wt, "images")

    def runs(self):
        return agent_loop.main_check_runs(self.folder())

    def settle(self, limit=30):
        """Waits for the runner in flight, if any, to finish."""
        end = time.time() + limit
        while agent_loop.main_check_flight(self.folder()) and time.time() < end:
            time.sleep(0.05)

    def in_flight(self, limit=20):
        """Waits for a runner just started to take the check's lock."""
        end = time.time() + limit
        while not agent_loop.main_check_flight(self.folder()) and time.time() < end:
            time.sleep(0.05)

    def counted(self):
        return len(self.count.read_text().splitlines()) if self.count.exists() else 0

    def land(self, message, **files):
        """Commits these files on the main branch and pushes them; returns the commit."""
        for name, text in files.items():
            put(self.wt / name, text)
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        self.git("push", "-q", "origin", "main")
        return agent_loop.head_commit(self.wt)

    def go(self, limit=60):
        """Starts a run on the tip and waits for it, and any bisect it begins, to finish; returns the check's listing."""
        before = len(agent_loop.main_check_runs(self.folder(), unjudged=True))
        code, started = self.ask(name="images", start=True)
        self.assertEqual((code, started["result"]), (0, "STARTED"), started)
        end = time.time() + limit
        while time.time() < end and (agent_loop.main_check_flight(self.folder()) or
                                     len(agent_loop.main_check_runs(self.folder(), unjudged=True)) == before):
            time.sleep(0.05)
        log = self.folder() / "runner.log"
        self.assertLess(time.time(), end, log.read_text() if log.exists() else "the runner never finished")
        self.settle()
        return self.listed()

    def listed(self):
        code, line = self.ask(name="images")
        self.assertEqual((code, line["result"]), (0, "MAIN_CHECKS"), line)
        [check] = line["checks"]
        return check

    def test_a_run_on_the_tip_is_recorded_and_listed(self):
        self.declare(f"echo run >> {self.count}; test ! -f broken", "; lock gpu")
        head = agent_loop.head_commit(self.wt)
        check = self.go()
        [run] = self.runs()
        self.assertEqual((run["kind"], run["commit"], run["result"], len(run["attempts"])), ("tip", head, "pass", 1))
        self.assertTrue(Path(run["attempts"][0]["stdout"]).exists())
        self.assertEqual(self.counted(), 1)
        self.assertIn('"lock": "gpu"', (agent_loop.loop_dir(self.wt) / agent_loop.LOCKS_FILE).read_text())
        self.assertEqual((check["name"], check["latest"]["result"], check["latest"]["commit"], check["due"]),
                         ("images", "pass", head, False))
        _, every = self.ask()
        self.assertEqual([c["name"] for c in every["checks"]], ["images"])
        [report] = agent_loop.main_check_report_lines(self.wt)
        self.assertIn(f"main-branch check `images`: passed on {head[:12]}", report)

    def test_a_second_start_finds_the_run_in_flight(self):
        self.declare(f"echo run >> {self.count}; sleep 2")
        code, started = self.ask(name="images", start=True)
        self.assertEqual((code, started["result"], started["started"]), (0, "STARTED", ["images"]))
        self.in_flight()
        self.assertEqual(self.ask(name="images", start=True)[1]["result"], "ALREADY_RUNNING")
        self.settle()
        self.assertEqual(self.counted(), 1)

    def test_a_pass_holds_for_its_commit_and_the_check_is_due_once_the_main_branch_moves(self):
        self.declare(f"echo run >> {self.count}")
        first = agent_loop.head_commit(self.wt)
        self.assertEqual(self.go()["latest"]["commit"], first)
        later = self.land("another module's work", **{"src/a.txt": "a"})
        spec = agent_loop.profile(self.wt)["main_checks"]["images"]
        self.assertTrue(agent_loop.main_check_due(spec, self.runs(), None, later))
        check = self.go()
        self.assertEqual((check["latest"]["result"], check["latest"]["commit"]), ("pass", later))
        self.assertEqual(self.counted(), 2)

    def test_a_failure_that_passes_on_its_retry_is_a_pass(self):
        flag = self.root / "flaked"
        self.declare(f"test -f {flag} || {{ touch {flag}; exit 1; }}")
        latest = self.go()["latest"]
        self.assertEqual((latest["result"], latest["flaky"], latest["attempts"]), ("pass", True, 2), latest)

    def test_a_failure_that_holds_is_bisected_to_the_commit_that_broke_it(self):
        self.declare("test ! -f broken")
        self.assertEqual(self.go()["latest"]["result"], "pass")
        self.land("tidy the camera", **{"src/camera.txt": "1"})
        c2 = self.land("water: foam on the shore", **{"broken": "x", "docs/plans/WATER/LOG.md": "- 2026-11-18 foam"})
        self.land("tidy the sky", **{"src/sky.txt": "1"})
        c4 = self.land("tidy the sky again", **{"src/sky.txt": "2"})
        latest = self.go()["latest"]
        self.assertEqual((latest["result"], latest["commit"]), ("fail", c4), latest)
        culprit = latest["culprit"]
        self.assertEqual((culprit["commit"], culprit["subject"], culprit["modules"]),
                         (c2, "water: foam on the shore", ["WATER"]))
        self.assertEqual([(r["kind"], r["result"]) for r in self.runs()],
                         [("tip", "pass"), ("tip", "fail"), ("bisect", "fail"), ("bisect", "pass")])
        self.assertIn(f"first failing commit {c2[:12]}", agent_loop.main_check_report_lines(self.wt)[0])
        [broken] = [b for b in agent_loop.main_broken(self.wt) if b["check"] == "images"]
        self.assertEqual(broken["modules"], ["WATER"])

    def test_a_run_that_cant_judge_the_commit_fails_nothing_and_runs_again(self):
        # A capture that dropped frames on a busy machine says nothing about the code; it exits 75.
        busy = self.root / "busy"
        busy.touch()
        self.declare(f"echo run >> {self.count}; test -f {busy} && exit 75; true")
        head = agent_loop.head_commit(self.wt)
        check = self.go()
        self.assertEqual(self.runs(), [])
        [run] = agent_loop.main_check_runs(self.folder(), unjudged=True)
        self.assertEqual((run["commit"], run["result"], len(run["attempts"])), (head, "unjudged", 3))
        self.assertNotIn("bisect", run)
        self.assertIn(f"couldn't judge {head[:12]}", agent_loop.main_check_report_lines(self.wt)[0])
        self.assertTrue(check["due"])
        busy.unlink()
        latest = self.go()["latest"]
        self.assertEqual((latest["result"], latest["commit"]), ("pass", head), latest)
        self.assertEqual(self.counted(), 4)

    def test_a_bisect_that_blames_a_plans_only_commit_names_no_culprit_and_fails_nothing(self):
        # The same code failed and passed, as when the machine was loaded: the check is flaky, not broken by a commit.
        calm = self.root / "calm"
        calm.touch()
        self.declare(f"test -f {calm}")
        self.assertEqual(self.go()["latest"]["result"], "pass")
        self.land("orchestrate: update STATUS.md", **{"docs/plans/STATUS.md": "# Status"})
        tip = self.land("tidy the sky", **{"src/sky.txt": "1"})
        calm.unlink()
        self.go()
        [run] = [r for r in agent_loop.main_check_runs(self.folder(), unjudged=True) if r["commit"] == tip]
        self.assertEqual((run["result"], run["bisect"]), ("unjudged", "no_culprit"), run)
        self.assertNotIn("culprit", run)
        self.assertIn("changed only the plans folder", run["bisect_why"])
        self.assertEqual([r["result"] for r in self.runs()], ["pass"])
        calm.touch()
        latest = self.go()["latest"]
        self.assertEqual((latest["result"], latest["commit"]), ("pass", tip), latest)

    def test_a_failure_an_older_version_judged_says_so_and_how_to_judge_it_again(self):
        old = {"result": "fail", "check": "images"}
        self.assertIn("main-check images --start", agent_loop.older_judge(old))
        self.assertIn("before 2.12.0", agent_loop.older_judge(old))
        self.assertEqual(agent_loop.older_judge({**old, "version": agent_loop.VERSION}), "")
        self.assertEqual(agent_loop.older_judge({"result": "pass", "check": "images"}), "")

    def test_a_bisect_stops_at_a_commit_it_cant_judge_rather_than_guess(self):
        self.declare("test -f loaded && exit 75; test ! -f broken")
        self.assertEqual(self.go()["latest"]["result"], "pass")
        self.land("a busy hour", **{"loaded": "x"})
        (self.wt / "loaded").unlink()
        self.land("water: foam on the shore", **{"broken": "x"})
        self.land("tidy the sky", **{"src/sky.txt": "1"})
        latest = self.go()["latest"]
        self.assertEqual((latest["result"], latest["bisect"]), ("fail", "stopped"), latest)
        self.assertNotIn("culprit", latest)

    def test_an_items_check_that_asks_main_check_is_refused_and_fails(self):
        # Before 2.14.0 an item could wait here for a main-branch check; in Thrum that held most work packages an hour.
        self.declare(f"echo run >> {self.count}")
        check = 'python3 "$ORCHESTRATE_SCRIPT" main-check images'
        self.write_done([work_package("WP1", "in_progress", ["pass"], check=check)])
        self.commit_all()
        prof = agent_loop.profile(self.wt)
        tree = agent_loop.verify_tree(self.wt, "WATER", agent_loop.tip(self.wt, prof))
        doc = agent_loop.load_done(self.wt, "WATER", prof)
        [failure] = agent_loop.check_failures(tree, prof, agent_loop.find(doc, "WP1"))
        self.assertIn("main-check", failure)
        self.assertEqual(self.counted(), 0)
        code, line = self.ask(name="images")  # outside an item's check it lists the check
        self.assertEqual((code, line["result"]), (0, "MAIN_CHECKS"))
        with mock.patch.dict(os.environ, {agent_loop.ITEM_CHECK_ENV: "WP1.1"}):
            code, line = self.ask(name="images")
        self.assertEqual((code, line["result"]), (1, "REFUSED"), line)
        self.assertIn("no longer decides", line["why"])


if __name__ == "__main__":
    unittest.main()
