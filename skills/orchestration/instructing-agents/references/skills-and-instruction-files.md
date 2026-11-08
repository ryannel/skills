# Skills and standing instruction files

Contents:
- [Skills](#skills)
- [AGENTS.md and CLAUDE.md](#agentsmd-and-claudemd)

How to build, package and test a skill belongs to `skill-creator`, which sits alongside this skill. This page is about
what to write in a skill.

## Skills

A skill is a folder. It holds a `SKILL.md`, and it can also hold `references/`, `scripts/` and `assets/`. The
frontmatter of `SKILL.md` holds `name` and `description`. Claude Code and Codex use the same format, which is the
agentskills.io standard.

### The description is the trigger

An agent sees only a skill's name and description until it decides to load the skill. When too many skills are
installed, the listing loses detail, and each harness loses it in its own way.

In Codex, the list is capped at about 2% of context, or 8,000 characters. Codex shortens descriptions first, and then
drops skills.

In Claude Code, each entry is capped at 1,536 characters, and that includes `when_to_use`. When the listing goes over
its budget of about 1% of context, whole descriptions are dropped, starting with the skills used least.

Either way, rarely used skills lose their descriptions first. So put the trigger words at the front.

Here's how to write the description.

Write it in the third person. Say what the skill does and when to use it, with the main use case first.

Add a "Not for…" line when a nearby skill would otherwise fire instead.

Keep it short and specific. A bad description is "Use when working with databases, queries, models, or persistence." A
good one is "Use when adding or changing a migration, or reviewing its rollout." Long or emphatic descriptions load
skills that don't help, and they can contradict each other.

On the Claude side, the more common fault is a skill that doesn't fire when it should. So name the nearby phrasings a
user might type. Don't swing the other way into emphasis.

Stay inside the limits. The name is at most 64 characters, lowercase and hyphenated, and it can't contain "claude" or
"anthropic". The description is at most 1,024 characters.

### Progressive disclosure

The body of a skill is a router, not a manual. Reading a skill costs context, so don't make the agent read more than
it needs. If the skill covers several workflows, keep `SKILL.md` small and point to one reference for each workflow,
saying when to read each one.

Keep the body under about 500 lines, and far less is usually better. Keep references one level deep. Any reference
over 100 lines gets a contents list.

Put the key instructions near the top. After compaction, Claude Code only re-attaches the first part of a skill that
was invoked.

Write it as standing instructions. Once a skill is invoked, it stays in the conversation and isn't read again.

Keep each rule in one place, and point to it from everywhere else.

### Content

Write only what the agent doesn't already have. Leave out what it knows, or can read for itself. Each paragraph costs
tokens, so each one has to earn them.

Match how much freedom you give to how fragile the work is:

- For open work, give heuristics and the outcome.
- Where there's a preferred pattern, give a template or pseudocode.
- For fragile operations where the order matters, give exact steps, a checklist that can be copied, or a script.

OpenAI says that elaborate itineraries and step-by-step recipes now hurt Astra. Anthropic still recommends clear
sequential steps and checklists for complex operations. These two fit together. Use steps where the order is fragile,
and judgment everywhere else.

Explain the reason instead of shouting. Anthropic's skill-creator calls capitalised ALWAYS and NEVER a yellow flag, and
says to reword the rule around its reason. Its older best-practices page still shows "MUST" and "ALWAYS use this exact
template" for output a machine will consume. So keep strict wording for strict formats only.

Use examples instead of adjectives. A few varied pairs of input and output show a style better than a description of
it does.

Use scripts for work that should come out the same every time. A script should handle its own errors. Say whether the
agent runs it or reads it.

Use one term for each concept. Keep facts that will go out of date out of the body. Keep patterns that have been
replaced in an "old patterns" note.

Give each skill one job. A repository skill steers every contributor's agent, so keep corrections for a particular
model out of it. A correction for one model goes in that model's goal or brief.

Rules that must hold go in hooks or permissions. Prose is context. It doesn't enforce anything.

### Frontmatter and policy knobs

Claude Code has these:

- `disable-model-invocation: true`, for task skills with side effects, so they run only when the user asks
- `user-invocable: false`, for skills only Claude uses
- `when_to_use`
- `hooks`, for rules that must hold while the skill is active
- `context: fork`, to run the skill in a subagent. The subagent can't see the conversation, so write the skill to make
  sense on its own.

Claude Code ignores fields it doesn't know, and it doesn't tell you.

In Codex, `agents/openai.yaml` holds these:

- interface fields, such as the display name and short description
- `policy.allow_implicit_invocation`, which defaults to true. False means the skill runs only when called explicitly
  with `$skill`.
- tool dependencies

### Testing

Compare the agent with and without the skill. Run realistic tasks both ways, each in a fresh session, because context
left over from earlier hides gaps. When you revise a skill, compare it against the previous version.

Test whether it triggers. Use realistic, messy prompts. Include some that should fire it, and near misses that
shouldn't.

Watch how agents use it. A file that's never opened may not be needed, or may be badly signposted. A file that's read
every time belongs in the body. Helper code that every run writes again belongs in `scripts/`.

Generalise from failures. Don't patch the skill to pass the specific test cases.

### Where skills live

Codex looks in `.agents/skills` in a repository, scanning from the current directory up to the root. It also looks in
`~/.agents/skills` for the user. It follows symlinks.

Claude Code looks in `.claude/skills` in a project, and in `~/.claude/skills` for the user. A personal skill overrides a
project skill with the same name.

To keep one shared copy, put the real folder in `~/.claude/skills` and symlink it into `~/.agents/skills`. Codex
documents that it follows symlinks. On this machine (7 Nov 2026), a symlinked skill didn't show up in Claude Code's /
list, and the cause isn't confirmed. That's why the real folder lives on the Claude side. A new skill only appears in
sessions started after it was added.

## AGENTS.md and CLAUDE.md

These files load into every session. So every line costs attention on every task, whether it's relevant or not.

Stick to stable norms the agent can't work out for itself. That means commands, conventions, boundaries, where things
live, and what needs a human. Move procedures into skills, which load only when needed. Leave out architecture the
agent can read for itself.

Point to files by when to use them, not as a mandate. Write "Use X.md when Y". Don't write "read X.md, Y.md and Z.md
before every edit".

Drop old pushes. Encouragement like "run the tests" makes Astra test too much. Lines like "keep going" and "be
thorough" make current Claude models work too much. Give standing permission for the safe test loop instead.

Look again at "ask first" language. Strong wording that was written to stop older models over-reaching makes Astra
stop work it should continue. State the real boundaries accurately. Those are things that are irreversible,
destructive, outward-facing, cost money, or are in other people's areas.

Say which instructions win. The user's instructions win over a skill's guidance.

Layer the files by directory. Codex joins them together from the root down, and closer files win. It stops at 32 KiB
by default. So put overrides next to the work they govern.

Prune regularly. For each line, ask whether removing it would cause a mistake you've actually seen. If a line keeps
being ignored, that usually means the file is too long. More emphasis won't help.

There's a cheap way to test a line you suspect. Replay one real session prompt twice from the same snapshot, once with
the line and once without it. Then compare quality, tool calls, tokens and time.
