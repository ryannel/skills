# The project settings: `ORCHESTRATE.md`

Every agent in the orchestrate set reads this file first. It holds everything particular to one project, which is
what lets the skills stay general. Keep it to about a page, and link to longer documents rather than copying them
in.

The script, `agent_loop.py`, reads the lines marked *(script)*. It takes everything after the label as the value,
so keep each of those lines in the shape `- **Label:** value`, with nothing else on the line but an optional
`*( )*` note. Run `agent_loop.py settings` to confirm the script can read them.

`Merge` and `Test command` are required. The commands that build, review or merge refuse to run without them, and
the rest warn and fall back to `local` and no test, because a guess at either could push without permission or merge
untested work.

Contents:
- [The file](#the-file)
- [What the lines mean](#what-the-lines-mean)
- [A model or an effort for one kind of agent](#a-model-or-an-effort-for-one-kind-of-agent)

## The file

```markdown
# Project settings: <project>

- **Purpose:** docs/plans/BRIEF.md  *(the project brief, or another document that says what the project is for and what finishes the current goal)*
- **Quality bar:** <how good inspected work has to be, in words, naming shipped examples>
- **References:** <for subjective work, the folder in the repository where the option the user chose and the reference sets are kept; or none>  *(the planner writes it when it chooses a reference)*
- **Plans:** docs/plans  *(script: leave it out for the standard place; an older project may name another folder)*
- **Evidence:** .orchestrate/evidence  *(script: where the working folder opens in each worktree, for reviews, handoffs and saved proof; never committed; leave it out for this standard place)*
- **Graded examples:** .orchestrate/evidence/graded-examples.md  *(script: optional; with this line, `human accept` and `human rereview` add each review the user overturns to this file in the working folder; left out, nothing is added)*
- **Test command:** npm run check  *(script: required; the project's test command, which must pass before a merge, or `none`)*
- **Setup command:** npm ci  *(script: optional; installs what the tests and checks need in a fresh checkout, or `none`)*
- **Merge:** local  *(script: required; `push` rebases onto Remote/Branch and pushes without force; `local` fast-forwards the local Branch only)*
- **Branch:** main  *(script: the main branch)*
- **Remote:** origin  *(script)*
- **Builders:** <how many builders, on which hosts, as the user said: "one Claude builder", say>  *(script: the lead writes it before the first build; `run` starts no builder without a count, adds the counts up, and starts none past them unless `--more-builders` carries the user's words)*
- **Lead check-in:** 3h  *(script: optional; how long the lead's `watch` waits for a warning sign before it wakes the lead anyway, such as 3h or 90m; left out, 3 hours)*
- **Default host:** <host>  *(script: optional; codex, claude or a `Host` line's name, for when the lead names none; left out, the host the script runs inside)*
- **Review host:** <same|other|host>  *(script: optional; see below)*
- **Planner host:** <host>  *(script: optional, and only if the user wants planners on another host; left out, the `Default host`)*
- **<Host> model:** <model>  *(script: optional, and only when the user named a model; any `<host> model:` line, such as `Claude model:`, sets that host's model)*
- **Claude planner:** <model> <effort>  *(script: optional, and only when the user asked; a model, an effort or both for one kind of agent on one host; see the last section)*
- **Reviewer:** <effort>  *(script: optional, and only when the user asked; an effort for one kind of agent on every host)*
- **Effort:** medium  *(script: optional; for builders and reviewers, default medium; planners default to high)*
- **Claude permissions:** auto  *(script: the permission mode for Claude sessions in the background: auto, acceptEdits, dontAsk or bypassPermissions)*
- **Codex sandbox:** workspace-write  *(script: or danger-full-access, which only the user chooses; a browser won't start inside workspace-write)*
- **Writable roots:** <paths the build writes outside the worktree, separated by commas, such as ~/.cargo, ~/.npm>  *(script)*
- **Host gemini:** gemini -p {prompt} -m {model}  *(script: optional; any other command-line agent, with {prompt}, {model}, {effort} and {cwd} placeholders)*
- **Gemini model:** <model>  *(script: needed when its host line has {model}, unless the command passes --model)*

## Starting from a clean clone
<how a new worktree gets to a running product: the setup command, seed data and test accounts, the services it
needs, where secrets come from, and how two worktrees avoid sharing a port or a database>

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| <web-chrome> | <Chrome, desktop> | <`npm run dev`> | <Playwright screenshots, console and network log> | <empty, loading, error, slow network, resize> |
| <cli> | <the built binary> | <`cargo run -- …`> | <transcript and exit code> | <bad arguments, piped input, Ctrl-C> |

## Rules
- **Exclusive resources:** <things only one run at a time may use, such as "simulator"; or none>  *(script: named in each builder's prompt, which wraps a command that uses one in `lock <name> -- <command>`)*
- **Shared resources:** <resources several runs may use at once, each with how many, such as "gpu: 3"; or none>  *(script: `lock gpu` shares it up to that number, and `lock gpu.alone` waits to have it alone, for a run that needs the whole device)*
- **Test command lock:** none  *(script: a lock name, such as `gpu` or `gpu.alone`, that the script takes whenever it runs the test command, for a test command that uses a shared or exclusive resource)*
- **Lock hold limit:** 30 minutes  *(script: the default; a command under `lock`, or a locked item check, that holds a lock longer is stopped; the test command isn't; or none)*
- **Main-branch check <name>:** `<command>`; every <30m>; gap <leave out>; lock <resource names, or leave out>; timeout <2h>  *(script: optional, one line per check too slow to run before every merge; it runs on the main branch's tip after merges, and an item proves itself with `python3 "$ORCHESTRATE_SCRIPT" main-check <name>`. `every` spaces out the runs nobody waits for; `gap` spaces out every run, even one an item waits for, for a check that takes a machine builders share)*
- **Human decides:** <for example: changing the goal; spending; publishing or deploying; anything that can't be undone>  *(script: sent again on resumed turns)*
- **Licences and paths not to touch:** <for example: no GPL code, because the project ships under MIT; ../other-repo belongs to another team, so ask before changing it>  *(script: sent again on resumed turns)*

## Project guidance
- <rules for this kind of work that each agent reads, such as "Building: .agents/skills/<project>-engineering">
```

## What the lines mean

The lead writes this file from the brief before planning, with `Merge: local`, which pushes nothing, and the planner
adds the test and setup commands. The host, `Builders`, model, `Merge` and `Human decides` lines are the user's
choices about how the agents work, and the lead writes them before the first build. Leave out each host or model line
the user said nothing about. The script then uses the host it runs inside and each host's default model, which stays
current when a newer one ships. A project that uses only Claude Code sets `Default host: claude`, because a Codex line
fails on the first run where Codex isn't installed.

The script runs `Setup command` again in a checkout only when a tracked manifest or lockfile there has changed, such
as `package.json` or `uv.lock`, or a file the command names. It should install into ignored folders and leave tracked
files as they were, which is why `npm ci` is better here than `npm install`.

`Merge: push` is standing permission to push verified work to the main branch, so set it only if the user has given
that permission. Without it, use `local`: the script merges into the local main branch, and the user pushes. If the
project's `AGENTS.md` or `CLAUDE.md` says not to push without authorisation, say in this line's note that the line is
that authorisation, so an agent that reads both knows which one wins.

`Review host` says where a review runs when the lead names no host:

- `same` means the builder's host.
- `other` means the other of `codex` and `claude`. A milestone's review goes to the host that didn't build it, and
  a design review goes to the host that didn't write the plan, when the `plan` command started the planner.
- A host name means that host.

Write `other` when the user builds with both hosts, because a reviewer from another company shares fewer of the
builder's blind spots.

`Planner host` sends planners to one host, such as Claude Code for a Claude planner model while the builders stay
on Codex. With `Review host: other`, their design reviews then go to the other host.

`BRIEF.md`, `GLOSSARY.md`, `ARCHITECTURE.md` and `STATUS.md` sit in the plans folder by name, so they need no line
here.

This file holds settings, not progress. Write no status here, such as which milestones are done, because the
script keeps that in `STATUS.md`, and a second copy here goes stale.

## A model or an effort for one kind of agent

There are four kinds of agent here: planner, builder, reviewer and design reviewer. A design reviewer is the
reviewer that reads a module's design before anything is built. Unless a line says otherwise, every kind uses the
host's `model` line and the `Effort` line, except that planners run at high.

To give one kind of agent something different, add a line for it. A model belongs to one host, because Claude Code
can't run a GPT model and Codex can't run a Claude one. So a line that names a model names the host first:

| Line | What it sets |
|---|---|
| `Claude planner: claude-fable-5-2 high` | The model and effort of planners that run on Claude Code |
| `Codex planner: gpt-6.2-astra` | The model of planners that run on Codex. Their effort stays as it was |
| `Codex design reviewer: high` | The effort of design reviewers on Codex. Their model stays the host's |
| `Reviewer: high` | The effort of reviewers on every host. A line with no host can't name a model |

A line for one host never reaches another. If the settings say `Claude planner: claude-fable-5-2` and a planner is
started on Codex, it gets Codex's own model. So a project built on two hosts, or moving to a new one, needs no line
removed. To get the stronger model on both hosts, give each its own line.

For each launch, the script takes the first of these that is set. For the model:

1. `--model` on the command;
2. the line for that kind of agent on that host;
3. the host's `model` line;
4. the built-in default. Claude Code and Codex have one; any other host needs its `model` line if its command
   takes a model.

For the effort:

1. `--effort` on the command;
2. the line for that kind of agent on that host;
3. the line for that kind of agent on every host;
4. high for a planner, and the `Effort` line for the rest.

A design reviewer with no line of its own uses the reviewer's.

A larger model or a higher effort spends the user's quota faster. Use an effort the host accepts.
