# OpenAI: Using GPT-6 (the latest-model guide)

- URL: https://developers.openai.com/api/docs/guides/latest-model
- Read in Chrome on 2026-11-10. Paraphrased; the quoted prompt lines are OpenAI's suggested starting prompts,
  shortened.
- The page covers GPT-6 Astra (highest intelligence), GPT-6.1 Sol (near-Astra at lower cost), GPT-6.1 Terra and
  GPT-6 Luna. Its prompting section says the prompts "address behavior observed with GPT-6 Astra" and are a
  starting point across the family: evaluate them on the model and workload you use. There is no separate
  prompting section for GPT-6.1 Sol on this page.
- The same page keeps the GPT-5.6 guide below it. Two parts of that still matter and are noted at the end.

## Effort

- GPT-6 Astra and GPT-6.1 Sol do not support effort `none`. Use `low` instead. GPT-6.1 Sol supports `low`,
  `medium` (default), `high`, `xhigh`, `max`.
- Effort can be changed mid-conversation with a `configuration_update` item, which keeps the prompt cache.
- With reasoning on, `temperature` and `top_p` are not accepted.

## What Astra does differently (OpenAI's five headings)

1. Initiative and follow-through. It is built to collaborate, so it asks a question when the answer could change
   the result. It may stop where the user expected it to assume and continue. It also asks non-blocking questions
   while working.
2. Instruction following. Stronger than earlier models, and more sensitive to instructions in skills and files
   such as AGENTS.md. OpenAI "strongly recommend[s] auditing skills and other files" the model can reach.
   Unclear or conflicting guidance in a skill file can make it pause and block work early.
3. Personality and writing. Tends to detailed, formatted responses (lists, tables, Markdown) and to recurring
   phrases across sessions.
4. Subagents. May delegate less than you want.
5. Testing. Thorough before calling a coding task done; on small tasks this means broader tests than needed.

## OpenAI's fixes, one per heading

1. Autonomy:
   - Tell it to infer intent and scope from the instructions and context, lean towards action, and carry the task
     to completion, proceeding on its own unless a step is clearly destructive or irreversible.
   - Tell it that "can you…", "I want to…", "help me…" are requests to do the work, not to confirm it can.
   - Ask for approval only after a concrete, reviewable result exists. Do the authorised work first so approval is
     the last step (before a deploy, an external write, a merge, a publish). No permission needed for reversible
     or read-only steps, or where authorisation was given earlier or is strongly implied.
   - "Do not introduce unsolicited warnings, disclaimers, approval flows… due to hypothetical risk."
2. Skills against the user:
   - State the priority: the user's instructions take precedence over a skill's guidelines.
   - For transparency: if a skill makes it ask permission, pause, leave work unfinished or diverge from the user's
     intent, it should name and link the exact SKILL.md, quote the instruction, and say how it applies, keeping
     explicit requirements apart from its own reading of guidelines. OpenAI suggests this as a way to find silent
     and conflicting guidance when many skills and instruction files are loaded.
3. Writing:
   - Default to clear paragraphs, one main idea each. Lists only for parallel, sequential or comparable items.
     "Familiar words, concrete examples, and precise verbs." Active voice. Main point early.
   - Technical writing: plain language over jargon; technical detail only as far as it helps; match the reader's
     background.
   - A list of stock phrases to avoid, plus: state the action directly; don't add what you won't do; no "X, not Y"
     framing that introduces an alternative nobody asked about; no invented compound labels; no vague qualifiers.
4. Subagents: say when and how much to delegate; the model responds well to that. Ask for messages between
   agents to be legible, since a person may read them.
5. Testing: no tests for reversible, low-impact changes that mirror the implementation. Run the tests the change
   needs; broaden or repeat only when new changes, failures or open concerns justify it.

## From the GPT-5.6 section (still the family's general advice)

- Favour leaner prompts. Removing repeated instructions and examples and simplifying tool descriptions improved
  internal coding-agent eval scores by roughly 10 to 15% and cut total tokens 41 to 66% (OpenAI's sample;
  directional). Method: start from a prompt that works; remove one group at a time; re-run the same evals; state
  each instruction once; expose only the tools the task needs; keep an example or style rule when it encodes a
  product requirement or corrects a measured gap.
- Define autonomy and approval boundaries in one compact policy, stated once. Requests to answer, explain, review,
  diagnose or plan: inspect and report, don't change. Requests to change, build or fix: make the in-scope local
  changes and run non-destructive validation without asking. Confirm before external writes, destructive actions,
  purchases, or a material expansion of scope. Name the safe local actions. Repeating "ask first" or "wait for
  approval" causes needless approval requests.
- Intent understanding: you often need not prescribe every step. Keep giving domain context, hard constraints,
  approval boundaries and success criteria, and say when an ambiguity should trigger a question.
- Length: broad "be concise" lines may now make answers too brief. For a short answer, say what it must keep
  (conclusion, evidence, caveat, next action) and what may go.
- Tone: labels like "friendly" are ambiguous. Describe the writing choices instead.
- Pro mode: keep the same outcome-focused prompt (goal, context, constraints, required evidence, success criteria,
  output format). Don't ask it to "think harder".
