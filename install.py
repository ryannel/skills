#!/usr/bin/env python3
"""Sets this repo's skills up for Claude Code and Codex, hooks included, with no settings edited by hand.

Usage:
  python3 install.py                          # instructing-agents, orchestrate and skill-creator, both hosts, user scope
  python3 install.py --plugins instructing-agents --host codex
  python3 install.py --repo ~/code/app        # also set up that repo (see below)
  python3 install.py --repo ~/code/app --scope project --source ryannel/skills
                                              # Claude plugins declared in the repo's .claude/settings.json

Claude Code: adds this repo as the `ryannel-skills` plugin marketplace and installs each plugin. A plugin's hooks come
with it (instructing-agents carries the handoff nudge), so nothing goes into settings.json by hand.

Codex: adds the same marketplace with the Codex CLI (the copy inside the Codex app when `codex` isn't on PATH), which
reads `.claude-plugin/marketplace.json` and installs each plugin's skills where the app loads them. Codex doesn't get
the hook (see README); instead, with instructing-agents, one line goes into the global AGENTS.md.

With --repo: if the repo has AGENTS.md but no CLAUDE.md and the `claude` CLI is older than 2.1.277 (which reads only
CLAUDE.md), writes a CLAUDE.md holding `@AGENTS.md`. With orchestrate, checks ORCHESTRATE.md with
`agent_loop.py profile` when the file exists; `/plan-module` writes it when it doesn't.

CLAUDE_CONFIG_DIR and CODEX_HOME are honoured, so a throwaway config can be used to try it.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKETPLACE = "ryannel-skills"
DEFAULT_PLUGINS = ["instructing-agents", "orchestrate", "skill-creator"]
CODEX_APP_CLI = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CLAUDE_READS_AGENTS_MD = (2, 1, 277)
AGENTS_LINE = "Apply the `instructing-agents` skill before you hand a prompt to another agent."


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    if check and r.returncode != 0:
        sys.exit(f"failed ({r.returncode}): {' '.join(cmd)}")
    return r


def version(binary: str) -> tuple[int, ...] | None:
    try:
        out = subprocess.run([binary, "--version"], text=True, capture_output=True).stdout
    except OSError:
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    return tuple(int(x) for x in m.groups()) if m else None


def codex_binary() -> str | None:
    found = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if found:
        return found
    return CODEX_APP_CLI if os.access(CODEX_APP_CLI, os.X_OK) else None


def warn_duplicates(plugins: list[str], host: str) -> None:
    """A standalone copy of a skill alongside the plugin's means two descriptions in every session."""
    names = {"orchestrate": ["plan-module", "build-milestone", "review-milestone", "build"]}
    if host == "claude":
        roots = [Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "skills"]
    else:
        roots = [Path.home() / ".agents" / "skills", Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"]
    for plugin in plugins:
        for skill in names.get(plugin, [plugin]):
            for root in roots:
                if (root / skill).exists():
                    print(f"  note: {root / skill} is a standalone copy of {skill}; remove it so {host} lists the skill once")


def setup_claude(plugins: list[str], scope: str, repo: Path | None, source: str) -> None:
    claude = shutil.which("claude")
    if not claude:
        print("Claude Code: `claude` isn't on PATH; skipped. Install it, then re-run with --host claude.")
        return
    cwd = repo if scope != "user" else None
    listed = run([claude, "plugin", "marketplace", "list"], check=False).stdout
    if MARKETPLACE in listed:
        run([claude, "plugin", "marketplace", "update", MARKETPLACE], check=False)
    else:
        run([claude, "plugin", "marketplace", "add", "--scope", scope, source], cwd=cwd)
    for p in plugins:
        r = run([claude, "plugin", "install", "--scope", scope, f"{p}@{MARKETPLACE}"], cwd=cwd)
        if "already installed" in r.stdout + r.stderr:
            # Claude Code re-copies a plugin only when its version in marketplace.json has changed.
            run([claude, "plugin", "update", "--scope", scope, f"{p}@{MARKETPLACE}"], cwd=cwd, check=False)
    warn_duplicates(plugins, "claude")


def setup_codex(plugins: list[str], source: str) -> None:
    codex = codex_binary()
    if not codex:
        print("Codex: no `codex` on PATH and no Codex app at /Applications/ChatGPT.app; skipped.")
        return
    Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).mkdir(parents=True, exist_ok=True)
    listed = run([codex, "plugin", "marketplace", "list"], check=False).stdout
    if MARKETPLACE not in listed:
        run([codex, "plugin", "marketplace", "add", source])
    for p in plugins:
        # A local marketplace is copied at install time, so re-adding picks up changes.
        run([codex, "plugin", "remove", f"{p}@{MARKETPLACE}"], check=False)
        run([codex, "plugin", "add", f"{p}@{MARKETPLACE}"])
    if "instructing-agents" in plugins:
        agents_md = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "AGENTS.md"
        text = agents_md.read_text() if agents_md.exists() else ""
        if "instructing-agents" in text:
            print(f"  {agents_md} already names instructing-agents; left as is")
        else:
            agents_md.parent.mkdir(parents=True, exist_ok=True)
            sep = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
            agents_md.write_text(text + sep + AGENTS_LINE + "\n")
            print(f"  added the instructing-agents line to {agents_md}")
    if "orchestrate" in plugins:
        # The Codex evaluator agent isn't a plugin component; link it the way the orchestrate README says.
        run(["bash", str(HERE / "skills/orchestration/build/scripts/install_agents.sh"), "--global", "--codex-only"],
            check=False)
    warn_duplicates(plugins, "codex")


def setup_repo(repo: Path, plugins: list[str]) -> None:
    claude = shutil.which("claude")
    v = version(claude) if claude else None
    agents, claude_md = repo / "AGENTS.md", repo / "CLAUDE.md"
    if agents.exists() and not claude_md.exists():
        if v is not None and v < CLAUDE_READS_AGENTS_MD:
            claude_md.write_text("@AGENTS.md\n")
            print(f"  wrote {claude_md} with @AGENTS.md (claude {'.'.join(map(str, v))} reads only CLAUDE.md)")
        else:
            print("  CLAUDE.md not needed: the claude CLI reads AGENTS.md" if v else
                  "  no claude CLI found; if an older one runs here, add a CLAUDE.md holding @AGENTS.md")
    if "orchestrate" in plugins:
        profile = repo / "ORCHESTRATE.md"
        if profile.exists():
            run([sys.executable, str(HERE / "skills/orchestration/build/scripts/agent_loop.py"), "profile",
                 "--worktree", str(repo)], check=False)
        else:
            print("  no ORCHESTRATE.md yet: run /plan-module in the repo, which writes it first")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", choices=["claude", "codex", "both"], default="both")
    ap.add_argument("--plugins", default=",".join(DEFAULT_PLUGINS),
                    help="comma-separated plugin names from .claude-plugin/marketplace.json")
    ap.add_argument("--scope", choices=["user", "project", "local"], default="user",
                    help="Claude Code install scope; project and local need --repo")
    ap.add_argument("--repo", type=Path, help="a repository to set up as well")
    ap.add_argument("--source", default=str(HERE),
                    help="marketplace source: this checkout (default) or ryannel/skills, which suits --scope project")
    a = ap.parse_args()
    plugins = [p.strip() for p in a.plugins.split(",") if p.strip()]
    repo = a.repo.expanduser().resolve() if a.repo else None
    if a.scope != "user" and not repo:
        ap.error("--scope project|local needs --repo")
    if a.host in ("claude", "both"):
        print("== Claude Code")
        setup_claude(plugins, a.scope, repo, a.source)
    if a.host in ("codex", "both"):
        print("== Codex")
        setup_codex(plugins, a.source)
    if repo:
        print(f"== {repo}")
        setup_repo(repo, plugins)


if __name__ == "__main__":
    main()
