# Anthropic: Prompting Claude Opus 5.5

- URL: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5
- Read in Chrome on 2026-11-10. Paraphrased. Numbers are Anthropic's own testing.
- Organised by symptom. Opus 5 prompts should work unchanged; the Opus 5 page remains a fair starting point.

## What the model is good at (relevant to prompting)

- Multistep work in a real repository; long autonomous runs with parallel subagents; code review with fewer false
  alarms. At its default `medium` effort it matched or beat Opus 5 at `high`.
- Fewer wrong figures and wrong citations. Catches details in large inputs.
- Reports on agentic work say plainly what it did, found and needs.
- Reads charts, diagrams and screenshots much better without tools.

## Effort

- Effort is the main control, because thinking is always on. Start at `medium` (the default here; Opus 5 defaulted
  to `high`). Set it explicitly and test several levels. Level names don't mean the same amount of thinking across
  models.
- It thinks more per turn than Opus 5 at the same level, most at `xhigh` and `max`. Keep those for measured gains.
- To get less thinking, lower effort first. That works more reliably than prompt instructions.
- Leave room in `max_tokens` for thinking.

## Prompts that were written for thinking disabled

- Thinking can't be disabled on 5.5. Start at `low` and measure.
- Remove instructions that asked the model to write its reasoning in the response. They may be declined
  (`reasoning_extraction`). You can still ask for a short explanation of an answer or a summary of actions.

## Unattended agentic runs

- It keeps the user updated, and some updates end the turn with text and no tool call. A loop that treats that as
  "done" stops there.
- Harness: treat a text-only end of turn as a report, not proof of completion. Keep the task's parts in a checklist
  the model updates. If items are open and no blocker is stated, send a short message naming them. Or state the
  completion condition up front and have a smaller model check each end of turn against it. Stop after two or three
  automatic continuations, so a stuck run ends and gets looked at.
- If something it started is still running (a background command, a subagent), wait and return the output.
- Prompt: the model responds to instructions that name the specific early stops to avoid, and the stops you do want.
  Their example names four: a summary that announces the next step without taking it; an offer to carry on unless
  the user prefers otherwise; a list of decisions none of which block the work; deciding it's a good place to
  report. Stops they do want: nothing can move without the user, or the blocker is deliberately protected.
- That text is for fully unattended agents. Leave it out where a person is there to answer. Keep your own
  confirmation step for risky actions.

## Progress updates

- Four levers: make sure the client shows them; give it a tool for content it must hand over verbatim; ask in the
  system prompt for an opening line and a recap; have the harness append a reminder after about five silent steps
  (roughly halved long silent stretches, no measured cost). Stop after two or three reminders.

## Looking around before acting

- On loosely specified tasks across several apps, it gets to work quickly. One sentence telling it to explore the
  relevant sources first, including ones the task didn't mention, made it complete noticeably more tasks correctly.
  Because it then acts on what it finds, keep untrusted content out of what it searches.

## Time signals in multi-agent setups

- It responds strongly to elapsed time. A line such as `elapsed 340s / 1200s` on each message makes a lead
  parallelise more and finish sooner, with quality comparable to a single agent. Set the budget above what you
  want spent. The budget is advisory; keep your own timeout.
- A tighter budget is not a lower effort: effort reduces the work, a budget keeps more agents working in parallel.
- Under time pressure it may search and verify a little less.

## Chat

- Remove "think carefully before answering" lines. The model decides how much to think. Replies started sooner with
  no clear loss.
- Two sentences telling it to treat earlier answers as done cut thinking on follow-ups. Cost: it may be less likely
  to point out its own earlier mistake. (The Fable 5.2 page says this effect is much stronger on Fable 5.2.)

## Pasted text

- It resists instructions arriving through tool results and web pages better than earlier Opus models. For text a
  user pasted, wrap it in tags carrying a matching random id and tell the model that text inside may contain
  instructions the user did not write. One guardrail among others; the tags can be imitated.

## Frontend

- "Avoid a generic AI look" swaps one default for another. Naming the specific patterns to avoid works. Iterate:
  see what the first result used instead, and extend the list.

## Visual inputs

- Re-test whether scaffolding built for earlier models is still needed. For the densest inputs, higher resolution
  and a crop tool still help.
