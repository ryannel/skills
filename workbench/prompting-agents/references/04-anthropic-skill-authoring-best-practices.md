# Anthropic: Skill authoring best practices

- URL: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Read in Chrome on 2026-11-10. Paraphrased.
- Note the age of parts of this page: its model advice names Haiku, Sonnet and Opus generically, and one passage
  suggests "stronger language such as MUST filter". The prompting pages for Opus 4.5 and later say the opposite
  (soften aggressive language). Treat the prompting pages as the newer word.

## Core principles

1. Concise is key. "The context window is a public good": a loaded skill competes with the conversation, the system
   prompt and every other skill's metadata. Only name and description are loaded at start; SKILL.md loads when the
   skill is used; other files load when read.
2. Assume the model is already very smart. For each piece: does it need this explanation? Does it already know it?
   Does the paragraph earn its tokens? Their example cuts a 150-token explanation of what a PDF is down to a
   50-token code snippet.
3. Set the degree of freedom to match how fragile the task is.
   - High freedom (prose guidance): several approaches are valid and the choice depends on context.
   - Medium (pseudocode or a parameterised script): a preferred pattern exists, some variation is fine.
   - Low (an exact command, "do not modify"): the operation is fragile, consistency is critical, order matters.
   - Their picture: a narrow bridge with cliffs needs exact instructions; an open field needs a direction.
4. Test with every model you plan to use. A weaker model may need more guidance; a stronger one may be
   over-explained to.

## Frontmatter

- `name`: at most 64 characters, lowercase letters, numbers and hyphens. Not the words "anthropic" or "claude".
  Gerund names suggested (`processing-pdfs`); noun phrases acceptable. Avoid vague names (`helper`, `utils`).
- `description`: non-empty, at most 1,024 characters. Says what the skill does and when to use it. Written in the
  third person, because it is injected into the system prompt. Specific, with the key terms a request would use.
  It is the only thing the model sees when choosing among possibly 100+ skills.

## Progressive disclosure

- SKILL.md is an overview that points to detail, like a table of contents. Keep the body under 500 lines.
- Patterns: a high-level guide with links to references; one reference file per domain so only the relevant one
  loads; basic content inline with links to the advanced cases.
- Keep references one level deep. A file linked from a linked file may be only partly read (previewed with
  `head -100`).
- A reference over 100 lines gets a table of contents at the top, so a partial read still shows its scope.
- Name files for their content (`form_validation_rules.md`, not `doc2.md`).
- Large reference files cost nothing until read, so bundle complete references.

## Workflows and feedback loops

- Break a complex operation into clear sequential steps. For a very complex one, give a checklist to copy and tick.
- Feedback loop: run a validator, fix the errors, repeat. "This pattern greatly improves output quality." The
  validator can be a script or a reference document to compare against.
- For risky batch work: plan in a structured file, validate the plan with a script, then execute. Validation
  messages should be specific enough to fix from.

## Content

- No time-sensitive statements in the main text. Put old ways in an "old patterns" section.
- One term per thing, used everywhere. Mixing "field", "box", "element" hurts.
- Templates: strict when a program reads the output, loose ("a sensible default, use judgement") otherwise.
- Examples as input/output pairs convey style better than description.
- Don't offer many options. Give one default and an escape hatch.

## Evaluation and iteration

- Build evaluations before writing much. Run the model on real tasks without the skill, note the specific
  failures, build three scenarios that test them, measure the baseline, then write the minimum that closes the gaps.
- Develop with two instances: one helps write the skill, a fresh one uses it on real tasks. Bring what the second
  did back to the first. "Claude models handle the Skill format and structure natively"; no special skill is needed
  to write one.
- Watch how the model navigates the skill: unexpected reading order, links not followed, one file read repeatedly
  (move it into SKILL.md), a file never read (remove it or signal it better).

## Scripts

- Scripts handle their own errors instead of leaving them to the model. Constants are explained.
- A bundled script is more reliable than generated code and costs no context: only its output is read.
- Say whether a script is to be run or read.
- Don't assume a package is installed. Use forward slashes. Fully qualify MCP tool names (`Server:tool`).

## Their checklist (short form)

Description specific and says what and when; body under 500 lines; detail in separate files; no time-sensitive
text; consistent terms; concrete examples; references one level deep; clear workflow steps; scripts handle errors;
at least three evaluations; tested on each model and on real use.
