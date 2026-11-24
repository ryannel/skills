"""What every `next` the script prints must be, checked on every result line printed while the tests run.

A lead follows `next` as printed, so a `next` that is empty, names an actor other than the lead, drops a flag the lead
gave, leaves a placeholder in a command the lead runs on its own, or sends the lead to `adopt` a builder's unreviewed
work sends the lead wrong. The dogfood run of 23 November 2026 found one of each, and each was fixed alone; these
checks catch the class.

`install` replaces the script's `print` with one that also reads each JSON line it writes to stdout, and `run_step`
with one that reads the line each step's own process printed. Each line is checked with what the command was given:
the `cmd_*` function's arguments, found on the call stack, or a step's words. What breaks a rule goes to `FOUND`,
which `support.Clean` empties before each test and fails the test on after it, so a result added to the script is
checked by the first test that prints it. test_next_invariants tests the checks themselves."""

import argparse
import builtins
import contextlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

FOUND: list[str] = []  # what broke a rule since the test began, one line each
SEEN: list[dict] = []  # every result line checked since the test began, for test_next_invariants

# The fields of a `next` that hold a command line a lead runs. `then` may instead be a whole `next` of its own.
COMMAND_FIELDS = ("command", "then", "alternative", "human")
# Programs other than the script that a `next` may name. Each is a step a lead runs itself in the repository.
SHELL_PROGRAMS = {"git", "cd", "env"}
# The flags that change what a command does, which a `next` re-running the same command must keep, with the
# Namespace field each comes from.
CARRIED = (("--one-step", "one_step"), ("--host", "host"), ("--model", "model"), ("--effort", "effort"))


def subcommands(agent_loop) -> tuple[dict, set]:
    """Each `cmd_*` function's subcommand name, and every name the parser takes, aliases included."""
    parser = agent_loop.build_parser()
    subs = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices
    names = {}
    for name, sub in subs.items():
        if sub.get_default("func"):
            names.setdefault(sub.get_default("func").__name__, name)
    return names, set(subs)


def flag(argv: list[str], name: str):
    """The value of `name` in argv (as `--x v` or `--x=v`), True for a flag with no value, None when absent."""
    for n, w in enumerate(argv):
        if w == name:
            nxt = argv[n + 1] if n + 1 < len(argv) else None
            return nxt if nxt is not None and not nxt.startswith("--") else True
        if w.startswith(name + "="):
            return w.split("=", 1)[1]
    return None


def loop_words(agent_loop, words: list[str]) -> list[list[str]]:
    """The words after the script's path of each script command in a command line's words."""
    out, loop = [], str(agent_loop.LOOP)
    for n, w in enumerate(words):
        if w == loop:
            argv = []
            for x in words[n + 1:]:
                if x in ("&&", "||", ";", "|"):
                    break
                argv.append(x)
            out.append(argv)
    return out


def programs(words: list[str]) -> list[str]:
    """The program each part of a shell chain runs, past any VAR=value in front of it."""
    out, start = [], True
    for w in words:
        if w in ("&&", "||", ";", "|"):
            start = True
            continue
        if start and re.match(r"[A-Z_][A-Z0-9_]*=", w):
            continue
        if start:
            out.append(w)
            start = False
    return out


def same_path(a, b) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except (OSError, TypeError):
        return a == b


def common_dir(tree: str) -> str:
    """The git common directory of a worktree, or the path itself when it isn't one."""
    out = subprocess.run(["git", "-C", tree, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else str(Path(tree).resolve())


def unreviewed_build(agent_loop, tree: str) -> str:
    """Why `tree` is a builder's worktree with commits the main branch doesn't have, or ''."""
    path = Path(tree)
    if not path.is_dir():
        return ""
    run = lambda *a: subprocess.run(["git", "-C", str(path), *a], capture_output=True, text=True)
    branch = run("symbolic-ref", "--quiet", "--short", "HEAD").stdout.strip()
    if not branch.startswith(agent_loop.build_branch("")):
        return ""
    try:
        base = agent_loop.base_ref(agent_loop.profile(path))
    except (Exception, SystemExit):
        return ""
    ahead = run("rev-list", "--count", "HEAD", "--not", base).stdout.strip()
    return f"{tree} is on {branch}, {ahead} commits past {base}" if ahead not in ("", "0") else ""


def caller() -> tuple[str, argparse.Namespace] | None:
    """The outermost `cmd_*` function of the script on the stack, or `run_steps`, and the Namespace it was given."""
    found = None
    frame = sys._getframe(1)
    while frame:
        code = frame.f_code
        if code.co_filename == SCRIPT and (code.co_name.startswith("cmd_") or code.co_name == "run_steps") \
                and code.co_argcount:
            a = frame.f_locals.get(code.co_varnames[0])
            if isinstance(a, argparse.Namespace):
                found = (code.co_name, a)
        frame = frame.f_back
    if found and found[0] == "run_steps":
        func = getattr(found[1], "func", None)
        return (getattr(func, "__name__", "cmd_run"), found[1])
    return found


def check_line(agent_loop, line: dict, given: tuple[str, list[str] | argparse.Namespace] | None,
               step: bool = False) -> list[str]:
    """What in one result line breaks a rule. `given` is (the subcommand, its arguments as a Namespace or as words)
    when known. `step` marks the line of a step a `run` or `plan` ran in its own process."""
    problems = []
    result = line.get("result", "?")
    for where, nxt in nexts(line):
        problems += [f"{result} {where}: {p}" for p in check_next(agent_loop, nxt, given, step)]
    # adopt run for another command (`--then`) hands that command back once it has merged the plan files
    if given and given[0] == "adopt" and result == "ADOPTED" and isinstance(given[1], argparse.Namespace) \
            and getattr(given[1], "then", None):
        command = (line.get("next") or {}).get("command")
        want = shlex.split(given[1].then)[2:]  # past `python3 <script>`, which may now name a newer copy
        if not isinstance(command, str) or shlex.split(command)[2:2 + len(want)] != want:
            problems.append(f"ADOPTED next: doesn't hand back the command adopt was run for: {given[1].then}")
    return problems


def nexts(value, where=""):
    """Each `next` in a result line, nested ones included (`can_start[0].next`, `main_broken[1].next`), with where."""
    if isinstance(value, dict):
        for k, v in value.items():
            here = f"{where}.{k}" if where else k
            if k == "next" and isinstance(v, dict):
                yield here, v
                v = {kk: vv for kk, vv in v.items() if kk not in COMMAND_FIELDS}
            if isinstance(v, (dict, list)):
                yield from nexts(v, here)
    elif isinstance(value, list):
        for n, v in enumerate(value):
            yield from nexts(v, f"{where}[{n}]")


def check_next(agent_loop, nxt: dict, given, step: bool, nested: bool = False) -> list[str]:
    problems = []
    command = nxt.get("command")
    decides = nxt.get("decides")
    # 1. a command the lead can run
    if not isinstance(command, str) or not command.strip():
        problems.append(f"`command` is {command!r}, so the lead has nothing to run")
    if not nested:
        if nxt.get("by") != "lead":
            problems.append(f"`by` is {nxt.get('by')!r}: every command is the lead's to run")
        if not isinstance(nxt.get("why"), str) or not nxt["why"].strip():
            problems.append("`why` is empty")
        if decides not in (None, "human"):
            problems.append(f"`decides` is {decides!r}; only the user decides, as `decides: human`")
        if (decides == "human") != bool(isinstance(nxt.get("ask"), str) and nxt["ask"].strip()):
            problems.append("`decides: human` comes without an `ask`" if decides == "human" else
                            "an `ask` comes without `decides: human`")
    for field in COMMAND_FIELDS:
        value = nxt.get(field)
        if field == "then" and isinstance(value, dict):
            problems += [f"then: {p}" for p in check_next(agent_loop, value, given, step, nested=True)]
            continue
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            problems.append(f"`{field}` is {value!r}")
            continue
        problems += [f"{field}: {p}" for p in check_command(agent_loop, value, nxt if field == "command" else None,
                                                             decides if field != "human" else "human", given, step,
                                                             nxt.get("why") or "")]
    return problems


def check_command(agent_loop, text: str, nxt: dict | None, decides, given, step: bool, why: str = "") -> list[str]:
    problems = []
    try:
        words = shlex.split(text)
    except ValueError as e:
        return [f"isn't valid shell ({e}): {text}"]
    if nxt is not None:
        argv = nxt.get("argv")
        want = (["env", *words] if words and re.match(r"[A-Z_][A-Z0-9_]*=", words[0]) else words)
        if argv != want:
            problems.append(f"`argv` {argv!r} isn't the command's words {want!r}")
    # 2. the script's own commands, or a program a lead runs itself
    names = SUBCOMMANDS_BY_NAME
    for prog in programs(words):
        if prog == "python3":
            continue
        if prog not in SHELL_PROGRAMS:
            problems.append(f"runs {prog!r}, which is neither the script nor a program a `next` may name: {text}")
    pythons = [n for n, w in enumerate(words) if w == "python3"]
    for n in pythons:
        if n + 1 >= len(words) or words[n + 1] != str(agent_loop.LOOP):
            problems.append(f"runs python3 on something other than this copy of the script: {text}")
    for argv in loop_words(agent_loop, words):
        if argv == ["--help"]:  # the script's own help, after a command line naming no command it has
            continue
        if not argv or argv[0] not in names:
            problems.append(f"names no subcommand of the script: {text}")
            continue
        try:
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                PARSER.parse_args(argv)
        except SystemExit as e:
            if e.code not in (0, None):  # `--help` prints the usage and exits 0
                    problems.append(f"the script's parser refuses it: {shlex.join(argv)}")
        problems += check_carried(argv, given, step, text, why)
        # 5. adopt merges what the worktree holds, so a builder's worktree with its own commits is never one
        if argv[0] == "adopt" and isinstance(w := flag(argv, "--worktree"), str):
            if why := unreviewed_build(agent_loop, w):
                problems.append(f"sends the lead to adopt a builder's unreviewed work ({why}): {text}")
        # a worktree a `next` names is one the lead can go to
        if isinstance(w := flag(argv, "--worktree"), str) and not Path(w).is_dir():
            problems.append(f"names a worktree that doesn't exist, {w}: {text}")
    # 4. a placeholder is for the lead to fill with the user's answer. It is a whole word, '<their answer, in their
    # words>'; a `<stash>` inside a task's prose is text. `human` fields count as the user's decision (check_next).
    holes = [w for w in words if agent_loop.PLACEHOLDER.fullmatch(w)]
    if holes and decides != "human" and not documented_placeholder(words, holes):
        problems.append(f"has a placeholder {holes[0]!r} but no `decides: human`: {text}")
    return problems


def documented_placeholder(words: list[str], holes: list[str]) -> bool:
    """A placeholder in a position the script's help (`agent_loop.py --help`, under Results) documents as the lead's
    to fill without the user: `run --message '<the missing fact>'`, the answer to a builder's Needs Context question,
    which the lead gives from what it knows, or takes to a planner or the user, and `builders --why '<...>'`, the
    lead's own reason for raising its working number."""
    return all((h == "<the missing fact>" and n > 0 and words[n - 1] == "--message" and "run" in words[:n]) or
               (n > 0 and words[n - 1] == "--why" and "builders" in words[:n])
               for h in holes for n in [words.index(h)])


# Flags a `next` may drop or change when its `why` says so, each with the words that say it and the reason.
SAID_WHY = {
    # a planner limited to a module that needs others' files: the task goes to a planner for the whole project
    "--module": ("without --module",),
    # a host that failed, or a reviewer that did what a reviewer doesn't: the retry goes to the other host
    "--host": ("other host", "Without --host"),
    "--model": ("other host",),
    "--effort": ("other host",),
}


def check_carried(argv: list[str], given, step: bool, text: str, why: str = "") -> list[str]:
    """3. A `next` that runs the command again, for the same module and work package, keeps the flags that change what
    it does. A step of a longer run has `--one-step` added by the command running the steps, so its own `next` never
    carries it, and neither does a top-level command's `next` when the lead didn't pass it."""
    if not given:
        return []
    sub, a = given
    if argv[0] != sub:
        return []
    get = (lambda dest, f: getattr(a, dest, None)) if isinstance(a, argparse.Namespace) else \
        (lambda dest, f: flag(a, f))
    module, work_package = get("module", "--module"), get("work_package", "--work-package")
    if isinstance(module, list):
        module = module[0] if len(module) == 1 else None
    nm = flag(argv, "--module")
    said = lambda f: any(w in why for w in SAID_WHY.get(f, ()))
    if module and nm is None:
        return [] if said("--module") else [f"drops --module {module} from the command it runs again: {text}"]
    if module and isinstance(nm, str) and nm.upper() != str(module).upper():
        return []  # another module's command, not this one again
    if work_package and isinstance(flag(argv, "--work-package"), str) and flag(argv, "--work-package") != work_package:
        return []
    problems = []
    tree, theirs = get("worktree", "--worktree"), flag(argv, "--worktree")
    if isinstance(tree, str) and isinstance(theirs, str) and not same_path(tree, theirs):
        # another worktree is another target (`migrate --branch` brings each over in turn), but of this repository
        if common_dir(tree) != common_dir(theirs):
            problems.append(f"names {theirs}, which isn't a worktree of {tree}'s repository: {text}")
        return problems
    for f, dest in CARRIED:
        mine = get(dest, f)
        theirs = flag(argv, f)
        if f == "--one-step":
            if step and theirs:
                problems.append(f"a step's `next` carries --one-step, which only the command running the steps "
                                f"adds: {text}")
            elif not step and bool(mine) != bool(theirs):
                problems.append(("drops" if mine else "adds") + f" --one-step: {text}")
            continue
        if mine and theirs != mine and not said(f):
            problems.append(f"{'drops' if theirs is None else 'changes'} {f} {mine}: {text}")
    return problems


def record(agent_loop, line, given, step=False):
    if not isinstance(line, dict) or "result" not in line:
        return
    SEEN.append(line)
    FOUND.extend(check_line(agent_loop, line, given, step))


SCRIPT = ""
PARSER = None
SUBCOMMANDS = {}
SUBCOMMANDS_BY_NAME = set()


def install(agent_loop) -> None:
    """Reads every result line the script prints in this process, and every line a step's process prints."""
    global SCRIPT, PARSER, SUBCOMMANDS, SUBCOMMANDS_BY_NAME
    SCRIPT = agent_loop.__file__
    PARSER = agent_loop.build_parser()
    SUBCOMMANDS, SUBCOMMANDS_BY_NAME = subcommands(agent_loop)

    def given_now():
        found = caller()
        return (SUBCOMMANDS.get(found[0], found[0]), found[1]) if found else None

    def printed(*args, **kw):
        builtins.print(*args, **kw)
        if kw.get("file") not in (None, sys.stdout) or len(args) != 1 or not isinstance(args[0], str):
            return
        text = args[0].strip()
        if not text.startswith("{"):
            return
        try:
            line = json.loads(text)
        except ValueError:
            return
        record(agent_loop, line, given_now())

    agent_loop.print = printed
    run_step = agent_loop.run_step

    def step(words, *a, **kw):
        line = run_step(words, *a, **kw)
        record(agent_loop, line, (words[0], list(words)) if words else None, step=True)
        return line

    agent_loop.run_step = step


def take() -> list[str]:
    """What broke a rule since the last call, and forgets it."""
    out = list(dict.fromkeys(FOUND))
    FOUND.clear()
    SEEN.clear()
    return out
