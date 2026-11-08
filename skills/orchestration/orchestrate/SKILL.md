---
name: orchestrate
description: Entry point to the orchestrate process for building software with AI agents (web apps, native apps, CLI tools, libraries, engines). Explains the levels and commands, sets a project up with its ORCHESTRATE.md profile, and reports where each module stands. Use when adopting the process in a repository, asking how planning, building and review fit together, or asking for status across modules. Not for doing a level's work (plan-project, plan-module, build-milestone, review-milestone, build-parallel).
---

# Orchestrate

**Outcome:** the project can run the process, and whoever asked knows where things stand and which command comes next.

The process is the planner, generator, evaluator and oracle pattern from Anthropic's long-running harness work, with
one lead for fan-out. It runs in Claude Code or Codex. Rationale and sources: [process](references/process.md).

## Levels and commands

| Level | Command | Produces | Default model and effort |
|---|---|---|---|
| Project | `/plan-project` | Purpose and goal, module map, build order, shared contracts, a brief per module | Claude Opus 5.5, high |
| Module | `/plan-module <module>` | The module's design, its milestones and a done-when file | Claude Opus 5.5, high |
| Milestone | `/build-milestone <module>` | The next milestone, built, verified and integrated | Codex `gpt-6.1-sol` or Claude Opus 5.5, medium |
| Milestone | `/review-milestone <module>` | A verdict on a milestone from a clean context | Claude Opus 5.5, medium |
| Fan-out | `/build-parallel <module> …` | Several modules' milestones at once, under one lead | Claude lead at medium; Codex generators |

Each command reads the level above it and writes only its own. A change needed above goes up as a proposal, and work
that doesn't depend on it carries on. The project's `ORCHESTRATE.md` can override any model or effort; every launch
names both.

**Speed 1** is one chat: the owner runs `/build-milestone` in Claude Code or Codex, and can switch vendor at a
milestone boundary, because the handover is the plan, the done-when file and the progress note. **Speed 2** is
`/build-parallel`, one Claude lead running Codex generators through `scripts/agent_loop.py`, with evaluator and
planner subagents.

## Set a project up

Done when the repository has:
1. **`ORCHESTRATE.md` at its root**, filled in from [the profile template](references/profile.md). Derive what you can
   from the repository (check command, targets, where docs live) and ask the owner, in one round, only for what you
   can't: purpose, what goes to them, integration policy and licences.
2. **A pointer in `AGENTS.md`** (and `CLAUDE.md` if the project uses it): one line saying work follows the orchestrate
   process as configured in `ORCHESTRATE.md`. Propose the edit to the owner if those files have their own uncommitted
   changes.
3. **The agents installed** for both vendors, by running `scripts/install_agents.sh <repo>` from this skill. It
   links the evaluator, planner and researcher agent definitions into the project's `.claude/agents/` and
   `.codex/agents/`.
4. **Project guidance linked from the profile,** not copied into these skills. Domain rules (an engine's hot-path
   rules, a web app's accessibility standard, a CLI's compatibility promise) live in the project, usually as a project
   skill or doc, and the profile says which level reads them.

If the project already has plans in another shape, leave them; `/plan-module` converts a module when it next plans it.

## Status

`python3 <build-parallel>/scripts/agent_loop.py status --module <M> --worktree <repo>` lists a module's milestones,
states, fail counts and passing items. `agent_loop.py quota` forecasts the Codex weekly limit. For an overview, read
each module plan's status lines (`Milestone:`, `Now:`, `Next:`, `Blocked:`).
