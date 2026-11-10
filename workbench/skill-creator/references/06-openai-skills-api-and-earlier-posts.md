# OpenAI: Skills in the API, and two earlier blog posts on testing and running skills

- URLs: https://developers.openai.com/api/docs/guides/tools-skills,
  https://developers.openai.com/blog/eval-skills (22 January 2026) and
  https://developers.openai.com/blog/skills-shell-tips (11 February 2026)
- Read in Chrome on 2026-11-10. Paraphrased.
- The two blog posts were written for models before GPT-6 Astra. Where they disagree with the Astra post
  ([prompting-agents note 09](../../prompting-agents/references/09-openai-rethinking-skills-and-prompts-astra.md))
  or the skill-creator that ships with Codex ([note 01](01-openai-codex-skill-creator.md)), the newer source wins.
  The disagreements are listed at the end.

## Skills in the API

- OpenAI's API reads the same Agent Skills format. Frontmatter is validated against the agentskills.io
  specification.
- For shell tools in the Responses API, the platform adds each skill's name, description and path to the **user
  prompt** context. If the model picks a skill, it reads `SKILL.md` from the path.
- "Skill instructions are user prompt input (not system prompt input)", so they have the same priority as other
  instructions the user gives. A skill cannot outrank the developer's system prompt.
- The model decides when to use a mounted skill. For a fixed workflow, say "use the <skill name> skill" in the
  request.
- Limits for an uploaded skill: one `SKILL.md` (the name is matched without regard to case), at most 500 files,
  25 MB per file uncompressed, 50 MB per zip.
- In the Agents API, the harness finds skills in up to 32 "capability directories" inside the sandbox.
- Safety: treat a skill as "privileged code and instructions". Review it before use. Don't let end users attach
  skills from an open catalogue. Put write actions and other high-impact actions behind explicit approval.

## Testing Agent Skills Systematically with Evals (January 2026)

The method: a prompt, a captured run (the transcript and the files produced), a small set of checks, and a score
to compare over time.

1. **Define success before writing the skill**, as checks you can measure, in four groups:
   - Outcome: did the task complete; does the app run?
   - Process: did the agent load the skill and run the commands you intended?
   - Style: does the output follow the conventions you asked for?
   - Efficiency: did it get there without repeating commands or burning tokens?
   Keep the list small, limited to checks that must pass.
2. **Run the skill by hand first**, naming it explicitly, to expose its hidden assumptions:
   - Triggering: a prompt that should load it doesn't, or a neighbouring prompt does.
   - Environment: it assumes an empty folder, or that `npm` is installed and preferred.
   - Execution: the agent skips a step because it assumes the step was already done.
   Every manual fix made at this stage is a candidate test case.
3. **Keep a small prompt set**, 10 to 20 rows, each marked should-trigger or should-not. Include four kinds: the
   skill named explicitly; the skill's exact scenario without its name; the scenario inside a noisier, realistic
   request; and at least one neighbouring request that must not trigger it. Add a row for each real miss.
4. **Start with checks a program computes.** `codex exec --json` prints the run as one JSON event per line, so a
   script can check that a command ran, that it exited with 0, and in what order. A failed check can be explained
   by opening the event file.
5. **Add a rubric judged by a model for what rules can't capture.** A second, read-only `codex exec` run inspects
   the result and returns JSON constrained by `--output-schema`, with one pass or fail and a note for each check.
6. **Extend only where it adds confidence**: count commands to catch looping, track tokens, run the build, start
   the app and request a page, check that `git status` is clean, check the skill still works with the least
   permissions.

Their summary: "Let real failures drive coverage. Every manual fix is a signal."

## Shell + Skills + Compaction (February 2026)

- A description is "routing logic (not marketing copy)". It answers: when should I use this, when should I not,
  and what does it produce.
- Making skills available can at first **reduce** correct triggering. Glean, an early customer, measured a drop
  of about 20% in its targeted tests after moving to skills. Triggering recovered after Glean added "don't use
  when" cases and edge cases to the descriptions.
- Put templates and worked examples inside the skill, not in the system prompt. They cost nothing until the
  skill is used. Glean reported this gave some of its largest gains in quality and speed.
- Glean's Salesforce skill raised accuracy on its tests from 73% to 85%. (Glean's number, on Glean's tests.)
- For a fixed production workflow, name the skill in the request.
- A skill combined with open network access is a path for data to leak. Keep the list of allowed hosts small.

## Where these older posts disagree with the newer OpenAI sources

| Older post | Newer source |
|---|---|
| The sample skill has a "When to use this" section in its body | Everything about when to use the skill goes in the description; the body is read after the decision (note 01 and prompting-agents note 12) |
| The sample skill is a numbered recipe of four steps | Recipes now limit the model. Keep fixed steps for operations where a deviation causes a concrete problem (note 01; prompting-agents note 09) |
| Put a "Use when / don't use when" block and negative examples in the description | Descriptions "as short as possible". Add an exclusion "only when [it] prevent[s] likely misrouting" (note 01; prompting-agents note 09) |
| Check that the agent ran the expected commands in the expected order | Test "observable behavior or meaningful invariants". Don't test wording, headings or patterns (note 01) |

The last row is a difference of degree. A check that a required command ran is a check of behaviour. A check that
the agent ran one particular sequence fails a run that reached the same result by a better route.
