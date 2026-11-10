# OpenAI Developers blog: Rethinking skills and prompts for GPT-6 Astra

- URL: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
- Read in Chrome on 2026-11-10. Paraphrased. The good/bad pairs are OpenAI's, reworded.
- The argument: instructions built up over a year of steering weaker models (skills, AGENTS.md, task prompts) now
  get in the way. Each release is a reason to re-check them; Astra more than any before.

## Skills

1. Descriptions should be "as short as possible while making it clear when the model should use them".
   - When many skills are installed, Codex shortens descriptions to fit, so the model sees less of each.
   - Descriptions that contradict each other, or that over-emphasise when to use the skill, make the model load
     instructions that don't help.
   - Bad: a migration skill that says to use it "when working with databases, queries, models, or persistence".
     Good: use it "when adding or changing a migration, or reviewing its rollout".
   - This is the opposite of the "pushy description" advice in Anthropic's skill-creator and on agentskills.io.
     OpenAI says it updated its own `$skill-creator` to counter these failures.
2. Progressive disclosure. Reading a skill uses context, brings compaction closer, and introduces guidance that may
   not apply. For a skill with several workflows, the root document is "a minimal router" to supporting docs and
   scripts.
3. Recipes now hurt. Many skills were written as detailed itineraries. Models handle nuance and ambiguity much
   better, so "overly specific guidance can now hinder results where it previously helped".
4. Other models read the same files. A repository's skills guide other contributors' agents, which may run other
   models. Guidance that helps Sol or Luna may over-constrain Astra. Consider who will read what you leave behind.

## AGENTS.md

- It applies to every task in the repository, so re-check each line often.
- Don't require reading a stack of docs before every edit. Say which doc is for what: "Use architecture.md for
  service boundaries, database.md for schema changes, and deployment.md when preparing a deployment."
- Earlier models needed telling to run tests and check their work. Astra does it unprompted; the old lines cause
  needless testing.
- Astra is tentative about how far to go. Use AGENTS.md to give standing permission for a workflow you know is
  safe, with the reason: the local tests use disposable fixtures and have no production access, so run them, fix
  failures the change caused, and re-run without asking at each step.

## Boundaries

- Strong "ask first" language written to restrain an earlier model is taken very seriously by Astra. It may stop
  where you would be happy for it to continue. Rewrite that language.

## Persistence

- Astra may reach a first implementation and come back for review with work still to do.
- Define completion before starting. If the task includes running the result, inspecting it and fixing what
  fails, say so in the request.
- A requirement to stop for review after the first implementation pulls the stopping point earlier. Check that
  you need that decision.
- To have it explore beyond a first pass, say what to explore and where to stop.

## Their closing suggestion

- Ask the model itself to audit your skills and instruction files against these points.
