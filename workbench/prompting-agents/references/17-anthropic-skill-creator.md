# Anthropic's skill-creator (the skill itself)

- Source: the `skill-creator` skill synced from claude.ai into this session (`/anthropic-skills:skill-creator`),
  506 lines, with `agents/` (grader, comparator, analyzer), `scripts/` (run_eval, run_loop, improve_description,
  aggregate_benchmark, package_skill, quick_validate), `eval-viewer/generate_review.py`, `references/schemas.md`.
- Read on 2026-11-10. Paraphrased.

## The process it runs

1. Capture intent: what the skill should let the agent do, when it should trigger, the output format, and whether
   test cases make sense. If the conversation already holds the workflow, take the answers from it, including the
   corrections the person made.
2. Interview and research before writing test prompts.
3. Write SKILL.md: `name`, `description`, the body. Read the draft again with fresh eyes and improve it.
4. Write two or three realistic test prompts and show them to the person. Save each as a folder under `evals/`
   (`prompt.md`, `case.yaml`, `graders/`, optional `files/`).
5. For each test, start two subagents in the same turn: one with the skill, one without (or with the old version).
6. While they run, draft assertions: objectively checkable, with names that read clearly in the viewer.
7. Record each run's tokens and duration when its notification arrives.
8. Grade each assertion with evidence, aggregate into a benchmark, and look for patterns the averages hide
   (assertions that pass either way, flaky cases, time and token cost).
9. Generate the review page with `eval-viewer/generate_review.py` and let the person review before you
   self-evaluate.
10. Read the person's feedback, improve, re-run into a new iteration folder, repeat.
11. Optimise the description: 20 realistic queries (half should trigger, half near-misses that shouldn't), the
    person reviews them, then a loop that scores on a held-out 40%.
12. Package.

## Its writing guidance

- Explain why, "in lieu of heavy-handed musty MUSTs". Writing ALWAYS or NEVER in capitals is "a yellow flag":
  reframe and give the reasoning.
- Use theory of mind. Make the skill general, not narrow to the examples.
- Keep the prompt lean. Read transcripts; if the skill makes the model waste time, remove the part that causes it.
- Generalise from feedback. The skill will run on prompts you'll never see; a fix that only makes these cases pass
  is worthless.
- If every test run wrote the same helper script, bundle it.
- Imperative form. SKILL.md under 500 lines. References with a table of contents when over 300 lines. Say when to
  read each reference. One reference per variant (aws.md, gcp.md) so only the relevant one loads.
- All "when to use" information goes in the description, not the body.
- No surprise: a skill's contents should match what its description says it is for.

## What the research moderates

| skill-creator says | Newer or measured guidance | What we take |
|---|---|---|
| Make descriptions "a little bit pushy" because Claude under-triggers skills | OpenAI: as short as possible; over-emphasis makes the model load skills that don't help; hosts shorten long descriptions (note 09, 10). Claude Code: over-triggering is fixed by a more specific description (note 05). Anthropic prompting: prompts written to fight under-triggering now over-trigger (note 01) | Say what it does and when, main use first, with the boundary. Add reach only for a measured miss |
| "Take your time and really mull things over"; "this task is pretty important" | Effort is the control; such phrases are ordinary text (notes 01, 14) | Leave them out of a skill |
| Example output template headed "ALWAYS use this exact template" | Emphasis makes current models over-apply a rule (notes 01, 14) | Strict template only where a program reads the output; say so plainly |
| Subagent runs as the test of a skill | Same on agentskills.io and in Claude Code docs; add that the baseline must really be without the skill, in a fresh context (note 05) | Keep |
| Assertions for objective output; a person for style | Same on agentskills.io (note 07) | Keep |
