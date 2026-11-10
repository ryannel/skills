#!/usr/bin/env python3
"""Copies a blind grader's grades into the round folder under the real side names, and prints the totals.
Usage: collect_grades.py <round folder> <blind folder> <key file>"""
import json
import sys
from pathlib import Path

round_dir, blind, key_file = (Path(a).resolve() for a in sys.argv[1:4])
key = json.loads(key_file.read_text())
for case, letters in sorted(key.items()):
    grades_file = blind / case / "grades.json"
    if not grades_file.exists():
        print(f"{case}: not graded")
        continue
    grades = json.loads(grades_file.read_text())
    named = {side: grades[letter] for letter, side in letters.items()}
    (round_dir / case).mkdir(parents=True, exist_ok=True)
    (round_dir / case / "grades.json").write_text(json.dumps(named, indent=2) + "\n")
    line = []
    for side in ("with_skill", "without_skill"):
        g = named[side]
        failed = [c["check"].split("-")[0] + ("?" if c.get("unclear") else "") for c in g if not c["passed"]]
        line.append(f"{side} {sum(c['passed'] for c in g)}/{len(g)}" + (f" (failed {' '.join(failed)})" if failed else ""))
    print(f"{case}: " + "; ".join(line))
