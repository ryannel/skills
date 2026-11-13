#!/usr/bin/env python3
"""Sets this repo's skills up for Claude Code and Codex, with no settings edited by hand.

Usage:
  python3 install.py                          # prompting-agents, orchestrate and skill-creator, both hosts, user scope
  python3 install.py --replace-standalone     # the same, first moving aside earlier standalone copies and hook
  python3 install.py --plugins prompting-agents --host codex
  python3 install.py --repo ~/code/app        # also set up that repo (see below)
  python3 install.py --repo ~/code/app --scope project
                                              # Claude plugins declared in the repo's .claude/settings.json
  python3 install.py --source .               # this checkout instead, to try changes before they are pushed

Claude Code: registers ryannel/skills on GitHub (or --source) as the `ryannel-skills` plugin marketplace and installs
each plugin. Installing from GitHub means every session loads the published version from the hosts' plugin caches,
never a working copy that someone is editing. If that marketplace is already registered from another source, it says so and re-registers it from this one,
reinstalling the plugins it had.

Codex: the same marketplace with the Codex CLI (the copy inside the Codex app when `codex` isn't on PATH), which
reads `.claude-plugin/marketplace.json`. With prompting-agents, one line goes into the global AGENTS.md.

skill-creator and orchestrate both need prompting-agents, so installing either installs it too. Claude Code does this
itself from the `dependencies` in marketplace.json; Codex doesn't read that field, so this script adds it.

prompting-agents replaced instructing-agents. Installing it uninstalls the old plugin, treats a standalone copy
of the old skill as an earlier install, and rewrites the old AGENTS.md line.

Earlier standalone installs: copies of these skills in ~/.claude/skills, ~/.agents/skills or ~/.codex/skills, and an
older hand-installed handoff hook in settings.json, would load next to the plugins. The installer finds them first and
stops, listing them. With --replace-standalone it moves the copies to ~/.ryannel-skills-backup/<time>/, removes
links into them, and drops the old hook entry from settings.json (backed up there too). A same-named skill that
doesn't match any committed version of this repo's skill is left alone.

With --repo: reports whether Claude will read the repo's AGENTS.md, from the files that decide it and the CLI
version, and writes a CLAUDE.md holding `@AGENTS.md` when it wouldn't and the repo has no CLAUDE.md. With
orchestrate, checks ORCHESTRATE.md with `agent_loop.py profile` when it exists; `/plan-module` writes it otherwise.

CLAUDE_CONFIG_DIR and CODEX_HOME are honoured, so a throwaway config can be used to try it.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKETPLACE = "ryannel-skills"
ENTRIES = {e["name"]: e for e in json.loads((HERE / ".claude-plugin/marketplace.json").read_text())["plugins"]}
DEFAULT_PLUGINS = ["prompting-agents", "orchestrate", "skill-creator"]
# A plugin, and the earlier plugins it replaced. Their skills either live on inside it or were retired.
RETIRED_PLUGINS = {"prompting-agents": ["instructing-agents"]}
RETIRED_SKILLS = {"prompting-agents": ["instructing-agents"]}  # skills that no current plugin holds
# A plugin, and the plugins it needs installed beside it. Orchestrate's agents write prompts for each other all day,
# and its skills tell them to use prompting-agents. skill-creator takes its writing guidance from it.
REQUIRES = {e["name"]: e.get("dependencies", []) for e in ENTRIES.values()}  # Codex ignores `dependencies`
PUBLISHED = "ryannel/skills"
CODEX_APP_CLI = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CLAUDE_READS_AGENTS_MD = (2, 1, 277)
AGENTS_LINE = "Apply the `prompting-agents` skill before you hand a prompt to another agent."
OLD_AGENTS_LINE = AGENTS_LINE.replace("prompting-agents", "instructing-agents")
OLD_HOOKS = ("instructing-agents-gate.py", "handoff_nudge.py")  # hand-installed copies of the retired handoff hook
failures: list[str] = []


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    if check and r.returncode != 0:
        sys.exit(f"failed ({r.returncode}): {' '.join(cmd)}")
    return r


def quiet_json(cmd: list[str], cwd: Path | None = None):
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def version(binary: str) -> tuple[int, ...] | None:
    try:
        out = subprocess.run([binary, "--version"], text=True, capture_output=True).stdout
    except OSError:
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    return tuple(int(x) for x in m.groups()) if m else None


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def codex_binary() -> str | None:
    found = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if found:
        return found
    return CODEX_APP_CLI if os.access(CODEX_APP_CLI, os.X_OK) else None


def skill_names(plugins: list[str]) -> list[str]:
    """The skills these plugins hold, and the retired skills they replaced."""
    return ([Path(p).name for plugin in plugins for p in ENTRIES[plugin].get("skills", [])]
            + [old for plugin in plugins for old in RETIRED_SKILLS.get(plugin, [])])


def with_required(plugins: list[str]) -> list[str]:
    """The plugins asked for, with any plugin they need added after them, each once."""
    out = list(plugins)
    for p in plugins:
        for needed in REQUIRES.get(p, []):
            if needed not in out:
                print(f"{p} needs {needed}, so it is installed too")
                out.append(needed)
    return out


def agents_md_text(text: str) -> tuple[str, str]:
    """The global AGENTS.md with the prompting-agents line in it, and what was done."""
    if OLD_AGENTS_LINE in text:
        return text.replace(OLD_AGENTS_LINE, AGENTS_LINE), "replaced the instructing-agents line in"
    if "prompting-agents" in text:
        return text, "already names prompting-agents; left as is:"
    sep = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    return text + sep + AGENTS_LINE + "\n", "added the prompting-agents line to"


# ---- earlier standalone installs ------------------------------------------------------------------------------

def frontmatter_name(skill_md: Path) -> str | None:
    m = re.match(r"---\n(?:.*\n)*?name:\s*['\"]?([\w-]+)", skill_md.read_text(errors="replace"))
    return m.group(1) if m else None


def from_this_repo(skill_md: Path) -> bool:
    """True when this SKILL.md is byte-identical to a committed version of one in this repo (or to the current one)."""
    try:
        blob = subprocess.run(["git", "hash-object", str(skill_md)], text=True, capture_output=True).stdout.strip()
        if blob and subprocess.run(["git", "-C", str(HERE), "cat-file", "-e", f"{blob}^{{blob}}"],
                                   capture_output=True).returncode == 0:
            return True
    except OSError:
        pass
    return any(skill_md.read_bytes() == (HERE / p / "SKILL.md").read_bytes()
               for e in ENTRIES.values() for p in e.get("skills", []) if (HERE / p / "SKILL.md").exists())


def find_standalone(plugins: list[str], hosts: list[str]) -> tuple[list[Path], list[Path], list[str]]:
    """Recognised standalone copies (folders or links to them), other links into them, and skills left alone."""
    roots = [claude_home() / "skills"] if "claude" in hosts else []
    if "codex" in hosts:
        roots += [Path.home() / ".agents" / "skills", codex_home() / "skills"]
    copies, others = [], []
    for name in skill_names(plugins):
        for path in (root / name for root in roots):
            if not (path.exists() or path.is_symlink()):
                continue
            md = path / "SKILL.md"
            if md.exists() and frontmatter_name(md) == name and from_this_repo(md):
                copies.append(path)
            else:
                others.append(f"{path} is a skill named {name} that doesn't match this repo's; left alone")
    real = {p.resolve() for p in copies if not p.is_symlink()}
    links = []
    for folder in (claude_home() / "agents", codex_home() / "agents", Path.home() / ".agents" / "skills",
                   claude_home() / "skills"):
        for p in sorted(folder.iterdir()) if folder.is_dir() else []:
            target = Path(os.path.realpath(p))
            if p.is_symlink() and p not in copies and any(target == r or r in target.parents for r in real):
                links.append(p)
    return copies, links, others


def old_hook_entries(settings: dict) -> list[tuple[str, int, int]]:
    found = []
    for event, groups in (settings.get("hooks") or {}).items():
        for gi, group in enumerate(groups or []):
            for hi, hook in enumerate(group.get("hooks") or []):
                command = hook.get("command", "")
                if any(name in command for name in OLD_HOOKS) and "CLAUDE_PLUGIN_ROOT" not in command:
                    found.append((event, gi, hi))
    return found


def migrate(plugins: list[str], hosts: list[str], replace: bool) -> None:
    copies, links, others = find_standalone(plugins, hosts)
    settings_path = claude_home() / "settings.json"
    settings = json.loads(settings_path.read_text()) if "claude" in hosts and settings_path.exists() else {}
    hooks = old_hook_entries(settings)
    for note in others:
        print(f"  note: {note}")
    if not (copies or links or hooks):
        return
    print("Earlier standalone installs would load next to the plugins:")
    for p in copies:
        print(f"  standalone copy: {p}" + (f" -> {os.readlink(p)}" if p.is_symlink() else ""))
    for p in links:
        print(f"  link into it:    {p} -> {os.readlink(p)}")
    for event, gi, hi in hooks:
        print(f"  settings hook:   {settings_path} {event}: {settings['hooks'][event][gi]['hooks'][hi]['command']}")
    if not replace:
        sys.exit("Nothing installed. Re-run with --replace-standalone to move these aside (backed up under "
                 "~/.ryannel-skills-backup/), or remove them yourself.")
    backup = Path.home() / ".ryannel-skills-backup" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup.mkdir(parents=True, exist_ok=True)
    log = []
    folders = [c for c in copies if not c.is_symlink()]
    for p in links + [c for c in copies if c.is_symlink()]:
        log.append(f"removed link {p} -> {os.readlink(p)}")
        p.unlink()
    for p in folders:
        dest = backup / p.parent.parent.name.lstrip(".") / p.parent.name / p.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), dest)
        log.append(f"moved {p} -> {dest}")
    if hooks:
        shutil.copy2(settings_path, backup / "settings.json")
        for event, gi, hi in sorted(hooks, reverse=True):
            del settings["hooks"][event][gi]["hooks"][hi]
        for event in list(settings["hooks"]):
            settings["hooks"][event] = [g for g in settings["hooks"][event] if g.get("hooks")]
            if not settings["hooks"][event]:
                del settings["hooks"][event]
        if not settings["hooks"]:
            del settings["hooks"]
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")
        log.append(f"removed {len(hooks)} hook entr{'y' if len(hooks) == 1 else 'ies'} from {settings_path} "
                   f"(previous file: {backup / 'settings.json'}); the hook script itself is left in place, unused")
    (backup / "MOVED.txt").write_text("\n".join(log) + "\n")
    print("  " + "\n  ".join(log))


# ---- marketplace source ---------------------------------------------------------------------------------------

def same_source(registered: str | None, requested: str) -> bool:
    if not registered:
        return False
    local = Path(requested).expanduser()
    if local.exists():
        return os.path.realpath(registered) == os.path.realpath(local)
    norm = lambda s: re.sub(r"(\.git)?/?$", "", re.sub(r"^(https://github\.com/|git@github\.com:)", "", s))
    return norm(registered) == norm(requested)


def claude_registered(claude: str) -> str | None:
    for m in quiet_json([claude, "plugin", "marketplace", "list", "--json"]) or []:
        if m.get("name") == MARKETPLACE:
            return m.get("path") or m.get("repo") or m.get("url") or m.get("installLocation") or ""
    return None


def tree_differs(a: Path, b: Path) -> bool:
    files = lambda root: {p.relative_to(root): p for p in root.rglob("*")
                          if p.is_file() and "__pycache__" not in p.parts} if root.exists() else {}
    fa, fb = files(a), files(b)
    return fa.keys() != fb.keys() or any(fa[k].read_bytes() != fb[k].read_bytes() for k in fa)


def stale_copy(plugin: str, install_path: Path) -> bool:
    """Whether a cached copy of the plugin differs from this checkout in any file its entry uses."""
    entry = ENTRIES[plugin]
    paths = entry.get("skills", []) + entry.get("agents", [])
    return any(tree_differs(HERE / p, install_path / p) if (HERE / p).is_dir()
               else not (install_path / p).exists() or (HERE / p).read_bytes() != (install_path / p).read_bytes()
               for p in paths)


def older_commit(plugin: str, scope: str) -> bool:
    """Whether Claude Code's copy of a plugin from the GitHub marketplace was made at an older commit than the
    marketplace's clone now holds. Claude Code re-copies only when `version` changes, so a fix pushed at the same
    version would otherwise never arrive."""
    home = claude_home() / "plugins"
    head = subprocess.run(["git", "-C", str(home / "marketplaces" / MARKETPLACE), "rev-parse", "HEAD"],
                          text=True, capture_output=True).stdout.strip()
    try:
        recs = json.loads((home / "installed_plugins.json").read_text())["plugins"].get(f"{plugin}@{MARKETPLACE}", [])
    except (OSError, ValueError, KeyError):
        return False
    sha = next((r.get("gitCommitSha") for r in recs if r.get("scope") == scope), None)
    return bool(head and sha and sha != head)


def setup_claude(plugins: list[str], scope: str, repo: Path | None, source: str) -> None:
    claude = shutil.which("claude")
    if not claude:
        print("Claude Code: `claude` isn't on PATH; skipped. Install it, then re-run with --host claude.")
        return
    cwd = repo if scope != "user" else None
    registered = claude_registered(claude)
    reinstall: list[str] = []
    if registered is not None and not same_source(registered, source):
        had = [p for p in quiet_json([claude, "plugin", "list", "--json"]) or [] if p["id"].endswith("@" + MARKETPLACE)]
        print(f"!! {MARKETPLACE} is registered from {registered}, not {source}. Re-registering it from {source};"
              f" removing it uninstalls its plugins, so they're reinstalled below.")
        run([claude, "plugin", "marketplace", "remove", MARKETPLACE])
        registered = None
        replaced_by = {old: new for new, olds in RETIRED_PLUGINS.items() for old in olds}
        reinstall = list(dict.fromkeys(replaced_by.get(n, n) for n in (p["id"].split("@")[0] for p in had
                                       if p.get("scope") == "user") if replaced_by.get(n, n) in ENTRIES))
        for p in had:
            if p.get("scope") != "user":
                print(f"!! {p['id']} was installed at {p.get('scope')} scope {p.get('projectPath', '')}; reinstall it"
                      f" there with: python3 {HERE / 'install.py'} --host claude --plugins {p['id'].split('@')[0]}"
                      f" --scope {p.get('scope')} --repo <that repo>")
    if registered is None:
        run([claude, "plugin", "marketplace", "add", "--scope", scope, source], cwd=cwd)
    else:
        run([claude, "plugin", "marketplace", "update", MARKETPLACE], check=False)
    for p in [x for x in reinstall if not (x in plugins and scope == "user")]:
        run([claude, "plugin", "install", "--scope", "user", f"{p}@{MARKETPLACE}"])
    for old in [f"{o}@{MARKETPLACE}" for p in plugins for o in RETIRED_PLUGINS.get(p, [])]:
        if any(x["id"] == old and x.get("scope") == scope
               for x in quiet_json([claude, "plugin", "list", "--json"], cwd=cwd) or []):
            run([claude, "plugin", "uninstall", "--scope", scope, old], cwd=cwd, check=False)
    for p in plugins:
        r = run([claude, "plugin", "install", "--scope", scope, f"{p}@{MARKETPLACE}"], cwd=cwd)
        if "already installed" not in r.stdout + r.stderr:
            continue
        run([claude, "plugin", "update", "--scope", scope, f"{p}@{MARKETPLACE}"], cwd=cwd, check=False)
        rec = next((x for x in quiet_json([claude, "plugin", "list", "--json"], cwd=cwd) or []
                    if x["id"] == f"{p}@{MARKETPLACE}" and x.get("scope") == scope), None)
        # Claude Code before in-place loading copies a local plugin and re-copies only when `version` changes.
        local = Path(source).expanduser().exists()
        if rec and not rec.get("readFromFolder") and (local and stale_copy(p, Path(rec["installPath"])) or
                                                      not local and older_commit(p, scope)):
            print(f"  the cached copy of {p} is older than {source} at the same version; reinstalling it")
            run([claude, "plugin", "uninstall", "--keep-data", "--scope", scope, f"{p}@{MARKETPLACE}"], cwd=cwd)
            run([claude, "plugin", "install", "--scope", scope, f"{p}@{MARKETPLACE}"], cwd=cwd)
    installed = {x["id"].split("@")[0]: x for x in quiet_json([claude, "plugin", "list", "--json"], cwd=cwd) or []
                 if x["id"].endswith("@" + MARKETPLACE) and x.get("scope") == scope}
    for x in installed.values():
        print(f"  {x['id']} {x.get('version')} ({x.get('scope')}) loads from "
              f"{x.get('readFromFolder') or x.get('installPath')}")
    if "orchestrate" in plugins and "orchestrate" not in installed:
        sys.exit(f"Claude Code: could not verify orchestrate at {scope} scope.")
    if "orchestrate" in installed:
        link_claude_agents(claude, installed["orchestrate"], scope, repo)


def link_claude_agents(claude: str, rec: dict, scope: str, repo: Path | None) -> None:
    """Claude Code 2.1.239 and 2.1.317 don't load the `agents` a marketplace entry lists (`claude plugin details`
    shows Agents (0)), so link the orchestrate agents from the installed copy, as install_agents.sh would."""
    details = subprocess.run([claude, "plugin", "details", rec["id"]], cwd=repo if scope != "user" else None,
                             text=True, capture_output=True)
    if details.returncode == 0 and re.search(r"Agents \([1-9][0-9]*\)", details.stdout):
        return
    root = Path(rec.get("readFromFolder") or rec["installPath"])
    folder = claude_home() / "agents" if scope == "user" else repo / ".claude" / "agents"
    folder.mkdir(parents=True, exist_ok=True)
    marker = "<!-- Managed by the ryannel/skills orchestrate installer. -->"
    for path in ENTRIES["orchestrate"].get("agents", []):
        destination, target = folder / Path(path).name, root / path
        if not target.is_file():
            sys.exit(f"Claude Code: missing agent definition {target}")
        if scope == "user" and (destination.is_symlink() or not destination.exists()):
            destination.unlink(missing_ok=True)
            destination.symlink_to(target)
            print(f"  linked {destination} -> {target}")
            continue
        contents = target.read_text()
        if destination.exists() or destination.is_symlink():
            existing = destination.read_text() if destination.is_file() else ""
            if existing == contents:
                continue
            if destination.is_symlink() or not existing.endswith(f"\n{marker}\n"):
                sys.exit(f"Claude Code: {destination} already exists. Move it aside and rerun to install the agent.")
        destination.write_text(f"{contents.rstrip()}\n\n{marker}\n")
        print(f"  wrote {destination}")


def codex_registered(codex: str) -> str | None:
    for m in (quiet_json([codex, "plugin", "marketplace", "list", "--json"]) or {}).get("marketplaces", []):
        if m.get("name") == MARKETPLACE:
            return (m.get("marketplaceSource") or {}).get("source") or m.get("root") or ""
    return None


def setup_codex(plugins: list[str], source: str) -> None:
    codex = codex_binary()
    if not codex:
        print("Codex: no `codex` on PATH and no Codex app at /Applications/ChatGPT.app; skipped.")
        return
    codex_home().mkdir(parents=True, exist_ok=True)
    registered = codex_registered(codex)
    if registered is not None and not same_source(registered, source):
        print(f"!! {MARKETPLACE} is registered in Codex from {registered}, not {source}. Re-registering it.")
        run([codex, "plugin", "marketplace", "remove", MARKETPLACE])
        registered = None
    if registered is None:
        run([codex, "plugin", "marketplace", "add", source])
    for p in plugins:
        # A local marketplace is copied at install time, so re-adding picks up changes.
        for old in RETIRED_PLUGINS.get(p, []):
            run([codex, "plugin", "remove", f"{old}@{MARKETPLACE}"], check=False)
        run([codex, "plugin", "remove", f"{p}@{MARKETPLACE}"], check=False)
        run([codex, "plugin", "add", f"{p}@{MARKETPLACE}"])
    if "prompting-agents" in plugins:
        agents_md = codex_home() / "AGENTS.md"
        text = agents_md.read_text() if agents_md.exists() else ""
        new, did = agents_md_text(text)
        if new != text:
            agents_md.parent.mkdir(parents=True, exist_ok=True)
            agents_md.write_text(new)
        print(f"  {did} {agents_md}")
    if "orchestrate" in plugins:
        # The Codex reviewer agent isn't a plugin component. Link it from the plugin's installed copy so it keeps
        # working if this checkout moves. Copy the definition if there is no plugin cache.
        script = "skills/orchestration/build/scripts/install_agents.sh"
        cached = sorted((codex_home() / "plugins/cache" / MARKETPLACE / "orchestrate").glob(f"*/{script}"))
        if cached:
            run(["bash", str(cached[-1]), "--global", "--codex-only"])
        else:
            target = (HERE / script).parent.parent / "agents/codex/orchestrate-reviewer.toml"
            destination = codex_home() / "agents" / target.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.unlink(missing_ok=True)
            shutil.copyfile(target, destination)
            print(f"  copied {destination}")


# ---- one repository -------------------------------------------------------------------------------------------

def imports_agents_md(path: Path, agents: Path) -> bool:
    if not path.exists():
        return False
    if path.is_symlink() and path.resolve() == agents.resolve():
        return True
    return bool(re.search(r"^@(\./)?AGENTS\.md\b", path.read_text(errors="replace"), re.MULTILINE))


def setup_repo(repo: Path, plugins: list[str]) -> None:
    claude = shutil.which("claude")
    v = version(claude) if claude else None
    agents, claude_md = repo / "AGENTS.md", repo / "CLAUDE.md"
    if agents.exists():
        user_files = {Path.home() / ".claude/CLAUDE.md", claude_home() / "CLAUDE.md"}
        shadows = [p for d in (repo, *repo.parents) for p in (d / "CLAUDE.md", d / ".claude/CLAUDE.md",
                   d / "CLAUDE.local.md") if p.exists() and p not in user_files]
        if any(imports_agents_md(p, agents) for p in (claude_md, repo / ".claude/CLAUDE.md")):
            print(f"  Claude reads AGENTS.md here: a CLAUDE.md in {repo} imports it")
        elif claude_md.exists():
            print(f"  !! {claude_md} doesn't import AGENTS.md, so Claude reads it instead of AGENTS.md. Add"
                  f" `@AGENTS.md` as its first line to share the rules.")
        elif shadows or v is None or v < CLAUDE_READS_AGENTS_MD:
            why = (f"{shadows[0]} stops Claude reading AGENTS.md" if shadows else
                   "no claude CLI found to check its version" if v is None else
                   f"claude {'.'.join(map(str, v))} reads only CLAUDE.md (AGENTS.md needs 2.1.277)")
            claude_md.write_text("@AGENTS.md\n")
            print(f"  wrote {claude_md} holding @AGENTS.md: {why}")
        else:
            print(f"  Claude reads AGENTS.md here: claude {'.'.join(map(str, v))}, and no CLAUDE.md,"
                  f" .claude/CLAUDE.md or CLAUDE.local.md in {repo} or above it (unless your Claude settings turn"
                  f" AGENTS.md off)")
    if "orchestrate" in plugins:
        profile = repo / "ORCHESTRATE.md"
        if profile.exists():
            r = run([sys.executable, str(HERE / "skills/orchestration/build/scripts/agent_loop.py"), "profile",
                     "--worktree", str(repo)], check=False)
            if r.returncode != 0:
                failures.append(f"{profile} didn't validate (agent_loop.py profile exited {r.returncode})")
        else:
            print("  no ORCHESTRATE.md yet: run /plan-module in the repo, which writes it first")


def checkout_revision(source: str) -> str:
    if not Path(source).expanduser().exists():
        return source
    sha = subprocess.run(["git", "-C", source, "rev-parse", "--short", "HEAD"], text=True, capture_output=True)
    dirty = subprocess.run(["git", "-C", source, "status", "--porcelain"], text=True, capture_output=True).stdout
    return f"{source} at {sha.stdout.strip() or 'no git revision'}" + (" with uncommitted changes" if dirty else "")


def choose(prompt: str, options: list[tuple[str, str]]) -> str:
    print(prompt)
    for number, (_, label) in enumerate(options, 1):
        print(f"  {number}. {label}")
    while True:
        answer = input("Choose a number (or q to quit): ").strip().lower()
        if answer == "q":
            sys.exit("Installation cancelled.")
        if answer in [str(number) for number in range(1, len(options) + 1)]:
            return options[int(answer) - 1][0]
        print("Choose one of the numbers shown above.")


def choose_orchestration_install(a: argparse.Namespace) -> None:
    if not sys.stdin.isatty():
        sys.exit("Run this command in an interactive terminal to choose an agent and scope.")
    hosts = []
    if shutil.which("claude"):
        hosts.append(("claude", "Claude Code"))
    if codex_binary():
        hosts.append(("codex", "Codex"))
    if not hosts:
        sys.exit("Install the Claude Code or Codex CLI before running this installer.")
    if len(hosts) == 2:
        hosts.append(("both", "Claude Code and Codex"))
    try:
        a.host = choose("Which agents should get the full orchestration setup?", hosts)
        scopes = [("user", "Global (all projects)")]
        if a.host == "claude":
            scopes.append(("project", "Project (this Git repository)"))
        else:
            print("The full Codex plugin and evaluator install at global scope.")
        a.scope = choose("Where should orchestration be installed?", scopes)
    except (EOFError, KeyboardInterrupt):
        sys.exit("Installation cancelled.")
    a.plugins = "orchestrate"
    a.source = PUBLISHED
    a.repo = None
    if a.scope == "project":
        git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True)
        if git_root.returncode:
            sys.exit("Run the project install from inside the target Git repository.")
        a.repo = Path(git_root.stdout.strip())


def main() -> None:
    if sys.argv[1:2] == ["--interactive"]:
        ap = argparse.ArgumentParser(description="Install the orchestration plugin and its agents interactively.")
        ap.add_argument("--replace-standalone", action="store_true",
                        help="move aside earlier standalone copies of the orchestration skills")
        a = ap.parse_args(sys.argv[2:])
        choose_orchestration_install(a)
    else:
        a = parse_scripted_args()
    install(a)


def parse_scripted_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", choices=["claude", "codex", "both"], default="both")
    ap.add_argument("--plugins", default=",".join(DEFAULT_PLUGINS),
                    help="comma-separated plugin names from .claude-plugin/marketplace.json")
    ap.add_argument("--scope", choices=["user", "project", "local"], default="user",
                    help="Claude Code install scope; project and local need --repo")
    ap.add_argument("--repo", type=Path, help="a repository to set up as well")
    ap.add_argument("--source", default=PUBLISHED,
                    help=f"marketplace source: {PUBLISHED} on GitHub (default), or a local checkout such as this one "
                         "when testing changes before they are pushed")
    ap.add_argument("--replace-standalone", action="store_true",
                    help="move aside earlier standalone copies of these skills and the hand-installed hook")
    a = ap.parse_args()
    if a.scope != "user" and not a.repo:
        ap.error("--scope project|local needs --repo")
    return a


def install(a: argparse.Namespace) -> None:
    plugins = with_required([p.strip() for p in a.plugins.split(",") if p.strip()])
    unknown = [p for p in plugins if p not in ENTRIES]
    if unknown:
        sys.exit(f"unknown plugin(s) {', '.join(unknown)}; choose from {', '.join(ENTRIES)}")
    repo = a.repo.expanduser().resolve() if a.repo else None
    hosts = ["claude", "codex"] if a.host == "both" else [a.host]
    migrate(plugins, hosts, a.replace_standalone)
    if "claude" in hosts:
        print("== Claude Code")
        setup_claude(plugins, a.scope, repo, a.source)
    if "codex" in hosts:
        print("== Codex")
        setup_codex(plugins, a.source)
    if repo:
        print(f"== {repo}")
        setup_repo(repo, plugins)
    print(f"== Installed from {checkout_revision(a.source)}. Restart open sessions to load it.")
    if failures:
        sys.exit("failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
