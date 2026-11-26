"""Tests for agent-relay, against fake host binaries, so they run without any of the real CLIs.

    python3 -m unittest discover tests/agent-relay
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "agent-relay" / "scripts"
RELAY = SCRIPTS / "relay.py"
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from relay import antigravity, claude, codex, hosts, models  # noqa: E402

CLAUDE_STREAM = "\n".join(json.dumps(e) for e in [
    {"type": "system", "subtype": "init", "session_id": "s1", "model": "claude-opus-5-5"},
    {"type": "assistant", "session_id": "s1", "message": {"id": "m1", "content": [{"type": "text", "text": "hi"}],
                                                          "usage": {"input_tokens": 10, "cache_read_input_tokens": 5,
                                                                    "output_tokens": 2}}},
    {"type": "rate_limit_event", "session_id": "s1", "rate_limit_info": {"status": "allowed"}},
    {"type": "result", "session_id": "s1", "result": "pong", "is_error": False, "total_cost_usd": 0.01,
     "usage": {"input_tokens": 10, "cache_creation_input_tokens": 3, "cache_read_input_tokens": 5,
               "output_tokens": 2}, "modelUsage": {"claude-opus-5-5": {"contextWindow": 1000000}}},
])

CODEX_STREAM = "\n".join(json.dumps(e) for e in [
    {"type": "thread.started", "thread_id": "t1"},
    {"type": "item.completed", "item": {"type": "agent_message", "text": "pong"}},
    {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 7}},
])


def fake_cli(folder: Path, name: str, body: str) -> str:
    """A fake host CLI: a Python script that records its argv and does `body`."""
    path = folder / name
    path.write_text("#!/usr/bin/env python3\nimport json, os, sys, time, signal\n"
                    f"open({str(folder / (name + '.argv'))!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
                    + textwrap.dedent(body))
    path.chmod(0o755)
    return str(path)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.env = {"AGENT_RELAY_STATE_DIR": str(self.dir / "state"), "AGENT_RELAY_QUOTA_DIR": str(self.dir / "q")}
        self.old = {k: os.environ.get(k) for k in [*self.env, "AGENT_RELAY_CLAUDE", "AGENT_RELAY_CODEX",
                                                     "AGENT_RELAY_AGY"]}
        os.environ.update(self.env)

    def tearDown(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def argv(self, name: str) -> list:
        return json.loads((self.dir / f"{name}.argv").read_text())

    def cli(self, *args, timeout=60) -> tuple[int, dict]:
        out = subprocess.run([sys.executable, str(RELAY), *args], capture_output=True, text=True, timeout=timeout,
                             env={**os.environ}, cwd=self.dir)
        return out.returncode, json.loads(out.stdout) if out.stdout.strip().startswith(("{", "[")) else out.stdout


class Parsing(unittest.TestCase):
    def test_claude_stream(self):
        got = claude.parse(CLAUDE_STREAM)
        self.assertEqual((got["session"], got["text"], got["model"], got["error"]), ("s1", "pong", "claude-opus-5-5",
                                                                                     False))
        self.assertEqual(got["usage"], {"input": 13, "cached": 5, "output": 2}, "cache writes count as input")
        self.assertEqual((got["window"], got["cost_usd"]), (1000000, 0.01))

    def test_claude_turn_stopped_before_its_result_still_counts_tokens(self):
        cut = "\n".join(CLAUDE_STREAM.splitlines()[:2])
        self.assertEqual(claude.parse(cut)["usage"], {"input": 10, "cached": 5, "output": 2, "incomplete": True})

    def test_claude_rejected_rate_limit_is_limited(self):
        line = json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected"}})
        self.assertTrue(claude.parse(line)["limited"])

    def test_codex_stream(self):
        got = codex.parse(CODEX_STREAM)
        self.assertEqual((got["session"], got["text"]), ("t1", "pong"))
        self.assertEqual(got["usage"], {"input": 60, "cached": 40, "output": 7}, "codex counts cached inside input")

    def test_codex_usage_limit_is_limited(self):
        line = json.dumps({"type": "turn.failed", "error": {"message": "You've hit your usage limit."}})
        self.assertTrue(codex.parse(line)["limited"])

    def test_antigravity_fixture(self):
        got = antigravity.parse((FIXTURES / "agy_turn.jsonl").read_text())
        self.assertEqual((got["session"], got["text"].strip(), got["model"]),
                         ("9e9d32cf-4cd1-48d8-af05-beacdd982adc", "PONG", "gemini-4-neon"))
        self.assertEqual(got["usage"]["output"], 49, "thinking counts as output")

    def test_antigravity_denials_from_stderr(self):
        err = "starting\nTool call run_command soft-denied: needs approval\nok"
        self.assertEqual(len(antigravity.denials(err)), 1)


class CommandLines(Base):
    def test_codex_headless_threads_are_not_labelled_as_the_apps(self):
        args, _ = codex.Codex().command(hosts.Request(prompt="p", cwd="/w", model="m", effort="low",
                                                      mode="read-only"))
        self.assertNotIn("--thread-source", args, "that label puts every headless run in the app's Recents")
        self.assertEqual(args[1], "exec")
        self.assertIn("--json", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")

    def test_codex_resume(self):
        args, _ = codex.Codex().command(hosts.Request(prompt="p", cwd="/w", session="t1"))
        self.assertEqual(args[args.index("resume") + 1], "t1")

    def test_claude_new_session_takes_messages_and_records_its_inbox(self):
        args, env = claude.Claude().command(hosts.Request(prompt="p", cwd="/w", mode="auto"), new_id="abc")
        self.assertEqual(args[args.index("--session-id") + 1], "abc")
        settings = json.loads(args[args.index("--settings") + 1])
        self.assertEqual(settings["crossSessionInbound"], "accept")
        hook = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertIn("CLAUDE_CODE_MESSAGING_SOCKET", hook)
        self.assertIn("abc.sock", hook)
        self.assertEqual(args[args.index("--permission-mode") + 1], "auto")

    def test_claude_env_drops_api_keys_and_parent_session(self):
        os.environ.update(ANTHROPIC_API_KEY="k", CLAUDECODE="1", CLAUDE_CONFIG_DIR="/c")
        try:
            env = claude.clean_env()
        finally:
            for k in ("ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CONFIG_DIR"):
                os.environ.pop(k, None)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], "/c")

    def test_antigravity_modes(self):
        agy = antigravity.Antigravity()
        args, env = agy.command(hosts.Request(prompt="p", mode="auto"))
        self.assertEqual(json.loads(args[args.index("--settings") + 1]), {"agentMode": "auto"},
                         "--mode auto is refused in print mode (antigravity-cli#1787)")
        self.assertNotIn("--mode", args)
        self.assertNotIn("--settings", agy.command(hosts.Request(prompt="p", mode="turbo"))[0])
        self.assertIn("--dangerously-skip-permissions",
                      agy.command(hosts.Request(prompt="p", mode="skip-permissions"))[0])
        self.assertEqual(env["AGY_CLI_DISABLE_AUTO_UPDATE"], "true")


class Runs(Base):
    def test_claude_run_through_a_fake_cli(self):
        os.environ["AGENT_RELAY_CLAUDE"] = fake_cli(self.dir, "claude", f"print({CLAUDE_STREAM!r})\n")
        r = claude.Claude().run(hosts.Request(prompt="p", cwd=str(self.dir), effort="low"))
        self.assertEqual((r.status, r.text, r.usage["output"]), ("done", "pong", 2))
        self.assertFalse(list((self.dir / "state" / "runs" / "claude").glob("*.json")), "the run record is removed")

    def test_cli_prints_one_json_result(self):
        os.environ["AGENT_RELAY_CODEX"] = fake_cli(self.dir, "codex", f"print({CODEX_STREAM!r})\n")
        code, out = self.cli("run", "--host", "codex", "--cwd", str(self.dir), "hello")
        self.assertEqual(code, 0)
        self.assertEqual((out["status"], out["session"], out["text"]), ("done", "t1", "pong"))
        self.assertNotIn("stdout", out)

    def test_failed_turn(self):
        os.environ["AGENT_RELAY_CODEX"] = fake_cli(self.dir, "codex", "sys.stderr.write('boom'); sys.exit(3)\n")
        r = codex.Codex().run(hosts.Request(prompt="p", cwd=str(self.dir)))
        self.assertEqual((r.status, r.exit_code), ("failed", 3))
        self.assertIn("boom", r.text)

    def test_stop_from_another_process_reports_interrupted(self):
        # Claude exits 0 on SIGINT, so the result must learn from the run record that it was stopped.
        body = ("print(json.dumps({'type':'system','subtype':'init','session_id':sys.argv[sys.argv.index('--session-id')+1]}), flush=True)\n"
                "signal.signal(signal.SIGINT, lambda *a: sys.exit(0))\n"
                "time.sleep(60)\n")
        os.environ["AGENT_RELAY_CLAUDE"] = fake_cli(self.dir, "claude", body)
        got = {}
        t = threading.Thread(target=lambda: got.update(r=claude.Claude().run(hosts.Request(prompt="p",
                                                                                        cwd=str(self.dir)))))
        t.start()
        runs = self.dir / "state" / "runs" / "claude"
        deadline = time.time() + 20
        while time.time() < deadline and not list(runs.glob("*.json")):
            time.sleep(0.1)
        session = list(runs.glob("*.json"))[0].stem
        code, out = self.cli("stop", "--host", "claude", "--session", session)
        t.join(30)
        self.assertEqual((code, out["status"]), (0, "done"))
        self.assertEqual(got["r"].status, "interrupted")

    def test_timeout(self):
        os.environ["AGENT_RELAY_AGY"] = fake_cli(self.dir, "agy", "time.sleep(60)\n")
        r = antigravity.Antigravity().run(hosts.Request(prompt="p", cwd=str(self.dir), timeout_s=1))
        self.assertEqual(r.status, "timeout")

    def test_antigravity_refusal_is_reported(self):
        body = (f"sys.stdout.write(open({str(FIXTURES / 'agy_turn.jsonl')!r}).read())\n"
                "sys.stderr.write('run_command soft-denied by policy\\n')\n")
        os.environ["AGENT_RELAY_AGY"] = fake_cli(self.dir, "agy", body)
        r = antigravity.Antigravity().run(hosts.Request(prompt="p", cwd=str(self.dir)))
        self.assertEqual(r.status, "refused")
        self.assertTrue(r.warnings)

    def test_stop_with_no_running_turn(self):
        code, out = self.cli("stop", "--host", "codex", "--session", "nope")
        self.assertEqual((code, out["status"]), (1, "failed"))


class Sandboxes(Base):
    def test_an_unwritable_state_folder_falls_back_to_the_temporary_directory(self):
        locked = self.dir / "locked"
        locked.mkdir()
        locked.chmod(0o500)
        os.environ["AGENT_RELAY_STATE_DIR"] = str(locked / "state")
        try:
            got = hosts.state_dir()
        finally:
            locked.chmod(0o700)
        self.assertEqual(got, Path(tempfile.gettempdir()) / f"agent-relay-{os.getuid()}")

    def test_a_failed_run_inside_codexs_sandbox_says_why(self):
        os.environ["AGENT_RELAY_CLAUDE"] = fake_cli(self.dir, "claude", "print('Not logged in'); sys.exit(1)\n")
        os.environ["CODEX_SANDBOX"] = "seatbelt"
        self.addCleanup(os.environ.pop, "CODEX_SANDBOX", None)
        code, out = self.cli("run", "--host", "claude", "--cwd", str(self.dir), "hello")
        self.assertEqual((code, out["status"]), (1, "failed"))
        self.assertIn("inside Codex's sandbox", out["warnings"][-1])

    def test_open_gives_claude_desktop_a_terminal(self):
        script = "print('in' if sys.stdin.isatty() and sys.stdout.isatty() else 'redirected')\n"
        os.environ["AGENT_RELAY_CLAUDE"] = fake_cli(self.dir, "claude", script)
        with unittest.mock.patch.object(claude.Claude, "live_session", lambda self, s: None):
            r = claude.Claude().open("s1", cwd=str(self.dir))
        self.assertEqual((r.status, r.text), ("done", "in"))


class Messaging(Base):
    def test_send_to_a_claude_session_the_relay_started(self):
        sock_path = str(self.dir / "in.sock")
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(sock_path)
        server.listen(1)
        got = []

        def accept():
            conn, _ = server.accept()
            with conn:
                data = b""
                while chunk := conn.recv(4096):
                    data += chunk
            got.extend(json.loads(line) for line in data.decode().splitlines())
        t = threading.Thread(target=accept)
        t.start()
        claude.inbox_dir().joinpath("s9.sock").write_text(sock_path)
        r = claude.Claude().send("s9", "hello")
        t.join(10)
        server.close()
        self.assertEqual(r.status, "done")
        self.assertEqual(got, [{"type": "user", "message": {"role": "user", "content": "hello"}}])

    def test_send_to_claude_without_a_socket(self):
        r = claude.Claude().send("unknown", "hello")
        self.assertEqual(r.status, "failed")
        self.assertIn("run --session", r.text)

    def test_codex_send_reads_the_resume_warning(self):
        body = "print('Queued message abc'); print('warning: failed to resume thread: no daemon', file=sys.stderr)\n"
        os.environ["AGENT_RELAY_CODEX"] = fake_cli(self.dir, "codex", body)
        r = codex.Codex().send("t1", "hi")
        self.assertEqual(r.status, "done")
        self.assertTrue(any("failed to resume" in w for w in r.warnings))
        self.assertEqual(self.argv("codex"), ["queue", "--thread", "t1", "--resume", "--message", "hi"])

    def test_antigravity_says_what_it_cant_do(self):
        os.environ["AGENT_RELAY_AGY"] = fake_cli(self.dir, "agy", "")
        for args in (["send", "--host", "agy", "--session", "c1", "hi"], ["open", "--host", "agy", "--session", "c1"],
                     ["run", "--host", "agy", "--app", "p"]):
            code, out = self.cli(*args)
            self.assertEqual((code, out["status"]), (2, "unsupported"), args)
            self.assertTrue(out["text"])


class Catalogue(Base):
    def test_shipped_catalogue_is_well_formed(self):
        cat = models.catalogue()
        self.assertTrue(cat["checked"])
        for m in cat["models"]:
            self.assertIn(m["host"], hosts.HOSTS)
            self.assertTrue(m["id"] and m.get("for"))

    def test_price_change_comes_into_force(self):
        m = {"price": {"input": 2.0}, "price_changes": [{"from": "2026-12-01", "input": 4.0}]}
        self.assertEqual(models.price_now(m, "2026-11-30")["input"], 2.0)
        self.assertEqual(models.price_now(m, "2026-12-01")["input"], 4.0)


class NeverRedeems(unittest.TestCase):
    def test_no_code_redeems_a_banked_reset(self):
        source = "".join(f.read_text() for f in SCRIPTS.rglob("*.py"))
        self.assertNotIn("rateLimitResetCredit/consume", source, "redeeming a banked reset is the user's decision")


class Help(unittest.TestCase):
    def test_every_command_has_help(self):
        for command in ("run", "stop", "send", "open", "status", "quota", "models", "check"):
            out = subprocess.run([sys.executable, str(RELAY), command, "--help"], capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, command)
            self.assertNotIn("orchestrate", out.stdout.lower(), "the relay stands on its own")


if __name__ == "__main__":
    unittest.main()
