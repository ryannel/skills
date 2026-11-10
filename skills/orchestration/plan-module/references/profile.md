# The project settings: `ORCHESTRATE.md`

Every agent in the orchestrate set reads this file first. It holds everything that is particular to this project,
which is what lets the skills stay general. Keep it to about a page, and link to longer documents instead of
copying them in.

The script, `agent_loop.py`, reads the lines marked *(script)*. Keep each of those in the shape
`- **Label:** value`, with nothing else on the line except an optional `*( )*` note, because the script takes the
rest of the line as the value. Run `agent_loop.py profile` to confirm the script can read them. `Integrate` and
`Check` are required. The script refuses to run without them, because a guess at either one would push without
permission or merge untested work.

```markdown
# Project settings: <project>

- **Purpose:** docs/modules/BRIEF.md  *(the project brief, or another document that says what the project is for and what finishes the current goal)*
- **Quality bar:** <how good inspected work has to be, in words, naming shipped examples>
- **Anchors:** <for subjective work, where the option the owner chose and the reference sets are kept; or none>
- **Plans:** docs/modules  *(script)*
- **Evidence:** docs/evidence  *(script: review files and saved proof)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past reviews the owner agreed with or overturned)*
- **Check:** npm run check  *(script: required; the project's test command, which must pass before a merge, or `none`)*
- **Integrate:** local  *(script: required; `push` rebases onto Remote/Branch and pushes without force; `local` fast-forwards the local Branch only)*
- **Branch:** main  *(script: the main branch)*
- **Remote:** origin  *(script)*
- **Builders:** usually one Codex builder  *(how many builders, on which hosts, when the owner doesn't say)*
- **Default host:** codex  *(script: optional; the host used when the lead names none; otherwise the host the script runs inside)*
- **Review host:** same  *(script: optional; see below)*
- **Codex model:** gpt-6.1-sol  *(script: any `<host> model:` line sets that host's model)*
- **Claude model:** claude-opus-5-5  *(script)*
- **Claude planner model:** claude-fable-5-2  *(script: optional; see below)*
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

`Integrate: push` is standing permission to push verified work to the main branch. Set it only if the owner has
given that permission. If the project's `AGENTS.md` or `CLAUDE.md` says not to push without authorisation, say in
the note that this line is that authorisation, so that an agent reading both knows which one wins. Without the
owner's permission use `local`, and the owner merges.

`Review host` says where a review runs when the lead names no host. `same` means the builder's host. `other`
means the other of `codex` and `claude`: a milestone's review goes to the host that didn't build it, and a
design review to the host that didn't write the plan, when the `plan` command started the planner. A host name means that host. Write `other` when the owner
builds with both hosts, because a reviewer from another company shares fewer of the builder's blind spots.

A `<host> model` line sets the model for every agent the script starts on that host. To give one kind of agent
a different model, add a line that names the host and the kind: `Claude planner model`, `Claude builder model`,
`Claude reviewer model`, and the same three for `Codex` or any other host. The model has to be one that host can
run. Add such a line only when the owner asked for it, because a larger model spends the owner's quota faster.
A `--model` on a command still wins over both lines.

The plans folder may hold two files that are not plans. `BRIEF.md` is the project brief: what the owner wants
and why, approved by the owner before planning. `GLOSSARY.md` holds the agreed name for each thing in the
project. Every agent looks for them there by name, so they need no line of their own in this file. They are kept
in the plans folder because the `adopt` command merges files from it, which lets the lead put a changed brief or
glossary on the main branch without making a commit by hand.
