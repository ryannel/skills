# OpenAI: Prompting (ChatGPT and Codex), and Custom instructions with AGENTS.md

- URLs: https://developers.openai.com/codex/prompting (redirects to https://learn.chatgpt.com/docs/prompting) and
  https://developers.openai.com/codex/agent-configuration/agents-md
- Read in Chrome on 2026-11-10. Paraphrased.

## The prompt's four parts

- Goal: what should be done. Context: what information or sources help. Output: format, length, level of detail.
  Boundaries: what must stay unchanged, what to avoid, what to check before acting.
- "Use only the parts that help." A short prompt is often enough. No required format.

## Their main points

1. Start with the result, not a list of steps. Add the audience or format when it changes the output. "Describe a
   process when the process itself matters. Otherwise, leave [it] room to search, compare information, and adjust
   its approach."
2. Share the information that could change the result. Add only the sources that matter and say what to take from
   each. For connected sources, name where to look and what to find, not every search.
3. Boundaries are "the few instructions" needed to prevent extra work or an unintended action. Add one when
   changing the wrong detail would make the result unusable, or when you want to review before it affects other
   people. Focus on the one or two that matter. Examples: keep the approved dates unchanged; use only the supplied
   sources and flag gaps instead of guessing; prepare a draft, don't send it.
4. Say how the result will be used. That sets length, detail and organisation.
5. For important work ask for a final check that names what to check ("every action item has an owner and a due
   date"; "flag what you couldn't verify").
6. Separate required work from optional polish.

## Prompting Codex

- A useful Codex prompt: names the behaviour wanted, points to the relevant code or reproduction steps, keeps the
  important constraints, and says how to verify the change.
- For a bug, the reproduction steps and constraints "matter more than a high-level description".
- An image gives visual requirements; behaviour it doesn't show (hover, validation, keyboard) must be in text.
- `/plan` to investigate and propose first. `/goal` sets a persistent goal.
- While Codex works, a message can steer the current run (change direction, add a detail) or be queued for the
  next run.
- If you revert one of its edits, tell it, so it doesn't overwrite yours.

## AGENTS.md

- Codex reads AGENTS.md before any work, once per run. Order: the global file in `~/.codex` (`AGENTS.override.md`
  if present, else `AGENTS.md`), then one file per directory from the project root down to the working directory.
  Files are concatenated root-down; the closer file comes later and so wins.
- Combined size limit 32 KiB by default (`project_doc_max_bytes`). Beyond it, files stop being added. Split
  guidance across nested directories.
- Put an override as close to the specialised work as possible.
- Code review rules go in a `## Code Review Rules` section in the AGENTS.md nearest the code. Keep rules concise;
  say what behaviour to flag and the safe path or exception; leave formatting and lint to CI.
- To check what loaded, ask Codex to summarise its current instructions.
- Their sample AGENTS.md still says "Always run `npm test` after modifying JavaScript files", which the newer
  Astra blog post warns can cause needless testing. The blog post is the newer word.
