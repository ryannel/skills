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
    mode = os.environ.get("FAKE_PLAN", "")
    turn = sum(json.loads(l)["role"] == "plan" for l in open(os.environ["FAKE_LOG"]))
    files = ["docs/modules/PAY-DONE.json"] + ([] if mode == "nodesign" else ["docs/modules/PAY.md",
                                                                             "docs/modules/PAY-PLAN.md"])
    if mode == "forge":
        (cwd / "docs/modules/WATER-ACCEPTED.json").write_text("{}")
        reply = "PLANNED: docs/modules/WATER-ACCEPTED.json"
    elif mode == "progress" or (mode == "late" and turn == 1):
        reply = "I've read the brief. Next I'll write the PAY design and its done-when file."
    elif mode == "blocked":
        (cwd / "docs/modules/PAY.md").write_text("# Pay design, half done")
        reply = "BLOCKED: the owner must choose the payment provider"
    else:
        if mode != "nodesign":
            (cwd / "docs/modules/PAY.md").write_text("# Pay design")
            (cwd / "docs/modules/PAY-PLAN.md").write_text("# Pay plan")
        (cwd / "docs/modules/PAY-DONE.json").write_text(json.dumps({"module": "PAY", "milestones": [
            {"id": "M1", "name": "pay", "state": "open", "fails": 0, "replans": 0,
             "items": [{"id": "M1.1", "statement": "pays", "check": "true", "status": "open", "evidence": ""}]}]}))
        reply = "Planned PAY. No owner decisions.\\nPLANNED: " + ", ".join(files)
if "claude" in Path(sys.argv[0]).name:
    model = sys.argv[sys.argv.index("--model") + 1]
    sid = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a in ("--session-id", "--resume")), "s1")
    print(json.dumps({"type": "system", "subtype": "init", "session_id": sid, "model": model}))
    print(json.dumps({"type": "result", "subtype": "success", "session_id": sid, "result": reply, "is_error": False}))
else:
    print(json.dumps({"type": "thread.started", "thread_id": "t1"}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": reply}}))
"""

FAKE_ENV = ("FAKE_VERSION", "FAKE_STATE", "FAKE_WEAKEN", "FAKE_FORGE", "FAKE_UPSTREAM_BREAK", "FAKE_REVIEW", "FAKE_PLAN",
            "FAKE_EXIT", "FAKE_SKIP_ATTENDED", "ORCHESTRATE_ROLE", "ORCHESTRATE_HEADLESS")


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
                      agent_loop.CLAUDE_HOME, agent_loop.AGENTS_HOME)
        agent_loop.CLAUDE_HOME, agent_loop.AGENTS_HOME = root / "claude-home", root / "agents-home"
        agent_loop.CODEX, agent_loop.CODEX_HOME = str(fake), self.home
        # No app on this machine counts: the Codex IPC socket lives under the fake CODEX_HOME, and Claude desktop's
        # session store is pointed at a folder that doesn't exist. Visible-session tests fake the apps explicitly.
        agent_loop.CLAUDE_APP_STORE = root / "no-claude-desktop"
        for key in FAKE_ENV:
            os.environ.pop(key, None)
        os.environ.update(FAKE_LOG=str(self.log), FAKE_PASS="1", FAKE_REPLY="DONE", FAKE_COMMIT="1")

    def tearDown(self):
        release()
        (agent_loop.CODEX, agent_loop.CODEX_HOME, agent_loop.CLAUDE, agent_loop.CLAUDE_APP_STORE,
         agent_loop.CLAUDE_HOME, agent_loop.AGENTS_HOME) = self.saved
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
                    clear_owner_rules=False)
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
        self.assertEqual((result["result"], result["verdict"], result["fails"], result["next"]),
                         ("REVIEWED", "FAIL", 1, "same-session"))
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
        self.write_done([dict(milestone("M1", "open", ["open"], inspect="frames"), fails=3, replans=1),
                         milestone("M2", "open", ["open"])])
        self.commit_all()
        commit = self.claim()
        os.environ.update(FAKE_REVIEW="fail")
        self.assertEqual(self.review(commit=commit)["next"], "park")
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


class FakeCodexApp:
    """Stands in for the Codex desktop app. A thread is a rollout file under the fake CODEX_HOME; a wake link runs the
    fake host as the app's turn would (in the thread's folder, with its role) and appends the turn's events."""

    def __init__(self, case, behaviour="run", effort_seen=None):
        self.case, self.behaviour, self.effort_seen = case, behaviour, effort_seen
        self.threads, self.queued, self.links, self.interrupts, self.activated = {}, {}, [], [], []
        self.sent = []

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

    def wake(self, t):
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
            codex_interrupt=self.interrupt, codex_queued=lambda t: int(t in self.queued),
            codex_goal_activate=lambda t: self.activated.append(t) or True,
            SETTLE_S=0.0, POLL_S=0.01, START_S=0.2, CLAUDE_IMPORT_WAIT_S=0.0,
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
            threading.Timer(0.5, lambda: setattr(agent_loop, "_STOP", True)).start()
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
                      review="r", task="t", evidence="e")
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
        self.assertIn("Advisory findings never change the state.", review)
        self.assertIn("counting\n   blocking findings only", review)
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
