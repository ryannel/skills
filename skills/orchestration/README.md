# Orchestration

These skills are for building software with AI agents in Claude Code and Codex. They work for web apps, native
apps, CLI tools, libraries and engines. Each project describes itself once, in a file called `ORCHESTRATE.md`, and
the skills read it, so they don't need to know anything project-specific.

| Skill | Model, effort | What it does |
|---|---|---|
| [`plan-module`](plan-module/) | Opus 5.5, high | Sets the project up, plans the modules and how they connect, then plans each module's design, milestones and done-when file |
| [`build-milestone`](build-milestone/) | Codex `gpt-6.1-sol` or Opus 5.5, medium | Builds the next milestone, proves it, and integrates it |
| [`review-milestone`](review-milestone/) | Opus 5.5, medium | Judges a claimed milestone or a design with fresh eyes |
| [`build`](build/) | Opus 5.5 lead, medium (any host can lead) | Builds the planned project unattended: keeps N builders busy on ready milestones, on Codex, Claude Code or another host, with fresh reviewers and a planner |

They link to each other's files, so install them together: the `orchestrate` plugin, or all four with
`npx skills add`. The Claude agents come with the plugin. The Codex evaluator needs
`build/scripts/install_agents.sh --global` (add `--codex-only` if the plugin already installed the Claude
agents).

You can work at two speeds. In one chat, you run `/plan-module`, then `/build-milestone`, in Claude Code or Codex.
You can even switch between them partway, because everything the next agent needs is in the files. Or you can fan
hand the whole build over with `/build`, saying how many builders on which hosts, such as "two Claude builders and one
Codex".

## What it borrows, and what's house practice

From the sources:
- A planner that says what to build and leaves the how to the builder, and a separate evaluator that uses the running
  product, because Claude grading its own work is lenient. These come from Anthropic's
  [harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) post. That post also had
  the evaluator agree testable criteria before building, which is what design review does here.
- Acceptance kept in a JSON file, progress kept in files, and checking the product end to end before building on it,
  from [long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
- Automated checks as the oracle, and locks so parallel agents don't collide, from
  [the C compiler](https://www.anthropic.com/engineering/building-c-compiler), which had no orchestrator at all.
- Planners and workers kept separate, from [Cursor's work on scaling agents](https://cursor.com/blog/scaling-agents).
- A durable spec, plan and status that survive compaction, from OpenAI's
  [long-horizon Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex) guide.

These sources describe different setups, not one shared recipe. The rest is house practice, kept because it fixed
something we saw, not because a source proved it:
- The escalation ladder. After one or two failed reviews, the same session tries again. After three, a fresh session
  takes over. After four, the planner re-plans. Four more after that, and the milestone is parked for the owner.
- Milestones proved only by commands close without a reviewer, except a module's last milestone, whose review reads
  the whole module. Anthropic's rule for when an evaluator is worth its cost was how hard the task is for the model,
  not what kind of proof it has, so treat this as a trade-off to revisit.
- Looks are judged against a quality bar written in words, never against a target image. That's the owner's rule:
  agents told to match an image copy its accidents too.
- Every agent is launched with its model and effort named, in agent files, skill frontmatter and the profile, because
  defaults change between releases.
- The owner sets the pace by choosing how many builders run. The loop forecasts quota, but never slows down on its own.

## What the loop enforces

The loop doesn't take a builder's word for anything. Before it accepts a claim, it checks four things. The done-when
file has to be valid, with the acceptance definitions unchanged since the planner wrote them. The work has to be
committed with nothing untracked, and integrated after a fresh fetch. The profile's `Check` and every item's `check`
have to pass when the loop runs them itself. And the milestone's state has to say what happens next. A builder saying
`DONE` is never enough on its own.

## Known limits

- The checks run with the lead's own permissions, outside Codex's sandbox. The check strings are pinned, but a script
  a check calls can still be changed by the builder, so review new check scripts. Proper isolation would need a
  container.
- The reviewer is the least proven part. `review-milestone` makes it use the product itself, read the whole diff,
  write down what it's going to inspect before it looks, and fail what it finds rather than argue it away. It ships
  with four graded examples, and the owner calibrates it by spot-checking early verdicts. That's the method
  Anthropic used, but nobody has yet measured how often this reviewer catches a fake.
- The reviewer has write access, because it records its own verdict. It can't launch other agents, the lead checks
  what its commit touched, and the loop rejects changed definitions.
- The loop is POSIX only. Its goal-based stop rules depend on Codex's local goal database, and whether `codex exec`
  writes to it hasn't been confirmed. Without it, those rules are skipped.
- No project has run a complete milestone cycle under this version yet.

## What's left out, for now

The rule is to start small and add something only when its absence has actually caused a problem. So these aren't
here yet:
- merging through pull requests (`Integrate` is `push` or `local`);
- dedicated research agents (an ordinary subagent does the job);
- trying several designs in parallel, or a second agent confirming each finding;
- running checks in a container.
