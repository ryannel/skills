"""Checks how the script stops, pauses, resumes and clears the queue of a thread the Codex app runs, and the `thread`
command a lead uses for them.

From app 26.1117 the app runs its threads in its own app-server, which only the app can reach, and the IPC router
older apps used no longer listens. The script reaches the app-server that runs a thread only when the app runs on
the shared daemon, through its control socket: a websocket at ws://localhost/rpc over a unix socket. The fake here
is such a server, in a thread of the test process, keeping goal status in a goal store and queued messages in
memory. When no server can stop a turn, the command says so and asks the user to press Stop in the app."""

import contextlib
import io
import json
import os
import socket
import sqlite3
import struct
import sys
import tempfile
import threading
import base64
import hashlib
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Clean, Repo, agent_loop, release  # noqa: E402

REAL_GOAL_ACTIVATE = agent_loop.codex_goal_activate  # Repo replaces it with a recorder; these tests use the real one
T1 = "01a20000-0000-7000-8000-000000000001"
T2 = "01a20000-0000-7000-8000-000000000002"


class FakeSharedServer:
    """The shared app-server daemon, as far as the script uses it: it holds the threads in `loaded`, keeps each
    thread's goal status in <codex home>/goals_1.sqlite and its queued messages in `queued`, and records every
    request in `requests`."""

    def __init__(self, home: Path, loaded=(T1,)):
        self.home, self.loaded, self.requests, self.queued = home, list(loaded), [], {}
        self.folder = Path(tempfile.mkdtemp(prefix="oc-", dir="/tmp"))  # a unix socket path must be short
        self.path = self.folder / "s.sock"
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(str(self.path))
        self.sock.listen(8)
        threading.Thread(target=self.serve, daemon=True).start()

    def close(self):
        self.sock.close()
        for p in self.folder.iterdir():
            p.unlink()
        self.folder.rmdir()

    def serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self.client, args=(conn,), daemon=True).start()

    def client(self, conn):
        with conn:
            self.talk(conn)

    def talk(self, conn):
        try:
            data = b""
            while b"\r\n\r\n" not in data:
                data += conn.recv(4096)
            head, data = data.split(b"\r\n\r\n", 1)
            key = next(line.split(b":", 1)[1].strip() for line in head.split(b"\r\n")
                       if line.lower().startswith(b"sec-websocket-key"))
            accept = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                         b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n")
            while True:
                while len(data) < 2 or len(data) < self.frame_size(data):
                    chunk = conn.recv(65536)
                    if not chunk:
                        return
                    data += chunk
                size, at = self.frame_size(data), self.payload_at(data)
                mask, body, data = data[at - 4:at], data[at:size], data[size:]
                message = json.loads(bytes(b ^ mask[i % 4] for i, b in enumerate(body)))
                if "id" in message:
                    reply = self.answer(message)
                    out = json.dumps({"id": message["id"], **reply}).encode()
                    n = len(out)
                    conn.sendall(bytes([0x81]) + (bytes([n]) if n < 126 else bytes([126]) + struct.pack(">H", n))
                                 + out)
        except OSError:
            return

    @staticmethod
    def payload_at(data):
        n = data[1] & 0x7F
        return (2 if n < 126 else 4 if n == 126 else 10) + 4

    def frame_size(self, data):
        if len(data) < 2:
            return 2
        n, at = data[1] & 0x7F, self.payload_at(data)
        if n == 126:
            if len(data) < 4:
                return 4
            n = struct.unpack(">H", data[2:4])[0]
        return at + n

    def answer(self, m):
        method, params = m["method"], m.get("params") or {}
        self.requests.append((method, params))
        if method == "initialize":
            return {"result": {"userAgent": "fake"}}
        if method == "thread/loaded/list":
            return {"result": {"data": self.loaded, "nextCursor": None}}
        thread = params.get("threadId")
        if thread not in self.loaded:
            return {"error": {"code": -32600, "message": f"thread not found: {thread}"}}
        if method == "turn/interrupt":
            write(self.home, thread, {"type": "event_msg", "payload": {"type": "turn_aborted",
                                                                       "turn_id": params["turnId"]}})
            return {"result": {}}
        if method == "thread/goal/set":
            set_goal(self.home, thread, params["status"])
            return {"result": {"goal": {"status": params["status"]}}}
        if method == "thread/queue/list":
            return {"result": {"data": [{"id": i} for i in self.queued.get(thread, [])], "nextCursor": None}}
        if method == "thread/queue/delete":
            items = self.queued.get(thread, [])
            found = params["queuedSubmissionId"] in items
            if found:
                items.remove(params["queuedSubmissionId"])
            return {"result": {"deleted": found}}
        return {"error": {"code": -32601, "message": f"unknown method {method}"}}


def write(home: Path, thread: str, *events):
    path = home / "sessions/2026/11/23" / f"rollout-2026-11-23T10-00-00-{thread}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as handle:
        for e in events:
            handle.write(json.dumps(e) + "\n")


def started(home: Path, thread: str, turn: str):
    """A task_started as app 26.1117 writes it: the turn id is under `turn_attribution`."""
    write(home, thread, {"type": "event_msg", "payload": {"type": "task_started", "turn_attribution": {
        "turn_id": turn, "turn_trigger": "queue"}}})


def set_goal(home: Path, thread: str, status: str):
    conn = sqlite3.connect(home / "goals_1.sqlite")
    with conn:
        conn.execute("create table if not exists thread_goals (thread_id text primary key, status text)")
        conn.execute("insert or replace into thread_goals values (?, ?)", (thread, status))
    conn.close()


def refused_socket(folder: Path) -> Path:
    """A socket file nothing listens on, as the IPC router of app 26.1117 leaves it: connecting is refused."""
    path = folder / "ipc" / "ipc.sock"
    path.parent.mkdir(parents=True, exist_ok=True)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(str(path))
    s.close()
    return path


class SharedServerPath(Clean):
    """The mechanism: the shared app-server, then the old IPC router, and what is said when neither can act."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp(prefix="oc-home-", dir="/tmp"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.home, True))
        for name, value in dict(CODEX_HOME=self.home, CODEX_CONTROL_SOCK=self.home / "none.sock",
                                codex_goal_activate=REAL_GOAL_ACTIVATE).items():
            p = mock.patch.object(agent_loop, name, value)
            p.start()
            self.addCleanup(p.stop)

    def server(self, **kw):
        fake = FakeSharedServer(self.home, **kw)
        self.addCleanup(fake.close)
        p = mock.patch.object(agent_loop, "CODEX_CONTROL_SOCK", fake.path)
        p.start()
        self.addCleanup(p.stop)
        return fake

    def test_the_turn_id_is_read_from_either_rollout_format(self):
        self.assertEqual(agent_loop.turn_id_of({"turn_id": "a"}), "a")
        self.assertEqual(agent_loop.turn_id_of({"turn_attribution": {"turn_id": "b"}}), "b")
        started(self.home, T1, "turn-1")
        self.assertEqual(agent_loop.codex_running_turn(T1), "turn-1")
        write(self.home, T1, {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": "turn-1"}})
        self.assertIsNone(agent_loop.codex_running_turn(T1))
        self.assertIsNone(agent_loop.codex_running_turn(T2), "a thread with no rollout has no turn running")

    def test_a_stop_through_the_shared_server_pauses_the_goal_and_interrupts_the_running_turn(self):
        fake = self.server()
        set_goal(self.home, T1, "active")
        started(self.home, T1, "turn-1")
        self.assertTrue(agent_loop.codex_interrupt(T1))
        methods = [m for m, _ in fake.requests if m not in ("initialize", "thread/loaded/list")]
        self.assertEqual(methods, ["thread/goal/set", "turn/interrupt"], "paused first, so no goal turn follows")
        self.assertEqual(fake.requests[-1][1], {"threadId": T1, "turnId": "turn-1"})
        self.assertEqual(agent_loop.goal_status(T1), "paused")
        self.assertIsNone(agent_loop.codex_running_turn(T1))

    def test_a_thread_the_shared_server_doesnt_hold_isnt_stopped_there(self):
        fake = self.server(loaded=[T2])
        srv, why = agent_loop.codex_control(T1)
        self.assertIsNone(srv)
        self.assertIn("doesn't hold this thread", why)
        self.assertNotIn("turn/interrupt", [m for m, _ in fake.requests])

    def test_a_refused_ipc_socket_is_reported_not_swallowed(self):
        refused_socket(self.home)
        started(self.home, T1, "turn-1")
        self.assertFalse(agent_loop.codex_interrupt(T1))
        why = agent_loop.CODEX_WHY[T1]
        self.assertIn("no shared app-server is running", why)
        self.assertIn("ipc.sock", why)
        self.assertIn("ConnectionRefusedError", why)
        self.assertIn("refused the connection (ConnectionRefusedError)", agent_loop.codex_ipc_why())

    def test_queued_messages_are_deleted_through_the_server_that_runs_the_thread(self):
        fake = self.server()
        fake.queued[T1] = ["q1", "q2"]
        self.assertEqual(agent_loop.codex_clear_queue(T1), (2, ""))
        self.assertTrue(agent_loop.codex_unqueue(T1))
        self.assertEqual(fake.queued[T1], [])

    def test_a_goal_change_on_a_thread_the_shared_server_runs_goes_to_that_server(self):
        fake = self.server()
        self.assertTrue(agent_loop.codex_goal_activate(T1, "paused"))
        self.assertEqual(agent_loop.goal_status(T1), "paused")
        self.assertIn(("thread/goal/set", {"threadId": T1, "status": "paused"}), fake.requests)

    def test_a_failed_goal_change_says_why(self):
        def broken():
            raise OSError("no app-server")
        with mock.patch.object(agent_loop, "CodexAppServer", broken):
            self.assertFalse(agent_loop.codex_goal_activate(T1, "paused"))
        self.assertIn("the goal couldn't be set paused: OSError: no app-server", agent_loop.CODEX_WHY[T1])

    def test_visible_codex_needs_the_app_running_not_its_old_ipc_router(self):
        with mock.patch.dict(os.environ, {"ORCHESTRATE_VISIBLE": "1"}), \
                mock.patch.object(agent_loop.sys, "platform", "darwin"), \
                mock.patch.object(agent_loop, "CODEX_APP_CLI", sys.executable):
            with mock.patch.object(agent_loop, "codex_app_running", lambda: True):
                self.assertIsNone(agent_loop.visible_unavailable("codex"))
            with mock.patch.object(agent_loop, "codex_app_running", lambda: False):
                self.assertIn("isn't running", agent_loop.visible_unavailable("codex"))

    def test_a_pause_whose_turn_the_app_wont_stop_asks_the_user_to_press_stop(self):
        agent_loop.SESSION_PATH["turn_not_stopped"] = "the Codex app didn't take the stop for thread " + T1
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            agent_loop.emit("PAUSED", module="WATER", milestone="M1", thread=T1)
        line = json.loads(out.getvalue().splitlines()[-1])
        self.assertEqual(line["next"]["decides"], "human")
        self.assertIn(f"codex://threads/{T1}", line["next"]["ask"])
        self.assertIn("click the Stop button", line["next"]["ask"])
        self.assertEqual(line["next"]["argv"][2:6], ["thread", "status", "--thread", T1])


class ThreadCommand(Repo):
    """`thread stop|pause|resume|unqueue|status` on a thread a run started."""

    def setUp(self):
        super().setUp()
        for name, value in dict(codex_goal_activate=REAL_GOAL_ACTIVATE,
                                CODEX_CONTROL_SOCK=self.home / "none.sock").items():
            p = mock.patch.object(agent_loop, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.home.mkdir(parents=True, exist_ok=True)
        agent_loop.note_thread(self.wt, "codex", T1, "build", "case · WATER · M1 build")
        state = self.wt / ".git/orchestrate/WATER.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"module": "WATER", "milestone": "M1", "thread": T1, "host": "codex",
                                     "path": "visible"}))
        set_goal(self.home, T1, "active")
        started(self.home, T1, "turn-1")

    def thread(self, action, **kw):
        return self.call(agent_loop.cmd_thread, action=action, worktree=str(self.wt), **kw)

    def server(self):
        fake = FakeSharedServer(self.home)
        self.addCleanup(fake.close)
        p = mock.patch.object(agent_loop, "CODEX_CONTROL_SOCK", fake.path)
        p.start()
        self.addCleanup(p.stop)
        return fake

    def test_stop_ends_the_turn_when_the_shared_server_runs_the_thread(self):
        self.server()
        result = self.thread("stop", module="WATER")
        self.assertEqual((result["result"], result["thread"], result["goal"]), ("STOPPED", T1, "paused"))
        self.assertIsNone(agent_loop.codex_running_turn(T1))

    def test_stop_the_app_alone_can_do_is_NOT_DONE_and_asks_the_user_what_to_click(self):
        home = self.home

        class ShortLived:  # a short-lived app-server can still pause the goal, which lives in a shared file
            def call(s, method, params, timeout=60):
                set_goal(home, params["threadId"], params["status"])
                return {}

            def close(s):
                pass
        with mock.patch.object(agent_loop, "codex_ipc_interrupt", lambda t: "the app's IPC router refused the stop "
                               "(ConnectionRefusedError: [Errno 61] Connection refused)"), \
                mock.patch.object(agent_loop, "CodexAppServer", ShortLived):
            result = self.thread("stop", module="WATER")
        self.assertEqual(result["result"], "NOT_DONE")
        self.assertIn("ConnectionRefusedError", result["reason"])
        self.assertIn("only the app can reach", result["reason"])
        self.assertEqual((result["goal"], result["turn_running"]), ("paused", "turn-1"))
        self.assertIn("no goal turn after this one", result["note"])
        nxt = result["next"]
        self.assertEqual(nxt["decides"], "human")
        self.assertIn('"case · WATER · M1 build"', nxt["ask"])
        self.assertIn(f"codex://threads/{T1}", nxt["ask"])
        self.assertEqual(nxt["argv"][2:4], ["thread", "status"])

    def test_pause_resume_and_unqueue_work_without_the_shared_server(self):
        calls = []

        class ShortLived:  # the short-lived app-server the script starts; both stores are shared files
            def __init__(s):
                pass

            def call(s, method, params, timeout=60):
                calls.append(method)
                if method == "thread/goal/set":
                    set_goal(self.home, params["threadId"], params["status"])
                    return {}
                if method == "thread/queue/list":
                    return {"data": [{"id": "q1"}] if "q1" not in calls else []}
                if method == "thread/queue/delete":
                    calls.append(params["queuedSubmissionId"])
                    return {"deleted": True}

            def close(s):
                pass
        queued, links = [], []
        with mock.patch.object(agent_loop, "CodexAppServer", ShortLived), \
                mock.patch.object(agent_loop, "codex_queue", lambda t, text: queued.append(text)), \
                mock.patch.object(agent_loop, "open_link", lambda url: links.append(url) or True):
            paused = self.thread("pause", module="WATER")
            unqueued = self.thread("unqueue", thread=T1)
            resumed = self.thread("resume", module="WATER")
        self.assertEqual((paused["result"], paused["goal"], paused["turn_running"]), ("GOAL_PAUSED", "paused", "turn-1"))
        self.assertIn("goes on until it ends", paused["note"])
        self.assertEqual((unqueued["result"], unqueued["removed"]), ("UNQUEUED", 1))
        self.assertEqual((resumed["result"], resumed["goal"]), ("GOAL_RESUMED", "active"))
        self.assertEqual((queued, links), ([agent_loop.CONTINUE_GOAL], [f"codex://threads/wake/{T1}"]))

    def test_status_says_whether_the_script_can_stop_the_thread(self):
        result = self.thread("status", module="WATER")
        self.assertEqual((result["result"], result["goal"], result["turn_running"], result["can_stop"]),
                         ("THREAD", "active", "turn-1", False))
        self.server()
        self.assertTrue(self.thread("status", module="WATER")["can_stop"])

    def test_a_thread_no_run_started_is_left_alone(self):
        with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
            agent_loop.cmd_thread(agent_loop.build_parser().parse_args(
                ["thread", "stop", "--thread", T2, "--worktree", str(self.wt)]))
        release()
        self.assertIn("isn't a thread a run in this repository started", str(stop.exception))
