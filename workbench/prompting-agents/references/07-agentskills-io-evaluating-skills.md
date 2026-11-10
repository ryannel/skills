# agentskills.io: Evaluating skill output quality

- URL: https://agentskills.io/skill-creation/evaluating-skills
- Read in Chrome on 2026-11-10. Paraphrased. This is the method Anthropic's skill-creator automates.

## Test cases

- A test case is a realistic prompt, a plain description of what success looks like, and input files if needed.
- Start with two or three. Vary phrasing, detail and formality. Include one boundary case (bad input, an unusual
  request, a place where the skill's instructions could be read two ways). Use real context: file paths, column
  names, personal detail. "Process this data" tests nothing.
- Do not write pass/fail checks yet. Write them after the first outputs, because you often don't know what good
  looks like until the skill has run.

## Runs

- Run each case twice: with the skill, and without it (or with the previous version, from a snapshot).
- Each run starts with a clean context, so the agent follows only what SKILL.md says. A subagent gives this; so
  does a separate session.
- Record tokens and duration for each run. A skill that improves quality and triples tokens is a different trade
  from one that is better and cheaper.

## Assertions and grading

- Good assertions are specific and observable ("both axes are labelled", "at least 3 recommendations"). Weak ones
  are vague ("the output is good") or brittle (an exact phrase).
- Style, design and "feels right" are for a person to judge. Don't force assertions onto them.
- A pass needs concrete evidence quoted from the output. A section titled "Summary" holding one vague sentence
  fails "includes a summary".
- Check by script whatever a script can check.
- To compare two versions, use a blind comparison: a judge sees both outputs without knowing which is which.

## Reading the results

- Remove assertions that pass in both configurations; they show the model didn't need the skill for that.
- Investigate assertions that fail in both; the assertion or the case is probably wrong.
- Study assertions that pass only with the skill: which instruction made the difference?
- Inconsistent results across runs mean a flaky case or an ambiguous instruction. Add an example or be more specific.
- Read the transcript of any run that took much longer or used many more tokens.

## A person reviews

- Assertions check only what you thought to check. A person catches output that is technically correct and misses
  the point. Feedback must be specific to act on. Empty feedback means it was fine.

## Improving

- Three signals: failed assertions (a specific gap), human feedback (a broader quality problem), transcripts (why).
- Four guidelines for the revision:
  1. Generalise from the feedback. Fix the underlying issue, not the test case.
  2. Keep the skill lean. If pass rates stop rising as rules are added, the skill may be over-constrained: remove
     instructions and see if results hold.
  3. Explain why. "Do X because Y tends to cause Z" works better than "ALWAYS do X".
  4. Bundle repeated work as a script.
- Stop when the person is satisfied, feedback is empty, or rounds stop improving things.
