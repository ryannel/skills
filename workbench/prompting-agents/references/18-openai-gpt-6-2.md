# OpenAI: GPT-6.2 Astra and GPT-6.2 Sol

Read 17 November 2026, the release day, through fetch subagents. No page shows a date.

## Using GPT-6.2 (API guide)

<https://developers.openai.com/api/docs/guides/latest-model/gpt-6.2-astra.md>. The old "Using GPT-6" URL
(`/api/docs/guides/latest-model`) now serves this guide. A `gpt-6.2-sol.md` variant returns 404.

- Covers `gpt-6.2-astra` ("the most demanding tasks") and `gpt-6.2-sol` ("complex work at lower cost"). Every
  behaviour section is headed as Astra behaviour; the examples are "a starting point across the GPT-6.2 model
  family". No Sol-specific prompting advice.
- Writing: more concise and direct by default than earlier models; revisit "be concise" lines. Use the user's
  terms, active voice, key points first; final answers self-contained, without shorthand from reasoning, tool
  calls or subagent instructions.
- Task completion: when intent is unclear it may propose a next step and wait. Stop only for a large scope
  change, a concrete block, a user-owned decision, or an irreversible or destructive action; otherwise make a
  reversible assumption, state it, and continue. Check the work against the full request before finishing.
- Code: reuse existing logic, keep behaviour callers rely on, readable over dense. Skip new tests unless
  requested, required by the repo, or needed for a specific regression.
- Effort: start at `medium`; replace `none`/`minimal` with `low`. Higher effort helps persistence on long tasks.
- Does not mention: GPT-6 or GPT-6.1 by name, lists/tables, skills, AGENTS.md, delegation.

## Prompting GPT-6.2 in Codex

<https://learn.chatgpt.com/guides/prompting-gpt-6-2-astra>, linked from the Codex prompting page
(`developers.openai.com/codex/prompting`, which now redirects to `learn.chatgpt.com/docs/prompting`).

- Applies across the family, "including GPT-6.2 Astra and GPT-6.2 Sol". First passes are closer to usable than
  GPT-6 Astra's.
- Describe the work as to a colleague who knows the project, and say what you will look for in review.
- When work splits into independent parts, tell Codex to use subagents as needed; put recurring instructions of
  that kind in a skill or AGENTS.md with the condition for when they apply.
- AGENTS.md: keep it lean; requirements and conventions Codex can't infer, plus workflows the project depends on.
- Visual work: review at the size people will see it; try the actions an interactive result supports.
- Not covered: approvals, formatting, conciseness, cautions from older models.

## Release announcement and model pages

- `openai.com/index/introducing-gpt-6-2-astra-sol/` returned 403. The OpenAI staff post
  <https://community.openai.com/t/gpt-6-2-astra-and-sol-are-now-available/1417531> reproduces it: released
  17 November 2026; Astra the frontier model for the hardest projects, Sol efficient for everyday work; Sol
  "nearly matches" Astra on FrontierCode 2.0 at about a fifth of the cost. No prompting or migration advice.
- <https://developers.openai.com/api/docs/models/gpt-6.2-sol>: rejects reasoning effort `none`.
- The Codex models page (`learn.chatgpt.com/docs/models`) lists both 6.2 models under "Recommended models". The
  fetch found no "previous generation" label on GPT-6 Astra or GPT-6.1 Sol, though the Codex app's own model list
  reportedly shows one.
- The GPT-6 Astra skills blog post has no update note for 6.2.
