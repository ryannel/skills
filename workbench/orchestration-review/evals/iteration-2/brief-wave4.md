# Testing the orchestrate suite end to end

## What this is for

`orchestrate` is a set of skills plus a loop script for planning and building projects with AI agents on Claude Code
and Codex. It's about to be published. We want to know how well it works for an engineer who picks it up cold, and
where it's confusing, slow, wasteful or wrong, so those things can be fixed first.

You play that engineer's agent. You take one small fictitious project from an empty repository to built and
accepted, using the suite the way its own docs say to. Your message names the project, the repository and the hosts.

## The suite under test

`/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/e2e/suite-v4/orchestration/`. `README.md` there is the entry point, and the four skills
are the folders beside it. The loop script is `build/scripts/agent_loop.py`.

Use these files by path. An older copy is installed in this session as the `orchestrate` plugin (skills named
`orchestrate:*`, agents named `orchestrate-planner` and `orchestrate-evaluator`). Don't call those through the Skill
or Agent tools, because they aren't the version under test.

## Facts about this run

- You stand in for the owner wherever the process needs one: a decision, a pick, an attended item, an owner command.
  Decide as a reasonable owner would. Log each one, because each is a place where an unattended run would have
  stopped and waited.
- Every loop command needs `ORCHESTRATE_HEADLESS=1` in its environment, so sessions run headless and nothing opens in
  the real owner's desktop apps.
- There's no remote, so the project integrates locally.
- The suite's owner commands ask for a typed confirmation at a terminal, so that only the real owner can make
  those calls. Nobody is at a terminal in this test, and you mustn't fake one. Where the run needs an owner command,
  log it as a stop with the exact command. If the docs give the lead another way forward, take it and say so;
  otherwise leave that module there and carry on with whatever else is ready.
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

- Work only inside your scenario folder. Don't edit anything under `/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/e2e/suite-v4` or `/Users/ryannel/Workspace/skills`. If the suite
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
