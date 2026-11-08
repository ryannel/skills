# Sources

Re-read on 7 November 2026. Re-check them when a model ships or a guide changes; each one is tied to the model it was
measured on.

## OpenAI

- **Rethinking skills and prompts for GPT-6 Astra.** https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
  Covers short descriptions, routers, recipes, AGENTS.md pointers, decision boundaries and persistence. Compared
  against GPT-5.6 Sol.
- **Using GPT-6.** https://developers.openai.com/api/docs/guides/latest-model
  Covers initiative and follow-through, instruction precedence, writing style, delegation and testing. Measured on
  Astra.
- **Reasoning models.** https://developers.openai.com/api/docs/guides/reasoning
  Covers effort levels, goal and constraints over steps, and defining done and verification.
- **Maintaining software with the GPT-6 family.** https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family
  Compares Astra and Sol costs, Sol's blind spots, goal examples and instruction A/B replay.
- **Run long horizon tasks with Codex.** https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
  Covers the spec, plan, runbook and status files, and verification at each milestone.
- **Using Goals in Codex.** https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
  Covers the six goal elements, evidence-based completion and budget stops.
- **Using PLANS.md (ExecPlans).** https://developers.openai.com/cookbook/articles/codex_exec_plans
  Covers self-contained living plans and acceptance phrased as behaviour. Archived; written for gpt-5.2-codex.
- **ChatGPT Learn.** https://learn.chatgpt.com/docs/build-skills, /docs/prompting, /docs/long-running-work and
  /docs/agent-configuration/agents-md.
- **GPT-6.1 Sol system card.** https://deploymentsafety.openai.com/gpt-6-1-sol/gpt-6-1-sol.pdf
  Source for persistence, reward hacking and misrepresentation (§7.2, §7.4.1, §7.6), via the 7 Nov research report.

## Anthropic

- **Prompting Claude Opus 5.5.** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5
- **What's new in Opus 5.5.** https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5
- **Prompting Claude Opus 5.** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
  Covers scope, over-verification, verbosity and delegation.
- **Prompting best practices.** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- **Claude Code best practices.** https://code.claude.com/docs/en/best-practices
  Covers emphasis, "keep going" lines, unattended-run questions, subagent uses and reviewer independence. Confirmed by
  the review on 7 Nov.
- **Claude Code goals, skills and subagents.** https://code.claude.com/docs/en/goal, /docs/en/skills and
  /docs/en/sub-agents.
- **Skill authoring best practices.** https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **skill-creator.** https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
- **Effective context engineering for AI agents.** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Harness design for long-running application development.** https://www.anthropic.com/engineering/harness-design-long-running-apps
