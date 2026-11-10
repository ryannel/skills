# prompting-agents

More and more of an agent's work is writing for other agents: a brief for a subagent, a goal for a run that
lasts all night, a request for a review, an instruction file the next session will read. The agent on the other
end is usually as capable as the one writing, but it starts with nothing except the text it is given. Most bad
prompts fail in one of two ways. They tell that agent how to do work it already knows how to do, or they leave
out something it needed and had no way to find.

This skill teaches the writing agent to avoid both. It says what a prompt has to carry, what to leave out, where
an instruction belongs, and how each current model needs to be addressed. It is written in the plain, step-by-step
style it asks for, which is Randall Munroe's in "What If?", without the jokes.

It doesn't cover writing or testing skills, which is the job of [skill-creator](../skill-creator/).

## What's in the folder

- `SKILL.md`: the guidance every prompt needs. The agent reads this when the skill loads.
- `references/kinds.md`: what a subagent brief, a long-run goal, a review request, a steer and a system prompt
  each need beyond that.
- `references/instruction-files.md`: what belongs in a `CLAUDE.md` or `AGENTS.md`, and what doesn't.
- `references/writing-style.md`: each writing habit shown on a real sentence.
- `references/models/`: one file each for Claude Opus 5.5 and Claude Fable 5.2, and one shared by GPT-6 Astra
  and GPT-6.1 Sol. Each says what that model tends to do and what to write to correct for it.

## Where the guidance comes from

The guidance comes from what Anthropic and OpenAI published about prompting their current models, read on 10
November 2026. The research summary, with a note on every page read, is in
[workbench/prompting-agents](../../workbench/prompting-agents/README.md). The main sources are these:

- **Anthropic:** [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices),
  the model pages for [Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)
  and [Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5),
  and Claude Code's pages on [instruction files](https://code.claude.com/docs/en/memory) and
  [best practices](https://code.claude.com/docs/en/best-practices).
- **OpenAI:** [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model),
  [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra),
  [Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family),
  and Codex's pages on [prompting](https://developers.openai.com/codex/prompting) and
  [AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md).
- **The writing style:** Munroe's [Relativistic Baseball](https://what-if.xkcd.com/1/), plus corrections from
  the owner of this repository.

Where the two vendors disagreed, the research summary says which side we took and why.

## How far to trust it

Every number in the skill is the vendor's own measurement on the vendor's own tasks; none was checked here.
OpenAI has published no prompting advice specific to GPT-6.1 Sol, so its section rests on one blog post. The
model files will go out of date first, which is why each carries the date it was checked, and why
`freshness.json` at the root of this repository tracks them.

The first version of the skill was tested on three tasks, each run once with the skill and once without. The
current version has been rewritten since and hasn't been tested yet.
