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


def entry_for(doc, design_ok=True):
    """A project entry as agent_loop.project builds it, with the design agreed unless told otherwise."""
    rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
    if design_ok:
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)}
    return {"stem": doc["module"], "doc": doc, "record": rec, "design": agent_loop.text_hash(None),
            "problems": agent_loop.validate(doc, doc["module"])}


def release():
    """In-process runs keep their run locks and signal handlers; tests run many in one process."""
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

    def test_forecast_from_last_day(self):
        h, now, reset = 3600, 1_000_000.0, 1_000_000.0 + 72 * 3600
        samples = [(now - 24 * h, 40.0, reset), (now - 12 * h, 45.0, reset), (now, 50.0, reset)]
        f = agent_loop.forecast(samples, now)
        self.assertEqual(f["per_day"], 10.0)
        self.assertIsNone(f["runs_out"])
        fast = [(now - 24 * h, 20.0, reset), (now, 50.0, reset)]
        self.assertIsNotNone(agent_loop.forecast(fast, now)["runs_out"])
        old_window = [(now - 20 * h, 90.0, now - 10 * h), (now - 2 * h, 1.0, reset), (now, 2.0, reset)]
        self.assertEqual(agent_loop.forecast(old_window, now)["per_day"], 12.0)

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

    def test_reviewer_fail_must_add_exactly_one_fail(self):
        before = done(milestone("M1", "claimed", ["pass"]))
        a = json.loads(json.dumps(before))
        a["milestones"][0].update(state="in_progress", fails=2)
        self.assertTrue(any("exactly 1" in p for p in agent_loop.delta_problems(before, a, "review", "M1")))

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
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x", "CLAUDE_CONFIG_DIR": "/c", "CLAUDECODE": "1"}):
            env = agent_loop.clean_env("review")
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual((env["CLAUDE_CONFIG_DIR"], env["ORCHESTRATE_ROLE"]), ("/c", "review"))

    def test_claude_stream_parsing(self):
        out = "\n".join(json.dumps(e) for e in [
            {"type": "system", "subtype": "init", "session_id": "s9", "model": "claude-opus-5-5"},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "working"}]}},
            {"type": "result", "result": "BLOCKED: no device", "is_error": False}])
        self.assertEqual(agent_loop.parse_output("claude", out), ("s9", "BLOCKED: no device", "claude-opus-5-5", False))


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
role = os.environ.get("ORCHESTRATE_ROLE", "build")
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "role": role,
                          "api_key": "ANTHROPIC_API_KEY" in os.environ}) + "\\n")
if os.environ.get("FAKE_EXIT"):
    sys.exit(int(os.environ["FAKE_EXIT"]))
cwd = Path(os.getcwd())
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
    d = json.loads(path.read_text())
    target = next((m for m in d["milestones"] if m["state"] == "claimed"), None)
    ev = cwd / "docs/evidence/WATER"
    ev.mkdir(parents=True, exist_ok=True)
    if mode == "design":
        (ev / "design-review.md").write_text("design is fine")
        reply = "DESIGN OK"
    elif mode == "nothing":
        reply = "PASS M999"
    else:
        mid, verdict = target["id"], ("fail" if mode == "fail" else "pass")
        for i in target["items"]:
            i["verdict"], i["review"] = verdict, f"docs/evidence/WATER/{mid}-review.md"
        if verdict == "pass":
            target["state"] = "done"
        else:
            target["state"], target["fails"] = "in_progress", target.get("fails", 0) + 1
        if mode == "delete":
            d["milestones"] = [m for m in d["milestones"] if m is target or m["state"] != "open"]
        path.write_text(json.dumps(d))
        (ev / f"{mid}-review.md").write_text(f"review of {mid}: {verdict}")
        if mode == "overreach":
            (cwd / "src.txt").write_text("fixed it myself")
        reply = f"PASS {mid}" if verdict == "pass" else f"FAIL {mid}: 1 fail, 0 cant_tell, 0 outside the items"
elif role == "plan":
    if os.environ.get("FAKE_PLAN") == "forge":
        (cwd / "docs/modules/WATER-ACCEPTED.json").write_text("{}")
    else:
        (cwd / "docs/modules/PAY.md").write_text("# Pay design")
        (cwd / "docs/modules/PAY-PLAN.md").write_text("# Pay plan")
        (cwd / "docs/modules/PAY-DONE.json").write_text(json.dumps({"module": "PAY", "milestones": [
            {"id": "M1", "name": "pay", "state": "open", "fails": 0, "replans": 0,
             "items": [{"id": "M1.1", "statement": "pays", "check": "true", "status": "open", "evidence": ""}]}]}))
    reply = "Planned PAY. Files: docs/modules/PAY*. No owner decisions."
if "claude" in Path(sys.argv[0]).name:
    model = sys.argv[sys.argv.index("--model") + 1]
    print(json.dumps({"type": "system", "subtype": "init", "session_id": "s1", "model": model}))
    print(json.dumps({"type": "result", "subtype": "success", "session_id": "s1", "result": reply, "is_error": False}))
else:
    print(json.dumps({"type": "thread.started", "thread_id": "t1"}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": reply}}))
"""

FAKE_ENV = ("FAKE_STATE", "FAKE_WEAKEN", "FAKE_FORGE", "FAKE_UPSTREAM_BREAK", "FAKE_REVIEW", "FAKE_PLAN",
            "FAKE_EXIT", "FAKE_SKIP_ATTENDED", "ORCHESTRATE_ROLE")


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
        self.saved = (agent_loop.CODEX, agent_loop.CODEX_HOME, agent_loop.CLAUDE)
        agent_loop.CODEX, agent_loop.CODEX_HOME = str(fake), self.home
        for key in FAKE_ENV:
            os.environ.pop(key, None)
        os.environ.update(FAKE_LOG=str(self.log), FAKE_PASS="1", FAKE_REPLY="DONE", FAKE_COMMIT="1")

    def tearDown(self):
        release()
        agent_loop.CODEX, agent_loop.CODEX_HOME, agent_loop.CLAUDE = self.saved
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
                    budget_hours=4.0, turn_timeout_hours=0.1, host=None, model=None, effort=None)
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

    def owner(self, action, milestone_id, reason="owner said so", where=None):
        with mock.patch.object(agent_loop, "owner_confirm", lambda *a: None):
            return self.call(agent_loop.cmd_owner, action=action, module="WATER", milestone=milestone_id,
                             worktree=str(where or self.wt), reason=reason)

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def state(self):
        return json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())


class Building(Repo):
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
        self.assertEqual(self.run_loop()["result"], "DESIGN_OWED")
        os.environ.update(FAKE_REVIEW="design")
        self.assertEqual(self.review("design")["verdict"], "DESIGN OK")
        os.environ.pop("FAKE_REVIEW")
        self.assertEqual(self.run_loop()["result"], "CLAIMED")

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
        self.assertEqual((result["result"], result["verdict"], result["fails"]), ("REVIEWED", "FAIL", 1))
        m1 = self.read_done()["milestones"][0]
        self.assertEqual((m1["state"], m1["items"][0]["status"], m1["items"][0]["evidence"]), ("in_progress", "open", ""))
        self.assertEqual(m1["items"][0]["verdict"], "fail")
        # The builder resumes its session with the findings, in its worktree.
        os.environ.pop("FAKE_REVIEW")
        self.run_loop(message="FINDINGS")
        last = self.calls()[-1]
        self.assertEqual(last["argv"][last["argv"].index("resume") + 1], "t1")
        self.assertIn("--add-dir", last["argv"][:last["argv"].index("resume")])
        self.assertEqual(last["argv"][-1], "FINDINGS")

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
        self.assertEqual(self.read_record()["milestones"]["M1"]["accepted"]["by"], "owner")
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
        with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit):
            agent_loop.owner_confirm("accept", "WATER:M1")
        env = {k: v for k, v in os.environ.items() if k != "ORCHESTRATE_ROLE"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(sys, "stdin", io.StringIO("WATER:M1\n")):
            with self.assertRaises(SystemExit):
                agent_loop.owner_confirm("accept", "WATER:M1")

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
        self.assertEqual(self.read_record()["milestones"]["M1"]["authorised"]["by"], "owner")
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
                f"agent_loop.run_lock(Path({str(self.wt)!r}), 'WATER'); agent_loop.install_stop(); print('up', flush=True)\n"
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
