# Parts C and D results: instructing-agents alignment, packaging and setup

9 November 2026, branch `fold-d` (worktree `~/Workspace/skill-factory-fold-d`). Opus 5.5, medium effort. Tested on
Claude Code 2.1.239 (the `claude` on PATH) and the Codex CLI 0.167.0-alpha.3.2 bundled in `/Applications/ChatGPT.app`.
Every install below went into a throwaway `HOME`, `CLAUDE_CONFIG_DIR` and `CODEX_HOME` under the session scratchpad,
with throwaway git repos. The real `~/.claude` and `~/.codex` weren't changed (mtimes checked at the end).
`skills/orchestration` wasn't touched.

## Per item

### 9. instructing-agents description aligned with the hook
Changed:
- `skills/instructing-agents/SKILL.md` description. It still says when the skill applies ("before sending any prompt
  another agent will act on, even a short one", with the same kinds, matching what the hook catches). It adds "The check
  at the top is often enough for a short prompt", which lets the agent decide how much to read. "a session brief" and
  "Covers Claude Code, Codex and other hosts" are dropped. Length 448 → 445 characters.
- One edited sentence after the five-point check: if a hook refused the launch, run the check and resend; for a short
  prompt the check is often enough; read on for a goal, a long unattended run, a reviewer brief or an instruction
  file.

Verified: `check_skill.py` passes on `skills/instructing-agents` and `skills/skill-creator`. Codex's model-visible
skill list (`codex debug prompt-input`) shows the new description.
Not verified: no receiver or trigger run, so nothing is known yet about behaviour.

### 10. Hook shipped in the instructing-agents plugin
Changed:
- `skills/instructing-agents/hooks/handoff_nudge.py` holds the gate from `gate-hook-current.py`, with the same
  behaviour: one nudge per context per agent, again after a `compact_boundary` or 400 KB of transcript, fail-open, off
  under `~/Workspace/scratch/ia-trial`. Its differences:
  - it also matches `Task`, for older Claude Code;
  - it keeps state in `$CLAUDE_PLUGIN_DATA` when the host sets it, falling back to
    `${CLAUDE_CONFIG_DIR:-~/.claude}/hooks/.state`, the old location;
  - the skip list can be overridden with `INSTRUCTING_AGENTS_NUDGE_SKIP`, whose default is the trial folder.
- `.claude-plugin/marketplace.json`: the instructing-agents entry gains an inline `hooks` object (PreToolUse on
  `Agent|Task|SendMessage|Bash`, running `python3 "${CLAUDE_PLUGIN_ROOT}/skills/instructing-agents/hooks/handoff_nudge.py"`).
  The version goes to 2.1.0.

Why inline, not `hooks/hooks.json` as the plan said:
- All four entries use `source: "./"`. A root `hooks/hooks.json` loaded with every plugin. I put one there
  temporarily: `claude plugin details skill-creator@ryannel-skills` then showed `Hooks (1)`; after removing it, 0.
- A file path in the marketplace entry passes `claude plugin validate` (with and without `--strict`), but at load time
  the plugin shows "failed to load", because "the file-path and array forms are not yet supported in a marketplace
  entry".
- The inline object loads. I corrected skill-creator's `references/writing.md` (lines 76–82), which had given the
  `hooks/hooks.json` form as the general rule.

Verified on a fresh install of all three plugins in a throwaway config:
- `claude plugin details` shows `Hooks (1) PreToolUse` for instructing-agents, and `Hooks (0)` for orchestrate and
  skill-creator.
- I ran the exact command from the entry, with `CLAUDE_PLUGIN_ROOT` set to the installed cache path, on PreToolUse
  payloads:
  - first Agent call refused with the nudge, resend passes;
  - a subagent (`agent_id`) gets its own nudge;
  - a commit message mentioning `claude -p` passes, while `cd x && codex exec` is refused;
  - after a `compact_boundary` it is refused once more, then passes;
  - a cwd under `~/Workspace/scratch/ia-trial-short` passes;
  - non-JSON input passes, exit 0;
  - with `CLAUDE_PLUGIN_DATA` set, state lands there.

Not verified: the hook firing inside a live Claude Code session. The `claude` CLI isn't signed in here, and neither is
the desktop app's bundled 2.1.317 when run as a child process ("Not logged in"). Without a session, I couldn't see
whether `CLAUDE_PLUGIN_DATA` is set for hook commands in 2.1.239; either way, the fallback works. The owner's own
settings hook, which runs the same logic, did fire on one of my Bash calls during this work.

### 11. Codex
Established on this machine, without a model turn, using the app's bundled CLI and its app-server (the API the app
uses):
- Codex 0.167 has plugins, marketplaces and hooks (`codex features list`: `plugins`, `hooks` stable). It reads
  `.claude-plugin/marketplace.json`. `codex plugin marketplace add <this repo>` listed all four plugins, and
  `codex plugin add instructing-agents@ryannel-skills` copied the repo to
  `$CODEX_HOME/plugins/cache/ryannel-skills/instructing-agents/2.1.0` and enabled it in `config.toml`.
- Only each entry's listed skills load. The app-server `skills/list` returned `instructing-agents:instructing-agents`,
  `orchestrate:{build,build-milestone,plan-module,review-milestone}` and `skill-creator:skill-creator`, all enabled.
  The model-visible list from `codex debug prompt-input` carries all of them except `orchestrate:build`. That one is
  explicit-only by design, through `disable-model-invocation` and `allow_implicit_invocation: false`. Plugin skills
  are namespaced, so the plugin's `skill-creator` doesn't clash with Codex's system `skill-creator`.
- Codex doesn't read hooks from a Claude marketplace entry: `hooks/list` returned no hooks after the install. To check
  that it reads plugin hooks at all, I made a test plugin with hooks in its own `.codex-plugin/plugin.json`.
  `hooks/list` showed that hook with `source: plugin` and `trustStatus: untrusted`, so a Codex plugin hook needs
  approval in the app before it runs. The binary also exports `PLUGIN_ROOT` and `CLAUDE_PLUGIN_ROOT`, and
  `PLUGIN_DATA`.
- The setup script writes the global AGENTS.md line, and `debug prompt-input` shows it in the model's instructions.
- So Codex gets the skills by plugin, not by copying into `~/.agents/skills`, and the AGENTS.md line instead of a hook.

Not shipped: a Codex hook. It would need the instructing-agents plugin to have its own source folder with a
`.codex-plugin/plugin.json`. With `source: "./"`, a root manifest would apply to all four plugins, the same problem as
on Claude. It would also need Codex's PreToolUse tool names for shell and `spawn_agent`/`send_input`, which I
couldn't observe without a turn, and an approval in the app.

Not verified: the Codex app UI showing the plugin; it runs against the real `~/.codex`. A Codex turn applying the
skill. A GitHub source (`ryannel/skills`), because the branch isn't pushed.

### 12. Per-repo setup
Changed:
- New `install.py` at the repo root, one command. Its flags are `--host claude|codex|both`, `--plugins` (default
  instructing-agents, orchestrate, skill-creator), `--scope user|project|local` for Claude, `--repo`, and `--source`
  (default this checkout; `ryannel/skills` for a portable project entry). It honours `CLAUDE_CONFIG_DIR` and
  `CODEX_HOME`.
- `README.md`:
  - a new "Setting up for Claude Code and Codex" section: what each host gets, the hook's behaviour, and what stays
    manual;
  - the instructing-agents section now points there instead of `npx skills`, which installs the skill without the
    hook.

What `install.py --repo` does:
- It writes `CLAUDE.md` holding `@AGENTS.md` only when the repo has AGENTS.md, has no CLAUDE.md, and `claude` is older
  than 2.1.277. The 2.1.277 cutoff is taken from the plan (item 7), not re-verified.
- With orchestrate, it runs `agent_loop.py profile` when ORCHESTRATE.md exists, and otherwise says `/plan-module`
  writes it. I didn't add an ORCHESTRATE.md writer: its values are project-specific, plan-module's first step already
  writes it from the template, and plan-module is in `skills/orchestration`. `profile` already parses strictly; the
  `--strict` flag in the plan doesn't exist on this base. If fold-b adds one, switch the call.

Verified:
- Fresh run in throwaway configs (`t1`, both hosts, user scope, repo with only AGENTS.md):
  - Claude: marketplace added, three plugins enabled, hook on instructing-agents only.
  - Codex: three plugins added, six skills listed, the AGENTS.md line written, the evaluator agent linked.
  - Repo: `CLAUDE.md` = `@AGENTS.md` written (2.1.239 < 2.1.277).
- A second run is idempotent: "already installed" and a version check on Claude, a fresh copy on Codex, and the
  AGENTS.md line left as is.
- `t2` (`--scope project`) wrote `.claude/settings.json` with `extraKnownMarketplaces` and `enabledPlugins`; the
  plugin is enabled at project scope with its hook.

## What stays manual
- **Replacing the owner's hand-installed hook** (not done; it's the real `~/.claude`). After merging to main, from the
  main checkout so the marketplace path lasts:
  1. Run `python3 ~/Workspace/skill-factory/install.py`, or add `--plugins instructing-agents`.
  2. Delete the PreToolUse entry in `~/.claude/settings.json` that runs `~/.claude/hooks/instructing-agents-gate.py`,
     and that file.
  3. Remove the standalone copies `install.py` names: `~/.claude/skills/{instructing-agents,skill-creator,
     plan-module,build-milestone,review-milestone,build}` and their symlinks in `~/.agents/skills`. Otherwise each
     description loads twice. `~/.codex/AGENTS.md` already has the line, and the script leaves it.
  4. Restart sessions.

  The desktop app's sessions read `~/.claude`, so the plugin should load there, but I haven't verified that.
- **Updates:** Claude Code re-copies a plugin only when its `version` changes, so bump it on each change. Codex
  re-copies on every `install.py` run.
- **ORCHESTRATE.md** is written by `/plan-module`.
- **A live check:** sign the `claude` CLI in, open a session in any repo outside the trial folder, ask for a subagent,
  and expect one refusal with the nudge, then the launch.
- **Codex hook:** see item 11.

## For the orchestration README (for you to place; I didn't edit it)
Suggested replacement for the install paragraph in `skills/orchestration/README.md` (lines 14–17):

> They link to each other's files, so install them together. From a clone of the skills repo,
> `python3 install.py --plugins orchestrate` installs the `orchestrate` plugin in Claude Code (skills and the planner
> and evaluator agents) and in Codex (the skills, read from the same marketplace, plus the evaluator agent through
> `build/scripts/install_agents.sh --global --codex-only`). `python3 install.py --plugins orchestrate --repo <repo>`
> also adds a `CLAUDE.md` holding `@AGENTS.md` when an older Claude CLI would otherwise miss AGENTS.md, and checks
> `ORCHESTRATE.md` with `agent_loop.py profile` once `/plan-module` has written it. `npx skills add` still works for the
> skills alone.

Two observations for the orchestration owner, not investigated:
- `install_agents.sh --global` writes to `$HOME/.claude/agents` and ignores `CLAUDE_CONFIG_DIR`.
- `claude plugin details orchestrate@ryannel-skills` reports `Agents (0)`, although the entry lists two agent files.
  This is unchanged by this branch. It may be how `details` counts, or the agents may not load from a `strict: false`
  entry; worth a look.

## Files
- `skills/instructing-agents/SKILL.md` (description, one sentence)
- `skills/instructing-agents/hooks/handoff_nudge.py` (new)
- `.claude-plugin/marketplace.json` (instructing-agents entry: inline hooks, 2.1.0)
- `skills/skill-creator/references/writing.md` (hook-packaging host fact corrected)
- `install.py` (new)
- `README.md` (setup section; instructing-agents install line)
