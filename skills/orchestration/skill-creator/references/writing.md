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

The name is lowercase with hyphens, at most 64 characters, and can't contain "claude" or "anthropic". The description
is at most 1,024 characters.

## The description

Until an agent decides to load a skill, the name and description are all it sees. So the description is the trigger.
If it's vague, the skill fires at the wrong times or never fires at all.

Say what the skill does, then when to use it, in the third person, with the main use first. Name the phrasings a user
might actually type. A user who wants a dashboard might say "chart", "metrics" or "KPI page" without ever saying
"dashboard".

Be specific rather than loud. "Use when adding or changing a database migration, or reviewing its rollout" beats "Use
for anything involving databases". Broad or emphatic descriptions load the skill when it won't help.

If a neighbouring skill could fire instead, add a "Not for…" line that names it.

Put the trigger words near the front. When too many skills are installed, harnesses shorten or drop descriptions to
fit, and the end of a long description is the first thing to go.

## The body

Write only what the agent doesn't already know. Every paragraph costs attention on every run, so every paragraph has
to earn its place. A good test for a line is to ask what mistake the agent would make without it. If you can't name
one, cut it.

Start with as little as you can. Add a line when you see the agent get something wrong, keep that line narrow, and say
why it's there. Most bloat comes from fixing mistakes nobody has actually seen.

Say what finished looks like and how to prove it, what the agent may and may not touch, and where to find things.
Leave the method to the agent wherever many methods would work. Match the freedom to how fragile the work is. Open
work gets a goal and a few rules of thumb. Work with a preferred pattern gets a template. Fragile work where the order
matters, like a migration, gets exact steps or a script.

Keep `SKILL.md` short, and treat it as a map. If the skill covers several workflows, give each its own reference and
say when to read it: "Read aws.md when deploying to AWS." Keep references one level deep, and give any reference over
about 100 lines a contents list. Keep the most important instructions near the top, because some harnesses only
re-attach the start of a skill after compacting the conversation.

Use examples instead of adjectives. One short input and output pair shows a style better than a paragraph describing
it.

Put repeatable work in scripts. If every run would write the same helper, write it once and bundle it. Say whether
the agent should run it or read it.

Keep each rule in one place and point to it from elsewhere. Use one word for each idea throughout.

Anything that truly must never happen belongs in a hook, a permission rule or a sandbox. Prose is advice, and agents
weigh it against everything else.

## The voice

Write the way Randall Munroe explains things in "What If?": plain words, short sentences, concrete examples, and the
obvious said out loud. Leave out the jokes, because agents can take them literally and they cost attention.

Give the reason with every rule. Models generalise from reasons. "Don't use ellipses, because a text-to-speech engine
reads this aloud" lets the agent handle cases you never listed. "NEVER use ellipses" doesn't.

Skip the shouting. Capital letters and words like MUST make current models apply a rule too widely. The exception is
an exact format a program will read, where strict wording is right.

Use full sentences. Lists are for real lists, like a checklist, a set of fields or a set of options. Avoid bold
phrases at the start of every bullet, long chains of semicolons, and clauses packed together to save words. They
look efficient, but they're hard to read, and they hide the reasons.

Here's the difference. This is the packed style:

> **Verify on target.** Capture from exact build; cover edge conditions; label proxies; no claims without evidence.

And this is the plain one:

> Look at the output yourself, using the exact build on its real target. Passing tests tell you the code does what the
> tests say. They don't tell you it looks right. If you used a stand-in, like a Mac standing in for an iPhone, say so.

The plain version is longer, but each sentence does one job, and the agent knows why.

## Frontmatter options

Claude Code reads a few extra fields:
- `disable-model-invocation: true` makes the skill run only when the user asks for it. Use it for skills with side
  effects, like deploying.
- `user-invocable: false` hides the skill from the user's menu, for skills only the agent uses.
- `when_to_use` adds trigger guidance alongside the description.
- `context: fork` runs the skill in a subagent. That subagent can't see the conversation, so the skill has to make
  sense on its own.

Claude Code ignores fields it doesn't recognise, and doesn't warn you. Codex reads extra settings from
`agents/openai.yaml` in the skill folder, including a display name and `policy.allow_implicit_invocation`.

## Where skills live

Claude Code looks in `.claude/skills/` in a project and `~/.claude/skills/` for the user. Codex and many other agents
look in `.agents/skills/` and `~/.agents/skills/`. To share one copy between them, keep the real folder in
`~/.claude/skills/` and symlink it into `~/.agents/skills/`. Codex follows symlinks. Claude Code has been seen to miss
symlinked skills, which is why the real folder lives on its side.

`npx skills add <owner/repo> --skill <name> -g` installs a published skill for every agent at once. A new skill only
shows up in sessions started after it was installed.
