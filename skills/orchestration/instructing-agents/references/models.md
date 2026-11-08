# Models, persistence and harnesses

Contents:
- [Which vendor warns against which habit](#which-vendor-warns-against-which-habit)
- [Persistence by model and harness](#persistence-by-model-and-harness)
- [Harness stop causes](#harness-stop-causes)
- [Claude Opus 5.5](#claude-opus-55)
- [OpenAI GPT-6 Astra](#openai-gpt-6-astra)
- [OpenAI GPT-6.1 Sol](#openai-gpt-61-sol)
- [Choosing a model and effort](#choosing-a-model-and-effort)

Each vendor's advice comes from testing one particular model. A tip that helped that model may not hold for yours, so
re-check it on the model you're using. Sometimes a newer guide doesn't mention something an older one found. When
that happens, this file keeps the older finding and marks it as untested on the newer model.

## Which vendor warns against which habit

The two vendors warn against some of the same habits, but not always for the same reasons. A blank cell means this
file records no warning from that vendor.

| Habit | Anthropic | OpenAI |
|---|---|---|
| Step-by-step recipes and itineraries | Prefer judgment, and give heuristics for open-ended work. But still give sequential steps and checklists for complex, fragile operations. | These now hurt Astra. |
| Emphasis and capitals | Plain lines are followed. Piling on emphasis makes Claude apply a rule too widely or trigger tools too often. | The warning is about strong "ask first" language and over-emphatic skill descriptions. |
| Mandatory reading lists | | Point to docs by use case instead. |
| Review stops after a first implementation | | They pull Astra toward stopping early. |
| "Keep going" and "double-check" lines | "Keep going" causes over-work, and Opus 5 already checked its own work. "Be thorough" only nudges within the effort setting, so change the effort instead. | OpenAI recommends persistence wording for Astra (see below). |
| "Run the tests" encouragement | | Astra already tests, and the line makes it test too much. |

## Persistence by model and harness

The vendors disagree about whether to push a model to keep going. So decide separately for each run, based on the
model and the harness it runs in.

For Astra, define what "complete" means before it starts, and say whether the job includes running, inspecting and
fixing the result. OpenAI's autonomy wording helps here. It tells the model to lean toward action, to carry the task
through to completion, and to treat "can you…" as a request to act rather than a question. It shouldn't stop at a
plan or a partial answer. Keep OpenAI's limits on that wording too. The model should act on its own unless an action
is clearly destructive or irreversible, and it shouldn't add warnings or approval steps nobody asked for.

For Sol, add no extra pressure. In its system card it kept going past warnings more often than Astra did. Spend those words on asking for evidence
and honest claims instead.

For Claude with a human in the loop, add no push either. Current Claude models carry on through a task once it's
agreed, and lines that push them cause over-work.

For Claude running unattended, use a harness loop: Claude Code's `/goal`, or a Stop hook. If you don't have one, use
the unattended paragraph from the Opus 5.5 guide. That paragraph names the ways Claude tends to stop early, so that it
avoids them:

- a summary that announces the next step without taking it
- an offer to continue
- a list of decisions that don't actually block the work
- stopping at a natural checkpoint

Also name the stops you do want. Keep your own confirmation step for risky or irreversible actions. And add the
paragraph from the very first request.

## Harness stop causes

When an agent stops, check the harness before you blame the instructions.

Codex `/goal` has several ways to stop. An interruption pauses the goal, and only the user or the system can resume
it. Running out of budget stops substantive work without completing the goal. A turn that only makes a plan doesn't
trigger a continuation. A continuation turn that makes no tool call stops the next continuation from happening. And
the agent can only declare itself blocked after several turns in a row with no progress.

Claude Code `/goal` stops in different ways. The loop stops after several turns in a row with no tool use, but the goal
stays set. Evaluation waits while background work or a subagent is running. Auth errors, credit errors and context
overflow clear the goal. Rate limits only pause it. A Stop hook can only block a stop a limited number of times.

Claude with no loop at all stops when the turn ends, because the session ends there. So if an Opus 5.5 turn ends with
only text, it may have been a progress report that the harness treated as the finished answer.

## Claude Opus 5.5

Model id: `claude-opus-5-5`.

Effort is the main control. The default is `medium`. Opus 5 defaulted to `high`, but Opus 5.5 at `medium` matched or
beat Opus 5 at `high` on multistep repository work, and `low` comes close on several coding evals. So set effort
explicitly, and try a few levels on your task. Keep `xhigh` and `max` for when you've measured that they help. If you
want less thinking, lower the effort rather than writing instructions about it. Thinking can't be turned off, and
forcing a tool with `tool_choice` returns an error. To get a tool used, say when it applies.

In Claude Code, it tends to read a request conservatively and build the smallest thing that satisfies it. So say how
ambitious to be, and don't add a scope-narrowing paragraph unless you've seen it over-reach.

It starts work quickly. On loosely specified tasks that draw on several sources, tell it to explore broadly first,
including sources the task didn't name. Keep untrusted content out of what it searches.

In unattended loops, keep the parts of the task in a checklist that it updates. When items are still open and it
hasn't stated a blocker, continue it with a short message that names those items. Stop after two or three automatic
continuations. Wait for background work to finish before treating the task as done.

Time signals change how it works. A line showing elapsed time against a budget, such as `elapsed 340s / 1200s`, mainly
makes it run more work in parallel in multi-agent harnesses. Keep a hard timeout of your own anyway. Under time
pressure it checks its work a little less.

For the look of a frontend, "avoid a generic AI look" doesn't work. It just swaps one default style for another. Name
the specific patterns to avoid instead, and add to the list each round.

The rest of this section was measured on Opus 5 and hasn't been tested on 5.5.

Opus 5 sometimes widened the scope of a task on its own judgment. Opus 5.5 in Claude Code leans the other way (see
above), so use this only where you've seen it over-reach. The scope paragraph tells it to:

- deliver what was asked, at the intended scope
- check in only when different readings of the request would lead to materially different work
- if the request seems wrong, say so in a sentence and then continue as asked

It checks and corrects its own work without being asked. So remove "double-check" lines and lines asking for a
verification subagent. Limit its narration of corrections to errors that change the user's decisions.

Its responses and written deliverables run long, and lowering effort doesn't shorten them. If you want brevity, ask
for it explicitly.

It delegates readily. Only delegate work that is large, independent and can run in parallel. Don't ask it to spawn a
subagent to double-check its own work, because it already does that. An independent reviewer with its own brief is a
different thing, and still worth it where the work is hard to judge. Use one subagent where one is enough. Claude Code and the Agent SDK have hard caps on subagents.

## OpenAI GPT-6 Astra

Model id: `gpt-6-astra`.

Astra is tentative about stopping. It may come back for review after a first implementation while work still remains,
and it asks more clarifying questions than earlier models. See [persistence](#persistence-by-model-and-harness) for
what to do about that, and remove review gates you don't need. When you do want approval, have it prepare results you
can review before it asks.

It is more sensitive to skills and AGENTS.md than earlier models. Text that's unclear or contradicts itself makes it
pause. So make the
order of precedence explicit: the user's instructions win over skill guidance. And ask it to cite the exact skill line
behind any pause.

It tests small changes too much. Ask for tests that are meaningful and necessary, and sized to the change.

It delegates too little. If you want it to hand out work in parallel, say so.

Its writing is heavily formatted. Ask for short prose paragraphs, lists only where they help, plain words, and the
main point first.

For effort, neither `none` nor `minimal` is supported. If you used `minimal` before, start with `low` and compare.

## OpenAI GPT-6.1 Sol

Model id: `gpt-6.1-sol`.

There is no prompting guide specific to Sol. OpenAI points to the GPT-6 guide, which is centred on Astra. Sol is
trained like Astra and comes close to its quality at much lower cost.

Sol keeps going and overclaims more than Astra does. In its system card, it kept going past warnings more often when
it shouldn't have. It also reward-hacked more, hid its uncertainty more, and misrepresented its work more often on
coding-deception tasks. Those gaps were in low-severity flags. At severity 3 and above, Sol had 28 flags to Astra's
27 across 49,650 tasks, so it isn't worse at the serious end. Even so, cut recipes and emphasis as you would for Astra, but don't add "keep going" pressure. That
last point is an inference from those figures. Ask for the evidence behind every claim. Keep what's verified, what's
approximate and what's blocked separate. And give it a stated path to follow when it's blocked.

Sol misses some subtle patterns that Astra catches. In OpenAI's audit, Sol Ultra found 92% of Astra's findings at about
14% of the cost. One thing it missed was constant feature flags that other flags depended on. So name known blind
spots in the goal or brief for that run. Keep those corrections narrow, and keep them out of shared skills and
AGENTS.md, because those files steer every model. Revisit the corrections when models change.

Broad, ambiguous requests worked on Astra but not on GPT-5.6 Sol. Nobody has re-measured that on 6.1. So for Sol,
start with a scoped goal that has clear validation criteria.

For effort, Sol takes `low` to `max` and defaults to `medium`. There is no `none`. Compare `medium` with `high` on your
own workload, and only use `xhigh` and `max` when you've measured a gain.

## Choosing a model and effort

Start small. Before scaling up, compare configurations on one task that's typical of the work. A cheaper model at
medium effort is often enough.

Raise the effort or switch to a stronger model for hard reasoning, deep debugging, subtle audits that cut across the
codebase, and long work with no one watching. Drop back down for routine follow-ups.

Effort is a tuning knob. It won't rescue a bad prompt, so fix the instructions first.
