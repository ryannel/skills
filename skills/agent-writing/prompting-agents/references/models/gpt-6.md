# GPT-6 Astra and GPT-6.1 Sol

Checked against OpenAI's documentation on 10 November 2026. Advice about a model goes out of date faster than
anything else in this skill, so if OpenAI has published newer guidance, read it first.

OpenAI has published no separate prompting advice for Sol, so everything here is written for Astra and applies
to Sol too. The one known difference is at the end.

## Habits to write against

Left to itself, Astra hands back its first version, and stops to ask before steps it could have taken on its own.
So say that the job includes running the result, checking it and fixing what fails. Tell it to do everything it
is already allowed to do before it asks for approval, so that approval is asked for on finished work. If the
prompt says "can you…" or "help me…", say that it is a request to do the work, not to discuss it.

It takes cautions at full strength, particularly anything worded as "ask first". An old caution in an instruction
file, a saved note or a reviewer's message can make it ask for approval it doesn't need, or refuse to retry.
Remove those lines, write "get approval before X" rather than "never X", and where a boundary sits close to
ordinary work, say where it stops.

With many skills loaded, it sometimes pauses and it isn't clear why. Ask it to name the skill file and quote the
line that made it stop. It also helps to say that the user's instructions outrank a skill's.

It runs far more tests than a change needs if the prompt or an instruction file says "always run the tests".
Remove that line, and say what checking this particular change needs.

It delegates too little unless told otherwise. Say when to hand work to a subagent, and how much.

It answers in lists and tables by default. If you want prose, ask for paragraphs, with lists only for items that
are parallel or in sequence.

## What a prompt for Astra needs

Less than you might expect. Given the outcome, Astra works out where to look and what evidence it needs, so a
short, loosely worded request is often enough. OpenAI's own example prompts for it give the outcome, what to
verify, what to keep and the form of the result. None of them gives steps.

## Sol

In OpenAI's one published comparison, Sol missed indirect cases that Astra caught, such as a flag used only as a
dependency of another flag. When you need those cases found, name the kind of case you mean.
