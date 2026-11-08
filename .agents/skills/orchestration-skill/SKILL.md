---
name: orchestration-skill
description: Authoring spec for the orchestration domain (skills/orchestration). Use when adding or changing a skill, agent file or script in that domain. Not for the generative-media domain (media-model-skill).
metadata:
  internal: true
---

# Writing an orchestration skill

**Outcome:** a skill that works installed in any repository, in Claude Code and Codex, and reads as part of the suite.

- **Generic, configured by the profile.** Nothing project-specific: paths, commands, targets, owner rules and domain
  standards come from the project's `ORCHESTRATE.md` ([template](../../../skills/orchestration/plan-module/references/profile.md)).
  If a skill needs a new setting, add it to the template, and to `agent_loop.py`'s `profile()` if the loop reads it.
- **Written to `instructing-agents`.** Outcome, done-when, constraints and pointers; reasons with rules; no emphasis or
  pressure lines; descriptions that say when to use and when not, and don't overlap a sibling's.
- **Model and effort named** in each skill's first line and each agent file, so nothing inherits a default.
- **One writer per done-when field,** as listed in `plan-module/references/done-when.md`. A change to who writes what
  updates that list, the skills that write, and the loop.
- **Links stay inside the domain** (`../sibling/…`); installs flatten the domain folder.
- **Scripts are stdlib Python** with tests in `tests/orchestration/` (not shipped with the skill). Run
  `python3 -m unittest discover tests/orchestration` before committing. Don't call `claude -p` from scripts: it bills
  through the API.
- **Agent files** for Claude live in `build-parallel/agents/claude/` and are listed in the marketplace entry; Codex twins
  live in `build-parallel/agents/codex/` and install with `install_agents.sh`.
- **Lean by default.** Each SKILL.md stays near 400 words: outcome, done-when, method, permissions. Add a line only for
  a failure that has been seen, and record deliberate omissions in the domain README.
- **Check packaging** with `claude plugin validate .` and `npx skills add ./ --list`.
