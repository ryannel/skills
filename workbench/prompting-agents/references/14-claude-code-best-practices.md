# Claude Code docs: Best practices for Claude Code

- URL: https://code.claude.com/docs/en/best-practices
- Read in Chrome on 2026-11-10 (the sections on the two kinds of instruction, telling Claude what it can't see,
  giving it a check to run, rules without exceptions, what subagents cost, steering, and what to stop doing).
  Paraphrased.

## Two kinds of instruction

- Non-deterministic: you write it and the model reads it (a prompt, CLAUDE.md, a skill). The model decides what to
  do with it. It usually follows; nothing guarantees it.
- Deterministic: you configure it and the harness executes it (a hook, a deny rule, a managed setting, a test, CI,
  a spend limit, branch protection). It applies every time, whatever the model decided.
- Most of the time you want the model to decide. Almost every guideline has exceptions, and with the real code in
  front of it the model is usually better placed to judge than a rule written in advance.
- The deterministic kind is for what must always or never happen. It need not be dramatic: "never edit the
  generated client in `src/gen/`".
- The sign a line belongs in a hook: you keep adding emphasis and it is still missed. However strongly a line is
  worded, following it on a given turn is still the model's call. The reverse also holds: a hook for a mere
  preference should be deleted.

## Tell it what it can't see

- Write down only what the model can't find by reading the repository, or would spend time rediscovering every
  session. It reads the code first and finds layout, conventions and the test framework faster than you can
  explain them.
- What it can't find was never in the repository: a decision made in a meeting, a process in one person's head,
  the environment variable the integration tests need.
- The test before writing anything down: "Could it find this by reading the code? Would it actually go and look?"
  If both are yes, leave it out.
- A specific prompt helps for the same reason: it carries what the model doesn't have. Name the file, describe
  the symptom, say what "fixed" looks like. State a preference between two reasonable approaches, because it
  can't be read from the code.
- If you already have the thing, hand it over (the file, the screenshot, the command output) instead of
  describing it.
- "Think step by step" and "be thorough" are ordinary text, not controls. Effort is the control. Such wording
  nudges within the effort setting and cannot lift past it.
- One phrase that still helps: "be ambitious", with the scope spelled out. The model reads a request
  conservatively because it can't see how much you hoped for. That is telling it scope, which only you know.
- When exploring, a vague prompt is fine.

## Give it a check to run

- The model stops when the work looks done. With nothing to run, "looks done" is all it has, and the person
  becomes the test suite.
- Give it something that comes back pass or fail and it can read: a test, a build's exit code, a linter, a diff
  against a fixture, a screenshot beside the mock-up. The most useful line in CLAUDE.md is the command that runs it.
- Strictness, from the model deciding to the harness enforcing: in the prompt ("run the auth tests and keep going
  until they pass"); as a `/goal` (a separate model checks the condition after every turn; useful for long
  background runs, where a turn sometimes ends on a progress summary with items still open); as a Stop hook (the
  turn can't end until the script passes); by a reviewer that never saw the conversation.
- Ask for evidence: the command and its output, or the screenshot. "All tests pass" tells you very little.
- A review against a spec: say what to check and to report only gaps that affect correctness. Keep "skip style".
  "A reviewer that's asked to find problems will always find something", and fixing every finding adds
  abstraction layers and tests for cases that can't happen.

## Subagents

- They pay off for: independent work in parallel; keeping long output out of the main conversation; a reviewer
  that hasn't seen how the code was written; a task with fewer tools.
- They cost tokens, and sometimes time, because a fresh subagent must first gather context the conversation
  already had.
- It is the same model (or a smaller one) on the same task. "You get parallelism or a fresh pair of eyes out of
  it, but not a smarter answer."
- Ask for short summaries back. A tool restriction in the agent's definition is enforced; one in the prompt is
  requested.

## Steering

- Watch the first minute and stop it the moment it drifts.
- After two failed corrections, start a new conversation with one better prompt that folds in what you learned. A
  third correction adds to a conversation that already holds two failed attempts for the model to keep re-reading.

## What to stop doing (their table)

| Old advice | Why it's gone |
|---|---|
| Manage the context window aggressively | 1M-token windows and automatic compaction. A focused context still answers better and costs less. |
| IMPORTANT or capitals on lines it keeps missing | Current models follow a plain line; emphasis makes them over-apply it. A rule that can't bend is a hook. A line lost in a long file means the file is too long. |
| Subagents to protect context | Rarely the problem now. |
| Delegate for a better answer | Delegating doesn't improve the answer. A fresh reviewer helps for a different reason. |
| "Think hard", "be thorough" | Effort is the control. |
| "Keep going", "loop until done", "don't be lazy" | Models carry on through an agreed task; such lines cause over-work. A check to pass is different and still worth giving. |
| Describe architecture and layout in CLAUDE.md | The model reads the repository. Write only what isn't there. |
