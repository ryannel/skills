# Anthropic: Prompting best practices

- URL: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Read in Chrome on 2026-11-10. Paraphrased; short quotes are marked.
- Covers every current Claude model (Fable 5.2 down to Haiku 4.5). Says: read the model's own page first, then this.
  A technique that names one model was measured on that model; re-check it before applying it to another.

## Per-model differences (the page's own table)

- Fable 5.2: effort calibration, finishing long tasks, approvals, code ownership, progress updates, subagent
  delegation, caution that builds up, instructions written for earlier models, final reports, safeguard refusals.
- Opus 5.5 (against Opus 5): effort calibration, prompts written for thinking disabled, progress updates, safeguard
  refusals, tools for complex visual inputs.
- Opus 5 (against earlier Opus): longer default responses, progress updates, deliverable length, task scope and
  over-verification, subagent control, self-correction.

## General principles

1. Be clear and direct. Treat the model as a brilliant new employee with no context on your norms. Test: would a
   colleague with minimal context be confused by the prompt? If the model should do more than the literal task, say so.
2. Give the reason with the rule. Their example: "never use ellipses" works worse than explaining that the text is
   read aloud by a text-to-speech engine. The model generalises from the explanation.
3. Use numbered steps only when order or completeness matters.
4. Examples steer format, tone and structure reliably. Make them relevant, varied (so it doesn't copy an accident),
   and wrapped in `<example>` tags. Three to five is their suggested number.
5. XML tags separate instructions, context, examples and inputs in a mixed prompt. Use consistent names.
6. A one-sentence role in the system prompt focuses behaviour.
7. Long inputs (20k+ tokens) go at the top; the question goes at the end (up to 30% better in their tests). Ask for
   relevant quotes first on long-document tasks.

## Output and formatting

- Say what to do, not what not to do ("write flowing prose paragraphs", not "don't use markdown").
- The prompt's own style leaks into the output. A prompt without markdown gets less markdown back.
- Current models are concise and may skip summaries after tool use; ask for a summary if you want one.
- Fable 5.1 writes fewer progress updates and already formats lightly; old anti-markdown blocks over-suppress on it.

## Tool use and action

- Models follow instructions precisely. "Can you suggest changes" gets suggestions; "change this" gets edits.
- Opus 4.5 and later respond more to the system prompt, so prompts written to fight under-triggering now
  over-trigger. Fix: soften aggressive language ("CRITICAL: You MUST use this tool when" becomes "Use this tool
  when"). Remove "if in doubt, use X".
- Independent tool calls run in parallel by default; a prompt can push that near 100% or turn it down.

## Thinking

- Fable 5.x and Opus 5.5: thinking is always on, adaptive is the only mode. Effort plus task complexity decide how
  much. On Fable 5.2 an instruction to answer without deliberating did not stop thinking at medium effort and above:
  lower the effort instead.
- "Prefer general instructions over prescriptive steps." A general "think thoroughly" often beats a hand-written
  step-by-step plan, because the model's reasoning often exceeds what a person would prescribe.
- Do not ask Fable 5.x, Opus 5.5, Opus 5 or Sonnet 5.5 to write out their reasoning in tags; it may be declined.
- Self-check instructions help most models. Opus 5 is the exception: it verifies unprompted, and carried-over
  verification instructions cause over-verification. Remove them on Opus 5.

## Agentic systems

- Long work: state in files. Structured data (test status) in JSON, loose notes in text, git as the log and the
  checkpoint. Tests written first and never edited. A different prompt for the first context window than for later
  ones. A fresh context that reads the files can beat compaction.
- Tell the model if its context will be compacted, or it may wrap up early near the limit.
- Risky actions: ask it to weigh reversibility, and list what needs confirmation.
- Subagents: current models delegate unprompted, and Opus 4.6 and Opus 5 over-delegate. Say when a subagent is
  warranted (parallel, isolated context, independent work) and when to work directly.
- Over-engineering and test-gaming are known tendencies; sample prompts scope the work and ask for general solutions.
- Explicit prompt chaining is still useful when you need to inspect the steps between.

## Migration

- Page was cut off at 50k characters; the migration section was not read in full. It opens with "be specific about
  the behaviour you want".
