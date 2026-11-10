# Claude Opus 5.5

Checked against Anthropic's documentation on 10 November 2026. Advice about a model goes out of date faster than
anything else in this skill, so if Anthropic has published newer guidance, read it first.

## Habits to write against

In a long unattended run, Opus tends to stop partway and write a progress report, or offer to continue, even with
work left. So say that errors, timeouts and failing tools are things to work through, not reasons to stop, and
that anything protected on purpose is to be reported rather than worked around. Then name any other stopping
points you don't want.

It can also work for a long time without saying anything. If someone is following the run, ask for a one-line
update every few tool calls.

## Lines that help on Opus

**On a loosely specified task across several applications,** add one sentence asking it to look through the
relevant sources first, including ones the task didn't mention. Otherwise it starts work quickly, from whatever
it already has.

**When it leads subagents,** put the elapsed time in each message, as in `elapsed 340s / 1200s`. Opus responds
strongly to it: it runs more subagents in parallel and finishes sooner.

**When it builds an interface,** name the specific visual patterns to avoid. "Avoid a generic look" only swaps
one default look for another.
