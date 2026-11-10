# OpenAI: Prompt engineering guide, and OpenAI's skill-creator

- URLs: https://developers.openai.com/api/docs/guides/prompt-engineering and
  https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md
- Read in Chrome on 2026-11-10. Paraphrased. GitHub showed the top and bottom of the 368-line SKILL.md and
  collapsed the middle (lines 150 to 294: the progressive-disclosure patterns and creation steps 1 to 3).

## Prompt engineering guide (API)

- The page points to "Using GPT-6" as the GPT-6 Astra prompting guide (note 08). What it adds:
- Message roles carry authority: `developer` (or the `instructions` parameter) outranks `user`. Their picture: the
  developer message is the function definition, the user message is its arguments.
- A developer message usually has, in order: Identity (purpose, style, goals), Instructions, Examples, Context.
  Context goes near the end because it changes per request, and stable content at the start is cached.
- Markdown headings and lists mark sections and hierarchy. XML tags mark where a piece of content begins and
  ends, and attributes can carry metadata the instructions refer to.
- Few-shot examples: a handful of input/output pairs covering a diverse range of inputs.
- Keep prompts in code, with typed inputs, review, tests and evaluation checks before a change. Pin production to
  a model snapshot, and build evals so you can see what a prompt or model change did.
- Reasoning models do better "with only high-level guidance": a senior co-worker you give a goal to. Their
  non-reasoning models need precise instructions: a junior co-worker. (Astra and Sol 6.1 always reason.)

## OpenAI's skill-creator (the copy in openai/skills)

- The blog post in note 09 says OpenAI recently updated `$skill-creator` to push shorter descriptions and less
  recipe-like bodies. The copy I read still says the description should be "clear and comprehensive" and gives a
  long example, so this repository copy may predate that update. Codex ships its own copy as a system skill.
- Shared with Anthropic's guidance, almost word for word: the context window is a public good; assume the agent
  is already very smart and add only what it lacks; set the degree of freedom by fragility (narrow bridge, open
  field); three loading levels (metadata always, body on trigger, resources as needed); SKILL.md under 500 lines;
  say clearly when to read each reference; information lives in SKILL.md or a reference, not both.
- Its own additions:
  - All "when to use" information goes in the description. A "When to use this skill" section in the body is
    read only after the skill has already triggered, so it does nothing.
  - No README, changelog, installation guide or other auxiliary file inside the skill folder. The folder holds
    only what an agent needs to do the job, not the story of how it was made.
  - For a reference over 10,000 words, put grep patterns for it in SKILL.md.
  - Write in the imperative.
  - Test every bundled script by running it.
  - Only `name` and `description` in the frontmatter (plus `metadata`).
  - Iterate by using the skill on real tasks and noticing where the agent struggles.
