"""Each command's --help says what it does, because the skills point agents there instead of describing the
script's mechanics themselves."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import agent_loop  # noqa: E402


class CommandHelp(unittest.TestCase):
    def setUp(self):
        parser = agent_loop.build_parser()
        self.sub = next(a for a in parser._actions if a.dest == "command")
        self.top = parser.format_help()

    def test_every_command_has_a_description_and_a_reference(self):
        for name, p in self.sub.choices.items():
            with self.subTest(command=name):
                self.assertTrue(p.description, f"{name} has no description")
                self.assertTrue(p.epilog, f"{name} has no reference text after its flags")

    def test_no_flag_points_at_text_the_help_doesnt_print(self):
        for name, p in self.sub.choices.items():
            with self.subTest(command=name):
                self.assertNotIn("see above", p.format_help())

    def test_the_top_level_help_carries_the_result_contract(self):
        for words in ("Results and exit status", "`next`", "decides: human", "exit 1 on REFUSED or FAILED"):
            self.assertIn(words, self.top)


if __name__ == "__main__":
    unittest.main()
