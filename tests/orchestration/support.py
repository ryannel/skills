"""What every orchestration test shares: a folder of this process's own, the script, the fake host and `Repo`.

Import it first in every test file. Before it imports the script, it points every host, home and state folder the
script reads at that folder, so no test reads the owner's settings or writes under their home folder. A test that
forgets to install a fake host fails at once instead of starting the real CLI.

Tests run many commands in one process, and the script keeps per-process state in module globals. `Clean` puts that
state, the script's settings and the environment back the way they were before each test, so a test passes or fails
the same whichever test ran before it. The parallel runner, run.py, depends on that.

`Repo` gives each test a repository with a bare origin. Building one with git takes about 0.2 s, and some tests need
a long history first, so each process builds the repository once and copies it back for each test. The copy goes to
the same path every time, because the remote's URL, the script's own checkouts and the loop records hold absolute
paths."""

import argparse
import atexit
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills/orchestration/build/scripts"

PROCESS = Path(tempfile.mkdtemp(prefix="orchestrate-tests-"))
atexit.register(shutil.rmtree, PROCESS, True)
CASE = PROCESS / "case"  # the one repository folder each test in this process uses
SAVED = PROCESS / "saved"  # copies of it: the base repository, and the long histories some tests start from

(PROCESS / "gitconfig").write_text("[user]\n\tname = t\n\temail = t@t\n")
os.environ.update(
    CODEX_HOME=str(PROCESS / "codex-home"), CLAUDE_CONFIG_DIR=str(PROCESS / "claude-home"),
    XDG_STATE_HOME=str(PROCESS / "state"), XDG_CACHE_HOME=str(PROCESS / "cache"),
    ORCHESTRATE_LOOPS_DIR=str(PROCESS / "loops"), ORCHESTRATE_CODEX="/no/such/host",
    ORCHESTRATE_CLAUDE="/no/such/host",
    # The owner's git settings (pull.rebase, the LFS filters) never reach the test repositories. The file here
    # gives commits an author, as CI's global settings do.
    GIT_CONFIG_GLOBAL=str(PROCESS / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")
for key in [k for k in os.environ if k.startswith("FAKE_")] + ["ORCHESTRATE_ROLE", "ORCHESTRATE_VISIBLE"]:
    os.environ.pop(key, None)

sys.path.insert(0, str(SCRIPTS))
import agent_loop  # noqa: E402

agent_loop.AGENTS_HOME = PROCESS / "agents-home"
agent_loop.CLAUDE_APP_STORE = PROCESS / "no-claude-desktop"
agent_loop.CODEX_APP_CLI = "/no/such/app"
# Shorter waits than a real run uses. Each is a module setting, so the script behaves the same apart from timing.
agent_loop.RUN_POLL_S = 0.05
agent_loop.MERGE_POLL_S = 0.05
agent_loop.PLANNER_POLL_S = 0.05
agent_loop.LOCK_PATIENCE_S = 0.0

# What each test starts from: the environment, the script's settings, and its per-process state.
ENVIRONMENT = dict(os.environ)
SETTINGS = {module: {name: value for name, value in vars(module).items()
                     if name.strip("_").replace("_", "").isupper() and not callable(value)
                     and not isinstance(value, type(os))}
            for module in (agent_loop, agent_loop.codex_quota)}
STATE = {name: getattr(agent_loop, name) for name in (
    "RUN_HERE", "LIVE", "_LIVE_LOCK", "_RUN_LOCKS", "CONTEXT", "HOSTS_USED", "_COMMON", "QUOTA_WORKTREE",
    "TURN_USAGE", "TURN_SIZE", "TURN_STOP", "WARNINGS", "EMIT_EXTRA", "LAUNCH_HOSTS", "_VERSIONS", "SESSION_PATH",
    "_IMPORTS_SENT", "_HELP")}
assert not any(STATE.values()), "the script's per-process state starts empty"

PROFILE = ("- **Plans:** docs/plans\n- **Merge:** push\n- **Test command:** none\n- **Default host:** codex\n")


def release():
    """What a real process leaves behind when it exits: its run locks, loop record, signal handlers and the state
    it keeps in module globals. Tests run many commands in one process, so they call this after each one. State a
    test has replaced with a patch is left to the patch."""
    agent_loop.loop_end()
    for handle in agent_loop._HELD:
        handle.close()
    agent_loop._HELD.clear()
    agent_loop._STOP = False
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    for name, start in STATE.items():
        if getattr(agent_loop, name) is start:
            start.clear()


def reset():
    """Puts the environment, the script's settings and its state back to what every test starts from."""
    release()
    os.environ.clear()
    os.environ.update(ENVIRONMENT)
    for module, values in SETTINGS.items():
        for name, value in values.items():
            setattr(module, name, value)


class Clean(unittest.TestCase):
    """A test that starts from the same state whichever test ran before it in this process."""

    def setUp(self):
        reset()
        self.addCleanup(reset)


def put(path, text):
    """Writes a plan file, making its module's folder first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def done(*milestones, module="WATER"):
    return {"module": module, "milestones": list(milestones)}


def item(iid, status="open", **proof):
    proof = proof or {"check": "true"}
    return {"id": iid, "statement": f"{iid} works", **proof, "status": status, "evidence": ""}


def milestone(mid, state, statuses, fails=0, **proof):
    items = [item(f"{mid}.{i}", s, **proof) for i, s in enumerate(statuses, 1)]
    return {"id": mid, "name": mid, "state": state, "fails": fails, "replans": 0, "items": items}


def proved(m):
    """The milestone with evidence on every item that passes."""
    for i in m["items"]:
        if i["status"] == "pass":
            i["evidence"] = "docs/evidence/WATER/run.log"
    return m


# The fake host. It is installed as `codex` and as `claude`, and acts as the name it was started under. What it does
# is set by FAKE_ variables: FAKE_PASS passes every item of the first open milestone and merges it, FAKE_REVIEW picks
# a reviewer's verdict, FAKE_PLAN a planner's, and so on below.
FAKE_HOST = """#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
if "--help" in sys.argv:
    print("usage: codex exec [--json]")
    sys.exit(0)
if "--version" in sys.argv:
    print(os.environ.get("FAKE_VERSION", "fake-cli 9.9.9"))
    sys.exit(0)
role = os.environ.get("ORCHESTRATE_ROLE", "build")
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "role": role, "pid": os.getpid(),
                          "api_key": "ANTHROPIC_API_KEY" in os.environ}) + "\\n")
if os.environ.get("FAKE_EXIT"):
    sys.exit(int(os.environ["FAKE_EXIT"]))
if os.environ.get("FAKE_FAIL_RESUME") and os.environ["FAKE_FAIL_RESUME"] in sys.argv[1:-1]:
    print("ERROR: no rollout found for thread id " + os.environ["FAKE_FAIL_RESUME"], file=sys.stderr)
    sys.exit(1)
if os.environ.get("FAKE_ROLLOUT"):  # a Codex session's rollout file gains one token_count event per turn, as real ones do
    contexts = [int(x) for x in os.environ.get("FAKE_CONTEXTS", "40000").split(",")]
    n = sum(1 for _ in open(os.environ["FAKE_LOG"])) - 1
    total = {"input_tokens": 0, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 0,
             "reasoning_output_tokens": 0, "total_tokens": 0}
    if os.path.exists(os.environ["FAKE_ROLLOUT"]):
        for line in open(os.environ["FAKE_ROLLOUT"]):
            info = json.loads(line)["payload"].get("info")
            total = info["total_token_usage"] if info else total
    step = {"input_tokens": 10000 * (n + 1), "cached_input_tokens": 8000 * (n + 1), "output_tokens": 300}
    total = {k: total.get(k, 0) + step.get(k, 0) for k in total}
    last = {"input_tokens": contexts[min(n, len(contexts) - 1)] - 300, "cached_input_tokens": 0, "output_tokens": 300,
            "total_tokens": contexts[min(n, len(contexts) - 1)]}
    with open(os.environ["FAKE_ROLLOUT"], "a") as f:
        f.write(json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": None}}) + "\\n")
        f.write(json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": total, "last_token_usage": last, "model_context_window": 475000}}}) + "\\n")
if os.environ.get("FAKE_SLEEP"):  # a turn the script stops at the turn limit
    import time
    time.sleep(float(os.environ["FAKE_SLEEP"]))
if os.environ.get("FAKE_TOOL_HANG") and "claude" in Path(sys.argv[0]).name and \\
        sum(json.loads(l)["role"] == role for l in open(os.environ["FAKE_LOG"])) == 1:
    # a first turn whose Computer Use call never answers, as two did in Thrum for 98 and 116 minutes
    import time
    sid = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a in ("--session-id", "--resume")), "s1")
    print(json.dumps({"type": "system", "subtype": "init", "session_id": sid,
                      "model": sys.argv[sys.argv.index("--model") + 1]}), flush=True)
    print(json.dumps({"type": "assistant", "session_id": sid, "message": {"content": [
        {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "./dev build"}}]}}), flush=True)
    print(json.dumps({"type": "user", "session_id": sid, "message": {"content": [
        {"type": "tool_result", "tool_use_id": "toolu_1", "content": "built"}]}}), flush=True)
    print(json.dumps({"type": "assistant", "session_id": sid, "message": {"content": [
        {"type": "tool_use", "id": "toolu_2", "name": "mcp__computer-use__screenshot",
         "input": {"app": "Thrum"}}]}}), flush=True)
    time.sleep(float(os.environ["FAKE_TOOL_HANG"]))
    sys.exit(0)
cwd = Path(os.getcwd())
if os.environ.get("FAKE_LOOPS"):  # what `loops` shows while this turn runs
    seen = subprocess.run([sys.executable, os.environ["FAKE_LOOPS_SCRIPT"], "runs", "--json", "--repo", str(cwd)],
                          capture_output=True, text=True)
    with open(os.environ["FAKE_LOOPS"], "a") as out:
        out.write(json.dumps(json.loads(seen.stdout)) + "\\n")
def git(*a):
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          capture_output=True, text=True)
reply = os.environ.get("FAKE_REPLY", "DONE")
path = cwd / "docs/plans/WATER/DONE.json"
if role == "build" and os.environ.get("FAKE_HANDOFF"):
    (cwd / "docs/evidence/WATER").mkdir(parents=True, exist_ok=True)
    (cwd / "docs/evidence/WATER/M1-handoff.md").write_text(os.environ["FAKE_HANDOFF"])
if role == "build" and os.environ.get("FAKE_PASS") == "1":
    d = json.loads(path.read_text())
    for m in d["milestones"]:
        if m["state"] in ("not_started", "in_progress"):
            m["state"] = os.environ.get("FAKE_STATE", "in_progress")
            for i in m["items"]:
                if i.get("needs") and os.environ.get("FAKE_SKIP_NEEDS"):
                    continue
                i["status"], i["evidence"] = "pass", "run log"
                if os.environ.get("FAKE_WEAKEN"):
                    i["check"] = "true"
            if os.environ.get("FAKE_WEAKEN"):
                m["replans"] = m.get("replans", 0) + 1
            break
    if os.environ.get("FAKE_FORGE"):
        last = d["milestones"][-1]
        last["state"] = "done"
        for i in last["items"]:
            i.update(status="pass", evidence="x", verdict="pass", review="x")
    path.write_text(json.dumps(d))
    if os.environ.get("FAKE_COMMIT", "1") == "1":
        git("commit", "-qam", "pass")
        git("pull", "-q", "--rebase", "origin", "main")
        git("push", "-q", "origin", "main")
    if os.environ.get("FAKE_UPSTREAM_BREAK"):
        (cwd / "broken").write_text("x")
        git("add", "broken")
        git("commit", "-qm", "someone else breaks it")
        git("push", "-q", "origin", "main")
        git("reset", "-q", "--hard", "HEAD~1")
elif role == "review":
    mode = os.environ.get("FAKE_REVIEW", "pass")
    if os.environ.get("FAKE_DURING"):  # something lands on the tip while the review runs
        subprocess.run(os.environ["FAKE_DURING"], shell=True, check=True, capture_output=True)
    d = json.loads(path.read_text())
    target = next((m for m in d["milestones"] if m["state"] == "ready_for_review"), None)
    ev = cwd / "docs/evidence/WATER"
    ev.mkdir(parents=True, exist_ok=True)
    if mode == "design":
        (ev / "design-review.md").write_text("design is fine")
        reply = "DESIGN OK"
    elif mode == "design_changes":
        (ev / "design-review.md").write_text("the design needs a second pass")
        reply = "DESIGN CHANGES: the water surface has no LOD plan"
    elif mode == "nothing":
        reply = "PASS M999"
    elif mode == "needs_access":  # a reviewer that can't reach the product, and judges nothing
        (ev / f"{target['id']}-review.md").write_text("couldn't reach the app")
        reply = "The console is locked.\\nBLOCKED needs_access: unlock the Mac's console and approve Computer Use"
    else:
        mid, verdict = target["id"], ("fail" if mode == "fail" else "pass")
        for i in target["items"]:
            i["verdict"], i["review"] = verdict, f"docs/evidence/WATER/{mid}-review.md"
        if verdict == "pass":
            target["state"] = "done"
            if os.environ.get("FAKE_PASS_FINDINGS"):
                target["findings"] = [{"name": "a nit"}]
        else:
            target["state"] = "in_progress"
            target["findings"] = [{"name": os.environ.get("FAKE_FINDING", "the water is flat") + f" ({i['id']})",
                                   "item": i["id"]} for i in target["items"]]
            if os.environ.get("FAKE_DIFFERENT"):
                for f in target["findings"]:
                    f["different"] = os.environ["FAKE_DIFFERENT"]
            if os.environ.get("FAKE_NO_FINDINGS"):
                target.pop("findings")
        if mode == "delete":
            d["milestones"] = [m for m in d["milestones"] if m is target or m["state"] != "not_started"]
        path.write_text(json.dumps(d))
        n = int(target.get("rounds", 0) or 0) + (verdict != "pass")  # the loop counts this round after the fake
        text = f"review of {mid}: {verdict}, failed round {n}"
        if os.environ.get("FAKE_CAPTURE"):
            (ev / f"{mid}-review").mkdir(exist_ok=True)
            (ev / f"{mid}-review" / "shot.png").write_bytes(f"PNG {n}".encode())
            text += f"; see [the shot]({mid}-review/shot.png)"
        (ev / f"{mid}-review.md").write_text(text)
        if mode == "overreach":
            (cwd / "src.txt").write_text("fixed it myself")
        reply = f"PASS {mid}" if verdict == "pass" else f"FAIL {mid}: 1 fail, 0 could_not_judge, 0 outside the items"
elif role == "plan":
    mode = os.environ.get("FAKE_PLAN", "")
    (cwd / "docs/plans/PAY").mkdir(parents=True, exist_ok=True)
    if os.environ.get("FAKE_DURING"):  # something lands on the tip while the planner works
        subprocess.run(os.environ["FAKE_DURING"], shell=True, check=True, capture_output=True)
    if mode == "catch_up":  # the planner brings the tip into its worktree, and writes a test outside the plans
        git("fetch", "-q", "origin")
        git("merge", "-q", "--ff-only", "origin/main")
        (cwd / "acceptance").mkdir(exist_ok=True)
        (cwd / "acceptance/test_pay.py").write_text("assert True\\n")
    turn = sum(json.loads(l)["role"] == "plan" for l in open(os.environ["FAKE_LOG"]))
    files = ["docs/plans/PAY/DONE.json"] + ([] if mode == "nodesign" else ["docs/plans/PAY/DESIGN.md",
                                                                             "docs/plans/PAY/PLAN.md"])
    if mode == "forge":
        (cwd / "docs/plans/WATER/ACCEPTED.json").write_text("{}")
        reply = "PLANNED: docs/plans/WATER/ACCEPTED.json"
    elif mode == "progress" or (mode == "late" and turn == 1):
        reply = "I've read the brief. Next I'll write the PAY design and its done-when file."
    elif mode in ("replan", "replan_counted"):  # re-plans WATER M1; `replan_counted` also does the bookkeeping
        water = cwd / "docs/plans/WATER/DONE.json"
        d = json.loads(water.read_text())
        m = d["milestones"][0]
        m["items"][0]["statement"] = "a smaller first step"
        if mode == "replan_counted":
            m.update(fails=0, replans=m.get("replans", 0) + 1, state="not_started")
        water.write_text(json.dumps(d))
        (cwd / "docs/plans/WATER/DESIGN.md").write_text("# Water design, re-planned")
        reply = "Re-planned M1.\\nPLANNED: docs/plans/WATER/DONE.json, docs/plans/WATER/DESIGN.md"
    elif mode.startswith("keep_"):  # a diagnosis that keeps WATER M1's plan and names who acts
        reply = f"Read every round.\\nKEEP WATER M1: {mode[5:]}: the {mode[5:]} has to act"
    elif mode == "blocked":
        (cwd / "docs/plans/PAY/DESIGN.md").write_text("# Pay design, half done")
        reply = "BLOCKED: the owner must choose the payment provider"
    else:
        if mode != "nodesign":
            (cwd / "docs/plans/PAY/DESIGN.md").write_text("# Pay design")
            (cwd / "docs/plans/PAY/PLAN.md").write_text("# Pay plan" + os.environ.get("FAKE_ASSUME", ""))
        (cwd / "docs/plans/PAY/DONE.json").write_text(json.dumps({"module": "PAY", "milestones": [
            {"id": "M1", "name": "pay", "state": "not_started", "fails": 0, "replans": 0,
             "items": [{"id": "M1.1", "statement": "pays", "check": "true", "status": "open", "evidence": ""}]}]}))
        reply = "Planned PAY. No owner decisions.\\nPLANNED" + ("" if os.environ.get("FAKE_PLAN_BARE") else ": " + ", ".join(files))
        side = os.environ.get("FAKE_PLAN_SIDE")
        if side:  # a planner that forges a record, commits it and puts it on the tip itself, or fakes the tip
            (cwd / "docs/plans/WATER/ACCEPTED.json").write_text('{"forged": true}')
            git("add", "docs/plans/WATER/ACCEPTED.json")
            git("commit", "-qm", "tidy")
            git(*(["push", "-q", "origin", "HEAD:main"] if side == "push" else
                  ["update-ref", "refs/remotes/origin/main", "HEAD"]))
if "claude" in Path(sys.argv[0]).name:
    model = sys.argv[sys.argv.index("--model") + 1]
    sid = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a in ("--session-id", "--resume")), "s1")
    print(json.dumps({"type": "system", "subtype": "init", "session_id": sid, "model": model}))
    result = {"type": "result", "subtype": "success", "session_id": sid, "result": reply, "is_error": False}
    if os.environ.get("FAKE_COST"):  # Claude's total_cost_usd is the session's running total
        result.update(total_cost_usd=float(os.environ["FAKE_COST"]),
                      usage={"input_tokens": 10, "cache_read_input_tokens": 5, "output_tokens": 2})
    print(json.dumps(result))
else:
    print(json.dumps({"type": "thread.started", "thread_id": os.environ.get("FAKE_THREAD", "t1")}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": reply}}))
    if os.environ.get("FAKE_USAGE"):
        print(json.dumps({"type": "turn.completed",
                          "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 7}}))
"""


# The command line. The test helpers turn their keyword arguments into the arguments a lead would type and parse
# them here, so a flag renamed in the parser, or a default changed there, fails the tests.
PARSER = agent_loop.build_parser()
COMMANDS = {sub.get_default("func"): sub
            for sub in next(a for a in PARSER._actions if isinstance(a, argparse._SubParsersAction)).choices.values()}


def parse(func, **kw):
    """The arguments `func`'s command gets when it is typed with these flags (keyword names are the flags'
    destinations). A keyword the command has no flag for fails the test that passed it."""
    sub = COMMANDS[func]
    actions = {a.dest: a for a in sub._actions}
    positional, flags = [], []
    for key, value in kw.items():
        action = actions.get(key)
        if action is None:
            raise AssertionError(f"`{sub.prog}` has no flag for {key}")
        if not action.option_strings:
            positional += value if isinstance(value, list) else [value]
        elif isinstance(action, argparse._StoreTrueAction):
            flags += [action.option_strings[0]] if value else []
        elif value is not None:
            for v in value if isinstance(value, list) else [value]:
                flags.append(f"{action.option_strings[0]}={v}")
    return parse_argv(sub, [*flags, *[str(p) for p in positional]])


def parse_argv(parser, argv):
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            return parser.parse_args(argv)
    except SystemExit:
        raise AssertionError(f"{shlex.join(argv)} doesn't parse: {err.getvalue().strip()}") from None


def check_next_commands(result):
    """Every `next` command a result line gives must be one the script's own parser accepts, so a lead running it
    never meets a flag that doesn't exist."""
    if isinstance(result, list):
        for x in result:
            check_next_commands(x)
    if not isinstance(result, dict):
        return
    for key, value in result.items():
        if key == "next" and isinstance(value, dict):
            for field in ("command", "then", "alternative", "owner"):
                text = value.get(field)
                if isinstance(text, str) and str(agent_loop.LOOP) in text and \
                        (field in ("command", "then") or text.startswith(("python3 ", "ORCHESTRATE_"))):
                    for argv in loop_commands(text):
                        parse_argv(PARSER, argv)
        check_next_commands(value)


def loop_commands(text):
    """The arguments of each `agent_loop.py` command in a shell command line, which must be one a lead can paste:
    the shell must parse it, and a placeholder such as '<what the owner said, in their words>' must be quoted, so
    it reaches the script as one word. In 2.1.0 a placeholder with an apostrophe in it ended its own quotes."""
    try:
        words = shlex.split(text)
    except ValueError as e:
        raise AssertionError(f"this command isn't valid shell ({e}): {text}") from None
    broken = [p for p in re.findall(r"(?<!\S)'(<[^<>]*>)'(?!\S)", text) if p not in words]
    if broken:
        raise AssertionError(f"the shell splits the placeholder {broken[0]!r} in this command: {text}")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    redirects = [t for t in lexer if t and set(t) <= set("<>")]
    if redirects:
        raise AssertionError(f"this command has a placeholder the shell would read as a redirection: {text}")
    out = []
    for n, word in enumerate(words):
        if word == str(agent_loop.LOOP):
            argv = []
            for w in words[n + 1:]:
                if w in ("&&", "||", ";", "|"):
                    break
                argv.append(w)
            out.append(argv)
    return out


def copy_case(source, target):
    """Copies a case folder, symbolic links as links. Copying files keeps their modification times."""
    partial = target.with_name(target.name + ".partial")
    shutil.copytree(source, partial, symlinks=True)
    partial.rename(target)


def clear_case():
    """Removes the case folder. It is moved aside first, so a process a test left running can't stop it going."""
    if CASE.exists():
        aside = Path(tempfile.mkdtemp(prefix="old-case-", dir=PROCESS))
        CASE.rename(aside / "case")
        shutil.rmtree(aside, ignore_errors=True)


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def build_base():
    """The repository every `Repo` test starts from: a bare origin, a worktree with WATER planned and authorised,
    and the fake host installed as `codex` and as `claude`."""
    CASE.mkdir()
    wt, origin = CASE / "wt", CASE / "origin.git"
    (CASE / "codex-home").mkdir()
    sh("git", "init", "-q", "--bare", "-b", "main", str(origin))
    sh("git", "init", "-q", "-b", "main", str(wt))
    sh("git", "-C", str(wt), "config", "user.name", "t")
    sh("git", "-C", str(wt), "config", "user.email", "t@t")
    (wt / "docs/plans").mkdir(parents=True)
    (wt / "ORCHESTRATE.md").write_text(PROFILE)
    doc = done(milestone("M1", "not_started", ["open"]), milestone("M2", "not_started", ["open"]))
    put(wt / "docs/plans/WATER/DONE.json", json.dumps(doc))
    rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
    rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)}
    put(wt / "docs/plans/WATER/ACCEPTED.json", json.dumps(rec))
    sh("git", "-C", str(wt), "add", "-A")
    sh("git", "-C", str(wt), "commit", "-qm", "init")
    sh("git", "-C", str(wt), "remote", "add", "origin", str(origin))
    sh("git", "-C", str(wt), "push", "-q", "origin", "main")
    for name in ("codex", "claude"):
        (CASE / name).write_text(FAKE_HOST)
        (CASE / name).chmod(0o755)
    SAVED.mkdir(exist_ok=True)
    copy_case(CASE, SAVED / "base")


def shares(*names):
    """Marks a test that starts from the saved repositories named, which `Repo.restore` builds once per process.
    The parallel runner, run.py, runs the tests that share one in the same process, so it is built once in all."""
    def mark(test):
        test.shares = names
        return test
    return mark


class Repo(Clean):
    """A repository with a bare origin, the fake host as both `codex` and `claude`, and a module, WATER, whose plan
    is authorised. Every test in a process gets it at the same path, copied from the one built first."""

    def setUp(self):
        super().setUp()
        clear_case()
        if (SAVED / "base").exists():
            copy_case(SAVED / "base", CASE)
        else:
            build_base()
        self.root, self.wt, self.origin, self.home = CASE, CASE / "wt", CASE / "origin.git", CASE / "codex-home"
        self.log = CASE / "log"
        self.loops = CASE / "loops"
        agent_loop.CODEX, agent_loop.CLAUDE = str(CASE / "codex"), str(CASE / "claude")
        agent_loop.CODEX_HOME, agent_loop.CLAUDE_HOME = self.home, CASE / "claude-home"
        agent_loop.AGENTS_HOME, agent_loop.LOOPS_DIR = CASE / "agents-home", self.loops
        agent_loop.codex_quota.CACHE_DIR = CASE / "quota-cache"
        # Loop records go to this test's folder, for the loop in this process and for any process it starts.
        os.environ.update(ORCHESTRATE_LOOPS_DIR=str(self.loops), FAKE_LOG=str(self.log), FAKE_PASS="1",
                          FAKE_REPLY="DONE", FAKE_COMMIT="1")
        # Goal changes never reach a real Codex app-server; tests read what the script asked for here.
        self.goal_changes = []
        goals = mock.patch.object(agent_loop, "codex_goal_activate",
                                  lambda t, status="active": self.goal_changes.append(status) or True)
        goals.start()
        self.addCleanup(goals.stop)

    def restore(self, name, build):
        """Runs `build` on this test's repository and returns what it returns, or, when a test in this process has
        already run it with the same FAKE_ settings, copies back the repository it left and returns the same. A
        build must leave the environment as it found it, because the copy keeps files, not the process."""
        fakes = sorted((k, v) for k, v in os.environ.items() if k.startswith("FAKE_"))
        saved = SAVED / f"{name}-{hashlib.sha1(json.dumps(fakes).encode()).hexdigest()[:12]}"
        answer = CASE / "restored.json"
        if saved.exists():
            clear_case()
            copy_case(saved, CASE)
        else:
            out = build()
            self.assertEqual(sorted((k, v) for k, v in os.environ.items() if k.startswith("FAKE_")), fakes,
                             f"{name} changed the FAKE_ settings")
            answer.write_text(json.dumps(out))
            copy_case(CASE, saved)
            answer.unlink()
            return out
        out = json.loads(answer.read_text())
        answer.unlink()
        return out

    def sh(self, *args, cwd=None):
        return sh(*args, cwd=cwd)

    def git(self, *args, where=None):
        return self.sh("git", "-C", str(where or self.wt), *args)

    def write_done(self, milestones, design_ok=True, authorise=True, module="WATER", where=None, ready=()):
        """Writes the done-when file and, as a planner turn through the loop would, its acceptance record. Each
        milestone named in `ready` also gets the Ready for Review record the script writes after its checks pass."""
        where = where or self.wt
        doc = done(*milestones, module=module)
        put(where / f"docs/plans/{module}/DONE.json", json.dumps(doc))
        if authorise:
            rec = agent_loop.adopt(doc, agent_loop.text_hash(None))
            rec["design"] = {"verdict": "ok", "hash": agent_loop.text_hash(None)} if design_ok else None
            for mid in ready:
                rec["milestones"][mid]["ready_for_review"] = {"at": agent_loop.now(), "checks": []}
            put(where / f"docs/plans/{module}/ACCEPTED.json", json.dumps(rec))

    def ready_for_review(self, m1=None):
        """Merges M1 as the script leaves it once its checks pass: Ready for Review, every item passing with
        evidence, and the record saying so. Returns the commit, for a review. It stands in for a builder turn
        (1.9 s) where a test only needs something to review (0.2 s)."""
        m1 = m1 or milestone("M1", "ready_for_review", ["pass"], inspect="frame sequence")
        m1["state"] = "ready_for_review"
        for i in m1["items"]:
            i["status"] = "pass"
        self.write_done([proved(m1), milestone("M2", "not_started", ["open"])], ready=("M1",))
        self.commit_all()
        work = agent_loop.head_commit(self.wt)
        record = self.wt / "docs/plans/WATER/ACCEPTED.json"
        rec = json.loads(record.read_text())
        rec["milestones"]["M1"]["ready_for_review"]["commit"] = work
        record.write_text(json.dumps(rec))
        self.commit_all()
        return work

    def read_done(self, ref="origin/main"):
        self.git("fetch", "-q", "origin")
        return json.loads(self.git("show", f"{ref}:docs/plans/WATER/DONE.json").stdout)

    def read_record(self, ref="origin/main"):
        self.git("fetch", "-q", "origin")
        return json.loads(self.git("show", f"{ref}:docs/plans/WATER/ACCEPTED.json").stdout)

    def commit_all(self, where=None):
        where = where or self.wt
        self.git("add", "-A", where=where)
        self.git("commit", "-qm", "x", where=where)
        self.git("pull", "-q", "--rebase", "origin", "main", where=where)
        self.git("push", "-q", "origin", "main", where=where)

    def call(self, func, **kw):
        """Runs a command as the lead would type it, and returns its result line. Every `next` command in the
        result must parse."""
        args = parse(func, **kw) if func in COMMANDS else argparse.Namespace(**kw)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
                func(args)
        finally:
            release()
        result = json.loads(out.getvalue().splitlines()[-1])
        check_next_commands(result)
        return result

    def printed(self, func, code=None, **kw):
        """What a command prints. With `code`, the command must exit with it."""
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                if code is None:
                    func(parse(func, **kw))
                else:
                    with self.assertRaises(SystemExit) as stop:
                        func(parse(func, **kw))
                    self.assertEqual(stop.exception.code, code)
        finally:
            release()
        return out.getvalue()

    def run_loop(self, **kw):
        args = dict(module="WATER", worktree=str(self.wt), budget_hours=4.0, turn_timeout_hours=0.1)
        args.update(kw)
        return self.call(agent_loop.cmd_run, **args)

    def review(self, milestone_id="M1", commit="HEAD", **kw):
        args = dict(module="WATER", milestone=milestone_id, commit=commit, worktree=str(self.wt),
                    turn_timeout_hours=0.1)
        args.update(kw)
        return self.call(agent_loop.cmd_review, **args)

    def plan(self, **kw):
        args = dict(worktree=str(self.wt), task="plan PAY", turn_timeout_hours=0.1)
        args.update(kw)
        return self.call(agent_loop.cmd_plan, **args)

    def adopt(self, *paths):
        return self.call(agent_loop.cmd_adopt, worktree=str(self.wt), paths=list(paths))

    def ready(self, where=None):
        return json.loads(self.printed(agent_loop.cmd_ready, worktree=str(where or self.wt)))

    def owner(self, action, milestone_id, reason="owner said so", where=None, item=None, asked=None):
        """An owner command. For `feedback`, `reason` is what the owner said and `asked` the lead's question."""
        feedback = action == "feedback"
        return self.call(agent_loop.cmd_owner, action=action, module="WATER", milestone=milestone_id,
                         item=[item] if isinstance(item, str) else item, worktree=str(where or self.wt),
                         text=None if feedback else reason, said=reason if feedback else None,
                         asked=(asked or "Which direction do you want?") if feedback else None)

    def refused_feedback(self, mid, items, said="approved it"):
        """The error `owner feedback` stops with."""
        try:
            with self.assertRaises(SystemExit) as stop, contextlib.redirect_stdout(io.StringIO()):
                agent_loop.cmd_owner(parse(agent_loop.cmd_owner, action="feedback", module="WATER", milestone=mid,
                                           item=items, said=said, asked="Is it right?", worktree=str(self.wt)))
        finally:
            release()
        return str(stop.exception)

    def migrate(self):
        return self.call(agent_loop.cmd_migrate, worktree=str(self.wt))

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def prompt(self, call):
        argv = call["argv"]
        return argv[argv.index("-p") + 1] if "-p" in argv else argv[-1]

    def state(self):
        return json.loads((self.wt / ".git/orchestrate/WATER.json").read_text())
