#!/usr/bin/env python3
"""Checks a skill folder for the mistakes that make a skill silently fail to load or fire.

Usage: python3 check_skill.py <skill-folder> [<skill-folder> ...]

It checks that SKILL.md opens with frontmatter on line 1, that the frontmatter is valid YAML with a valid name and a
description within the limits, that every relative Markdown link resolves (anchors included), and that any reference
over 100 lines has a contents list near the top. It prints one line per problem and exits 1 if there were any.

The YAML check uses PyYAML when it's installed. Without it, a stricter scan catches the usual mistakes (an unquoted
value containing ": ", an unterminated quote, a duplicate key, a line that isn't `key: value`), but it isn't a full
parser, so run `claude plugin validate` too where it's available.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED = ("anthropic", "claude")
LINK = re.compile(r"\[[^\]]*\]\(<?([^)\s>]+)>?\)")
KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$")


def scan_yaml(block: str) -> tuple[dict, list[str]]:
    """Top-level `key: value` pairs and the mistakes that make a YAML parser reject them or read them wrongly."""
    fields, problems, key, block_scalar = {}, [], None, False
    for n, line in enumerate(block.splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if key is None:
                problems.append(f"line {n}: indented line with no key above it")
            else:
                fields[key] = (fields[key] + " " + line.strip()).strip()
            continue
        m = KEY.match(line)
        if not m:
            problems.append(f"line {n}: not a `key: value` line")
            key = None
            continue
        key, value = m.group(1), (m.group(2) or "").strip()
        if key in fields:
            problems.append(f"line {n}: duplicate key {key!r}")
        block_scalar = value in ("|", ">", "|-", ">-", "|+", ">+")
        if block_scalar or not value:
            fields[key] = ""
        elif value[0] in "\"'":
            q = value[0]
            if len(value) < 2 or not value.endswith(q):
                problems.append(f"line {n}: {key} opens a {q} quote that doesn't close on the line")
            fields[key] = value[1:-1]
        elif value[0] in "[{":
            fields[key] = value
        else:
            if ": " in value or value.endswith(":") or " #" in value:
                problems.append(f"line {n}: {key} has an unquoted ': ' or ' #' in its value; quote the whole value")
            if value[0] in "&*!|>%@`":
                problems.append(f"line {n}: {key} starts with {value[0]!r}, which YAML reads specially; quote it")
            fields[key] = value
    return fields, problems


def frontmatter(text: str) -> tuple[dict | None, list[str]]:
    """The frontmatter's fields and any YAML problems, or None when there is no frontmatter block."""
    if not text.startswith("---\n"):
        return None, []
    end = text.find("\n---", 4)
    if end == -1:
        return None, []
    block = text[4:end]
    try:
        import yaml
    except ImportError:
        return scan_yaml(block)
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as e:
        return {}, [f"frontmatter isn't valid YAML: {str(e).splitlines()[0]}"]
    if not isinstance(data, dict):
        return {}, ["frontmatter isn't a YAML mapping of keys to values"]
    return {k: v if isinstance(v, str) else str(v) for k, v in data.items()}, []


def anchors(md: Path) -> set[str]:
    """The heading anchors GitHub and most renderers generate for a Markdown file."""
    out = set()
    for line in md.read_text().splitlines():
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*$", line)
        if m:
            slug = re.sub(r"[^\w\- ]", "", m.group(1).lower()).replace(" ", "-")
            out.add(slug)
    return out


def check(folder: Path) -> list[str]:
    problems = []
    skill = folder / "SKILL.md"
    if not skill.exists():
        return [f"{folder}: no SKILL.md"]
    text = skill.read_text()
    fields, yaml_problems = frontmatter(text)
    problems += [f"{skill}: {p}" for p in yaml_problems]
    if fields is None:
        problems.append(f"{skill}: frontmatter must start on line 1 with --- and close with ---")
        fields = {}
    name, description = fields.get("name", ""), fields.get("description", "")
    if not NAME.match(name) or len(name) > 64:
        problems.append(f"{skill}: name {name!r} must be lowercase words joined by hyphens, at most 64 characters")
    if any(word in name for word in RESERVED):
        problems.append(f"{skill}: name {name!r} contains a reserved word ({', '.join(RESERVED)})")
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
        in_code = False
        for line in body.splitlines():
            if line.lstrip().startswith("```"):
                in_code = not in_code
            if in_code:
                continue
            for target in LINK.findall(line):
                if re.match(r"^[a-z]+:", target):
                    continue
                path, _, anchor = target.partition("#")
                dest = (md.parent / path) if path else md
                if not dest.exists():
                    problems.append(f"{md}: link to {target} doesn't resolve")
                elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                    problems.append(f"{md}: link to {target} names a heading that isn't there")
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
