"""A paused 2.13 repository, including the state and evidence that live outside git."""

import json
import shlex
import subprocess
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Repo, agent_loop, put  # noqa: E402


class WorkPackageMigration(Repo):
    def setUp(self):
        super().setUp()
        self.plans = self.wt / "docs/plans"
        self.state_dir = agent_loop.loop_dir(self.wt)
        self.vision = "The team builds for the Apple M1.\n"
        self.log_entry = "2026-11-21: M1 passed its first review.\n"
        self.task = "Diagnose the disputed captures from the test on the Apple M1."
        rel = ".orchestrate/evidence/WATER/"
        put(self.plans / "BRIEF.md", self.vision)
        put(self.plans / "WATER/PLAN.md", "# Water\n\n## M1: Surface\n\n## M2: Foam\n")
        put(self.plans / "WATER/LOG.md", self.log_entry)
        with (self.wt / "ORCHESTRATE.md").open("a") as f:
            f.write("- **Purpose:** docs/plans/BRIEF.md\n")
        water = {"id": "M1", "name": "Surface", "status": "in_progress", "depends_on": ["CORE:M3"],
                 "items": [{"id": "M1.4", "statement": "Runs on an Apple M1", "check": "true", "builder_result": "pass",
                            "evidence": rel + "M1/shot.png", "review": rel + "M1-review.md", "verdict": "fail"}]}
        core = {"id": "M3", "name": "Renderer", "status": "done",
                "items": [{"id": "M3.1", "statement": "Paints a frame", "check": "true", "builder_result": "pass",
                           "evidence": "checked"}]}
        older = {"verdict": "fail", "at": "2026-11-21T00:00:00Z", "items": {"M1.4": "fail"},
                 "findings": [{"name": "Missing surface", "item": "M1.4"}], "review": rel + "M1-review-1.md"}
        latest = {**older, "at": "2026-11-22T00:00:00Z", "review": rel + "M1-review.md"}
        for module, entry in (("WATER", water), ("CORE", core)):
            record = {"definitions": agent_loop.definitions(entry),
                      "authorised": {"by": "adopt", "files": ["docs/plans/BRIEF.md"]}, "reviews": []}
            if module == "WATER":
                record.update(reviews=[older, latest],
                              human_feedback=[{"items": ["M1.4"], "said": "Use the Apple M1", "at": latest["at"]}])
            else:
                record["done"] = {"at": latest["at"], "by": "checks"}
            put(self.plans / module / "DONE.json", json.dumps({"module": module, "milestones": [entry]}))
            put(self.plans / module / "RECORD.json", json.dumps({
                "module": module, "design": {"verdict": "ok", "hash": agent_loop.text_hash(None)},
                "milestones": {entry["id"]: record}, "briefs": [{"task": self.task}]}))
        self.git("add", "-A")
        self.git("commit", "-qm", "M1 review", "-m", agent_loop.TRAILER)
        self.git("push", "-q", "origin", "main")
        self.before = agent_loop.head_commit(self.wt)
        self.git("update-ref", "refs/orchestrate/claims/WATER/M1", self.before)
        self.git("push", "-q", "origin", "refs/orchestrate/claims/WATER/M1")
        for stem in ("M1-review", "M1-review-1"):
            put(self.evidence(f"WATER/{stem}.md"), f"[capture]({stem}/shot.png)\nFAIL M1: missing surface\n")
            put(self.evidence(f"WATER/{stem}/shot.png"), stem)
        put(self.evidence("WATER/M1/shot.png"), "builder's capture")
        put(self.evidence("WATER/M1-handoff.md"), "Re-run the capture once the changes land.\n")
        put(self.state_dir / "WATER.json", json.dumps({"module": "WATER", "milestone": "M1", "thread": "s1"}))
        result = self.state_dir / "results/WATER-M1-review.json"
        argv = ["python3", "agent_loop.py", "review", "--milestone", "M1"]
        put(result, json.dumps({"module": "WATER", "milestone": "M1", "result": "REVIEWED",
                                "verdict": "FAIL", "result_file": str(result),
                                "quota": {"forecast": {"open_milestones": 1}},
                                "next": {"argv": argv, "command": shlex.join(argv),
                                         "alternative": shlex.join([*argv, "--host", "claude"])}}))

    def test_a_review_can_resume_from_the_recorded_2_13_builder_commit(self):
        doc, rec = self.read_done(), self.read_record()
        doc["milestones"][0]["status"] = "ready_for_review"
        rec["milestones"]["M1"]["ready_for_review"] = {"commit": self.before, "checked": self.before,
                                                       "at": "2026-11-23T12:00:00Z"}
        put(self.plans / "WATER/DONE.json", json.dumps(doc))
        put(self.plans / "WATER/RECORD.json", json.dumps(rec))
        self.git("commit", "-qam", "M1 ready for review", "-m", agent_loop.TRAILER)
        self.git("push", "-q", "origin", "main")
        self.assertEqual(self.migrate()["result"], "MIGRATED")
        review = self.review("WP1", commit=None)
        self.assertEqual((review["result"], review.get("verdict")), ("REVIEWED", "PASS"), review)
        self.assertIn("before `migrate` brought", " ".join(review["warnings"]))
        self.assertIn("done", self.read_record()["work_packages"]["WP1"])

    def test_done_heading_for_work_package_zero_can_start_with_mac(self):
        module = self.plans / "T2-CAPTURE"
        heading = "Mac engine images and runtime motion without a desktop capture grant: done"
        plan = f"# Capture\n\n## M0 {heading}\nUse this M0 Mac.\n"
        put(module / "PLAN.md", plan)
        entry = {"id": "M0", "status": "done",
                 "items": [{"id": "M0.1", "statement": "Images load", "check": "true",
                            "builder_result": "pass", "evidence": "checked"}]}
        put(module / "DONE.json", json.dumps({"module": "T2-CAPTURE", "milestones": [entry]}))
        put(module / "RECORD.json", json.dumps({"milestones": {
            "M0": {"definitions": agent_loop.definitions(entry), "done": {"by": "checks"}}}}))
        self.commit_all()

        result = self.migrate()
        self.assertEqual(result["result"], "MIGRATED", result)
        self.assertEqual((module / "PLAN.md").read_text(), plan.replace("## M0", "## WP0"))
        self.assertEqual(result["rewrites"]["docs/plans/T2-CAPTURE/PLAN.md"], {"M0 → WP0": 1})
        prof = agent_loop.profile(self.wt)
        capture = agent_loop.project(self.wt, prof, "HEAD")["T2-CAPTURE"]
        [entry] = capture["doc"]["work_packages"]
        self.assertEqual((entry["id"], entry["status"]), ("WP0", "done"))
        self.assertTrue(agent_loop.recorded_done(entry, capture["record"]))
        self.assertEqual(self.migrate()["result"], "NOTHING")

    def test_old_names_left_by_the_rewrite_fail_before_commit_or_local_moves(self):
        plan = self.plans / "WATER/PLAN.md"
        original = plan.read_text()
        migrate_tree = agent_loop.migrate_tree
        remote = self.git("ls-remote", "origin").stdout
        local = self.git("show-ref").stdout

        def leave_old_heading(tree, *args, **kwargs):
            changed = migrate_tree(tree, *args, **kwargs)
            put(tree / plan.relative_to(self.wt), original)
            return changed

        with mock.patch.object(agent_loop, "migrate_tree", side_effect=leave_old_heading), \
                mock.patch.object(agent_loop, "land") as land:
            result = self.migrate()
        self.assertEqual(result["result"], "FAILED", result)
        self.assertIn("stopped before committing", result["detail"])
        self.assertIn("docs/plans/WATER/PLAN.md has old work package headings", result["problems"])
        land.assert_not_called()
        self.assertEqual(agent_loop.head_commit(self.state_dir / "verify/_MIGRATE"), self.before)
        self.assertEqual(self.git("ls-remote", "origin").stdout, remote)
        self.assertEqual(self.git("show-ref").stdout, local)
        self.assertEqual(plan.read_text(), original)
        self.assertTrue(self.evidence("WATER/M1/shot.png").is_file())
        self.assertTrue((self.state_dir / "results/WATER-M1-review.json").is_file())

    def test_migrate_preserves_reviews_dependencies_claims_and_evidence(self):
        result = self.migrate()
        self.assertEqual(result["result"], "MIGRATED", result)
        self.assertFalse((self.plans / "BRIEF.md").exists())
        self.assertEqual((self.plans / "VISION.md").read_text(), self.vision)
        self.assertIn("docs/plans/VISION.md", (self.wt / "ORCHESTRATE.md").read_text())
        self.assertEqual((self.plans / "WATER/LOG.md").read_text(), self.log_entry)
        self.assertEqual(self.git("show", "-s", "--format=%s", self.before).stdout.strip(), "M1 review")
        self.assertEqual((self.plans / "WATER/PLAN.md").read_text(), "# Water\n\n## WP1: Surface\n\n## WP2: Foam\n")
        doc, rec = self.read_done(), self.read_record()
        self.assertNotIn("milestones", doc)
        self.assertNotIn("milestones", rec)
        self.assertNotIn("briefs", rec)
        self.assertEqual(rec["tasks"], [{"task": self.task}])
        [water] = doc["work_packages"]
        [item] = water["items"]
        self.assertEqual((water["id"], item["id"], item["statement"], water["depends_on"]),
                         ("WP1", "WP1.4", "Runs on an Apple M1", ["CORE:WP3"]))
        record = rec["work_packages"]["WP1"]
        self.assertEqual(record["definitions"], agent_loop.definitions(water))
        [vision] = record["authorised"]["files"]
        self.assertEqual(self.wt / vision, self.plans / "VISION.md")
        self.assertTrue((self.wt / vision).is_file())
        self.assertEqual(record["human_feedback"][0]["items"], ["WP1.4"])
        self.assertEqual(record["human_feedback"][0]["said"], "Use the Apple M1")
        core = json.loads((self.plans / "CORE/RECORD.json").read_text())
        self.assertIn("done", core["work_packages"]["WP3"])
        self.assertEqual((self.wt / item["evidence"]).read_text(), "builder's capture")
        self.assertEqual(self.wt / item["review"], self.wt / record["reviews"][-1]["review"])
        self.assertTrue(self.evidence("WATER/WP1-handoff.md").is_file())
        self.assertEqual(len(record["reviews"]), 2)
        for review, capture in zip(record["reviews"], ("M1-review-1", "M1-review")):
            self.assertEqual(review["items"], {"WP1.4": "fail"})
            self.assertEqual(review["findings"][0]["item"], "WP1.4")
            path = self.wt / review["review"]
            self.assertEqual(path.read_text(), f"[capture]({capture}/shot.png)\nFAIL M1: missing surface\n")
            self.assertEqual((path.parent / path.stem / "shot.png").read_text(), capture)
        for repo in (self.wt, self.origin):
            self.assertEqual(self.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/orchestrate/claims",
                                      where=repo).stdout.strip(), f"refs/orchestrate/claims/WATER/WP1 {self.before}")
        state = json.loads((self.state_dir / "WATER.json").read_text())
        self.assertEqual(state["work_package"], "WP1")
        self.assertNotIn("milestone", state)
        result_file = self.state_dir / "results/WATER-WP1-review.json"
        saved = json.loads(result_file.read_text())
        self.assertEqual((saved["work_package"], Path(saved["result_file"])), ("WP1", result_file))
        self.assertEqual(saved["quota"]["forecast"], {"open_work_packages": 1})
        self.assertEqual(saved["next"]["argv"][-2:], ["--work-package", "WP1"])
        self.assertEqual(saved["next"]["argv"], shlex.split(saved["next"]["command"]))
        self.assertEqual(shlex.split(saved["next"]["alternative"])[-4:], ["--work-package", "WP1", "--host", "claude"])
        self.assertFalse((self.state_dir / "results/WATER-M1-review.json").exists())
        self.assertEqual(self.ready()["invalid"], [])

        def snapshot():
            files = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                     for root in (self.plans, self.evidence(), self.state_dir / "results")
                     for p in root.rglob("*") if p.is_file()}
            return files, self.git("show-ref").stdout, self.git("ls-remote", "origin").stdout

        before = snapshot()
        self.assertEqual(self.migrate()["result"], "NOTHING")
        self.assertEqual(snapshot(), before)

    def test_migrate_rewrites_active_text_and_checks_in_the_referenced_module(self):
        evidence_path = ".orchestrate/evidence/WATER/M1/check_loaded.py"
        put(self.evidence("WATER/M1/check_loaded.py"), '# M1 runs on this M3 Max\nassert 3 == 3\n')
        brief = "# Water feature\nM1 predates migration.\n"
        put(self.plans / "WATER/BRIEF.md", brief)
        put(self.plans / "ARCHITECTURE.md",
            "| # | Module | What it's for | Needs |\n|---|---|---|---|\n"
            "| 1 | CORE | Renderer | |\n| 2 | WATER | Surface | CORE M3 |\n"
            "\nWATER M1 and CORE:M3.1 run on this M3 Max. UNKNOWN:M1 stays literal.\n")
        put(self.plans / "BRIEF.md", "Goal: WATER M1 builds on CORE:M3.1 and runs on this M3 Max.\n")
        design = "Measure M1.4 after CORE M3.1. Use this M3 Max. See [history](BRIEF.md).\n"
        put(self.plans / "WATER/DESIGN.md", design)
        put(self.plans / "CORE/DESIGN.md", "M3.1 renders on this M3 Max, an Apple M3.\n")
        put(self.plans / "WATER/PLAN.md", "## M1: Surface\nRun M1.4's check first.\n\n## M2: Foam\n")
        doc, rec = self.read_done(), self.read_record()
        [water] = doc["milestones"]
        water.update(failed_reviews=2, failed_reviews_with_repeat=1)
        water["quality_bar"] = "Compare to CORE:M3.1 and M2 on this M3 Max."
        item = water["items"][0]
        item.update(statement="M1.4 uses CORE M3.1 on this M3 Max; unmatched M99 stays literal.",
                    inspect="Run M1.4 first, then CORE:M3.1.", ask="Is M1.4 ready after CORE M3?",
                    check=f"python3 {evidence_path}", reads=[evidence_path])
        record_check = 'python3 -c \'import json; r=json.load(open("docs/plans/CORE/RECORD.json"))["milestones"]; assert r.get("M3", {}).get("done")\''
        water["items"].append({"id": "M1.5", "statement": "CORE M3 is Done", "check": record_check,
                               "builder_result": "pass", "evidence": "checked"})
        rec["milestones"]["M1"]["definitions"] = agent_loop.definitions(water)
        rec["design"]["hash"] = agent_loop.text_hash(design)
        put(self.plans / "WATER/DONE.json", json.dumps(doc))
        put(self.plans / "WATER/RECORD.json", json.dumps(rec))
        self.commit_all()

        def check_all(items):
            for i in items:
                completed = subprocess.run(i["check"], cwd=self.wt, shell=True, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, (i["check"], completed.stderr))

        agent_loop.link_evidence(self.wt)
        check_all(water["items"])
        result = self.migrate()
        self.assertEqual(result["result"], "MIGRATED", result)
        [water] = self.read_done()["work_packages"]
        check_all(water["items"])
        item, dependency = water["items"]
        self.assertEqual(item["reads"], [evidence_path.replace("/M1/", "/WP1/")])
        self.assertEqual(item["statement"], "WP1.4 uses CORE WP3.1 on this M3 Max; unmatched M99 stays literal.")
        self.assertEqual(item["inspect"], "Run WP1.4 first, then CORE:WP3.1.")
        self.assertEqual(item["ask"], "Is WP1.4 ready after CORE WP3?")
        self.assertIn('["work_packages"]; assert r.get("WP3"', dependency["check"])
        self.assertEqual(water["quality_bar"], "Compare to CORE:WP3.1 and WP2 on this M3 Max.")
        self.assertEqual((water["status"], water["failed_reviews"], water["failed_reviews_with_repeat"]),
                         ("in_progress", 2, 1))
        self.assertEqual([i["builder_result"] for i in water["items"]], ["pass", "pass"])
        new_design = (self.plans / "WATER/DESIGN.md").read_text()
        self.assertEqual(new_design, design.replace("M1.4", "WP1.4").replace("CORE M3.1", "CORE WP3.1"))
        self.assertEqual(self.read_record()["design"]["hash"], agent_loop.text_hash(new_design))
        self.assertEqual(self.read_record()["work_packages"]["WP1"]["definitions"], agent_loop.definitions(water))
        self.assertEqual((self.plans / "WATER/BRIEF.md").read_text(), brief)
        self.assertFalse((self.plans / "WATER/VISION.md").exists())
        self.assertIn("Run WP1.4's check first.", (self.plans / "WATER/PLAN.md").read_text())
        self.assertIn("WATER WP1 and CORE:WP3.1 run on this M3 Max. UNKNOWN:M1 stays literal.",
                      (self.plans / "ARCHITECTURE.md").read_text())
        self.assertIn("WATER WP1 builds on CORE:WP3.1 and runs on this M3 Max",
                      (self.plans / "VISION.md").read_text())
        self.assertEqual((self.plans / "CORE/DESIGN.md").read_text(),
                         "WP3.1 renders on this M3 Max, an Apple M3.\n")
        self.assertEqual(self.evidence("WATER/WP1/check_loaded.py").read_text(),
                         '# M1 runs on this M3 Max\nassert 3 == 3\n')
        self.assertIn("milestones → work_packages", result["rewrites"]["docs/plans/WATER/DONE.json"])
        self.assertIn("M1 → WP1", result["rewrites"]["docs/plans/WATER/PLAN.md"])
        core = agent_loop.project(self.wt, agent_loop.profile(self.wt), "HEAD")["CORE"]
        self.assertTrue(agent_loop.recorded_done(core["doc"]["work_packages"][0], core["record"]))
        before = agent_loop.head_commit(self.wt)
        self.assertEqual(self.migrate()["result"], "NOTHING")
        self.assertEqual(agent_loop.head_commit(self.wt), before)
