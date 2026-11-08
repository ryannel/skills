#!/usr/bin/env python3
"""Checks a skill folder for the mistakes that make a skill silently fail to load or fire.

Usage: python3 check_skill.py <skill-folder> [<skill-folder> ...]

It checks that SKILL.md opens with frontmatter on line 1, that the frontmatter has a valid name and a description
within the limits, that every relative Markdown link resolves, and that any reference over 100 lines has a contents
list near the top. It prints one line per problem and exits 1 if there were any. No dependencies beyond Python 3.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def frontmatter(text: str) -> dict[str, str] | None:
    """Top-level `key: value` pairs, with folded or literal blocks joined. Enough for name and description."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fields, key = {}, None
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fields[key] = "" if value in ("|", ">", "|-", ">-") else value.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def check(folder: Path) -> list[str]:
    problems = []
    skill = folder / "SKILL.md"
    if not skill.exists():
        return [f"{folder}: no SKILL.md"]
    text = skill.read_text()
    fields = frontmatter(text)
    if fields is None:
        problems.append(f"{skill}: frontmatter must start on line 1 with --- and close with ---")
        fields = {}
    name, description = fields.get("name", ""), fields.get("description", "")
    if not NAME.match(name) or len(name) > 64:
        problems.append(f"{skill}: name {name!r} must be lowercase words joined by hyphens, at most 64 characters")
    if name != folder.name:
        problems.append(f"{skill}: name {name!r} doesn't match the folder name {folder.name!r}")
    if not description:
        problems.append(f"{skill}: no description, so the skill can never be chosen automatically")
    elif len(description) > 1024:
        problems.append(f"{skill}: description is {len(description)} characters; the limit is 1,024")
    if len(text.splitlines()) > 500:
        problems.append(f"{skill}: body is over 500 lines; move detail into references")

    for md in folder.rglob("*.md"):
        body = md.read_text()
        for target in LINK.findall(body):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#")[0]
            if path and not (md.parent / path).exists():
                problems.append(f"{md}: link to {target} doesn't resolve")
        lines = body.splitlines()
        if md != skill and len(lines) > 100 and not any("contents" in l.lower() for l in lines[:15]):
            problems.append(f"{md}: {len(lines)} lines with no contents list near the top")
    return problems


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    problems = [p for arg in sys.argv[1:] for p in check(Path(arg).resolve())]
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)" if problems else "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
