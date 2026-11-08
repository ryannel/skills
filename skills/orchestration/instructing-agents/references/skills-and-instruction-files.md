# Skills and standing instruction files

Contents:
- [Skills](#skills)
- [AGENTS.md and CLAUDE.md](#agentsmd-and-claudemd)

The mechanics of building, packaging and evaluating a skill belong to skill-creator (Anthropic's, or Codex's bundled
`$skill-creator`). This page covers what to write in a skill.

## Skills

A skill is a folder with a `SKILL.md` and optional `references/`, `scripts/` and `assets/`. The `SKILL.md` frontmatter
holds `name` and `description`. Claude Code and Codex share the format (the agentskills.io standard).

### The description is the trigger

Agents see only the name and description until they decide to load a skill. When too many skills are installed, the
listing loses detail:
- **Codex:** the list is capped at about 2% of context, or 8,000 characters. Codex shortens descriptions first, then
  drops skills.
- **Claude Code:** each entry is capped at 1,536 characters, including `when_to_use`. When the listing overflows its
  budget of about 1% of context, whole descriptions are dropped, starting with the least-used skills.

Rarely used skills lose their descriptions first, so front-load the trigger words.

Writing the description:
- **Write it in the third person.** Say what the skill does and when to use it, with the main use case first.
- **Add a "Not for…" line** when a near neighbour would otherwise fire.
- **Keep it short and specific.** Bad: "Use when working with databases, queries, models, or persistence." Good: "Use
  when adding or changing a migration, or reviewing its rollout." Long or emphatic descriptions load skills that don't
  help, and they can contradict each other.
- **On the Claude side, undertriggering is the commoner fault.** Name the adjacent phrasings a user might type. Don't
  swing into emphasis.
- **Respect the limits.** The name is at most 64 lowercase, hyphenated characters and contains neither "claude" nor
  "anthropic". The description is at most 1,024 characters.

### Progressive disclosure

- **The body is a router, not a manual.** For several workflows, keep `SKILL.md` minimal and point to one reference per
  workflow, saying when to read each. Reading a skill costs context.
- **Keep the body under about 500 lines; far less is usually better.** Keep references one level deep. Give any
  reference over 100 lines a contents list.
- **Put key instructions near the top.** After compaction, Claude Code re-attaches only the first part of an invoked
  skill.
- **Write it as standing instructions.** An invoked skill stays in the conversation and isn't re-read.
- **Keep each rule in one place,** and point to it from elsewhere.

### Content

- **Write only what the agent lacks.** Leave out what it knows or can read for itself, and make each paragraph justify
  its tokens.
- **Match freedom to fragility.**
  - Heuristics and the outcome for open work.
  - A template or pseudocode where there is a preferred pattern.
  - Exact steps, a copyable checklist or a script for fragile, sequence-critical operations.

  OpenAI says elaborate itineraries and step recipes now hurt Astra. Anthropic still recommends clear sequential steps
  and checklists for complex operations. The two fit together: steps where the order is fragile, judgment everywhere
  else.
- **Explain the why instead of shouting.** Anthropic's skill-creator calls capitalised ALWAYS/NEVER a yellow flag:
  reframe with the reason. Its older best-practices page still shows "MUST" and "ALWAYS use this exact template" for
  machine-consumed output. Keep strict wording for strict formats only.
- **Use examples over adjectives.** A few diverse input/output pairs convey style better than a description.
- **Use scripts for deterministic work.** A script should handle its own errors. Say whether the agent runs it or reads
  it.
- **Use one term per concept.** Keep time-sensitive facts out of the body, and keep superseded patterns in an "old
  patterns" note.
- **Give each skill one job.** A repository skill steers every contributor's agent, so keep model-specific corrections
  out of it. Put a correction for one model in that model's goal or brief.
- **Put rules that must hold in hooks or permissions.** Prose is context, not enforcement.

### Frontmatter and policy knobs

- **Claude Code:**
  - `disable-model-invocation: true` for task skills with side effects, so they run only when the user asks;
  - `user-invocable: false` for Claude-only skills;
  - `when_to_use`;
  - `hooks` for rules that must hold while the skill is active;
  - `context: fork` to run the skill in a subagent, which can't see the conversation, so write it to stand alone.
  - Unknown fields are ignored silently.
- **Codex:** `agents/openai.yaml` holds:
  - interface fields such as display name and short description;
  - `policy.allow_implicit_invocation` (default true; false means explicit `$skill` only);
  - tool dependencies.

### Testing

- **Compare with and without the skill.** Run realistic tasks both ways in fresh sessions, since leftover context hides
  gaps. When revising a skill, compare against the previous version.
- **Test triggering** with realistic, messy prompts, including some that should fire and near misses that shouldn't.
- **Watch how agents use it.**
  - Files never opened may be unneeded or badly signposted.
  - Files re-read every time belong in the body.
  - Helper code every run rewrites belongs in `scripts/`.
- **Generalise from failures.** Don't patch for the specific test cases.

### Where skills live

- **Codex:** `.agents/skills` in a repository (scanned from the current directory up to the root) and `~/.agents/skills`
  for the user. Symlinks are followed.
- **Claude Code:** `.claude/skills` in a project and `~/.claude/skills` for the user. Personal skills override project
  ones with the same name.
- **One shared copy:** keep the authoritative folder in `~/.claude/skills` and symlink it into `~/.agents/skills`.
  Codex documents that it follows symlinks. On this machine (7 Nov 2026), a symlinked skill didn't show in Claude
  Code's / list (cause unconfirmed), so the real folder lives there. A new skill appears only in sessions started
  after it is added.

## AGENTS.md and CLAUDE.md

These load into every session, so each line costs attention on every task.
- **Keep to stable norms the agent can't infer:** commands, conventions, boundaries, where things live, and what needs a
  human. Move procedures into skills, which load on demand. Leave out architecture the agent can read for itself.
- **Point by use, not mandate.** Write "Use X.md when Y", not "read X.md, Y.md and Z.md before every edit".
- **Drop old pushes.** "Run the tests" encouragement makes Astra over-test. "Keep going" and "be thorough" lines make
  current Claude models over-work. Give standing permission for the safe test loop instead.
- **Revisit "ask first" language.** Strong wording written to stop older models over-reaching makes Astra stop work it
  should continue. State the real boundaries accurately: irreversible, destructive, outward-facing, spending, and other
  people's areas.
- **State precedence:** the user's instructions win over skill guidance.
- **Layer by directory.** Codex concatenates from the root down, closer files win, and it stops at 32 KiB by default.
  Put overrides next to the work they govern.
- **Prune regularly.** For each line, ask whether removing it would cause a mistake you have seen. A line that keeps
  being ignored usually means the file is too long; more emphasis won't help.

A cheap test for a suspect instruction is to replay one real session prompt twice from the same snapshot, once with the
line and once without it. Compare quality, tool calls, tokens and time.
