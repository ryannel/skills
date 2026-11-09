# Hosts and models

Contents:
- [What a new agent can already see](#what-a-new-agent-can-already-see)
- [What the harness already tells the model](#what-the-harness-already-tells-the-model)
- [Persistence](#persistence)
- [Why runs stop](#why-runs-stop)
- [Claude Opus 5.5](#claude-opus-55)
- [GPT-6.1 Sol and GPT-6 Astra](#gpt-61-sol-and-gpt-6-astra)
- [Choosing effort](#choosing-effort)

These facts move with each release, and some change on the server with no release at all. They were checked on
9 November 2026. Each vendor's advice was measured on one model, so a tip may not carry over to the next one.

## What a new agent can already see

The brief has to supply whatever the new agent can't see, so this decides how much context to write.

| Launch | Sees your conversation? | Loads project instructions? | Effort |
|---|---|---|---|
| Claude Code subagent (Agent tool) | No | CLAUDE.md and AGENTS.md, except the built-in Explore and Plan agents | The session's level on the same model. On another model, set `effort` on the call or in the agent file |
| Claude Code fork | Yes, up to the fork | Yes | Same as the parent |
| Claude Code skill with `context: fork` | No, despite the name | Yes | The skill's `effort` field, if set |
| `claude -p` | No | Yes | `--model` and `--effort` |
| Codex `spawn_agent` | Yes by default (`fork_turns="all"`). Pass `"none"` for a fresh start | Yes | `xhigh` by default, whatever the parent's |
| `codex exec` | No | Yes | `-m` and `-c model_reasoning_effort=…`. The default is low for Sol |

No Claude Code subagent gets your auto memory, output style or the skills you loaded. In Codex all agents share one
workspace and tool state, and a subagent's tokens count against the root goal's budget.

In Claude Code, AGENTS.md loads only when there's no project CLAUDE.md or CLAUDE.local.md. A CLAUDE.local.md added for
private notes silently stops AGENTS.md loading. `~/.claude/CLAUDE.md` doesn't count, so it loads alongside AGENTS.md.

## What the harness already tells the model

Codex sends GPT-6.1 Sol and GPT-6 Astra almost the same system prompt. It already tells them to persist until the
goal is done, to act without asking unless something is destructive or irreversible, to treat "can you…" as a request
to act, to put the user's instructions above skills, to quote the skill line behind any pause, to test in proportion
to the change, and to write plain connected prose. Don't repeat these in a goal, brief or AGENTS.md. OpenAI found
leaner prompts scored 10–15% better on its coding evals (measured on GPT-5.6).

The Codex `/goal` template treats your goal as data, below the system prompt. A goal can state requirements, but it
can't override the harness's defaults. Change those in AGENTS.md, config or the approval policy.

OpenAI updates these prompts from the server, and the desktop app and the CLI can carry different versions. On
7 November the desktop version told Sol to "make the smallest change that fully solves the problem" and to skip new
tests unless they were requested, required by the repository, or needed to catch a specific regression. So if tests
or a broad scope are part of done, say so in the goal or in AGENTS.md. The template each surface has is in
`~/.codex/models_cache*.json`.

Claude Code adds its own guidance on delegation to Opus under its default system prompt, so a brief that also damps
delegation may double it.

## Persistence

Whether to tell an agent to keep going depends on the model and on whether a harness loop is running.

For GPT-6.1 Sol and Astra in Codex, add nothing. The system prompt already pushes them to finish. In OpenAI's system
card, Sol carried on past a warning in 23.5% of runs, against Astra's 17.4%, so spend the words on evidence instead.
Outside Codex, in a harness without that prompt, OpenAI's autonomy paragraph from the Using GPT-6 guide is worth
adding.

For Claude with a person in the loop, add nothing. Current Claude models carry on through an agreed task, and "keep
going" lines cause over-work.

For Claude running unattended, use a loop: Claude Code `/goal` or a Stop hook. Without one, use the unattended
paragraph from Anthropic's Opus 5.5 guide. It names the early stops to avoid (a summary that announces the next step
without taking it, an offer to carry on, a list of decisions that don't block anything, stopping at a natural
checkpoint) and the stops you do want. Keep your own confirmation for risky actions, and leave the paragraph out
where someone is there to answer.

## Why runs stop

Check these before blaming the text.

Codex `/goal`:
- An interruption pauses the goal, and only the user can resume it.
- Running out of budget stops new work. The model summarises progress and what's left.
- Three automatic continuation turns in a row with no activity block the goal. Interrupted continuations count.
- The model may call itself blocked only when the same blocker has held for three goal turns.
- Long runs at `xhigh` sometimes fail with "model is at capacity" or dropped streams.
- A server-side template change can alter behaviour with no model release.

Claude Code `/goal`:
- After several turns in a row with no tool use, the loop stops and hands back control, with the goal still set.
- Evaluation waits while a subagent or background command is running. A background job that never ends can stall
  the loop.
- Auth errors, credit errors and context overflow clear the goal. Rate limits only pause it.
- A Stop hook can block a stop only a limited number of times.

With no loop, a turn that ends in text ends the run. Opus 5.5 sometimes ends a turn with a progress update, and an
unattended harness reads that as finished. Treat a text-only ending as a report, keep the task's parts in a checklist,
and continue with a short message naming the open items, two or three times at most.

## Claude Opus 5.5

Model id `claude-opus-5-5`. Effort is the main control, and the default is `medium`, where Opus 5 defaulted to
`high`. For less thinking, lower the effort rather than writing about it. "Be thorough" only nudges within the level.
In Claude Code, `ultrathink` raises it for one turn.

No Anthropic source documents which way Opus 5.5 leans on scope. Claude Code's guide says Claude in general reads
requests conservatively and that "be ambitious" helps. Opus 5 widened scope on its own, and practitioners report Opus
5.5 doing so too. State the scope both ways: how ambitious to be, and what's out of bounds.

It gets to work quickly. On a loosely specified task that draws on several sources, say to look through the relevant
sources before acting.

It checks its own work. Opus 5 guidance says to remove "double-check" lines and requests for a verification subagent,
and that hasn't been re-tested on 5.5. A fresh reviewer with its own brief is a different thing and still worth it.

For honest status reports, Anthropic's measured wording (on Fable 5) is: "Before reporting progress, audit each claim
against a tool result from this session. Only report work you can point to evidence for; if something is not yet
verified, say so explicitly." It hasn't been re-tested on Opus 5.5.

Don't ask it to write out its reasoning step by step in a plan or review. It may decline that as reasoning
extraction. Ask for a short explanation of what it decided and why.

For a frontend's look, "avoid a generic AI look" swaps one default for another. Name the specific patterns to avoid.

## GPT-6.1 Sol and GPT-6 Astra

Model ids `gpt-6.1-sol` and `gpt-6-astra`. There's no Sol-specific prompting guide. OpenAI's GPT-6 guide was measured
on Astra, and Codex prompts the two the same way.

Sol carries on and overclaims more than Astra. Its system card found more unwanted persistence (above), more reward
hacking and concealed uncertainty, and a coding-misrepresentation rate of 1.5% against Astra's 0.5%. At severity 3
and above the two were level (28 flags against 27 in 49,650 tasks). So ask for the evidence behind each claim, keep
verified, approximate and blocked apart, and give a stated path for when it's blocked. Sol is far better on all of
these than GPT-5.6 Sol, so guardrails written for GPT-5.6 are probably stronger than it needs.

Sol misses some subtle patterns Astra catches. In OpenAI's audit, Sol at Ultra found 92% of Astra's findings at 14% of
the cost, and missed constant feature flags that other flags depended on. Name a known blind spot like that in the
brief for that run, and keep it out of shared files.

Broad goals work on Sol when the region is bounded. OpenAI ran a broad dead-code `/goal` on Sol over named
subdirectories with good results. Its advice is to start with one small task, compare models and efforts on it, then
widen to a directory and then the whole codebase.

Astra is tentative about stopping and asks more questions. It may come back for review after a first implementation
with work left. Remove review gates you don't need, and when you want approval, have it prepare a result first. It
over-tests small changes, delegates less than you might want, and formats heavily unless asked for prose.

## Choosing effort

The vendors disagree. OpenAI's API guide and Anthropic's Opus 5.5 guide say to use the highest levels only where
you've measured a gain. Codex's own best practices suggest Extra High for long, agentic, reasoning-heavy work, and
Claude Code's guide suggests raising effort when the work turns on cases that are easy to miss, like a bug in
unfamiliar code or a schema change with many readers. A sound default is medium for routine work and high for hard
debugging, subtle audits and long unattended runs, then compare on your own tasks. Effort won't rescue a bad brief, so
fix the text first. Codex's `ultra` level is maximum reasoning plus automatic delegation, not just more thinking.
