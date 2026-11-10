#!/usr/bin/env python3
"""Copies one case's two runs to folders named A and B, in a random order, for a grader that must not know which
run had the skill. Usage: make_blind.py <round folder> <blind folder> <key file> <case> [<case> ...]"""
import json
import random
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EVALS = {"clear-small-request": "intent-conversation", "vague-new-product": "intent-conversation",
         "existing-project-new-feature": "intent-conversation", "tangled-terms": "domain-language",
         "new-name-mid-task": "domain-language", "small-tool": "domain-language"}
SIDE = re.compile(r"with(out)?[-_]skill")
round_dir, blind, key_file = (Path(a).resolve() for a in sys.argv[1:4])
key = json.loads(key_file.read_text()) if key_file.exists() else {}
for case in sys.argv[4:]:
    sides = ["with_skill", "without_skill"]
    random.shuffle(sides)
    key[case] = dict(zip("AB", sides))
    out = blind / case
    if out.exists():
        shutil.rmtree(out)
    for letter, side in key[case].items():
        # The run without the skill is not repeated in a later round, so take it from the first one that has it.
        run = next(r / case / side / "run-1" for r in (round_dir, round_dir.parent / "round-1")
                   if (r / case / side / "run-1").exists())
        (out / letter).mkdir(parents=True)
        text = (run / "transcript.md").read_text().split("\n", 1)[1]  # the first line names the side
        (out / letter / "transcript.md").write_text(f"# Run {letter}\n" + text)
        shutil.copy(run / "git-changes.txt", out / letter / "git-changes.txt")
        shutil.copytree(run / "work", out / letter / "work")
        for f in (out / letter).rglob("*"):  # a path an agent printed can name the side
            try:
                body = f.read_text() if f.is_file() else None
            except UnicodeDecodeError:
                body = None
            if body and SIDE.search(body):
                f.write_text(SIDE.sub("run", body))
    case_dir = REPO / "workbench" / EVALS[case] / "evals" / case
    shutil.copytree(case_dir / "graders", out / "checks")
    if (case_dir / "files").exists():
        shutil.copytree(case_dir / "files", out / "files-at-the-start")
    (out / "first-message.md").write_text((case_dir / "prompt.md").read_text().split("---", 2)[2].strip() + "\n")
    if (case_dir / "owner.md").exists():
        shutil.copy(case_dir / "owner.md", out / "owner.md")
key_file.write_text(json.dumps(key, indent=2) + "\n")
print("made", *sys.argv[4:])
