"""The delivery history: reading Claude and Codex session files into small records, tagging them from the script's
ledger, and drawing the dashboard from them."""

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Repo, agent_loop  # noqa: E402

import delivery_history as h  # noqa: E402  (support puts the scripts folder on the path)


def jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


THREAD = "019a0000-0000-7000-8000-000000000001"


def codex_rollout(cwd: str) -> list[dict]:
    """One Codex turn: two model responses (one recorded twice), a tool call, a compaction and a limit reading."""
    ev = lambda ts, typ, payload: {"timestamp": ts, "type": typ, "payload": payload}
    usage = lambda i, c, o: {"input_tokens": i, "cached_input_tokens": c, "output_tokens": o,
                             "reasoning_output_tokens": 10}
    return [
        ev("2026-11-10T10:00:00Z", "session_meta", {"id": THREAD, "cwd": cwd, "cli_version": "0.1", "source": "exec"}),
        ev("2026-11-10T10:00:01Z", "event_msg", {"type": "task_started", "turn_id": "turn-1",
                                                 "model_context_window": 200000}),
        ev("2026-11-10T10:00:01Z", "turn_context", {"turn_id": "turn-1", "model": "gpt-test", "effort": "high"}),
        ev("2026-11-10T10:00:05Z", "token_usage_record", {"turn_id": "turn-1", "thread_id": THREAD,
                                                          "response_id": "r1", "usage": usage(1000, 600, 50)}),
        ev("2026-11-10T10:00:05Z", "token_usage_record", {"turn_id": "turn-1", "thread_id": THREAD,
                                                          "response_id": "r1", "usage": usage(1000, 600, 50)}),
        ev("2026-11-10T10:00:06Z", "response_item", {"type": "function_call", "name": "exec", "call_id": "c1"}),
        ev("2026-11-10T10:00:09Z", "response_item", {"type": "function_call_output", "call_id": "c1"}),
        ev("2026-11-10T10:00:10Z", "event_msg", {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": 1000}, "last_token_usage": {"total_tokens": 150000}},
            "rate_limits": {"primary": {"used_percent": 12.0, "window_minutes": 10080, "resets_at": 1794000000}}}),
        ev("2026-11-10T10:00:11Z", "compacted", {"replacement_history": []}),
        ev("2026-11-10T10:00:20Z", "token_usage_record", {"turn_id": "turn-1", "thread_id": THREAD,
                                                          "response_id": "r2", "usage": usage(2000, 1500, 70)}),
        ev("2026-11-10T10:00:21Z", "event_msg", {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": 3000}, "last_token_usage": {"total_tokens": 30000}}}),
        ev("2026-11-10T10:00:30Z", "event_msg", {"type": "task_complete", "turn_id": "turn-1", "duration_ms": 29000}),
    ]


class Readers(unittest.TestCase):

    def test_codex_turn_sums_each_response_once(self):
        with tempfile.TemporaryDirectory() as d:
            path = jsonl(Path(d) / f"rollout-2026-11-10T10-00-00-{THREAD}.jsonl", codex_rollout(d))
            got = h.read_codex(path)
        [turn] = got["turns"]
        self.assertEqual(turn["tokens"]["prompt"], 3000)  # r1 counted once, not twice
        self.assertEqual(turn["tokens"]["cache_read"], 2100)
        self.assertEqual(turn["tokens"]["output"], 120)
        self.assertEqual(turn["model"], "gpt-test")
        self.assertEqual(turn["duration_ms"], 29000)
        self.assertEqual(turn["tools"]["exec"][0], 1)
        self.assertEqual(turn.get("compactions"), 1)
        kinds = [e["kind"] for e in got["events"]]
        self.assertIn("compaction", kinds)
        self.assertIn("limit_changed", kinds)

    def test_claude_usage_repeated_per_content_block_counts_once(self):
        msg = {"id": "msg-1", "model": "claude-test", "usage": {
            "input_tokens": 10, "cache_read_input_tokens": 900, "cache_creation_input_tokens": 100,
            "output_tokens": 40}}
        rows = [
            {"type": "user", "timestamp": "2026-11-10T10:00:00Z", "sessionId": "s1", "cwd": "/r", "uuid": "u1",
             "message": {"content": "build it"}},
            {"type": "assistant", "timestamp": "2026-11-10T10:00:02Z", "message": {**msg, "content": [
                {"type": "text", "text": "ok"}]}},
            {"type": "assistant", "timestamp": "2026-11-10T10:00:03Z", "message": {**msg, "content": [
                {"type": "tool_use", "id": "t1", "name": "Bash"}]}},
            {"type": "user", "timestamp": "2026-11-10T10:00:08Z", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "t1", "is_error": True}]}},
            {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-11-10T10:00:09Z",
             "compactMetadata": {"preTokens": 150000, "postTokens": 20000, "trigger": "auto"}},
        ]
        with tempfile.TemporaryDirectory() as d:
            got = h.read_claude(jsonl(Path(d) / "s1.jsonl", rows))
        [turn] = got["turns"]
        self.assertEqual(turn["tokens"]["prompt"], 1010)
        self.assertEqual(turn["tokens"]["output"], 40)
        self.assertEqual(turn["tools"]["Bash"][0], 1)
        self.assertEqual(turn["tools"]["Bash"][2], 1)  # the tool's error
        self.assertEqual([e["kind"] for e in got["events"]], ["compaction"])

    def test_one_limit_reading_reported_by_many_threads_is_kept_once(self):
        events = {}
        for i, (at, pct) in enumerate([("a1", 10.0), ("a2", 10.0), ("a3", 11.0), ("a4", 11.0)]):
            e = {"kind": "limit_changed", "at": at, "limit": "primary", "used_percent": pct, "window_minutes": 1,
                 "resets_at": "r", "session": f"s{i}"}
            events[h.key_of("events", e)] = e
        h.thin_limits(events)
        self.assertEqual(sorted(e["at"] for e in events.values()), ["a1", "a3"])


class WorkPackages(unittest.TestCase):

    def test_an_item_failed_twice_is_a_repeated_finding(self):
        proj = {"CORE": {"doc": {"work_packages": [{"id": "WP1", "name": "n", "status": "done",
                                                  "items": [{"id": "WP1.1"}, {"id": "WP1.2"}]}]},
                         "record": {"work_packages": {"WP1": {
                             "authorised": {"at": "2026-11-10T09:00:00Z"},
                             "done": {"at": "2026-11-11T09:00:00Z"},
                             "reviews": [
                                 {"verdict": "fail", "at": "2026-11-10T12:00:00Z", "items": {"WP1.1": "fail",
                                                                                            "WP1.2": "pass"}},
                                 {"verdict": "fail", "at": "2026-11-10T15:00:00Z", "items": {"WP1.1": "fail"}},
                                 {"verdict": "pass", "at": "2026-11-11T09:00:00Z", "items": {"WP1.1": "pass"}}]}}}}}
        [row] = h.work_package_rows(proj)
        self.assertEqual(row["size"], 2)
        self.assertEqual(row["done"], "2026-11-11T09:00:00Z")
        self.assertEqual([r["findings"] for r in row["reviews"]],
                         [[{"name": "WP1.1"}], [{"name": "WP1.1", "repeat": True}], []])


class Dashboard(unittest.TestCase):

    def test_existing_history_survives_the_3_0_names_and_the_next_sweep(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            labels = {"module": "CORE", "milestone": "M3"}
            run = {"host": "codex", "session": "s1", "kind": "script", **labels}
            jsonl(folder / "sessions.jsonl", [run])
            jsonl(folder / "turns.jsonl", [{**run, "turn": "t1", "weighted": 13}])
            at = "2026-11-01T12:00:00Z"
            jsonl(folder / "events.jsonl", [{"kind": "review_failed", "at": at, **labels}])
            jsonl(folder / "milestones.jsonl", [{**labels, "name": "Renderer", "status": "done", "size": 1}])
            def check():
                summary = h.summary(folder)
                self.assertEqual(summary["costliest_work_packages"], [("CORE WP3", {"weighted": 13, "turns": 1})])
                self.assertEqual(summary["errors"], {"review_failed": 1})
                model = h.dashboard_model(folder)
                [work_package] = model["work_packages"]
                self.assertEqual((work_package["work_package"], work_package["name"]), ("WP3", "Renderer"))
                self.assertEqual(model["events"][0]["work_package"], "WP3")
                self.assertEqual(model["sessions"][0]["work_package"], "WP3")
                [turn] = model["turns"]["rows"]
                self.assertEqual(turn[model["turns"]["columns"].index("work_package")], "WP3")
            check()
            # The first sweep sees the same failed review in the migrated record. It must count just once.
            row = {"module": "CORE", "work_package": "WP3", "name": "Renderer", "status": "done", "size": 1,
                   "reviews": [{"verdict": "fail", "at": at, "findings": [{"name": "WP3.1"}]}]}
            h._write_work_packages(folder, [row])
            check()

    def test_page_embeds_the_records_and_cannot_be_closed_by_their_text(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            jsonl(folder / "sessions.jsonl", [{"host": "codex", "session": "s", "kind": "script",
                                               "title": "</script><script>alert(1)</script>"}])
            jsonl(folder / "turns.jsonl", [{"host": "codex", "session": "s", "turn": "t", "start": "2026-11-10T10:00:00Z",
                                            "duration_ms": 5, "tokens": {"prompt": 7}, "weighted": 7}])
            out = h.render(folder, meta={"project": "p"})
            html = out.read_text()
        self.assertNotIn("/*__DATA__*/null", html)
        self.assertEqual(html.count("</script>"), 2)  # the data block's and the page script's own
        blob = html.split('type="application/json">', 1)[1].split("</script>", 1)[0]
        model = json.loads(blob)
        self.assertEqual(model["turns"]["rows"][0][model["turns"]["columns"].index("tokens")][0], 7)


class Commands(Repo):
    """`history` reads a session the script ran from the host's own file, and tags it from the ledger."""

    def setUp(self):
        super().setUp()
        self.history_home = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.history_home, True))
        os.environ.pop("ORCHESTRATE_NO_HISTORY", None)
        for name, value in (("CODEX_HOME", self.history_home / "codex"), ("CLAUDE_HOME", self.history_home / "claude"),
                            ("HISTORY_ROOT", self.history_home / "history")):
            patch = mock.patch.object(h, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def run_cmd(self, func, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            func(argparse.Namespace(worktree=str(self.root), **kw))
        return out.getvalue()

    def test_history_tags_a_script_session_from_the_ledger(self):
        jsonl(self.history_home / "codex" / "sessions" / "2026" / "11" / "10" / f"rollout-2026-11-10T10-00-00-{THREAD}.jsonl",
              codex_rollout(str(self.root)))
        folder = agent_loop.loop_dir(self.root)
        jsonl(folder / "usage.jsonl", [{"at": "2026-11-10T10:00:31Z", "role": "build", "module": "core",
                                        "work_package": "WP1", "host": "codex", "model": "gpt-test", "session": THREAD,
                                        "exit": 124, "version": "9.9", "usage": {}}])
        with mock.patch.object(agent_loop.codex_quota, "read", side_effect=RuntimeError):
            self.run_cmd(agent_loop.cmd_history, json=False, full=False, budget=60)
        records = h.rows(h.project_dir(self.root))
        [turn] = records["turns"]
        self.assertEqual((turn["role"], turn["module"], turn["work_package"], turn["version"]),
                         ("build", "core", "WP1", "9.9"))
        self.assertEqual(records["sessions"][0]["kind"], "script")
        self.assertIn("turn_timed_out", [e["kind"] for e in records["events"]])

        written = json.loads(self.run_cmd(agent_loop.cmd_dashboard, out=None, open=False, json=False, no_sweep=True,
                                          budget=10))
        self.assertTrue(Path(written["written"]).is_file())

    def test_every_result_is_kept_beside_the_latest_one(self):
        folder = agent_loop.loop_dir(self.root)
        agent_loop.note_result(folder, {"result": "ERROR", "module": "core", "reason": "x" * 900, "quota": {}})
        [row] = [json.loads(line) for line in (folder / "results.jsonl").read_text().splitlines()]
        self.assertEqual((row["result"], row["module"], len(row["reason"])), ("ERROR", "core", 400))
        self.assertNotIn("quota", row)


if __name__ == "__main__":
    unittest.main()
