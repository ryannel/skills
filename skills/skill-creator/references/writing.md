# Writing a skill

Contents:
- [The folder](#the-folder)
- [The description](#the-description)
- [The body](#the-body)
- [The voice](#the-voice)
- [Frontmatter options](#frontmatter-options)
- [Where skills live](#where-skills-live)

## The folder

A skill is a folder with a `SKILL.md` in it. `SKILL.md` starts with frontmatter holding a `name` and a `description`,
and then the instructions. The folder can also hold `references/` for longer material the agent reads when it needs
it, `scripts/` for code it runs, and `assets/` for files it uses in its output. Claude Code, Codex and many other
agents read the same format, from the agentskills.io standard.

The name is lowercase with hyphens, at most 64 characters, and matches the folder. The description is at most 1,024
characters. Anthropic also reserves the words "claude" and "anthropic" in names, so leave them out if the skill might
be used there.

A skill that links to files in a sibling skill only works when both are installed together. Either keep the skill
self-contained, or say in the description that it comes as part of a set.

## The description

Until an agent decides to load a skill, the name and description are all it sees. So the description is the trigger.
If it's vague, the skill fires at the wrong times or never fires at all.

Say what the skill does, then when to use it, in the third person. Name the phrasings a user might actually type. A
user who wants a dashboard might say "chart", "metrics" or "KPI page" without ever saying "dashboard". If a
neighbouring skill could fire instead, end with a "Not for…" line that names it. That's all a description needs.

Be specific rather than loud. "Use when adding or changing a database migration, or reviewing its rollout" beats "Use
for anything involving databases". Anthropic's own skill-creator suggests making descriptions "a little pushy",
because Claude used to under-trigger skills. OpenAI's guidance for GPT-6 Astra warns the other way: broad
descriptions load skills that don't help. Specific wins both ways, so start specific and widen only if testing shows
the skill misses.

Put the trigger words near the front, and keep the description to two or three sentences. When too many skills are
installed, harnesses shorten or drop descriptions to fit, and the end of a long description is the first thing to go.

## The body

Write only what the agent doesn't already know. Every paragraph costs attention on every run, so every paragraph has
to earn its place. A good test for a line is to ask what mistake the agent would make without it. If you can't name
one, cut it.

There are two kinds of line that pass that test. One is a correction: a mistake someone has actually watched an agent
make. Add those only after seeing the mistake, keep each one narrow, and say why it's there. Most bloat comes from
fixing mistakes nobody has seen. The other kind is a contract: an input the skill needs, a file format a program
reads, or a state another agent depends on. Write those from the start, and write them exactly, because the agent
can't guess them.

Say what finished looks like and how to prove it, what the agent may and may not touch, and where to find things.
Leave the method to the agent wherever many methods would work. Match the freedom to how fragile the work is. Open
work gets a goal and a few rules of thumb. Work with a preferred pattern gets a template. Fragile work where the order
matters, like a migration, gets numbered steps or a script.

Keep `SKILL.md` short, and treat it as a map. If the skill covers several workflows, give each its own reference and
say when to read it: "Read aws.md when deploying to AWS." Keep references one level deep, and give any reference over
about 100 lines a contents list. Keep the most important instructions near the top, because some harnesses only
re-attach the start of a skill after compacting the conversation.

Use examples instead of adjectives. One short input and output pair shows a style better than a paragraph describing
it.

Put repeatable work in scripts. If every run would write the same helper, write it once and bundle it. Say whether
the agent should run it or read it.

Keep each rule in one place and point to it from elsewhere. Use one word for each idea throughout.

Anything that truly must never happen belongs in a hook, a permission rule, a sandbox or a script that checks it.
Prose is advice, and agents weigh it against everything else. When the skill depends on such a hook or script, ship
it inside the skill's package together with its setup step, so installing the skill installs the mechanism. A hook
someone added to their own settings by hand doesn't travel to the next machine or repo. In a Claude Code plugin, that
means a `hooks/hooks.json` that calls a bundled script through `${CLAUDE_PLUGIN_ROOT}`, and installing the plugin
installs the hook (Claude Code 2.1.239, checked 9 November 2026). Where a host can't install it from the package,
bundle a setup script and say what it does, and what stays manual.

Facts about a host, like a folder it reads, a flag, a limit or a minimum version, change between releases. Write
each with the date you checked it and the host version you checked it on, so a reader can tell when it has gone
stale and what to re-check.

## The voice

Write the way Randall Munroe explains things in "What If?": plain words, short sentences, concrete examples. Leave
out the jokes, because agents can take them literally and they cost attention.

Give the reason with the rule. Anthropic's prompting guide shows that Claude generalises from the explanation:
"Don't use ellipses, because a text-to-speech engine reads this aloud" lets the agent handle cases you never listed,
and "NEVER use ellipses" doesn't. OpenAI's Astra guidance makes the matching point from the other side: define
completion and where to stop, and stop prescribing steps. Both come to the same thing. The agent should know what you're
after and why.

Say the obvious out loud only when agents have been seen to skip it, and attach what happened. "Agents that skipped
the list looked at whatever caught their eye and missed the broken parts" earns its place. An obvious line with no
story is just a line the agent already knew.

Skip the shouting. Capital letters and words like MUST make current models apply a rule too widely. The exception is
an exact format a program will read, where strict wording is right.

Use full sentences for explanation. Where precision matters more than flow, use the structure that holds it exactly.
That means a table for who changes which field and when, an exact list of allowed values, or numbered steps where the
order matters. Plain prose and exact contracts sit side by side. What doesn't work is the packed style in between:
bold phrases at the start of every bullet, chains of semicolons, and clauses squeezed together to save words. It
looks efficient, but it's hard to read, it hides the reasons, and it isn't precise either.

Here's the difference. This is the packed style:

> **Verify on target.** Capture from exact build; cover edge conditions; label proxies; no claims without evidence.

And this is the plain one:

> Look at the output yourself, using the exact build on its real target. Passing tests tell you the code does what the
> tests say. They don't tell you it looks right. If you used a stand-in, like a Mac standing in for an iPhone, say so.

The plain version is longer, but each sentence does one job, and the agent knows why.

Define the few words the skill depends on, such as "done", "blocked" or "fail", the first time you use them. Then use
them the same way everywhere.

## Frontmatter options

Claude Code reads a few extra fields. Other hosts ignore them, and Anthropic's API may refuse a skill that has them.
- `disable-model-invocation: true` makes the skill run only when the user asks for it. Use it for skills with side
  effects, like deploying.
- `user-invocable: false` hides the skill from the user's menu, for skills only the agent uses.
- `when_to_use` adds trigger guidance alongside the description.
- `model` and `effort` switch the model and effort while the skill is active, for the rest of that turn. Use them
  when the skill needs a particular model, rather than writing "run as…" in the body, which the running model can't
  act on.
- `context: fork` runs the skill in a subagent. That subagent can't see the conversation, so the skill has to make
  sense on its own.

Claude Code ignores fields it doesn't recognise, and doesn't warn you. Codex reads extra settings from
`agents/openai.yaml` in the skill folder, including a display name and `policy.allow_implicit_invocation`. Set that
to false for the same effect as `disable-model-invocation`.

## Where skills live

These facts change between releases. They were checked on 8 November 2026. The host versions weren't recorded then,
so add them at the next check.

Claude Code looks in `.claude/skills/` in a project and `~/.claude/skills/` for the user. It watches those folders,
so an added or edited skill shows up in the running session. A new top-level skills folder needs `/reload-skills`.
Codex and many other agents look in `.agents/skills/` and `~/.agents/skills/`, and Codex picks up changes
automatically, with a restart as the fallback.

To share one copy between them, keep the real folder in `~/.claude/skills/` and symlink it into `~/.agents/skills/`.
Codex documents that it follows symlinks. On one machine in November 2026, Claude Code didn't list a symlinked skill,
and the cause wasn't found, so the real folder lives on the Claude side.

`npx skills add <owner/repo> --skill <name> -g` installs a published skill for every agent at once.
