# OpenAI Developers blog: Maintaining software with the GPT-6 family

- URL: https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family
- Read in Chrome on 2026-11-10. Paraphrased. Written by an engineer on OpenAI's Core Experimentation team. It is
  the only source I found with real prompts for GPT-6 Astra and GPT-6.1 Sol and measured results for both.

## What the prompts look like

- Dead code, first try. One sentence, typos included: asks for help finding and cleaning up dead code, and says
  it may check Slack, the feature-flag platform "or any other source you need to confirm" things are unused. The
  author says this was too ambiguous for GPT-5.6 Sol to complete. Astra worked out where to look (past pull
  requests, Slack threads, trackers, production profiling tables) and explained each deletion.
- Stale experiments. Five sentences. In order: the outcome (find and remove dead code tied to stale gates in
  projects A and B); what to verify (live configuration, git history, overlapping pull requests); what to preserve
  (production behaviour, safeguards, gates meant as kill switches); what to ignore (SDK fallbacks, local
  overrides); the form of the result (one small draft pull request per clean-up, with a link to the evidence).
- The whole-repository `/goal`. Longer. It states the scope ("every… in this entire repository"), names the
  indirect cases the model might miss (enums, wrappers, aliases, dynamically assembled names, cross-service
  consumers), says not to stop at a conservative shortlist, says what the report must contain, and ends with one
  boundary: "Do not modify live configurations or services."
- None of them gives steps. Each gives the outcome, the evidence wanted, what to leave alone, and what comes back.

## How the prompts were made

- Start with one small task and a short prompt. Review the result.
- Comment on the result, then ask the model to fold the review feedback into the next, wider prompt. The model
  wrote the `/goal` prompt after the author had reviewed its first pull requests.
- Scale from one instance, to a subdirectory, to the whole codebase.

## Astra and Sol 6.1 on the same prompt

| Configuration | API cost | Findings | Cost per finding |
|---|---|---|---|
| GPT-6 Astra, Ultra | $109.06 | 142 | $0.77 |
| GPT-6.1 Sol, Ultra | $15.12 | 131 | $0.12 |
| GPT-6.1 Sol, Medium | $5.27 | 86 | $0.06 |

- Sol 6.1 at Ultra found 92% as many as Astra for 14% of the cost.
- Most of the difference was one pattern: constant feature flags used as dependencies of other flags. Astra
  found them; Sol 6.1 missed them.
- The author's conclusion: find the cheaper model's error pattern, then write the prompt line that corrects it.
  And re-check those lines at each new model, because a later model may make them obsolete.

## Judgement

- Astra found a flag that cost CPU but was marked "Permanent" in the console. It raised it for a person to decide
  instead of removing it.
- Some of the models' proposals "added more complexity than their expected benefit justified". A person still
  prioritises and measures.

## A prompt for auditing instruction files (theirs, summarised)

- Find one AGENTS.md instruction in recent sessions that seems to have misdirected an agent or caused needless
  work. Replay the original prompt twice from the same snapshot with the same model: once unchanged, once with
  only that instruction removed or fixed. Compare quality, behaviour, tool calls, tokens, time and cost.
