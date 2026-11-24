"""The working folder (2.6.0): evidence lives outside git, in one folder per repository that every worktree links
to, `migrate` moves a project's committed evidence there, and `cleanup` clears what the build keeps."""

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Repo, agent_loop, done, work_package, put  # noqa: E402


class WorkingFolder(Repo):
    def test_every_command_links_the_working_folder_and_git_ignores_it(self):
        self.ready()
        link = self.wt / ".orchestrate/evidence"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), self.evidence().resolve())
        (link / "WATER").mkdir()
        (link / "WATER/WP1.log").write_text("ran")
        self.assertEqual(self.evidence("WATER/WP1.log").read_text(), "ran")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        add = subprocess.run(["git", "-C", str(self.wt), "add", "-f", ".orchestrate/evidence/WATER/WP1.log"],
                             capture_output=True, text=True)
        self.assertNotEqual(add.returncode, 0)  # git can't commit through the link
        self.assertIn("/.orchestrate/evidence", (self.wt / ".git/info/exclude").read_text())

    def test_a_second_worktree_sees_the_same_files(self):
        self.ready()
        other = self.root / "other"
        self.git("worktree", "add", "-q", "--detach", str(other), "origin/main")
        self.ready(where=other)
        self.evidence("shared.md").write_text("one copy")
        self.assertEqual((other / ".orchestrate/evidence/shared.md").read_text(), "one copy")

    def test_a_review_stays_in_the_working_folder(self):
        self.ready_for_review()
        out = self.review()
        self.assertEqual(out["result"], "REVIEWED", out)
        self.assertTrue(self.evidence("WATER/WP1-review.md").exists())
        self.git("fetch", "-q", "origin")
        self.assertNotIn("WP1-review", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)
        rec = self.read_record()["work_packages"]["WP1"]
        self.assertEqual(rec["reviews"][-1]["review"], ".orchestrate/evidence/WATER/WP1-review.md")

    def test_merge_refuses_commits_that_put_evidence_in_git(self):
        prof = agent_loop.profile(self.wt)
        (self.wt / ".orchestrate/evidence").unlink()  # a worktree without the link, as a clone elsewhere has
        put(self.wt / ".orchestrate/evidence/WATER/WP1.log", "ran")
        put(self.wt / "src/water.rs", "fn main() {}")
        self.git("add", "-f", "-A")
        self.git("commit", "-qm", "water and its log")
        ok, why = agent_loop.land(self.wt, prof)
        self.assertFalse(ok)
        self.assertIn("evidence in git: .orchestrate/evidence/WATER/WP1.log", why)
        self.assertIn("as test data", why)
        self.git("fetch", "-q", "origin")
        self.assertNotIn("water.rs", self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)


class Migrate(Repo):
    DESIGN = ("# WATER design\n\nThe proof is in [the design proof](../../evidence/WATER/design-proof/), run with "
              "`docs/evidence/WATER/design-proof/proof.py`. See [the guide](../../guide.md) and "
              "[a site](https://example.test/docs/evidence/x).\n")

    def old_project(self, old_ids=True):
        """A project as 2.5.0 left it: evidence committed under docs/evidence, linked from the plans."""
        with open(self.wt / "ORCHESTRATE.md", "a") as f:
            f.write("- **Evidence:** docs/evidence  *(script: review files and saved proof)*\n"
                    "- **Graded examples:** docs/evidence/graded-examples.md\n")
        first, second = ("M1", "M2") if old_ids else ("WP1", "WP2")
        stem = f"docs/evidence/WATER/{first}"
        put(self.wt / f"{stem}-review.md", f"PASS {first}\nsee [shot]({first}-review/shot.png)")
        put(self.wt / f"{stem}-review/shot.png", "PNG")
        put(self.wt / f"{stem}.log", "builder's proof")
        put(self.wt / "docs/evidence/WATER/design-proof/proof.py", "print('proof')")
        (self.wt / "docs/evidence/WATER/design-proof/proof.py").chmod(0o755)
        put(self.wt / "docs/evidence/WATER/design-review.md", "DESIGN OK")
        put(self.wt / "docs/evidence/graded-examples.md", "## an example")
        put(self.wt / "docs/plans/WATER/DESIGN.md", self.DESIGN)
        w1 = work_package(first, "done", ["pass"])
        for i in w1["items"]:
            i.update(review=f"{stem}-review.md", evidence=f"{stem}.log", verdict="pass")
        w2 = work_package(second, "not_started", ["open"], check="test -f docs/evidence/WATER/baseline.png")
        doc = done(w1, w2)
        rec = agent_loop.adopt(doc, agent_loop.text_hash(self.DESIGN))
        rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(self.DESIGN),
                         "review": "docs/evidence/WATER/design-review.md", "commit": "a" * 40}
        rec["work_packages"][first]["reviews"] = [{"verdict": "pass", "review": f"{stem}-review.md", "commit": "b" * 40}]
        if old_ids:
            doc["milestones"] = doc.pop("work_packages")
            rec["milestones"] = rec.pop("work_packages")
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        put(self.wt / "docs/plans/WATER/RECORD.json", json.dumps(rec))
        self.commit_all()

    def test_every_command_refuses_a_project_that_commits_its_evidence(self):
        self.old_project(old_ids=False)
        with self.assertRaises(SystemExit) as stop:
            agent_loop.profile(self.wt)
        self.assertIn("still keeps its evidence in git, under docs/evidence", str(stop.exception))
        self.assertIn(" migrate --worktree ", str(stop.exception))

    def test_migrate_copies_the_evidence_and_points_everything_at_it(self):
        self.old_project()
        out = self.migrate()
        self.assertEqual(out["result"], "MIGRATED", out)
        ev = out["evidence"]
        self.assertEqual((ev["from"], ev["to"], ev["copied"], ev["already_there"]),
                         ("docs/evidence", ".orchestrate/evidence", 6, 0))
        self.assertEqual(ev["definitions_naming_it"], ["WATER WP2.1"])
        self.assertIn(str(self.wt.resolve()), ev["linked"])
        # the files, in the working folder, with their mode
        self.assertEqual(self.evidence("WATER/WP1-review/shot.png").read_text(), "PNG")
        self.assertEqual(self.evidence("WATER/WP1.log").read_text(), "builder's proof")
        self.assertTrue(os.access(self.evidence("WATER/design-proof/proof.py"), os.X_OK))
        self.assertEqual((self.wt / ".orchestrate/evidence/WATER/WP1-review.md").read_text(), "PASS M1\nsee [shot](M1-review/shot.png)")
        # the settings, the done-when file and the record
        self.git("fetch", "-q", "origin")
        settings = self.git("show", "origin/main:ORCHESTRATE.md").stdout
        self.assertIn("- **Evidence:** .orchestrate/evidence\n", settings)
        self.assertIn("- **Graded examples:** .orchestrate/evidence/graded-examples.md", settings)
        doc = self.read_done()
        self.assertEqual({(i["review"], i["evidence"]) for i in doc["work_packages"][0]["items"]},
                         {(".orchestrate/evidence/WATER/WP1-review.md", ".orchestrate/evidence/WATER/WP1.log")})
        self.assertEqual(doc["work_packages"][1]["items"][0]["check"], "test -f docs/evidence/WATER/baseline.png")
        rec = self.read_record()
        self.assertEqual(rec["design"]["review"], ".orchestrate/evidence/WATER/design-review.md")
        self.assertEqual(rec["work_packages"]["WP1"]["reviews"][0]["review"], ".orchestrate/evidence/WATER/WP1-review.md")
        self.assertEqual(rec["work_packages"]["WP1"]["reviews"][0]["commit"], "b" * 40)  # hashes stay as they are
        # the plan's links, from the design's own folder, opening through the link
        design = self.git("show", "origin/main:docs/plans/WATER/DESIGN.md").stdout
        self.assertIn("[the design proof](../../../.orchestrate/evidence/WATER/design-proof/)", design)
        self.assertIn("`.orchestrate/evidence/WATER/design-proof/proof.py`", design)
        self.assertIn("[the guide](../../guide.md)", design)
        self.assertIn("https://example.test/docs/evidence/x", design)
        self.assertEqual(rec["design"]["hash"], agent_loop.text_hash(design))  # the design review still counts
        self.assertTrue((self.wt / "docs/plans/WATER" / "../../../.orchestrate/evidence/WATER/design-proof/proof.py")
                        .exists())
        # the old files stay in git until the user has them purged
        self.assertIn("docs/evidence/WATER/M1-review.md",
                      self.git("ls-tree", "-r", "--name-only", "origin/main").stdout)
        self.git("pull", "-q", "--rebase", "origin", "main")
        self.assertEqual(agent_loop.profile(self.wt)["evidence"], ".orchestrate/evidence")
        self.assertEqual(self.ready()["design_not_approved"], [])

    def test_migrate_twice_does_nothing_more(self):
        self.old_project()
        self.assertEqual(self.migrate()["result"], "MIGRATED")
        self.evidence("WATER/WP1-review.md").write_text("newer")
        self.git("pull", "-q", "--rebase", "origin", "main")
        before = self.git("rev-parse", "origin/main").stdout
        again = self.migrate()
        self.assertEqual(again["result"], "NOTHING", again)
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.git("rev-parse", "origin/main").stdout, before)
        self.assertEqual(self.evidence("WATER/WP1-review.md").read_text(), "newer")

    def test_migrate_with_a_commit_map_points_records_and_run_state_at_the_new_hashes(self):
        put(self.wt / "docs/plans/WATER/DESIGN.md", "# WATER design\n")
        doc = done(work_package("WP1", "done", ["pass"]), work_package("WP2", "ready_for_review", ["pass"]))
        put(self.wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
        rec = agent_loop.adopt(doc, agent_loop.text_hash("# WATER design\n"))
        rec["work_packages"]["WP1"]["reviews"] = [{"verdict": "pass", "commit": "b" * 40}]
        rec["work_packages"]["WP2"]["ready_for_review"] = {"commit": "c" * 40, "checked": "d" * 40}
        put(self.wt / "docs/plans/WATER/RECORD.json", json.dumps(rec))
        self.commit_all()
        state = self.wt / ".git/orchestrate/results/WATER-WP2-run.json"
        put(state, json.dumps({"result": "READY_FOR_REVIEW", "commit": "c" * 40}))
        commit_map = self.root / "commit-map"
        commit_map.write_text("old new\n" + "".join(f"{o * 40} {n * 40}\n" for o, n in ("b1", "c2", "d3"))
                              + "e" * 40 + " " + "0" * 40 + "\n")
        out = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), commit_map=str(commit_map))
        self.assertEqual(out["result"], "MIGRATED", out)
        self.assertEqual((out["commits_remapped"], out["records"], out["state_files"]), (3, 1, 1))
        rec = self.read_record()
        self.assertEqual(rec["work_packages"]["WP1"]["reviews"][0]["commit"], "1" * 40)
        self.assertEqual(rec["work_packages"]["WP2"]["ready_for_review"], {"commit": "2" * 40, "checked": "3" * 40})
        self.assertEqual(json.loads(state.read_text())["commit"], "2" * 40)
        self.assertIn(agent_loop.COMMIT_MAP_SUBJECT, self.git("log", "-3", "--format=%s", "origin/main").stdout)
        again = self.call(agent_loop.cmd_migrate, worktree=str(self.wt), commit_map=str(commit_map))
        self.assertEqual(again["result"], "NOTHING", again)

    def test_after_migrate_merge_refuses_new_files_in_the_old_folder(self):
        self.old_project()
        self.migrate()
        self.git("pull", "-q", "--rebase", "origin", "main")
        prof = agent_loop.profile(self.wt)
        put(self.wt / "docs/evidence/WATER/WP2.log", "ran")
        self.git("add", "-A")
        self.git("commit", "-qm", "a log in the old place")
        ok, why = agent_loop.land(self.wt, prof)
        self.assertFalse(ok)
        self.assertIn("docs/evidence/WATER/WP2.log", why)


class Cleanup(Repo):
    def cleanup(self, **kw):
        out = self.printed(agent_loop.cmd_cleanup, worktree=str(self.wt), **kw)
        return json.loads(out.splitlines()[-1]) if not kw.get("json") else json.loads(out)

    def done_w1(self):
        self.ready_for_review()
        self.assertEqual(self.review()["verdict"], "PASS")
        self.evidence("WATER/WP1-review").mkdir(exist_ok=True)
        self.evidence("WATER/WP1-review/shot.png").write_text("PNG")
        self.evidence("WATER/WP2.log").write_text("WP2 is still being built")
        self.evidence("graded-examples.md").write_text("## an example")

    def test_cleanup_lists_by_kind_and_removes_nothing(self):
        self.done_w1()
        out = self.cleanup()
        self.assertEqual(out["result"], "WOULD_REMOVE", out)
        self.assertEqual(out["kinds"]["evidence"]["items"], 2)  # WP1-review.md and its folder
        self.assertNotIn("graded", out["kinds"])
        self.assertTrue(self.evidence("WATER/WP1-review.md").exists())
        found = self.cleanup(json=True)
        self.assertEqual(found["next"]["decides"], "human")
        self.assertIn("--yes", found["next"]["command"])
        self.assertEqual(sorted(Path(f["path"]).name for f in found["found"] if f["kind"] == "evidence"),
                         ["WP1-review", "WP1-review.md"])

    def test_cleanup_with_yes_removes_done_work_packages_evidence_only(self):
        self.done_w1()
        out = self.cleanup(yes=True)
        self.assertEqual(out["result"], "REMOVED", out)
        self.assertFalse(self.evidence("WATER/WP1-review.md").exists())
        self.assertFalse(self.evidence("WATER/WP1-review").exists())
        self.assertTrue(self.evidence("WATER/WP2.log").exists())
        self.assertTrue(self.evidence("graded-examples.md").exists())
        self.assertTrue((self.wt / "docs/plans/WATER/DONE.json").exists())
        self.assertEqual(self.cleanup(kind=["evidence"])["result"], "NOTHING")

    def test_graded_examples_go_only_when_named(self):
        self.done_w1()
        out = self.cleanup(kind=["graded"], yes=True)
        self.assertEqual(out["kinds"], {"graded": {"items": 1, "bytes": len("## an example")}})
        self.assertFalse(self.evidence("graded-examples.md").exists())
        self.assertTrue(self.evidence("WATER/WP1-review.md").exists())

    def test_older_than_keeps_recent_files(self):
        self.done_w1()
        self.assertEqual(self.cleanup(kind=["evidence"], older_than=1)["result"], "NOTHING")
        old = time.time() - 3 * 86400
        for p in (self.evidence("WATER/WP1-review.md"), self.evidence("WATER/WP1-review/shot.png"),
                  self.evidence("WATER/WP1-review")):
            os.utime(p, (old, old))
        out = self.cleanup(kind=["evidence"], older_than=2)
        self.assertEqual(out["kinds"]["evidence"]["items"], 2, out)

    def test_a_module_whose_run_lock_is_held_is_left_alone(self):
        self.done_w1()
        with mock.patch.object(agent_loop, "run_holder", lambda folder, key: 4242 if key == "WATER" else None):
            out = self.cleanup(kind=["evidence"], yes=True)
        self.assertEqual(out["result"], "NOTHING", out)
        self.assertIn("WATER: its run lock is held", out["kept"][0])
        self.assertTrue(self.evidence("WATER/WP1-review.md").exists())

    def test_ledgers_lose_only_the_rows_the_history_has_copied(self):
        self.ready()
        usage = agent_loop.loop_dir(self.wt) / "usage.jsonl"
        usage.write_text(json.dumps({"at": "2026-01-01T00:00:00Z", "n": 1}) + "\n"
                         + json.dumps({"at": "2026-11-18T12:00:00Z", "n": 2}) + "\n")
        out = self.cleanup(kind=["ledgers"])
        self.assertEqual(out["result"], "NOTHING")  # the tests run with the delivery history off
        self.assertIn("hasn't copied them yet", out["kept"][0])
        copied = agent_loop.delivery_history.parse_time("2026-06-01T00:00:00Z")
        with mock.patch.object(agent_loop, "history_copied_at", lambda worktree: copied):
            out = self.cleanup(kind=["ledgers"], yes=True)
        self.assertEqual(out["kinds"]["ledgers"]["items"], 1, out)
        self.assertEqual([json.loads(line)["n"] for line in usage.read_text().splitlines()], [2])

    def test_cleanup_is_refused_inside_a_session(self):
        with mock.patch.dict(os.environ, {"ORCHESTRATE_ROLE": "build"}), self.assertRaises(SystemExit) as stop:
            self.cleanup()
        self.assertIn("user's decision", str(stop.exception))


if __name__ == "__main__":
    unittest.main()
