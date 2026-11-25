"""`rename` gives milestones typed references without disturbing approvals, paths or links."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import agent_loop, put  # noqa: E402

NAMES = {"G3t": "tile-dataflow", "G4": "apple-reconstruction"}


class RenameText(unittest.TestCase):
    def test_prose_cells_and_backticks_become_typed_references(self):
        text = "| `APPLE-TILE` | G3t | feeds `G4`'s colour, then G4 |"
        self.assertEqual(agent_loop.rename_milestones_text(text, NAMES),
                         "| `APPLE-TILE` | `milestone/tile-dataflow` | feeds `milestone/apple-reconstruction`'s "
                         "colour, then `milestone/apple-reconstruction` |")

    def test_paths_links_and_anchors_keep_the_old_id(self):
        text = ("[the G3T record](../decisions/G3T-METAL-BOUNDARY.md), evidence/G4/shot.png, #g4-plan, "
                "G4-INTEGRITY.md and G3T")
        self.assertEqual(agent_loop.rename_milestones_text(text, NAMES),
                         "[the `milestone/tile-dataflow` record](../decisions/G3T-METAL-BOUNDARY.md), "
                         "evidence/G4/shot.png, #g4-plan, G4-INTEGRITY.md and `milestone/tile-dataflow`")

    def test_longer_ids_and_other_codes_are_left_alone(self):
        self.assertEqual(agent_loop.rename_milestones_text("G40, G4a, AG4, G4-wide", NAMES), "G40, G4a, AG4, G4-wide")


class RenameTree(unittest.TestCase):
    def test_approvals_follow_the_renamed_text(self):
        with tempfile.TemporaryDirectory() as d:
            tree = Path(d)
            prof = {"plans": "docs/plans"}
            design = "# Tile\n\nFeeds G4.\n"
            wp = {"id": "WP1", "name": "Split", "status": "done",
                  "items": [{"id": "WP1.1", "statement": "Ready for G4", "check": "true"}]}
            put(tree / "docs/plans/TILE/DESIGN.md", design)
            put(tree / "docs/plans/TILE/DONE.json", json.dumps({"module": "TILE", "work_packages": [wp]}))
            put(tree / "docs/plans/TILE/LOG.md", "2026-11-01: G4 planned.\n")
            put(tree / "docs/plans/TILE/RECORD.json", json.dumps({
                "module": "TILE", "design": {"verdict": "ok", "hash": agent_loop.text_hash(design)},
                "work_packages": {"WP1": {"definitions": agent_loop.definitions(wp)}}}))
            put(tree / "docs/plans/VISION.md", "- **Apple reconstruction** (`milestone/apple-reconstruction`, was G4)\n")
            done: dict = {}
            agent_loop.rename_milestones_tree(tree, prof, NAMES, done)
            new_design = (tree / "docs/plans/TILE/DESIGN.md").read_text()
            new_wp = json.loads((tree / "docs/plans/TILE/DONE.json").read_text())["work_packages"][0]
            record = json.loads((tree / "docs/plans/TILE/RECORD.json").read_text())
            self.assertIn("`milestone/apple-reconstruction`", new_design)
            self.assertEqual(new_wp["items"][0]["statement"], "Ready for `milestone/apple-reconstruction`")
            self.assertTrue(agent_loop.design_ok(record, agent_loop.text_hash(new_design)))
            self.assertTrue(agent_loop.authorised(new_wp, record))
            self.assertEqual((tree / "docs/plans/TILE/LOG.md").read_text(), "2026-11-01: G4 planned.\n")
            self.assertIn("`milestone/apple-reconstruction`", (tree / "docs/plans/VISION.md").read_text())


if __name__ == "__main__":
    unittest.main()
