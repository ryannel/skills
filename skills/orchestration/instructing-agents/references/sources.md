# Sources

These were re-read on 7 November 2026. Each one is tied to the model it was measured on, so its advice can go stale
when a new model ships. Re-check them whenever a model ships or a guide changes.

## OpenAI

- [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
  It covers short descriptions, routers, recipes, AGENTS.md pointers, decision boundaries and persistence. Its
  comparisons are against GPT-5.6 Sol.
- [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model). It covers initiative and follow-through,
  instruction precedence, writing style, delegation and testing. It was measured on Astra.
- [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning). It covers effort levels, giving a goal and
  constraints rather than steps, and defining what done and verification mean.
- [Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family).
  It compares what Astra and Sol cost, and covers Sol's blind spots, example goals and A/B replays of instructions.
- [Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex). It covers
  the spec, plan, runbook and status files, and verifying at each milestone.
- [Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex). It covers the six
  elements of a goal, completion based on evidence, and stops when the budget runs out.
- [Using PLANS.md (ExecPlans)](https://developers.openai.com/cookbook/articles/codex_exec_plans). It covers plans that
  are self-contained and kept up to date, with acceptance written as behaviour. It's archived, and it was written for
  gpt-5.2-codex.
- ChatGPT Learn: [build skills](https://learn.chatgpt.com/docs/build-skills),
  [prompting](https://learn.chatgpt.com/docs/prompting),
  [long-running work](https://learn.chatgpt.com/docs/long-running-work) and
  [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- [GPT-6.1 Sol system card](https://deploymentsafety.openai.com/gpt-6-1-sol/gpt-6-1-sol.pdf). This is the source for
  the figures on persistence, reward hacking and misrepresentation (§7.2, §7.4.1 and §7.6). They reached this file
  through the research report of 7 November.

## Anthropic

- [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).
- [What's new in Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5).
- [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5).
  It covers scope, over-verification, verbosity and delegation.
- [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices). It covers emphasis, "keep going"
  lines, questions to settle before an unattended run, what subagents are for, and keeping reviewers independent. The
  review on 7 November confirmed it.
- Claude Code [goals](https://code.claude.com/docs/en/goal), [skills](https://code.claude.com/docs/en/skills) and
  [subagents](https://code.claude.com/docs/en/sub-agents).
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
- [skill-creator](https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md).
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).
- [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps).
