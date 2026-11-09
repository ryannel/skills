"""The instructing-agents handoff hook: which Bash commands count as a launch, and the once-per-context refusal."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "skills/instructing-agents/hooks/handoff_nudge.py"
spec = importlib.util.spec_from_file_location("handoff_nudge", HOOK)
nudge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nudge)

LAUNCHES = [
    "codex exec 'fix the build'",
    "codex e task",
    "cd repo && codex exec -",
    "codex -m gpt-6.1-sol exec task",
    "codex --full-auto exec task",
    'claude -p "review this"',
    "claude --print task",
    "claude --model claude-opus-5-5 -p task",
    "echo hello\ncodex exec task",
    "timeout 600 claude -p task",
    "CLAUDE_CONFIG_DIR=/x claude -p task",
    'FOO="a b" codex exec task',
    "env -u X CODEX_HOME=/y codex exec task",
    "nohup claude -p task > out.log &",
    "/usr/local/bin/codex exec task",
    "x=$(claude -p summarise)",
    "if true; then codex exec task; fi",
    "python3 ~/Workspace/codexctl/codexctl.py send core 'hold'",
    "cat brief.md | claude -p",
    "cat <<EOF | codex exec -\nthe brief\nEOF",
]
NOT_LAUNCHES = [
    'git commit -m "note: run tests && codex exec later"',
    "git commit -m 'mention claude -p in prose'",
    'echo "{\\"cmd\\": \\"codex exec task\\"}"',
    "grep -rn 'claude -p' docs",
    "claude --version",
    "claude plugin list",
    "codex plugin add x@y",
    "python3 skills/orchestration/build/scripts/agent_loop.py run --message 'Owner boundary'",
    "ls codex-exec-notes",
    "cat > notes.md <<'EOF'\nclaude -p in a heredoc body is text\nEOF",
    "python3 - <<EOF\ncodex exec task\nEOF\necho done",
]


class Matching(unittest.TestCase):
    def test_documented_launch_spellings_match(self):
        for command in LAUNCHES:
            self.assertTrue(nudge.launches(command), command)

    def test_quoted_text_and_other_commands_pass(self):
        for command in NOT_LAUNCHES:
            self.assertFalse(nudge.launches(command), command)


class Refusal(unittest.TestCase):
    def run_hook(self, payload, state):
        env = {**os.environ, "CLAUDE_PLUGIN_DATA": state, "INSTRUCTING_AGENTS_NUDGE_SKIP": ""}
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, capture_output=True,
                           env=env)
        self.assertEqual(r.returncode, 0)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else "pass"

    def test_first_launch_refused_once_then_passes_and_unrelated_commands_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp, "t.jsonl")
            transcript.write_text("{}\n")
            base = {"session_id": "s", "transcript_path": str(transcript), "cwd": tmp, "tool_name": "Bash"}
            quoted = {**base, "tool_input": {"command": 'git commit -m "x && codex exec y"'}}
            launch = {**base, "tool_input": {"command": "timeout 60 claude -p task"}}
            self.assertEqual(self.run_hook(quoted, tmp), "pass")
            self.assertEqual(self.run_hook(launch, tmp), "deny")
            self.assertEqual(self.run_hook(launch, tmp), "pass")
            with transcript.open("a") as f:
                f.write('{"type":"system","subtype":"compact_boundary"}\n')
            self.assertEqual(self.run_hook(launch, tmp), "deny")

    def test_bad_input_fails_open(self):
        r = subprocess.run([sys.executable, str(HOOK)], input="not json", text=True, capture_output=True)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
