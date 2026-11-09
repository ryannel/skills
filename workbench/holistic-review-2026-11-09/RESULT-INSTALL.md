# Decisions 10–16: install, hook and shared skills

9 November 2026, branch `fix-install` (worktree `~/Workspace/skill-factory-fix-install`), on top of `0b484b2`. Opus 5.5,
medium effort. The synthesis and both reviews are untracked files in `~/Workspace/skill-factory-integrate/workbench/
holistic-review-2026-11-09/`, not in this worktree, so this file starts the folder here.

Host versions: Claude Code 2.1.239 (the `claude` on PATH) and 2.1.317 (the desktop app's bundled CLI, put first on
PATH through a symlink for some runs), and the Codex CLI 0.167.0-alpha.3.2 inside `/Applications/ChatGPT.app`. Every
install ran with a throwaway `HOME`, `CLAUDE_CONFIG_DIR` and `CODEX_HOME` in the session scratchpad. The owner-shaped
homes copied the real layout: the six standalone skills in `~/.claude/skills`, symlinks to them in `~/.agents/skills`
beside a real `find-skills`, agent links into the standalone `build` copy in `~/.claude/agents` and `~/.codex/agents`,
an unrelated Codex skill, the real `settings.json` with its hand-installed gate hook, and the real `~/.codex/AGENTS.md`.
The real `~/.claude`, `~/.agents` and `~/.codex` weren't changed (mtimes compared before and after).
`skills/orchestration` wasn't touched. Nothing pushed.

| Decision | Status | Commit |
|---|---|---|
| 10. Install from this checkout | resolved | `f5dc44f` |
| 11. Migration | resolved, plus an agents gap the reviews didn't see | `f5dc44f` |
| 12. Repo setup reports what it checked | resolved | `f5dc44f` |
| 13. Hook matching | resolved | `cdf23ee` |
| 14. Plugin facts | resolved; one reviewer claim narrowed | `9d96a32`, `ca74608` |
| 15. Claims match evidence | resolved within these files | `9d96a32`, this file |
| 16. Wording | resolved | `ca74608`, `9d96a32` |

## 10. Install from this checkout (A4)
`install.py` reads the registered source from `claude plugin marketplace list --json` and `codex plugin marketplace
list --json`. If it differs from the checkout (or `--source`), it prints a `!!` line, removes the marketplace and
adds it from the requested source. On Claude, removing a marketplace uninstalls its plugins, so the run reinstalls
every user-scope plugin it had, and prints a reinstall command for any at project or local scope. A cached Claude copy
that differs from the checkout at the same version is reinstalled (`uninstall --keep-data`, then `install`). The run
ends by printing where each plugin loads from and the checkout's revision.

Checked: a home with `ryannel-skills` registered on both hosts from an old copy of the repo, with
`generative-media-skills` and `instructing-agents` installed on Claude 2.1.239. After the run both hosts list the new
checkout, all four Claude plugins are reinstalled, and the installed hook files carry the new code (the old copy's
don't). Stale copy: installed from a scratch copy of the checkout, edited its hook, re-ran; the cached copy was
reinstalled and holds the edit. Unit tests cover the source comparison (`tests/install`).

## 11. Migration (A8, F2)
Before any host command, `install.py` looks for copies of the selected plugins' skills in `~/.claude/skills`,
`~/.agents/skills` and `~/.codex/skills`. It counts a copy as one of these skills only when its `SKILL.md` is
byte-identical to a committed version in this repo. It also finds links into those copies, and settings.json hook
entries that run `instructing-agents-gate.py` or `handoff_nudge.py` outside `${CLAUDE_PLUGIN_ROOT}`. Without the flag
it lists them and exits 1 with nothing changed. With `--replace-standalone` it removes the links, moves the folders to
`~/.ryannel-skills-backup/<time>/`, and copies `settings.json` there. It then deletes only the old hook entries from
`settings.json`, removing any group or event left empty, and writes `MOVED.txt`. A same-named skill that matches no
committed version is reported and left alone. The gate script file stays, unused.

The reviews missed one consequence. Removing the standalone `build` copy removes the Claude agent links into it, and
the plugin doesn't replace them. On both 2.1.239 and 2.1.317, `claude plugin details orchestrate@ryannel-skills` shows
`Agents (0)`. A minimal probe marketplace showed why. An entry's `agents` list was ignored, while a root `agents/`
folder loaded for every entry. The docs say the entry's list should replace that folder. So `install.py` now links
both orchestrate agents into `~/.claude/agents` from the installed copy when `details` shows no agents. The loop's
`agent_installed()` looks there, so it finds them without decision 7's change. The Codex evaluator is now linked from
the plugin cache rather than the checkout (A8's side point), by running the cached `install_agents.sh`.

Checked on owner-shaped homes, with 2.1.239 (`shapeA`) and with 2.1.317 (`shapeE`), both hosts:
- Without the flag: exit 1. It listed 12 skill entries, 3 agent links and the settings hook, and changed nothing.
- With the flag: exit 0. `~/.claude/skills` was empty afterwards, and `~/.agents/skills` held only `find-skills`.
  The PreToolUse entry was gone, and every other `settings.json` key matched the real file (`enabledPlugins` and
  `extraKnownMarketplaces` were added). The agents were linked from the plugin, and the Codex evaluator from the cache.
- A third run was clean.
- `claude plugin details instructing-agents` shows exactly one hook. The installed hook copy, run on payloads, refused
  a `timeout 60 claude -p` launch once and passed a commit message naming `codex exec`.
- Unit tests (`tests/install`) check the refusal, the move, that unrelated hooks and skills are kept, and the backup.

## 12. Repo setup (A7)
A7 holds. `--repo` now reports from what it checked. If the repo's `CLAUDE.md` or `.claude/CLAUDE.md` imports
AGENTS.md, it says so. If a `CLAUDE.md` exists without the import, it says Claude reads that file instead, and doesn't
edit it. If a `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` sits in the repo or above it, or the CLI is older
than 2.1.277 or missing, it writes `CLAUDE.md` holding `@AGENTS.md` and names the reason. The user's own
`~/.claude/CLAUDE.md` doesn't count. Otherwise it says Claude reads AGENTS.md and names the version and the files
checked. A failed `agent_loop.py profile` now makes the run exit 1. The logic mirrors the loop's
`instruction_warnings()`. It doesn't import that function, because another agent is editing `agent_loop.py` now.

Checked with real runs:
- AGENTS.md only on 2.1.317: reported as read, nothing written.
- `CLAUDE.local.md`, or a parent folder's `CLAUDE.md`: import written, with the shadowing file named.
- An existing `CLAUDE.md`: warned and left unedited.
- 2.1.239: import written, with the version named.
- An invalid `ORCHESTRATE.md`: exit 1, `failed: … didn't validate`.

Unit tests cover the same cases.

## 13. Hook matching (A9, F8)
Before matching, the hook blanks quoted spans and heredoc bodies, keeping the rest of a heredoc's first line. It
accepts `env` (with options), `nohup`, `time`, `timeout N` and `NAME=value` prefixes. Newlines and backticks now count
as separators. It also matches `claude --print` and `codex` options before `exec`. The docstring now says the hook
ships inline in `marketplace.json`, and what it doesn't cover: launches inside `sh -c '…'` or a script. As decided,
the loop's own launches aren't matched.

I didn't act on A9's request to drop the default `~/Workspace/scratch/ia-trial` skip: the owed trigger trial depends
on it. The README documents it, and `INSTRUCTING_AGENTS_NUDGE_SKIP` overrides it.

Checked: `tests/instructing-agents/test_handoff_nudge.py` has 20 launch spellings that must match, including every one
both reviews found missed, and 11 that must pass, including the reviewers' quoted-separator false positives and heredoc
bodies. It also covers the once-per-context refusal, the re-nudge after `compact_boundary`, and fail-open on bad
input. The owner's real gate (the old regex) refused several of my own Bash calls during this work, the same failure.

## 14. Plugin facts (F5)
F5's first point is right, but not in the way it reads. The update rule depends on the version, and both behaviours
were reproduced. 2.1.317 records `readFromFolder` and loads in place ("nothing to update; edits take effect at the next
session start"). 2.1.239 copies into the cache and wouldn't re-copy an edit without a version bump. The README,
`writing.md` and an `install.py` comment now state both, with their versions.

The `strict: false` conflict is confirmed by the manifest reference. The README now warns against a root
`.claude-plugin/plugin.json`.

F5 overstates `testing.md`: it puts the eval manifest in the skill's own folder, which conflicts only when that folder
is a `strict: false` entry's source, as in a single-skill repo. Here it would be `skills/skill-creator/`, which no
entry uses as a source. `testing.md` now says not to put one in such a folder.

I also corrected the README's claim that the plugin brings the Claude agents (see 11).

## 15. Claims match evidence (A10)
The README's setup section now names the versions it was checked on and ends with what isn't verified: the plugin
hook in a live session, a post-compaction handoff, and the description-only trigger trial. The owed items are below.
The receiver and trigger records A10 cites live in other workbench folders and weren't changed. A10 says they already
acknowledge the gaps.

## 16. Wording (A12, A11, F10)
- **"Only fragile steps" (A12).** It now reads "a list … you made up tends to cap the agent", and "give steps when the
  order or completeness matters, as in a data migration". This matches `writing.md` and Anthropic's guidance. The
  SKILL.md body went from 1,511 to 1,509 words, and no description changed.
- **Where skills live.** `writing.md` has a dated paragraph on plugins: namespaced skills, in-place versus copied, the
  missing entry agents, and that a standalone copy duplicates the plugin's.
- **Stale values.** `autoCompactWindow` is now 500,000, as of 9 November, and `freshness.json`'s `updated` is
  2026-11-09.
- **One install route.** The root README sends instructing-agents, orchestrate and skill-creator through
  `install.py`. The `npx` and `/plugin` routes remain for the generative-media skills only.

From F10, the 2.1.317 versus 2.1.239 dates in `hosts-and-models.md` are both stated, so I left them. The
`BUILD_TEMPLATE` wording is in orchestration.

## Checks run
- `check_skill.py` passes on `skills/instructing-agents` and `skills/skill-creator`.
- `claude plugin validate .` passes.
- `tests/install` (10 tests), `tests/instructing-agents` (4) and `tests/orchestration/test_check_skill.py` pass.
- The orchestration loop tests weren't run, since nothing there changed.

## Owed (not code)
- **Owner or lead, after merge:** run `python3 ~/Workspace/skill-factory/install.py --replace-standalone` from the
  main checkout, then restart sessions. On 2.1.317 the plugins read that folder in place, so it must stay put.
- **Owner:** the live hook check, the post-compaction handoff and the trigger trial listed in the synthesis.
- **Orchestration:** decision 7's resolver should treat linked agents in `~/.claude/agents` as installed. It already
  does, but plugin-provided agents never appear on these Claude versions. `install_agents.sh --global` writes
  `$HOME/.claude/agents` and ignores `CLAUDE_CONFIG_DIR`.
- **Side effect:** re-registering a marketplace deletes the Claude plugins' data folders, which lose only the hook's
  nudge markers. A source switch therefore costs one extra nudge per context.
