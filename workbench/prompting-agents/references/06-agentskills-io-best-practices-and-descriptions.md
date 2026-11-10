# agentskills.io: Best practices for skill creators, and Optimizing skill descriptions

- URLs: https://agentskills.io/skill-creation/best-practices and
  https://agentskills.io/skill-creation/optimizing-descriptions
- Read in Chrome on 2026-11-10. Paraphrased.
- agentskills.io is the home of the Agent Skills open standard. Anthropic started the format; it is now a Linux
  Foundation project that other agent tools read too. So this is the cross-vendor word on skills.

## Start from real expertise

- The common failure: asking a model to write a skill from its general knowledge. The result is generic ("handle
  errors appropriately"), not the specific facts that make a skill worth loading.
- Two good sources:
  1. A real task done with an agent. Keep the steps that worked, the corrections the person made, the input and
     output formats, and the context the person had to supply.
  2. The project's own material: runbooks, style guides, schemas, review comments, fix commits, incident reports.
     Project-specific material beats a generic best-practice article.
- Then run the skill on real tasks and feed all results back, not only failures. Read the execution trace, not
  only the output. Wasted steps usually come from one of three causes: instructions too vague (the agent tries
  several approaches), instructions that don't apply to this task (it follows them anyway), or many options with
  no default.

## Spending context

- The test for each piece: "Would the agent get this wrong without this instruction?" If no, cut it. If unsure,
  test it. If the agent already does the whole task well without the skill, the skill may add nothing.
- Scope a skill like a function: one coherent unit of work. Too narrow and several skills load for one task and
  may conflict. Too broad and it is hard to trigger precisely.
- Aim for moderate detail. A skill that covers every edge case can hurt: the agent struggles to find what applies
  and follows instructions that don't. Short stepwise guidance with one working example tends to beat exhaustive
  documentation.
- SKILL.md under 500 lines and 5,000 tokens. Move detail to `references/`, and say when to load each file: "Read
  `references/api-errors.md` if the API returns a non-200 status code" beats "see references/".

## Calibrating control

- Match specificity to fragility, part by part. Where variation is fine, describe what to look for and give the
  reason, because an agent that knows the purpose decides better in context. Where the operation is fragile, give
  the exact command and say not to change it.
- Give a default, not a menu. Mention the alternative briefly as the escape hatch.
- Teach the method for a class of problems, not the answer to one instance. Specific details (a template, a
  constraint, a tool) are fine; the approach should generalise.

## Patterns

- Gotchas: often the highest-value part. Concrete, environment-specific facts that defy a reasonable assumption
  (a soft-delete column; one id with three names; a health endpoint that lies). Keep them in SKILL.md, because the
  agent may not recognise the moment to go and load them. Each correction you have to make becomes a new gotcha.
- Output template: more reliable than describing a format in prose.
- Checklist for a multi-step workflow with dependencies.
- Validation loop: do the work, run a validator, fix, repeat.
- Plan, validate, execute for batch or destructive work. The validator's error names what is wrong and what is
  available, so the agent can correct itself.
- If traces show every run re-inventing the same logic, write it once as a tested script in `scripts/`.

## Descriptions

- The description carries the whole burden of triggering. Agents usually consult a skill only when the task needs
  something beyond what they can do alone, so a simple one-step request may not trigger even a matching skill.
- Write it as an instruction: "Use this skill when…", not "This skill does…". (Anthropic's older page says third
  person. Both agree it must say what and when.)
- Describe the user's intent, not the skill's mechanics.
- Lean pushy: list the contexts, including ones where the user doesn't name the domain.
- A few sentences to a short paragraph. Hard limit 1,024 characters.

## Testing a description

- About 20 realistic queries, 8 to 10 that should trigger and 8 to 10 that shouldn't. Vary phrasing,
  explicitness, detail and complexity. The useful positives are ones where the link to the skill is not obvious.
  The useful negatives are near-misses that share keywords but need something else.
- Realistic queries carry file paths, personal context, specific details, casual language and typos.
- Run each query three times; behaviour varies. Pass a positive at a trigger rate above 0.5.
- Split about 60% train, 40% validation. Use only train failures to guide changes. Pick the version with the best
  validation rate, which may not be the last.
- Don't add keywords from failed queries; address the general category they represent. If stuck, try a
  structurally different description. Five rounds is usually enough.
- Finish with 5 to 10 fresh queries never used in tuning.
