# Testing the orchestrate suite end to end

## What this is for

`orchestrate` is a set of skills plus a loop script for planning and building projects with AI agents on Claude Code
and Codex. It's about to be published. We want to know how well it works for an engineer who picks it up cold, and
where it's confusing, slow, wasteful or wrong, so those things can be fixed first.

You play that engineer's agent. You take one small fictitious project from an empty repository to built and
accepted, using the suite the way its own docs say to. Your message names the project, the repository and the hosts.

## The suite under test

`/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/e2e/suite-v5/orchestration/`. `README.md` there is the entry point, and the four skills
are the folders beside it. The loop script is `build/scripts/agent_loop.py`.

Use these files by path. An older copy is installed in this session as the `orchestrate` plugin (skills named
`orchestrate:*`, agents named `orchestrate-planner` and `orchestrate-evaluator`). Don't call those through the Skill
or Agent tools, because they aren't the version under test.

## Facts about this run

- The owner of this suite works only by chatting with the lead and never uses a terminal, and this version was just
  changed to match: the lead runs every loop command, the owner's decisions included. This run is the first live
  test of that, so it's the part to watch most closely. You are the lead, and you also stand in for the owner. Keep
  the two apart: when a stop needs the owner, write down in your log what you, as lead, would have asked them in
  chat and what they answered, then record it the way the docs tell a lead to. Judge whether what the loop gave you
  at that stop was enough to ask a good question without reading anything else.
- As the owner, decide as a reasonable one would. Once the first milestone is accepted, change your mind about one
  small thing in what's wanted (your message says what), and see how the docs have the lead handle a change the
  owner gives in chat. At the end, ask for the report and check it shows every decision recorded in your name, in
  the words you gave.
- Every loop command needs `ORCHESTRATE_HEADLESS=1` in its environment, so sessions run headless and nothing opens in
  the real owner's desktop apps.
- There's no remote, so the project integrates locally.
- If anything in the docs, a result line or an error still tells the owner to type a command or go to a terminal,
  that's a bug in this version: log it with the exact text.
- Use each host's default model and effort. Both hosts were checked a few minutes ago and start fine from here. The
  Codex CLI isn't on PATH; the loop finds it by itself.
- Loop commands that run a session take many minutes. Run them in the background and wait for them to finish, rather
  than under a timeout that would kill them.

## Done

Every planned milestone is accepted by the loop, or you've met something you can't get past, which is a result too.
If the same loop stop comes back three times with no progress, stop there and report it.

Either way, check for yourself whether what got built does what the owner asked, by using it. Don't take the
acceptance record's word for it.

## Boundaries

- Work only inside your scenario folder. Don't edit anything under `/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/e2e/suite-v5` or `/Users/ryannel/Workspace/skills`. If the suite
  has a bug, record it. Work around it only if you can do so without editing the suite, and say how.
- A real build is running in `~/Workspace/thrum` on the same Codex account. Don't touch that repository, and don't
  run `pause` or owner commands against any repository but yours.
- Quota is shared with that build. Don't raise models or effort, and don't run more builders than your message says.
- Nothing leaves this machine: no push, no remote.

## What comes back

In your scenario's `out/` folder:

- `friction.md`, written as you go and not at the end. One entry per thing that got in the way: what you were trying
  to do, what happened (the command and its exact output, or the doc passage), what you expected, what it cost in
  time or tokens, and how bad it was (blocked, wasted time or tokens, confusing, or nitpick). Note briefly what
  worked well too. Add anything you wished the tools had offered.
- `loop-results.jsonl`: every loop command you ran and its raw result line, in order, with the time.
- `result.json`: per milestone, whether the loop accepted it, how many reviews it took and how many failed;
  wall-clock per phase; tokens from the result lines' `usage`; each owner decision you made; and your own verdict on
  whether the product meets the ask, with what you ran to check.

Keep what you verified apart from what you suspect. Your final message: the outcome in a few lines, then the five
problems most worth fixing.
