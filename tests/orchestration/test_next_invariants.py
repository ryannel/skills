"""The rules every `next` the script prints must keep, and the checks that hold every test to them.

support.py installs invariants.py, which reads every result line the script prints while any test runs, and fails
the test on a `next` that breaks a rule, so a result path any test reaches is checked, new ones included. This module
tests that each check catches what it is for (the dogfood run of 23 November 2026 found one of each class), and walks
the commands no other test runs on a plain repository, so their results are checked too.

The rules: every `next` (its `then` and `alternative` too) has a non-empty command that the shell parses, whose `argv`
is its words, and that runs this copy of the script with a subcommand and flags its parser takes, or one of the few
programs a lead runs itself; `by` is the lead, `why` says why, `decides: human` comes with an `ask` and an `ask` only
with it; a command run again for the same module and milestone keeps the caller's --one-step, --module, --host, --model and
--effort unless its `why` says why not, and gains no --one-step the caller didn't pass; a `--worktree` exists and
belongs to the caller's repository; `adopt` given `--then` hands it back; a placeholder appears only in a command the
user decides, in `human`, or as `run --message '<the missing fact>'`; and no `next` sends the lead to `adopt` a
builder's worktree with commits the main branch doesn't have."""

import argparse
import contextlib
import io
import json
import os
import shlex
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import PROFILE, Clean, Repo, agent_loop, milestone, put  # noqa: E402
import invariants  # noqa: E402

LOOP = str(agent_loop.LOOP)


def nxt(*words, **more):
    command = shlex.join(["python3", LOOP, *words])
    return agent_loop.fit_next(agent_loop.next_cmd(command, "lead", "because", **more))


def problems(line, given=None, step=False):
    return invariants.check_line(agent_loop, line, given, step)


def ns(**kw):
    return argparse.Namespace(**{"one_step": False, "host": None, "model": None, "effort": None, **kw})


class EachCheckCatchesItsClass(Clean):
    """Each check, fed a `next` of the kind the dogfood run found, names it; a sound `next` passes them all."""

    def setUp(self):
        super().setUp()
        self.wt = os.getcwd()

    def test_a_sound_next_passes(self):
        line = {"result": "READY", "next": nxt("ready", "--worktree", self.wt)}
        self.assertEqual(problems(line), [])

    def test_a_next_with_no_command(self):
        line = {"result": "REVIEWED", "next": agent_loop.next_cmd(None, "lead", "finished")}
        self.assertTrue(any("nothing to run" in p for p in problems(line)), problems(line))

    def test_a_next_for_another_actor(self):
        line = {"result": "DESIGN_NOT_APPROVED", "next": dict(nxt("status", "--worktree", self.wt), by="planner")}
        self.assertTrue(any("`by` is 'planner'" in p for p in problems(line)), problems(line))

    def test_a_decision_without_a_question_and_a_question_without_a_decision(self):
        asked = {"result": "X", "next": nxt("status", "--worktree", self.wt, decides="human")}
        self.assertTrue(any("without an `ask`" in p for p in problems(asked)), problems(asked))
        told = {"result": "X", "next": nxt("status", "--worktree", self.wt, ask="Shall I?")}
        self.assertTrue(any("without `decides: human`" in p for p in problems(told)), problems(told))

    def test_a_retry_that_drops_one_step_or_another_flag(self):
        given = ("plan", ns(worktree=self.wt, one_step=True, model="m-1", effort="low"))
        line = {"result": "INVALID", "next": nxt("plan", "--worktree", self.wt, "--task", "t", "--model", "m-1")}
        found = problems(line, given)
        self.assertTrue(any("drops --one-step" in p for p in found), found)
        self.assertTrue(any("drops --effort low" in p for p in found), found)
        self.assertFalse(any("--model" in p.split(":")[1] for p in found if "drops" in p), found)

    def test_a_retry_in_another_worktree_or_without_the_module(self):
        given = ("run", ns(worktree=self.wt, module="WATER"))
        moved = {"result": "PAUSED", "next": nxt("run", "--worktree", "/", "--module", "WATER")}
        self.assertTrue(any("isn't a worktree of" in p for p in problems(moved, given)), problems(moved, given))
        dropped = {"result": "PAUSED", "next": nxt("run", "--worktree", self.wt)}
        self.assertTrue(any("drops --module WATER" in p for p in problems(dropped, given)))
        other = {"result": "REVIEWED", "next": nxt("run", "--worktree", self.wt, "--module", "PAY")}
        self.assertEqual(problems(other, given), [], "another module's run is not this one again")

    def test_one_step_the_caller_never_passed(self):
        line = {"result": "INVALID", "next": nxt("plan", "--worktree", self.wt, "--task", "t", "--one-step")}
        self.assertTrue(any("adds --one-step" in p for p in problems(line, ("plan", ns(worktree=self.wt)))))
        # a step's own `next` never carries it: the command running the steps adds it
        step = ("plan", ["plan", "--worktree", self.wt, "--task", "t", "--one-step"])
        self.assertTrue(any("only the command running the steps" in p for p in problems(line, step, step=True)))

    def test_adopt_that_forgets_its_then(self):
        then = shlex.join(["python3", LOOP, "plan", "--worktree", self.wt, "--task", "t", "--one-step"])
        line = {"result": "ADOPTED", "next": nxt("ready", "--worktree", self.wt)}
        found = problems(line, ("adopt", ns(worktree=self.wt, then=then)))
        self.assertTrue(any("doesn't hand back" in p for p in found), found)

    def test_a_placeholder_the_lead_cant_fill(self):
        line = {"result": "X", "next": nxt("pause", "--worktree", self.wt, "--module", "<M>")}
        self.assertTrue(any("placeholder '<M>'" in p for p in problems(line)), problems(line))
        asked = {"result": "X", "next": nxt("pause", "--worktree", self.wt, "--module", "<M>", decides="human",
                                            ask="Which module?")}
        self.assertEqual(problems(asked), [])

    def test_the_documented_exceptions_pass(self):
        # `human` is the command that records the user's decision, so its placeholder is the user's words
        line = {"result": "X", "next": dict(nxt("ready", "--worktree", self.wt), human=shlex.join(
            ["python3", LOOP, "human", "release", "--module", "WATER", "--milestone", "M1", "--worktree", self.wt,
             "--text", "<what the user said, in their words>"]))}
        self.assertEqual(problems(line), [])
        # a builder's Needs Context question is the lead's to answer first, as the script's help says
        line = {"result": "BLOCKED", "next": nxt("run", "--module", "WATER", "--worktree", self.wt, "--message",
                                                 "<the missing fact>")}
        self.assertEqual(problems(line), [])
        # a scoped planner that needs other modules' files: the task goes to a planner for the whole project
        given = ("plan", ns(worktree=self.wt, module="PAY"))
        line = {"result": "INVALID", "next": agent_loop.fit_next(agent_loop.next_cmd(
            shlex.join(["python3", LOOP, "plan", "--worktree", self.wt, "--task", "t"]), "lead",
            "again, without --module, so it may change every module it needs to"))}
        self.assertEqual(problems(line, given), [])

    def test_argv_that_isnt_the_command(self):
        line = {"result": "X", "next": dict(nxt("status", "--worktree", self.wt), argv=["python3", LOOP, "ready"])}
        self.assertTrue(any("isn't the command's words" in p for p in problems(line)), problems(line))

    def test_a_command_the_parser_or_the_shell_refuses(self):
        for words, why in ((["status", "--no-such-flag"], "parser refuses"), (["frobnicate"], "no subcommand")):
            line = {"result": "X", "next": nxt(*words)}
            self.assertTrue(any(why in p for p in problems(line)), problems(line))
        bad = {"result": "X", "next": {"command": "python3 'unclosed", "by": "lead", "why": "w"}}
        self.assertTrue(any("isn't valid shell" in p for p in problems(bad)), problems(bad))
        other = {"result": "X", "next": {"command": "rm -rf build", "argv": ["rm", "-rf", "build"], "by": "lead",
                                         "why": "w"}}
        self.assertTrue(any("runs 'rm'" in p for p in problems(other)), problems(other))

    def test_nested_nexts_and_then_are_checked(self):
        line = {"result": "READY", "next": nxt("ready", "--worktree", self.wt),
                "can_start": [{"module": "WATER", "next": {"command": None, "by": "lead", "why": "w"}}]}
        self.assertTrue(any(p.startswith("READY can_start[0].next:") for p in problems(line)), problems(line))
        line = {"result": "X", "next": dict(nxt("status", "--worktree", self.wt),
                                            then={"command": None, "by": "lead", "why": "w"})}
        self.assertTrue(any("then: `command` is None" in p for p in problems(line)), problems(line))


class AdoptOfABuildersWork(Repo):
    """A builder's worktree holds commits no review has passed; `adopt` there would merge them to main."""

    def test_adopt_in_a_builders_worktree_with_its_own_commits_is_caught(self):
        (self.wt / "ORCHESTRATE.md").write_text(PROFILE + "- **Worktrees:** .orchestrate/worktrees\n")
        self.write_done([milestone("M1", "not_started", ["open"])])
        self.commit_all()
        built, _ = agent_loop.module_worktree(self.wt, agent_loop.profile(self.wt), "WATER")
        line = {"result": "X", "next": nxt("adopt", "--worktree", str(built))}
        self.assertEqual(problems(line), [], "a builder's worktree with nothing of its own yet is harmless")
        put(built / "src/water.py", "print('water')\n")
        self.git("add", "-A", where=built)
        self.git("commit", "-qm", "WATER M1: water", where=built)
        self.assertTrue(any("adopt a builder's unreviewed work" in p for p in problems(line)), problems(line))


class EveryCommandOnAPlainRepository(Repo):
    """The commands no other test needs a scenario for, each run as the lead would type it, so every result line
    they print goes through the checks."""

    def lines(self):
        return [l for l in invariants.SEEN if isinstance(l, dict)]

    def run_argv(self, *words):
        """Runs the script's own main() as `python3 agent_loop.py <words>` would, for the paths that start there:
        a command line the parser refuses, and `run` and `plan` going through their steps."""
        out = io.StringIO()
        with mock.patch.object(sys, "argv", [LOOP, *words]), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                agent_loop.main()
            except SystemExit:
                pass
            finally:
                from support import release
                release()
        return [json.loads(l) for l in out.getvalue().splitlines() if l.startswith("{")]

    def test_reading_commands(self):
        wt = str(self.wt)
        for func, kw in ((agent_loop.cmd_ready, {}), (agent_loop.cmd_status, {}),
                         (agent_loop.cmd_next, {"module": "WATER"}),
                         (agent_loop.cmd_next, {"module": "WATER", "milestone": "M1"}),
                         (agent_loop.cmd_settings, {}), (agent_loop.cmd_locks, {}),
                         (agent_loop.cmd_cleanup, {"json": True}), (agent_loop.cmd_main_check, {}),
                         (agent_loop.cmd_adopt, {"paths": []}), (agent_loop.cmd_migrate, {})):
            with self.subTest(command=func.__name__, **{k: str(v) for k, v in kw.items()}):
                try:
                    self.printed(func, worktree=wt, **kw)
                except AssertionError:
                    with contextlib.suppress(AssertionError):
                        self.printed(func, code=1, worktree=wt, **kw)
        self.assertTrue(any(l.get("next") for l in self.lines()), "the walk printed no `next` to check")

    def test_a_command_line_the_parser_refuses(self):
        [line] = self.run_argv("run", "--worktree", str(self.wt), "--modul", "WATER")
        self.assertEqual(line["result"], "ERROR", line)
        self.assertEqual(problems(line), [])
        self.assertIn(line, self.lines())

    def test_a_run_through_its_steps(self):
        lines = self.run_argv("run", "--worktree", str(self.wt), "--module", "WATER", "--turn-timeout-hours", "0.1")
        self.assertTrue(lines and lines[-1].get("steps_run"), lines)
        self.assertGreater(len(self.lines()), 1, "each step's own line is checked too")


if __name__ == "__main__":
    unittest.main()
