# Gemini 4 Neon and Gemini 4 Carbon

Checked against Google's documentation on 26 November 2026, eight days after Neon was released. Advice about a model
goes out of date faster than anything else in this skill, so if Google has published newer guidance, read it first.

Neon (`gemini-4-neon`) is Google's model for complex coding and production work, and the default in Antigravity on
paid plans. Carbon (`gemini-4-carbon`) is Google's model for deep, long-horizon work: architecture, hard debugging and
security. Google has published model guides for each but no prompting guide for the Gemini 4 family, so this file
says less than the Claude and GPT files, and says where it comes from.

The sources are Google's model guides for [Neon](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-neon)
and [Carbon](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-carbon), the
[Antigravity models page](https://antigravity.google/docs/models/), Antigravity's page on
[rules](https://antigravity.google/docs/rules), and the
[Neon launch post](https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301).
Lines marked **Reported** come from developers' write-ups rather than Google, and are kept because they are
consistent with what Google does say; treat them as a place to look, not a fact.

## Which one to use

Google positions the two by depth, not by quality. Neon is for "complex coding, analytical reasoning, and
production-grade enterprise workflows", and Google says it costs about a third less per task than Carbon at high
effort. Carbon is for "your hardest, long-horizon projects". Antigravity's own Orchestrator pairs a planner (Neon by
default, or Carbon) that explores, plans and reviews with a cheaper executor that edits files and runs the tests. That
is the same split as a planner and builders: Carbon where the work is to decide, Neon where it is to build.

## Effort

The effort setting matters more here than a line in the prompt, because, as with the other current models, how hard
a model reasons is set outside the prompt.

- **Neon** takes low, medium, high and xhigh. Google's guide gives high as the default and suggests xhigh for proofs
  and the most complex multi-file engineering, high for agent loops and code generation, and medium for general
  coding and tool use. Google warns that xhigh can over-think a simple request and use up its output budget on it.
- **Carbon** takes low, medium and high, with medium as the default. Google suggests high for multi-file engineering,
  architecture and security work.

Thinking counts against the output budget and builds up over a long conversation, so a run at a high effort reaches
its limits sooner.

## Habits to write against

Google's guides say plainly that the models don't follow length targets. "Keep it under 200 words" does little;
if length matters, ask for a shape instead, such as one paragraph per finding, or a schema when a program reads the
answer.

Carbon's guide asks for sequential tool turns rather than many calls at once, and for progress to be reported
through a dedicated update (what was done, the plan, the next step) rather than as free text between tool calls. In
a prompt, that means asking it to report progress in one place at the end of each step, not narrate as it goes.

Both guides suggest putting nothing but the request before a tool call: text the model writes before calling a
tool tends to become its plan, so a prompt that invites it to "think out loud first" makes its tool use worse.

**Reported:** Carbon's developer guide, as summarised by developers who read it, describes one shape for long runs:
check first that the model has the tools and documents it needs, then let it run the whole plan on its own, with
its own checks, and pause only before something that can't be undone. That is the same advice as for the other
models: say what done looks like and what needs approval, and leave the rest to the model.

**Reported:** developers found Carbon claimed in its summaries that work was verified when it had only checked its
own output. Ask for the evidence (the command and its result, or a screenshot from the browser) rather than the
claim, as the main guidance in this skill already says.

What Google has not documented: how literally these models read instructions, how verbose they are by default,
whether they stop early, ask for approval they don't need, or overreach. Until a test here shows otherwise, write to
them as you would to Claude Opus 5.5, and look at what the first run does.

## Instruction files and skills in Antigravity

Antigravity reads `AGENTS.md` (or `GEMINI.md`) from the workspace folder and every parent up to the repository root,
plus the global files in `~/.gemini/`, and adds them all together rather than letting one replace another. Each file
is cut off at 24,000 bytes, and all the always-on rules share a 20,000-token budget; past it, Antigravity swaps the
largest files for pointers the model reads only when it decides to. So a long `AGENTS.md` written for another host
can be partly unread here. Keep it to the requirements the model can't work out from the code, and move procedures
into skills, which Antigravity reads from `.agents/skills/` and `~/.gemini/config/skills/`.
