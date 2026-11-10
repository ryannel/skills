# Claude Fable 5.2

Checked against Anthropic's documentation on 10 November 2026. Advice about a model goes out of date faster than
anything else in this skill, so if Anthropic has published newer guidance, read it first.

## Habits to write against

Fable follows every instruction exactly as written, and that includes every caution it finds: in the prompt, in
instruction files, in saved notes and in a reviewer's messages, however old. A stale "always ask first" is enough
to make it ask for approval it doesn't need, or refuse to retry something that failed. So keep cautions few and
current, and remove old ones from those files rather than adding a line that overrides them. Write "get approval
before X" rather than "never X", and where a boundary sits close to ordinary work, say where it stops.

Like Opus, it can end a turn with a list of what's left, or an offer to continue. Say that errors, timeouts and
failing tools are things to work through, and that anything protected on purpose is to be reported.

With code it doesn't think it owns, Fable adds new code beside the old instead of restructuring it. Telling it
"this codebase is yours" fixes that, and makes it merge duplicates, but it also makes it change things nobody
asked for. So say both who owns the code and what is in scope.

How much it delegates depends on the prompt. With no guidance it delegates too little; if the prompt invites
delegation, it delegates too much. Say when a subagent is worth its cost, and roughly how much to hand off.

Hard style limits, such as a maximum number of words per sentence, make its prose choppy. Instead, say who will
read what it writes and what they need from it.

It can work for a long time without saying anything. If someone is following the run, ask for a one-line update
every few tool calls.

It is slow to point out a mistake in its own earlier answer if anything in the prompt tells it to treat earlier
answers as settled. Remove lines like that.

## Lines to leave out

Don't write a token budget you don't mean. Fable changes how much it spends to match a budget it finds in the
prompt.
