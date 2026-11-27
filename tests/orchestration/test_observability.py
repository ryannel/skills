"""The live project page reads the same fake repository as the command tests."""
import copy
import http.client
import json
import os
from pathlib import Path
import select
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Repo, agent_loop, done, put, work_package  # noqa: E402
import observability_model  # noqa: E402
from observability_server import Content  # noqa: E402

VISION = """# Vision and scope document for Test water

## Goal

> Water should flow through the channel.

## First release

Water reaches the drain.

## Milestones

- **First flow** (`milestone/first-flow`, was G7). Water reaches the drain.
- **Earlier work** (`milestone/earlier-work`, closed 2026-09-01). The channel exists.
- **Later flow** (`milestone/later-flow`, was G8). The water fills the pool.

## Still open

- **Pool depth** The user chooses.
"""


class Observability(Repo):
    def test_model_uses_project_plans_and_milestone_dependencies(self):
        plans = self.wt / "planning"
        self.git("mv", "docs/plans", "planning")
        put(plans / "VISION.md", VISION)
        put(plans / "ARCHITECTURE.md", """| # | Module | What it's for | Needs |
|---|---|---|---|
| 1 | WATER | Drain water | PIPE |
| 2 | PIPE | Carry water | |
""")
        put(plans / "WATER/DESIGN.md", "# Running water: the design\n")
        water = json.loads((plans / "WATER/DONE.json").read_text())
        water["work_packages"][-1].update(closes="first-flow", depends_on=["PIPE:WP1", "WP1"])
        put(plans / "WATER/DONE.json", json.dumps(water))
        put(plans / "PIPE/DONE.json", json.dumps(done(work_package("WP1", "not_started", ["open"]), module="PIPE")))
        self.commit_all()
        prof = {"plans": "planning", "evidence": ".orchestrate/evidence"}
        files = Content(self.wt.resolve(), (self.wt / ".git").resolve(), **prof)
        model, history, commits = observability_model.build(
            self.wt, prof, {"builders": {"running": 2, "limit": 4}}, {"meta": {"version": "1"}},
            module_table=agent_loop.module_table, module_stems=["WATER", "PIPE"], live_runs=[],
            content=files, recorded_done=agent_loop.recorded_done, supervisor_running=False,
            here={"run_state": True, "history": False, "evidence": False})
        self.assertEqual(model["project"]["name"], "Test water")
        self.assertEqual(model["project"]["goal"], "Water should flow through the channel.")
        self.assertEqual(model["project"]["v1_exit"], "Water reaches the drain.")
        self.assertEqual([m["id"] for m in model["modules"]], ["WATER", "PIPE"])
        self.assertEqual(model["modules"][0]["name"], "Running water")
        self.assertEqual(model["documents"]["WATER/design"]["path"], "planning/WATER/DESIGN.md")
        self.assertEqual(model["now"]["builders"], {"running": 2, "limit": 4})
        first, earlier, later = model["milestones"]
        self.assertEqual(first["closed_by"], "WATER:WP2")
        self.assertEqual(first["needs"], ["WATER:WP1", "WATER:WP2", "PIPE:WP1"])
        self.assertEqual(first["longest_chain"][-1], "WATER:WP2")
        self.assertEqual(earlier["closed_at"], "2026-09-01")
        self.assertTrue(earlier["historical"] and earlier["closed"])
        self.assertFalse(later["closed"])
        self.assertIsNone(later["closed_by"])
        self.assertEqual(later["needs"], [])
        self.assertIsNone(history["agents"])
        self.assertTrue(any("WATER:WP2" in row["definitions_changed"] for row in commits))

    def plan_mark(self, slug):
        put(self.wt / "docs/plans/VISION.md", VISION)
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# Water design\n")
        put(self.wt / "docs/plans/WATER/PLAN.md", "# Water plan\n")
        self.commit_all()
        self.git("push", "origin", "main")
        os.environ.update(FAKE_PLAN="milestone", FAKE_CLOSES=slug)
        return self.plan(kind="change", module="WATER", task="Mark the work package that closes the milestone",
                         one_step=True)

    def test_planner_can_add_mark_without_resetting_work(self):
        before = self.read_done()["work_packages"][-1]
        result = self.plan_mark("first-flow")
        self.assertEqual(result["result"], "PLANNED", result)
        after = self.read_done()["work_packages"][-1]
        self.assertEqual(after.pop("closes"), "first-flow")
        self.assertEqual(after, before)
        self.assertEqual(agent_loop.definitions(before), agent_loop.definitions(after | {"closes": "first-flow"}))

    def test_planner_cannot_name_an_unknown_milestone(self):
        result = self.plan_mark("unknown")
        self.assertEqual(result["result"], "INVALID", result)
        self.assertIn("names milestone/unknown", " ".join(result["problems"]))

    def test_builders_and_reviewers_cannot_set_the_mark(self):
        before = self.read_done()
        marked = copy.deepcopy(before)
        marked["work_packages"][0]["closes"] = "first-flow"
        for role in ("build", "review", "design"):
            with self.subTest(role=role):
                problems = agent_loop.delta_problems(before, marked, role, "WP1")
                self.assertTrue(any("closes" in p or "changed" in p for p in problems))
        put(self.wt / "docs/plans/VISION.md", VISION)
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(marked))
        result = self.adopt("docs/plans/VISION.md", "docs/plans/WATER/DONE.json")
        self.assertTrue(any("only a planner" in p for p in result["problems"]), result)

    def test_reviewer_summary_is_saved_in_the_record(self):
        commit = self.ready_for_review()
        os.environ["FAKE_REVIEW_SUMMARY"] = "The channel carried the full flow. The drain stayed clear."
        result = self.review(commit=commit)
        self.assertEqual(result["result"], "REVIEWED", result)
        reviews = self.read_record()["work_packages"]["WP1"]["reviews"]
        self.assertEqual(reviews[-1]["summary"], os.environ["FAKE_REVIEW_SUMMARY"])

    def test_serve_reads_only_allowed_content_and_streams_changes(self):
        plans = self.wt / "docs/plans"
        put(plans / "VISION.md", VISION)
        put(self.wt / "private.txt", "outside")
        (plans / "shortcut.txt").symlink_to(self.wt / "private.txt")
        evidence = self.wt / ".git/orchestrate/evidence"
        put(evidence / "WATER/proof.txt", "evidence")
        folder = agent_loop.delivery_history.project_dir(self.wt)
        put(folder / "checks.jsonl", '{"exit": 0}\n')
        state = self.wt / ".git/orchestrate"
        before = sorted(p.relative_to(state) for p in state.rglob("*"))
        command = [sys.executable, str(agent_loop.LOOP), "serve", "--port", "0", "--worktree", str(self.wt)]
        with (self.root / "serve.log").open("w+") as log, subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=log, text=True,
        ) as process:
            try:
                self.assertTrue(select.select([process.stdout], [], [], 30)[0], "serve did not print its URL")
                ready = json.loads(process.stdout.readline())
                if ready.get("result") != "SERVING":
                    log.seek(0)
                    self.fail(f"{ready}\n{log.read()}")
                self.assertEqual(ready["pid"], process.pid)
                url = ready["url"]
                self.assertTrue(url.startswith("http://127.0.0.1:"))
                with urlopen(url, timeout=10) as response:
                    self.assertIn(b'new EventSource("/events")', response.read())
                with urlopen(url + "model.json", timeout=10) as response:
                    model = json.load(response)
                self.assertEqual(model["modules"][0]["id"], "WATER")
                self.assertTrue(model["project"]["here"]["history"])
                with urlopen(url + "history.json", timeout=10) as response:
                    self.assertEqual(json.load(response)["machinery"]["check_outcomes"], {"passed": 1})
                with urlopen(url + "plan-commits.json", timeout=10) as response:
                    self.assertTrue(json.load(response))
                for path, text in (("docs/plans/VISION.md", VISION), (".orchestrate/evidence/WATER/proof.txt", "evidence")):
                    with urlopen(url + "content/" + path, timeout=10) as response:
                        self.assertEqual(response.read().decode(), text)
                for path in ("private.txt", "docs/plans/shortcut.txt", "docs/plans/%2e%2e/%2e%2e/private.txt",
                             ".orchestrate/evidence/%2e%2e/results.jsonl"):
                    with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                        urlopen(url + "content/" + path, timeout=10)
                    self.assertEqual(error.exception.code, 404)
                stream = http.client.HTTPConnection(url.split("/")[2], timeout=20)
                try:
                    stream.request("GET", "/events")
                    response = stream.getresponse()
                    self.assertEqual(response.readline().strip(), b": connected")
                    self.assertEqual(response.readline().strip(), b"")
                    put(plans / "VISION.md", VISION.replace("Water should flow", "Water should rush"))
                    self.assertEqual(response.readline().strip(), b"event: changed")
                    self.assertEqual(response.readline().strip(), b"data: {}")
                    self.assertEqual(response.readline().strip(), b"")
                    with urlopen(url + "model.json", timeout=10) as model_response:
                        self.assertIn("rush", json.load(model_response)["project"]["goal"])
                    put(folder / "checks.jsonl", '{"exit": 1}\n')
                    self.assertEqual(response.readline().strip(), b"event: changed")
                    with urlopen(url + "history.json", timeout=10) as history_response:
                        self.assertEqual(json.load(history_response)["machinery"]["check_outcomes"], {"failed": 1})
                finally:
                    response.close()
                    stream.close()
                self.assertEqual(sorted(p.relative_to(state) for p in state.rglob("*")), before)
                self.assertFalse((self.wt / ".orchestrate/evidence").exists())
            finally:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
