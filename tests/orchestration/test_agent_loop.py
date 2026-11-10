"""Checks for agent_loop's mechanical decisions: the acceptance record, the queue, claims, reviews, plans, owner
commands, profile, pins, locks and report lines. Hosts are fake executables; no model is launched.

Tests named after a review finding (astra_1, fable_3, ...) reproduce that finding from
workbench/review-2026-11-08 and check it no longer happens."""

import argparse
import contextlib
import io
import json
import os
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

SCRIPTS = Path(__file__).resolve().parents[2] / "skills/orchestration/build/scripts"
sys.path.insert(0, str(SCRIPTS))
import agent_loop  # noqa: E402

PROFILE = ("- **Plans:** docs/modules\n- **Integrate:** push\n- **Check:** none\n- **Default host:** codex\n")


def done(*milestones, module="WATER"):
    return {"module": module, "milestones": list(milestones)}


def item(iid, status="open", **proof):
    proof = proof or {"check": "true"}
    return {"id": iid, "statement": f"{iid} works", **proof, "status": status, "evidence": ""}


def milestone(mid, state, statuses, fails=0, **proof):
    items = [item(f"{mid}.{i}", s, **proof) for i, s in enumerate(statuses, 1)]
    return {"id": mid, "name": mid, "state": state, "fails": fails, "replans": 0, "items": items}


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


def release():
    """In-process runs keep their run locks, loop records and signal handlers; tests run many in one process. Ending
    the record first does what a real process does at exit."""
    agent_loop.loop_end()
    for handle in agent_loop._HELD:
        handle.close()
    agent_loop._HELD.clear()
    agent_loop._STOP = False
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


class Decisions(unittest.TestCase):
    def test_escalation_ladder(self):
        self.assertEqual([agent_loop.escalation(n) for n in range(6)],
                         ["none", "same-session", "same-session", "fresh-session", "replan", "replan"])
        self.assertEqual(agent_loop.escalation(4, replans=1), "park")
        self.assertEqual(agent_loop.escalation(2, replans=1), "same-session")
        # every failed review counts as a round; three rounds start a new session even with nothing repeated
        self.assertEqual([agent_loop.escalation(0, rounds=n) for n in range(1, 8)],
                         ["same-session", "same-session", "fresh-session", "same-session", "same-session",
                          "diagnose", "diagnose"])
        self.assertEqual(agent_loop.escalation(1, rounds=6, diagnoses=1), "park")
        self.assertEqual(agent_loop.escalation(4, rounds=6), "replan")  # a repeated failure is the plan's fault first

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
        history = [{"state": "done", "rounds": 3, "pct": [1.0, 1.2, 1.5]},
                   {"state": "done", "rounds": 1, "pct": [2.0, 2.4, 3.0]}]
        open_ms = [{"state": "open", "rounds": 1}] * 4
        recent = {"hours": 12.0, "loop": [1.0, 1.0, 1.0], "other": [0.6, 1.2, 1.8]}
        f = agent_loop.plan_forecast(acc, history, open_ms, recent)
        self.assertEqual(f["per_milestone"], [1.0, 1.8, 3.0])
        self.assertEqual(f["rounds_per_milestone"], 2.0)
        self.assertEqual(f["plan_pct"], [4.0, 7.2, 12.0])
        self.assertEqual(f["other_use_before_reset"], [5.0, 10.0, 15.0])  # at the last 12 h's rate, not the week's
        self.assertFalse(f["warn"])
        self.assertTrue(f["verdict"].startswith("Quota lasts"), f["verdict"])
        self.assertNotIn("runs_out", f)

    def test_plan_forecast_warns_only_when_it_wont_last(self):
        history = [{"state": "done", "rounds": 1, "pct": [4.0, 5.0, 6.0], "builder_hours": 2.0}] * 2
        recent = {"hours": 10.0, "loop": [1.0, 1.0, 1.0], "other": [0.0, 0.0, 0.0]}
        short = agent_loop.plan_forecast({"used_percent": 90.0, "hours_left": 100.0}, history,
                                         [{"state": "open"}] * 4, recent)  # 16-24 % against 10 % left
        self.assertTrue(short["warn"])
        self.assertTrue(short["verdict"].startswith("Quota runs short"), short["verdict"])
        self.assertEqual(short["plan_hours_one_builder"], 8.0)
        self.assertIn("runs_out", short)  # 2.5 %/h uses the 10 % up in four hours
        maybe = agent_loop.plan_forecast({"used_percent": 95.0, "hours_left": 100.0}, history,
                                         [{"state": "open"}], recent)  # 4-6 % against 5 % left
        self.assertTrue(maybe["warn"])
        self.assertTrue(maybe["verdict"].startswith("Quota may run short"), maybe["verdict"])

    def test_plan_forecast_says_too_little_data_without_history(self):
        acc = {"used_percent": 20.0, "hours_left": 100.0}
        recent = {"hours": 12.0, "loop": [0.0] * 3, "other": [0.0] * 3}
        f = agent_loop.plan_forecast(acc, [{"state": "open", "pct": [1, 1, 1]}], [{"state": "open"}] * 2, recent)
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

    def test_definitions_ignore_claims_but_not_checks_or_attended(self):
        m = milestone("M1", "open", ["open"])
        before = agent_loop.definitions(m)
        m["items"][0].update(status="pass", evidence="log", verdict="pass")
        self.assertEqual(agent_loop.definitions(m), before)
        m["items"][0]["attended"] = "plug in the phone"
        self.assertNotEqual(agent_loop.definitions(m), before)

    def test_last_milestone_and_inspected_milestones_need_review(self):
        d = done(milestone("M1", "open", ["pass"]), milestone("M2", "open", ["open"]))
        self.assertFalse(agent_loop.needs_review(d["milestones"][0], d))
        self.assertTrue(agent_loop.needs_review(d["milestones"][1], d))

    def test_validate_rejects_missing_proof_and_empty_milestones(self):
        bare = milestone("M1", "open", ["open"])
        del bare["items"][0]["check"]
        self.assertTrue(any("nothing proves it" in p for p in agent_loop.validate(done(bare))))
        self.assertTrue(any("no items" in p for p in agent_loop.validate(done(milestone("M1", "open", [])))))
        dup = done(milestone("M1", "open", ["open"]), milestone("M1", "open", ["open"]))
        self.assertTrue(any("duplicate" in p for p in agent_loop.validate(dup)))
        self.assertEqual(agent_loop.validate(done(milestone("M1", "open", ["open"]))), [])

    def test_astra_14_malformed_shapes_are_problems_not_crashes(self):
        for bad in ({"milestones": "bad"}, {"milestones": ["x"]}, [], {"milestones": [{"id": 3, "items": "no"}]},
                    done(dict(milestone("M1", "open", ["open"]), fails=-1)),
                    done(dict(milestone("M1", "open", ["open"]), items=[{"id": "a", "statement": "s", "check": 3}]))):
            self.assertTrue(agent_loop.validate(bad), bad)

    def test_fable_8_forward_and_self_needs_in_a_module_are_errors(self):
        d = done(dict(milestone("M1", "open", ["open"]), needs=["M2"]), milestone("M2", "open", ["open"]))
        self.assertTrue(any("comes at or after it" in p for p in agent_loop.validate(d, "WATER")))
        d = done(milestone("M1", "open", ["open"]), dict(milestone("M2", "open", ["open"]), needs=["M9"]))
        self.assertTrue(any("isn't in this module" in p for p in agent_loop.validate(d, "WATER")))
        ok = done(milestone("M1", "open", ["open"]), dict(milestone("M2", "open", ["open"]), needs=["M1", "CORE:M3"]))
        self.assertEqual(agent_loop.validate(ok, "WATER"), [])


class Queue(unittest.TestCase):
    """next_step is the one readiness predicate behind ready, status and run."""

    def test_astra_2_a_done_state_without_accepted_review_doesnt_release_dependents(self):
        core = done(milestone("M1", "done", ["pass"], inspect="captures"), module="CORE")
        water = done(dict(milestone("M1", "open", ["open"]), needs=["CORE:M1"]))
        proj = {"CORE": entry_for(core), "WATER": entry_for(water)}
        self.assertEqual(agent_loop.next_step("CORE", proj)["status"], "review_owed")
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual((step["status"], step["needs"]), ("waiting", ["CORE:M1"]))

    def test_astra_2_a_forged_done_without_a_record_acceptance_isnt_accepted(self):
        water = done(milestone("M1", "open", ["open"]), milestone("M2", "open", ["open"]))
        e = entry_for(water)
        water["milestones"][0].update(state="done")  # written into the file, never accepted by the loop
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["milestone"], "M1")

    def test_astra_2_and_fable_17_open_milestone_with_passing_items_is_still_next(self):
        water = done(milestone("M1", "open", ["pass"]), milestone("M2", "open", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water)})["milestone"], "M1")
        water = done(milestone("M1", "in_progress", ["pass"]), milestone("M2", "open", ["open"]))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)})
        self.assertEqual((step["milestone"], step["status"]), ("M1", "ready"))

    def test_milestones_run_in_file_order_not_in_progress_first(self):
        water = done(milestone("M1", "done", ["pass"]), milestone("M2", "open", ["open"]),
                     milestone("M3", "in_progress", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water)})["milestone"], "M2")

    def test_fable_8_parked_needs_and_cycles_are_reported_not_waited_on(self):
        prk = done(milestone("M1", "parked", ["open"]), module="PRK")
        water = done(dict(milestone("M1", "open", ["open"]), needs=["PRK:M1"]))
        proj = {"PRK": entry_for(prk), "WATER": entry_for(water)}
        self.assertEqual(agent_loop.next_step("PRK", proj)["status"], "parked")
        step = agent_loop.next_step("WATER", proj)
        self.assertEqual(step["status"], "invalid")
        self.assertIn("parked", step["problems"][0])
        a = done(dict(milestone("M1", "open", ["open"]), needs=["B:M1"]), module="A")
        b = done(dict(milestone("M1", "open", ["open"]), needs=["A:M1"]), module="B")
        cycles = agent_loop.need_cycles({"A": entry_for(a), "B": entry_for(b)})
        self.assertEqual(set(cycles), {"A", "B"})

    def test_unplanned_module_is_waiting_and_missing_milestone_is_invalid(self):
        core = done(milestone("M1", "open", ["open"]), module="CORE")
        water = done(dict(milestone("M1", "open", ["open"]), needs=["PAY:M1"]))
        proj = {"WATER": entry_for(water), "CORE": entry_for(core)}
        self.assertEqual(agent_loop.next_step("WATER", proj)["needs"], ["PAY:M1 (not planned)"])
        water["milestones"][0]["needs"] = ["CORE:M7"]
        proj["WATER"] = entry_for(water)
        self.assertEqual(agent_loop.next_step("WATER", proj)["status"], "invalid")

    def test_design_review_gates_a_module(self):
        water = done(milestone("M1", "open", ["open"]))
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(water, design_ok=False)})["status"],
                         "design_owed")

    def test_blocked_and_taken(self):
        water = done(dict(milestone("M1", "blocked", ["open"]), blocked="needs the iPhone"))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)})
        self.assertEqual((step["status"], step["blocked"]), ("blocked", "needs the iPhone"))
        water = done(milestone("M1", "open", ["open"]))
        step = agent_loop.next_step("WATER", {"WATER": entry_for(water)}, {("WATER", "M1"): "other"}, "me")
        self.assertEqual((step["status"], step["by"]), ("taken", "other"))

    def test_unauthorised_definitions_are_invalid(self):
        water = done(milestone("M1", "open", ["open"]))
        e = entry_for(water)
        water["milestones"][0]["items"][0]["check"] = "true # weakened"
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": e})["status"], "invalid")


class Deltas(unittest.TestCase):
    def setUp(self):
        self.before = done(milestone("M1", "in_progress", ["open"]), milestone("M2", "open", ["open"]))

    def after(self):
        return json.loads(json.dumps(self.before))

    def test_builder_may_change_only_its_fields_on_its_milestone(self):
        a = self.after()
        a["milestones"][0]["state"] = "claimed"
        a["milestones"][0]["items"][0].update(status="pass", evidence="log")
        self.assertEqual(agent_loop.delta_problems(self.before, a, "build", "M1"), [])
        a["milestones"][0]["replans"] = 1
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
        before = done(milestone("M1", "claimed", ["pass"]), milestone("M2", "open", ["open"]))
        a = done(milestone("M1", "done", ["pass"]))
        self.assertTrue(agent_loop.delta_problems(before, a, "review", "M1"))

    def test_a_reviewer_cant_set_the_counts(self):
        before = done(milestone("M1", "claimed", ["pass"]))
        for field in ("rounds", "replans", "diagnoses"):
            a = json.loads(json.dumps(before))
            a["milestones"][0].update(state="in_progress", **{field: 2})
            self.assertTrue(agent_loop.delta_problems(before, a, "review", "M1"), field)

    def test_planner_cant_grant_passes(self):
        a = self.after()
        a["milestones"][1]["state"] = "done"
        self.assertTrue(agent_loop.delta_problems(self.before, a, "plan"))


class Profiles(unittest.TestCase):
    def test_profile_reads_labelled_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "ORCHESTRATE.md").write_text(
                "- **Plans:** [docs/design/modules](docs/design/modules/)  *(read by the loop)*\n"
                "- **Evidence:** docs/my evidence  *(loop)*\n"
                "- **Check:** `npm run check < /dev/null`  *(loop)*\n"
                "- **Integrate:** local  *(loop)*\n"
                "- **Branch:** trunk  *(loop: integrate here)*\n"
                "- **Codex sandbox:** danger-full-access  *(loop)*\n"
                "- **Codex generator:** gpt-6.1-sol, high\n- **Writable roots:** ~/.cargo, ~/.npm\n")
            p = agent_loop.profile(Path(tmp), strict=True)
            self.assertEqual((p["plans"], p["branch"], p["model"], p["effort"], p["evidence"], p["check"], p["sandbox"]),
                             ("docs/design/modules", "trunk", "gpt-6.1-sol", "high", "docs/my evidence",
                              "npm run check < /dev/null", "danger-full-access"))
            self.assertEqual(p["roots"], ["~/.cargo", "~/.npm"])
            self.assertEqual(p["graded_examples"], "docs/my evidence/graded-examples.md")

    def test_astra_7_and_fable_1_missing_integrate_or_check_fails_strict_and_never_defaults_to_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            for text in ("# profile\n", "- **Check:** none\n", "- **Integrate:** push\n"):
                Path(tmp, "ORCHESTRATE.md").write_text(text)
                with self.assertRaises(SystemExit, msg=text):
                    agent_loop.profile(Path(tmp), strict=True)
            Path(tmp, "ORCHESTRATE.md").write_text("# profile\n")
            with contextlib.redirect_stderr(io.StringIO()):
                loose = agent_loop.profile(Path(tmp))
            self.assertEqual((loose["integrate"], loose["check"]), ("local", ""))
            Path(tmp, "ORCHESTRATE.md").write_text("- **Integrate:** push\n- **Check:** none\n")
            self.assertEqual(agent_loop.profile(Path(tmp), strict=True)["check"], "")

    def test_profile_strict_rejects_missing_unfilled_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                agent_loop.profile(Path(tmp), strict=True)
            good = "- **Integrate:** push\n- **Check:** none\n"
            for bad in ("- **Evidence:** <where review files go>\n", "- **Codex sandbox:** open\n",
                        "- **Codex generator:** gpt-6.1-sol turbo\n", "- **Integrate:** pull-request\n- **Check:** none\n"):
                Path(tmp, "ORCHESTRATE.md").write_text(good + bad if "Integrate" not in bad else bad)
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

    def test_planner_host_sends_planners_to_that_host_unless_the_lead_names_one(self):
        base = "- **Integrate:** local\n- **Check:** none\n- **Default host:** codex\n"
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
        base = "- **Integrate:** local\n- **Check:** none\n"
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


class Processes(unittest.TestCase):
    def tearDown(self):
        agent_loop._STOP = False

    def test_fable_6_a_pause_stops_the_whole_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "child"
            threading.Timer(0.5, lambda: setattr(agent_loop, "_STOP", True)).start()
            started = time.time()
            code, _, _ = agent_loop.run_proc(["sh", "-c", f"sleep 30 & echo $! > {pidfile}; wait"], None, 60)
            self.assertEqual(code, 130)
            self.assertLess(time.time() - started, 15)
            pid = int(pidfile.read_text())
            time.sleep(0.2)
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_astra_13_a_missing_cli_is_a_controlled_result(self):
        self.assertEqual(agent_loop.run_proc(["/no/such/host"], None, 5)[0], 127)


FAKE_HOST = """#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
if "--help" in sys.argv:
    print("usage: codex exec [--json]")
    sys.exit(0)
if "--version" in sys.argv:
    print(os.environ.get("FAKE_VERSION", "fake-cli 9.9.9"))
    sys.exit(0)
role = os.environ.get("ORCHESTRATE_ROLE", "build")
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "role": role,
                          "api_key": "ANTHROPIC_API_KEY" in os.environ}) + "\\n")
if os.environ.get("FAKE_EXIT"):
    sys.exit(int(os.environ["FAKE_EXIT"]))
cwd = Path(os.getcwd())
if os.environ.get("FAKE_LOOPS"):  # what `loops` shows while this turn runs
    seen = subprocess.run([sys.executable, os.environ["FAKE_LOOPS_SCRIPT"], "loops", "--json", "--repo", str(cwd)],
                          capture_output=True, text=True)
    with open(os.environ["FAKE_LOOPS"], "a") as out:
        out.write(json.dumps(json.loads(seen.stdout)) + "\\n")
def git(*a):
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          capture_output=True, text=True)
reply = os.environ.get("FAKE_REPLY", "DONE")
path = cwd / "docs/modules/WATER-DONE.json"
if role == "build" and os.environ.get("FAKE_PASS") == "1":
    d = json.loads(path.read_text())
    for m in d["milestones"]:
        if m["state"] in ("open", "in_progress"):
            m["state"] = os.environ.get("FAKE_STATE", "claimed")
            for i in m["items"]:
                if i.get("attended") and os.environ.get("FAKE_SKIP_ATTENDED"):
                    continue
                i["status"], i["evidence"] = "pass", "run log"
                if os.environ.get("FAKE_WEAKEN"):
                    i["check"] = "true"
            if os.environ.get("FAKE_WEAKEN"):
                m["replans"] = m.get("replans", 0) + 1
            break
    if os.environ.get("FAKE_FORGE"):
        last = d["milestones"][-1]
        last["state"] = "done"
        for i in last["items"]:
            i.update(status="pass", evidence="x", verdict="pass", review="x")
    path.write_text(json.dumps(d))
    if os.environ.get("FAKE_COMMIT", "1") == "1":
        git("commit", "-qam", "pass")
        git("pull", "-q", "--rebase", "origin", "main")
        git("push", "-q", "origin", "main")
    if os.environ.get("FAKE_UPSTREAM_BREAK"):
        (cwd / "broken").write_text("x")
        git("add", "broken")
        git("commit", "-qm", "someone else breaks it")
        git("push", "-q", "origin", "main")
        git("reset", "-q", "--hard", "HEAD~1")
elif role == "review":
    mode = os.environ.get("FAKE_REVIEW", "pass")
    if os.environ.get("FAKE_DURING"):  # something lands on the tip while the review runs
        subprocess.run(os.environ["FAKE_DURING"], shell=True, check=True, capture_output=True)
    d = json.loads(path.read_text())
    target = next((m for m in d["milestones"] if m["state"] == "claimed"), None)
    ev = cwd / "docs/evidence/WATER"
    ev.mkdir(parents=True, exist_ok=True)
    if mode == "design":
        (ev / "design-review.md").write_text("design is fine")
        reply = "DESIGN OK"
    elif mode == "design_changes":
        (ev / "design-review.md").write_text("the design needs a second pass")
        reply = "DESIGN CHANGES: the water surface has no LOD plan"
    elif mode == "nothing":
        reply = "PASS M999"
    else:
        mid, verdict = target["id"], ("fail" if mode == "fail" else "pass")
        for i in target["items"]:
            i["verdict"], i["review"] = verdict, f"docs/evidence/WATER/{mid}-review.md"
        if verdict == "pass":
            target["state"] = "done"
            if os.environ.get("FAKE_PASS_FINDINGS"):
                target["findings"] = [{"name": "a nit"}]
        else:
            target["state"] = "in_progress"
            target["findings"] = [{"name": os.environ.get("FAKE_FINDING", "the water is flat") + f" ({i['id']})",
                                   "item": i["id"]} for i in target["items"]]
            if os.environ.get("FAKE_DIFFERENT"):
                for f in target["findings"]:
                    f["different"] = os.environ["FAKE_DIFFERENT"]
            if os.environ.get("FAKE_NO_FINDINGS"):
                target.pop("findings")
        if mode == "delete":
            d["milestones"] = [m for m in d["milestones"] if m is target or m["state"] != "open"]
        path.write_text(json.dumps(d))
        n = int(target.get("rounds", 0) or 0) + (verdict != "pass")  # the loop counts this round after the fake
        text = f"review of {mid}: {verdict}, failed round {n}"
        if os.environ.get("FAKE_CAPTURE"):
            (ev / f"{mid}-review").mkdir(exist_ok=True)
            (ev / f"{mid}-review" / "shot.png").write_bytes(f"PNG {n}".encode())
            text += f"; see [the shot]({mid}-review/shot.png)"
        (ev / f"{mid}-review.md").write_text(text)
        if mode == "overreach":
            (cwd / "src.txt").write_text("fixed it myself")
        reply = f"PASS {mid}" if verdict == "pass" else f"FAIL {mid}: 1 fail, 0 cant_tell, 0 outside the items"
elif role == "plan":
    mode = os.environ.get("FAKE_PLAN", "")
    if os.environ.get("FAKE_DURING"):  # something lands on the tip while the planner works
        subprocess.run(os.environ["FAKE_DURING"], shell=True, check=True, capture_output=True)
    if mode == "catch_up":  # the planner brings the tip into its worktree, and writes a test outside the plans
        git("fetch", "-q", "origin")
        git("merge", "-q", "--ff-only", "origin/main")
        (cwd / "acceptance").mkdir(exist_ok=True)
        (cwd / "acceptance/test_pay.py").write_text("assert True\\n")
    turn = sum(json.loads(l)["role"] == "plan" for l in open(os.environ["FAKE_LOG"]))
    files = ["docs/modules/PAY-DONE.json"] + ([] if mode == "nodesign" else ["docs/modules/PAY.md",
                                                                             "docs/modules/PAY-PLAN.md"])
    if mode == "forge":
        (cwd / "docs/modules/WATER-ACCEPTED.json").write_text("{}")
        reply = "PLANNED: docs/modules/WATER-ACCEPTED.json"
    elif mode == "progress" or (mode == "late" and turn == 1):
        reply = "I've read the brief. Next I'll write the PAY design and its done-when file."
    elif mode in ("replan", "replan_counted"):  # re-plans WATER M1; `replan_counted` also does the bookkeeping
        water = cwd / "docs/modules/WATER-DONE.json"
        d = json.loads(water.read_text())
        m = d["milestones"][0]
        m["items"][0]["statement"] = "a smaller first step"
        if mode == "replan_counted":
            m.update(fails=0, replans=m.get("replans", 0) + 1, state="open")
        water.write_text(json.dumps(d))
        (cwd / "docs/modules/WATER.md").write_text("# Water design, re-planned")
        reply = "Re-planned M1.\\nPLANNED: docs/modules/WATER-DONE.json, docs/modules/WATER.md"
    elif mode.startswith("keep_"):  # a diagnosis that keeps WATER M1's plan and names who acts
        reply = f"Read every round.\\nKEEP WATER M1: {mode[5:]}: the {mode[5:]} has to act"
    elif mode == "blocked":
        (cwd / "docs/modules/PAY.md").write_text("# Pay design, half done")
        reply = "BLOCKED: the owner must choose the payment provider"
    else:
        if mode != "nodesign":
            (cwd / "docs/modules/PAY.md").write_text("# Pay design")
            (cwd / "docs/modules/PAY-PLAN.md").write_text("# Pay plan" + os.environ.get("FAKE_ASSUME", ""))
        (cwd / "docs/modules/PAY-DONE.json").write_text(json.dumps({"module": "PAY", "milestones": [
            {"id": "M1", "name": "pay", "state": "open", "fails": 0, "replans": 0,
             "items": [{"id": "M1.1", "statement": "pays", "check": "true", "status": "open", "evidence": ""}]}]}))
        reply = "Planned PAY. No owner decisions.\\nPLANNED: " + ", ".join(files)
        side = os.environ.get("FAKE_PLAN_SIDE")
        if side:  # a planner that forges a record, commits it and puts it on the tip itself, or fakes the tip
            (cwd / "docs/modules/WATER-ACCEPTED.json").write_text('{"forged": true}')
            git("add", "docs/modules/WATER-ACCEPTED.json")
            git("commit", "-qm", "tidy")
            git(*(["push", "-q", "origin", "HEAD:main"] if side == "push" else
                  ["update-ref", "refs/remotes/origin/main", "HEAD"]))
if "claude" in Path(sys.argv[0]).name:
    model = sys.argv[sys.argv.index("--model") + 1]
    sid = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a in ("--session-id", "--resume")), "s1")
    print(json.dumps({"type": "system", "subtype": "init", "session_id": sid, "model": model}))
    result = {"type": "result", "subtype": "success", "session_id": sid, "result": reply, "is_error": False}
    if os.environ.get("FAKE_COST"):  # Claude's total_cost_usd is the session's running total
        result.update(total_cost_usd=float(os.environ["FAKE_COST"]),
                      usage={"input_tokens": 10, "cache_read_input_tokens": 5, "output_tokens": 2})
    print(json.dumps(result))
else:
    print(json.dumps({"type": "thread.started", "thread_id": "t1"}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": reply}}))
    if os.environ.get("FAKE_USAGE"):
        print(json.dumps({"type": "turn.completed",
                          "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 7}}))
"""

FAKE_ENV = ("FAKE_DIFFERENT", "FAKE_NO_FINDINGS", "FAKE_PASS_FINDINGS", "FAKE_FINDING", "FAKE_VERSION", "FAKE_STATE", "FAKE_WEAKEN", "FAKE_FORGE", "FAKE_UPSTREAM_BREAK", "FAKE_REVIEW", "FAKE_PLAN",
            "FAKE_EXIT", "FAKE_SKIP_ATTENDED", "FAKE_LOOPS", "FAKE_LOOPS_SCRIPT", "FAKE_USAGE", "FAKE_COST", "FAKE_CAPTURE",
            "FAKE_DURING", "FAKE_ASSUME", "FAKE_PLAN_SIDE", "ORCHESTRATE_ROLE",
            "ORCHESTRATE_HEADLESS")


class Repo(unittest.TestCase):
    """A throwaway repository with a bare origin, a fake host, and a module whose plan is authorised."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.root, self.wt, self.origin, self.home = root, root / "wt", root / "origin.git", root / "codex-home"
        self.home.mkdir()
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.sh("git", "init", "-q", "-b", "main", str(self.wt))
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@t")
        (self.wt / "docs/modules").mkdir(parents=True)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE)
        self.write_done([milestone("M1", "open", ["open"]), milestone("M2", "open", ["open"])])
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "origin", "main")
        fake = root / "codex"
        fake.write_text(FAKE_HOST)
        fake.chmod(0o755)
        self.log = root / "log"
        self.saved = (agent_loop.CODEX, agent_loop.CODEX_HOME, agent_loop.CLAUDE, agent_loop.CLAUDE_APP_STORE,
                      agent_loop.CLAUDE_HOME, agent_loop.AGENTS_HOME, agent_loop.LOOPS_DIR)
        # Loop records go to this test's folder, for the loop in this process and for any process it starts.
        self.loops = agent_loop.LOOPS_DIR = root / "loops"
        self.saved_loops_env = os.environ.get("ORCHESTRATE_LOOPS_DIR")
        os.environ["ORCHESTRATE_LOOPS_DIR"] = str(self.loops)
        agent_loop.CLAUDE_HOME, agent_loop.AGENTS_HOME = root / "claude-home", root / "agents-home"
        agent_loop.CODEX, agent_loop.CODEX_HOME = str(fake), self.home
        self.cache_dir = agent_loop.codex_quota.CACHE_DIR
        agent_loop.codex_quota.CACHE_DIR = root / "quota-cache"
        # No app on this machine counts: the Codex IPC socket lives under the fake CODEX_HOME, and Claude desktop's
        # session store is pointed at a folder that doesn't exist. Visible-session tests fake the apps explicitly.
        agent_loop.CLAUDE_APP_STORE = root / "no-claude-desktop"
        for key in FAKE_ENV:
            os.environ.pop(key, None)
        os.environ.update(FAKE_LOG=str(self.log), FAKE_PASS="1", FAKE_REPLY="DONE", FAKE_COMMIT="1")

    def tearDown(self):
        release()
        (agent_loop.CODEX, agent_loop.CODEX_HOME, agent_loop.CLAUDE, agent_loop.CLAUDE_APP_STORE,
         agent_loop.CLAUDE_HOME, agent_loop.AGENTS_HOME, agent_loop.LOOPS_DIR) = self.saved
        if self.saved_loops_env is None:
            os.environ.pop("ORCHESTRATE_LOOPS_DIR", None)
        else:
            os.environ["ORCHESTRATE_LOOPS_DIR"] = self.saved_loops_env
        agent_loop.codex_quota.CACHE_DIR = self.cache_dir
        for key in FAKE_ENV:
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def sh(self, *args, cwd=None):
        return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)

    def git(self, *args, where=None):
        return self.sh("git", "-C", str(where or self.wt), *args)

    def write_done(self, milestones, design_ok=True, authorise=True, module="WATER", where=None):
        """Writes the done-when file and, as a planner turn through the loop would, its acceptance record."""
        where = where or self.wt
        doc = done(*milestones, module=module)
        (where / f"docs/modules/{module}-DONE.json").write_text(json.dumps(doc))
        if authorise:
            rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
            rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)} if design_ok else None
            (where / f"docs/modules/{module}-ACCEPTED.json").write_text(json.dumps(rec))

    def read_done(self, ref="origin/main"):
        self.git("fetch", "-q", "origin")
        return json.loads(self.git("show", f"{ref}:docs/modules/WATER-DONE.json").stdout)

    def read_record(self, ref="origin/main"):
        self.git("fetch", "-q", "origin")
        return json.loads(self.git("show", f"{ref}:docs/modules/WATER-ACCEPTED.json").stdout)

    def commit_all(self, where=None):
        where = where or self.wt
        self.git("add", "-A", where=where)
        self.git("commit", "-qm", "x", where=where)
        self.git("pull", "-q", "--rebase", "origin", "main", where=where)
        self.git("push", "-q", "origin", "main", where=where)

    def call(self, func, **kw):
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                func(argparse.Namespace(**kw))
        finally:
            release()
        return json.loads(out.getvalue().splitlines()[-1])

    def run_loop(self, **kw):
        args = dict(module="WATER", worktree=str(self.wt), milestone=None, fresh=False, message=None,
                    budget_hours=4.0, turn_timeout_hours=0.1, host=None, model=None, effort=None, owner_rule=None,
                    clear_owner_rules=False, no_design_review=False)
        args.update(kw)
        return self.call(agent_loop.cmd_run, **args)

    def review(self, milestone_id="M1", commit="HEAD", **kw):
        args = dict(module="WATER", milestone=milestone_id, commit=commit, worktree=str(self.wt), host=None,
                    model=None, effort=None, turn_timeout_hours=0.1)
        args.update(kw)
        return self.call(agent_loop.cmd_review, **args)

    def ready(self, where=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_ready(argparse.Namespace(worktree=str(where or self.wt)))
        return json.loads(out.getvalue())

    def owner(self, action, milestone_id, reason="owner said so", where=None, item=None):
        return self.call(agent_loop.cmd_owner, action=action, module="WATER", milestone=milestone_id, item=item,
                         worktree=str(where or self.wt), text=reason)

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def state(self):
        return json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())


class Building(Repo):
    def test_quota_costs_the_loops_milestones_and_counts_other_threads_apart(self):
        import test_codex_quota as fixtures
        self.assertEqual(self.run_loop()["result"], "CLAIMED")  # M1, in the fake host's thread t1
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
        self.assertEqual(set(summary) - {"runs_out", "note"}, {"used_percent", "resets_at", "burn", "verdict", "warn",
                                                                "detail"})

    def test_claims_check_only_milestone_and_accepts_it_in_the_record(self):
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("CLAIMED", False))
        self.assertEqual(self.read_record()["milestones"]["M1"]["accepted"]["by"], "checks")
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M2")
        self.assertIn("quota", result)

    def test_fable_16_build_prompt_names_the_skill_file(self):
        self.run_loop()
        self.assertIn("build-milestone/SKILL.md", self.calls()[0]["argv"][-1])
        self.assertIn(" land --worktree .", self.calls()[0]["argv"][-1])

    def test_astra_1_weakening_a_check_and_bumping_replans_is_invalid_and_stays_invalid(self):
        self.write_done([milestone("M1", "open", ["open"], check="test -f real-proof"),
                         milestone("M2", "open", ["open"])])
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
        self.write_done([milestone("M1", "open", ["open"], check="test ! -f broken"), milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_UPSTREAM_BREAK="1")
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "BUDGET")
        self.assertIn("M1.1 `test ! -f broken` exited 1", self.state()["claim_blocked"])

    def test_astra_5_a_check_that_leaves_untracked_files_blocks_the_claim(self):
        self.write_done([milestone("M1", "open", ["open"], check="touch new-helper"), milestone("M2", "open", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "BUDGET")
        self.assertIn("left changes", self.state()["claim_blocked"])

    def test_invalid_file_stops_before_any_turn(self):
        bare = milestone("M1", "open", ["open"])
        del bare["items"][0]["check"]
        self.write_done([bare], authorise=False)
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "INVALID")
        self.assertFalse(self.log.exists())

    def test_astra_14_unparseable_done_when_file_is_invalid_not_a_crash(self):
        (self.wt / "docs/modules/WATER-DONE.json").write_text("{not json")
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "INVALID")

    def test_uncommitted_pass_is_not_claimed(self):
        os.environ.update(FAKE_COMMIT="0")
        self.assertEqual(self.run_loop(budget_hours=0.0)["result"], "BUDGET")
        self.assertIn("uncommitted", self.state()["claim_blocked"])

    def test_untracked_files_block_the_claim(self):
        (self.wt / "helper.sh").write_text("echo hi\n")
        self.run_loop(budget_hours=0.0)
        self.assertIn("untracked", self.state()["claim_blocked"])

    def test_failing_profile_check_blocks_the_claim(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("none", "`sh -c 'exit 4'`"))
        self.commit_all()
        self.run_loop(budget_hours=0.0)
        self.assertIn("Check `sh -c 'exit 4'` exited 4", self.state()["claim_blocked"])

    def test_done_without_a_claim_never_finishes_as_done(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        result = self.run_loop()
        self.assertEqual(result["result"], "UNCLAIMED")
        self.assertIn("items not yet pass", result["reasons"][0])
        self.assertEqual(len(self.calls()), 3)

    def test_builder_done_on_reviewed_milestone_is_not_a_claim(self):
        os.environ.update(FAKE_STATE="done")
        self.write_done([milestone("M1", "open", ["open"], inspect="captures"), milestone("M2", "open", ["open"])])
        self.commit_all()
        self.run_loop(budget_hours=0.0)
        self.assertIn("set its state to claimed", self.state()["claim_blocked"])

    def test_claimed_milestone_blocks_the_next_until_reviewed(self):
        self.write_done([milestone("M1", "claimed", ["pass"], inspect="captures"), milestone("M2", "open", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["milestone"]), ("REVIEW_OWED", "M1"))

    def test_design_owed_holds_the_module(self):
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False)
        self.commit_all()
        self.assertEqual(self.run_loop(no_design_review=True)["result"], "DESIGN_OWED")
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design")["verdict"], "DESIGN OK")
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "CLAIMED")

    def test_a_plan_revised_before_its_design_review_is_authorised_by_that_review(self):
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        self.review("design")  # the record adopts the first definitions here
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.write_done([milestone("M1", "open", ["open"], check="test -n revised")], authorise=False)
        (self.wt / "docs/evidence/WATER/design-review.md").unlink()  # the fake reviewer rewrites the same text
        self.commit_all()
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "INVALID")  # revised outside a planner turn
        os.environ.update(FAKE_REVIEW="design")
        second = self.review("design")
        self.assertEqual(second.get("verdict"), "DESIGN OK", second)
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "CLAIMED")
        self.assertEqual(self.read_record()["milestones"]["M1"]["authorised"]["by"], "design review")

    def test_blocked_report_records_blocked_state_and_unblock_requeues(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device attached")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["blocked"]), ("blocked", "no device attached"))
        self.assertEqual(self.ready()["blocked"][0]["blocked"], "no device attached")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_unblock(argparse.Namespace(module="WATER", milestone="M1", worktree=str(self.wt)))
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M1")

    def test_attended_items_are_batched_into_the_blocked_reason(self):
        self.write_done([dict(milestone("M1", "open", ["open"]), items=[
            item("M1.1"), item("M1.2", inspect="on the phone", attended="plug in the iPhone")]),
            milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_ATTENDED="1", FAKE_REPLY="BLOCKED: the iPhone item needs a person")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        self.assertIn("attended items need a person or hardware: M1.2", self.read_done()["milestones"][0]["blocked"])

    def test_second_blocked_report_with_an_active_goal_finishes(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device")
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.assertEqual(self.run_loop()["result"], "BLOCKED")
        self.assertEqual(len(self.calls()), 2)

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
        self.assertEqual(result["result"], "FLOOR")
        self.assertIn("couldn't start", result["reason"])

    def test_claude_builder_claims_with_a_clean_environment(self):
        fake = self.root / "claude"
        fake.write_text(FAKE_HOST)
        fake.chmod(0o755)
        agent_loop.CLAUDE = str(fake)
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret"}):
            result = self.run_loop(host="claude")
        self.assertEqual(result["result"], "CLAIMED")
        call = self.calls()[0]
        self.assertFalse(call["api_key"])
        self.assertIn("--effort", call["argv"])
        self.assertEqual(call["argv"][call["argv"].index("--model") + 1], "claude-opus-5-5")

    def test_waiting_when_needs_are_unmet(self):
        self.write_done([dict(milestone("M1", "open", ["open"]), needs=["CORE:M1"])])
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
        _, seen = agent_loop.own_progress(self.wt, 10 ** 9, "docs/modules")
        self.git("pull", "-q", "--rebase", "origin", "main")
        moved, seen = agent_loop.own_progress(self.wt, seen, "docs/modules")
        self.assertFalse(moved)
        (self.wt / "mine.txt").write_text("mine")
        self.git("add", "-A")
        self.git("commit", "-qm", "mine")
        self.assertTrue(agent_loop.own_progress(self.wt, seen, "docs/modules")[0])


class Reviewing(Repo):
    def setUp(self):
        super().setUp()
        self.write_done([milestone("M1", "open", ["open"], inspect="frame sequence"), milestone("M2", "open", ["open"])])
        self.commit_all()

    def claim(self):
        result = self.run_loop()
        self.assertEqual((result["result"], result["review"]), ("CLAIMED", True))
        return result["commit"]

    def test_a_passing_review_lands_and_accepts(self):
        commit = self.claim()
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"]), ("REVIEWED", "PASS"))
        rec = self.read_record()["milestones"]["M1"]
        self.assertEqual((rec["accepted"]["by"], rec["accepted"]["commit"]), ("review", commit))
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M2")

    def test_fable_3_a_failed_review_resets_the_items_that_failed(self):
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="fail")
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["verdict"], result["fails"], result["rounds"], result["ladder"]),
                         ("REVIEWED", "FAIL", 0, 1, "same-session"))
        self.assertEqual(result["next"]["ladder"], "same-session")
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
        self.assertTrue(last["argv"][-1].startswith("FINDINGS\n\nObjective: M1 claimed"))

    def test_the_loop_parks_a_milestone_when_the_ladder_runs_out(self):
        self.write_done([failed_before(dict(milestone("M1", "open", ["open"], inspect="frames"), fails=3, replans=1,
                                            rounds=3)), milestone("M2", "open", ["open"])])
        self.commit_all()
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="fail")
        parked = self.review(commit=commit)
        self.assertEqual((parked["fails"], parked["repeated"]), (4, ["the water is flat (M1.1)"]))
        self.assertEqual((parked["ladder"], parked["next"]["ladder"], parked["next"]["by"]), ("park", "park", "owner"))
        self.assertIn(" owner unpark --module WATER --milestone M1 ", parked["next"]["command"])
        self.assertEqual(self.read_done()["milestones"][0]["state"], "parked")

    def test_astra_3_review_of_a_missing_commit_is_invalid(self):
        self.claim()
        result = self.review(commit="does-not-exist")
        self.assertEqual(result["result"], "INVALID")
        self.assertIn("doesn't exist", result["problems"][0])

    def test_astra_3_a_reviewer_that_writes_nothing_is_invalid_and_nothing_lands(self):
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="nothing")
        result = self.review(commit=commit)
        self.assertEqual((result["result"], result["landed"]), ("INVALID", False))
        self.assertTrue(any("M999" in p for p in result["problems"]))
        self.assertEqual(self.read_done()["milestones"][0]["state"], "claimed")

    def test_astra_4_reviewer_source_edits_are_caught_and_not_landed(self):
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="overreach")
        result = self.review(commit=commit)
        self.assertEqual(result["result"], "INVALID")
        self.assertTrue(any("src.txt" in p for p in result["problems"]))
        self.git("fetch", "-q", "origin")
        self.assertNotIn("src.txt", self.git("ls-tree", "--name-only", "origin/main").stdout)

    def test_astra_4_reviewer_deleting_a_milestone_is_caught(self):
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="delete")
        self.assertEqual(self.review(commit=commit)["result"], "INVALID")

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
        self.assertEqual(self.review(commit=commit)["result"], "FLOOR")

    def test_owner_accept_skips_review_and_rereview_keeps_the_old_review(self):
        self.claim()
        result = self.owner("accept", "M1", reason="typo fix")
        self.assertEqual(result["result"], "DONE")
        accepted = self.read_record()["milestones"]["M1"]["accepted"]
        self.assertEqual((accepted["by"], accepted["words"]), ("owner decision", "typo fix"))
        self.assertEqual(self.ready()["ready"][0]["milestone"], "M2")
        # Now a reviewed acceptance, then a re-review.
        self.owner("rereview", "M1")
        self.git("pull", "-q", "--rebase", "origin", "main")
        result = self.review(commit=self.read_record()["milestones"]["M1"]["claim"]["commit"])
        self.assertEqual(result["verdict"], "PASS")
        again = self.owner("rereview", "M1", reason="too lenient")
        self.assertEqual(self.read_done()["milestones"][0]["state"], "claimed")
        self.git("fetch", "-q", "origin")
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout
        self.assertIn("docs/evidence/WATER/M1-review-1.md", files)
        self.assertTrue(again["commit"])

    def test_owner_commands_are_refused_inside_a_loop_session(self):
        for verb in ("accept", "rereview", "unpark", "scope", "release", "answer"):
            with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit) as stop:
                agent_loop.cmd_owner(argparse.Namespace(action=verb, module="WATER", milestone="M1", item=None,
                                                        text="yes", worktree=str(self.wt)))
            self.assertIn(f"owner {verb} can't run inside a session the loop started", str(stop.exception))

    def test_astra_1_a_record_edited_outside_the_loop_blocks_the_claim(self):
        start = agent_loop.head_commit(self.wt)
        rec = json.loads((self.wt / "docs/modules/WATER-ACCEPTED.json").read_text())
        rec["milestones"]["M1"]["accepted"] = {"by": "review"}
        (self.wt / "docs/modules/WATER-ACCEPTED.json").write_text(json.dumps(rec))
        self.commit_all()
        prof = agent_loop.profile(self.wt, strict=True)
        self.assertEqual(len(agent_loop.record_tampering(self.wt, prof, start, agent_loop.head_commit(self.wt))), 1)


class OwnerAndPlanner(Repo):
    def test_fable_7_owner_scope_change_authorises_without_spending_a_replan(self):
        d = json.loads((self.wt / "docs/modules/WATER-DONE.json").read_text())
        d["milestones"][0]["items"][0]["statement"] = "M1.1 works, and faster"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(d))
        self.assertEqual(self.owner("scope", "M1")["result"], "DONE")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["replans"], m1["fails"], m1["items"][0]["statement"]), (0, 0, "M1.1 works, and faster"))
        self.assertEqual(self.read_record()["milestones"]["M1"]["authorised"]["by"], "owner decision")
        self.git("checkout", "-q", "--", ".")
        self.assertEqual(self.run_loop()["result"], "CLAIMED")

    def test_owner_unpark(self):
        self.write_done([dict(milestone("M1", "parked", ["open"]), fails=4), milestone("M2", "open", ["open"])])
        self.commit_all()
        self.assertEqual(self.run_loop()["result"], "PARKED")
        self.owner("unpark", "M1")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["fails"]), ("open", 0))

    def test_fable_9_a_planned_module_is_committed_landed_and_queued(self):
        result = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="plan PAY", host=None, model=None,
                           effort=None, turn_timeout_hours=0.1)
        self.assertEqual((result["result"], result["landed"]), ("PLANNED", True))
        self.assertEqual(result["design_review_owed"], ["PAY"])
        self.assertIn("features.multi_agent=false", self.calls()[0]["argv"])
        self.assertIn({"module": "PAY"}, self.ready()["design_owed"])
        rec = json.loads(self.git("show", "origin/main:docs/modules/PAY-ACCEPTED.json").stdout)
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
        self.assertTrue(agent_loop.take_claim(self.wt, prof, "WATER", "M1")[0])
        other = self.second_clone()
        ok, holder = agent_loop.take_claim(other, prof, "WATER", "M1")
        self.assertFalse(ok)
        self.assertEqual(holder, agent_loop.me(self.wt))
        self.assertEqual(self.ready(other)["taken"][0]["milestone"], "M1")
        self.assertEqual(self.run_loop(worktree=str(other))["result"], "TAKEN")

    def test_a_claim_is_released_when_the_milestone_is_accepted(self):
        self.run_loop()
        prof = agent_loop.profile(self.wt, strict=True)
        agent_loop.sync_claims(self.wt, prof)
        self.assertNotIn(("WATER", "M1"), agent_loop.claims(self.wt))

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
        self.write_done([dict(milestone("M1", "open", ["open"]), needs=["CORE:M1"])])
        self.write_done([dict(milestone("M1", "open", ["open"]), needs=["WATER:M1"])], module="CORE")
        self.commit_all()
        invalid = self.ready()["invalid"]
        self.assertEqual({i["module"] for i in invalid}, {"WATER", "CORE"})
        self.assertTrue(all("cycle" in i["problems"][-1] for i in invalid))

    def test_ready_and_project_status(self):
        (self.wt / "docs/modules/CORE-DONE.json").write_text(json.dumps(done(milestone("M1", "open", ["open"]),
                                                                            module="CORE")))
        self.commit_all()
        r = self.ready()
        self.assertEqual(r["ready"][0]["milestone"], "M1")
        self.assertEqual(r["design_owed"], [{"module": "CORE"}])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent_loop.cmd_status(argparse.Namespace(module=None, worktree=str(self.wt)))
        self.assertIn("CORE: design_owed", out.getvalue())
        self.assertIn("WATER: ready (M1)", out.getvalue())


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
        result = self.run_loop()
        self.assertEqual(result["result"], "CLAIMED")
        self.assertFalse({"pid", "loops", "turns", "registered"} & set(result))  # the result contract is unchanged
        during = json.loads(seen.read_text().splitlines()[0])["loops"]
        self.assertEqual(len(during), 1, during)
        v = during[0]
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
        self.assertEqual(self.run_loop()["result"], "CLAIMED")  # and the module runs again

    def test_bookkeeping_that_cant_be_written_never_stops_a_loop(self):
        blocker = self.root / "not-a-folder"
        blocker.write_text("")
        agent_loop.LOOPS_DIR = blocker / "loops"
        self.assertEqual(self.run_loop()["result"], "CLAIMED")
        self.assertEqual(agent_loop.LIVE, {})

    def test_a_loop_without_a_record_is_found_in_the_process_table(self):
        self.assertEqual((agent_loop.etime_s("1-02:03:04"), agent_loop.etime_s("05:06")), (93784.0, 306.0))
        script = self.root / "old" / "agent_loop.py"  # an older copy, which keeps no record
        script.parent.mkdir()
        script.write_text("import time\ntime.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, str(script), "run", "--module", "WATER", "--worktree", str(self.wt),
                                 "--host", "claude"])
        try:
            time.sleep(1.1)  # its run state, written after it started
            (self.wt / ".git/orchestrate").mkdir(exist_ok=True)
            (self.wt / ".git/orchestrate/WATER.json").write_text(json.dumps({"milestone": "M2", "path": "visible"}))
            found = [r for r in self.listed() if r["pid"] == proc.pid]
            self.assertEqual(len(found), 1, self.listed())
            v = agent_loop.loop_view(found[0])
            self.assertEqual((v["role"], v["module"], v["milestone"], v["host"], v["path"], v["registered"]),
                             ("build", "WATER", "M2", "claude", "visible", False))
            self.assertEqual(v["loop"], str(script))
        finally:
            proc.kill()
            proc.wait(timeout=5)
        self.assertEqual([r for r in self.listed() if r["pid"] == proc.pid], [])


class Guidance(Repo):
    """The four things a lead had to work out by hand before a milestone could run: plans left uncommitted, a
    sandbox refusing writes under .git, an owed design review, and what to run after any stop short of building."""

    def adopt(self, *paths):
        return self.call(agent_loop.cmd_adopt, worktree=str(self.wt), message=None, paths=list(paths))

    def plan_core(self):
        (self.wt / "docs/modules/CORE-DONE.json").write_text(json.dumps(done(milestone("M1", "open", ["open"]),
                                                                            module="CORE")))
        (self.wt / "docs/modules/CORE.md").write_text("# Core design")

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
        self.assertEqual(r["unlanded_plans"]["uncommitted"], ["docs/modules/CORE-DONE.json", "docs/modules/CORE.md"])
        self.assertIn(" adopt --worktree ", r["next"]["command"])
        result = self.run_loop(module="CORE")
        self.assertEqual(result["result"], "INVALID")
        self.assertIn("no done-when file at the integrated tip", result["problems"][0])
        self.assertIn("CORE-DONE.json", result["next"]["why"])
        self.assertIn(" adopt ", result["next"]["command"])
        self.assertFalse(self.log.exists())
        (self.wt / "docs/modules/WATER.md").write_text("# Water design")  # committed here, never integrated
        self.git("add", "docs/modules/WATER.md")
        self.git("commit", "-qm", "water design")
        self.assertEqual(self.ready()["unlanded_plans"]["unintegrated"], ["docs/modules/WATER.md"])

    def test_fix1_adopt_lands_only_the_plan_files_and_refuses_anything_else(self):
        self.plan_core()
        (self.wt / "src").mkdir()
        (self.wt / "src/engine.rs").write_text("unfinished work")
        refused = self.adopt("src/engine.rs")
        self.assertEqual(refused["result"], "REFUSED")
        self.assertIn("isn't a plan file under docs/modules/", refused["problems"][0])
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertEqual(result["files"], ["docs/modules/CORE-DONE.json", "docs/modules/CORE.md"])
        self.git("fetch", "-q", "origin")
        landed = self.git("show", "--name-only", "--format=", "origin/main").stdout.split()
        self.assertEqual(sorted(landed), ["docs/modules/CORE-DONE.json", "docs/modules/CORE.md"])
        self.assertEqual((self.wt / "src/engine.rs").read_text(), "unfinished work")  # left alone, not swept in
        self.assertNotIn(agent_loop.TRAILER, self.git("log", "-1", "--format=%B", "origin/main").stdout)
        r = self.ready()
        self.assertNotIn("unlanded_plans", r)
        self.assertEqual(r["design_owed"], [{"module": "CORE"}])
        self.assertTrue(result["worktree"].startswith("fast-forwarded"), result["worktree"])

    def test_fix1_adopt_refuses_a_plan_that_grants_what_a_planner_cant(self):
        forged = milestone("M1", "done", ["pass"])
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(done(forged, milestone("M2", "open", ["open"]))))
        (self.wt / "docs/modules/WATER-ACCEPTED.json").write_text("{}")
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED")
        self.assertTrue(any("only the loop writes" in p for p in result["problems"]), result)
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
            code_land, land = self.main("land", "--worktree", str(self.wt))
        finally:
            os.chmod(self.wt / ".git", 0o755)
        self.assertEqual((code, ready["result"]), (1, "FLOOR"))
        self.assertEqual(ready["blocked_write"]["path"], str(self.wt.resolve() / ".git/FETCH_HEAD"))
        self.assertIn("outside the sandbox, or with escalation", ready["reason"])
        self.assertIn(" ready --worktree ", ready["next"]["command"])
        self.assertEqual((code_land, land["result"]), (1, "FAILED"))
        self.assertIn(str(self.wt.resolve() / ".git"), land["blocked_write"]["path"])
        self.assertIn("outside the sandbox", land["detail"])

    # 3. An owed design review

    def test_fix3_run_does_the_owed_design_review_then_builds_on_design_ok(self):
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "CLAIMED", result)
        self.assertEqual([c["role"] for c in self.calls()], ["review", "build"])
        self.assertEqual(self.read_record()["design"]["verdict"], "ok")

    def test_fix3_any_other_design_verdict_stops_the_run_and_says_what_next(self):
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        result = self.run_loop()
        self.assertEqual(result["result"], "DESIGN_OWED")
        self.assertEqual(result["design_review"]["verdict"], "DESIGN CHANGES")
        self.assertIn(" plan --worktree ", result["next"]["command"])
        self.assertEqual([c["role"] for c in self.calls()], ["review"])

    def test_fix3_no_design_review_opts_out(self):
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False)
        self.commit_all()
        result = self.run_loop(no_design_review=True)
        self.assertEqual(result["result"], "DESIGN_OWED")
        self.assertIn(" review --module WATER --milestone design ", result["next"]["command"])
        self.assertFalse(self.log.exists())

    # 4. The next command

    def test_fix4_waiting_follows_the_need_to_the_command_that_moves_it(self):
        self.write_done([dict(milestone("M1", "open", ["open"]), needs=["CORE:M1"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual(result["result"], "WAITING")
        self.assertIn(" plan --worktree ", result["next"]["command"])
        self.assertIn("Plan module CORE", result["next"]["command"])
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False, module="CORE")
        self.commit_all()
        result = self.run_loop()
        self.assertIn(" review --module CORE --milestone design ", result["next"]["command"])
        r = self.ready()  # nothing ready: the lead still gets a command
        self.assertEqual(r["ready"], [])
        self.assertIn(" review --module CORE --milestone design ", r["next"]["command"])

    def test_fix4_review_blocked_invalid_and_floor_carry_the_next_command(self):
        self.write_done([milestone("M1", "claimed", ["pass"], inspect="captures"), milestone("M2", "open", ["open"])])
        self.commit_all()
        owed = self.run_loop()
        self.assertEqual(owed["result"], "REVIEW_OWED")
        self.assertIn(" review --module WATER --milestone M1 --commit ", owed["next"]["command"])
        self.write_done([milestone("M1", "open", ["open"]), milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no device attached")
        blocked = self.run_loop()
        self.assertEqual(blocked["result"], "BLOCKED")
        self.assertIn(" unblock --module WATER --milestone M1 ", blocked["next"]["command"])
        self.assertIn("no device attached", blocked["next"]["why"])
        again = self.run_loop()
        self.assertEqual(again["result"], "BLOCKED")
        self.assertIn(" unblock ", again["next"]["command"])
        agent_loop.CODEX = "/no/such/codex"
        with contextlib.redirect_stdout(io.StringIO()):
            agent_loop.cmd_unblock(argparse.Namespace(module="WATER", milestone="M1", worktree=str(self.wt)))
        floor = self.run_loop()
        self.assertEqual(floor["result"], "FLOOR")
        self.assertIn("--host claude", floor["next"]["alternative"])
        (self.wt / "docs/modules/WATER-DONE.json").write_text("{not json")
        self.commit_all()
        invalid = self.run_loop()
        self.assertEqual(invalid["result"], "INVALID")
        self.assertIn(" plan --worktree ", invalid["next"]["command"])

    def test_fix4_owner_decisions_are_commands_for_the_owner_never_run(self):
        self.write_done([milestone("M1", "parked", ["open"], inspect="captures"), milestone("M2", "open", ["open"])])
        self.commit_all()
        result = self.run_loop()
        self.assertEqual(result["result"], "PARKED")
        self.assertEqual(result["next"]["by"], "owner")
        self.assertIn(" owner unpark --module WATER --milestone M1 ", result["next"]["command"])
        self.write_done([milestone("M1", "done", ["pass"], inspect="captures"), milestone("M2", "open", ["open"])],
                        authorise=False)  # done in the file, never accepted by the loop
        self.commit_all()
        result = self.run_loop()
        self.assertEqual((result["result"], result["next"]["by"]), ("REVIEW_OWED", "owner"))
        self.assertIn(" owner accept ", result["next"]["command"])
        self.assertFalse(self.log.exists())
        self.assertEqual(self.read_done()["milestones"][0]["state"], "done")
        self.assertNotIn("accepted", self.read_record()["milestones"]["M1"])

    def test_fix4_taken_points_at_other_work(self):
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.assertTrue(agent_loop.take_claim(other, prof, "WATER", "M1")[0])
        result = self.run_loop()
        self.assertEqual(result["result"], "TAKEN")
        self.assertIn(" ready --worktree ", result["next"]["command"])
        self.assertIn(" owner release ", result["next"]["owner"])


class Landing(unittest.TestCase):
    def test_astra_10_local_integration_with_no_remote_fast_forwards_the_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, wt = Path(tmp, "repo"), Path(tmp, "repo-build")
            run = lambda *a, where=main: subprocess.run(["git", "-C", str(where), *a], check=True, capture_output=True)
            run("init", "-q", "-b", "main", str(main), where=tmp)
            run("config", "user.name", "t")
            run("config", "user.email", "t@t")
            (main / "ORCHESTRATE.md").write_text("- **Integrate:** local\n- **Check:** test -f feature\n")
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
        if self.behaviour == "hang":
            info["running"] = turn
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
            codex_goal_activate=lambda t: self.activated.append(t) or True,
            SETTLE_S=0.0, POLL_S=0.01, START_S=0.2, STALL_START_S=1.0, CLAUDE_IMPORT_WAIT_S=0.0,
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
                         ("CLAIMED", "visible", "gpt-6.1-sol medium"))
        (t, info), = app.threads.items()
        self.assertEqual((info["model"], info["effort"], info["role"], info["title"], info["cwd"]),
                         ("gpt-6.1-sol", "medium", "build", "build WATER M1", self.wt.resolve()))
        self.assertIn(f"codex://threads/wake/{t}", app.links)
        self.assertEqual((self.state()["thread"], self.state()["path"]), (t, "visible"))
        self.assertTrue(self.calls(), "the app ran the turn")
        self.assertEqual(self.read_record()["milestones"]["M1"]["accepted"]["by"], "checks")

    def test_decision_8_a_resumed_turn_goes_to_the_same_thread_with_the_message(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        with FakeCodexApp(self).installed() as app:
            self.assertEqual(self.run_loop()["result"], "NEEDS_CONTEXT")
            self.run_loop(message="Use the simulator.")
        self.assertEqual(len(app.threads), 1)
        self.assertTrue(app.sent[0].startswith(agent_loop.GOAL_LINE + "Objective: milestone M1"))
        self.assertNotIn("gpt-6.1-sol", app.sent[0])
        self.assertTrue(app.sent[-1].startswith("Use the simulator.\n\nObjective: M1 claimed"))

    def test_decision_8_a_turn_on_another_effort_in_the_app_is_PIN(self):
        with FakeCodexApp(self, effort_seen="xhigh").installed():
            result = self.run_loop()
        self.assertEqual(result["result"], "PIN")
        self.assertIn("gpt-6.1-sol/xhigh", result["mismatches"][0])

    def test_decision_8_the_owner_pressing_stop_in_the_app_is_PAUSED_not_a_failure(self):
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
            result = self.run_loop(turn_timeout_hours=0.5 / 3600)
        self.assertEqual(result["result"], "FLOOR")
        self.assertEqual(len(app.interrupts), 2)
        self.assertEqual(len(app.activated), 2)

    def test_decision_8_run_again_reactivates_a_goal_paused_in_the_app(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        with FakeCodexApp(self).installed() as app:
            self.run_loop()
            t = self.state()["thread"]
            with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
                conn.execute("create table thread_goals (thread_id text, status text)")
                conn.execute("insert into thread_goals values (?, 'paused')", (t,))
            self.run_loop()
        self.assertEqual(app.activated, [t])

    def test_decision_8_run_after_unblock_reactivates_a_blocked_goal(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        with FakeCodexApp(self).installed() as app:
            self.run_loop()
            t = self.state()["thread"]
            with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
                conn.execute("create table thread_goals (thread_id text, status text)")
                conn.execute("insert into thread_goals values (?, 'blocked')", (t,))
            self.run_loop()
        self.assertEqual(app.activated, [t])

    def test_decision_8_a_review_runs_in_its_own_visible_thread_in_the_verify_tree(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        with FakeCodexApp(self).installed() as app:
            commit = self.run_loop()["commit"]
            result = self.review(commit=commit, effort="high")
        self.assertEqual((result["result"], result["verdict"], result["path"]), ("REVIEWED", "PASS", "visible"))
        review = [i for i in app.threads.values() if i["role"] == "review"][0]
        self.assertEqual((review["title"], review["effort"]), ("review WATER M1", "high"))
        self.assertIn("orchestrate/verify", str(review["cwd"]))

    def test_decision_8_a_turn_the_app_starts_late_is_waited_for_not_given_up_on(self):
        with FakeCodexApp(self, behaviour="late").installed() as app:
            result = self.run_loop()
        self.assertEqual(result["result"], "CLAIMED")
        self.assertEqual(app.unqueued, [])

    def test_decision_8_a_turn_the_app_never_starts_is_unqueued_so_it_cant_run_unwatched(self):
        with FakeCodexApp(self, behaviour="never").installed() as app:
            result = self.run_loop()
        self.assertEqual(result["result"], "FLOOR")
        self.assertIn("queued message was removed", result["stderr"])
        self.assertEqual(app.queued, {})
        self.assertTrue(app.unqueued)

    def test_decision_8_without_the_app_the_loop_runs_headless_and_says_why(self):
        result = self.run_loop()
        self.assertEqual((result["result"], result["path"]), ("CLAIMED", "headless"))
        self.assertTrue(result["path_reason"])
        self.assertEqual(self.calls()[0]["argv"][0], "exec")


class VisibleClaude(Repo):
    """Decision 8: Claude turns run in the loop's own signed-in CLI, imported into the Code tab."""

    def setUp(self):
        super().setUp()
        fake = self.root / "claude"
        fake.write_text(FAKE_HOST)
        fake.chmod(0o755)
        agent_loop.CLAUDE = str(fake)
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
        self.assertEqual((result["result"], result["path"]), ("CLAIMED", "visible"))
        argv = self.calls()[0]["argv"]
        sid = argv[argv.index("--session-id") + 1]
        self.assertEqual(self.links, [f"claude://resume?session={sid}"])
        self.assertEqual(self.state()["thread"], sid)

    def test_decision_8_the_loop_wont_write_to_a_session_the_owner_has_open_in_the_app(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        with self.app():
            self.run_loop(host="claude")
        with self.app(owner_pid=4242):
            result = self.run_loop(host="claude")
        self.assertEqual(result["result"], "PAUSED")
        self.assertIn("pid 4242", result["reason"])
        self.assertEqual(len(self.calls()), 1)


class VisibleChoice(unittest.TestCase):
    def test_decision_8_each_reason_to_fall_back_is_named(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(agent_loop, "CODEX_HOME", Path(tmp)), \
                mock.patch.object(agent_loop, "CODEX_APP_CLI", sys.executable), \
                mock.patch.object(agent_loop, "CLAUDE_APP_STORE", Path(tmp)), \
                mock.patch.object(agent_loop.sys, "platform", "darwin"):
            with mock.patch.dict(os.environ, {"ORCHESTRATE_HEADLESS": "1"}):
                self.assertIn("ORCHESTRATE_HEADLESS", agent_loop.visible_unavailable("codex"))
            with mock.patch.dict(os.environ, {"ORCHESTRATE_HEADLESS": ""}):
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
                            "- **Owner decides:** spending and publishing\n")
ECHO_HOST = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "role": "build"}) + "\\n")
print("NEEDS_CONTEXT: which device?")
"""


class Fold(Repo):
    """Fold-learnings part B (workbench/fold-learnings-2026-11-09/PLAN.md items 5-8)."""

    def use_claude(self):
        fake = self.root / "claude"
        fake.write_text(FAKE_HOST)
        fake.chmod(0o755)
        agent_loop.CLAUDE = str(fake)

    def prompt(self, call):
        argv = call["argv"]
        return argv[argv.index("-p") + 1] if "-p" in argv else argv[-1]

    def bounds(self):
        (self.wt / "ORCHESTRATE.md").write_text(BOUNDS_PROFILE)
        self.commit_all()

    # Item 5: constraints that survive a resumed turn.

    def test_item5_a_resumed_claude_turn_restates_the_binding_constraints(self):
        self.use_claude()
        self.bounds()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        self.run_loop(host="claude")
        result = self.run_loop(host="claude", message="Use the simulator.")
        first, resumed = (self.prompt(c) for c in self.calls())
        self.assertNotIn("Still binding", first)
        message, _, restated = resumed.partition("\n\n")
        self.assertEqual(message, "Use the simulator.")
        for part in ("change only M1's state and its items' status and evidence in docs/modules/WATER-DONE.json",
                     f"`python3 {agent_loop.LOOP} land --worktree .` (push:", "Check: none.",
                     "Licences and paths not to touch: no GPL code; never modify ../other-repo.",
                     "Owner decides: spending and publishing."):
            self.assertIn(part, restated)
        self.assertTrue(restated.startswith("Objective: M1 claimed, every item pass with evidence"))
        self.assertLessEqual(len(restated.split()), 90, "the restatement stays terse")
        self.assertNotIn("constraints_missing", result)

    def test_item5_a_turn_resumed_inside_a_run_restates_too(self):
        self.use_claude()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="DONE")
        self.assertEqual(self.run_loop(host="claude")["result"], "UNCLAIMED")
        later = [self.prompt(c) for c in self.calls()[1:]]
        self.assertEqual(len(later), 2)
        for p in later:
            self.assertTrue(p.startswith("The loop can't accept the claim yet"))
            self.assertIn("\n\nObjective: M1 claimed", p)
            self.assertIn("Still binding: change only M1's state", p)

    def test_item5_codex_restates_only_when_no_goal_is_active_and_records_the_goal(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which device?")
        self.assertEqual(self.run_loop()["goal"], "none")
        self.run_loop(message="Use the simulator.")
        self.assertIn("\n\nObjective: M1 claimed", self.prompt(self.calls()[-1]))
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        before = len(self.calls())
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
        self.run_loop(host="echo")
        first, second = (c["argv"][-1] for c in self.calls())
        self.assertNotIn("Still binding", first)
        self.assertIn("This continues earlier work", second)
        self.assertTrue(second.endswith("Check: none."))

    def test_item5_a_missing_out_of_bounds_line_is_reported_not_guessed(self):
        self.use_claude()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop(host="claude")
        result = self.run_loop(host="claude", message="go on")
        self.assertEqual(result["constraints_missing"], list(agent_loop.BOUNDS))
        restated = self.prompt(self.calls()[-1])
        self.assertNotIn("Owner decides", restated)
        self.assertNotIn("not to touch", restated)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Owner decides:** <e.g. spending>\n")
        self.assertIsNone(agent_loop.profile(self.wt)["bounds"]["Owner decides"], "a placeholder isn't a rule")

    def test_item5_a_reviewer_restatement_never_tells_it_to_integrate(self):
        prof = agent_loop.profile(self.wt)
        text, _ = agent_loop.binding(prof, "review", done="docs/modules/WATER-DONE.json",
                                     review="docs/evidence/WATER/M1-review.md")
        self.assertIn("change only docs/evidence/WATER/M1-review.md and the verdict fields", text)
        self.assertNotIn("land", text)
        self.assertIn("don't commit, push or launch agents", text)

    # Item 6: launch records.

    def test_holistic_5_model_and_effort_are_in_no_prompt_only_the_launch_record(self):
        values = dict(goal=agent_loop.GOAL_LINE, milestone="M1", module="W", done="d", loop="l", skill="s", commit="c",
                      review="r", task="t", evidence="e", captures="r-captures", answers="", changed="", briefs="")
        for name in ("BUILD_TEMPLATE", "REVIEW_TEMPLATE", "DESIGN_REVIEW_TEMPLATE", "PLAN_TEMPLATE",
                     "FINDINGS_TEMPLATE"):
            template = getattr(agent_loop, name)
            self.assertNotIn("{model}", template, name)
            self.assertNotIn("{effort}", template, name)
            text = template.format(**values).lower()
            for word in ("effort", "gpt-6", "opus", "launched on"):
                self.assertNotIn(word, text, f"{name} mentions {word}")
        self.assertTrue(agent_loop.BUILD_TEMPLATE.format(**values).startswith(agent_loop.GOAL_LINE + "Objective:"))
        self.use_claude()
        self.assertEqual(self.run_loop(host="claude", effort="high")["result"], "CLAIMED")
        argv = self.calls()[-1]["argv"]
        self.assertEqual(argv[argv.index("--effort") + 1], "high")
        self.assertNotIn("high", self.prompt(self.calls()[-1]))
        self.assertEqual(self.read_record()["milestones"]["M1"]["claim"]["effort"], "high")

    def test_item6_a_claude_claim_records_effort_cli_and_only_the_observed_model(self):
        self.use_claude()
        os.environ.update(FAKE_VERSION="2.1.400 (Claude Code)")
        self.assertEqual(self.run_loop(host="claude")["result"], "CLAIMED")
        claim = self.read_record()["milestones"]["M1"]["claim"]
        self.assertEqual({k: claim[k] for k in ("host", "model", "effort", "cli", "observed")},
                         {"host": "claude", "model": "claude-opus-5-5", "effort": "medium",
                          "cli": "2.1.400 (Claude Code)", "observed": {"model": "claude-opus-5-5"}})

    def test_item6_a_codex_claim_without_a_rollout_observes_nothing(self):
        self.assertEqual(self.run_loop(effort="high")["result"], "CLAIMED")
        claim = self.read_record()["milestones"]["M1"]["claim"]
        self.assertEqual((claim["effort"], claim["observed"], claim["cli"], claim["path"]),
                         ("high", {}, "fake-cli 9.9.9", "headless"))

    def test_item6_a_visible_review_records_what_the_rollout_showed(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_VERSION="codex-cli 0.167.0")
        with FakeCodexApp(self).installed():
            commit = self.run_loop()["commit"]
            self.assertEqual(self.review(commit=commit, effort="high")["verdict"], "PASS")
        rec = self.read_record()["milestones"]["M1"]
        self.assertEqual(rec["claim"]["observed"], {"model": "gpt-6.1-sol", "effort": "medium"})
        review = rec["reviews"][-1]
        self.assertEqual({k: review[k] for k in ("model", "effort", "observed", "cli", "path")},
                         {"model": "gpt-6.1-sol", "effort": "high", "cli": "codex-cli 0.167.0", "path": "visible",
                          "observed": {"model": "gpt-6.1-sol", "effort": "high"}})

    def test_item6_one_unverified_turn_drops_a_field_for_good(self):
        self.assertEqual(agent_loop.still_observed(None, {"model": "m"}), {"model": "m"})
        self.assertEqual(agent_loop.still_observed({"model": "m"}, {}), {})
        self.assertEqual(agent_loop.still_observed({}, {"model": "m"}), {})

    # Item 7: the loader check runs on the resolved launch.

    def test_item7_an_agents_md_only_repo_warns_on_the_claude_binary_the_launch_uses(self):
        self.use_claude()
        (self.wt / "AGENTS.md").write_text("rules")
        self.commit_all()
        os.environ.update(FAKE_VERSION="2.1.239 (Claude Code)")
        result = self.run_loop(host="claude")
        self.assertEqual(result["result"], "CLAIMED", "a warning, not a failure")
        agents = [w for w in result["warnings"] if "AGENTS.md" in w]
        self.assertEqual(len(agents), 1)
        self.assertIn("2.1.239", agents[0])
        self.assertIn("`@AGENTS.md`", agents[0])
        self.assertIn(agent_loop.CLAUDE, agents[0])

    def test_item7_the_profile_default_host_isnt_checked_when_the_launch_resolves_to_another(self):
        (self.wt / "AGENTS.md").write_text("rules")
        self.commit_all()
        os.environ.update(FAKE_VERSION="2.1.239 (Claude Code)")
        result = self.run_loop()  # codex, which reads AGENTS.md itself
        self.assertFalse([w for w in result.get("warnings", []) if "AGENTS.md" in w])

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
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        commit = self.run_loop(host=host)["commit"]
        builder = self.calls()[-1]
        self.assertEqual(self.review(commit=commit, host=host)["verdict"], "PASS")
        self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="plan PAY", host=host, model=None, effort=None,
                  turn_timeout_hours=0.1)
        for role in ("review", "plan"):
            call = next(c for c in self.calls() if c["role"] == role)
            self.assertNotIn(resume_flag, call["argv"], f"{host} {role} resumes nothing")
            skill = "review-milestone" if role == "review" else "plan-module"
            self.assertRegex(self.prompt(call), rf"^Use the {skill} skill",
                             f"{host} {role} gets only its own task")
            if role == "review":
                self.assertNotEqual(call["cwd"], builder["cwd"], "a clean checkout, not the builder's tree")

    def test_item8_codex_reviewers_and_planners_start_a_new_session(self):
        self.fresh_review_and_plan("codex", "resume")

    def test_item8_claude_reviewers_and_planners_start_a_new_session(self):
        self.use_claude()
        self.fresh_review_and_plan("claude", "--resume")


class Holistic(Repo):
    """Decisions 1-9 of workbench/holistic-review-2026-11-09/SYNTHESIS.md."""

    use_claude, prompt = Fold.use_claude, Fold.prompt

    def plan(self, **kw):
        args = dict(worktree=str(self.wt), task="plan PAY", host=None, model=None, effort=None, turn_timeout_hours=0.1)
        args.update(kw)
        return self.call(agent_loop.cmd_plan, **args)

    def plan_calls(self):
        return [c for c in self.calls() if c["role"] == "plan"]

    # 1. A planner's progress report isn't a plan.

    def test_holistic_1_a_progress_report_from_the_planner_lands_nothing(self):
        os.environ.update(FAKE_PLAN="progress")
        result = self.plan()
        self.assertEqual((result["result"], result["landed"]), ("UNFINISHED", False))
        self.assertIn("wasn't `PLANNED", result["owed"])
        self.assertEqual(len(self.plan_calls()), 3, "the first turn and two nudges, no more")
        self.git("fetch", "-q", "origin")
        self.assertNotIn("PAY", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)

    def test_holistic_1_a_planner_nudged_after_a_progress_report_lands_its_plan(self):
        os.environ.update(FAKE_PLAN="late")
        result = self.plan()
        self.assertEqual((result["result"], result["landed"], result["modules"]), ("PLANNED", True, ["PAY"]))
        nudge = self.prompt(self.plan_calls()[1])
        self.assertTrue(nudge.startswith("Your last line wasn't `PLANNED: <files>`"))

    def test_holistic_1_a_plan_missing_its_design_is_nudged_with_the_gap_and_never_lands(self):
        os.environ.update(FAKE_PLAN="nodesign")
        result = self.plan()
        self.assertEqual((result["result"], result["landed"]), ("UNFINISHED", False))
        self.assertIn("docs/modules/PAY-DONE.json has no design at docs/modules/PAY.md", result["owed"])
        self.assertIn("docs/modules/PAY-DONE.json", result["left_uncommitted"])

    def test_holistic_1_a_blocked_planner_lands_nothing_and_says_what_it_left(self):
        os.environ.update(FAKE_PLAN="blocked")
        result = self.plan()
        self.assertEqual((result["result"], result["landed"]), ("BLOCKED", False))
        self.assertEqual(result["left_uncommitted"], ["docs/modules/PAY.md"])
        self.assertEqual(len(self.plan_calls()), 1)

    def test_holistic_1_named_files_must_exist_and_be_changed(self):
        owed = agent_loop.plan_owed(self.wt, agent_loop.head_commit(self.wt), "PLANNED: docs/modules/NOPE.md, "
                                    "docs/modules/WATER-DONE.json")
        self.assertIn("docs/modules/NOPE.md doesn't exist", owed)
        self.assertIn("docs/modules/WATER-DONE.json isn't changed", owed)
        self.assertIsNone(agent_loop.plan_owed(self.wt, "HEAD", "NEEDS_CONTEXT: which provider?"))

    # 2. Owner rules survive fresh sessions.

    def test_holistic_2_an_owner_rule_survives_fresh_sessions_and_milestones_until_cleared(self):
        self.use_claude()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        rule = "never edit the schema"
        self.run_loop(host="claude", owner_rule=[rule])
        self.run_loop(host="claude", fresh=True, message="Findings: see the review.")
        self.run_loop(host="claude", message="go on")
        first, fresh, resumed = (self.prompt(c) for c in self.calls())
        self.assertIn("Owner: never edit the schema.", first)
        self.assertIn("Owner: never edit the schema.", fresh, "a fresh session keeps the rule")
        self.assertIn("Findings: see the review.", fresh)
        self.assertIn("Owner: never edit the schema.", resumed)
        self.assertEqual(self.state()["owner_rules"], [rule])
        self.run_loop(host="claude", fresh=True, clear_owner_rules=True)
        self.assertNotIn("Owner:", self.prompt(self.calls()[-1]))
        self.assertEqual(self.state()["owner_rules"], [])

    def test_holistic_2_an_active_codex_goal_still_gets_owner_rules_added_after_it(self):
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: x")
        self.run_loop()
        with sqlite3.connect(self.home / "goals_1.sqlite") as conn:
            conn.execute("create table thread_goals (thread_id text, status text)")
            conn.execute("insert into thread_goals values ('t1', 'active')")
        self.run_loop(message="go on", owner_rule=["keep the public API"])
        resumed = self.prompt(self.calls()[1])
        self.assertEqual(resumed, "go on\n\nOwner: keep the public API.")

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

    def test_holistic_4_no_skill_or_claude_agent_file_sets_model_or_effort(self):
        root = agent_loop.SKILLS
        files = [root / n / "SKILL.md" for n in ("build", "build-milestone", "review-milestone", "plan-module")]
        files += sorted((root / "build/agents/claude").glob("*.md"))
        for f in files:
            front = f.read_text().split("\n---\n")[0]
            self.assertNotRegex(front, r"(?m)^(model|effort):", str(f))

    # 6. A resumed Claude turn restates the objective (covered with item 5 above), terse.

    def test_holistic_6_the_restatement_opens_with_the_objective(self):
        text, _ = agent_loop.binding(agent_loop.profile(self.wt), "build", "M2", None, "d.json")
        self.assertTrue(text.startswith("Objective: M2 claimed, every item pass with evidence and the work integrated."))

    # 7. Plugin installs: skills, namespaced names and agents.

    def install_plugin(self, home):
        ver = home / "plugins/cache/ryannel-skills/orchestrate/1.3.0"
        for name in ("review-milestone", "plan-module", "build-milestone"):
            (ver / "skills/orchestration" / name).mkdir(parents=True)
            (ver / "skills/orchestration" / name / "SKILL.md").write_text("x")
        (ver / "skills/orchestration/build/agents/claude").mkdir(parents=True)
        (ver / "skills/orchestration/build/agents/claude/orchestrate-evaluator.md").write_text("x")
        (ver / ".claude-plugin").mkdir()
        (ver / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": [
            {"name": "orchestrate", "skills": ["./skills/orchestration/review-milestone",
                                               "./skills/orchestration/plan-module",
                                               "./skills/orchestration/build-milestone"],
             "agents": ["./skills/orchestration/build/agents/claude/orchestrate-evaluator.md"]},
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
        self.use_claude()
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        commit = self.run_loop(host="claude")["commit"]
        self.install_plugin(agent_loop.CLAUDE_HOME)
        self.assertEqual(self.review(commit=commit, host="claude")["verdict"], "PASS")
        argv = next(c for c in self.calls() if c["role"] == "review")["argv"]
        self.assertEqual(argv[argv.index("--agent") + 1], "orchestrate-evaluator")

    # 8. The reviewer fails only on blocking defects.

    def test_holistic_8_review_skill_and_findings_message_separate_blocking_from_advisory(self):
        review = (agent_loop.SKILLS / "review-milestone/SKILL.md").read_text()
        self.assertIn("A Suggestion never changes the\n`state`.", review)
        self.assertIn("Count Must Fix findings only.", review)
        self.assertNotIn("If you think the defect doesn't matter, say so in the finding", review)
        self.assertIn("Every blocking finding counts", agent_loop.FINDINGS_TEMPLATE)


class Locks(unittest.TestCase):
    def test_lock_takes_worktree_after_the_name_and_runs_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            marker = Path(tmp) / "where"
            with self.assertRaises(SystemExit) as exit_:
                agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=None, command_args=[
                    "--worktree", tmp, "--", "sh", "-c", f"pwd > {marker}"]))
            self.assertEqual(exit_.exception.code, 0)
            self.assertEqual(Path(marker.read_text().strip()).resolve(), Path(tmp).resolve())

    def test_lock_refuses_outside_a_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                agent_loop.cmd_lock(argparse.Namespace(name="gpu", worktree=tmp, command_args=["--", "true"]))


if __name__ == "__main__":
    unittest.main()


class CodexProject(unittest.TestCase):
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

    def adopt(self, *paths):
        return self.call(agent_loop.cmd_adopt, worktree=str(self.wt), message=None, paths=list(paths))

    def printed(self, func, code=None, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            if code is None:
                func(argparse.Namespace(**kw))
            else:
                with self.assertRaises(SystemExit) as stop:
                    func(argparse.Namespace(**kw))
                self.assertEqual(stop.exception.code, code)
        release()
        return out.getvalue()

    def fake_claude(self):
        fake = self.root / "claude"
        fake.write_text(FAKE_HOST)
        fake.chmod(0o755)
        agent_loop.CLAUDE = str(fake)

    def edit_m2(self, check="test -n changed"):
        doc = self.read_done("HEAD")
        doc["milestones"][1]["items"][0]["check"] = check
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))

    # 1. The one-chat path

    def draft(self):
        """WATER as a draft: planned, nothing built, its design review still owed."""
        self.write_done([milestone("M1", "open", ["open"]), milestone("M2", "open", ["open"])], design_ok=False)
        self.commit_all()

    def test_item1_adopt_authorises_a_drafts_revisions_for_the_owed_design_review(self):
        self.draft()
        self.edit_m2()
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertEqual(result["authorised"], ["WATER"])
        r = self.ready()
        self.assertEqual(r.get("invalid", []), [])
        self.assertEqual(r["design_owed"], [{"module": "WATER"}])
        stamp = self.read_record()["milestones"]["M2"]["authorised"]
        self.assertEqual(stamp["by"], "adopt")
        self.assertIn("before the module's design review passed", stamp["why"])
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("## Definitions changed through adopt", report)
        self.assertIn("WATER M2: definitions authorised by adopt", report)
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.run_loop()["result"], "CLAIMED")  # after the design review judged them

    def test_item1_a_lead_cant_weaken_checks_once_the_design_review_passed(self):
        """The reviewer's probe: design agreed, nothing built, a check rewritten to `true`."""
        m1 = milestone("M1", "open", ["open", "open"], inspect="the frames match the spec")
        m1["items"][0]["check"] = "cargo test --test physics -- --exact solver_converges"
        self.write_done([m1, milestone("M2", "open", ["open"])])
        self.commit_all()
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["check"] = "true"
        doc["milestones"][0]["items"][1].pop("inspect", None)
        doc["milestones"][0]["items"][1]["check"] = "true"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
        result = self.adopt()
        self.assertEqual(result["result"], "REFUSED", result)
        self.assertIn("a design review of it has passed", result["problems"][0])
        self.assertIn(" owner scope --module WATER --milestone M1 ", result["next"]["owner"])
        self.assertEqual(self.read_done()["milestones"][0]["items"][0]["check"],
                         "cargo test --test physics -- --exact solver_converges")
        self.assertEqual(self.run_loop()["result"], "INVALID")  # the edit here still isn't authorised

    def test_item1_a_claim_alone_closes_the_draft(self):
        self.draft()
        prof = agent_loop.profile(self.wt, strict=True)
        other = self.root / "lead2"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        self.assertTrue(agent_loop.take_claim(other, prof, "WATER", "M1")[0])  # claimed, nothing accepted
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
                self.assertTrue(agent_loop.take_claim(other, prof, "WATER", "M1")[0])
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
        self.assertIn("ORCHESTRATE.md", self.ready()["unlanded_plans"]["uncommitted"])
        result = self.adopt()
        self.assertEqual(result["result"], "ADOPTED", result)
        self.assertIn("ORCHESTRATE.md", result["files"])
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("show", "origin/main:ORCHESTRATE.md").stdout, PROFILE)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** high\n")
        self.assertIn("differs from the one at origin/main", self.ready()["profile_differs"])
        self.assertIn("differs from the one at origin/main", self.printed(agent_loop.cmd_status, module=None,
                                                                           worktree=str(self.wt)))
        refused = self.adopt("ORCHESTRATE.md")
        self.assertEqual(refused["result"], "REFUSED")
        self.assertIn("the lead commits and integrates it with git once the owner has agreed", refused["problems"][0])
        self.assertIn("once the owner has agreed to it", self.ready()["profile_differs"])
        nothing = self.adopt()
        self.assertEqual(nothing["result"], "NOTHING")
        self.assertIn("profile_differs", nothing)

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
            prof = json.loads(self.printed(agent_loop.cmd_profile, code=1, worktree=str(self.wt), host=None))
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
        self.write_done([milestone("M1", "open", ["open", "open", "open"]), milestone("M2", "open", ["open"])])
        doc = json.loads((self.wt / "docs/modules/WATER-DONE.json").read_text())
        checks = ["true", "test -f built.txt", "if then"]
        # not built yet, a failing test whose output looks like shell trouble, and one that doesn't parse
        for i, check in zip(doc["milestones"][0]["items"], checks):
            i["check"] = check
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
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
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
        out = json.loads(self.printed(agent_loop.cmd_check, code=0, module="WATER", milestone="M1",
                                      worktree=str(self.wt), plans_from=None, timeout=60.0, json=True))
        self.assertEqual(out["pass"], 3)

    # 5. Cost in one place

    def test_item5_a_paused_claude_turn_counts_the_tokens_it_showed(self):
        partial = "\n".join(json.dumps(e) for e in [
            {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 10, "output_tokens": 1}}},
            {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 10, "output_tokens": 3}}},
            {"type": "assistant", "message": {"id": "b", "usage": {"input_tokens": 5, "cache_read_input_tokens": 100,
                                                                   "output_tokens": 2}}}])
        self.assertEqual(agent_loop.usage_of("claude", partial),
                         {"input": 15, "cached": 100, "output": 5, "incomplete_turns": 1, "turns": 1})

    def test_item5_every_turn_lands_in_the_ledger_and_cost_adds_it_up(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_USAGE="1", FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "CLAIMED", result)
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

    def test_item5_a_turn_with_no_tokens_is_marked_incomplete(self):
        result = self.run_loop()  # the fake codex prints no turn.completed
        self.assertEqual(result["result"], "CLAIMED")
        self.assertEqual(agent_loop.ledger_rows(self.wt)[0]["usage"], {"incomplete_turns": 1})
        c = agent_loop.cost_of(agent_loop.ledger_rows(self.wt))
        self.assertIn("showed no tokens or only some", agent_loop.cost_line(c["total"]))

    # 6. quota

    def test_item6_quota_rounds_small_costs_and_counts_in_words(self):
        self.assertEqual([agent_loop.pct(x) for x in (0, 0.04, 0.42, 3.25, 41.6)],
                         ["0%", "under 0.1%", "0.4%", "3.2%", "42%"])
        acc = {"used_percent": 30.0, "hours_left": 50.0}
        recent = {"hours": 12.0, "loop": [0.1, 0.2, 0.3], "other": [0.01, 0.02, 0.03]}
        done_ms = [{"module": "W", "milestone": "M1", "state": "done", "pct": [0.1, 0.2, 0.3], "rounds": 1}]
        open_one = [{"module": "W", "milestone": "M2", "state": "open", "rounds": 1}]
        verdict = agent_loop.plan_forecast(acc, done_ms, open_one, recent)["verdict"]
        self.assertTrue(verdict.startswith("Quota lasts: the 1 open milestone and other use need about 0.3%"), verdict)
        verdict = agent_loop.plan_forecast(acc, done_ms, [], recent)["verdict"]
        self.assertTrue(verdict.startswith("Quota lasts: other use needs about"), verdict)

    def test_item6_quota_reads_out_the_verdict_first_and_json_behind_a_flag(self):
        acc = {"used_percent": 30.0, "resets_at": "2026-11-12T00:00:00Z", "hours_left": 40.0, "complete": True,
               "recent": {"hours": 12, "burn": {}}, "outside": {"pct": 0.5},
               "use_this_window": {"loop_pct": [1.0, 1.2, 1.4], "other_local_pct": [0.0, 0.0, 0.0],
                                   "elsewhere_pct": 0.5},
               "forecast": {"verdict": "Quota lasts: x.", "warn": False}}
        with mock.patch.object(agent_loop, "quota_report", lambda *a, **k: acc):
            text = self.printed(agent_loop.cmd_quota, worktree=None, budget=1.0, json=False)
            raw = json.loads(self.printed(agent_loop.cmd_quota, worktree=None, budget=1.0, json=True))
        self.assertTrue(text.startswith("Quota lasts: x."), text)
        self.assertIn("1.2% by orchestrate loops on this machine (any repository)", text)
        self.assertIn("from elsewhere", text)
        self.assertEqual(raw["used_percent"], 30.0)

    def test_item6_a_claude_turn_carries_no_quota(self):
        self.fake_claude()
        result = self.run_loop(host="claude")
        self.assertEqual(result["result"], "CLAIMED")
        self.assertNotIn("quota", result)

    # 7. Stops that say what's next and who holds what

    def test_item7_reviewed_and_planned_name_what_comes_next(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        changes = self.review("design", commit=None)
        self.assertEqual((changes["verdict"], changes["next"]["by"]), ("DESIGN CHANGES", "planner"))
        self.assertIn(" plan --worktree ", changes["next"]["command"])
        self.assertEqual(changes["next"]["findings"], "docs/evidence/WATER/design-review.md")
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
        self.write_done([milestone("M1", "open", ["open"], inspect="frames")])
        self.commit_all()
        claim = self.run_loop()
        passed = self.review(commit=claim["commit"])
        self.assertIsNone(passed["next"]["command"])
        self.assertIn("finished", passed["next"]["why"])

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
        self.write_done([milestone("M1", "done", ["pass"]), milestone("M2", "open", ["open"])], authorise=False)
        self.commit_all()  # the builder's file says done; the loop has checked nothing
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        line = next(l for l in status.splitlines() if l.strip().startswith("M1"))
        self.assertIn("done, unchecked", line)
        self.assertIn("the loop hasn't checked this claim yet", line)
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE.replace("codex", "claude") + "- **Codex model:** gpt-x\n")
        prof = json.loads(self.printed(agent_loop.cmd_profile, worktree=str(self.wt), host=None))
        self.assertNotIn("model", prof)

    # 8. Reviews on the right host

    def test_item8_the_profile_sends_reviews_to_the_other_host(self):
        self.fake_claude()
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([milestone("M1", "open", ["open"], inspect="frames")], design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design")
        result = self.run_loop()
        self.assertEqual(result["result"], "CLAIMED", result)
        self.assertEqual(result["design_review"]["host"], "claude")
        os.environ.update(FAKE_REVIEW="pass")
        review = self.review(commit=result["commit"])
        self.assertEqual((review["verdict"], review["host"]), ("PASS", "claude"))
        builds = [c for c in self.calls() if c["role"] == "build"]
        self.assertEqual(builds[0]["argv"][0], "exec")  # codex built it

    def test_item8_review_host_flag_wins(self):
        self.fake_claude()
        self.write_done([milestone("M1", "open", ["open"])], design_ok=False)
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
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_USAGE="1")
        first = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        self.review(commit=first["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        second = self.run_loop(message="FINDINGS")
        self.assertEqual(second["result"], "CLAIMED", second)
        claim = self.read_record()["milestones"]["M1"]["claim"]
        self.assertEqual(claim["usage"]["output"], 7)  # this round only
        self.assertEqual(claim["session_usage"]["output"], 14)  # the session so far
        self.assertEqual(second["usage"]["output"], 14)  # the result line's meaning is unchanged

    def test_item7_a_resumed_claude_turn_costs_only_the_rise_in_its_sessions_total(self):
        self.fake_claude()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="NEEDS_CONTEXT: which colour?", FAKE_COST="0.5")
        self.assertEqual(self.run_loop(host="claude")["result"], "NEEDS_CONTEXT")
        os.environ.update(FAKE_PASS="1", FAKE_REPLY="DONE", FAKE_COST="0.8")
        self.assertEqual(self.run_loop(host="claude", message="blue")["result"], "CLAIMED")
        rows = agent_loop.ledger_rows(self.wt)
        self.assertEqual([r["usage"]["cost_usd"] for r in rows], [0.5, 0.3])
        self.assertEqual(rows[1]["session"], rows[0]["session"])
        self.assertEqual(self.read_record()["milestones"]["M1"]["claim"]["usage"]["cost_usd"], 0.8)

    # 8. The owner's answer to an attended item

    def test_item8_the_owners_answer_goes_through_the_record(self):
        m1 = milestone("M1", "open", ["open", "open"], inspect="frames")
        m1["items"][1]["attended"] = "the owner picks a direction"
        self.write_done([m1, milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_ATTENDED="1", FAKE_STATE="in_progress", FAKE_REPLY="BLOCKED: M1.2 needs the owner")
        blocked = self.run_loop()
        self.assertEqual(blocked["result"], "BLOCKED", blocked)
        self.assertEqual(blocked["next"]["by"], "owner")
        self.assertIn(" owner answer --module WATER --milestone M1 --item M1.2 ", blocked["next"]["command"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        answered = self.owner("answer", "M1", "Direction B, the ink one.", item="M1.2")
        self.assertEqual((answered["result"], answered["unblocked"]), ("DONE", True))
        answers = self.read_record()["milestones"]["M1"]["owner_answers"]
        self.assertEqual([(a.get("by"), a["item"], a["text"]) for a in answers], [(None, "M1.2", "Direction B, the ink one.")])
        self.assertEqual(self.read_done()["milestones"][0]["state"], "open")
        for key in ("FAKE_SKIP_ATTENDED", "FAKE_STATE"):
            os.environ.pop(key)
        os.environ.update(FAKE_REPLY="DONE")
        claim = self.run_loop()
        self.assertEqual(claim["result"], "CLAIMED", claim)
        prompt = self.calls()[-1]["argv"][-1]
        self.assertIn("The owner answered", prompt)
        self.assertIn("M1.2 (", prompt)
        self.assertIn("Direction B, the ink one.", prompt)
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        self.assertIn("owner_answers", self.calls()[-1]["argv"][-1])

    # 9. Captures beside the review

    def test_item9_a_reviewers_captures_land_beside_the_review(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="pass", FAKE_CAPTURE="1")
        result = self.review(commit=claim["commit"])
        self.assertEqual(result["verdict"], "PASS", result)
        self.git("fetch", "-q", "origin")
        self.assertIn("PNG", self.git("show", "origin/main:docs/evidence/WATER/M1-review/shot.png").stdout)

    # 10. Owner commands

    def test_item10_an_owner_command_needs_the_owners_words(self):
        with self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_owner(argparse.Namespace(action="accept", module="WATER", milestone="M1", item=None,
                                                    text="  ", worktree=str(self.wt)))
        self.assertIn("owner accept needs --text, the owner's words", str(stop.exception))

    def test_item10_owner_scope_leaves_the_worktree_clean(self):
        self.edit_m2()
        result = self.owner("scope", "M2")
        self.assertEqual(result["result"], "DONE", result)
        self.assertTrue(result["worktree"].startswith("fast-forwarded"), result)
        self.assertEqual(self.git("status", "--porcelain").stdout.strip(), "")
        self.assertEqual(self.read_done("HEAD")["milestones"][1]["items"][0]["check"], "test -n changed")

    # 11. A planner's report keeps its end

    def test_item11_a_long_report_keeps_its_end(self):
        report = "x" * 9000 + "\nOwner decides: pick a licence.\nPLANNED: a, b"
        kept = agent_loop.tail(report, 6000)
        self.assertTrue(kept.startswith("[earlier text cut] "))
        prose = "Planned PAY files. " * 400 + "Owner decides: pick a licence."
        cut = agent_loop.tail(prose, 1500)
        self.assertTrue(cut.startswith("[earlier text cut] Planned PAY files."), cut[:60])
        lines = "\n".join(f"line {n} of the planner's notes" for n in range(400))
        self.assertTrue(agent_loop.tail(lines, 1500).startswith("[earlier text cut] line "))
        self.assertTrue(kept.endswith("Owner decides: pick a licence.\nPLANNED: a, b"))
        self.assertEqual(agent_loop.tail("short", 6000), "short")

    # Round four: the commands tried on finished projects

    def test_r4_cost_falls_back_to_the_committed_record_when_the_ledger_has_nothing(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])],
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
        self.write_done([milestone("M1", "open", ["open", "open"]), milestone("M2", "open", ["open"])])
        doc = json.loads((self.wt / "docs/modules/WATER-DONE.json").read_text())
        doc["milestones"][0]["items"][0]["check"] = "true"
        doc["milestones"][0]["items"][1]["check"] = "echo nope-not-built; exit 3"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
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
        (empty / "ORCHESTRATE.md").write_text(PROFILE)  # the owner's profile, waiting for adopt to land it
        adopted = self.call(agent_loop.cmd_adopt, worktree=str(empty), message=None, paths=[])
        self.assertEqual(adopted["result"], "FAILED", adopted)
        self.assertIn("no commits yet", adopted["detail"])
        self.assertNotIn("fatal:", adopted["detail"])
        self.assertIn("commit --allow-empty", adopted["next"]["command"])
        self.assertIn("push -u origin main", adopted["next"]["command"])
        before = self.log.read_text() if self.log.exists() else ""
        planned = self.call(agent_loop.cmd_plan, worktree=str(empty), task="Plan the project", host=None, model=None,
                            effort=None, turn_timeout_hours=0.1)
        self.assertEqual(planned["result"], "FLOOR", planned)
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
        self.assertIn("these changed in docs/modules/WATER-DONE.json: M2.1 changed.", second)
        before = {"milestones": [milestone("M1", "open", ["open", "open"]), milestone("M2", "open", ["open"])]}
        after = {"milestones": [milestone("M1", "open", ["open"]), milestone("M3", "open", ["open"])]}
        after["milestones"][0]["bar"] = "higher"
        self.assertEqual(agent_loop.changed_items(before, after),
                         ["M1's bar or needs changed", "M1.2 removed", "M3 added", "M2 removed"])


    # Round five: the ladder's re-plan rung

    def test_r5_four_failed_reviews_hand_every_surface_the_planners_command(self):
        self.write_done([failed_before(dict(milestone("M1", "open", ["open"], inspect="frames"), fails=3, rounds=3)),
                         milestone("M2", "open", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual(claim["result"], "CLAIMED", claim)
        os.environ.update(FAKE_REVIEW="fail")
        failed = self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual((failed["fails"], failed["ladder"]), (4, "replan"))
        self.assertEqual((failed["next"]["ladder"], failed["next"]["by"]), ("replan", "planner"))
        self.assertIn(" plan --worktree ", failed["next"]["command"])
        self.assertIn("Re-plan WATER M1", failed["next"]["command"])
        self.assertIn("docs/evidence/WATER/M1-review.md", failed["next"]["command"])
        self.assertEqual(failed["next"]["findings"], "docs/evidence/WATER/M1-review.md")
        # ready: not ready, owed a re-plan, with the command
        r = self.ready()
        self.assertEqual(r["ready"], [])
        self.assertEqual([s["milestone"] for s in r["replan_owed"]], ["M1"])
        self.assertEqual(r["replan_owed"][0]["next"]["command"], failed["next"]["command"])
        self.assertEqual(r["next"]["command"], failed["next"]["command"])
        # next: the planner's task, not the builder's findings
        nxt = json.loads(self.printed(agent_loop.cmd_next, module="WATER", milestone="M1", worktree=str(self.wt)))
        self.assertEqual(nxt["action"], "replan")
        self.assertTrue(nxt["message"].startswith("Re-plan WATER M1"), nxt["message"])
        self.assertNotIn("set the state back to claimed", nxt["message"])
        self.assertEqual(nxt["next"]["command"], failed["next"]["command"])
        # status says so, with the command
        status = self.printed(agent_loop.cmd_status, module=None, worktree=str(self.wt))
        self.assertIn("WATER: replan_owed (M1)", status)
        self.assertIn("a planner looks at it before any more building", status)
        self.assertIn("Re-plan WATER M1", status)
        # run starts no builder
        before = len(self.calls())
        stopped = self.run_loop()
        self.assertEqual(stopped["result"], "REPLAN_OWED", stopped)
        self.assertEqual(stopped["next"]["command"], failed["next"]["command"])
        self.assertEqual(len(self.calls()), before)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("WATER M1: replan owed", report)
        # once the planner has re-planned (fails 0, replans 1), it's the builder's again
        doc = self.read_done()
        m1 = doc["milestones"][0]
        m1.update(fails=0, replans=1, state="open")
        m1["items"][0]["statement"] = "a smaller first step"
        self.assertEqual(agent_loop.next_step("WATER", {"WATER": entry_for(doc)})["status"], "ready")

    def test_r5_next_gives_a_command_on_every_rung(self):
        prof = agent_loop.profile(self.wt)
        for fails, replans, rounds, diagnoses, word, by, has in (
                (0, 0, 1, 0, "same-session", "lead", "--message"),
                (1, 0, 2, 0, "same-session", "lead", "--message"),
                (0, 0, 3, 0, "fresh-session", "lead", "--fresh"),
                (3, 0, 4, 0, "fresh-session", "lead", "--fresh"),
                (4, 0, 4, 0, "replan", "planner", " plan "),
                (4, 1, 5, 0, "park", "owner", " owner unpark "),
                (1, 0, 6, 0, "diagnose", "planner", " plan "),
                (1, 1, 6, 1, "park", "owner", " owner unpark ")):
            word_now = agent_loop.escalation(fails, replans, rounds, diagnoses)
            counts = {"fails": fails, "replans": replans, "rounds": rounds, "diagnoses": diagnoses}
            then = agent_loop.ladder_next(word_now, "WATER", "M1", counts, self.wt, prof)
            self.assertEqual((word_now, then["ladder"], then["by"]), (word, word, by))
            self.assertIn(has, then["command"])

    # Round six: the taste-led rerun

    # Round eighteen: the owner decides in chat, and the lead records it

    def test_r18_an_attended_block_tells_the_lead_what_to_ask_and_what_to_run(self):
        m1 = milestone("M1", "open", ["open", "open"], inspect="frames")
        m1["items"][1]["attended"] = "the owner picks a direction"
        self.write_done([m1, milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_SKIP_ATTENDED="1", FAKE_STATE="in_progress", FAKE_REPLY="BLOCKED: M1.2 needs the owner")
        blocked = self.run_loop()
        nxt = blocked["next"]
        self.assertEqual((blocked["result"], nxt["by"]), ("BLOCKED", "owner"), blocked)
        self.assertTrue(nxt["ask"].startswith("M1.2: M1.2 works (the owner picks a direction). The builder's note: "),
                        nxt["ask"])
        self.assertIn("M1.2 needs the owner", nxt["ask"])
        self.assertIn("Evidence to show them: docs/evidence/WATER/", nxt["ask"])
        self.assertNotIn(agent_loop.ATTENDED_BLOCK, nxt["ask"])
        self.assertIn(" owner answer --module WATER --milestone M1 --item M1.2 ", nxt["command"])
        self.assertIn("--text '<the owner's words, as they gave them>'", nxt["command"])
        self.assertIn("Ask the owner in chat", nxt["why"])
        self.assertNotIn("alternative", nxt)
        for text in (json.dumps(blocked), json.dumps(self.ready())):
            self.assertNotIn("terminal", text)
            self.assertNotIn("relay", text)
        self.git("pull", "-q", "--rebase", "origin", "main")
        answered = self.owner("answer", "M1", "Direction B, the ink one.", item="M1.2")
        self.assertEqual((answered["result"], answered["unblocked"]), ("DONE", True))
        rec = self.read_record()
        [d] = rec["decisions"]
        self.assertEqual((d["action"], d["milestone"], d["item"], d["words"]), ("answer", "M1", "M1.2",
                                                                               "Direction B, the ink one."))
        self.assertNotIn("by", d)
        self.assertNotIn("by", rec["milestones"]["M1"]["owner_answers"][0])
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Decisions recorded in the owner's name (check each is one you made)")[1]
        self.assertIn('- WATER M1 M1.2: answer, ', section.split("\n## ")[0])
        self.assertIn('"Direction B, the ink one."', section.split("\n## ")[0])
        for key in ("FAKE_SKIP_ATTENDED", "FAKE_STATE"):
            os.environ.pop(key)
        os.environ.update(FAKE_REPLY="DONE")
        claim = self.run_loop()
        self.assertIn("Direction B, the ink one.", self.calls()[-1]["argv"][-1])
        os.environ.update(FAKE_REVIEW="pass")
        self.review(commit=claim["commit"])
        self.assertIn("owner_answers (for M1.2)", self.calls()[-1]["argv"][-1])

    def test_r18_every_verb_keeps_the_owners_words_and_report_lists_them(self):
        self.write_done([dict(milestone("M1", "parked", ["open"]), fails=4), milestone("M2", "open", ["open"])])
        self.commit_all()
        self.assertEqual(self.owner("unpark", "M1", "give it one more go")["result"], "DONE")
        self.assertEqual(self.owner("accept", "design", "the design is fine")["result"], "DONE")
        released = self.owner("release", "M2", "that lead's machine is gone")
        self.assertEqual(released["result"], "RELEASED", released)
        rec = self.read_record()
        self.assertEqual([(d["action"], d["milestone"], d["words"]) for d in rec["decisions"]],
                         [("unpark", "M1", "give it one more go"), ("accept", "design", "the design is fine"),
                          ("release", "M2", "that lead's machine is gone")])
        self.assertEqual(rec["design"]["by"], "owner decision")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Decisions recorded in the owner's name")[1].split("\n## ")[0]
        for line in ('- WATER M1: unpark, ', '"give it one more go"', '- WATER design: accept, ',
                     '- WATER M2: release, '):
            self.assertIn(line, section)

    def test_r19_scope_with_nothing_changed_says_so(self):
        with self.assertRaises(SystemExit) as stop:
            agent_loop.cmd_owner(argparse.Namespace(action="scope", module="WATER", milestone="M1", item=None,
                                                    text="keep it as it is", worktree=str(self.wt)))
        release()
        self.assertIn("nothing changed: docs/modules/WATER-DONE.json here has the same definitions as the tip",
                      str(stop.exception))
        self.assertNotIn("decisions", self.read_record())

    def test_r19_report_lists_planner_turns_with_their_tasks(self):
        self.plan(task="Plan PAY. The owner said: \"card payments only, no PayPal\"")
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Planner turns (with the task each was given)")[1].split("\n## ")[0]
        self.assertIn(', PAY: Plan PAY. The owner said: "card payments only, no PayPal"', section)

    def test_r18_older_records_read_as_they_were_written(self):
        rec = json.loads((self.wt / "docs/modules/WATER-ACCEPTED.json").read_text())
        at = agent_loop.now()
        m1 = rec["milestones"]["M1"]
        m1["owner"] = [{"by": "owner", "reason": "typo fix", "at": at, "action": "accept"}]
        m1["owner_answers"] = [{"by": "owner", "text": "Direction A", "at": at, "item": "M1.1"},
                               {"by": "lead", "text": "Direction B", "at": at, "item": "M1.1", "relayed": True}]
        rec["design"] = {"by": "owner", "reason": "fine as it is", "at": at, "verdict": "ok",
                         "hash": rec["design"]["hash"]}
        (self.wt / "docs/modules/WATER-ACCEPTED.json").write_text(json.dumps(rec))
        self.commit_all()
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Decisions recorded in the owner's name")[1].split("\n## ")[0]
        self.assertIn('- WATER M1: accept, ', section)
        self.assertIn('"typo fix"', section)
        self.assertIn('- WATER M1 M1.1: answer, ', section)
        self.assertIn('"Direction B" (recorded then as relayed by the lead)', section)
        self.assertIn('- WATER design: accept, ', section)
        note = agent_loop.answers_note(m1["owner_answers"], "M1", "docs/modules/WATER-ACCEPTED.json")
        self.assertIn("Direction A", note)
        self.assertIn("Direction B", note)
        self.assertIn("the latest stands", note)

    def test_r18_owner_stops_ask_in_chat_and_never_send_anyone_to_a_terminal(self):
        prof = agent_loop.profile(self.wt)
        for word in ("park",):
            then = agent_loop.ladder_next(word, "WATER", "M1", {"fails": 4, "replans": 1, "rounds": 4}, self.wt, prof)
            self.assertEqual(then["by"], "owner")
            self.assertTrue(then["ask"])
            self.assertIn("--text '<the owner's words", then["command"])
        for step in ({"module": "WATER", "milestone": "M1", "status": "parked"},
                     {"module": "WATER", "milestone": "M1", "status": "review_owed", "state": "done"},
                     {"module": "WATER", "milestone": "M1", "status": "taken", "by": "elsewhere"}):
            n = agent_loop.next_for(step, self.wt, prof)
            text = json.dumps(n)
            self.assertNotIn("terminal", text)
            self.assertNotIn("--reason", text)
            self.assertIn("--text '<the owner's words", text)
            if n["by"] == "owner":
                self.assertTrue(n["ask"])

    def test_r6_quota_counts_only_this_repositorys_milestones(self):
        import test_codex_quota as fixtures
        now = fixtures.NOW
        elsewhere = self.root / "other-repo"
        elsewhere.mkdir()
        other = fixtures.Rollout(self.home, "o1", now - 10 * 3600, cwd=str(elsewhere), origin="codex_exec",
                                 source="exec", name="build WATER M1")
        other.turn("t", now - 10 * 3600, now - 9 * 3600, [(now - 10 * 3600 + i * 600, 2_000_000, i) for i in range(1, 5)])
        mine = fixtures.Rollout(self.home, "h1", now - 8 * 3600, cwd=str(self.wt / "sub"), origin="codex_exec",
                                source="exec", name="build WATER M2")
        mine.turn("t", now - 8 * 3600, now - 7 * 3600, [(now - 8 * 3600 + i * 600, 2_000_000, 10 + i)
                                                        for i in range(1, 5)])
        reading = agent_loop.codex_quota.read(budget_s=10, home=self.home, cache=False, now=now)
        own = agent_loop.loop_threads(self.wt, reading)
        self.assertEqual((own["o1"]["here"], own["h1"]["here"]), (False, True))
        acc = agent_loop.quota_report(self.wt, reading=reading)
        self.assertEqual([m["milestone"] for m in acc["milestones"]], ["M2"])

    def test_r6_report_lists_every_design_review_in_the_window(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])],
                        design_ok=False)
        self.commit_all()
        os.environ.update(FAKE_REVIEW="design_changes")
        self.review("design", commit=None)
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
        rec = json.loads(self.git("show", "origin/main:docs/modules/WATER-ACCEPTED.json").stdout)
        rec.pop("design_history")
        prof = agent_loop.profile(self.wt)
        ref = self.git("rev-parse", "origin/main").stdout.strip()
        older = agent_loop.design_reviews(self.wt, prof, ref, "WATER", rec)
        self.assertEqual([d["review"] for d in older],
                         ["docs/evidence/WATER/design-review-1.md", "docs/evidence/WATER/design-review.md"])

    # Round seven: the browser-game run

    def test_r7_a_block_with_other_causes_still_names_the_owners_command(self):
        m1 = milestone("M1", "open", ["open", "open"], inspect="frames")
        m1["items"][1]["attended"] = "the owner plays both and picks a direction"
        self.write_done([m1, milestone("M2", "open", ["open"])])
        self.commit_all()
        os.environ.update(FAKE_PASS="0", FAKE_REPLY="BLOCKED: no browser starts here; M1.2 needs the owner's pick")
        blocked = self.run_loop()
        self.assertEqual(blocked["result"], "BLOCKED", blocked)
        self.assertIn(" unblock ", blocked["next"]["command"])  # the lead's cause leads
        [owed] = blocked["next"]["owner_answers"]
        self.assertEqual((owed["item"], owed["by"]), ("M1.2", "owner"))
        self.assertIn(" owner answer --module WATER --milestone M1 --item M1.2 ", owed["command"])
        self.assertIn("M1.2", owed["ask"])
        self.assertNotIn("relay", owed)
        self.assertIn("M1.2 also wait", blocked["next"]["why"])
        r = self.ready()
        self.assertEqual(r["blocked"][0]["attended"], ["M1.2"])
        self.assertEqual(r["next"]["owner_answers"][0]["item"], "M1.2")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("- WATER M1 M1.2: ", report)
        self.assertIn("Ask the owner in chat; their answer goes in `", report)
        self.assertIn(" owner answer --module WATER --milestone M1 --item M1.2 ", report)

    def test_r7_codex_in_workspace_write_is_warned_off_browser_work(self):
        self.assertEqual(agent_loop.browser_warnings(self.wt), [])
        profile = PROFILE + ("\n## Targets\n\n| Target | What it is | Run | Capture | Edge conditions |\n"
                             "|---|---|---|---|---|\n| web | Chromium, desktop | `npm run dev` | Playwright screenshots | resize |\n"
                             "| cli | the binary | `cargo run` | transcript | bad args |\n")
        (self.wt / "ORCHESTRATE.md").write_text(profile)
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["target"] = "web"
        doc["milestones"][1]["items"][0]["check"] = "npx playwright test"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
        [warning] = agent_loop.browser_warnings(self.wt)
        self.assertIn("target web, WATER M1.1, WATER M2.1 need a browser", warning)
        self.assertNotIn("target cli", warning)
        self.assertNotIn("--host claude", warning)  # round eleven: never steer a lead off the owner's host
        self.assertIn("has to ask to run it outside the sandbox", warning)
        self.assertIn("Codex sandbox: danger-full-access", warning)
        self.assertIn(warning, agent_loop.preflight("codex", self.wt, "build"))
        self.assertNotIn(warning, agent_loop.preflight("codex", self.wt, "plan"))
        prof = json.loads(self.printed(agent_loop.cmd_profile, worktree=str(self.wt), host="codex"))
        self.assertIn(warning, prof["preflight"]["warnings"])
        (self.wt / "ORCHESTRATE.md").write_text(profile.replace("**Default host:** codex",
                                                                "**Default host:** codex\n- **Codex sandbox:** danger-full-access"))
        self.assertEqual(agent_loop.browser_warnings(self.wt), [])

    # Round eight: the re-plan's bookkeeping, scope as a re-plan, and every review round kept

    def four_fails(self):
        """WATER M1 after its fourth failed review, owed a re-plan, with each round's review kept."""
        # three failed reviews so far, two of them repeats; both rounds below repeat what failed before
        self.write_done([failed_before(dict(milestone("M1", "open", ["open"], inspect="frames"), fails=2, rounds=3)),
                         milestone("M2", "open", ["open"])])
        self.commit_all()
        for n in range(2):
            os.environ.pop("FAKE_REVIEW", None)
            claim = self.run_loop(**({"message": "FINDINGS"} if n else {}))
            self.assertEqual(claim["result"], "CLAIMED", claim)
            os.environ.update(FAKE_REVIEW="fail")
            failed = self.review(commit=claim["commit"])
        os.environ.pop("FAKE_REVIEW")
        self.git("pull", "-q", "--rebase", "origin", "main")
        return failed

    def test_r8_every_review_round_is_kept_and_named(self):
        failed = self.four_fails()
        self.assertEqual(failed["ladder"], "replan")
        rounds = [r.get("review") for r in self.read_record()["milestones"]["M1"]["reviews"]]
        self.assertEqual(rounds, ["docs/evidence/WATER/M1-review-1.md", "docs/evidence/WATER/M1-review.md"])
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout
        self.assertIn("docs/evidence/WATER/M1-review-1.md", files)
        task = failed["next"]["command"]
        self.assertIn("Its reviews, one per round: docs/evidence/WATER/M1-review-1.md, "
                      "docs/evidence/WATER/M1-review.md", task)
        self.assertNotIn("git log", task)
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        self.assertIn("[docs/evidence/WATER/M1-review-1.md]", report)

    def test_r8_the_loop_does_the_replans_bookkeeping_once(self):
        for mode in ("replan", "replan_counted"):
            with self.subTest(mode=mode):
                self.tearDown()
                self.setUp()
                self.four_fails()
                os.environ.update(FAKE_PLAN=mode)
                planned = self.call(agent_loop.cmd_plan, worktree=str(self.wt), task="Re-plan WATER M1", host=None,
                                    model=None, effort=None, turn_timeout_hours=0.1)
                self.assertEqual((planned["result"], planned["replanned"]), ("PLANNED", ["WATER M1"]), planned)
                m1 = self.read_done()["milestones"][0]
                self.assertEqual((m1["fails"], m1["replans"], m1["state"]), (0, 1, "open"))
                self.assertNotEqual(agent_loop.next_step("WATER", agent_loop.read_project(
                    self.wt, agent_loop.profile(self.wt))[1])["status"], "replan_owed")

    def test_r8_a_plan_that_leaves_an_owed_milestone_alone_settles_nothing(self):
        before = {"milestones": [dict(milestone("M1", "in_progress", ["open"]), fails=4)]}
        after = json.loads(json.dumps(before))
        self.assertEqual(agent_loop.settle_replans(before, after, "WATER"), [])
        self.assertEqual(after["milestones"][0]["fails"], 4)
        after["milestones"][0]["items"][0]["check"] = "test -f smaller"
        self.assertEqual(agent_loop.settle_replans(before, after, "WATER"), ["WATER M1"])
        self.assertEqual((after["milestones"][0]["fails"], after["milestones"][0]["replans"]), (0, 1))

    # A milestone that keeps failing on something new: the round-six diagnosis

    def six_rounds(self, diagnoses=0):
        """WATER M1 after its sixth failed review, only one of which repeated an earlier round's finding."""
        self.write_done([dict(milestone("M1", "open", ["open"], inspect="frames"), fails=1, rounds=5,
                              diagnoses=diagnoses), milestone("M2", "open", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual(claim["result"], "CLAIMED", claim)
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

    def test_six_rounds_of_new_findings_owe_a_diagnosis_not_a_replan(self):
        failed = self.six_rounds()
        self.assertEqual((failed["fails"], failed["rounds"], failed["repeated"], failed["ladder"]),
                         (1, 6, [], "diagnose"), failed)
        self.assertEqual((failed["next"]["ladder"], failed["next"]["by"]), ("diagnose", "planner"))
        self.assertIn(" plan --worktree ", failed["next"]["command"])
        self.assertIn("Diagnose WATER M1", failed["next"]["command"])
        self.assertIn("KEEP WATER M1: builder", failed["next"]["command"])
        self.assertEqual(self.run_loop()["result"], "REPLAN_OWED")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual(m1["findings"], [{"name": "the water is flat (M1.1)", "item": "M1.1", "repeat": False}])
        rnd = self.read_record()["milestones"]["M1"]["reviews"][-1]
        self.assertEqual((rnd["items"], rnd["findings"][0]["name"]), ({"M1.1": "fail"}, "the water is flat (M1.1)"))

    def test_a_diagnosis_that_changes_the_plan_settles_like_a_replan(self):
        self.six_rounds()
        planned = self.diagnose("replan")
        self.assertEqual((planned["result"], planned["replanned"]), ("PLANNED", ["WATER M1"]), planned)
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["fails"], m1["rounds"], m1["replans"], m1["diagnoses"], m1["state"]), (0, 0, 1, 1, "open"))
        self.assertNotIn("findings", m1)

    def test_a_diagnosis_that_keeps_the_plan_names_who_acts(self):
        for who, by, has in (("builder", "lead", "--fresh"), ("reviewer", "lead", "--fresh"),
                             ("owner", "owner", " owner unpark ")):
            with self.subTest(who=who):
                self.tearDown()
                self.setUp()
                self.six_rounds()
                kept = self.diagnose(f"keep_{who}")
                self.assertEqual((kept["result"], kept["who"], kept["next"]["by"]), ("KEPT", who, by), kept)
                self.assertIn(has, kept["next"]["command"])
                self.assertIn(f"the {who} has to act", json.dumps(kept["next"]))
                m1 = self.read_done()["milestones"][0]
                self.assertEqual((m1["fails"], m1["rounds"], m1["diagnoses"]), (0, 0, 1))
                self.assertEqual(m1["state"], "parked" if who == "owner" else "in_progress")
                e = self.read_record()["milestones"]["M1"]
                self.assertEqual(e["diagnoses"][-1]["who"], who)
                self.assertEqual(e["counted_from"], e["diagnoses"][-1]["at"])
                if who == "owner":
                    self.assertTrue(kept["next"]["ask"])
                    self.assertTrue(kept["next"]["history"])
                    # every later readout gives the planner's reason and the rounds it read
                    later = agent_loop.next_for({"module": "WATER", "milestone": "M1", "status": "parked"}, self.wt,
                                                agent_loop.profile(self.wt))
                    self.assertIn("the owner has to act", later["ask"])
                    self.assertEqual(later["history"], kept["next"]["history"])
                    nxt = json.loads(self.printed(agent_loop.cmd_next, module="WATER", milestone="M1",
                                                  worktree=str(self.wt)))
                    self.assertEqual(nxt["action"], "park")
                    continue
                self.assertEqual(self.run_loop(fresh=True, message="FINDINGS")["result"], "CLAIMED")
                os.environ.update(FAKE_REVIEW="fail")
                again = self.review()
                os.environ.pop("FAKE_REVIEW")
                prompt = self.calls()[-1]["argv"][-1]
                told = "judged that their findings went beyond its items" in prompt
                self.assertEqual(told, who == "reviewer")
                # the rounds before the diagnosis no longer count: the same finding isn't a repeat
                self.assertEqual((again["fails"], again["rounds"], again["repeated"]), (0, 1, []), again)

    def test_keep_is_refused_when_no_diagnosis_is_owed(self):
        self.four_fails()
        refused = self.diagnose("keep_builder")
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("isn't owed one", refused["problems"][0])

    def test_a_second_diagnosis_parks_it_with_each_rounds_failures(self):
        parked = self.six_rounds(diagnoses=1)
        self.assertEqual((parked["ladder"], parked["next"]["by"]), ("park", "owner"), parked)
        self.assertEqual(self.read_done()["milestones"][0]["state"], "parked")
        self.assertTrue(any("the water is flat (M1.1)" in h for h in parked["next"]["history"]), parked["next"])
        for verb in ("Accept it", "change its scope", "unpark it"):
            self.assertIn(verb, parked["next"]["ask"])
        # the owner unparks it: the counts start again, and the earlier rounds no longer count as repeats
        self.assertEqual(self.owner("unpark", "M1", "one more go")["result"], "DONE")
        self.git("pull", "-q", "--rebase", "origin", "main")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["fails"], m1["rounds"], m1["diagnoses"]), ("open", 0, 0, 0))
        self.assertTrue(self.read_record()["milestones"]["M1"]["counted_from"])
        claim = self.run_loop()
        os.environ.update(FAKE_REVIEW="fail")
        again = self.review(commit=claim["commit"])
        self.assertEqual((again["fails"], again["rounds"], again["ladder"]), (0, 1, "same-session"), again)

    def test_a_failure_says_how_it_differs_or_counts_as_a_repeat(self):
        self.write_done([dict(milestone("M1", "open", ["open"], inspect="frames")), milestone("M2", "open", ["open"])])
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
        self.assertEqual([(r["fails"], r["rounds"]) for r in results], [(0, 1), (1, 2), (1, 3)])
        self.assertEqual(results[2]["ladder"], "fresh-session")

    def test_a_pass_after_a_failed_round_clears_the_findings(self):
        self.write_done([dict(milestone("M1", "open", ["open"], inspect="frames")), milestone("M2", "open", ["open"])])
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
        # the second reviewer was told the first round's findings, so it can keep their names
        prompt = self.calls()[prompt_before]["argv"][-1]
        self.assertIn("Earlier failed rounds of M1 that still count", prompt)
        self.assertIn("the water is flat (M1.1)", prompt)

    def test_a_planner_cant_change_the_counts(self):
        before = {"milestones": [dict(milestone("M1", "parked", ["open"]), fails=3, rounds=5, diagnoses=1,
                                      findings=[{"name": "x"}])]}
        after = json.loads(json.dumps(before))
        m = after["milestones"][0]
        m.update(fails=0, rounds=0, diagnoses=0, state="open")
        m.pop("findings")
        after["milestones"].append(dict(milestone("M1b", "open", ["open"]), fails=2, replans=1, diagnoses=1))
        settled = agent_loop.settle_replans(before, after, "WATER")
        agent_loop.keep_counts(before, after, settled, "WATER")
        m, split = after["milestones"]
        self.assertEqual((m["fails"], m["rounds"], m["diagnoses"], m["state"], m["findings"]),
                         (3, 5, 1, "parked", [{"name": "x"}]))
        self.assertEqual((split["fails"], split["rounds"], split["replans"], split["diagnoses"]), (0, 0, 1, 1))

    def test_owner_scope_restarts_the_counts_and_takes_it_out_of_parked(self):
        self.six_rounds(diagnoses=1)
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["statement"] = "what the owner wants now"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
        self.assertEqual(self.owner("scope", "M1")["result"], "DONE")
        self.git("pull", "-q", "--rebase", "origin", "main")
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["fails"], m1["rounds"], m1["diagnoses"]), ("open", 0, 0, 0))
        self.assertNotIn("findings", m1)

    def test_a_review_must_list_its_findings_on_a_fail_and_none_on_a_pass(self):
        for env, review in (("FAKE_NO_FINDINGS", "fail"),):
            with self.subTest(env=env):
                self.tearDown()
                self.setUp()
                claim = self.run_loop()
                os.environ.update({env: "1", "FAKE_REVIEW": review})
                bad = self.review(commit=claim["commit"])
                self.assertEqual(bad["result"], "INVALID", bad)

    def test_r8_owner_scope_on_an_owed_milestone_is_the_replan(self):
        self.four_fails()
        doc = self.read_done("HEAD")
        doc["milestones"][0]["items"][0]["statement"] = "what the owner wants now"
        (self.wt / "docs/modules/WATER-DONE.json").write_text(json.dumps(doc))
        scoped = self.owner("scope", "M1")
        self.assertEqual((scoped["result"], scoped["replanned"]), ("DONE", ["M1"]), scoped)
        self.assertIn("counts as the re-plan", scoped["replanned_why"])
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["fails"], m1["replans"], m1["state"]), (0, 1, "open"))


    # Round nine: the second whole-change review

    def attended_m1(self, state="blocked", status="open"):
        m1 = milestone("M1", state, ["open", status], inspect="frames")
        m1["items"][1]["attended"] = "the owner picks a direction"
        if state == "blocked":
            m1["blocked"] = "M1.2 needs the owner"
        self.write_done([m1, milestone("M2", "open", ["open"])])
        self.commit_all()

    def test_r9_owner_decisions_are_refused_while_the_module_is_held(self):
        self.attended_m1()
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
                for verb in ("answer", "accept", "release"):
                    with self.assertRaises(SystemExit) as stop:
                        agent_loop.cmd_owner(argparse.Namespace(action=verb, module="WATER", milestone="M1",
                                                                item="M1.2", text="B", worktree=str(self.wt)))
                    release()
                    messages.append(str(stop.exception))
            finally:
                proc.kill()
                proc.wait()
                proc.stdout.close()
            for message in messages:
                self.assertIn(says, message)
                self.assertIn(f"pid {proc.pid}", message)
        self.assertEqual(self.owner("answer", "M1", "Direction B.", item="M1.2")["result"], "DONE")  # once free

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
            f"cd {other} && echo '# Water, revised' > docs/modules/WATER.md && git add -A && "
            "git -c user.name=t -c user.email=t@t commit -qm revise && git push -q origin main"))
        stale = self.review("design", commit=None)
        self.assertEqual((stale["verdict"], stale["counted"]), ("DESIGN OK", False), stale)
        self.assertIn("the design document", stale["not_counted"])
        self.assertIn(" review --module WATER --milestone design ", stale["next"]["command"])
        rec = self.read_record()
        self.assertFalse(agent_loop.design_passed(rec))
        self.assertIn("not_counted", rec["design_history"][-1])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertEqual(self.ready()["design_owed"], [{"module": "WATER"}])

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
        self.assertFalse(agent_loop.plan_drift(behind, prof, "origin/main")["profile_differs"])
        (behind / "ORCHESTRATE.md").write_text(PROFILE + "- **Effort:** low\n")
        self.assertTrue(agent_loop.plan_drift(behind, prof, "origin/main")["profile_differs"])

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

    # Round ten: two modules built at once

    def plan(self, **kw):
        return self.call(agent_loop.cmd_plan, **{**dict(worktree=str(self.wt), task="plan PAY", host=None, model=None,
                                                        effort=None, turn_timeout_hours=0.1), **kw})

    def test_r15_a_planner_that_catches_up_with_loop_commits_still_lands(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        # another module's claim (with the loop's trailer) lands mid-turn, and the planner fast-forwards to it: that
        # commit is on the tip and isn't the planner's work, so the turn lands what it left uncommitted
        os.environ.update(FAKE_PLAN="catch_up", FAKE_DURING=(
            f"cd {other} && echo '{{}}' > docs/modules/WATER-ACCEPTED.json && git add -A && "
            f"git -c user.name=t -c user.email=t@t commit -qm 'orchestrate: claim WATER M1' -m '{agent_loop.TRAILER}' "
            "&& git push -q origin main"))
        planned = self.plan()
        self.assertEqual((planned["result"], planned["landed"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertIn("acceptance/test_pay.py", files)
        self.assertIn("docs/modules/PAY-DONE.json", files)

    def forge_on_tip(self):
        """A FAKE_DURING command: a commit without the loop's trailer changes WATER's acceptance record on the tip."""
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        return (f"cd {other} && echo '{{\"forged\": true}}' > docs/modules/WATER-ACCEPTED.json && git add -A && "
                "git -c user.name=t -c user.email=t@t commit -qm 'tidy records' && git push -q origin main")

    def test_r15_a_record_forged_elsewhere_during_a_planner_turn_refuses_it(self):
        os.environ.update(FAKE_DURING=self.forge_on_tip())
        refused = self.plan()
        self.assertEqual((refused["result"], refused["landed"]), ("INVALID", False), refused)
        self.assertIn("without the loop's trailer changed an acceptance record on the tip", refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "owner"))
        self.assertNotIn("docs/modules/PAY-DONE.json",
                         self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split())
        self.assertTrue((self.wt / "docs/modules/PAY-DONE.json").exists())  # left uncommitted, for the owner

    def test_r15_a_record_forged_during_a_review_refuses_it(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        claimed = self.run_loop()
        self.assertEqual((claimed["result"], claimed["review"]), ("CLAIMED", True), claimed)
        os.environ.update(FAKE_DURING=self.forge_on_tip())
        refused = self.review(commit=claimed["commit"])
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("without the loop's trailer changed an acceptance record on the tip", refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "owner"))
        self.assertEqual(self.read_done()["milestones"][0]["state"], "claimed")  # no verdict was recorded

    def test_r15_a_local_landing_during_a_planner_turn_doesnt_refuse_it(self):
        main, side = self.root / "local", self.root / "local-side"
        self.sh("git", "init", "-q", "-b", "main", str(main))
        (main / "docs/modules").mkdir(parents=True)
        (main / "ORCHESTRATE.md").write_text(PROFILE.replace("Integrate:** push", "Integrate:** local"))
        self.git("add", "-A", where=main)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init", where=main)
        self.git("worktree", "add", "-q", "-b", "side", str(side), "main", where=main)
        script = Path(agent_loop.__file__).resolve()
        # mid-turn, another worktree lands, which fast-forwards main in the checkout the planner is working in
        os.environ.update(FAKE_DURING=(
            f"cd {side} && echo x > feature && git add -A && git -c user.name=t -c user.email=t@t commit -qm feature "
            f"&& env -u ORCHESTRATE_ROLE {sys.executable} {script} land --worktree {side} --no-check"))
        planned = self.plan(worktree=str(main))
        self.assertEqual((planned["result"], planned["landed"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "main", where=main).stdout.split()
        self.assertIn("feature", files)
        self.assertIn("docs/modules/PAY-DONE.json", files)
        self.assertIn("docs/modules/PAY-ACCEPTED.json", files)

    # Round sixteen: a module the loop has no record for is new once any record exists; planner commits are refused

    SHIP = ("import json, sys\n"
            "d = sys.argv[1]\n"
            "json.dump({'module': 'SHIP', 'milestones': [{'id': 'M1', 'name': 'ship', 'state': 'done', 'fails': 0,"
            " 'replans': 0, 'items': [{'id': 'M1.1', 'statement': 'ships', 'check': 'true', 'status': 'pass',"
            " 'evidence': 'x', 'verdict': 'pass', 'review': 'x'"
            + "}]}]}, open(d + '/docs/modules/SHIP-DONE.json', 'w'))\n"
            "open(d + '/docs/modules/SHIP.md', 'w').write('# Ship')\n")

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
        (main / "docs/modules").mkdir(parents=True)
        (main / "ORCHESTRATE.md").write_text(PROFILE.replace("Integrate:** push", "Integrate:** local"))
        self.write_done([milestone("M1", "open", ["open"])], where=main)  # a record: the loop is in use here
        self.git("add", "-A", where=main)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init", where=main)
        self.git("worktree", "add", "-q", "-b", "side", str(side), "main", where=main)
        return main, side

    def assert_ship_is_new(self, where):
        r = self.ready(where=where)
        self.assertNotIn("SHIP", [x["module"] for x in r["finished"]], r)
        self.assertIn({"module": "SHIP"}, r["design_owed"], r)

    def test_r16_a_planner_that_commits_and_pushes_a_finished_module_is_refused_and_accepts_nothing(self):
        os.environ.update(FAKE_DURING=self.ship(self.wt, f"&& git -C {self.wt} push -q origin HEAD:main"))
        refused = self.plan()
        self.assertEqual((refused["result"], refused["landed"]), ("INVALID", False), refused)
        self.assertIn("the planner committed in this worktree (1 commit in its reflog during the turn",
                      refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "lead"))
        self.git("reset", "-q", "--hard", "origin/main")
        self.git("clean", "-qfd")
        self.assert_ship_is_new(self.wt)  # it reached the tip, but as a new module

    def test_r16_a_planner_that_commits_in_the_local_checkout_is_refused_and_accepts_nothing(self):
        main, _ = self.local_repo()
        os.environ.update(FAKE_DURING=self.ship(main))
        refused = self.plan(worktree=str(main))
        self.assertEqual((refused["result"], refused["landed"]), ("INVALID", False), refused)
        self.assertIn("in its reflog during the turn", refused["problems"][0])
        self.git("clean", "-qfd", where=main)
        self.git("checkout", "-q", ".", where=main)
        self.assert_ship_is_new(main)  # a plain commit there is the tip

    def test_r16_a_module_landed_from_elsewhere_and_edited_by_the_planner_is_new_push(self):
        other = self.root / "other"
        self.sh("git", "clone", "-q", str(self.origin), str(other))
        # landed deliberately from another clone (no reflog entry here), fast-forwarded into, then edited uncommitted
        os.environ.update(FAKE_DURING=(
            self.ship(other, "&& git -C " + str(other) + " push -q origin main") +
            f" && git -C {self.wt} fetch -q origin && git -C {self.wt} merge -q --ff-only origin/main && "
            f"echo '# Ship, revised' > {self.wt}/docs/modules/SHIP.md && "
            f"sed -i.bak s/ships/ships\\ fast/ {self.wt}/docs/modules/SHIP-DONE.json && "
            f"rm {self.wt}/docs/modules/SHIP-DONE.json.bak"))
        planned = self.plan()
        self.assertEqual((planned["result"], planned["landed"]), ("PLANNED", True), planned)
        self.assertIn("SHIP", planned["modules"])
        self.assertIn("SHIP", planned["design_review_owed"])
        rec = json.loads(self.git("show", "origin/main:docs/modules/SHIP-ACCEPTED.json").stdout)
        self.assertNotIn("accepted", rec["milestones"]["M1"])
        self.assertIsNone(rec["design"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assert_ship_is_new(self.wt)

    def test_r16_a_module_landed_from_elsewhere_and_edited_by_the_planner_is_new_local(self):
        main, side = self.local_repo()
        script = Path(agent_loop.__file__).resolve()
        os.environ.update(FAKE_DURING=(
            self.ship(side) + f" && env -u ORCHESTRATE_ROLE {sys.executable} {script} land --worktree {side} "
            f"--no-check && echo '# Ship, revised' > {main}/docs/modules/SHIP.md && "
            f"sed -i.bak s/ships/ships\\ fast/ {main}/docs/modules/SHIP-DONE.json && "
            f"rm {main}/docs/modules/SHIP-DONE.json.bak"))
        planned = self.plan(worktree=str(main))
        self.assertEqual((planned["result"], planned["landed"]), ("PLANNED", True), planned)
        self.assertIn("SHIP", planned["modules"])  # through the plan's own record-keeping
        self.assertIn("SHIP", planned["design_review_owed"])
        rec = json.loads(self.git("show", "main:docs/modules/SHIP-ACCEPTED.json", where=main).stdout)
        self.assertNotIn("accepted", rec["milestones"]["M1"])
        self.assert_ship_is_new(main)

    def test_r16_a_reviewer_that_commits_is_refused(self):
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        claimed = self.run_loop()
        self.assertEqual((claimed["result"], claimed["review"]), ("CLAIMED", True), claimed)
        os.environ.update(FAKE_DURING="git -c user.name=t -c user.email=t@t commit -q --allow-empty -m habit")
        refused = self.review(commit=claimed["commit"])
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("the reviewer committed in its checkout", refused["problems"][0])
        self.assertEqual(self.read_done()["milestones"][0]["state"], "claimed")

    def test_r16_a_repository_with_no_records_still_adopts_modules_as_they_stand(self):
        origin, wt = self.root / "legacy.git", self.root / "legacy"
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(origin))
        self.sh("git", "init", "-q", "-b", "main", str(wt))
        (wt / "docs/modules").mkdir(parents=True)
        (wt / "ORCHESTRATE.md").write_text(PROFILE)
        self.write_done([milestone("M1", "done", ["pass"]), milestone("M2", "open", ["open"])], authorise=False,
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
        rec = json.loads(self.git("show", "origin/main:docs/modules/WATER-ACCEPTED.json", where=wt).stdout)
        self.assertEqual(rec["milestones"]["M1"]["accepted"], {"by": "adopted"})
        self.assertFalse(agent_loop.unrecorded(wt, prof, "origin/main"))
        self.git("pull", "-q", "--rebase", "origin", "main", where=wt)
        r = self.ready(where=wt)
        self.assertEqual([(x["module"], x["milestone"]) for x in r["ready"]], [("WATER", "M2")], r)
        self.assertIn({"module": "PAY"}, r["design_owed"])
        # once a record has existed, deleting every record doesn't bring adoption as it stands back
        self.git("rm", "-q", "docs/modules/WATER-ACCEPTED.json", "docs/modules/PAY-ACCEPTED.json", where=wt)
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "drop records", where=wt)
        self.assertFalse(agent_loop.unrecorded(wt, prof, "HEAD"))

    # Round seventeen: a design review goes to the host that didn't plan it, decided once; planners get the loop path

    def test_r17_a_design_review_goes_to_the_host_that_didnt_plan_it_everywhere(self):
        self.fake_claude()
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([milestone("M1", "parked", ["open"])])  # nothing of WATER's is ready
        self.commit_all()
        planned = self.plan(host="claude")
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertTrue(planned["next"]["command"].endswith("--host codex"), planned["next"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        rec = json.loads(self.git("show", "origin/main:docs/modules/PAY-ACCEPTED.json").stdout)
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
        self.fake_claude()
        self.write_done([milestone("M1", "parked", ["open"])])
        self.commit_all()
        planned = self.plan(host="claude")
        self.assertTrue(planned["next"]["command"].endswith("--host claude"), planned["next"])
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertNotIn("--host", self.ready()["next"]["command"])

    def test_r17_planners_get_the_loop_path_and_dont_hunt_for_host_clis(self):
        self.plan()
        prompt = [c for c in self.calls() if c["role"] == "plan"][0]["argv"][-1]
        self.assertIn(f"python3 {agent_loop.LOOP} check --module <M> --milestone <id> --worktree .", prompt)
        self.assertIn("The loop finds the host CLIs (codex, claude) itself", prompt)

    def test_r10_everything_a_planner_writes_lands_with_its_plan(self):
        os.environ.update(FAKE_PLAN="catch_up")  # nothing new on the tip, so the fast-forward moves nothing
        planned = self.plan()
        self.assertEqual((planned["result"], planned["landed"]), ("PLANNED", True), planned)
        files = self.git("ls-tree", "-r", "--name-only", "origin/main").stdout.split()
        self.assertIn("acceptance/test_pay.py", files)

    def test_r13_a_planner_that_lands_a_forged_record_itself_is_refused(self):
        os.environ.update(FAKE_PLAN_SIDE="push")
        refused = self.plan()
        self.assertEqual((refused["result"], refused["landed"]), ("INVALID", False), refused)
        self.assertIn("without the loop's trailer changed an acceptance record on the tip", refused["problems"][0])
        # no revert handed out: the owner decides what happens to a commit already on the tip
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "owner"))

    def test_r13_a_planner_that_fakes_the_tracking_ref_is_refused(self):
        os.environ.update(FAKE_PLAN_SIDE="ref")
        refused = self.plan()
        self.assertEqual((refused["result"], refused["landed"]), ("INVALID", False), refused)
        self.assertIn("the planner committed in this worktree", refused["problems"][0])
        self.assertIn("tidy", refused["problems"][0])
        self.assertEqual((refused["next"]["command"], refused["next"]["by"]), (None, "lead"))
        self.assertNotIn("forged", self.git("show", "origin/main:docs/modules/WATER-ACCEPTED.json").stdout)
        # the lead sets the turn aside by hand; the next plan lands nothing of it
        self.git("reset", "-q", "--hard", "origin/main")
        self.git("clean", "-qfd")
        os.environ.pop("FAKE_PLAN_SIDE")
        planned = self.plan()
        self.assertEqual(planned["result"], "PLANNED", planned)
        self.assertNotIn("forged", self.git("show", "origin/main:docs/modules/WATER-ACCEPTED.json").stdout)

    def test_r15_a_second_refusal_from_the_same_start_is_refused_the_same_way(self):
        os.environ.update(FAKE_PLAN_SIDE="ref")
        first = self.plan()
        self.git("reset", "-q", "--hard", "origin/main")
        self.git("clean", "-qfd")
        second = self.plan()
        self.assertEqual((first["result"], second["result"]), ("INVALID", "INVALID"), second)
        self.assertEqual(first["next"], second["next"])  # no branch to collide with

    def test_r13_a_plan_on_commits_the_tip_lacks_is_refused(self):
        (self.wt / "notes.txt").write_text("x")
        self.git("add", "-A")
        self.git("commit", "-qm", "side work")
        refused = self.plan()
        self.assertEqual(refused["result"], "INVALID", refused)
        self.assertIn("1 commit the integrated tip doesn't: ", refused["problems"][0])
        self.assertIn("side work", refused["problems"][0])
        self.assertIn(" worktree add --detach ", refused["next"]["command"])
        self.assertIn("-plan-", refused["next"]["command"])
        self.assertNotIn("reset", refused["next"]["command"])  # this checkout and its commits are left alone
        self.assertIn(" plan --worktree ", refused["next"]["then"])
        self.assertIn("-plan-", refused["next"]["then"])
        self.assertIn(" adopt ", refused["next"]["alternative"])
        self.assertFalse(self.log.exists())  # no planner turn was spent
        subprocess.run(refused["next"]["command"], shell=True, check=True, capture_output=True)
        fresh = Path(refused["next"]["then"].split("--worktree ")[1].split(" ")[0])
        self.assertEqual(agent_loop.head_commit(fresh), self.git("rev-parse", "origin/main").stdout.strip())
        self.assertIn("side work", self.git("log", "-1", "--format=%s").stdout)

    def test_r13_land_refuses_plan_and_review_sessions(self):
        for role in ("plan", "review"):
            with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": role}), self.assertRaises(SystemExit) as stop:
                agent_loop.cmd_land(argparse.Namespace(worktree=str(self.wt), no_check=False))
            self.assertIn(f"land isn't for a {role} session", str(stop.exception))

    def test_r10_a_refused_plan_says_what_to_do(self):
        os.environ.update(FAKE_PLAN="forge")
        refused = self.plan(task="x")
        self.assertEqual(refused["result"], "INVALID")
        self.assertIn("stash push --include-untracked", refused["next"]["command"])
        self.assertIn(" plan --worktree ", refused["next"]["command"])
        self.assertIn("only the loop writes acceptance records", refused["next"]["command"])

    def test_r10_a_second_planner_is_told_to_wait_for_the_first(self):
        code = (f"import sys, time; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop\n"
                f"from pathlib import Path; wt = Path({str(self.wt)!r}); agent_loop.run_lock(wt, '_plan')\n"
                "agent_loop.loop_register(wt, 'plan', task='Revise CORE', host='claude', model='m', effort='high')\n"
                "print('up', flush=True); time.sleep(60)\n")
        proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "up")
            taken = self.plan(task="Revise REPORT", host="codex")
        finally:
            proc.kill()
            proc.wait()
            proc.stdout.close()
        self.assertEqual(taken["result"], "TAKEN")
        self.assertIn(f"pid {proc.pid}", taken["by"])
        self.assertIn("one planner runs per repository", taken["next"]["why"])
        self.assertIn(" plan --worktree ", taken["next"]["command"])
        self.assertIn("--task 'Revise REPORT' --host codex", taken["next"]["command"])

    def test_r10_a_claim_for_review_names_the_review_command(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Review host:** other\n")
        self.write_done([milestone("M1", "open", ["open"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        claim = self.run_loop()
        self.assertEqual((claim["result"], claim["review"]), ("CLAIMED", True), claim)
        self.assertIn(f" review --module WATER --milestone M1 --commit {claim['commit']} ", claim["next"]["command"])
        self.assertTrue(claim["next"]["command"].endswith("--host claude"), claim["next"]["command"])

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

    def test_r10_the_build_row_doesnt_carry_the_design_reviews_tokens(self):
        self.draft()
        script = self.root / "loops-script.py"
        script.write_text(f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import agent_loop; agent_loop.main()\n")
        seen = self.root / "seen.jsonl"
        os.environ.update(FAKE_REVIEW="design", FAKE_USAGE="1", FAKE_LOOPS=str(seen), FAKE_LOOPS_SCRIPT=str(script))
        claim = self.run_loop()
        self.assertEqual(claim["result"], "CLAIMED", claim)
        rows = [json.loads(l) for l in seen.read_text().splitlines()]
        build = [r for snap in rows for r in snap.get("loops", snap) if isinstance(r, dict) and r.get("role") == "build"]
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
        self.write_done([milestone("M1", "open", ["open"], inspect="drive it in a browser"),
                         milestone("M2", "open", ["open"])])
        self.commit_all()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual([w for w in agent_loop.preflight("codex", self.wt, "review") if "browser" in w], [])
            build = [w for w in agent_loop.preflight("codex", self.wt, "build") if "browser" in w]
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
        rec = json.loads(self.git("show", "origin/main:docs/modules/PAY-ACCEPTED.json").stdout)
        self.assertEqual(rec["briefs"][-1]["task"], ask)
        self.assertEqual(rec["milestones"]["M1"]["authorised"]["task"], ask[:120])  # the whole ask is kept once
        self.assertIn("and when the input is empty, says so", self.git("log", "--format=%B", "origin/main").stdout)
        self.git("pull", "-q", "--rebase", "origin", "main")
        os.environ.update(FAKE_REVIEW="design")
        self.review("design", module="PAY", commit=None)
        self.assertIn("docs/modules/PAY-ACCEPTED.json under `briefs`", self.calls()[-1]["argv"][-1])

    def test_r12_a_planners_assumptions_are_counted_and_reported(self):
        os.environ.update(FAKE_ASSUME="\n\n## Log\n\n- Assumption: accents means any letter with a Latin base\n"
                                       "Assumption: the size limit is in bytes\nNot an assumption: this line\n")
        planned = self.plan()
        self.assertEqual(planned["assumptions"], {"PAY": 2}, planned)
        self.git("pull", "-q", "--rebase", "origin", "main")
        report = self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=False)
        section = report.split("## Assumptions the planners made (for the owner to overturn)")[1].split("\n## ")[0]
        self.assertIn("- PAY ([plan](docs/modules/PAY-PLAN.md)):", section)
        self.assertIn("  - accents means any letter with a Latin base", section)
        self.assertIn("  - the size limit is in bytes", section)
        self.assertNotIn("this line", section)

    def test_r12_a_written_report_links_from_where_it_lives(self):
        quoted = "a reviewer wrote [see](docs/x.md) and [u](https://x.test/a)"  # not the report's own links
        text = (agent_loop.md_link("r", "docs/evidence/WATER/M1-review.md") + " "
                + agent_loop.md_link("p", "docs/modules/PAY-PLAN.md") + " " + quoted)
        self.assertEqual(agent_loop.relink(text, "docs/evidence/build-reports"),
                         "[r](../WATER/M1-review.md) [p](../../modules/PAY-PLAN.md) " + quoted)
        self.assertEqual(agent_loop.relink(text, None),
                         "[r](docs/evidence/WATER/M1-review.md) [p](docs/modules/PAY-PLAN.md) " + quoted)
        os.environ.update(FAKE_ASSUME="\n- Assumption: one\n")
        self.plan()
        self.git("pull", "-q", "--rebase", "origin", "main")
        written = json.loads(self.printed(agent_loop.cmd_report, worktree=str(self.wt), since=24.0, write=True))
        body = (self.wt / written["written"]).read_text()
        self.assertIn("([plan](../../modules/PAY-PLAN.md))", body)

    def test_r13_a_run_that_builds_nothing_isnt_recorded_as_the_modules_run(self):
        self.write_done([milestone("M1", "claimed", ["pass"], inspect="frames"), milestone("M2", "open", ["open"])])
        self.commit_all()
        owed = self.run_loop(host="claude")
        self.assertEqual(owed["result"], "REVIEW_OWED", owed)
        agent_loop.RUN_HERE.clear()
        self.assertEqual(agent_loop.known_run(str(self.wt), "WATER"), {})
