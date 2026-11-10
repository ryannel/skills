#!/usr/bin/env python3
"""Runs the conversation test cases for `interview-me` and `domain-language`.

Each run is one conversation between two headless Claude Code sessions. One is the agent under test. The other
plays the owner from the case's `owner.md`. This program passes each message from one to the other and saves the
conversation as `transcript.md`.

Usage: run_conversations.py <round folder> <scratch folder> <copy of skills/orchestration> [case/side ...]

Each headless session spends the plan's quota. The copy of the skills gets a stand-in for `agent_loop.py` that
refuses `plan`, `run` and `review`, so a conversation can't go on to start planners, builders and reviewers.
"""
import json
import shutil
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CASES = {
    # case: (folder of the case, skill under test, stop when the owner approves)
    "clear-small-request": ("workbench/intent-conversation/evals", "interview-me", False),
    "vague-new-product": ("workbench/intent-conversation/evals", "interview-me", True),
    "existing-project-new-feature": ("workbench/intent-conversation/evals", "interview-me", True),
    "tangled-terms": ("workbench/domain-language/evals", "domain-language", False),
    "new-name-mid-task": ("workbench/domain-language/evals", "domain-language", False),
    "small-tool": ("workbench/domain-language/evals", "domain-language", False),
}
MAX_OWNER_REPLIES = 12
TURN_TIMEOUT = 1500
CLAUDE = shutil.which("claude")
# The model a headless session used by default on the day of the first round. Named so that both sides match.
MODEL = "claude-fable-5-2"

CHAT_NOTE = ("Each reply you write is sent to the owner as a chat message, and the owner's answer comes back as "
             "your next message.")
OWNER_TAGS = """

After your message, write one more line that holds exactly one of these tags:

- `[[APPROVED]]` if the agent's last message showed you a whole written brief or a whole glossary, and your
  message says it is right. A yes to one question, or to one choice, is `[[REPLY]]`.
- `[[NO_REPLY]]` if the agent's last message asks you nothing and says its work is finished. Write nothing
  before the tag in that case.
- `[[REPLY]]` in every other case.

You asked for one thing, in your first message. When the agent has done it and offers further work that you did
not ask for, the conversation is over: use `[[NO_REPLY]]`.
"""


def claude(args, prompt, cwd):
    proc = subprocess.run([CLAUDE, "-p", "--setting-sources", "project", "--output-format", "json", *args],
                          input=prompt, cwd=cwd, capture_output=True, text=True, timeout=TURN_TIMEOUT)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"result": "", "is_error": True, "raw": proc.stdout[-2000:] + proc.stderr[-2000:]}


def run(case, side, round_dir, scratch, skills_copy):
    evals, skill, stop_at_approval = CASES[case]
    case_dir = REPO / evals / case
    out = round_dir / case / side / "run-1"
    work = scratch / case / side / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    out.mkdir(parents=True, exist_ok=True)
    if (case_dir / "place-files.sh").exists():
        subprocess.run(["sh", str(case_dir / "place-files.sh")], cwd=work, check=True)

    request = (case_dir / "prompt.md").read_text().split("---", 2)[2].strip()
    owner_page = (case_dir / "owner.md").read_text() if (case_dir / "owner.md").exists() else None

    notes = []
    if owner_page:
        notes.append(CHAT_NOTE)
    if side == "with_skill":
        notes.append(f"A skill for this kind of request is in the folder {skills_copy / skill}. "
                     "Read its SKILL.md before you reply, and follow it.")
    session = str(uuid.uuid4())
    base = ["--permission-mode", "acceptEdits", "--allowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "Skill", "--max-turns", "80", "--model", MODEL]
    if notes:
        base += ["--append-system-prompt", " ".join(notes)]

    transcript = [("Owner", request)]
    meta = {"case": case, "side": side, "skill": skill, "session": session, "turns": [], "ended": None}
    message, first = request, True
    while True:
        args = base + (["--session-id", session] if first else ["--resume", session])
        first = False
        reply = claude(args, message, work)
        meta["turns"].append({k: reply.get(k) for k in
                              ("duration_ms", "num_turns", "total_cost_usd", "is_error", "subtype", "raw")
                              if reply.get(k) is not None}
                             | {"models": sorted((reply.get("modelUsage") or {}).keys()),
                                "output_tokens": (reply.get("usage") or {}).get("output_tokens")})
        transcript.append(("Agent", reply.get("result") or "(no reply)"))
        if reply.get("is_error") or not owner_page:
            meta["ended"] = "error" if reply.get("is_error") else "the case has no owner"
            break
        owner_replies = sum(1 for who, _ in transcript if who == "Owner") - 1
        if owner_replies >= MAX_OWNER_REPLIES:
            meta["ended"] = f"{MAX_OWNER_REPLIES} owner replies used"
            break
        shown = "\n\n".join(f"{who}:\n{text}" for who, text in transcript)
        answer = claude(["--model", "sonnet", "--tools", "", "--system-prompt", owner_page + OWNER_TAGS],
                        f"The conversation so far:\n\n{shown}\n\nWrite the owner's next message.",
                        scratch)
        text = (answer.get("result") or "").strip()
        tag = "REPLY"
        for t in ("APPROVED", "NO_REPLY", "REPLY"):
            if f"[[{t}]]" in text:
                tag, text = t, text.replace(f"[[{t}]]", "").strip()
                break
        if tag == "NO_REPLY" or not text:
            meta["ended"] = "the agent finished and asked nothing"
            break
        transcript.append(("Owner", text))
        # A yes to a single question was once tagged as an approval, so the agent's message must be page-sized.
        if tag == "APPROVED" and stop_at_approval and len(transcript[-2][1]) > 1500:
            meta["ended"] = "the owner approved; the approval was not passed to the agent"
            break
        message = text

    (out / "transcript.md").write_text(
        f"# {case}, {side.replace('_', ' ')}\n\n" + "\n\n".join(f"## {who}\n\n{text}" for who, text in transcript)
        + f"\n\n---\n\nEnded: {meta['ended']}.\n")
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    changes = ""
    if (work / ".git").exists():
        for cmd in (["git", "status", "--short"], ["git", "log", "--oneline", "--all"],
                    ["git", "diff", "HEAD"]):
            got = subprocess.run(cmd, cwd=work, capture_output=True, text=True).stdout
            changes += f"$ {' '.join(cmd)}\n{got}\n"
    (out / "git-changes.txt").write_text(changes or "The working folder is not a git repository.\n")
    if (out / "work").exists():
        shutil.rmtree(out / "work")
    shutil.copytree(work, out / "work", ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
    return f"{case}/{side}: {meta['ended']} ({len(transcript)} messages)"


GUARD = '''#!/usr/bin/env python3
"""Stands in for agent_loop.py during a conversation test. The commands that start agents are refused, because one
test conversation went on to plan and build a whole project. Every other command goes to the real script."""
import json, os, sys
if len(sys.argv) > 1 and sys.argv[1] in ("plan", "run", "review"):
    print(json.dumps({"result": "HELD", "reason": "this is a test of the conversation, so no planner, builder or "
                      "reviewer is started. Tell the owner the command you would have run."}))
    sys.exit(0)
real = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_loop_real.py")
os.execv(sys.executable, [sys.executable, real, *sys.argv[1:]])
'''


def guard(skills_copy):
    """Puts the stand-in above in place of the copy's agent_loop.py, once."""
    scripts = skills_copy / "build" / "scripts"
    if not (scripts / "agent_loop_real.py").exists():
        (scripts / "agent_loop.py").rename(scripts / "agent_loop_real.py")
        (scripts / "agent_loop.py").write_text(GUARD)


def main():
    round_dir, scratch, skills_copy = (Path(a).resolve() for a in sys.argv[1:4])
    if REPO in skills_copy.parents:
        raise SystemExit("give a copy of skills/orchestration outside the repository, not the skills themselves")
    guard(skills_copy)
    wanted = sys.argv[4:] or [f"{c}/{s}" for c in CASES for s in ("with_skill", "without_skill")]
    jobs = [w.split("/") for w in wanted]
    with ThreadPoolExecutor(max_workers=6) as pool:
        def guarded(job):
            try:
                return run(job[0], job[1], round_dir, scratch, skills_copy)
            except Exception as err:  # one failed conversation must not hide the others
                return f"{job[0]}/{job[1]}: FAILED TO RUN: {err!r}"
        for line in pool.map(guarded, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
