# OpenAI: Build skills (ChatGPT and Codex)

- URL: https://developers.openai.com/codex/build-skills (redirects to https://learn.chatgpt.com/docs/build-skills)
- Read in Chrome on 2026-11-10. Paraphrased.
- Codex and ChatGPT read the same Agent Skills format as Claude Code: a folder with SKILL.md (`name` and
  `description` required), optional `scripts/`, `references/`, `assets/`. OpenAI adds an optional
  `agents/openai.yaml` for display metadata, invocation policy and tool dependencies.

## What is loaded

- At start: each skill's name, description and file path.
- The list may use at most 2% of the model's context window (8,000 characters if the window is unknown). With
  many skills, Codex shortens descriptions first, and for very large sets may leave some skills out with a warning.
- When a skill is chosen, its whole SKILL.md is read.

## Descriptions

- Implicit use depends on the description, so "write concise descriptions with clear scope and boundaries".
- Put the main use case and trigger words first, so a shortened description still matches.
- Their template line: "Explain exactly when this skill should and should not trigger."

## Invoking

- Explicit: `$skill-name` in Codex, `@` in ChatGPT. Implicit: the model matches the task to the description.
- `policy.allow_implicit_invocation: false` in `agents/openai.yaml` makes a skill explicit-only (the Codex
  counterpart of Claude Code's `disable-model-invocation`).

## Where Codex finds skills

- `.agents/skills` in the working directory and each parent up to the repository root; `$HOME/.agents/skills`;
  `/etc/codex/skills`; and system skills bundled with Codex (`skill-creator`, `skill-installer`).
- Two skills with the same name are not merged; both appear.
- Disable one without deleting it with a `[[skills.config]]` entry in `~/.codex/config.toml`.

## Their four best practices

1. Keep each skill focused on one job.
2. Prefer instructions over scripts unless you need deterministic behaviour or external tooling.
3. Write imperative steps with explicit inputs and outputs.
4. Test prompts against the description to confirm it triggers correctly.

## Making one

- `$skill-creator` asks what the skill does, when it should trigger, and whether it is instruction-only (the
  default) or includes scripts. "Record & Replay" drafts a skill from a recorded demonstration.
