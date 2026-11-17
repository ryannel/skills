# GPT-6.2 Astra and GPT-6.2 Sol

Checked against OpenAI's documentation on 17 November 2026, the day both models were released. Advice about a model
goes out of date faster than anything else in this skill, so if OpenAI has published newer guidance, read it first.

Astra (`gpt-6.2-astra`) is OpenAI's most capable model, for the hardest work. Sol (`gpt-6.2-sol`) is the cheaper
model for everyday work. OpenAI has published one set of prompting advice for both: its guide describes Astra's
behaviour and calls its examples "a starting point across the GPT-6.2 model family", and its Codex guide says the
same techniques apply to Sol. So everything here is written for Astra and applies to Sol too.

The sources are OpenAI's [Using
GPT-6.2](https://developers.openai.com/api/docs/guides/latest-model/gpt-6.2-astra.md) guide, its [Prompting GPT-6.2
in Codex](https://learn.chatgpt.com/guides/prompting-gpt-6-2-astra) guide, and the [release
announcement](https://community.openai.com/t/gpt-6-2-astra-and-sol-are-now-available/1417531). Lines marked **New
in 6.2** come from those pages. Lines marked **From GPT-6 Astra** come from OpenAI's earlier [Rethinking skills and
prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) post.
The 6.2 pages neither repeat nor contradict them, so they are kept until a test shows they no longer hold.

## Habits to write against

When the request is unclear, Astra may propose a next step and wait for you to confirm it, rather than take it. So
say what counts as finished, and tell it to do everything it is already allowed to do before it asks. **New in
6.2:** OpenAI's guide now names the few reasons worth stopping for: a large change of scope, a concrete block, a
decision that belongs to the user, and an action that can't be undone. Everywhere else, it suggests telling the
model to make a reasonable assumption it can reverse, say what the assumption was, and carry on. **From GPT-6
Astra:** if the prompt says "can you…" or "help me…", say that it is a request to do the work, not to discuss it.

**New in 6.2:** Astra is more concise and direct by default than the models before it. A "be concise" line written
for an older model now pushes it further than you want, so re-read any such line and keep it only if the answers
are still too long.

**New in 6.2:** Its first version is closer to usable than GPT-6 Astra's, but it still stops when the work looks
done. Say what you will look for when you review the result, and ask it to check the work against the whole request
before it finishes. For visual work, ask it to look at the result at the size people will see it, and to try the
actions an interactive result offers. Higher effort helps it stay with a long task through the final checks.

**New in 6.2:** It writes new tests only when they are requested, when the repository requires them, or when a
particular regression needs one, and OpenAI's guide suggests saying so. If a line in an instruction file says
"always run the tests", it is now the cause of extra test runs. Remove it, and say what checking this particular
change needs. **From GPT-6 Astra:** the same was true of the earlier model, which ran tests on its own.

**From GPT-6 Astra:** it delegated too little unless told otherwise. **New in 6.2:** when work splits into
independent parts, OpenAI's Codex guide says to tell it to use subagents as needed, which leaves the model to
decide when parallel work helps and how to divide it. If the same kind of split comes up again and again, put that
line, with the condition for when it applies, in a skill or `AGENTS.md`.

**From GPT-6 Astra:** it takes cautions at full strength, particularly anything worded as "ask first". An old
caution in an instruction file, a saved note or a reviewer's message can make it ask for approval it doesn't need,
or refuse to retry. Remove those lines, write "get approval before X" rather than "never X", and where a boundary
sits close to ordinary work, say where it stops.

**From GPT-6 Astra:** with many skills loaded, it sometimes paused and it wasn't clear why. Ask it to name the
skill file and quote the line that made it stop. It also helps to say that the user's instructions outrank a
skill's.

**From GPT-6 Astra:** it answered in lists and tables by default. If you want prose, ask for paragraphs, with lists
only for items that are parallel or in sequence.

## What a prompt for Astra needs

Less than you might expect. **New in 6.2:** OpenAI's Codex guide says to describe the work as you would to a
colleague who knows the project, and to say how you will judge it. For written answers, OpenAI's guide asks for the
user's own terms, the main point first, and a final answer that stands on its own, without shorthand carried over
from its reasoning or from instructions it gave its subagents. For code, describe the project's conventions and the
behaviour that callers rely on, because the model reuses existing logic when it knows what must be kept.

**New in 6.2:** the Codex guide says an `AGENTS.md` for these models should stay short. Put in the requirements and
conventions Codex can't work out from the code, tests and docs, and any workflow the project depends on, and leave
routine choices to the model.

## Sol

OpenAI says Sol nearly matches Astra on merge-ready changes to real codebases, at about a fifth of the cost
([announcement](https://community.openai.com/t/gpt-6-2-astra-and-sol-are-now-available/1417531)). It has published
no case where Sol misses something Astra finds. **From GPT-6.1 Sol:** the earlier Sol missed indirect cases that
Astra caught, such as a flag used only as a dependency of another flag ([Maintaining software with the GPT-6
family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)). Until a test shows the gap
is closed, name the kind of indirect case you mean when you need those found.
