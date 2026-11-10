# Models

Checked against Anthropic's and OpenAI's documentation on 10 November 2026. These facts go out of date faster
than anything else in this skill. If the model you are writing for is newer than the ones here, read its vendor's
prompting page first.

## By symptom

Find what you see. Before you add the fix, look for an instruction that causes the symptom and remove that first.

| What you see | Most likely on | What to change in the prompt |
|---|---|---|
| The turn ends with a list of what's left, or an offer to continue | Fable 5.2; Opus 5.5 unattended | Say that errors, timeouts and failing tools are to be worked through, and that things protected on purpose are to be reported. On Opus 5.5 also name the stops you don't want |
| It asks before doing work it could have done | GPT-6 Astra | Tell it to finish the work it is already allowed to do, so that approval is the last step on a finished result. Say that "can you…" and "help me…" are requests to do the work |
| It returns after a first version | GPT-6 Astra | Put running the result, checking it and fixing failures into what done means |
| It asks for approvals it doesn't need, or won't retry | Fable 5.2; GPT-6 Astra | Remove old cautions from instruction files, saved notes and reviewer messages. Name the steps that need no approval. Rewrite "never X" as "get a go-ahead before X" |
| It pauses and you can't tell why | GPT-6 Astra with many skills | Ask it to name the skill file and quote the line that made it pause. State that the user's instructions outrank a skill's |
| It runs far more tests than the change needs | GPT-6 Astra; Claude Opus 5 | Remove "always run the tests" lines. Say what checking this change needs |
| It delegates too little | GPT-6 Astra; Fable 5.2 | Say when to delegate and how much |
| It delegates too much | Claude Opus 5; Fable 5.2 where prompts invite it | Remove lines that tell it to delegate. Say when a subagent is worth its cost |
| It adds code beside old code instead of restructuring | Fable 5.2 | Say who owns the code. "This codebase is yours" makes it merge duplicates. It also makes changes nobody asked for, so say what is in scope |
| Its prose is choppy | Fable 5.2 | Remove hard style limits such as "20 words per sentence". Describe the reader |
| Its replies are full of lists and tables | GPT-6 Astra | Ask for paragraphs, with lists only for items that are parallel or in sequence |
| It says nothing for a long stretch | Fable 5.2; Opus 5.5 | Ask for a one-line update every few tool calls |
| It is slow to point out its own earlier mistake | Fable 5.2 | Remove any line that tells it to treat earlier answers as settled |
| It finds fewer cases than the top model | GPT-6.1 Sol | Find the kind of case it misses and name it in the prompt. In OpenAI's one comparison, Sol missed indirect cases, such as a flag used only as a dependency of another flag |

## Lines that do nothing on these models

All four models always think before they act, and how much they think is a setting outside the prompt. Besides
the pressure phrases the main file lists, take these out:

- "Answer directly without deliberating." It doesn't reduce thinking.
- A request to write the reasoning into the reply. The model may decline it.
- A token budget you don't mean. Fable 5.2 changes how much it spends to match a budget written in the prompt.

## Lines that help on one model

- **Claude Opus 5.5, on a loosely specified task across several applications:** one sentence asking it to look
  through the relevant sources first, including ones the task didn't mention. It otherwise starts work quickly.
- **Claude Opus 5.5 leading subagents:** a line such as `elapsed 340s / 1200s` in each message. It responds
  strongly to elapsed time, runs more subagents in parallel and finishes sooner.
- **Claude Opus 5.5 building an interface:** name the specific visual patterns to avoid. "Avoid a generic look"
  swaps one default for another.
- **GPT-6 Astra:** a short, loosely worded request is enough. Astra works out where to look and what evidence it
  needs. OpenAI's own example prompts for it give the outcome, what to verify, what to keep and the form of the
  result. None gives steps.
- **GPT-6.1 Sol:** OpenAI has published no separate prompting advice for it. Start from the Astra advice.

## When the model changes

Re-read everything that carries over: system prompts, skills, instruction files, saved notes, and text the
harness adds to messages. Check each line against the leave-out list in the main file. Lines written to push an
earlier model now push too hard: Fable 5.2 follows each one as written, and GPT-6 Astra takes "ask first" wording
at full strength.

Both hosts can do this reading for you. In Claude Code, `/doctor prompt-audit` reports instructions written for
older models and files that contradict each other. In Codex, ask the model to audit your skills and `AGENTS.md`
against OpenAI's migration guide.
