# The project settings: `ORCHESTRATE.md`

Every agent in the orchestrate set reads this file first. It holds everything particular to one project, which is
what lets the skills stay general. Keep it to about a page, and link to longer documents rather than copying them
in.

The script, `agent_loop.py`, reads the lines marked *(script)*. It takes everything after the label as the value,
so keep each of those lines in the shape `- **Label:** value`, with nothing else on the line but an optional
`*( )*` note. Run `agent_loop.py profile` to confirm the script can read them. `Integrate` and `Check` are required,
and the script refuses to run without them, because a guess at either could push without permission or merge
untested work.

Contents:
- [The file](#the-file)
- [Lines that need care](#lines-that-need-care)
- [A model or an effort for one kind of agent](#a-model-or-an-effort-for-one-kind-of-agent)

## The file

```markdown
# Project settings: <project>

- **Purpose:** docs/plans/BRIEF.md  *(the project brief, or another document that says what the project is for and what finishes the current goal)*
- **Quality bar:** <how good inspected work has to be, in words, naming shipped examples>
- **Anchors:** <for subjective work, where the option the owner chose and the reference sets are kept; or none>
- **Plans:** docs/plans  *(script: leave it out for the standard place; an older project may name another folder)*
- **Evidence:** docs/evidence  *(script: review files and saved proof)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past reviews the owner agreed with or overturned)*
- **Check:** npm run check  *(script: required; the project's test command, which must pass before a merge, or `none`)*
- **Integrate:** local  *(script: required; `push` rebases onto Remote/Branch and pushes without force; `local` fast-forwards the local Branch only)*
- **Branch:** main  *(script: the main branch)*
- **Remote:** origin  *(script)*
- **Builders:** usually one Codex builder  *(how many builders, on which hosts, when the owner doesn't say)*
- **Default host:** codex  *(script: optional; the host used when the lead names none; otherwise the host the script runs inside)*
- **Review host:** same  *(script: optional; see below)*
- **Planner host:** claude  *(script: optional; the host planners run on when the lead names none; otherwise the `Default host`)*
- **Codex model:** gpt-6.1-sol  *(script: any `<host> model:` line sets that host's model)*
- **Claude model:** claude-opus-5-5  *(script)*
- **Claude planner:** <model> <effort>  *(script: optional, and only when the owner asked; a model, an effort or both for one kind of agent on one host; see the last section)*
- **Reviewer:** <effort>  *(script: optional, and only when the owner asked; an effort for one kind of agent on every host)*
- **Effort:** medium  *(script: optional; for builders and reviewers, default medium; planners run at high unless `--effort` says otherwise)*
- **Claude permissions:** auto  *(script: the permission mode for Claude sessions in the background: auto, acceptEdits, dontAsk or bypassPermissions)*
- **Codex sandbox:** workspace-write  *(script: or danger-full-access, which only the owner chooses; a browser won't start inside workspace-write)*
- **Writable roots:** <paths the build writes outside the worktree, such as ~/.cargo or ~/.npm>  *(script)*
- **Host gemini:** gemini -p {prompt} -m {model}  *(script: optional; any other command-line agent, with {prompt}, {model}, {effort} and {cwd} placeholders)*
- **Gemini model:** <model>  *(script: needed for each host line)*

## Starting from a clean clone
<how a new worktree gets to a running product: the setup command, seed data and test accounts, the services it
needs, where secrets come from, and how two worktrees avoid sharing a port or a database>

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| <web-chrome> | <Chrome, desktop> | <`npm run dev`> | <Playwright screenshots, console and network log> | <empty, loading, error, slow network, resize> |
| <cli> | <the built binary> | <`cargo run -- …`> | <transcript and exit code> | <bad arguments, piped input, Ctrl-C> |

## Rules
- **Exclusive resources:** <things only one run at a time may use, such as "simulator" or "gpu: timing runs"; or none>
- **Large captures:** <where frame sequences and other bulky evidence go if they aren't committed, and how a reviewer gets them>
- **Owner decides:** <for example: changing the goal; spending; publishing or deploying; anything that can't be undone>  *(script: sent again on resumed turns)*
- **Licences and paths not to touch:** <for example: no GPL code; never modify ../other-repo>  *(script: sent again on resumed turns)*

## Project guidance
- <rules for this kind of work that each agent reads, such as "Building: .agents/skills/<project>-engineering">
```

## Lines that need care

`Integrate: push` is standing permission to push verified work to the main branch, so set it only if the owner has
given that permission. Without it, use `local`, and the owner merges. If the project's `AGENTS.md` or `CLAUDE.md`
says not to push without authorisation, say in this line's note that the line is that authorisation, so an agent
that reads both knows which one wins.

`Review host` says where a review runs when the lead names no host:

- `same` means the builder's host.
- `other` means the other of `codex` and `claude`. A milestone's review goes to the host that didn't build it, and
  a design review goes to the host that didn't write the plan, when the `plan` command started the planner.
- A host name means that host.

Write `other` when the owner builds with both hosts, because a reviewer from another company shares fewer of the
builder's blind spots.

`Planner host` sends planners to one host, such as Claude Code for a Claude planner model while the builders stay
on Codex. With `Review host: other`, their design reviews then go to the other host.

The plans folder holds four files of the project's besides the module folders. `STATUS.md` is the owner's page,
which the script writes. `BRIEF.md` is the project brief: what the owner wants and why, approved by the owner
before planning. `GLOSSARY.md` holds the agreed name for each thing in the project. `ARCHITECTURE.md` is the list
of modules. Every agent looks for them there by name, so they need no line in this file. They are kept in the
plans folder because the `adopt` command merges files from it, which lets the lead put a changed brief or glossary
on the main branch without making a commit by hand. [The module's files](done-when.md#where-everything-is) shows
the whole layout.

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
| `Codex planner: gpt-6-astra` | The model of planners that run on Codex. Their effort stays as it was |
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

Add these lines only when the owner asked for them, because a larger model or a higher effort spends the owner's
quota faster. Use an effort the host accepts.
