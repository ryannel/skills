# Sources

Re-read on 9 November 2026. Each source was measured on one model, so its advice can go stale when a new model ships,
and the Codex system prompts can change on the server with no release. Re-check when either happens.

## OpenAI

- Codex system prompts and model catalogue, `codex-rs/models-manager/models.json` in
  [openai/codex](https://github.com/openai/codex). The autonomy, skill-precedence, testing and writing rules Codex
  already sends Sol and Astra, the subagent fork default, and the effort defaults.
- Codex goal templates, [continuation](https://github.com/openai/codex/blob/main/codex-rs/ext/goal/templates/goals/continuation.md)
  and [budget limit](https://github.com/openai/codex/blob/main/codex-rs/ext/goal/templates/goals/budget_limit.md). How
  `/goal` derives requirements from the objective and referenced files, and when it may call itself blocked.
- [Codex changelog](https://developers.openai.com/codex/changelog). Empty-continuation and interruption limits.
- [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model). Measured on Astra. Its GPT-5.6 section
  has the lean-prompt figures.
- [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
  Recipes, reading lists, "ask first" language and short descriptions.
- [Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family).
  Sol against Astra on broad goals, its blind spots, and start-small-then-widen.
- [Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex). The six parts of
  a goal.
- [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning). Effort as a tuning knob.
- ChatGPT Learn: [best practices](https://learn.chatgpt.com/guides/best-practices),
  [models](https://learn.chatgpt.com/docs/models), [long-running work](https://learn.chatgpt.com/docs/long-running-work)
  and [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- [GPT-6.1 Sol system card](https://deploymentsafety.openai.com/gpt-6-1-sol/gpt-6-1-sol.pdf), §7.2, §7.4, §7.5.1 and
  §7.6. Persistence, misrepresentation, messages from other agents.
- [Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex). Spec,
  plan and status files. GPT-5.x era.

## Anthropic

- [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)
  and [what's new in Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5). Effort, the
  unattended paragraph, text-only turn endings, exploring first.
- [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5).
  Scope, self-verification, review filters, delegation. Not re-tested on 5.5.
- [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5).
  Intent over request, the measured progress-claim audit, fresh-context verifiers.
- [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
  Reasons with rules.
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices). Emphasis, "keep going", effort,
  delegation, reviewer prompts.
- Claude Code [subagents](https://code.claude.com/docs/en/sub-agents), [memory](https://code.claude.com/docs/en/memory),
  [goal](https://code.claude.com/docs/en/goal) and [skills](https://code.claude.com/docs/en/skills). What a subagent
  loads, AGENTS.md loading, the goal evaluator, `context: fork`.
- Claude Code's Agent tool description and the `prompt-audit` catalogue in the bundled `claude-api` skill (Claude Code
  2.1.317). Briefing a subagent like a peer, hedges, the recency trap.
- [When to fold subagents into your main agent loop](https://claude.com/blog/building-agents-when-to-fold-subagents-into-your-main-agent-loop)
  (22 October 2026). Splitting by context rather than role.
- [Getting the most out of Opus 5.5](https://claude.dev/blog/getting-the-most-out-of-opus-5-5/) (22 September 2026).
  Includes the "would block the merge" reviewer example.
- [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps).
  Separate evaluators. Opus 4.5 and 4.6 era.

## Practice

The rules against listing what to look at, against technique recipes in goals, against invented numeric targets, and
for treating repeated trials as a sign of missing research come from corrections one maintainer made to agent-written
goals, steers and briefs in November 2026.
