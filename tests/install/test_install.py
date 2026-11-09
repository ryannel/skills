"""install.py without the host CLIs: finding and moving aside earlier standalone installs, matching the marketplace
source, and what --repo reports. The CLI paths were run against throwaway configs; see the holistic-review result."""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("install", ROOT / "install.py")
install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install)


class Home:
    """A throwaway home shaped like an earlier standalone install."""

    def __init__(self, tmp: str):
        self.home = Path(tmp)
        self.claude, self.codex = self.home / ".claude", self.home / ".codex"
        self.env = mock.patch.dict(os.environ, {"HOME": tmp, "CLAUDE_CONFIG_DIR": str(self.claude),
                                                "CODEX_HOME": str(self.codex)})
        for name in ("instructing-agents", "build"):
            src = ROOT / ("skills/instructing-agents" if name == "instructing-agents" else "skills/orchestration/build")
            dest = self.claude / "skills" / name
            dest.mkdir(parents=True)
            (dest / "SKILL.md").write_bytes((src / "SKILL.md").read_bytes())
            (self.home / ".agents/skills").mkdir(parents=True, exist_ok=True)
            (self.home / ".agents/skills" / name).symlink_to(dest)
        (self.claude / "skills/build/agents").mkdir()
        (self.claude / "skills/build/agents/e.md").write_text("agent\n")
        (self.claude / "agents").mkdir()
        (self.claude / "agents/orchestrate-evaluator.md").symlink_to(self.claude / "skills/build/agents/e.md")
        mine = self.home / ".agents/skills/my-own"
        mine.mkdir()
        (mine / "SKILL.md").write_text("---\nname: my-own\ndescription: x\n---\n")
        other = self.codex / "skills/skill-creator"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("---\nname: skill-creator\ndescription: someone else's\n---\n")
        self.settings = {"theme": "dark", "hooks": {"PreToolUse": [
            {"matcher": "Agent|Bash", "hooks": [{"type": "command",
                                                 "command": "python3 ~/.claude/hooks/instructing-agents-gate.py"}]},
            {"matcher": "Edit", "hooks": [{"type": "command", "command": "echo keep"}]}]}}
        (self.claude / "settings.json").write_text(json.dumps(self.settings))


def quietly(fn, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        fn(*args)
    return out.getvalue()


class Migration(unittest.TestCase):
    plugins = ["instructing-agents", "orchestrate", "skill-creator"]

    def test_without_the_flag_it_lists_everything_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Home(tmp)
            with h.env, self.assertRaises(SystemExit) as stop:
                out = io.StringIO()
                with redirect_stdout(out):
                    install.migrate(self.plugins, ["claude", "codex"], False)
            self.assertIn("--replace-standalone", str(stop.exception))
            text = out.getvalue()
            for expected in ("skills/instructing-agents", "skills/build", "orchestrate-evaluator.md",
                             "instructing-agents-gate.py", "doesn't match this repo's; left alone"):
                self.assertIn(expected, text)
            self.assertTrue((h.claude / "skills/build/SKILL.md").exists())
            self.assertEqual(json.loads((h.claude / "settings.json").read_text()), h.settings)

    def test_with_the_flag_it_moves_copies_drops_links_and_only_the_old_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Home(tmp)
            with h.env:
                quietly(install.migrate, self.plugins, ["claude", "codex"], True)
            self.assertEqual(sorted(p.name for p in (h.claude / "skills").iterdir()), [])
            self.assertEqual(sorted(p.name for p in (h.home / ".agents/skills").iterdir()), ["my-own"])
            self.assertFalse((h.claude / "agents/orchestrate-evaluator.md").is_symlink())
            self.assertTrue((h.codex / "skills/skill-creator/SKILL.md").exists())
            settings = json.loads((h.claude / "settings.json").read_text())
            self.assertEqual(settings, {"theme": "dark", "hooks": {"PreToolUse": [h.settings["hooks"]["PreToolUse"][1]]}})
            backup = next((h.home / ".ryannel-skills-backup").iterdir())
            self.assertTrue((backup / "claude/skills/build/SKILL.md").exists())
            self.assertEqual(json.loads((backup / "settings.json").read_text()), h.settings)
            self.assertIn("removed link", (backup / "MOVED.txt").read_text())

    def test_a_clean_home_passes(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"HOME": tmp,
                "CLAUDE_CONFIG_DIR": f"{tmp}/.claude", "CODEX_HOME": f"{tmp}/.codex"}):
            self.assertEqual(quietly(install.migrate, self.plugins, ["claude", "codex"], False), "")

    def test_the_plugins_own_hook_isnt_old(self):
        plugin = {"hooks": {"PreToolUse": [{"hooks": [{"command":
                  'python3 "${CLAUDE_PLUGIN_ROOT}/skills/instructing-agents/hooks/handoff_nudge.py"'}]}]}}
        self.assertEqual(install.old_hook_entries(plugin), [])


class Source(unittest.TestCase):
    def test_local_paths_compare_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(install.same_source(os.path.realpath(tmp), tmp))
            self.assertFalse(install.same_source("/old/checkout", tmp))

    def test_github_spellings(self):
        self.assertTrue(install.same_source("ryannel/skills", "https://github.com/ryannel/skills.git"))
        self.assertFalse(install.same_source("someone/skills", "ryannel/skills"))


class Repo(unittest.TestCase):
    def setup(self, tmp, cli, *files):
        repo = Path(tmp, "parent", "repo")
        repo.mkdir(parents=True)
        (repo / "AGENTS.md").write_text("# rules\n")
        for f in files:
            Path(tmp, f).parent.mkdir(parents=True, exist_ok=True)
            Path(tmp, f).write_text("# x\n")
        with mock.patch.object(install, "version", return_value=cli), \
                mock.patch.object(install.shutil, "which", return_value="claude"), \
                mock.patch.dict(os.environ, {"HOME": tmp, "CLAUDE_CONFIG_DIR": f"{tmp}/.claude"}):
            return repo, quietly(install.setup_repo, repo, ["instructing-agents"])

    def test_new_cli_with_nothing_in_the_way_reads_agents_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, out = self.setup(tmp, (2, 1, 317))
            self.assertIn("Claude reads AGENTS.md here", out)
            self.assertFalse((repo / "CLAUDE.md").exists())

    def test_a_shadowing_file_gets_an_import_whatever_the_version(self):
        for shadow in ("parent/CLAUDE.md", "parent/repo/CLAUDE.local.md", "parent/repo/.claude/CLAUDE.md"):
            with tempfile.TemporaryDirectory() as tmp:
                repo, out = self.setup(tmp, (2, 1, 317), shadow)
                self.assertIn("stops Claude reading AGENTS.md", out, shadow)
                self.assertEqual((repo / "CLAUDE.md").read_text(), "@AGENTS.md\n")

    def test_old_cli_gets_an_import_and_an_existing_claude_md_is_reported_not_edited(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, out = self.setup(tmp, (2, 1, 239))
            self.assertIn("reads only CLAUDE.md", out)
        with tempfile.TemporaryDirectory() as tmp:
            repo, out = self.setup(tmp, (2, 1, 317), "parent/repo/CLAUDE.md")
            self.assertIn("doesn't import AGENTS.md", out)
            self.assertEqual((repo / "CLAUDE.md").read_text(), "# x\n")

    def test_the_users_own_claude_md_doesnt_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp, "repo")
            repo.mkdir()
            (repo / "AGENTS.md").write_text("# rules\n")
            Path(tmp, ".claude").mkdir()
            Path(tmp, ".claude/CLAUDE.md").write_text("# mine\n")
            with mock.patch.object(install, "version", return_value=(2, 1, 317)), \
                    mock.patch.object(install.shutil, "which", return_value="claude"), \
                    mock.patch.dict(os.environ, {"HOME": tmp, "CLAUDE_CONFIG_DIR": f"{tmp}/.claude"}):
                self.assertIn("Claude reads AGENTS.md here", quietly(install.setup_repo, repo, ["instructing-agents"]))


class InteractiveOrchestration(unittest.TestCase):
    def test_project_fallback_copies_both_claude_agents_and_can_be_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            record = {"id": "orchestrate@ryannel-skills", "installPath": str(ROOT)}
            details = mock.Mock(returncode=1, stdout="", stderr="unknown command 'details'")
            with mock.patch.object(install.subprocess, "run", return_value=details):
                for _ in range(2):
                    quietly(install.link_claude_agents, "claude", record, "project", project)
            agents = project / ".claude" / "agents"
            self.assertEqual(sorted(p.name for p in agents.iterdir()),
                             ["orchestrate-evaluator.md", "orchestrate-planner.md"])
            for agent in agents.iterdir():
                self.assertFalse(agent.is_symlink())
                self.assertIn("Managed by the ryannel/skills", agent.read_text())


if __name__ == "__main__":
    unittest.main()
