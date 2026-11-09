"""Checks for skill-creator's check_skill.py, including the malformed YAML from the round-two review (Astra 17)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills/skill-creator/scripts"))
import check_skill  # noqa: E402


def skill(tmp: str, front: str, body: str = "# Skill\n", name: str = "bad-yaml") -> Path:
    folder = Path(tmp, name)
    folder.mkdir()
    (folder / "SKILL.md").write_text(f"---\n{front}---\n\n{body}")
    return folder


class CheckSkill(unittest.TestCase):
    def test_a_good_skill_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = skill(tmp, 'name: bad-yaml\ndescription: "Does a thing: well. Use when asked."\n')
            self.assertEqual(check_skill.check(folder), [])

    def test_astra_17_unquoted_colon_in_a_value_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = skill(tmp, "name: bad-yaml\ndescription: broken: mapping\n")
            self.assertTrue(any("description" in p for p in check_skill.check(folder)))

    def test_duplicate_keys_unterminated_quotes_and_stray_lines(self):
        for front in ('name: bad-yaml\ndescription: one\ndescription: two\n',
                      'name: bad-yaml\ndescription: "never closed\n',
                      'name: bad-yaml\ndescription: fine\njust some words\n'):
            with tempfile.TemporaryDirectory() as tmp:
                self.assertTrue(check_skill.check(skill(tmp, front)), front)

    def test_reserved_words_in_the_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = skill(tmp, "name: claude-helper\ndescription: Helps.\n", name="claude-helper")
            self.assertTrue(any("reserved" in p for p in check_skill.check(folder)))

    def test_links_to_missing_headings_are_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = skill(tmp, "name: bad-yaml\ndescription: Helps.\n",
                           body="# Skill\n\n## Real heading\n\n[ok](#real-heading) [bad](#no-such-heading)\n")
            problems = check_skill.check(folder)
            self.assertEqual(len(problems), 1)
            self.assertIn("no-such-heading", problems[0])


if __name__ == "__main__":
    unittest.main()
