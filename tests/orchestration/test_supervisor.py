"""Checks the supervisor: one per repository, started by any command and again after it dies, stopped when the build
is finished, waits on the user or the user stops it; the builders it starts itself; and each host adapter that wakes
the lead, against a fake host: a Claude Code inbox socket, the Codex app's queue, and a command from the settings."""

import json
import os
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import PROFILE, Clean, Repo, agent_loop, release  # noqa: E402


class FakeClaudeSession:
    """A Claude Code session's inbox socket: it reads each connection's lines, as Claude Code does. The path is
    short, because a Unix socket's path is limited to about 100 bytes."""

    def __init__(self):
        self.folder = tempfile.mkdtemp(prefix="cc", dir="/tmp")
        self.path = os.path.join(self.folder, "s.sock")
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.path)
        self.server.listen(5)
        self.messages = []
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            with conn:
                data = b""
                while chunk := conn.recv(65536):
                    data += chunk
            self.messages.append([json.loads(line) for line in data.decode().splitlines() if line])

    def close(self):
        self.server.close()
        Path(self.path).unlink(missing_ok=True)
        os.rmdir(self.folder)

    def texts(self):
        return [m[-1]["message"]["content"] for m in self.messages]


def look(steps=None, loops=(), limit=2, free=2, broken=(), running=(), ahead=()):
    """What `watch_look` returns, cut to what the supervisor reads."""
    return {"steps": steps or {}, "loops": list(loops), "limit": limit, "free": free, "broken": list(broken),
            "running": set(running), "ahead": list(ahead)}


def step(module, status, **more):
    return {"module": module, "status": status, **more}


class Wiring(Repo):
    """What the supervisor needs from a repository, with no supervisor process: a lead's record, wakes, waiters."""

    def setUp(self):
        super().setUp()
        self.folder = agent_loop.loop_dir(self.wt)
        agent_loop.SUPERVISOR_ON = True

    def lead(self, **rec):
        agent_loop.write_private(self.folder / agent_loop.LEAD_FILE, rec)

    def claude(self):
        session = FakeClaudeSession()
        self.addCleanup(session.close)
        self.lead(host="claude", session="s1", socket=session.path, token="t0k")
        return session


class RecordingTheLead(Wiring):
    """A lead's command records how to reach it; nothing else's does."""

    def test_a_claude_code_lead_is_recorded_with_its_socket_and_token_where_only_this_user_can_read_it(self):
        os.environ.update(CLAUDECODE="1", CLAUDE_CODE_SESSION_ID="s1", CLAUDE_CODE_MESSAGING_SOCKET="/tmp/x.sock",
                          CLAUDE_CODE_MESSAGING_TOKEN="t0k", CLAUDE_CODE_ENTRYPOINT="claude-desktop")
        agent_loop.note_lead(self.wt)
        path = self.folder / agent_loop.LEAD_FILE
        rec = json.loads(path.read_text())
        self.assertEqual((rec["host"], rec["session"], rec["socket"], rec["token"]), ("claude", "s1", "/tmp/x.sock", "t0k"))
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_a_codex_lead_is_an_app_thread_when_its_rollout_says_the_app_started_it(self):
        sessions = self.home / "sessions/2026/11/23"
        sessions.mkdir(parents=True)
        for thread, origin, source in (("app1", "codex_work_desktop", "vscode"), ("cli1", "codex_exec", "exec")):
            (sessions / f"rollout-2026-11-23T10-00-00-{thread}.jsonl").write_text(json.dumps(
                {"type": "session_meta", "payload": {"id": thread, "originator": origin, "source": source}}) + "\n")
            os.environ["CODEX_THREAD_ID"] = thread
            self.assertEqual(agent_loop.note_lead(self.wt)["app_thread"], thread == "app1")

    def test_a_builder_thread_and_an_unknown_host_dont_replace_the_lead(self):
        self.lead(host="claude", session="s1", socket="/tmp/x.sock")
        (self.folder / "threads.jsonl").write_text(json.dumps({"session": "builder1"}) + "\n")
        os.environ["CODEX_THREAD_ID"] = "builder1"
        self.assertEqual(agent_loop.note_lead(self.wt)["session"], "s1")
        del os.environ["CODEX_THREAD_ID"]
        self.assertEqual(agent_loop.note_lead(self.wt)["session"], "s1")  # a person's terminal

    def test_a_session_the_script_started_never_records_itself(self):
        os.environ.update(CLAUDECODE="1", CLAUDE_CODE_SESSION_ID="b1", ORCHESTRATE_ROLE="build")
        with mock.patch.object(agent_loop, "ensure_supervisor", lambda *a, **k: True):
            agent_loop.supervise_hook("status", self.wt)
        self.assertFalse((self.folder / agent_loop.LEAD_FILE).exists())
        os.environ.pop("ORCHESTRATE_ROLE")
        with mock.patch.object(agent_loop, "ensure_supervisor", lambda *a, **k: True):
            agent_loop.supervise_hook("merge", self.wt)  # a builder's command
        self.assertFalse((self.folder / agent_loop.LEAD_FILE).exists())


class WakingTheLead(Wiring):
    """Each host adapter, against a fake host; `watch` first when one waits; a wake that reaches nobody is kept."""

    def deliver(self, prof=None, word="RUN_ENDED"):
        return agent_loop.deliver_wake(self.wt, prof or {"lead_wake": "auto"}, word,
                                       {"woke_for": ["build WATER ended"]})

    def test_claude_code_is_woken_by_a_message_on_its_inbox_socket_with_its_token(self):
        session = self.claude()
        rec = self.deliver()
        self.assertEqual((rec["delivered"], rec["via"]), (True, "claude"), rec)
        deadline = time.time() + 5
        while not session.messages and time.time() < deadline:
            time.sleep(0.02)
        auth, user = session.messages[0]
        self.assertEqual(auth, {"type": "auth", "token": "t0k"})
        self.assertEqual(user["type"], "user")
        self.assertIn("RUN_ENDED", user["message"]["content"])
        self.assertIn("not from the user", user["message"]["content"])

    def test_codex_app_thread_is_woken_by_a_queued_message_and_a_cli_thread_is_not(self):
        calls = self.root / "queue-calls"
        fake = self.root / "codex-app"
        fake.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" >> {calls}\necho \"Queued message m1 for thread $3.\"\n")
        fake.chmod(0o755)
        agent_loop.CODEX_APP_CLI = str(fake)
        self.lead(host="codex", session="app1", app_thread=True)
        rec = self.deliver()
        self.assertEqual((rec["delivered"], rec["via"]), (True, "codex"), rec)
        words = calls.read_text().splitlines()
        self.assertEqual(words[:4], ["queue", "--thread", "app1", "--resume"])
        self.lead(host="codex", session="cli1", app_thread=False)
        rec = self.deliver()
        self.assertFalse(rec["delivered"])
        self.assertIn("isn't one the desktop app holds", rec["error"])

    def test_the_settings_command_wakes_a_host_the_script_doesnt_know(self):
        out = self.root / "woken"
        self.lead(host="other", session=None)
        rec = self.deliver({"lead_wake": f"printf %s {{message}} > {out}"})
        self.assertTrue(rec["delivered"], rec)
        self.assertIn("RUN_ENDED", out.read_text())

    def test_a_running_watch_takes_the_wake_and_nothing_is_pushed(self):
        session = self.claude()
        waiter = subprocess.Popen(["sleep", "30"])
        self.addCleanup(lambda: (waiter.kill(), waiter.wait()))
        agent_loop.write_atomically(self.folder / agent_loop.WAITER_FILE, {"pid": waiter.pid})
        rec = self.deliver()
        self.assertEqual(rec["via"], "watch")
        time.sleep(0.2)
        self.assertEqual(session.messages, [])

    def test_a_wake_that_reaches_nobody_is_carried_by_the_leads_next_result_with_the_watch_to_start(self):
        self.lead(host="claude", session="s1", socket="/tmp/gone.sock")  # the session has ended
        rec = self.deliver()
        self.assertFalse(rec["delivered"])
        agent_loop.WAKE_CONTEXT = {"worktree": self.wt, "setting": "auto"}
        with mock.patch.object(agent_loop, "supervisor_alive", lambda folder: True):
            line = self.call(agent_loop.cmd_ready, worktree=str(self.wt))
        self.assertEqual(line["wake"]["missed"]["result"], "RUN_ENDED")
        self.assertTrue(line["wake"]["run_in_background"])
        self.assertIn("watch", line["wake"]["command"])
        self.assertTrue(any("nothing can wake you" in w for w in line["warnings"]))

    def test_a_lead_the_supervisor_can_push_to_is_told_nothing(self):
        self.claude()
        agent_loop.WAKE_CONTEXT = {"worktree": self.wt, "setting": "auto"}
        with mock.patch.object(agent_loop, "supervisor_alive", lambda folder: True):
            line = self.call(agent_loop.cmd_ready, worktree=str(self.wt))
        self.assertNotIn("wake", line)
        # the user's Lead wake line can turn the push off, and then the lead keeps `watch`
        agent_loop.WAKE_CONTEXT = {"worktree": self.wt, "setting": "watch"}
        with mock.patch.object(agent_loop, "supervisor_alive", lambda folder: True):
            line = self.call(agent_loop.cmd_ready, worktree=str(self.wt))
        self.assertIn("Lead wake line says watch", line["wake"]["why"])

    def test_watch_returns_the_supervisors_next_wake_and_a_missed_one_at_once(self):
        held = agent_loop.take_file_lock(self.folder / agent_loop.SUPERVISOR_LOCK)  # a supervisor, as far as
        self.addCleanup(held.close)  # anyone else can tell
        self.lead(host="claude", session="s1", socket="/tmp/gone.sock")
        self.deliver(word="CHECK_IN")  # reaches nobody
        got = agent_loop.wait_for_wake(self.wt)
        self.assertEqual(got[0], "CHECK_IN")

        def later():
            time.sleep(0.3)
            self.deliver(word="WARNING_SIGNS")
        threading.Thread(target=later).start()
        with mock.patch.object(agent_loop, "WATCH_POLL_S", 0.02):
            got = agent_loop.wait_for_wake(self.wt)
        self.assertEqual(got, ("WARNING_SIGNS", {"woke_for": ["build WATER ended"]}))
        self.assertTrue(json.loads((self.folder / agent_loop.WAKE_FILE).read_text())["delivered"])
        self.assertFalse((self.folder / agent_loop.WAITER_FILE).exists())


class StartingBuilders(Clean):
    """The supervisor starts the routine runs, up to the builders count, and leaves the lead's judgement alone."""

    def setUp(self):
        super().setUp()
        self.started = []
        self.results = {}
        for name, value in (("start_run", lambda worktree, prof, stem: self.started.append(stem) or True),
                            ("latest_result", lambda folder, stem: self.results.get(stem)),
                            ("loop_dir", lambda worktree: Path("/nowhere"))):
            patch = mock.patch.object(agent_loop, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def fill(self, seen, started=None):
        return agent_loop.fill_builders(Path("/repo"), {}, seen, started if started is not None else {})

    def test_it_fills_the_free_slots_with_modules_that_can_start(self):
        steps = {k: step(k, "can_start") for k in ("A", "B", "C")}
        self.assertEqual(self.fill(look(steps, free=2)), ["A", "B"])
        self.started.clear()
        steps["B"] = step("B", "ready_for_review")
        self.assertEqual(self.fill(look(steps, free=5, running={"A"})), ["B", "C"])

    def test_no_builders_count_a_broken_test_command_or_a_busy_module_starts_nothing(self):
        steps = {"A": step("A", "can_start")}
        self.assertEqual(self.fill(look(steps, limit=None)), [])
        self.assertEqual(self.fill(look(steps, broken=[{"check": "test command"}])), [])
        self.assertEqual(self.fill(look(steps, loops=[{"role": "review", "module": "A"}])), [])
        self.assertEqual(self.fill(look(steps), started={"A": time.time()}), [])

    def test_a_module_runs_in_its_own_worktree_and_never_in_the_main_checkout(self):
        main, own = Path("/repo"), Path("/repo/.claude/worktrees/water")
        with mock.patch.object(agent_loop, "main_checkout", lambda worktree: main), \
                mock.patch.object(Path, "exists", lambda self: True), \
                mock.patch.object(agent_loop, "worktrees_by_branch", lambda worktree: {"build/water": own}):
            self.assertEqual(agent_loop.run_worktree(main, {}, "WATER").as_posix(), own.resolve().as_posix())
            self.assertIsNone(agent_loop.run_worktree(main, {}, "SKY"))
            self.assertEqual(agent_loop.run_worktree(main, {"worktrees": ".wt"}, "SKY"), main)

    def test_the_supervisor_drops_the_codex_turn_that_started_it(self):
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "t1", "CODEX_CI": "1", "ORCHESTRATE_ROLE": "build"}):
            env = agent_loop.supervised_env()
        self.assertFalse({"CODEX_THREAD_ID", "CODEX_CI", "ORCHESTRATE_ROLE"} & set(env))
        self.assertEqual(env[agent_loop.SUPERVISED_ENV], "1")

    def test_a_builders_count_saved_while_it_waits_is_read_at_the_next_look(self):
        prof = {"builders": None, "check_in_s": 3600}
        with mock.patch.object(agent_loop, "profile", lambda worktree: {"builders": 2, "check_in_s": 3600}):
            self.assertIsNone(agent_loop.supervise_tick(Path("/repo"), prof, look({"A": step("A", "can_start")},
                                                                                limit=None), True, {}))
        self.assertEqual(prof["builders"], 2)

    def test_only_a_result_that_left_nothing_for_the_lead_lets_it_start_the_module(self):
        loop = str(agent_loop.LOOP)

        def then(*words, **more):
            return {"command": "x", "argv": ["python3", loop, *words], "by": "lead", **more}
        allowed = [None, {"result": "WAITING"}, {"result": "REVIEWED", "verdict": "PASS"},
                   {"result": "UNBLOCKED", "next": then("run", "--module", "A", "--worktree", "/r")}]
        refused = [{"result": "RUNNING"},
                   {"result": "BLOCKED", "next": then("run", "--module", "A", "--worktree", "/r",
                                                      decides="human", ask="Give access?")},
                   {"result": "STALLED", "next": then("run", "--module", "A", "--fresh", "--message", "why")},
                   {"result": "HOST_FAILED", "next": then("run", "--module", "A", "--host", "claude")},
                   {"result": "PAUSED", "next": None},
                   {"result": "REVIEWED", "verdict": "FAIL", "next": then("plan", "--task", "diagnose")}]
        for line in allowed:
            self.assertTrue(agent_loop.routine_start(line, "A"), line)
        for line in refused:
            self.assertFalse(agent_loop.routine_start(line, "A"), line)


class EndingTheBuild(Clean):
    def test_finished_and_waiting_for_the_user_end_it_and_anything_running_or_the_leads_doesnt(self):
        done = {"A": step("A", "finished"), "B": step("B", "finished")}
        self.assertEqual(agent_loop.build_end(look(done))[0], "BUILD_FINISHED")
        self.assertIsNone(agent_loop.build_end(look(done, loops=[{"role": "plan"}])))
        user = {"A": step("A", "blocked", reason="needs_access", milestone="M2"),
                "B": step("B", "waiting", reason="on_dependency")}
        word, lines = agent_loop.build_end(look(user))
        self.assertEqual(word, "WAITING_FOR_USER")
        self.assertIn("A M2 (needs_access)", lines[0])
        # a Blocked needs_context is the lead's to answer, and work a planner could plan now is the lead's too
        self.assertIsNone(agent_loop.build_end(look({"A": step("A", "blocked", reason="needs_context")})))
        self.assertIsNone(agent_loop.build_end(look(user, ahead=[{"module": "C"}])))


class SupervisorLife(Repo):
    """The supervisor as a process: started by a command, one per repository, started again after it dies, and
    stopped by the user or by the end of the build."""

    def setUp(self):
        super().setUp()
        agent_loop.SUPERVISOR_ON = True
        self.folder = agent_loop.loop_dir(self.wt)
        os.environ.update(ORCHESTRATE_CODEX=agent_loop.CODEX, ORCHESTRATE_CLAUDE=agent_loop.CLAUDE,
                          CODEX_HOME=str(self.home), CLAUDE_CONFIG_DIR=str(self.root / "claude-home"),
                          HOME=str(self.root / "home"))
        self.addCleanup(self.stop_all)

    def stop_all(self):
        info = json.loads((self.folder / agent_loop.SUPERVISOR_FILE).read_text()) \
            if (self.folder / agent_loop.SUPERVISOR_FILE).exists() else {}
        if info.get("pid") and agent_loop.pid_alive(info["pid"]):
            os.kill(info["pid"], signal.SIGKILL)

    def pid(self):
        """The pid of the supervisor that holds the lock, once one does: it takes a few seconds to start."""
        self.assertTrue(self.until(lambda: agent_loop.lock_held(self.folder / agent_loop.SUPERVISOR_LOCK) and
                                   (self.folder / agent_loop.SUPERVISOR_FILE).exists() and
                                   "pid" in json.loads((self.folder / agent_loop.SUPERVISOR_FILE).read_text())))
        return json.loads((self.folder / agent_loop.SUPERVISOR_FILE).read_text())["pid"]

    def until(self, test, limit=30):
        deadline = time.time() + limit
        while time.time() < deadline:
            if test():
                return True
            time.sleep(0.1)
        return False

    def gone(self):
        """Whether the supervisor has stopped, said why, and let go of its lock."""
        return "stopped" in json.loads((self.folder / agent_loop.SUPERVISOR_FILE).read_text()) and \
            not agent_loop.lock_held(self.folder / agent_loop.SUPERVISOR_LOCK)

    def no_builders(self):
        settings = self.wt / "ORCHESTRATE.md"
        settings.write_text(settings.read_text().replace("- **Builders:** 20 builders\n", ""))
        self.commit_all()

    def test_one_per_repository_started_again_after_it_dies_and_stopped_by_the_user(self):
        self.no_builders()
        self.assertTrue(agent_loop.ensure_supervisor(self.wt))
        first = self.pid()
        self.assertTrue(agent_loop.ensure_supervisor(self.wt))  # a second command finds it running
        self.assertEqual(self.pid(), first)
        os.kill(first, signal.SIGKILL)
        self.assertTrue(self.until(lambda: not agent_loop.lock_held(self.folder / agent_loop.SUPERVISOR_LOCK)))
        self.assertTrue(agent_loop.ensure_supervisor(self.wt))  # any command starts it again
        second = self.pid()
        self.assertNotEqual(second, first)
        # the user stops everything: it goes, and no command but the lead carrying on starts it again
        self.pid()
        line = self.call(agent_loop.cmd_pause, worktree=str(self.wt))
        self.assertIn(line["result"], ("NOTHING", "PAUSED"))
        self.assertTrue(self.until(self.gone))
        self.assertEqual(json.loads((self.folder / agent_loop.SUPERVISOR_FILE).read_text())["stopped"]["reason"],
                         "user")
        self.assertFalse(agent_loop.ensure_supervisor(self.wt))
        self.assertTrue(agent_loop.ensure_supervisor(self.wt, restart=True))

    def test_it_builds_the_module_wakes_the_lead_when_the_run_ends_and_stops_when_the_build_is_finished(self):
        settings = self.wt / "ORCHESTRATE.md"  # the supervisor starts a module only in a worktree of its own
        settings.write_text(settings.read_text().replace("- **Builders:**", "- **Worktrees:** .worktrees\n- **Builders:**"))
        self.commit_all()
        session = FakeClaudeSession()
        self.addCleanup(session.close)
        agent_loop.write_private(self.folder / agent_loop.LEAD_FILE,
                                 {"host": "claude", "session": "s1", "socket": session.path, "token": "t"})
        self.assertTrue(agent_loop.ensure_supervisor(self.wt))
        self.assertTrue(self.until(lambda: any("BUILD_FINISHED" in t for t in session.texts()), limit=150),
                        session.texts() or (self.folder / "supervisor.log").read_text())
        # the run's end wakes the lead, on its own or with the end of the build when both are seen at once
        words = [t.split(": ", 1)[1].split(".")[0] for t in session.texts()]
        self.assertEqual(words[-1], "BUILD_FINISHED", session.texts())
        self.assertEqual(set(words[:-1]) - {"RUN_ENDED"}, set())
        self.assertIn("steps WATER", " ".join(session.texts()))
        self.assertIn('"result": "REVIEWED"', " ".join(session.texts()))
        self.assertTrue(agent_loop.recorded_done(self.read_done()["milestones"][1], self.read_record()))
        self.assertTrue(self.until(self.gone))
        stopped = json.loads((self.folder / agent_loop.SUPERVISOR_FILE).read_text())["stopped"]
        self.assertEqual(stopped["reason"], "finished")
        self.assertFalse(agent_loop.ensure_supervisor(self.wt))  # nothing has moved since


class NewestCopyWins(Wiring):
    """Runs started on an older copy keep running its commands for hours, so the newest copy's supervisor must win."""

    def test_a_newer_supervisor_is_left_alone_and_ignores_an_older_copys_stop(self):
        stop = self.folder / agent_loop.SUPERVISOR_STOP
        agent_loop.write_atomically(self.folder / agent_loop.SUPERVISOR_FILE, {"pid": 1, "version": "99.0.0"})
        with mock.patch.object(agent_loop, "supervisor_alive", lambda folder: True):
            self.assertTrue(agent_loop.ensure_supervisor(self.wt))
        self.assertFalse(stop.exists(), "an older copy never stops a newer supervisor")
        stop.write_text("newer")  # as copies before 2.12.3 ask any other version to stop
        self.assertIsNone(agent_loop.supervise_tick(self.wt, {}, {"tip": None, "steps": {}, "loops": []}, False, {}))
        self.assertFalse(stop.exists())
        stop.write_text("user")
        self.assertEqual(agent_loop.supervise_tick(self.wt, {}, {}, False, {}), ("STOP", {"reason": "user"}))

    def test_an_older_supervisor_is_asked_to_stop(self):
        stop = self.folder / agent_loop.SUPERVISOR_STOP
        agent_loop.write_atomically(self.folder / agent_loop.SUPERVISOR_FILE, {"pid": 1, "version": "2.0.0"})
        with mock.patch.object(agent_loop, "supervisor_alive", lambda folder: True), \
                mock.patch.object(agent_loop, "SUPERVISOR_HANDOVER_S", 0.0):
            self.assertTrue(agent_loop.ensure_supervisor(self.wt))
        self.assertEqual(stop.read_text(), "newer")

    def test_supervise_status_replaces_an_older_supervisor_too(self):
        agent_loop.write_atomically(self.folder / agent_loop.SUPERVISOR_FILE, {"pid": 1, "version": "2.0.0"})
        asked = []
        with mock.patch.object(agent_loop, "supervisor_alive", lambda folder: True), \
                mock.patch.object(agent_loop, "ensure_supervisor", lambda worktree, restart=False: asked.append(1)):
            line = self.call(agent_loop.cmd_supervise, worktree=str(self.wt), stop=False, status=True,
                             test_wake=False)
        self.assertEqual((line["result"], asked), ("SUPERVISOR", [1]))


class MachineOverview(Repo):

    def test_flow_and_the_wake_show_cpu_share_and_check_health(self):
        self.wt = self.wt.resolve()
        prof = agent_loop.profile(self.wt)
        prof["main_checks"] = {"images": {"command": "check-images"}}
        folder = agent_loop.loop_dir(self.wt)
        for seconds, code in ((8, 0), (12, 0), (20, 0)):
            agent_loop.note_row(self.wt, agent_loop.CHECK_RUNS_FILE,
                                {"command": "make test", "seconds": seconds, "exit": code,
                                 "started_s": time.time(), "stdout": "/logs/test.stdout"})
        main = agent_loop.main_check_dir(self.wt, "images")
        for i, code in enumerate((0, 124), 1):
            agent_loop.write_atomic(main / "runs" / f"{i}.json",
                                    {"commit": "abc", "result": "fail" if code else "pass", "finished_s": i,
                                     "command": "check-images", "attempts": [
                                         {"seconds": 6 * i, "exit": code, "stderr": "/logs/images.stderr"}]})
        snapshot = [(1, 0, 1, "launchd"), (10, 1, 0, "python3"), (11, 10, 8, "/bin/sh"),
                    (12, 11, 150, "/tools/rustc"), (13, 1, 50, "rustc"),
                    (20, 1, 300, "/Applications/Simulator.app/Contents/MacOS/Simulator"),
                    (21, 20, 80, "/Applications/Simulator.app/Contents/Helper.app/Contents/MacOS/Helper"),
                    (30, 1, 30, "/Applications/Codex.app/Contents/MacOS/Codex")]
        stamp = time.time()
        with mock.patch.object(agent_loop, "live_loops", return_value=([{"pid": 10, "role": "steps"}], [])), \
                mock.patch.object(agent_loop, "start_due_checks"), \
                mock.patch.object(agent_loop.shutil, "disk_usage", return_value=mock.Mock(free=10**10)), \
                mock.patch.object(agent_loop, "profile", return_value=prof), \
                mock.patch.object(agent_loop, "cpu_processes", return_value=snapshot) as ps, \
                mock.patch.object(agent_loop, "memory_pressure", return_value="warning"), \
                mock.patch.object(agent_loop.os, "getloadavg", return_value=(19.5, 12, 6.5)), \
                mock.patch.object(agent_loop.os, "cpu_count", return_value=14), \
                mock.patch.object(agent_loop.time, "time", return_value=stamp):
            state = {"woke_at": stamp - 3600}
            agent_loop.write_atomically(folder / agent_loop.WATCH_FILE, state)
            _, wake = agent_loop.watch_wake(self.wt, prof, tick=lambda *_: ("CHECK_IN", ["test wake"]))
            cli = json.loads(self.printed(agent_loop.cmd_flow, worktree=str(self.wt), since=None))
        self.assertEqual(ps.call_count, 2)
        for key, value in cli.items():
            self.assertEqual(value, wake[key], key)
        machine = wake["machine"]
        self.assertEqual(machine["load"], {"1m": 19.5, "15m": 6.5})
        self.assertEqual(machine["cores"], 14)
        self.assertEqual(machine["memory_pressure"], "warning")
        self.assertEqual(machine["cpu_by_app"][:3], [
            {"app": "Simulator", "cpu_pct": 380, "orchestrate_cpu_pct": 0},
            {"app": "rustc", "cpu_pct": 200, "orchestrate_cpu_pct": 150},
            {"app": "Codex", "cpu_pct": 30, "orchestrate_cpu_pct": 0},
        ])
        self.assertEqual(machine["checks"]["commands"]["make test"],
                         {"seconds": 20, "usual_seconds": 10, "exit": 0, "timed_out": False,
                          "slow": True, "stdout": "/logs/test.stdout"})
        self.assertEqual(machine["checks"]["main_branch"]["images"],
                         {"command": "check-images", "seconds": 12, "usual_seconds": 6, "exit": 124,
                          "timed_out": True, "slow": True, "stderr": "/logs/images.stderr"})

    def test_the_overview_omits_machine_readings_that_fail(self):
        folder = agent_loop.loop_dir(self.wt)
        with mock.patch.object(agent_loop.subprocess, "run", side_effect=PermissionError), \
                mock.patch.object(agent_loop, "loop_dir", return_value=folder), \
                mock.patch.object(agent_loop.os, "getloadavg", side_effect=OSError), \
                mock.patch.object(agent_loop.os, "cpu_count", return_value=None):
            machine = agent_loop.machine_summary(self.wt, {}, {"loops": []})
        self.assertEqual(machine, {"checks": {"commands": {}, "main_branch": {}}})


if __name__ == "__main__":
    import unittest
    unittest.main()
