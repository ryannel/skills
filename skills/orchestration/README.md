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
| [`instructing-agents`](instructing-agents/) | | Writes goals, briefs, steers and AGENTS.md files that agents act on |

The first four link to each other's files, so install them together: the `orchestrate` plugin, or all four with
`npx skills add`. The Claude agents come with the plugin. The Codex evaluator needs
`build/scripts/install_agents.sh --global` (add `--codex-only` if the plugin already installed the Claude
agents).

You can work at two speeds. In one chat, you run `/plan-module`, then `/build-milestone`, in Claude Code or Codex.
You can even switch between them partway, because everything the next agent needs is in the files. Or you can
hand the whole build over with `/build`, saying how many builders on which hosts, such as "two Claude builders and one
Codex".

## What it borrows, and what's house practice

From the sources:
- A planner that says what to build and leaves the how to the builder, and a separate evaluator that uses the running
  product, because Claude grading its own work is lenient. These come from Anthropic's
  [harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) post. Its first harness
  also had the evaluator agree testable criteria per sprint, and the author later dropped sprints for a stronger
  model. Design review keeps one such agreement per module, because a reviewer who agreed the items up front judges
  them more fairly later.
- Acceptance kept in a JSON file, progress kept in files, and checking the product end to end before building on it,
  from [long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
- Automated checks as the oracle, and locks so parallel agents don't collide, from
  [the C compiler](https://www.anthropic.com/engineering/building-c-compiler), which had no orchestrator at all and
  locked tasks rather than integration.
- Planners and workers kept separate, from [Cursor's work on scaling agents](https://cursor.com/blog/scaling-agents).
  The same post found locks became the bottleneck at twenty agents. Here one lock covers rebase, the Check and push,
  which is a deliberate trade at two or three builders; revisit it if more run, since a slow Check caps integration
  at one claim per Check.
- A durable spec, plan and status that survive compaction, from OpenAI's
  [long-horizon Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex) guide.

These sources describe different setups, not one shared recipe. The rest is house practice, kept because it fixed
something we saw, not because a source proved it:
- The escalation ladder in [the done-when reference](plan-module/references/done-when.md#when-a-review-fails): the
  same session, then a fresh one, then a re-plan, then parked for the owner.
- Milestones proved only by commands close without a reviewer, except a module's last milestone, whose review reads
  the whole module. Anthropic's rule for when an evaluator is worth its cost was how hard the task is for the model,
  not what kind of proof it has, so treat this as a trade-off to revisit.
- Looks are judged against a quality bar written in words, never against a target image. That's the owner's rule:
  agents told to match an image copy its accidents too.
- Every agent is launched with its model and effort named, in agent files, skill frontmatter and the profile, because
  defaults change between releases.
- The owner sets the pace by choosing how many builders run. The loop forecasts quota, but never slows down on its own.

## What the loop enforces

The loop doesn't take any agent's word for anything, and it is the only thing that decides what is accepted. It keeps
`<MODULE>-ACCEPTED.json` beside each done-when file, written only in its own commits, holding the authorised
definitions, the commit it checked, the reviews, and whether each milestone was accepted and by what.

- **Builders.** Before it accepts a claim, the done-when file has to be valid, with only the builder's own fields
  changed and the definitions the ones last authorised. The work has to be committed, with nothing untracked, and
  integrated after a fresh fetch. The profile's `Check` and every item's `check` have to pass when the loop runs them
  itself, in a clean checkout of the integrated tip. A builder saying `DONE` is never enough.
- **Reviewers.** They work in a clean checkout of the claimed commit. The loop checks that they changed only the
  review file and their own fields on that milestone, that the verdicts agree with the last line, and that a fail
  added one to `fails`, then lands the verdict itself. Anything else, and nothing lands.
- **Planners.** The loop validates what they wrote, rejects a plan that grants passes or touches a record, commits and
  integrates the rest, and records the new definitions. A new module waits for a design review.
- **The queue.** One rule decides what's ready, for `ready`, `status` and `run` alike: a milestone starts only when
  the ones before it in its module, and its `needs` elsewhere, are accepted. Claims on milestones are refs every clone
  can see, so two leads don't start the same one.
- **The owner.** Accepting without review, re-reviewing, unparking and changing scope are owner commands, refused
  inside any session the loop started and confirmed at a terminal.

## Hosts

| | Codex | Claude Code | Another CLI |
|---|---|---|---|
| Launch | on a Mac with the Codex app running, a thread the app lists under the project and runs itself; else `codex exec --json`; resumable either way | `claude -p` with stream-json, resumable; on a Mac with Claude desktop running and the CLI signed in, the session is also imported into the Code tab | the profile's `Host <name>:` command, one fresh process per turn |
| Owner in the app | watch, steer by typing, Stop (the loop reports `PAUSED`), take over after Stop; `run` again hands it back | watch the transcript; open the session to take over, and the loop pauses rather than write to it at the same time | none |
| Model and effort | pinned at launch and checked per turn from the session file | pinned at launch; the model is checked from the stream, the effort isn't | pinned in the command; not checked |
| Launch records | claims and reviews record the requested model and effort, the CLI version, and under `observed` only what the session file showed | the same; `observed` can hold the model, never the effort | requested model and effort only |
| Resumed turns | restate the binding rules (field ownership, `land`, Check, the profile's out-of-bounds lines) only when no goal is active; the result says `goal` | restate them on every resumed turn | each turn after the first carries them |
| Reviewers and planners can't launch agents | `-c features.multi_agent=false` | `--disallowedTools Agent`, plus the orchestrate agent files when installed | only the prompt says so |
| Goals and quota | goal status and a weekly-quota forecast, from Codex's local files | neither (Claude's `/goal` exists under `-p`, but the loop doesn't use it) | neither |
| Skills | found by name | found by name | the prompt gives each skill's path |

## Known limits

- Everything the loop starts runs inside the lead's process, with its sandbox and operating-system permissions. A
  lead in a sandbox without network or `.git` writes can't run builders that integrate, and a builder that needs
  screen recording or a camera needs it granted to the app the lead runs in.
- The checks run with the lead's own permissions, outside any host's sandbox. The check strings are pinned, but a
  script a check calls can still be changed by the builder, so review new check scripts. Proper isolation would need
  a container.
- The acceptance record is protected by convention and detection, not cryptography: a commit that edits it without
  the loop's trailer blocks the next claim, but an agent that forges the trailer deliberately could get past that. A
  module the loop hasn't seen before is taken as it stands, once.
- Claude runs are meant to use the signed-in plan, so the loop removes every `ANTHROPIC_*` and `CLAUDE*` variable
  except `CLAUDE_CONFIG_DIR` and `CLAUDE_CODE_OAUTH_TOKEN` (the plan's token) from their environment. That also drops any provider or deployment settings kept in
  those variables, and a configured credential helper could still supply other credentials. Anthropic has said `--bare` will become the
  default for `claude -p`, and bare mode reads only API-key credentials and skips agent and skill discovery, so
  Claude builders will need a change then. Tested with Claude Code 2.1.239 and Codex 0.167.
- The reviewer is the least proven part. `review-milestone` makes it use the product itself, read the whole diff,
  write down what it's going to inspect before it looks, and fail what it finds rather than argue it away. It ships
  with four graded examples, and the owner calibrates it by spot-checking early verdicts. That's the method
  Anthropic used, but nobody has yet measured how often this reviewer catches a fake, or wrongly fails a sound one.
- Sessions in the apps rest on internal surfaces: Codex deep links, its IPC socket and experimental app-server
  methods, and Claude desktop's `claude://resume` import. They were proven with the Codex app 26.1103 (CLI
  0.167.0-alpha.3.2) and Claude desktop 4.23118.0, and can change with an app update. Each result line says which
  path ran (`path`, and `path_reason` when headless); `ORCHESTRATE_HEADLESS=1` forces the old path. A new Codex thread
  opens in the app's window, which brings the app forward, and starts with a one-line bootstrap turn. A Claude
  session runs in the loop's own CLI, so the CLI must be signed in; signed out, Claude runs fail as before.
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
