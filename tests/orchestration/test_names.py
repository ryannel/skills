"""The script's result names and fields keep to the set's glossary.

The authoring spec says the script uses the glossary's names, but nothing checked it, and by 2.0.0 the script
printed results such as FLOOR and PIN that no glossary entry or skill explained. A lead reading FLOOR told the human
"likely quota" for a merge that had finished after its turn ended. These tests fail when a result or field name
drifts from the glossary again.
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT / "skills" / "orchestration"
SCRIPT = DOMAIN / "build" / "scripts" / "agent_loop.py"
GLOSSARY = DOMAIN / "GLOSSARY.md"

# Calls whose first string argument, or keyword `result`, is a result name.
RESULT_CALLS = ("emit", "finish", "_result", "done_with")
# Words the glossary says to avoid, as they would appear inside a field name.
AVOIDED_IN_FIELDS = ("land", "integrat", "park", "attend", "harness", "claim", "loop")
# Old names the script may still read from files written by older versions, and where.
READ_FOR_OLD_FILES = {"PIN": 'state.get("result") in ("WRONG_MODEL_OR_EFFORT", "PIN")'}


def script_tree() -> ast.Module:
    return ast.parse(SCRIPT.read_text())


def call_name(node: ast.Call) -> str | None:
    return getattr(node.func, "id", None) or getattr(node.func, "attr", None)


def string_values(node: ast.AST) -> set[str]:
    """The string constants an expression can evaluate to, through `a if c else b`."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.IfExp):
        return string_values(node.body) | string_values(node.orelse)
    return set()


def printed_results() -> set[str]:
    names = set()
    for node in ast.walk(script_tree()):
        if isinstance(node, ast.Call) and call_name(node) in RESULT_CALLS:
            for arg in node.args[:3]:
                names |= {v for v in string_values(arg) if re.fullmatch(r"[A-Z][A-Z_]+", v)}
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "result":
                    names |= {s for s in string_values(v) if re.fullmatch(r"[A-Z][A-Z_]+", s)}
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "RUN_RESULTS" for t in node.targets):
            names |= {v.value for v in node.value.values if isinstance(v, ast.Constant)}
    return names


def result_fields() -> set[str]:
    fields = set()
    for node in ast.walk(script_tree()):
        if isinstance(node, ast.Call) and call_name(node) in RESULT_CALLS:
            fields |= {k.arg for k in node.keywords if k.arg}
        if isinstance(node, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "result" for k in node.keys):
            fields |= {k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    return fields


def glossary_results() -> tuple[set[str], set[str]]:
    """(the names in the glossary's Results table, the old names its Avoid line lists)."""
    section = GLOSSARY.read_text().split("\n## Results", 1)[1]
    rows = [l for l in section.splitlines() if l.startswith("| `")]
    names = {n for row in rows for n in re.findall(r"`([A-Z][A-Z_]+)`", row.split("|")[1])}
    avoid = next(l for l in section.split("\n\n") if l.startswith("Avoid:"))
    old = set(re.findall(r"`([A-Z][A-Z_]+)` \(now", avoid))
    return names, old


class ResultNames(unittest.TestCase):
    def test_every_result_the_script_prints_is_in_the_glossary(self):
        names, _ = glossary_results()
        missing = sorted(printed_results() - names)
        self.assertEqual(missing, [], "add these to the Results table in GLOSSARY.md, with what each means")

    def test_every_result_in_the_glossary_is_one_the_script_prints(self):
        names, _ = glossary_results()
        stale = sorted(names - printed_results() - {"NEEDS_CONTEXT"})  # passed through from the agent's last line
        self.assertEqual(stale, [], "the glossary lists results the script no longer prints")

    def test_every_result_is_explained_in_a_skill(self):
        names, _ = glossary_results()
        skills = "".join(p.read_text() for p in DOMAIN.rglob("SKILL.md"))
        unexplained = sorted(n for n in names if f"`{n}`" not in skills)
        self.assertEqual(unexplained, [], "the lead or an agent meets these results, but no skill says what they mean")

    def test_old_result_names_are_only_read_from_old_files(self):
        _, old = glossary_results()
        self.assertTrue(old)
        text = SCRIPT.read_text()
        for name in sorted(old):
            uses = [l.strip() for l in text.splitlines() if f'"{name}"' in l and not l.strip().startswith("#")]
            allowed = READ_FOR_OLD_FILES.get(name)
            self.assertEqual([u for u in uses if not (allowed and allowed in u)], [], name)


class FieldNames(unittest.TestCase):
    def test_no_result_field_uses_a_word_the_glossary_avoids(self):
        bad = sorted(f for f in result_fields() if any(w in f for w in AVOIDED_IN_FIELDS))
        self.assertEqual(bad, [], "rename these fields to the glossary's word, such as `merged` for `landed`")


class RenamedInOldProjects(unittest.TestCase):
    """Names renamed in 2.1.0 that existing projects and running scripts still hold."""

    def setUp(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from support import agent_loop
        self.agent_loop = agent_loop

    def test_migrate_renames_claim_to_ready_for_review(self):
        rec = {"milestones": {"M1": {"claim": {"commit": "abc", "checked": "def"}}}}
        self.assertIn("`claim` (now `ready_for_review`)", self.agent_loop.old_names_in_record(rec))
        new = self.agent_loop.upgrade_record(rec)
        self.assertEqual(new["milestones"]["M1"], {"ready_for_review": {"commit": "abc", "checked": "def"}})
        self.assertEqual(self.agent_loop.old_names_in_record(new), [])

    def test_a_record_not_yet_migrated_still_reads(self):
        self.assertEqual(self.agent_loop.ready_record({"claim": {"commit": "abc"}}), {"commit": "abc"})
        self.assertEqual(self.agent_loop.ready_record({"ready_for_review": {"commit": "def"}}), {"commit": "def"})

    def test_loops_still_runs_the_runs_command(self):
        import subprocess
        import sys
        for name in ("runs", "loops"):
            done = subprocess.run([sys.executable, str(SCRIPT), name, "--help"], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("only runs in the repository", done.stdout)

if __name__ == "__main__":
    unittest.main()
