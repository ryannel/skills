# Orchestration

These skills are for building software with AI agents in Claude Code and Codex. They work for web apps, native
apps, CLI tools, libraries and engines. Each project describes itself once, in a file called `ORCHESTRATE.md`, and
the skills read it, so they don't need to know anything project-specific.

| Skill | Model, effort | What it does |
|---|---|---|
| [`plan-module`](plan-module/) | Opus 5.5, high | Sets the project up, plans the modules and how they connect, then plans each module's design, milestones and done-when file |
| [`build-milestone`](build-milestone/) | Codex `gpt-6.1-sol` or Opus 5.5, medium | Builds the next milestone, proves it, and merges it |
| [`review-milestone`](review-milestone/) | Opus 5.5, medium | Judges a milestone or a design with fresh eyes |
| [`build-parallel`](build-parallel/) | Opus 5.5 lead, medium | Runs several Codex builders at once, with reviewers and a planner on call |
| [`instructing-agents`](instructing-agents/) | | Writes goals, briefs, steers and skills that agents act on |
| [`skill-creator`](skill-creator/) | | Creates, rewrites and tests skills in this suite's plain voice. Based on [Anthropic's skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) (Apache 2.0) |

You can work at two speeds. In one chat, you run `/plan-module`, then `/build-milestone`, in Claude Code or Codex.
You can even switch between them partway, because everything the next agent needs is in the files. Or you can fan
out with `/build-parallel`.

## Why it works this way

It's built on what Anthropic learned running agents for hours at a time
([harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps),
[long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents),
[the C compiler](https://www.anthropic.com/engineering/building-c-compiler)), plus
[Cursor's work on scaling agents](https://cursor.com/blog/scaling-agents). Their setups had four roles. A planner
says what to build and leaves the how to the builder. A builder builds. Automated checks answer whatever they can.
And a separate reviewer uses the running product to judge the rest. The reviewer costs real time, so it only comes in
where checks can't decide: things you have to look at, contract changes, and the end of a module.

Done-when files are JSON, and every field has one writer, because agents are less likely to mangle a structured file
than a page of prose.

Work can be proved by commands, by looking at captures, or by reading code, and most things are best proved by a mix
([proofs](plan-module/references/proofs.md)). Looks are judged against a quality bar written in words, never against
a target image, because agents told to match an image copy its accidents too.

The loop doesn't take a builder's word for anything. The work has to be committed and merged, and the loop reruns the
checks itself.

When a review fails, what happens next depends on how many times it has failed. After one or two failures, the same
session tries again. After three, a fresh session takes over. After four, the planner re-plans. Four more after
that, and the milestone is parked for the owner.

Every agent is launched with its model and effort named, because defaults change between releases.

The owner sets the pace by choosing how many streams run. The loop forecasts quota, but never slows down on its own.

## What's left out, for now

The rule is to start small and add something only when its absence has actually caused a problem. So these aren't
here yet:
- merging through pull requests (streams rebase onto one branch instead);
- dedicated research agents (an ordinary subagent does the job);
- trying several designs in parallel, or a second agent confirming each finding;
- any report besides `DONE`, `BLOCKED` and `NEEDS_CONTEXT`.

The reviewer is the least proven part. Anthropic found Claude a lenient QA agent out of the box. It finds problems
and then waves them through, and it tests the surface. So `review-milestone` makes it use the product itself, write
down what it's going to inspect before it looks, and fail what it finds rather than argue it away. The owner
calibrates it by spot-checking early verdicts, and each one they overturn becomes an example for future reviews.
