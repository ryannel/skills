# domain-language

A project goes better when you, your agents, the code and the docs all use the same words for the same things.
Domain-driven design calls this shared vocabulary the ubiquitous language. Without one, each agent session picks
its own words, and after a while the code says `pending_review`, the docs say "claimed" and you say "ready", and
nobody is sure those are one thing.

This skill has the agent build that language with you and keep it sharp as the project goes on. It keeps the
agreed terms in `GLOSSARY.md`, and it:

- prefers the terms your field already uses, looked up rather than guessed, so that someone who knows the field
  recognises the work on sight;
- hunts out ambiguity: one word used for two things, or one thing called by two words;
- uses the agreed terms itself, and offers you the field's word when you use another, so you learn the field's
  language as you go;
- keeps an agreed term until someone deliberately changes it, whatever loose wording comes up in conversation;
- fixes names in the code, the docs and the UI that drift from the glossary, as it finds them;
- marks the terms it chose without you as `Proposed:`, so a guess is never mistaken for your decision;
- adds a short pointer to `AGENTS.md`, and `CLAUDE.md` if there is one, so later sessions keep to the glossary
  without this skill loaded.

## A glossary entry

```markdown
### Hold

A book kept on the shelf for a patron to collect.

- **Not:**
  - **Loan**: a book on loan has left the library; a book on hold hasn't.
- **Avoid:**
  - reservation: what patrons often say, but not the library term.
- **Source:** the standard library term (Koha, Evergreen)
```

## What's in the folder

- `SKILL.md`: the whole skill. It is short on purpose. The agent already knows domain-driven design, so the skill
  says what we want from it rather than explaining it.

## Install

```bash
npx skills add ryannel/skills --skill domain-language
```

## Where it comes from

The research behind it, a survey of the published glossary and ubiquitous-language skills, is in
[workbench/domain-language](../../workbench/domain-language/research.md). The skill was then cut down to the aims
above with the owner of this repository. An earlier, longer version was tested on three requests with and without
the skill. The current version hasn't been tested yet.

The orchestrate suite keeps its own project glossary and doesn't depend on this skill.
